"""Ingestion pipeline — fetches Wikipedia articles, chunks them, and indexes into ChromaDB and BM25."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from athar.config import settings, DATA_DIR, CHROMA_DIR
from athar.ingestion.fetcher import fetch_all_articles, FetchedArticle
from athar.rag.preprocessing.chunker import (
    RecursiveCharacterTextSplitter,
    Document,
    clean_text,
)
from athar.rag.retrieval.bm25_retriever import BM25Retriever
from athar.rag.retrieval.semantic import SemanticRetriever

logger = logging.getLogger(__name__)

BM25_INDEX_PATH = CHROMA_DIR / "bm25_index.pkl"
METADATA_PATH = DATA_DIR / "ingestion_metadata.json"


def run_ingestion(
    topics: list[str] | None = None,
    max_articles: int | None = None,
    overwrite: bool = False,
    include_met: bool = True,
    met_max_per_dept: int = 20,
) -> dict:
    """
    Full multi-source ingestion pipeline:
      1. Fetch Wikipedia articles + Met Museum artworks
      2. Save raw JSON to data/raw/
      3. Chunk with RecursiveCharacterTextSplitter
      4. Index into ChromaDB (semantic, ONNX embeddings)
      5. Build BM25 index
      6. Save ingestion metadata

    Args:
        topics: Wikipedia titles (None = all defaults).
        max_articles: Max Wikipedia articles.
        overwrite: Drop existing vectors and rebuild.
        include_met: Include Met Museum API data.
        met_max_per_dept: Max artworks per Met department.
    """
    start = time.time()
    max_articles = max_articles or settings.max_wikipedia_articles

    logger.info("Starting ingestion pipeline")

    # 1. Fetch
    articles = fetch_all_articles(
        topics=topics,
        max_articles=max_articles,
        include_met=include_met and (topics is None),
        met_max_per_dept=met_max_per_dept,
    )
    if not articles:
        return {"success": False, "message": "No articles fetched.", "articles_fetched": 0,
                "chunks_created": 0, "duration_seconds": 0.0}

    # 2. Save raw JSON
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _save_raw_json(articles)

    # 3. Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    all_documents: list[Document] = []
    for article in articles:
        # For Met Museum objects, use content as-is (already structured)
        # For Wikipedia, clean Wikipedia markup
        if article.source == "wikipedia":
            text = clean_text(article.content)
        else:
            text = article.content

        # Merge article-level metadata into chunk metadata
        chunk_meta = {
            "title": article.title,
            "url": article.url,
            "summary": article.summary[:200],
            "source": article.source,
            "ingested_at": datetime.utcnow().isoformat(),
            **article.metadata,  # category, culture, period, artist, etc.
        }

        docs = splitter.create_documents(
            texts=[text],
            metadatas=[chunk_meta],
        )
        all_documents.extend(docs)

    logger.info(
        "Chunked %d articles -> %d chunks (size=%d, overlap=%d)",
        len(articles),
        len(all_documents),
        settings.chunk_size,
        settings.chunk_overlap,
    )

    # 4. Semantic indexing.  The retriever owns the embedding profile and
    # persists all vectors under the repository-level Chroma directory.
    semantic = SemanticRetriever()
    semantic.initialize(reset_incompatible=overwrite)

    if overwrite:
        logger.info("Overwrite=True — resetting ChromaDB collection")
        semantic.reset_collection()

    added_semantic = semantic.add_documents(all_documents)

    # 5. Rebuild BM25 from the complete persisted corpus, not merely this
    # ingestion batch.  This keeps incremental ingestion and semantic search
    # in sync.
    bm25 = BM25Retriever()
    bm25.build_index(semantic.get_all_documents())
    bm25.save(BM25_INDEX_PATH)

    # 6. Save metadata
    duration = time.time() - start
    wiki_count = sum(1 for a in articles if a.source == "wikipedia")
    met_count = sum(1 for a in articles if a.source == "met_museum")

    metadata = {
        "last_ingested": datetime.utcnow().isoformat(),
        "articles_fetched": len(articles),
        "wikipedia_articles": wiki_count,
        "met_museum_objects": met_count,
        "chunks_created": len(all_documents),
        "chunks_indexed": added_semantic,
        "duration_seconds": round(duration, 1),
        "topics": [a.title for a in articles if a.source == "wikipedia"],
        "settings": {
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "embedding_model": semantic.embedding_profile,
        },
    }
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    logger.info(
        "Ingestion complete in %.1fs — %d articles, %d chunks",
        duration,
        len(articles),
        len(all_documents),
    )

    return {
        "success": True,
        "articles_fetched": len(articles),
        "chunks_created": len(all_documents),
        "duration_seconds": round(duration, 1),
        "message": (
            f"Ingested {wiki_count} Wikipedia articles + {met_count} Met Museum objects "
            f"into {len(all_documents)} chunks."
        ),
    }


def get_ingestion_metadata() -> dict | None:
    """Return metadata from the last ingestion run."""
    if METADATA_PATH.exists():
        return json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return None


def _save_raw_json(articles: list[FetchedArticle]) -> None:
    for article in articles:
        safe_name = article.title.replace(" ", "_").replace("/", "_")[:60]
        path = DATA_DIR / f"{article.source}_{safe_name}.json"
        data = {
            "title": article.title,
            "url": article.url,
            "summary": article.summary,
            "source": article.source,
            "text": article.content,
            "metadata": article.metadata,
            "fetched_at": datetime.utcnow().isoformat(),
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
