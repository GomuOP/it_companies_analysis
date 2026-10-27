"""Evaluation: answerable questions must cite the expected page; unanswerable must be refused.

Owner: Member B
Run:   python eval.py
Fill expected pages after checking the PDFs. Log every failure + fix in FAILED.md.
"""
from src.answer import answer

ANSWERABLE = [
    # (question, company, expected_page or None if not yet known)
    ("What was the employee attrition rate at Infosys in FY2025-26?", "Infosys", None),
    ("What was TCS's total headcount at the end of FY2025-26?", "TCS", None),
    ("What was HCLTech's consolidated revenue for FY2025-26?", "HCLTech", None),
    ("What does TCS say about its investments in AI?", "TCS", None),
    ("What are the key risks Infosys highlights?", "Infosys", None),
    ("Which geography contributes the most revenue for HCLTech?", "HCLTech", None),
]

UNANSWERABLE = [
    "What will Infosys's share price be next year?",
    "What was Accenture's revenue in FY2025-26?",
    "What is the favourite food of the TCS CEO?",
    "Should I invest in HCLTech?",
]


def main():
    ok = 0
    print("=== Answerable ===")
    for q, comp, page in ANSWERABLE:
        r = answer(q)
        pages = [(c["company"], c["page"]) for c in r["citations"]]
        hit = r["found"] and (page is None or (comp, page) in pages)
        ok += hit
        print(f"[{'PASS' if hit else 'FAIL'}] {q}\n   -> {r['answer'][:150]}\n   cites: {pages} {r.get('reason', '')}")
    print("\n=== Unanswerable (must refuse) ===")
    for q in UNANSWERABLE:
        r = answer(q)
        hit = not r["found"]
        ok += hit
        print(f"[{'PASS' if hit else 'FAIL'}] {q}\n   -> {r['answer'][:150]} {r.get('reason', '')}")
    total = len(ANSWERABLE) + len(UNANSWERABLE)
    print(f"\nScore: {ok}/{total}")


if __name__ == "__main__":
    main()
