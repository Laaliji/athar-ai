"""
Query routes — the core API endpoints for RAG queries.

Supports both blocking and Server-Sent Events (SSE) streaming modes.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool

from athar.models.schemas import QueryRequest, QueryResponse
from athar.rag.pipeline import pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Query"])


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """
    Submit a question to the RAG system.

    Returns a complete answer with sources and timing metrics.
    """
    if not pipeline.is_ready:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not ready. Ensure ingestion has run.",
        )

    try:
        return await run_in_threadpool(
            pipeline.query,
            request.question,
            request.conversation_id,
            request.max_sources,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Query error: %s", e)
        raise HTTPException(status_code=500, detail="Internal processing error.")


@router.post("/query/stream")
async def query_stream(request: QueryRequest) -> StreamingResponse:
    """
    Submit a question and receive the answer as a Server-Sent Events stream.

    The client receives:
    - `sources` event first (for immediate display)
    - `token` events (one per generated token)
    - `done` event with full metadata
    - `error` event on failure

    Example client usage (JavaScript):
        const evtSource = new EventSource('/api/query/stream');
        evtSource.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.type === 'token') appendText(data.content);
        };
    """
    if not pipeline.is_ready:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline not ready.",
        )

    async def event_generator():
        try:
            stream = pipeline.stream_generate(
                question=request.question, conversation_id=request.conversation_id
            )
            async for chunk in iterate_in_threadpool(stream):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.exception("Stream error: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Important for Nginx proxies
        },
    )


@router.get("/sample-questions")
async def get_sample_questions() -> dict:
    """Return curated sample questions for the welcome screen."""
    return {
        "questions": [
            "What was the House of Wisdom in Baghdad?",
            "Describe the key features of Islamic architecture",
            "Who was Ibn Khaldun and what were his major contributions?",
            "What makes the Alhambra palace architecturally unique?",
            "What innovations came from the Islamic Golden Age?",
            "Who was Avicenna and what did he contribute to medicine?",
            "Explain the role of madrasas in Islamic education",
            "What is Islamic calligraphy and what are its major styles?",
            "Tell me about the Silk Road and Islamic trade",
            "Who was Al-Khwarizmi and why is he important?",
            "Describe Moorish architecture in Al-Andalus",
            "What was the significance of the Abbasid Caliphate?",
        ]
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> dict:
    """Retrieve conversation history for a session."""
    messages = pipeline.get_conversation(conversation_id)
    return {
        "conversation_id": conversation_id,
        "messages": [msg.model_dump() for msg in messages],
        "turn_count": len(messages) // 2,
    }


@router.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str) -> dict:
    """Clear conversation history for a session."""
    pipeline.clear_conversation(conversation_id)
    return {"message": f"Conversation {conversation_id} cleared."}
