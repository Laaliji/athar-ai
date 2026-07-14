"""
FastAPI endpoint tests using TestClient.
These tests use mock objects to avoid requiring a live RAG pipeline.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from athar.main import app
from athar.models.schemas import QueryResponse, SystemMetrics


class TestHealthEndpoints:

    @pytest.fixture
    def client(self):
        """Create a test client with a mocked pipeline."""
        with (
            patch("athar.api.routes.health.pipeline") as mock_pipeline,
            patch("athar.api.routes.query.pipeline", mock_pipeline),
            patch("athar.api.routes.admin.pipeline", mock_pipeline),
        ):
            mock_pipeline.is_ready = True
            mock_pipeline.get_status.return_value = {
                "status": "ready",
                "llm_provider": "groq",
                "llm_model": "llama-3.3-70b-versatile",
                "embedding_model": "all-MiniLM-L6-v2",
                "vector_db_ready": True,
                "bm25_ready": True,
                "documents_loaded": 1250,
                "uptime_seconds": 42.0,
                "version": "3.0.0",
            }

            yield TestClient(app, raise_server_exceptions=False)

    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data or "message" in data

    def test_health_check(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "timestamp" in data
        assert "version" in data

    def test_system_status(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "llm_provider" in data
        assert "documents_loaded" in data


class TestQueryEndpoints:

    @pytest.fixture
    def client_with_query(self):
        """Test client with mocked successful query."""
        mock_response = QueryResponse(
            query_id="test-123",
            question="What is the House of Wisdom?",
            answer="The House of Wisdom was an intellectual center in Baghdad.",
            sources=[
                {
                    "title": "House of Wisdom",
                    "url": "https://en.wikipedia.org/wiki/House_of_Wisdom",
                    "excerpt": "The House of Wisdom...",
                    "score": 0.92,
                }
            ],
            processing_time_ms=1234.5,
            retrieval_time_ms=234.5,
            generation_time_ms=1000.0,
            model_used="groq/llama-3.3-70b-versatile",
            conversation_id="conv-abc",
            num_chunks_retrieved=3,
            confidence=0.87,
        )

        with patch("athar.api.routes.query.pipeline") as mock_pipeline:
            mock_pipeline.is_ready = True
            mock_pipeline.query.return_value = mock_response

            yield TestClient(app)

    def test_query_returns_200(self, client_with_query):
        resp = client_with_query.post(
            "/api/query",
            json={"question": "What is the House of Wisdom?"},
        )
        assert resp.status_code == 200

    def test_query_empty_question_rejected(self, client_with_query):
        resp = client_with_query.post(
            "/api/query",
            json={"question": "  "},
        )
        assert resp.status_code == 422  # Pydantic validation

    def test_query_too_short_rejected(self, client_with_query):
        resp = client_with_query.post(
            "/api/query",
            json={"question": "Hi"},
        )
        assert resp.status_code == 422

    def test_sample_questions(self, client_with_query):
        resp = client_with_query.get("/api/sample-questions")
        assert resp.status_code == 200
        data = resp.json()
        assert "questions" in data
        assert len(data["questions"]) > 0


class TestAdminEndpoints:

    @pytest.fixture
    def admin_client(self):
        mock_metrics = SystemMetrics(
            total_queries=150,
            avg_response_time_ms=2300.0,
            avg_retrieval_time_ms=300.0,
            avg_generation_time_ms=2000.0,
            queries_last_hour=12,
            error_rate=0.02,
        )

        with (
            patch("athar.api.routes.admin.pipeline") as mock_pipeline,
            patch("athar.api.routes.health.pipeline", mock_pipeline),
        ):
            mock_pipeline.is_ready = True
            mock_pipeline.get_metrics.return_value = mock_metrics
            mock_pipeline.semantic.count.return_value = 1250
            mock_pipeline.semantic.get_collection_metadata.return_value = {
                "name": "islamic_heritage",
                "count": 1250,
                "embedding_model": "all-MiniLM-L6-v2",
            }

            with patch("athar.api.routes.admin.get_ingestion_metadata") as mock_meta:
                mock_meta.return_value = {
                    "last_ingested": "2026-07-12T00:00:00",
                    "articles_fetched": 40,
                    "topics": ["House of Wisdom", "Alhambra"],
                }

                yield TestClient(app)

    def test_metrics_endpoint(self, admin_client):
        resp = admin_client.get("/api/admin/metrics")
        assert resp.status_code == 200

    def test_kb_stats_endpoint(self, admin_client):
        resp = admin_client.get("/api/admin/kb/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_chunks" in data
        assert "collection_name" in data
