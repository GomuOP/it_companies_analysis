"""Evaluation: answerable questions must cite an expected page; unanswerable must be refused.

Owner: Member B
Run:   python eval.py
Expected pages: every PDF page (1-based) that states the exact figure from data/key_facts.md. Log every failure + fix in FAILED.md.
"""
from src.answer import answer

ANSWERABLE = [
    # (question, company, set of acceptable PDF pages, or None if any citation of that company is fine)
    ("What was Tech Mahindra's revenue in FY2023-24?", "TechMahindra", {2, 8, 20, 26, 201, 317, 435, 500, 501, 502, 524, 525}),
    ("What was Tech Mahindra's total headcount at the end of FY2023-24?", "TechMahindra", {2, 8, 21, 319}),
    ("What was Tech Mahindra's IT attrition in FY2023-24?", "TechMahindra", {9, 23, 103, 320}),
    ("What was Wipro's consolidated revenue in FY2023-24?", "Wipro", {23, 38, 90, 247, 302, 303, 346, 410}),
    ("What was Wipro's IT Services operating margin in FY2023-24?", "Wipro", {22}),
    ("How many employees did Wipro have as of March 31, 2024?", "Wipro", {17, 105}),
    ("What was Wipro's voluntary attrition in FY2023-24?", "Wipro", {22, 434}),
    ("What was HCLTech's consolidated revenue for FY2023-24?", "HCLTech", {5, 14, 15, 62, 104, 105, 106, 320, 321, 336}),
    ("What was HCLTech's EBIT margin in FY2023-24?", "HCLTech", {7}),
    ("What was HCLTech's total headcount in FY2023-24?", "HCLTech", {7, 15, 79, 107, 182, 192, 193, 196}),
    ("What was HCLTech's employee attrition rate in FY2023-24?", "HCLTech", {7, 79, 124}),
    ("What does Tech Mahindra say about its investments in AI?", "TechMahindra", None),
    ("What are the key risks Wipro highlights?", "Wipro", None),
    ("Compare the attrition of Wipro and HCLTech in FY2023-24.", "HCLTech", {7, 79, 124}),
]

UNANSWERABLE = [
    "What will Wipro's share price be next year?",
    "What was Accenture's revenue in FY2023-24?",
    "What was Infosys's headcount in FY2023-24?",
    "What was Wipro's revenue in FY2019-20?",
    "What is the favourite food of the Tech Mahindra CEO?",
    "Should I invest in HCLTech?",
    "Who won the 2023 Cricket World Cup?",
]


def is_error(r):
    return r.get("reason", "").startswith("LLM error")


def main():
    ok = errors = 0
    print("=== Answerable ===")
    for q, comp, pages in ANSWERABLE:
        r = answer(q)
        cites = [(c["company"], c["page"]) for c in r["citations"]]
        hit = r["found"] and any(c == comp and (pages is None or p in pages) for c, p in cites)
        ok += hit
        errors += is_error(r)
        print(f"[{'PASS' if hit else 'ERROR' if is_error(r) else 'FAIL'}] {q}\n   -> {r['answer'][:150]}\n   cites: {cites} {r.get('reason', '')}")
    print("\n=== Unanswerable (must refuse) ===")
    for q in UNANSWERABLE:
        r = answer(q)
        # An API error is not a refusal: it says nothing about whether the system would have refused
        hit = not r["found"] and not is_error(r)
        ok += hit
        errors += is_error(r)
        print(f"[{'PASS' if hit else 'ERROR' if is_error(r) else 'FAIL'}] {q}\n   -> {r['answer'][:150]} {r.get('reason', '')}")
    total = len(ANSWERABLE) + len(UNANSWERABLE)
    print(f"\nScore: {ok}/{total}" + (f"  ({errors} LLM errors: rerun when the API recovers)" if errors else ""))


if __name__ == "__main__":
    main()
