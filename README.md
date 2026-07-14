# Athar AI — Islamic Heritage Explorer

A conversational RAG (Retrieval-Augmented Generation) system for exploring Islamic history, architecture, science, and art. It combines BM25 keyword search, persistent semantic retrieval, reciprocal-rank fusion, cross-encoder reranking, and source-grounded generation.

---

## Architecture

```
User Query
    │
    ├─► BM25 Retriever (rank_bm25)           ─┐
    │   keyword-based, fast exact matching     │
    │                                          ├─► RRF Fusion → top-k chunks
    └─► Semantic Retriever (ChromaDB)         ─┘
        dense embeddings, conceptual similarity
                    │
                    ▼
            Context Builder
        (chunks + conversation history)
                    │
                    ▼
           LLM Generation
        Groq → Ollama → HuggingFace
                    │
                    ▼
        Streaming SSE response
```

**Hybrid retrieval** uses Reciprocal Rank Fusion (RRF) to combine BM25 and semantic scores without requiring score normalization. BM25 excels at named entities (scholars, places, dates); semantic search handles conceptual queries.

---

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Uvicorn |
| Vector store | ChromaDB |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2`, with a deterministic hashing fallback |
| Keyword retrieval | rank-bm25 |
| LLM (primary) | Groq — Llama 3.3 70B |
| LLM (local fallback) | Ollama |
| LLM (offline fallback) | HuggingFace FLAN-T5 |
| Frontend | React 18 |
| Config | pydantic-settings |
| Testing | pytest + ruff |
| Deployment | Docker Compose |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- A free [Groq API key](https://console.groq.com) (optional but recommended)

### Setup

```bash
git clone <repo-url>
cd athar-ai

# Backend
cd backend
pip install -e ".[dev]"

# Configure (add GROQ_API_KEY for best results)
cp ../.env.example ../.env

# Build the knowledge base
cd ..
python -m athar.ingestion --overwrite

# Start the API server
cd backend
uvicorn athar.main:app --reload --port 8000
```

```bash
# Frontend (separate terminal)
cd frontend
npm install
npm start
```

Open http://localhost:3000. The API docs are at http://localhost:8000/api/docs.

### Docker

```bash
docker compose up -d
docker compose exec backend python -m athar.ingestion --overwrite
```

---

## LLM Configuration

Set `LLM_PROVIDER` in `.env`. The system falls through automatically if a provider is unavailable:

```
# .env
GROQ_API_KEY=gsk_...         # Free, fastest, best quality
LLM_PROVIDER=groq

# Or use Ollama for fully local inference:
# LLM_PROVIDER=ollama
# ollama pull llama3.2
```

---

## Knowledge Base

The ingestion pipeline fetches Wikipedia articles on Islamic civilization topics:

- **Scholars**: Ibn Khaldun, Avicenna, Averroes, Al-Kindi, Al-Khwarizmi, Al-Biruni, Alhazen
- **Architecture**: Alhambra, Dome of the Rock, Blue Mosque, Hagia Sophia, Great Mosque of Córdoba
- **History**: House of Wisdom, Islamic Golden Age, Abbasid Caliphate, Al-Andalus, Ottoman Empire
- **Science**: Islamic mathematics, astronomy, medicine, algebra
- **Art & Culture**: Islamic calligraphy, geometric patterns, arabesque, Silk Road

Running ingestion fetches up to 40 Wikipedia articles (plus Met Museum records for default ingestion), chunks them, stores vectors in ChromaDB, and rebuilds BM25 from the entire persisted corpus.

### Retrieval guarantees

- Persisted paths are resolved from the repository root, so ingestion and serving use the same ChromaDB directory.
- The default dense encoder is `all-MiniLM-L6-v2`. If it cannot load, a stable feature-hashing encoder is used; it remains compatible with stored vectors after a restart.
- Each collection records its embedding profile. The API refuses to query incompatible vectors rather than silently producing invalid rankings; rebuild them with `--overwrite`.
- Every ingestion run rebuilds BM25 from ChromaDB, preventing drift between lexical and semantic retrieval.

---

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/query` | POST | Blocking query |
| `/api/query/stream` | POST | SSE streaming query |
| `/api/health` | GET | Health check |
| `/api/status` | GET | System status |
| `/api/sample-questions` | GET | Suggested questions |
| `/api/admin/metrics` | GET | Query latency metrics |
| `/api/admin/kb/stats` | GET | Knowledge base info |
| `/api/admin/ingest` | POST | Trigger re-ingestion |

---

## Project Structure

```
athar-ai/
├── backend/
│   ├── src/athar/
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── api/routes/          # query, admin, health
│   │   ├── rag/
│   │   │   ├── pipeline.py
│   │   │   ├── retrieval/       # semantic, bm25, hybrid
│   │   │   ├── generation/      # llm.py (multi-provider)
│   │   │   └── preprocessing/   # chunker
│   │   ├── ingestion/           # fetcher, ingest pipeline
│   │   └── models/schemas.py
│   ├── tests/
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/src/
│   ├── App.js
│   ├── components/
│   │   ├── ChatInterface.js     # streaming chat
│   │   ├── AdminDashboard.js
│   │   └── ConversationSidebar.js
│   └── services/api.js
├── scripts/ingest.py
├── docker-compose.yml
└── .env.example
```

---

## Tests

```bash
cd backend
pytest tests/ -v
ruff check src tests
```

After ingestion, measure retriever hit-rate@5 and MRR against the curated evaluation set:

```bash
python scripts/evaluate_retrieval.py
```

The evaluation focuses on retrieval quality, so chunking, indexing, and ranking regressions can be detected without an LLM judge.

---

## Notes

- The `asyncio_mode` warning from pytest is harmless — it comes from the `anyio` plugin version mismatch with `pytest-asyncio`, not the project code.
- For local inference without a GPU, Ollama on CPU works fine for smaller models (`llama3.2:3b`).
- ChromaDB data persists in `./chroma_db/` between restarts. Delete it to start fresh.
