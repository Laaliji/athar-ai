"""Regression tests for the restart-safe embedding fallback."""

from athar.rag.preprocessing.chunker import Document
from athar.rag.retrieval.semantic import HashingEmbeddingFunction, _document_id


def test_hashing_embeddings_are_stable_across_instances():
    text = "The House of Wisdom was an intellectual centre in Baghdad."

    first = HashingEmbeddingFunction()([text])[0]
    second = HashingEmbeddingFunction()([text])[0]

    assert first == second
    assert len(first) == HashingEmbeddingFunction.DIM


def test_document_ids_do_not_collide_for_different_sources():
    first = Document(
        content="same text",
        metadata={"source": "wikipedia", "url": "https://a", "title": "A", "chunk_index": 0},
    )
    second = Document(
        content="same text",
        metadata={"source": "wikipedia", "url": "https://b", "title": "A", "chunk_index": 0},
    )

    assert _document_id(first) != _document_id(second)
