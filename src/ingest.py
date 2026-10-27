"""Step 1-3: PDF -> page text -> chunks.jsonl (each chunk tagged with company, FY, PDF page).

Owner: Member A
Run:   python -m src.ingest
Page numbers are 1-based PDF page indices (what a PDF viewer shows), NOT the printed page labels.
"""
import json
import re
import pymupdf as fitz

from .config import COMPANIES, PDF_DIR, CHUNKS_PATH, CHUNK_WORDS, CHUNK_OVERLAP, FISCAL_YEAR

# Running headers / footers and navigation tabs to strip
HEADER_PATTERNS = [
    re.compile(r"^integrated annual report 2023[-–]24$", re.I),
    re.compile(r"^hcltech annual report 2023[-–]24$", re.I),
    re.compile(r"^ambitions realized\.?$", re.I),
    re.compile(r"^scale at speed\s*\|\s*.*$", re.I),
    re.compile(
        r"^(?:value creation for stakeholders|sustainability at wipro|risk management|reporting context|performance and outlook|corporate overview|statutory reports and financial statements)$",
        re.I,
    ),
]


# Shifted HCLTech text uses \x03 for space and \x0f-\x1c for ",-./0-9", plus other low codes for
# punctuation. \x07/\x08 are left out: elsewhere they are bullet glyphs, not shifted text.
HCL_SHIFTED = re.compile(r"[\x03-\x06\x0b-\x1d]")
HCL_LIGATURES = {"¿": "fi", "À": "fl", "ႇ": "ff", "ႈ": "ffi"}

# Rupee symbol extracted as a stray glyph before amounts, e.g. "D 519,955 Mn" (TechM), "C 897,603" (Wipro)
# A backtick is never part of a word, so it is replaced before any number; D/C only before amounts.
RUPEE_GLYPH = {
    "TechMahindra": re.compile(r"`\s?(?=\d)|(?<![A-Za-z0-9])D (?=\d{1,3}(?:,\d{2,3})+|\d+\.\d)"),
    "Wipro": re.compile(r"`\s?(?=\d)|(?<![A-Za-z0-9])C (?=\d{1,3}(?:,\d{2,3})+|\d+\.\d)"),
}


def decode_hcl_span(text: str) -> str:
    """Fix HCLTech embedded font encoding artifact where characters are shifted by +29."""
    decoded = []
    for c in text:
        code = ord(c)
        if code == 3:
            decoded.append(" ")
        elif c in HCL_LIGATURES:
            decoded.append(HCL_LIGATURES[c])
        elif 4 <= code <= 97:
            decoded.append(chr(code + 29))
        else:
            decoded.append(c)
    return "".join(decoded)


def extract_page_text(page, company: str) -> str:
    """Extract page text, repairing custom font-encoding if in HCLTech."""
    if company == "HCLTech":
        # Decide per line, not per page: shifted and normal text are mixed on the same page,
        # and a shifted word on its own (e.g. "1DWLRQDO" = "National") has no control chars.
        lines = []
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                spans = [s["text"] for s in l["spans"]]
                if any(HCL_SHIFTED.search(s) for s in spans):
                    spans = [decode_hcl_span(s) if s.strip() else s for s in spans]
                lines.append("".join(spans))
        return "\n".join(lines)
    text = page.get_text("text")
    if company in RUPEE_GLYPH:
        text = RUPEE_GLYPH[company].sub("₹", text)
    return text


def clean(text: str) -> str:
    # Normalise non-breaking / special spaces
    text = text.replace("\u00a0", " ").replace("\xa0", " ")
    # Bullet / tab glyphs extracted as control characters
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", " ", text)
    # Strip running headers/footers
    filtered = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or any(p.match(s) for p in HEADER_PATTERNS):
            continue
        filtered.append(line)
    text = "\n".join(filtered)
    # Collapse multiple whitespace / blank lines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_page(words, size=CHUNK_WORDS, overlap=CHUNK_OVERLAP):
    if len(words) <= size:
        yield " ".join(words)
        return
    step = size - overlap
    for start in range(0, len(words), step):
        part = words[start : start + size]
        if len(part) < 40 and start > 0:  # tiny tail already covered by overlap
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
                raw_text = extract_page_text(page, company)
                text = clean(raw_text)
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
            print(
                f"[ok] {company}: {len(doc)} pages, {n_company} chunks, {empty_pages} near-empty pages"
            )
            if empty_pages > 0.3 * len(doc):
                print(
                    f"  WARNING: many empty pages - {company} PDF may be scanned (needs OCR). Consider another company."
                )
            n_total += n_company
    print(f"Wrote {n_total} chunks -> {CHUNKS_PATH}")


if __name__ == "__main__":
    ingest()
