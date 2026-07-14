"""
Main RAG Pipeline — orchestrates retrieval, context building, and generation.

This is the core of the system. It wires together:
  - Hybrid retrieval (BM25 + semantic via RRF)
  - Context window construction
  - Conversation history management
  - LLM generation (sync + async streaming)
  - In-memory metrics collection
"""

from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from athar.config import settings, CHROMA_DIR
from athar.models.schemas import (
    ConversationMessage,
    QueryResponse,
    RetrievedChunk,
    Source,
    SystemMetrics,
)
from athar.rag.generation.llm import BaseLLM, create_llm, AnswerPostProcessor
from athar.rag.retrieval.bm25_retriever import BM25Retriever
from athar.rag.retrieval.hybrid import HybridRetriever
from athar.rag.retrieval.semantic import SemanticRetriever
from athar.rag.cache import QueryCache, hash_context
from athar.rag.context_builder import ContextBuilder
from athar.rag.retrieval.query_processor import process_query
from athar.rag.error_handling import (
    RAGException,
    RetrievalError,
    GenerationError,
    retry_with_backoff,
    ErrorContext,
    CircuitBreaker,
)
from athar.rag.metrics import MetricsTracker

logger = logging.getLogger(__name__)

# Path for BM25 index persistence
BM25_INDEX_PATH = CHROMA_DIR / "bm25_index.pkl"


