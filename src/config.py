"""Central configuration. Change company list / thresholds here only."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PDF_DIR = DATA / "pdfs"
INDEX_DIR = DATA / "index"
CHUNKS_PATH = DATA / "chunks.jsonl"
METRICS_PATH = DATA / "metrics.json"

FISCAL_YEAR = "FY2025-26"

# file name in data/pdfs  ->  display name + aliases used to detect the company in a question
COMPANIES = {
    "TCS":     {"file": "tcs_fy26.pdf",     "aliases": ["tcs", "tata consultancy"]},
    "Infosys": {"file": "infosys_fy26.pdf", "aliases": ["infosys", "infy"]},
    "HCLTech": {"file": "hcltech_fy26.pdf", "aliases": ["hcl", "hcltech", "hcl tech", "hcl technologies"]},
}

# chunking
CHUNK_WORDS = 400          # ~550-600 tokens
CHUNK_OVERLAP = 60

# retrieval
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
TOP_K = 6                  # total chunks sent to the LLM
TOP_K_PER_COMPANY = 3      # used when no company is named (comparison questions)
MIN_SCORE = 0.55           # relevance gate on best cosine similarity - TUNE with eval.py

# LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

NOT_FOUND = "Not found in the reports."
