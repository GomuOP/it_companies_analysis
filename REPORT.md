# REPORT (keep to about 300 words)

**1. Approach.** Retrieval-augmented Q&A over three FY2023-24 annual reports (Tech Mahindra, Wipro, HCLTech). Chunks are tagged by page, retrieved with hybrid search, and answered by Gemini using only the retrieved context. Refusals happen at three points (relevance gate, the LLM's own "not found", and citation validation). The comparison chart reads hand-verified metrics, and each value carries its source page and quote.

**2. Tools, models, libraries.** Python, PyMuPDF, rank_bm25, sentence-transformers (bge-small-en-v1.5), Gemini (_model_) via google-genai, Streamlit, Plotly.

**3. Constraints.** 6.5-hour build; reports of 300+ pages with multi-column layouts and tables; no data allowed from outside the reports.

**4. Assumptions.** All three reports cover FY2023-24 (April 2023 to March 2024) under Ind AS; figures are consolidated; citations use the PDF page index; _add_.

**5. Top 5 design decisions.**
1. Page-level metadata on every chunk, so every answer can cite a page.
2. Hybrid BM25 and vector retrieval: BM25 catches exact financial terms, vectors catch paraphrases.
3. Three-layer refusal, to prefer "not found" over guessing.
4. LLM-proposed but human-verified chart values, so the chart is fully traceable.
5. A minimal stack (no vector DB or framework), so we could finish and explain every component.

**6. AI-assistant use.** _e.g. Claude was used for the architecture and code scaffold; every module was tested by running it and checking the cited pages manually._

**7. Prior work referred to.** RAG pattern (Lewis et al., 2020); reciprocal-rank fusion (Cormack et al., 2009); BGE embeddings (BAAI).

**8. Failed attempts.** _Summarise the main ones from FAILED.md._
