"""
Cross-encoder reranker for post-retrieval scoring.

After BM25+semantic retrieval returns candidate chunks, the reranker
scores each (query, chunk) pair jointly using a cross-encoder model.
This is significantly more accurate than bi-encoder similarity alone.

Model: ms-marco-MiniLM-L-6-v2
- Size: ~80MB
- Latency: ~10ms per (query, chunk) pair on CPU
- Trained on MS-MARCO passage ranking (350M query-passage pairs)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from athar.models.schemas import RetrievedChunk

logger = logging.getLogger(__name__)

# Cross-encoder model — lightweight MS-MARCO model, runs well on CPU
_CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_reranker = None
_reranker_available = False


def _load_reranker():
    """Lazy-load the cross-encoder model."""
    global _reranker, _reranker_available
    if _reranker is not None:
        return _reranker

    try:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder(_CROSS_ENCODER_MODEL)
        _reranker_available = True
        logger.info("Cross-encoder reranker loaded: %s", _CROSS_ENCODER_MODEL)
    except Exception as e:
        logger.warning(
            "Cross-encoder unavailable (%s) — falling back to hybrid scores only.", e
        )
        _reranker_available = False
        _reranker = None

    return _reranker


def rerank(
    query: str,
    chunks: list["RetrievedChunk"],
    top_k: int | None = None,
) -> list["RetrievedChunk"]:
    """
    Rerank chunks using a cross-encoder model.

    The cross-encoder reads the full (query, chunk) pair together,
    giving much more accurate relevance scores than the first-pass
    bi-encoder/BM25 retrieval.

    Falls back gracefully to the original order if the model is unavailable.

    Args:
        query: The user's question.
        chunks: Candidate chunks from hybrid retrieval.
        top_k: How many to return after reranking (None = all).

    Returns:
        Chunks sorted by reranker score, highest first.
    """
    if not chunks:
        return chunks

    reranker = _load_reranker()
    if reranker is None or not _reranker_available:
        # Graceful fallback — just return in hybrid score order
        return sorted(chunks, key=lambda c: c.hybrid_score, reverse=True)[:top_k or len(chunks)]

    try:
        pairs = [(query, chunk.content) for chunk in chunks]
        scores = reranker.predict(pairs)

        # Attach reranker score to each chunk
        for chunk, score in zip(chunks, scores):
            chunk.rerank_score = float(score)

        reranked = sorted(chunks, key=lambda c: c.rerank_score, reverse=True)

        if top_k:
            reranked = reranked[:top_k]

        logger.debug(
            "Reranked %d chunks -> top %d | top score: %.3f",
            len(chunks),
            len(reranked),
            reranked[0].rerank_score if reranked else 0,
        )
        return reranked

    except Exception as e:
        logger.warning("Reranking failed: %s — using hybrid scores.", e)
        return sorted(chunks, key=lambda c: c.hybrid_score, reverse=True)[:top_k or len(chunks)]


def is_available() -> bool:
    """Return True if the cross-encoder is loaded and ready."""
    return _reranker_available
