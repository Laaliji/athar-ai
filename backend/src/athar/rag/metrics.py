"""
Comprehensive metrics and analytics tracking for RAG pipeline.

Features:
- Retrieval quality metrics (precision, relevance)
- Performance metrics (latency, throughput)
- Query analytics (patterns, trends)
- Score distribution tracking
- Per-component metrics
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from athar.models.schemas import RetrievedChunk

logger = logging.getLogger(__name__)


@dataclass
class RetrievalMetrics:
    """Metrics for a single retrieval operation."""
    query: str
    timestamp: datetime
    
    # Retrieval stats
    num_semantic_results: int = 0
    num_bm25_results: int = 0
    num_final_results: int = 0
    
    # Score statistics
    avg_semantic_score: float = 0.0
    avg_bm25_score: float = 0.0
    avg_hybrid_score: float = 0.0
    avg_rerank_score: float = 0.0
    max_rerank_score: float = 0.0
    
    # Timing
    retrieval_ms: float = 0.0
    rerank_ms: float = 0.0
    
    # Quality indicators
    score_variance: float = 0.0
    has_high_confidence: bool = False
    used_mmr: bool = False
    used_adaptive_weights: bool = False
    
    # Weights used
    bm25_weight: float = 0.0
    semantic_weight: float = 0.0


@dataclass
class QueryAnalytics:
    """Analytics for query patterns and characteristics."""
    query: str
    timestamp: datetime
    
    # Query characteristics
    query_length: int = 0
    query_type: str = "unknown"
    num_entities: int = 0
    is_complex: bool = False
    
    # Processing
    was_expanded: bool = False
    num_expansions: int = 0
    
    # Cache
    cache_hit: bool = False
    cache_type: str | None = None  # "retrieval" or "generation"


@dataclass
class PerformanceMetrics:
    """Performance metrics over time."""
    window_start: datetime
    window_end: datetime
    
    # Counts
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    cache_hits: int = 0
    
    # Latency statistics (milliseconds)
    avg_total_latency: float = 0.0
    p50_total_latency: float = 0.0
    p95_total_latency: float = 0.0
    p99_total_latency: float = 0.0
    
    avg_retrieval_latency: float = 0.0
    avg_generation_latency: float = 0.0
    
    # Throughput
    queries_per_minute: float = 0.0
    
    # Quality
    avg_confidence: float = 0.0
    avg_chunks_retrieved: float = 0.0


@dataclass
class ComponentMetrics:
    """Metrics for individual pipeline components."""
    component_name: str
    
    # Call statistics
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    
    # Timing
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    
    # Recent latencies for percentile calculation
    recent_latencies: deque[float] = field(default_factory=lambda: deque(maxlen=1000))


class MetricsTracker:
    """
    Comprehensive metrics tracking for the RAG pipeline.
    
    Tracks retrieval quality, performance, query patterns, and component-level metrics.
    """
    
    def __init__(self, max_history: int = 10000):
        """
        Initialize metrics tracker.
        
        Args:
            max_history: Maximum number of historical records to keep
        """
        self.max_history = max_history
        
        # Historical data
        self.retrieval_history: deque[RetrievalMetrics] = deque(maxlen=max_history)
        self.query_history: deque[QueryAnalytics] = deque(maxlen=max_history)
        
        # Component-level metrics
        self.component_metrics: dict[str, ComponentMetrics] = {}
        
        # Query pattern tracking
        self.query_type_counts: defaultdict[str, int] = defaultdict(int)
        self.cache_hit_by_type: defaultdict[str, int] = defaultdict(int)
        
        # Score distributions (bucketed)
        self.score_buckets: defaultdict[str, list[float]] = defaultdict(list)
    
    def record_retrieval(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        retrieval_ms: float,
        bm25_weight: float = 0.0,
        semantic_weight: float = 0.0,
        used_mmr: bool = False,
        used_adaptive_weights: bool = False,
    ) -> None:
        """
        Record retrieval metrics for a query.
        
        Args:
            query: User query
            chunks: Retrieved chunks
            retrieval_ms: Retrieval time in milliseconds
            bm25_weight: BM25 weight used
            semantic_weight: Semantic weight used
            used_mmr: Whether MMR was used
            used_adaptive_weights: Whether adaptive weighting was used
        """
        if not chunks:
            logger.debug("No chunks to record metrics for")
            return
        
        # Calculate statistics
        semantic_scores = [c.semantic_score for c in chunks if c.semantic_score > 0]
        bm25_scores = [c.bm25_score for c in chunks if c.bm25_score > 0]
        hybrid_scores = [c.hybrid_score for c in chunks if c.hybrid_score > 0]
        rerank_scores = [c.rerank_score for c in chunks if c.rerank_score > 0]
        
        def safe_avg(scores: list[float]) -> float:
            return sum(scores) / len(scores) if scores else 0.0
        
        def safe_variance(scores: list[float]) -> float:
            if len(scores) < 2:
                return 0.0
            mean = safe_avg(scores)
            return sum((x - mean) ** 2 for x in scores) / len(scores)
        
        metrics = RetrievalMetrics(
            query=query[:100],  # Truncate for storage
            timestamp=datetime.utcnow(),
            num_semantic_results=len(semantic_scores),
            num_bm25_results=len(bm25_scores),
            num_final_results=len(chunks),
            avg_semantic_score=safe_avg(semantic_scores),
            avg_bm25_score=safe_avg(bm25_scores),
            avg_hybrid_score=safe_avg(hybrid_scores),
            avg_rerank_score=safe_avg(rerank_scores),
            max_rerank_score=max(rerank_scores) if rerank_scores else 0.0,
            retrieval_ms=retrieval_ms,
            score_variance=safe_variance(hybrid_scores) if hybrid_scores else 0.0,
            has_high_confidence=any(c.hybrid_score > 0.8 for c in chunks),
            used_mmr=used_mmr,
            used_adaptive_weights=used_adaptive_weights,
            bm25_weight=bm25_weight,
            semantic_weight=semantic_weight,
        )
        
        self.retrieval_history.append(metrics)
        
        # Update score buckets for distribution analysis
        for score in hybrid_scores[:10]:  # Top 10 only
            bucket = int(score * 10) / 10  # Round to nearest 0.1
            self.score_buckets["hybrid"].append(bucket)
        
        logger.debug(
            "Recorded retrieval metrics: %d chunks, avg_score=%.3f, time=%.1fms",
            len(chunks), metrics.avg_hybrid_score, retrieval_ms
        )
    
    def record_query_analytics(
        self,
        query: str,
        query_length: int,
        query_type: str,
        num_entities: int,
        is_complex: bool,
        was_expanded: bool,
        num_expansions: int,
        cache_hit: bool = False,
        cache_type: str | None = None,
    ) -> None:
        """
        Record query analytics.
        
        Args:
            query: User query
            query_length: Number of words in query
            query_type: Type of query (factual, conceptual, etc.)
            num_entities: Number of extracted entities
            is_complex: Whether query is complex
            was_expanded: Whether query was expanded
            num_expansions: Number of expansions generated
            cache_hit: Whether cache was hit
            cache_type: Type of cache hit
        """
        analytics = QueryAnalytics(
            query=query[:100],
            timestamp=datetime.utcnow(),
            query_length=query_length,
            query_type=query_type,
            num_entities=num_entities,
            is_complex=is_complex,
            was_expanded=was_expanded,
            num_expansions=num_expansions,
            cache_hit=cache_hit,
            cache_type=cache_type,
        )
        
        self.query_history.append(analytics)
        self.query_type_counts[query_type] += 1
        
        if cache_hit:
            self.cache_hit_by_type[query_type] += 1
    
    def record_component_call(
        self,
        component_name: str,
        latency_ms: float,
        success: bool = True,
    ) -> None:
        """
        Record metrics for a component call.
        
        Args:
            component_name: Name of the component
            latency_ms: Call latency in milliseconds
            success: Whether call was successful
        """
        if component_name not in self.component_metrics:
            self.component_metrics[component_name] = ComponentMetrics(
                component_name=component_name
            )
        
        metrics = self.component_metrics[component_name]
        metrics.total_calls += 1
        
        if success:
            metrics.successful_calls += 1
            metrics.recent_latencies.append(latency_ms)
            metrics.avg_latency_ms = (
                (metrics.avg_latency_ms * (metrics.successful_calls - 1) + latency_ms)
                / metrics.successful_calls
            )
            metrics.max_latency_ms = max(metrics.max_latency_ms, latency_ms)
            metrics.min_latency_ms = min(metrics.min_latency_ms, latency_ms)
        else:
            metrics.failed_calls += 1
    
    def get_retrieval_summary(
        self,
        time_window_minutes: int = 60,
    ) -> dict[str, Any]:
        """
        Get summary of retrieval metrics.
        
        Args:
            time_window_minutes: Time window for analysis
            
        Returns:
            Dictionary with retrieval metrics summary
        """
        cutoff = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        recent = [m for m in self.retrieval_history if m.timestamp > cutoff]
        
        if not recent:
            return {"message": "No recent retrieval data"}
        
        return {
            "time_window_minutes": time_window_minutes,
            "total_retrievals": len(recent),
            "avg_results_per_query": sum(m.num_final_results for m in recent) / len(recent),
            "avg_semantic_score": sum(m.avg_semantic_score for m in recent) / len(recent),
            "avg_bm25_score": sum(m.avg_bm25_score for m in recent) / len(recent),
            "avg_hybrid_score": sum(m.avg_hybrid_score for m in recent) / len(recent),
            "avg_rerank_score": sum(m.avg_rerank_score for m in recent) / len(recent),
            "high_confidence_rate": sum(1 for m in recent if m.has_high_confidence) / len(recent),
            "mmr_usage_rate": sum(1 for m in recent if m.used_mmr) / len(recent),
            "adaptive_weights_rate": sum(1 for m in recent if m.used_adaptive_weights) / len(recent),
            "avg_retrieval_latency_ms": sum(m.retrieval_ms for m in recent) / len(recent),
        }
    
    def get_query_patterns(self) -> dict[str, Any]:
        """
        Analyze query patterns and characteristics.
        
        Returns:
            Dictionary with query pattern analysis
        """
        if not self.query_history:
            return {"message": "No query data"}
        
        recent = list(self.query_history)[-1000:]  # Last 1000 queries
        
        # Query type distribution
        type_dist = {}
        for qtype, count in self.query_type_counts.items():
            type_dist[qtype] = {
                "count": count,
                "percentage": count / len(recent) * 100,
                "cache_hit_rate": (
                    self.cache_hit_by_type[qtype] / count * 100
                    if count > 0 else 0
                ),
            }
        
        # Complexity analysis
        complex_queries = sum(1 for q in recent if q.is_complex)
        expanded_queries = sum(1 for q in recent if q.was_expanded)
        
        return {
            "total_queries_analyzed": len(recent),
            "query_type_distribution": type_dist,
            "avg_query_length": sum(q.query_length for q in recent) / len(recent),
            "avg_entities_per_query": sum(q.num_entities for q in recent) / len(recent),
            "complex_query_rate": complex_queries / len(recent) * 100,
            "expansion_rate": expanded_queries / len(recent) * 100,
            "overall_cache_hit_rate": sum(1 for q in recent if q.cache_hit) / len(recent) * 100,
        }
    
    def get_component_metrics(self) -> dict[str, Any]:
        """
        Get metrics for all components.
        
        Returns:
            Dictionary with component-level metrics
        """
        result = {}
        
        for name, metrics in self.component_metrics.items():
            # Calculate percentiles from recent latencies
            latencies = sorted(metrics.recent_latencies)
            
            def percentile(p: float) -> float:
                if not latencies:
                    return 0.0
                idx = int(len(latencies) * p)
                return latencies[min(idx, len(latencies) - 1)]
            
            result[name] = {
                "total_calls": metrics.total_calls,
                "successful_calls": metrics.successful_calls,
                "failed_calls": metrics.failed_calls,
                "success_rate": (
                    metrics.successful_calls / metrics.total_calls * 100
                    if metrics.total_calls > 0 else 0
                ),
                "avg_latency_ms": round(metrics.avg_latency_ms, 2),
                "min_latency_ms": round(metrics.min_latency_ms, 2) if metrics.min_latency_ms != float('inf') else 0,
                "max_latency_ms": round(metrics.max_latency_ms, 2),
                "p50_latency_ms": round(percentile(0.5), 2),
                "p95_latency_ms": round(percentile(0.95), 2),
                "p99_latency_ms": round(percentile(0.99), 2),
            }
        
        return result
    
    def get_score_distribution(self, score_type: str = "hybrid") -> dict[str, Any]:
        """
        Get score distribution analysis.
        
        Args:
            score_type: Type of score ("hybrid", "semantic", "bm25")
            
        Returns:
            Score distribution statistics
        """
        scores = self.score_buckets.get(score_type, [])
        
        if not scores:
            return {"message": f"No {score_type} score data"}
        
        # Recent scores only (last 1000)
        recent_scores = scores[-1000:]
        
        # Calculate distribution
        from collections import Counter
        distribution = Counter(recent_scores)
        
        return {
            "score_type": score_type,
            "total_samples": len(recent_scores),
            "distribution": {
                f"{bucket:.1f}-{bucket+0.1:.1f}": count
                for bucket, count in sorted(distribution.items())
            },
            "avg_score": sum(recent_scores) / len(recent_scores),
            "min_score": min(recent_scores),
            "max_score": max(recent_scores),
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.retrieval_history.clear()
        self.query_history.clear()
        self.component_metrics.clear()
        self.query_type_counts.clear()
        self.cache_hit_by_type.clear()
        self.score_buckets.clear()
        logger.info("All metrics reset")


# Global metrics tracker instance
_metrics_tracker: MetricsTracker | None = None


def get_metrics_tracker() -> MetricsTracker:
    """Get or create global metrics tracker instance."""
    global _metrics_tracker
    if _metrics_tracker is None:
        _metrics_tracker = MetricsTracker()
    return _metrics_tracker
