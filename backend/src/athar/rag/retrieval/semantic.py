"""Persistent semantic retrieval backed by ChromaDB.

The primary embedding backend is ``sentence-transformers``.  When that model
is not available, the retriever deliberately falls back to a *stateless*
feature-hashing encoder.  Unlike a fitted TF-IDF vocabulary, feature hashing
produces the same vector for the same text after a process restart, which is
essential for a persisted vector collection.

Enhanced with Maximal Marginal Relevance (MMR) for diversity-aware retrieval.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Protocol

import chromadb
import numpy as np
from chromadb.config import Settings as ChromaSettings

from athar.config import CHROMA_DIR, settings
from athar.models.schemas import RetrievedChunk
from athar.rag.preprocessing.chunker import Document

logger = logging.getLogger(__name__)


class EmbeddingFunction(Protocol):
    """Minimal Chroma-compatible embedding function contract."""

    def __call__(self, input: list[str]) -> list[list[float]]:
        """Embed a batch of documents or queries."""


class SentenceTransformerEmbeddingFunction:
    """Normalized dense embeddings from a local sentence-transformers model."""

    def __init__(self, model_name: str, device: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model_name = model_name
        self._model = SentenceTransformer(model_name, device=device)
        self.dimension = int(self._model.get_sentence_embedding_dimension())

    def __call__(self, input: list[str]) -> list[list[float]]:
        vectors = self._model.encode(
            input,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()


class HashingEmbeddingFunction:
    """Stable, dependency-free fallback based on signed feature hashing.

    This is intentionally not presented as a dense semantic model.  It keeps
    the application usable in constrained environments while guaranteeing
    that stored and query vectors share the same space across restarts.
    """

    DIM = 768
    _TOKEN_RE = re.compile(r"[^\w\s]", re.UNICODE)

    @classmethod
    def _tokens(cls, text: str) -> list[str]:
        words = [
            word
            for word in cls._TOKEN_RE.sub(" ", text.lower()).split()
            if len(word) > 2 and not word.isdigit()
        ]
        # Bigrams retain a little phrase information without any fitted state.
        return words + [f"{a}_{b}" for a, b in zip(words, words[1:])]

    @classmethod
    def _embed_one(cls, text: str) -> list[float]:
        vector = [0.0] * cls.DIM
        counts = Counter(cls._tokens(text))
        for token, count in counts.items():
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % cls.DIM
            vector[index] += count if value & 1 else -count

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in input]


def _create_embedding_function() -> tuple[EmbeddingFunction, str, int]:
    """Create one embedding backend and an immutable collection profile."""
    try:
        embedding_function = SentenceTransformerEmbeddingFunction(
            settings.embedding_model,
            settings.embedding_device,
        )
        profile = f"sentence-transformers:{settings.embedding_model}"
        logger.info("Using dense embeddings: %s", settings.embedding_model)
        return embedding_function, profile, embedding_function.dimension
    except Exception as exc:
        logger.warning(
            "Dense embeddings unavailable (%s); using stable hashing fallback.", exc
        )
        return HashingEmbeddingFunction(), "hashing-v1", HashingEmbeddingFunction.DIM


class SemanticRetriever:
    """ChromaDB collection with an embedding profile checked on every startup."""

    def __init__(self) -> None:
        self._client: chromadb.PersistentClient | None = None
        self._collection: chromadb.Collection | None = None
        self._embed_fn: EmbeddingFunction | None = None
        self._embedding_profile = "uninitialized"
        self._embed_dim = 0
        self._is_ready = False

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @property
    def embedding_profile(self) -> str:
        return self._embedding_profile

    def initialize(self, reset_incompatible: bool = False) -> None:
        """Connect to the persistent collection using a CWD-independent path."""
        self._embed_fn, self._embedding_profile, self._embed_dim = _create_embedding_function()
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        existing_names = {
            getattr(collection, "name", str(collection))
            for collection in self._client.list_collections()
        }
        if settings.chroma_collection in existing_names:
            collection = self._client.get_collection(
                name=settings.chroma_collection,
                embedding_function=self._embed_fn,
            )
            metadata = collection.metadata or {}
            stored_profile = metadata.get("embedding_profile")
            if stored_profile != self._embedding_profile:
                if collection.count() and not reset_incompatible:
                    raise RuntimeError(
                        "The existing vector collection was created with a different "
                        f"embedding profile ({stored_profile or 'unknown'}). "
                        "Run ingestion with --overwrite to rebuild it."
                    )
                self._client.delete_collection(settings.chroma_collection)
                self._collection = self._create_collection()
            else:
                self._collection = collection
        else:
            self._collection = self._create_collection()

        logger.info(
            "ChromaDB ready — collection '%s' has %d chunks (%s)",
            settings.chroma_collection,
            self.count(),
            self._embedding_profile,
        )
        self._is_ready = True

    def add_documents(self, documents: list[Document]) -> int:
        """Upsert chunks with collision-resistant, source-stable identifiers."""
        self._require_ready()
        if not documents:
            return 0

        texts = [document.content for document in documents]
        metadatas = [_clean_metadata(document.metadata) for document in documents]
        ids = [_document_id(document) for document in documents]

        batch_size = 128
        for start in range(0, len(texts), batch_size):
            end = start + batch_size
            self._collection.upsert(  # type: ignore[union-attr]
                ids=ids[start:end],
                documents=texts[start:end],
                metadatas=metadatas[start:end],
            )
            logger.info("Indexed %d/%d chunks", min(end, len(texts)), len(texts))

        return len(documents)

    def retrieve(
        self, 
        query: str, 
        k: int | None = None,
        use_mmr: bool = False,
        mmr_lambda: float = 0.5,
    ) -> list[RetrievedChunk]:
        """
        Return semantic candidates ordered by cosine similarity.
        
        Args:
            query: User query string
            k: Number of results to return
            use_mmr: Whether to use MMR for diversity
            mmr_lambda: MMR diversity parameter (0=max diversity, 1=max relevance)
            
        Returns:
            List of retrieved chunks with semantic scores
        """
        self._require_ready()
        n_documents = self.count()
        if not n_documents:
            return []

        # Fetch more candidates if using MMR (need larger pool for diversity)
        fetch_k = k or settings.retrieval_top_k
        if use_mmr:
            fetch_k = min(fetch_k * 3, n_documents)  # 3x candidates for MMR

        results = self._collection.query(  # type: ignore[union-attr]
            query_texts=[query],
            n_results=min(fetch_k, n_documents),
            include=["documents", "metadatas", "distances", "embeddings"],
        )
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        embeddings = results.get("embeddings", [[]])[0] if use_mmr else None

        chunks: list[RetrievedChunk] = []
        for i, (document, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
            similarity = max(0.0, 1.0 - float(distance))
            if similarity >= settings.min_similarity:
                chunk = RetrievedChunk(
                    content=document,
                    metadata=metadata or {},
                    semantic_score=similarity,
                )
                # Store embedding for MMR if needed
                if embeddings and i < len(embeddings):
                    chunk.embedding = embeddings[i]
                chunks.append(chunk)
        
        # Apply MMR if requested
        if use_mmr and chunks and embeddings:
            # Get query embedding
            query_embedding = self._embed_fn([query])[0]  # type: ignore[misc]
            chunks = self._apply_mmr(
                chunks=chunks,
                query_embedding=query_embedding,
                k=k or settings.retrieval_top_k,
                lambda_param=mmr_lambda,
            )
            logger.debug("Applied MMR to %d candidates -> %d diverse results", len(chunks), k or settings.retrieval_top_k)
        
        return chunks
    
    def _apply_mmr(
        self,
        chunks: list[RetrievedChunk],
        query_embedding: list[float],
        k: int,
        lambda_param: float = 0.5,
    ) -> list[RetrievedChunk]:
        """
        Apply Maximal Marginal Relevance for diversity-aware ranking.
        
        MMR Formula: MMR = λ * Sim(q, d) - (1-λ) * max(Sim(d, d_i))
        where d_i are already selected documents.
        
        Args:
            chunks: Candidate chunks with embeddings
            query_embedding: Query vector
            k: Number of results to return
            lambda_param: Trade-off between relevance (1.0) and diversity (0.0)
            
        Returns:
            Reranked chunks with diversity considered
        """
        if not chunks or k <= 0:
            return chunks
        
        # Convert to numpy for efficient computation
        query_vec = np.array(query_embedding).reshape(1, -1)
        
        # Extract embeddings and normalize
        chunk_embeddings = []
        for chunk in chunks:
            if hasattr(chunk, 'embedding') and chunk.embedding:
                chunk_embeddings.append(np.array(chunk.embedding))
            else:
                # Fallback: use zeros (will have low MMR score)
                chunk_embeddings.append(np.zeros_like(query_vec[0]))
        
        doc_vectors = np.array(chunk_embeddings)
        
        # Normalize vectors for cosine similarity
        query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        doc_vectors = doc_vectors / (np.linalg.norm(doc_vectors, axis=1, keepdims=True) + 1e-10)
        
        # Compute query-document similarities
        query_sims = (doc_vectors @ query_vec.T).flatten()
        
        # MMR selection
        selected_indices = []
        remaining_indices = list(range(len(chunks)))
        
        for _ in range(min(k, len(chunks))):
            if not remaining_indices:
                break
            
            mmr_scores = []
            for idx in remaining_indices:
                # Relevance term
                relevance = query_sims[idx]
                
                # Diversity term (max similarity to already selected docs)
                if selected_indices:
                    selected_vecs = doc_vectors[selected_indices]
                    doc_vec = doc_vectors[idx].reshape(1, -1)
                    diversities = (selected_vecs @ doc_vec.T).flatten()
                    max_similarity = np.max(diversities)
                else:
                    max_similarity = 0.0
                
                # MMR score
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity
                mmr_scores.append((idx, mmr_score))
            
            # Select document with highest MMR score
            best_idx, best_score = max(mmr_scores, key=lambda x: x[1])
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)
        
        # Return chunks in MMR order
        mmr_chunks = [chunks[idx] for idx in selected_indices]
        
        # Update semantic scores to reflect MMR ranking (for downstream use)
        for i, chunk in enumerate(mmr_chunks):
            # Decay score based on MMR position to maintain ranking signal
            chunk.semantic_score = chunk.semantic_score * (0.95 ** i)
        
        return mmr_chunks

    def get_all_documents(self) -> list[Document]:
        """Return the full corpus for deterministic BM25 rebuilds."""
        self._require_ready()
        if not self.count():
            return []
        result = self._collection.get(  # type: ignore[union-attr]
            include=["documents", "metadatas"],
        )
        return [
            Document(content=document, metadata=metadata or {})
            for document, metadata in zip(
                result.get("documents", []), result.get("metadatas", [])
            )
            if document
        ]

    def count(self) -> int:
        return self._collection.count() if self._collection is not None else 0

    def reset_collection(self) -> None:
        self._require_ready()
        self._client.delete_collection(settings.chroma_collection)  # type: ignore[union-attr]
        self._collection = self._create_collection()
        logger.info("ChromaDB collection reset.")

    def get_collection_metadata(self) -> dict[str, Any]:
        if not self._is_ready:
            return {}
        return {
            "name": settings.chroma_collection,
            "count": self.count(),
            "embedding_model": self._embedding_profile,
            "embedding_dimension": self._embed_dim,
        }

    def _require_ready(self) -> None:
        if not self._is_ready or self._collection is None:
            raise RuntimeError("SemanticRetriever not initialized.")

    def _create_collection(self) -> chromadb.Collection:
        return self._client.create_collection(  # type: ignore[union-attr]
            name=settings.chroma_collection,
            embedding_function=self._embed_fn,
            metadata={
                "hnsw:space": "cosine",
                "embedding_profile": self._embedding_profile,
                "embedding_dimension": self._embed_dim,
            },
        )


def _document_id(document: Document) -> str:
    """Stable identifier: one source and chunk position maps to one vector."""
    metadata = document.metadata
    identity = "\x1f".join(
        str(metadata.get(key, ""))
        for key in ("source", "url", "title", "chunk_index")
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _clean_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value if isinstance(value, (str, int, float, bool)) else str(value)
        for key, value in metadata.items()
    }
