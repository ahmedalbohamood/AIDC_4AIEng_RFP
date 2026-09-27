"""Semantic similarity for free-text grading, as an alternative to string fuzzy-match.

rapidfuzz's token_set_ratio measures lexical overlap: it rewards shared words and
penalizes paraphrase, regardless of whether the paraphrase preserves the actual
fact. A model that writes "Bonfire Portal at https://usask.bonfirehub.ca" against
ground truth "Online Bonfire Portal at https://usask.bonfirehub.ca; submissions by
any other method... will not be accepted" is stating the same submission method
correctly and concisely - fuzzy match scores that ~55 (partial/wrong); a reader
would call it correct.

Embeddings compare meaning instead of tokens, so a concise correct paraphrase and a
verbose ground-truth sentence land close in vector space even with low word
overlap - while a genuinely different or fabricated answer does not, regardless of
surface similarity. This does NOT replace the present/absent hallucination check
(unaffected - that's exact boolean logic) or list/table item matching (left on
fuzzy match, which is designed for many short items rather than a full sentence).
It only replaces the free-text scoring branch's threshold logic.

Caching: identical (text) pairs recur constantly across backends re-answering the
same ground-truth value, so every embedding is cached to disk by its exact string,
keyed by model name - a rerun of grade.py after this file exists costs nothing.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

CACHE_PATH = Path(__file__).parent.parent / ".embedding_cache.json"
MODEL = "text-embedding-3-small"

_cache: dict[str, list[float]] | None = None
_client = None


def _load_cache() -> dict:
    global _cache
    if _cache is None:
        if CACHE_PATH.exists():
            _cache = json.loads(CACHE_PATH.read_text())
        else:
            _cache = {}
    return _cache


def _save_cache() -> None:
    CACHE_PATH.write_text(json.dumps(_cache))


def _key(text: str) -> str:
    return hashlib.sha256(f"{MODEL}:{text}".encode()).hexdigest()


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def embed(text: str) -> list[float]:
    text = text.strip()
    if not text:
        return [0.0]
    cache = _load_cache()
    k = _key(text)
    if k in cache:
        return cache[k]
    resp = _get_client().embeddings.create(model=MODEL, input=text)
    vec = resp.data[0].embedding
    cache[k] = vec
    _save_cache()
    return vec


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def semantic_similarity(text_a: str, text_b: str) -> float:
    """Cosine similarity in [0, 1] (embeddings are near-unit-norm, so this is
    effectively already 0-1 in practice for real text, but clamp defensively)."""
    sim = cosine(embed(text_a), embed(text_b))
    return max(0.0, min(1.0, sim))
