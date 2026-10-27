# REPORT (keep to about 300 words)

**1. Approach.** Retrieval-augmented Q&A over three FY2023-24 annual reports (Tech Mahindra, Wipro, HCLTech). Chunks are tagged by page, retrieved with hybrid search, and answered by Gemini using only the retrieved context. Refusals happen at three points (relevance gate, the LLM's own "not found", and citation validation). The comparison chart reads hand-verified metrics, and each value carries its source page, exact quote and definition.

**2. Tools, models, libraries.** Python, PyMuPDF, rank_bm25, sentence-transformers (bge-small-en-v1.5, CPU), Gemini (gemini-3.6-flash, falling back to 3.5-flash / 3.8-flash) via google-genai, Streamlit, Plotly.

**3. Constraints.** 6.5-hour build; reports of 364-556 pages with multi-column layouts, infographics and tables; HCLTech's financial statements use a shifted font encoding; no data allowed from outside the reports.

**4. Assumptions.** All three reports cover FY2023-24 (April 2023 to March 2024); chart figures are consolidated; citations use the 1-based PDF page index, not printed page labels; metric definitions differ between companies (e.g. EBIT margin vs IT Services operating margin) and are shown next to each value rather than normalised.

**5. Top 5 design decisions.**
1. Page-level metadata on every chunk, so every answer can cite a page.
2. Hybrid BM25 and vector retrieval: BM25 catches exact financial terms, vectors catch paraphrases.
3. Three-layer refusal, to prefer "not found" over guessing.
4. Human-verified chart values with page, quote and definition, so the chart is fully traceable.
5. A minimal stack (no vector DB or framework), so we could finish and explain every component.

**6. AI-assistant use.** Claude was used for the architecture, code scaffold and debugging; every module was tested by running it, and every chart value was checked on its cited PDF page.

**7. Prior work referred to.** RAG pattern (Lewis et al., 2020); reciprocal-rank fusion (Cormack et al., 2009); BGE embeddings (BAAI).

**8. Failed attempts.** Block-based extraction garbled infographic pages, so we kept line-based extraction with targeted header cleaning. Frequency-based header stripping removed real table labels, so we switched to regex rules. HCLTech's shifted font encoding made 180+ pages unsearchable until we decoded it. Full list in FAILED.md.
