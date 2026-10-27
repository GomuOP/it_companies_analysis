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


STOPWORDS = {"what", "was", "were", "is", "are", "the", "a", "an", "of", "in", "for", "to", "and", "s", "did",
             "does", "do", "how", "many", "much", "which", "at", "on", "by", "its", "their", "as", "end", "year",
             "compare", "comparison", "between", "versus", "vs", "all", "three", "companies", "company", "each"}


# Reports use different words for the same metric (e.g. Wipro: "sales", HCLTech: "headcount")
SYNONYMS = {"revenue": ["revenues", "sales", "operations", "consolidated"], "headcount": ["employees"],
            "employees": ["headcount"], "employee": ["headcount", "employees"]}


def query_tokens(question: str):
    """BM25 query terms: drop filler words, add synonyms; reports write FY2023-24 as FY24."""
    toks = [t for t in tokenize(question) if t not in STOPWORDS]
    toks += [s for t in toks for s in SYNONYMS.get(t, [])]
    # Every report covers FY2023-24, so the year terms are always added (most questions omit the year)
    toks += ["fy24", "2023", "24"]
    return toks


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
    named = detect_companies(question)
    # Company names are noise for BM25 here: results are already filtered by company below
    alias_toks = {t for n in named for a in COMPANIES[n]["aliases"] for t in tokenize(a)}
    bm = bm25.get_scores([t for t in query_tokens(question) if t not in alias_toks])

    targets = named if named else list(COMPANIES)
    per_company = TOP_K if len(targets) == 1 else TOP_K_PER_COMPANY

    results = []
    for comp in targets:
        idx = np.array([i for i, c in enumerate(chunks) if c["company"] == comp])
        if len(idx) == 0:
            continue
        by_vec = idx[np.argsort(-cos[idx])][:50].tolist()
        by_bm = idx[np.argsort(-bm[idx])][:50].tolist()
        # Half the slots go to the top BM25 hits: number-heavy pages (KPI tables, highlights) rank
        # high on keywords but low on vectors, and plain RRF pushed them out. The rest is filled by RRF.
        # (Comparisons keep only 1 such slot: generic metric words like "revenue" match many note tables.)
        picked = by_bm[:(per_company + 1) // 2 if len(targets) == 1 else 1]
        for i in _rrf([by_vec, by_bm]):
            if len(picked) >= per_company:
                break
            if i not in picked:
                picked.append(i)
        for i in picked:
            results.append({**chunks[i], "cosine": float(cos[i])})
    results.sort(key=lambda c: c["cosine"], reverse=True)
    return results


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What was the attrition rate?"
    for c in search(q):
        print(f"{c['cosine']:.3f}  {c['company']:12s} p.{c['page']:<4d} {c['text'][:110]}...")
