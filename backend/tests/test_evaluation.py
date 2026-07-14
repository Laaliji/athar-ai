"""Tests for deterministic retrieval evaluation metrics."""

from athar.evaluation import RetrievalCase, evaluate_retrieval
from athar.models.schemas import RetrievedChunk


class FakeRetriever:
    def __init__(self, results):
        self.results = results

    def retrieve(self, query, top_k=None):
        return self.results[query][:top_k]


def test_evaluation_calculates_hit_rate_and_mrr():
    cases = (
        RetrievalCase("first", ("House of Wisdom",)),
        RetrievalCase("second", ("Alhambra",)),
    )
    retriever = FakeRetriever(
        {
            "first": [
                RetrievedChunk(content="x", metadata={"title": "Other"}),
                RetrievedChunk(content="x", metadata={"title": "House of Wisdom"}),
            ],
            "second": [RetrievedChunk(content="x", metadata={"title": "Alhambra Palace"})],
        }
    )

    metrics = evaluate_retrieval(retriever, cases, top_k=3)

    assert metrics["hit_rate_at_k"] == 1.0
    assert metrics["mrr"] == 0.75
    assert metrics["results"][0]["first_relevant_rank"] == 2


def test_evaluation_rejects_invalid_top_k():
    try:
        evaluate_retrieval(FakeRetriever({}), (), top_k=0)
    except ValueError as error:
        assert "top_k" in str(error)
    else:
        raise AssertionError("Expected invalid top_k to fail")
