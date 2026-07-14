"""Small, dependency-free retrieval evaluation utilities.

The evaluation set intentionally measures retrieval, not generation.  This
makes regressions in chunking, indexing, or ranking visible without an LLM
judge and gives the project a reproducible CV-ready quality signal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from athar.models.schemas import RetrievedChunk


@dataclass(frozen=True)
class RetrievalCase:
    question: str
    expected_titles: tuple[str, ...]


class Retriever(Protocol):
    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        """Retrieve ranked chunks for an evaluation query."""


DEFAULT_EVALUATION_SET: tuple[RetrievalCase, ...] = (
    RetrievalCase("What was the House of Wisdom?", ("House of Wisdom",)),
    RetrievalCase("Why is Al-Khwarizmi important to algebra?", ("Al-Khwarizmi",)),
    RetrievalCase("What makes the Alhambra distinctive?", ("Alhambra",)),
    RetrievalCase("Who wrote the Muqaddimah?", ("Ibn Khaldun",)),
    RetrievalCase("What is the significance of the Dome of the Rock?", ("Dome of the Rock",)),
)


def evaluate_retrieval(
    retriever: Retriever,
    cases: tuple[RetrievalCase, ...] = DEFAULT_EVALUATION_SET,
    top_k: int = 5,
) -> dict[str, object]:
    """Compute hit-rate@k and mean reciprocal rank for title-level relevance."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    results: list[dict[str, object]] = []
    reciprocal_ranks: list[float] = []
    hits = 0

    for case in cases:
        chunks = retriever.retrieve(case.question, top_k=top_k)
        titles = [str(chunk.metadata.get("title", "")) for chunk in chunks]
        rank = _first_matching_rank(titles, case.expected_titles)
        if rank is not None:
            hits += 1
            reciprocal_ranks.append(1 / rank)
        else:
            reciprocal_ranks.append(0.0)
        results.append(
            {
                "question": case.question,
                "expected_titles": list(case.expected_titles),
                "retrieved_titles": titles,
                "first_relevant_rank": rank,
            }
        )

    total = len(cases)
    return {
        "cases": total,
        "top_k": top_k,
        "hit_rate_at_k": round(hits / total, 3) if total else 0.0,
        "mrr": round(sum(reciprocal_ranks) / total, 3) if total else 0.0,
        "results": results,
    }


def _first_matching_rank(titles: list[str], expected_titles: tuple[str, ...]) -> int | None:
    normalized_expected = {_normalize(title) for title in expected_titles}
    for index, title in enumerate(titles, start=1):
        normalized_title = _normalize(title)
        if any(expected in normalized_title for expected in normalized_expected):
            return index
    return None


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())
