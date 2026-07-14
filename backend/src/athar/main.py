"""FastAPI application entry point."""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from athar.api.middleware import LoggingMiddleware
from athar.api.routes import admin, health, query
from athar.config import settings
from athar.rag.pipeline import pipeline

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    try:
        pipeline.initialize()
        logger.info("RAG pipeline ready.")
    except Exception as e:
        logger.error("Pipeline init failed: %s", e)
        logger.warning("Run 'python scripts/ingest.py' to populate the knowledge base.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Athar AI — Islamic Heritage Explorer",
    description=(
        "Conversational AI for exploring Islamic history, art, architecture, and science. "
        "Built on a hybrid RAG pipeline combining BM25 keyword search and semantic "
        "vector retrieval over a curated knowledge base of Wikipedia articles."
    ),
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(health.router)
app.include_router(query.router)
app.include_router(admin.router)


if __name__ == "__main__":
    uvicorn.run(
        "athar.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
