"""Evaluate Athar's persisted hybrid retriever against curated questions.

Run after ingestion:
    python scripts/evaluate_retrieval.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from athar.config import CHROMA_DIR
from athar.evaluation import evaluate_retrieval
from athar.rag.retrieval.bm25_retriever import BM25Retriever
from athar.rag.retrieval.hybrid import HybridRetriever
from athar.rag.retrieval.semantic import SemanticRetriever


def main() -> None:
    semantic = SemanticRetriever()
    semantic.initialize()
    if not semantic.count():
        raise SystemExit("Knowledge base is empty. Run ingestion first.")

    bm25 = BM25Retriever()
    index_path = CHROMA_DIR / "bm25_index.pkl"
    if not bm25.load(index_path) or bm25.document_count != semantic.count():
        bm25.build_index(semantic.get_all_documents())
        bm25.save(index_path)

    print(json.dumps(evaluate_retrieval(HybridRetriever(semantic, bm25)), indent=2))


if __name__ == "__main__":
    main()
