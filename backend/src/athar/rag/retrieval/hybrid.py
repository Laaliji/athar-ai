"""
Hybrid Retrieval with Reciprocal Rank Fusion (RRF) + Cross-Encoder Reranking.

Pipeline:
  1. BM25 retrieval          — fast keyword matching
  2. Semantic retrieval      — dense vector similarity
  3. RRF fusion              — rank-based merging (no score normalization needed)
  4. Cross-encoder reranking — joint (query, passage) scoring for precision

Enhanced with:
  - Adaptive weight adjustment based on query characteristics
  - Query-specific retrieval strategy selection
  - Multi-query retrieval for complex queries
  - Improved score fusion with query analysis

Reference: Cormack, Clarke & Buettcher (2009) — "Reciprocal Rank Fusion
outperforms Condorcet and individual rank learning methods."
"""

from __future__ import annotations

import hashlib
import logging
import math
from collections import defaultdict

from athar.config import settings
from athar.models.schemas import RetrievedChunk, Source
from athar.rag.retrieval.bm25_retriever import BM25Retriever
from athar.rag.retrieval.reranker import rerank
from athar.rag.retrieval.semantic import SemanticRetriever
from athar.rag.retrieval.query_processor import (
    QueryType, 
    ProcessedQuery,
    process_query,
)

logger = logging.getLogger(__name__)

RRF_K = 60  # Standard RRF constant


class AdaptiveWeightCalculator:
    """
    Calculate adaptive BM25/Semantic weights based on query characteristics.
    
    Strategy:
    - FACTUAL queries (who, what, when, where) → favor BM25 (keywords matter)
    - CONCEPTUAL queries (why, how, explain) → favor semantic (meaning matters)
    - Queries with proper nouns/dates → favor BM25
    - Short queries (<5 words) → favor BM25 (keyword matching)
    - Long queries (>10 words) → favor semantic (context)
    """
    
    @staticmethod
    def calculate_weights(processed_query: ProcessedQuery) -> tuple[float, float]:
        """
        Calculate adaptive weights for BM25 and semantic retrieval.
        
        Args:
            processed_query: Processed query with metadata
            
        Returns:
            Tuple of (bm25_weight, semantic_weight)
        """
        # Start with baseline weights
        bm25_weight = settings.bm25_weight
        semantic_weight = settings.semantic_weight
        
        # Adjustment 1: Query type
        if processed_query.query_type == QueryType.FACTUAL:
            # Who, what, when, where → favor keywords
            bm25_weight += 0.15
            semantic_weight -= 0.15
        elif processed_query.query_type == QueryType.DEFINITION:
            # "What is X?" → balanced but slightly favor semantic
            semantic_weight += 0.05
            bm25_weight -= 0.05
        elif processed_query.query_type in (QueryType.CONCEPTUAL, QueryType.COMPARATIVE):
            # Why, how, comparisons → favor semantic understanding
            semantic_weight += 0.15
            bm25_weight -= 0.15
        elif processed_query.query_type == QueryType.TEMPORAL:
            # Time-based queries → favor BM25 for exact dates
            bm25_weight += 0.10
            semantic_weight -= 0.10
        
        # Adjustment 2: Query length
        query_words = len(processed_query.cleaned.split())
        if query_words <= 4:
            # Short queries → favor BM25
            bm25_weight += 0.10
            semantic_weight -= 0.10
        elif query_words >= 12:
            # Long queries → favor semantic
            semantic_weight += 0.10
            bm25_weight -= 0.10
        
        # Adjustment 3: Entity presence (proper nouns, dates)
        if processed_query.key_entities:
            # Has named entities → slightly favor BM25
            entity_boost = min(len(processed_query.key_entities) * 0.03, 0.15)
            bm25_weight += entity_boost
            semantic_weight -= entity_boost
        
        # Normalize to ensure they sum to 1.0
        total = bm25_weight + semantic_weight
        bm25_weight = bm25_weight / total
        semantic_weight = semantic_weight / total
        
        # Clamp to reasonable bounds
        bm25_weight = max(0.2, min(0.8, bm25_weight))
        semantic_weight = 1.0 - bm25_weight
        
        logger.debug(
            "Adaptive weights: bm25=%.2f, semantic=%.2f (query_type=%s, len=%d, entities=%d)",
            bm25_weight, semantic_weight, 
            processed_query.query_type.value, query_words, len(processed_query.key_entities)
        )
        
        return bm25_weight, semantic_weight


