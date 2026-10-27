"""Step 6: relevance gate -> Gemini (context-only, JSON) -> citation validation.

Owner: Member B
Quick test: python -m src.answer "What was Wipro attrition in FY2023-24?"
"""
import json
import sys
import time
from functools import lru_cache

from .config import (GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FALLBACK_MODELS, GEMINI_TIMEOUT_S,
                     MIN_SCORE, NOT_FOUND)
from .retrieve import search

PROMPT = """You answer questions about the FY2023-24 annual reports of Tech Mahindra, Wipro and HCLTech
using ONLY the context below.
Rules:
- Use only facts stated in the context. Do not use outside knowledge.
- If the context does not contain the answer, set "found" to false.
- If the question asks about a different company or a different fiscal year than the context covers,
  set "found" to false. Do not substitute another year's or another company's figure.
- Predictions, opinions and investment advice are not in the reports: set "found" to false.
- Every claim must cite the chunk id(s) it came from. Each chunk header shows its company; never attribute
  a figure to a company other than the one in that chunk's header.
- Keep numbers, units and fiscal years exactly as written in the context. Do not convert units or compute
  new figures. Say "consolidated" or "standalone" when the context says which one it is.
- For comparisons, state each company's value separately, each with its own citation. If the companies
  report in different units, you may convert to one unit (1 crore = 10 million) but also show the original
  figure as written, e.g. "₹897,603 million (≈ ₹89,760 crore)".
- Put chunk ids ONLY in the "citations" list, never inside the "answer" text.

Return JSON only:
{{"found": true|false, "answer": "<short answer>", "citations": ["<chunk id>", ...]}}

Context:
{context}

Question: {question}
"""


@lru_cache(maxsize=1)
def _client():
    # Kept alive for the process: google-genai closes the HTTP client when the Client object is garbage-collected
    from google import genai
    from google.genai import types
    return genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_S * 1000))


def call_gemini(prompt: str) -> dict:
    """Main model first; on overload / rate limit / timeout retry once, then try the fallback models."""
    from google.genai import types
    config = types.GenerateContentConfig(temperature=0, response_mime_type="application/json")
    last_error = None
    for model in [GEMINI_MODEL, *GEMINI_FALLBACK_MODELS]:
        for attempt in range(2):
            try:
                resp = _client().models.generate_content(model=model, contents=prompt, config=config)
            except Exception as e:  # 503 overloaded, 429 rate limit, timeouts, network errors
                last_error = f"{model}: {str(e)[:120]}"
                if "429" in str(e):  # quota used up: retrying the same model only wastes time
                    break
                time.sleep(2 * (attempt + 1))
                continue
            try:
                return {**json.loads(resp.text), "model": model}
            except (json.JSONDecodeError, TypeError):
                return {"found": False, "answer": "", "citations": [], "error": "bad JSON from LLM"}
    return {"found": False, "answer": "", "citations": [], "error": f"LLM unavailable ({last_error})"}


def not_found(reason, chunks):
    return {"found": False, "answer": NOT_FOUND, "citations": [], "reason": reason, "retrieved": chunks}


def answer(question: str) -> dict:
    chunks = search(question)
    best = chunks[0]["cosine"] if chunks else 0.0

    # Refusal 1: retrieval found nothing relevant -> do not call the LLM
    if best < MIN_SCORE:
        return not_found(f"best similarity {best:.2f} < threshold {MIN_SCORE}", chunks)

    context = "\n\n".join(f"[{c['id']}] ({c['company']}, {c['fy']}, page {c['page']})\n{c['text']}" for c in chunks)
    out = call_gemini(PROMPT.format(context=context, question=question))

    # Refusal 2: LLM says the context does not answer it
    if out.get("error"):
        return not_found(f"LLM error: {out['error']}", chunks)
    if not out.get("found"):
        return not_found("LLM: answer not in retrieved context", chunks)

    # Refusal 3: citations must point to chunks we actually retrieved
    by_id = {c["id"]: c for c in chunks}
    valid = [by_id[i] for i in out.get("citations", []) if i in by_id]
    if not valid:
        return not_found("no valid citations", chunks)

    return {
        "found": True,
        "answer": out.get("answer", ""),
        "citations": [{"id": c["id"], "company": c["company"], "fy": c["fy"], "page": c["page"],
                       "quote": c["text"][:300]} for c in valid],
        "retrieved": chunks,
    }


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What was the attrition rate at Wipro?"
    r = answer(q)
    print(r["answer"])
    for c in r["citations"]:
        print(f"  - {c['company']} Annual Report {c['fy']}, page {c['page']}")
    if not r["found"]:
        print("  reason:", r.get("reason"))
