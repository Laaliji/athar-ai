"""
Admin routes — knowledge base management, metrics, and re-ingestion.
"""

from __future__ import annotations

import logging
from threading import Lock

from fastapi import APIRouter, BackgroundTasks, HTTPException

from athar.ingestion.ingest import get_ingestion_metadata, run_ingestion
from athar.models.schemas import IngestRequest, IngestResponse, KnowledgeBaseStats, SystemMetrics
from athar.rag.pipeline import pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Track if ingestion is running (prevent concurrent runs)
_ingestion_running = False
_ingestion_lock = Lock()


@router.get("/metrics", response_model=SystemMetrics)
async def get_metrics() -> SystemMetrics:
    """Return real-time query performance metrics."""
    return pipeline.get_metrics()


@router.get("/kb/stats", response_model=KnowledgeBaseStats)
async def get_kb_stats() -> KnowledgeBaseStats:
    """Return knowledge base statistics."""
    meta = get_ingestion_metadata()
    chroma_meta = pipeline.semantic.get_collection_metadata()

    return KnowledgeBaseStats(
        total_documents=meta.get("articles_fetched", 0) if meta else 0,
        total_chunks=chroma_meta.get("count", pipeline.semantic.count()),
        collection_name=chroma_meta.get("name", "islamic_heritage"),
        embedding_model=chroma_meta.get("embedding_model", "unknown"),
        last_ingested=meta.get("last_ingested") if meta else None,
        topics=meta.get("topics", [])[:20] if meta else [],  # First 20 topics
    )


@router.post("/ingest", response_model=IngestResponse)
async def trigger_ingestion(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
) -> IngestResponse:
    """
    Trigger knowledge base re-ingestion in the background.

    This fetches fresh Wikipedia articles and rebuilds both
    the ChromaDB semantic index and BM25 keyword index.
    """
    global _ingestion_running

    with _ingestion_lock:
        if _ingestion_running:
            raise HTTPException(
                status_code=409,
                detail="Ingestion already running. Please wait for it to complete.",
            )
        # Mark it before scheduling the task so concurrent requests cannot
        # both pass the check before the worker begins.
        _ingestion_running = True

    def run():
        global _ingestion_running
        try:
            result = run_ingestion(
                topics=request.topics,
                max_articles=request.max_articles,
                overwrite=request.overwrite,
            )
            # Reload BM25 after ingestion
            from athar.config import CHROMA_DIR
            from athar.rag.retrieval.bm25_retriever import BM25Retriever
            bm25_path = CHROMA_DIR / "bm25_index.pkl"
            if bm25_path.exists():
                pipeline.bm25.load(bm25_path)
            logger.info("Post-ingestion BM25 reload complete.")
        except Exception:
            logger.exception("Background ingestion failed")
        finally:
            with _ingestion_lock:
                _ingestion_running = False

    background_tasks.add_task(run)

    return IngestResponse(
        success=True,
        articles_fetched=0,  # Actual count in background
        chunks_created=0,
        message="Ingestion started in background. Check /api/admin/kb/stats for progress.",
        duration_seconds=0,
    )


@router.get("/ingest/status")
async def get_ingestion_status() -> dict:
    """Check if ingestion is currently running."""
    return {
        "running": _ingestion_running,
        "chunks_indexed": pipeline.semantic.count(),
    }


@router.get("/recent-queries")
async def get_recent_queries() -> dict:
    """Return summary of recent query activity."""
    metrics = pipeline.get_metrics()
    return {
        "total_queries": metrics.total_queries,
        "queries_last_hour": metrics.queries_last_hour,
        "avg_response_time_ms": metrics.avg_response_time_ms,
        "error_rate": metrics.error_rate,
    }
