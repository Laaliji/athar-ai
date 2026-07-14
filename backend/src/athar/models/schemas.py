"""Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


# ── Source / Document Models ───────────────────────────────────────────────


class Source(BaseModel):
    title: str
    url: str
    excerpt: str
    score: float = Field(default=0.0, ge=0.0, le=1.0)


class RetrievedChunk(BaseModel):
    model_config = {"exclude": {"embedding"}}  # Pydantic v2 syntax
    
    content: str
    metadata: dict[str, Any]
    bm25_score: float = 0.0
    semantic_score: float = 0.0
    hybrid_score: float = 0.0
    rerank_score: float = 0.0  # set by cross-encoder reranker; 0 = not reranked
    embedding: list[float] | None = None  # for MMR diversity computation


# ── Query Models ────────────────────────────────────────────────────────────


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    conversation_id: str | None = None
    max_sources: int = Field(default=3, ge=1, le=8)
    stream: bool = False

    @field_validator("question")
    @classmethod
    def strip_question(cls, v: str) -> str:
        return v.strip()


class QueryResponse(BaseModel):
    query_id: str = Field(default_factory=lambda: str(uuid4()))
    question: str
    answer: str
    sources: list[Source]
    processing_time_ms: float
    retrieval_time_ms: float
    generation_time_ms: float
    model_used: str
    conversation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Quality indicators
    num_chunks_retrieved: int = 0
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reranker_used: bool = False


# ── Conversation Models ──────────────────────────────────────────────────────


class ConversationMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: list[Source] = []
    processing_time_ms: float | None = None


class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = "New Conversation"
    messages: list[ConversationMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Admin / System Models ────────────────────────────────────────────────────


class KnowledgeBaseStats(BaseModel):
    total_documents: int
    total_chunks: int
    collection_name: str
    embedding_model: str
    last_ingested: str | None = None
    topics: list[str] = []


class SystemMetrics(BaseModel):
    total_queries: int
    avg_response_time_ms: float
    avg_retrieval_time_ms: float
    avg_generation_time_ms: float
    queries_last_hour: int
    error_rate: float


class SystemStatus(BaseModel):
    status: str  # "ready" | "loading" | "error"
    llm_provider: str
    llm_model: str
    embedding_model: str
    vector_db_ready: bool
    bm25_ready: bool
    documents_loaded: int
    uptime_seconds: float
    version: str


class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    version: str


class IngestRequest(BaseModel):
    topics: list[str] | None = None  # None = use defaults
    max_articles: int = Field(default=40, ge=1, le=100)
    overwrite: bool = False


class IngestResponse(BaseModel):
    success: bool
    articles_fetched: int
    chunks_created: int
    message: str
    duration_seconds: float


# ── SSE Streaming Model ──────────────────────────────────────────────────────


class StreamChunk(BaseModel):
    type: str  # "token" | "sources" | "done" | "error"
    content: str = ""
    sources: list[Source] = []
    metadata: dict[str, Any] = {}
