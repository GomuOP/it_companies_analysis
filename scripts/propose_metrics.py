"""Ask Gemini to PROPOSE metric values from retrieved pages. Output is a draft for HUMAN checking.

Owner: Member C
Run:   python -m scripts.propose_metrics
Writes data/metrics_proposed.json. Open each PDF at the proposed page, verify, then copy into data/metrics.json.
"""
import json

from src.config import COMPANIES, DATA
from src.retrieve import search
from src.answer import call_gemini

QUERIES = {
    "Revenue": "consolidated revenue from operations for the year in crore",
    "Operating margin": "operating margin percentage for the year",
    "Headcount": "total number of employees headcount at year end",
    "Attrition": "employee attrition rate for the year",
}

PROMPT = """From the context, extract the {metric} of {company} for the latest fiscal year.
Return JSON only: {{"value": <number or null>, "unit": "<unit>", "fy": "<fiscal year>", "chunk_id": "<id>",
"quote": "<exact sentence containing the number>"}}. Use null if it is not clearly stated. Do not guess.

Context:
{context}
"""

out = []
for company in COMPANIES:
    for metric, q in QUERIES.items():
        chunks = search(f"{company} {q}")
        ctx = "\n\n".join(f"[{c['id']}] (page {c['page']})\n{c['text']}" for c in chunks)
        r = call_gemini(PROMPT.format(metric=metric, company=company, context=ctx))
        page = next((c["page"] for c in chunks if c["id"] == r.get("chunk_id")), None)
        rec = {"company": company, "metric": metric, **r, "page": page, "verified": False}
        print(rec)
        out.append(rec)

with open(DATA / "metrics_proposed.json", "w") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("Wrote data/metrics_proposed.json -> now VERIFY each value against the PDF page.")
