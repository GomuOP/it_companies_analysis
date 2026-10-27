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

FISCAL_YEAR = "FY2023-24"

# file name in data/pdfs  ->  display name + aliases used to detect the company in a question
COMPANIES = {
    "TechMahindra": {"file": "techmahindra_fy24.pdf", "aliases": ["tech mahindra", "techmahindra", "techm", "tech m", "mahindra"]},
    "Wipro":        {"file": "wipro_fy24.pdf",        "aliases": ["wipro"]},
    "HCLTech":      {"file": "hcltech_fy24.pdf",      "aliases": ["hcl", "hcltech", "hcl tech", "hcl technologies"]},
}

# chunking
CHUNK_WORDS = 300          # ~430 tokens; bge-small truncates at 512
CHUNK_OVERLAP = 50

# retrieval
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
TOP_K = 6                  # total chunks sent to the LLM
TOP_K_PER_COMPANY = 5      # per company when a question covers several companies (comparisons)
MIN_SCORE = 0.62           # relevance gate: answerable eval questions score 0.65-0.79, off-topic ~0.59

# LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
# Tried in order when the main model is overloaded (503), rate-limited or times out
GEMINI_FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.8-flash"]
GEMINI_TIMEOUT_S = 60

NOT_FOUND = "Not found in the reports."
