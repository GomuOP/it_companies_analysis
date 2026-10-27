"""Step 6: relevance gate -> Gemini (context-only, JSON) -> citation validation.

Owner: Member B
Quick test: python -m src.answer "What was Infosys attrition in FY2025-26?"
"""
import json
import sys

from .config import GEMINI_API_KEY, GEMINI_MODEL, MIN_SCORE, NOT_FOUND
from .retrieve import search

PROMPT = """You answer questions about company annual reports using ONLY the context below.
Rules:
- Use only facts stated in the context. Do not use outside knowledge.
- If the context does not contain the answer, set "found" to false.
- Every claim must cite the chunk id(s) it came from.
- Keep numbers, units and fiscal years exactly as written in the context.

Return JSON only:
{{"found": true|false, "answer": "<short answer>", "citations": ["<chunk id>", ...]}}

Context:
{context}

Question: {question}
"""


def _client():
    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


def call_gemini(prompt: str) -> dict:
    from google.genai import types
    resp = _client().models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json"),
    )
    try:
        return json.loads(resp.text)
    except (json.JSONDecodeError, TypeError):
        return {"found": False, "answer": "", "citations": [], "error": "bad JSON from LLM"}


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
    q = " ".join(sys.argv[1:]) or "What was the attrition rate at Infosys?"
    r = answer(q)
    print(r["answer"])
    for c in r["citations"]:
        print(f"  - {c['company']} Annual Report {c['fy']}, page {c['page']}")
    if not r["found"]:
        print("  reason:", r.get("reason"))
