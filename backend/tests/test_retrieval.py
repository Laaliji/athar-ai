"""Tests for the retrieval components."""

from __future__ import annotations

import pytest

from athar.rag.preprocessing.chunker import (
    Document,
    RecursiveCharacterTextSplitter,
    clean_text,
)
from athar.rag.retrieval.bm25_retriever import BM25Retriever, _tokenize
from athar.rag.retrieval.hybrid import _deduplicate_sources
from athar.models.schemas import RetrievedChunk


# ── Chunker Tests ─────────────────────────────────────────────────────────────

class TestRecursiveCharacterTextSplitter:

    def test_basic_split(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        text = "This is a sentence. " * 20
        chunks = splitter.split_text(text)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 150  # Allow some slack for overlap

    def test_respects_paragraphs(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=30, chunk_overlap=0)
        text = "Paragraph one text here.\n\nParagraph two text here.\n\nParagraph three text here."
        chunks = splitter.split_text(text)
        # Should split at paragraphs (each ~25 chars < chunk_size=30, but total > 30)
        assert len(chunks) >= 2

    def test_empty_text(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
        chunks = splitter.split_text("")
        assert chunks == []

    def test_short_text_no_split(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        text = "This is a short text."
        chunks = splitter.split_text(text)
        assert len(chunks) == 1
        assert chunks[0].strip() == text

    def test_create_documents_with_metadata(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=0)
        texts = ["Hello world. " * 10]
        metas = [{"title": "Test", "url": "http://example.com"}]
        docs = splitter.create_documents(texts, metas)
        assert len(docs) > 0
        for doc in docs:
            assert doc.metadata["title"] == "Test"
            assert "chunk_index" in doc.metadata

    def test_overlap_creates_continuity(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=50)
        text = "A" * 200
        chunks = splitter.split_text(text)
        # With overlap, chunks should share content
        assert len(chunks) >= 2


class TestCleanText:

    def test_removes_citations(self):
        text = "This is important.[1] More text.[23]"
        cleaned = clean_text(text)
        assert "[1]" not in cleaned
        assert "[23]" not in cleaned

    def test_normalizes_whitespace(self):
        text = "Text\n\n\n\nMore text"
        cleaned = clean_text(text)
        assert "\n\n\n" not in cleaned


# ── BM25 Tests ────────────────────────────────────────────────────────────────

class TestBM25Retriever:

    @pytest.fixture
    def bm25_with_docs(self):
        docs = [
            Document(
                content="The House of Wisdom was a major intellectual center in Baghdad.",
                metadata={"title": "House of Wisdom"},
            ),
            Document(
                content="The Alhambra is a palace and fortress complex in Granada, Spain.",
                metadata={"title": "Alhambra"},
            ),
            Document(
                content="Ibn Khaldun was a medieval Islamic historian and philosopher.",
                metadata={"title": "Ibn Khaldun"},
            ),
            Document(
                content="Islamic mathematics advanced algebra and developed new number systems.",
                metadata={"title": "Islamic Mathematics"},
            ),
        ]
        retriever = BM25Retriever()
        retriever.build_index(docs)
        return retriever

    def test_retriever_is_ready(self, bm25_with_docs):
        assert bm25_with_docs.is_ready

    def test_relevant_query(self, bm25_with_docs):
        results = bm25_with_docs.retrieve("House of Wisdom Baghdad", k=2)
        assert len(results) > 0
        # The first result should be about House of Wisdom
        top_title = results[0].metadata.get("title")
        assert top_title == "House of Wisdom"

    def test_scores_normalized(self, bm25_with_docs):
        results = bm25_with_docs.retrieve("Islamic history", k=4)
        for r in results:
            assert 0.0 <= r.bm25_score <= 1.0

    def test_empty_query(self, bm25_with_docs):
        results = bm25_with_docs.retrieve("the and or", k=3)
        # All words are stopwords — should return empty or very low scores
        assert isinstance(results, list)

    def test_top_k_limit(self, bm25_with_docs):
        results = bm25_with_docs.retrieve("Islamic knowledge", k=2)
        assert len(results) <= 2

    def test_empty_index(self):
        retriever = BM25Retriever()
        assert not retriever.is_ready
        results = retriever.retrieve("anything")
        assert results == []


class TestTokenizer:

    def test_lowercase(self):
        tokens = _tokenize("Hello WORLD")
        assert "hello" in tokens
        assert "world" in tokens

    def test_removes_stopwords(self):
        tokens = _tokenize("the quick brown fox")
        assert "the" not in tokens

    def test_removes_punctuation(self):
        tokens = _tokenize("hello, world! This is great.")
        assert "hello" in tokens
        assert "world" in tokens

    def test_empty_string(self):
        assert _tokenize("") == []


def test_source_scores_handle_negative_cross_encoder_logits():
    sources = _deduplicate_sources(
        [
            RetrievedChunk(
                content="A source passage",
                metadata={"title": "Source", "url": "https://example.test"},
                hybrid_score=0.8,
                rerank_score=-4.0,
            )
        ]
    )

    assert 0.0 <= sources[0].score <= 1.0
