"""Step 1-3: PDF -> page text -> chunks.jsonl (each chunk tagged with company, FY, PDF page).

Owner: Member A
Run:   python -m src.ingest
Page numbers are 1-based PDF page indices (what a PDF viewer shows), NOT the printed page labels.
"""
import json
import re
import pymupdf as fitz

from .config import COMPANIES, PDF_DIR, CHUNKS_PATH, CHUNK_WORDS, CHUNK_OVERLAP, FISCAL_YEAR


def clean(text: str) -> str:
    text = text.replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def chunk_page(words, size=CHUNK_WORDS, overlap=CHUNK_OVERLAP):
    if len(words) <= size:
        yield " ".join(words)
        return
    step = size - overlap
    for start in range(0, len(words), step):
        part = words[start:start + size]
        if len(part) < 40 and start > 0:   # tiny tail already covered by overlap
            break
        yield " ".join(part)


def ingest():
    n_total = 0
    with open(CHUNKS_PATH, "w", encoding="utf-8") as out:
        for company, meta in COMPANIES.items():
            path = PDF_DIR / meta["file"]
            if not path.exists():
                print(f"[skip] {company}: {path} not found")
                continue
            doc = fitz.open(path)
            n_company, empty_pages = 0, 0
            for i, page in enumerate(doc):
                text = clean(page.get_text("text"))
                if len(text) < 50:
                    empty_pages += 1
                    continue
                for j, chunk in enumerate(chunk_page(text.split())):
                    rec = {
                        "id": f"{company}-p{i + 1}-c{j}",
                        "company": company,
                        "fy": FISCAL_YEAR,
                        "page": i + 1,
                        "text": chunk,
                    }
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n_company += 1
            print(f"[ok] {company}: {len(doc)} pages, {n_company} chunks, {empty_pages} near-empty pages")
            if empty_pages > 0.3 * len(doc):
                print(f"  WARNING: many empty pages - {company} PDF may be scanned (needs OCR). Consider another company.")
            n_total += n_company
    print(f"Wrote {n_total} chunks -> {CHUNKS_PATH}")


if __name__ == "__main__":
    ingest()