class HybridRetriever:
    """
    BM25 + Semantic retrieval fused by RRF, then reranked by cross-encoder.
    
    Enhanced with adaptive weighting and multi-query support.
    """

    def __init__(self, semantic: SemanticRetriever, bm25: BM25Retriever) -> None:
        self.semantic = semantic
        self.bm25 = bm25
        self.weight_calculator = AdaptiveWeightCalculator()

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        final_k: int | None = None,
        use_adaptive_weights: bool = True,
        use_query_expansion: bool = True,
        use_mmr: bool = True,
    ) -> list[RetrievedChunk]:
        """
        Full retrieval pipeline: BM25 + Semantic -> RRF -> Rerank.

        Args:
            query: User question.
            top_k: Candidates per retriever (wider net before reranking).
            final_k: Final chunks returned after reranking.
            use_adaptive_weights: Calculate weights based on query type.
            use_query_expansion: Generate and use expanded queries.
            use_mmr: Use MMR for semantic diversity.

        Returns:
            Ranked list of RetrievedChunk.
        """
        top_k = top_k or settings.retrieval_top_k
        final_k = final_k or settings.retrieval_final_k

        # Step 1: Process query
        processed_query = process_query(query, enable_expansion=use_query_expansion)
        
        # Step 2: Calculate adaptive weights
        if use_adaptive_weights:
            bm25_weight, semantic_weight = self.weight_calculator.calculate_weights(
                processed_query
            )
        else:
            bm25_weight = settings.bm25_weight
            semantic_weight = settings.semantic_weight
        
        # Step 3: Collect queries to process (original + expansions)
        queries_to_process = [processed_query.cleaned]
        if use_query_expansion and processed_query.expanded:
            # Limit expansions to avoid over-fetching
            queries_to_process.extend(processed_query.expanded[:2])
        
        # Step 4: Run retrieval for all queries
        all_semantic_results = []
        all_bm25_results = []
        
        for query_variant in queries_to_process:
            # Semantic retrieval with optional MMR
            semantic_results = self.semantic.retrieve(
                query_variant, 
                k=top_k,
                use_mmr=use_mmr and processed_query.is_complex,
                mmr_lambda=0.5,  # Balance relevance and diversity
            )
            all_semantic_results.extend(semantic_results)
            
            # BM25 retrieval
            bm25_results = self.bm25.retrieve(query_variant, k=top_k)
            all_bm25_results.extend(bm25_results)
        
        logger.debug(
            "Hybrid first-pass: semantic=%d, bm25=%d (queries=%d)",
            len(all_semantic_results), 
            len(all_bm25_results),
            len(queries_to_process),
        )

        if not all_semantic_results and not all_bm25_results:
            return []

        # Step 5: RRF fusion with adaptive weights
        rrf_scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, RetrievedChunk] = {}

        for rank, chunk in enumerate(all_semantic_results):
            doc_id = _doc_id(chunk)
            rrf_scores[doc_id] += semantic_weight / (RRF_K + rank + 1)
            if doc_id not in chunk_map:
                chunk_map[doc_id] = chunk
            chunk_map[doc_id].semantic_score = max(
                chunk_map[doc_id].semantic_score, chunk.semantic_score
            )

        for rank, chunk in enumerate(all_bm25_results):
            doc_id = _doc_id(chunk)
            rrf_scores[doc_id] += bm25_weight / (RRF_K + rank + 1)
            if doc_id not in chunk_map:
                chunk_map[doc_id] = chunk
            chunk_map[doc_id].bm25_score = max(
                chunk_map[doc_id].bm25_score, chunk.bm25_score
            )

        # Sort by RRF score
        ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        max_rrf = ranked[0][1] if ranked else 1.0

        # Keep top_k * 2 candidates for the reranker (wider input = better reranking)
        rerank_pool_size = min(top_k * 2, len(ranked))
        candidates: list[RetrievedChunk] = []
        for doc_id, rrf_score in ranked[:rerank_pool_size]:
            chunk = chunk_map[doc_id]
            chunk.hybrid_score = rrf_score / max(max_rrf, 1e-9)
            candidates.append(chunk)

        # Step 6: Cross-encoder reranking
        reranked = rerank(processed_query.cleaned, candidates, top_k=final_k)

        logger.debug(
            "Hybrid final: %d chunks (pool=%d, reranked=%s, weights=%.2f/%.2f)",
            len(reranked), len(candidates),
            reranked[0].rerank_score > 0 if reranked else False,
            bm25_weight, semantic_weight,
        )
        return reranked

    def retrieve_with_sources(
        self,
        query: str,
        top_k: int | None = None,
        final_k: int | None = None,
        use_adaptive_weights: bool = True,
        use_query_expansion: bool = True,
        use_mmr: bool = True,
    ) -> tuple[list[RetrievedChunk], list[Source]]:
        """
        Retrieve chunks and format deduplicated Source citations.
        
        Args:
            query: User question
            top_k: Candidates per retriever
            final_k: Final chunks after reranking
            use_adaptive_weights: Use query-based weight adjustment
            use_query_expansion: Generate and use query variants
            use_mmr: Use MMR for diversity
            
        Returns:
            Tuple of (chunks, sources)
        """
        chunks = self.retrieve(
            query, 
            top_k=top_k, 
            final_k=final_k,
            use_adaptive_weights=use_adaptive_weights,
            use_query_expansion=use_query_expansion,
            use_mmr=use_mmr,
        )
        sources = _deduplicate_sources(chunks)
        return chunks, sources


# ── Helpers ───────────────────────────────────────────────────────────────────


def _doc_id(chunk: RetrievedChunk) -> str:
    """Collision-resistant key stable across Python processes."""
    stable_id = chunk.metadata.get("id") or chunk.metadata.get("chunk_id")
    if stable_id:
        return str(stable_id)
    identity = "\x1f".join(
        str(chunk.metadata.get(key, ""))
        for key in ("source", "url", "title", "chunk_index")
    )
    return hashlib.sha256(f"{identity}\x1f{chunk.content}".encode("utf-8")).hexdigest()


def _deduplicate_sources(chunks: list[RetrievedChunk]) -> list[Source]:
    """Build deduplicated Source list from retrieved chunks."""
    seen: set[str] = set()
    sources: list[Source] = []

    for chunk in chunks:
        title = chunk.metadata.get("title", "Unknown")
        url = chunk.metadata.get("url", "")
        excerpt = chunk.content[:250].strip() + "…"

        key = title + url
        if key not in seen:
            seen.add(key)
            # Use rerank score if available, else hybrid score
            # Cross-encoder logits are unbounded (and can be negative).  Map
            # them to a valid, human-readable confidence-like range.
            score = (
                1 / (1 + math.exp(-max(min(chunk.rerank_score, 20), -20)))
                if chunk.rerank_score != 0
                else chunk.hybrid_score
            )
            sources.append(Source(
                title=title,
                url=url,
                excerpt=excerpt,
                score=round(min(score, 1.0), 3),
            ))

    return sources
