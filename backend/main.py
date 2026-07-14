# Simple Athar.AI FastAPI Backend
# Uses the working simple RAG system

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simple_rag_system import SimpleIslamicRAG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global RAG instance
rag_system: Optional[SimpleIslamicRAG] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG system on startup"""
    global rag_system
    logger.info("🌙 Initializing Simple Athar.AI RAG system...")
    
    try:
        rag_system = SimpleIslamicRAG()
        
        # Try to load cached system first
        if not rag_system.load_system():
            logger.info("Setting up RAG system from scratch...")
            if rag_system.setup():
                rag_system.save_system()
                logger.info("RAG system initialized and cached")
            else:
                logger.error("Failed to setup RAG system")
                rag_system = None
        else:
            # Still need to setup LLM
            rag_system.setup_llm()
            logger.info("RAG system loaded from cache")
            
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        rag_system = None
    
    yield
    
    logger.info("Shutting down Simple Athar.AI...")

# Create FastAPI app
app = FastAPI(
    title="Simple Athar.AI API",
    description="Islamic Heritage Explorer - Simple RAG API",
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    question: str
    max_sources: Optional[int] = 3
    
class Source(BaseModel):
    title: str
    url: str
    excerpt: str
    
class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[Source]
    processing_time: float
    model_used: str
    
class SystemStatus(BaseModel):
    status: str
    model_loaded: bool
    database_ready: bool
    
class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str

# API Routes
@app.get("/")
async def root():
    return {
        "message": "Welcome to Simple Athar.AI - Islamic Heritage Explorer API",
        "version": "2.1.0",
        "docs": "/api/docs"
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy" if rag_system else "unhealthy",
        message="Simple Athar.AI API is running" if rag_system else "RAG system not initialized",
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/status", response_model=SystemStatus)
async def get_system_status():
    if not rag_system:
        return SystemStatus(
            status="not_initialized",
            model_loaded=False,
            database_ready=False
        )
    
    return SystemStatus(
        status="ready",
        model_loaded=rag_system.llm is not None,
        database_ready=len(rag_system.documents) > 0
    )

@app.post("/api/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Query the simple RAG system"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        start_time = time.time()
        
        # Query the RAG system
        result = rag_system.query(request.question)
        
        processing_time = time.time() - start_time
        
        # Format sources
        sources = []
        for source_doc in result.get("sources", []):
            sources.append(Source(
                title=source_doc.get("title", "Unknown"),
                url=source_doc.get("url", ""),
                excerpt=source_doc.get("excerpt", "")
            ))
        
        return QueryResponse(
            question=request.question,
            answer=result.get("answer", "No answer generated"),
            sources=sources[:request.max_sources],
            processing_time=processing_time,
            model_used="Simple RAG System"
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/api/sample-questions")
async def get_sample_questions():
    """Get sample questions for the UI"""
    return {
        "questions": [
            "What was the House of Wisdom in Baghdad?",
            "Describe the key features of Islamic architecture",
            "Who was Ibn Khaldun and what were his contributions?",
            "Tell me about the Alhambra palace",
            "What innovations came from the Islamic Golden Age?",
            "Describe Moorish architecture in Al-Andalus",
            "What was the role of madrasas in Islamic education?",
            "Tell me about Islamic calligraphy and its styles"
        ]
    }

@app.get("/api/system-info")
async def get_system_info():
    """Get system information"""
    if not rag_system:
        return {"error": "RAG system not initialized"}
    
    return {
        "documents_loaded": len(rag_system.documents),
        "model_type": "Simple RAG with TF-IDF",
        "llm_type": type(rag_system.llm).__name__ if rag_system.llm else "None",
        "cache_available": os.path.exists("simple_rag_cache/rag_cache.pkl")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)