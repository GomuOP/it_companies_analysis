# Failed attempts log

Log every attempt that didn't work, along with what you changed. This file is part of the submission.

| Time | Who | What we tried | What went wrong | What we changed |
|---|---|---|---|---|
| 13:03 | A | `page.get_text("blocks", sort=True)` on multi-column pages | Infographic pages (e.g. Wipro p. 31) produced fragmented vertical character runs and garbled text | Retained line-based `page.get_text("text")` with targeted pattern cleaning |
| 13:07 | A | Frequency-threshold stopline stripping (>8% of pages) | Stripped essential recurring financial table labels ("Total", "Particulars", "March 31, 2024", numbers) | Replaced with regex filtering targeting only document headers/footers and slogans |
| 13:10 | A | Direct text extraction on HCLTech PDF | Over 180 pages of financial statements and notes had shifted font encoding (+29 offset), yielding unsearchable characters | Implemented selective `decode_hcl_span()` in `ingest.py` to restore clean ASCII text and ligatures |
| 13:17 | A | Direct pickle save in `src.index` without ensuring directory | Crashed with `FileNotFoundError` if `data/index/` directory did not already exist | Added `INDEX_DIR.mkdir(parents=True, exist_ok=True)` in `src/index.py` |
