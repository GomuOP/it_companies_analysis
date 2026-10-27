"""Step 4: build BM25 + vector indexes from chunks.jsonl.

Owner: Member A
Run:   python -m src.index
"""
import json
import pickle
import re
import numpy as np
from rank_bm25 import BM25Okapi

from .config import CHUNKS_PATH, INDEX_DIR, EMBED_MODEL


def tokenize(text: str):
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())


def load_chunks():
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def build():
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks")

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])
    with open(INDEX_DIR / "bm25.pkl", "wb") as f:
        pickle.dump(bm25, f)
    print("BM25 index built")

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL)
    emb = model.encode([c["text"] for c in chunks], batch_size=32,
                       normalize_embeddings=True, show_progress_bar=True)
    np.save(INDEX_DIR / "embeddings.npy", emb.astype(np.float32))
    print(f"Embeddings saved: {emb.shape}")


if __name__ == "__main__":
    build()
