"""Step 5: hybrid retrieval (BM25 + vector, reciprocal-rank fusion) + company filter.

Owner: Member B
Quick test: python -m src.retrieve "What was Wipro attrition?"
"""
import pickle
import sys
from functools import lru_cache
import numpy as np

from .config import (COMPANIES, INDEX_DIR, EMBED_MODEL, BGE_QUERY_PREFIX,
                     TOP_K, TOP_K_PER_COMPANY)
from .index import load_chunks, tokenize


@lru_cache(maxsize=1)
def _load():
    from sentence_transformers import SentenceTransformer
    chunks = load_chunks()
    with open(INDEX_DIR / "bm25.pkl", "rb") as f:
        bm25 = pickle.load(f)
    emb = np.load(INDEX_DIR / "embeddings.npy")
    model = SentenceTransformer(EMBED_MODEL)
    return chunks, bm25, emb, model


def detect_companies(question: str):
    q = question.lower()
    return [name for name, m in COMPANIES.items() if any(a in q for a in m["aliases"])]


def _rrf(rank_lists, k=60):
    scores = {}
    for ranks in rank_lists:
        for r, idx in enumerate(ranks):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + r + 1)
    return sorted(scores, key=scores.get, reverse=True)


def search(question: str):
    """Returns list of chunk dicts with 'cosine' (for the relevance gate) and 'rank'."""
    chunks, bm25, emb, model = _load()
    qv = model.encode([BGE_QUERY_PREFIX + question], normalize_embeddings=True)[0]
    cos = emb @ qv
    bm = bm25.get_scores(tokenize(question))

    named = detect_companies(question)
    targets = named if named else list(COMPANIES)
    per_company = TOP_K if len(targets) == 1 else (TOP_K_PER_COMPANY if not named else max(2, TOP_K // len(targets)))

    results = []
    for comp in targets:
        idx = np.array([i for i, c in enumerate(chunks) if c["company"] == comp])
        if len(idx) == 0:
            continue
        by_vec = idx[np.argsort(-cos[idx])][:50].tolist()
        by_bm = idx[np.argsort(-bm[idx])][:50].tolist()
        for i in _rrf([by_vec, by_bm])[:per_company]:
            results.append({**chunks[i], "cosine": float(cos[i])})
    results.sort(key=lambda c: c["cosine"], reverse=True)
    return results


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What was the attrition rate?"
    for c in search(q):
        print(f"{c['cosine']:.3f}  {c['company']:12s} p.{c['page']:<4d} {c['text'][:110]}...")