class RAGPipeline:
    """Orchestrates retrieval, context assembly, and generation."""

    def __init__(self) -> None:
        self.semantic = SemanticRetriever()
        self.bm25 = BM25Retriever()
        self.hybrid: HybridRetriever | None = None
        self.llm: BaseLLM | None = None

        # Query cache for performance
        self.cache = QueryCache(
            retrieval_maxsize=100,
            retrieval_ttl=3600.0,  # 1 hour
            generation_maxsize=50,
            generation_ttl=1800.0,  # 30 minutes
        )

        # Context builder for intelligent context assembly
        self.context_builder = ContextBuilder(
            max_context_tokens=2000,
            max_history_tokens=500,
            chunk_max_tokens=150,
        )

        # Circuit breaker for LLM calls
        self.llm_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            success_threshold=2,
        )

        # Metrics tracker for analytics
        self.metrics = MetricsTracker(max_history=10000)

        # Conversation store: {conversation_id: deque[ConversationMessage]}
        self._conversations: dict[str, deque[ConversationMessage]] = {}

        # Metrics ring buffer (last 1000 queries)
        self._query_times: deque[dict] = deque(maxlen=1000)

        self._startup_time = time.time()
        self._is_ready = False

    # ── Initialization ────────────────────────────────────────────────────────

    def initialize(self) -> None:
        """
        Full pipeline initialization:
        1. Load embedding model + ChromaDB
        2. Load/build BM25 index
        3. Wire hybrid retriever
        4. Load LLM (Groq → Ollama → HuggingFace)
        """
        logger.info("Initializing RAG pipeline v%s", settings.app_version)

        # Semantic retriever (ChromaDB + sentence-transformers)
        self.semantic.initialize()

        # BM25 — try loading the saved index, then repair it from the persisted
        # Chroma corpus if it is absent or stale.
        if BM25_INDEX_PATH.exists():
            self.bm25.load(BM25_INDEX_PATH)
        if self.semantic.count() and self.bm25.document_count != self.semantic.count():
            logger.warning(
                "BM25 index is missing or stale (%d BM25 documents / %d vectors); rebuilding.",
                self.bm25.document_count,
                self.semantic.count(),
            )
            self.bm25.build_index(self.semantic.get_all_documents())
            self.bm25.save(BM25_INDEX_PATH)
        elif not self.semantic.count():
            logger.info("Knowledge base is empty — run ingestion to populate it.")

        # Wire hybrid retriever
        self.hybrid = HybridRetriever(self.semantic, self.bm25)

        # LLM (auto-detect best available provider)
        self.llm = create_llm()

        self._is_ready = True
        logger.info(
            "Pipeline ready — LLM: %s (%s) | chunks: %d",
            self.llm.model_name,
            self.llm.provider_name,
            self.semantic.count(),
        )

    @property
    def is_ready(self) -> bool:
        return (
            self._is_ready
            and self.semantic.is_ready
            and self.semantic.count() > 0
            and self.bm25.is_ready
            and self.llm is not None
        )

    # ── Query ─────────────────────────────────────────────────────────────────

    def query(
        self,
        question: str,
        conversation_id: str | None = None,
        max_sources: int = 3,
        use_cache: bool = True,
    ) -> QueryResponse:
        """
        Full RAG query: retrieve → build context → generate → record metrics.

        Args:
            question: The user's question.
            conversation_id: Optional session ID for multi-turn dialogue.
            max_sources: Maximum number of source citations.
            use_cache: Whether to use query caching.

        Returns:
            QueryResponse with answer, sources, and timing breakdown.
            
        Raises:
            RetrievalError: If retrieval fails
            GenerationError: If generation fails
            RAGException: For other pipeline errors
        """
        self._assert_ready()
        conv_id = conversation_id or str(uuid4())
        start = time.perf_counter()

        try:
            # 1. Retrieval with error handling
            retrieval_start = time.perf_counter()
            with ErrorContext("retrieval", reraise=True):
                # Process query for analytics
                processed_query = process_query(question, enable_expansion=True)
                
                chunks, sources = self._retrieve_with_retry(question, max_sources, use_cache)
                retrieval_ms = (time.perf_counter() - retrieval_start) * 1000
                
                # Record retrieval metrics
                self.metrics.record_retrieval(
                    query=question,
                    chunks=chunks,
                    retrieval_ms=retrieval_ms,
                    bm25_weight=settings.bm25_weight,
                    semantic_weight=settings.semantic_weight,
                    used_mmr=True,
                    used_adaptive_weights=True,
                )
                
                # Record query analytics
                self.metrics.record_query_analytics(
                    query=question,
                    query_length=len(processed_query.cleaned.split()),
                    query_type=processed_query.query_type.value,
                    num_entities=len(processed_query.key_entities),
                    is_complex=processed_query.is_complex,
                    was_expanded=len(processed_query.expanded) > 0,
                    num_expansions=len(processed_query.expanded),
                    cache_hit=retrieval_ms == 0.0,
                    cache_type="retrieval" if retrieval_ms == 0.0 else None,
                )

            # 2. Build context with conversation history
            with ErrorContext("context_building", reraise=True):
                context = self._build_context(chunks, conv_id)
                context_hash = hash_context(context)

            # 3. Generation with error handling and circuit breaker
            generation_start = time.perf_counter()
            with ErrorContext("generation", reraise=True):
                answer = self._generate_with_retry(
                    question, context, context_hash, 
                    processed_query.query_type.value, sources, use_cache
                )
                generation_ms = (time.perf_counter() - generation_start) * 1000
                
                # Record generation metrics
                self.metrics.record_component_call(
                    "generation",
                    generation_ms,
                    success=True,
                )

            total_ms = (time.perf_counter() - start) * 1000

            # 4. Update conversation history
            self._record_turn(conv_id, question, answer, sources)

            # 5. Record metrics
            confidence = _compute_confidence(chunks)
            self._query_times.append(
                {
                    "timestamp": datetime.utcnow(),
                    "total_ms": total_ms,
                    "retrieval_ms": retrieval_ms,
                    "generation_ms": generation_ms,
                    "success": True,
                    "cache_hit": use_cache and (retrieval_ms == 0.0 or generation_ms == 0.0),
                }
            )

            return QueryResponse(
                question=question,
                answer=answer,
                sources=sources[:max_sources],
                processing_time_ms=round(total_ms, 1),
                retrieval_time_ms=round(retrieval_ms, 1),
                generation_time_ms=round(generation_ms, 1),
                model_used=f"{self.llm.provider_name}/{self.llm.model_name}",  # type: ignore[union-attr]
                conversation_id=conv_id,
                num_chunks_retrieved=len(chunks),
                confidence=round(confidence, 3),
            )

        except Exception as exc:
            # Record failed query
            self._query_times.append(
                {
                    "timestamp": datetime.utcnow(),
                    "total_ms": (time.perf_counter() - start) * 1000,
                    "success": False,
                    "error": str(exc),
                }
            )
            logger.exception("Query failed: %s", question[:50])
            raise RAGException(f"Query pipeline failed: {exc}") from exc
    
    @retry_with_backoff(
        max_attempts=3,
        initial_delay=0.5,
        exceptions=(Exception,),
        logger_name="athar.rag.pipeline",
    )
    def _retrieve_with_retry(
        self,
        question: str,
        max_sources: int,
        use_cache: bool,
    ) -> tuple[list[RetrievedChunk], list[Source]]:
        """Retrieval with automatic retry on failure."""
        cache_key_params = {"max_sources": max_sources}
        
        if use_cache:
            cached_retrieval = self.cache.get_retrieval(question, **cache_key_params)
            if cached_retrieval:
                return cached_retrieval
        
        try:
            chunks, sources = self.hybrid.retrieve_with_sources(question)  # type: ignore[union-attr]
            
            if use_cache:
                self.cache.put_retrieval(question, (chunks, sources), **cache_key_params)
            
            return chunks, sources
        except Exception as exc:
            raise RetrievalError(f"Retrieval failed: {exc}") from exc
    
    def _generate_with_retry(
        self,
        question: str,
        context: str,
        context_hash: str,
        query_type: str,
        sources: list[Source],
        use_cache: bool,
    ) -> str:
        """Generation with circuit breaker and retry."""
        # Check cache first
        if use_cache:
            cached_answer = self.cache.get_generation(question, context_hash)
            if cached_answer:
                logger.info("Cache hit for generation: %s", question[:50])
                return cached_answer
        
        # Generate with circuit breaker
        try:
            def _generate() -> str:
                raw_answer = self.llm.generate(  # type: ignore[union-attr]
                    question, context, query_type=query_type
                )
                
                # Post-process answer
                answer, quality_metadata = AnswerPostProcessor.process(
                    raw_answer, question, context, len(sources)
                )
                
                return answer
            
            # Use circuit breaker for LLM call
            answer = self.llm_circuit_breaker.call(_generate)
            
            if use_cache:
                self.cache.put_generation(question, context_hash, answer)
            
            return answer
            
        except Exception as exc:
            raise GenerationError(f"Generation failed: {exc}") from exc

    def stream_generate(
        self,
        question: str,
        conversation_id: str | None = None,
    ) -> Iterator[dict]:
        """
        Streaming pipeline — yields token dicts for SSE.

        Yields dicts of shape:
          {"type": "token", "content": "..."}
          {"type": "sources", "sources": [...]}
          {"type": "done", "metadata": {...}}
          {"type": "error", "content": "..."}
        """
        self._assert_ready()
        conv_id = conversation_id or str(uuid4())

        try:
            with ErrorContext("streaming_query", reraise=True):
                # 1. Retrieve (not streamed — must happen first for sources)
                t0 = time.perf_counter()
                chunks, sources = self._retrieve_with_retry(question, max_sources=5, use_cache=True)
                retrieval_ms = (time.perf_counter() - t0) * 1000

                # 2. Emit sources immediately so UI can show them while text streams
                yield {
                    "type": "sources",
                    "sources": [s.model_dump() for s in sources],
                    "retrieval_ms": round(retrieval_ms, 1),
                }

                # 3. Build context
                context = self._build_context(chunks, conv_id)
                processed_query = process_query(question, enable_expansion=False)

                # 4. Stream tokens with circuit breaker
                t1 = time.perf_counter()
                full_answer = ""
                
                def _stream():
                    nonlocal full_answer
                    for token in self.llm.stream(  # type: ignore[union-attr]
                        question, context, query_type=processed_query.query_type.value
                    ):
                        full_answer += token
                        yield {"type": "token", "content": token}
                
                # Stream through circuit breaker
                for chunk_dict in self.llm_circuit_breaker.call(_stream):
                    yield chunk_dict

                generation_ms = (time.perf_counter() - t1) * 1000
                total_ms = retrieval_ms + generation_ms

                # 5. Post-process complete answer
                processed_answer, quality_metadata = AnswerPostProcessor.process(
                    full_answer, question, context, len(sources)
                )

                # 6. Update history
                self._record_turn(conv_id, question, processed_answer, sources)
                self._query_times.append(
                    {
                        "timestamp": datetime.utcnow(),
                        "total_ms": total_ms,
                        "retrieval_ms": retrieval_ms,
                        "generation_ms": generation_ms,
                        "success": True,
                    }
                )

                yield {
                    "type": "done",
                    "conversation_id": conv_id,
                    "metadata": {
                        "total_ms": round(total_ms, 1),
                        "retrieval_ms": round(retrieval_ms, 1),
                        "generation_ms": round(generation_ms, 1),
                        "model": self.llm.model_name,  # type: ignore[union-attr]
                        "chunks_used": len(chunks),
                        "confidence": round(_compute_confidence(chunks), 3),
                        "quality": quality_metadata,
                    },
                }

        except Exception as exc:
            logger.exception("Streaming pipeline error: %s", exc)
            self._query_times.append(
                {"timestamp": datetime.utcnow(), "total_ms": 0, "success": False, "error": str(exc)}
            )
            yield {"type": "error", "content": str(exc)}

    # ── Context Building ──────────────────────────────────────────────────────

    def _build_context(self, chunks: list[RetrievedChunk], conv_id: str) -> str:
        """
        Build the context string for the LLM using the advanced context builder.

        Includes:
        - Retrieved document chunks (numbered, optimally ordered)
        - Recent conversation history (last N turns)
        - Redundancy removal and compression
        """
        history = self._get_history(conv_id)
        
        context = self.context_builder.build(
            chunks=chunks,
            conversation_history=history if history else None,
            remove_redundancy=True,
        )
        
        return context

    # ── Conversation Management ───────────────────────────────────────────────

    def _get_history(self, conv_id: str) -> list[ConversationMessage]:
        return list(self._conversations.get(conv_id, deque()))

    def _record_turn(
        self,
        conv_id: str,
        question: str,
        answer: str,
        sources: list[Source],
    ) -> None:
        if conv_id not in self._conversations:
            self._conversations[conv_id] = deque(
                maxlen=settings.max_conversation_turns * 2
            )
        history = self._conversations[conv_id]
        history.append(ConversationMessage(role="user", content=question))
        history.append(
            ConversationMessage(role="assistant", content=answer, sources=sources)
        )

    def get_conversation(self, conv_id: str) -> list[ConversationMessage]:
        return self._get_history(conv_id)

    def clear_conversation(self, conv_id: str) -> None:
        self._conversations.pop(conv_id, None)

    # ── Metrics ───────────────────────────────────────────────────────────────

    def get_metrics(self) -> SystemMetrics:
        """Compute real-time metrics from the query ring buffer."""
        all_times = list(self._query_times)
        if not all_times:
            return SystemMetrics(
                total_queries=0,
                avg_response_time_ms=0,
                avg_retrieval_time_ms=0,
                avg_generation_time_ms=0,
                queries_last_hour=0,
                error_rate=0,
            )

        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent = [t for t in all_times if t["timestamp"] > one_hour_ago]
        successful = [t for t in all_times if t.get("success", True)]

        def avg(key: str, items: list) -> float:
            vals = [t.get(key, 0) for t in items if key in t]
            return round(sum(vals) / len(vals), 1) if vals else 0.0

        return SystemMetrics(
            total_queries=len(all_times),
            avg_response_time_ms=avg("total_ms", successful),
            avg_retrieval_time_ms=avg("retrieval_ms", successful),
            avg_generation_time_ms=avg("generation_ms", successful),
            queries_last_hour=len(recent),
            error_rate=round(
                1 - len(successful) / max(len(all_times), 1), 3
            ),
        )
    
    def get_detailed_metrics(self) -> dict:
        """
        Get comprehensive metrics including retrieval analytics.
        
        Returns:
            Dictionary with all available metrics
        """
        return {
            "system": self.get_metrics().model_dump(),
            "retrieval": self.metrics.get_retrieval_summary(time_window_minutes=60),
            "query_patterns": self.metrics.get_query_patterns(),
            "components": self.metrics.get_component_metrics(),
            "score_distribution": self.metrics.get_score_distribution("hybrid"),
            "cache": self.cache.get_stats(),
        }

    def get_status(self) -> dict:
        cache_stats = self.cache.get_stats()
        return {
            "status": "ready" if self.is_ready else "degraded",
            "llm_provider": self.llm.provider_name if self.llm else "none",
            "llm_model": self.llm.model_name if self.llm else "none",
            "embedding_model": settings.embedding_model,
            "vector_db_ready": self.semantic.is_ready,
            "bm25_ready": self.bm25.is_ready,
            "documents_loaded": self.semantic.count(),
            "uptime_seconds": round(time.time() - self._startup_time, 1),
            "version": settings.app_version,
            "cache_stats": cache_stats,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _assert_ready(self) -> None:
        if not self._is_ready:
            raise RuntimeError("RAG pipeline not initialized.")
        if self.semantic.count() == 0:
            raise RuntimeError(
                "Knowledge base is empty. Run ingestion first: "
                "`python scripts/ingest.py`"
            )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _compute_confidence(chunks: list[RetrievedChunk]) -> float:
    """Estimate answer confidence from retrieval scores."""
    if not chunks:
        return 0.0
    scores = [c.hybrid_score for c in chunks if c.hybrid_score > 0]
    if not scores:
        return 0.0
    return min(sum(scores) / len(scores), 1.0)


# ── Global pipeline instance ──────────────────────────────────────────────────
# Singleton managed by FastAPI lifespan
pipeline = RAGPipeline()
