"""
BM25 keyword retrieval using the rank_bm25 library.

BM25 (Best Match 25) is a bag-of-words retrieval function that excels at
exact keyword matching, making it complementary to dense semantic search.
Combining both is the foundation of Hybrid RAG.

Enhanced with:
- Porter stemming for better term matching
- N-gram support for phrase matching
- Expanded stopword list
- Configurable BM25 parameters (k1, b)
"""

from __future__ import annotations

import logging
import pickle
import re
import string
from pathlib import Path

from rank_bm25 import BM25Okapi, BM25Plus

from athar.models.schemas import RetrievedChunk
from athar.rag.preprocessing.chunker import Document

logger = logging.getLogger(__name__)


class EnhancedTokenizer:
    """
    Advanced tokenizer for BM25 with stemming and n-gram support.
    
    Features:
    - Porter stemming for term normalization
    - Comprehensive stopword filtering
    - Alphanumeric normalization
    - Optional bigram generation
    """
    
    # Expanded stopword list (English + common query words)
    STOPWORDS = {
        # Articles & determiners
        "a", "an", "the",
        # Pronouns
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
        "you", "your", "yours", "yourself", "yourselves",
        "he", "him", "his", "himself", "she", "her", "hers", "herself",
        "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
        # Auxiliary verbs
        "am", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "having",
        "do", "does", "did", "doing",
        "will", "would", "shall", "should", "may", "might", "must", "can", "could",
        # Prepositions
        "of", "at", "by", "for", "with", "about", "against", "between",
        "into", "through", "during", "before", "after", "above", "below",
        "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
        # Conjunctions
        "and", "but", "or", "nor", "so", "yet",
        # Common words
        "as", "if", "than", "then", "when", "where", "which", "who", "whom", "whose", "why",
        "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
        "no", "not", "only", "own", "same", "than", "too", "very",
        "this", "that", "these", "those",
        # Query words (often not useful for matching)
        "what", "tell", "show", "explain", "describe",
    }
    
    def __init__(self, use_stemming: bool = True, use_bigrams: bool = False):
        """
        Initialize tokenizer.
        
        Args:
            use_stemming: Apply Porter stemming to tokens
            use_bigrams: Generate bigrams in addition to unigrams
        """
        self.use_stemming = use_stemming
        self.use_bigrams = use_bigrams
        self._stemmer = None
        
        if use_stemming:
            try:
                from nltk.stem import PorterStemmer
                self._stemmer = PorterStemmer()
            except ImportError:
                logger.warning(
                    "NLTK not available for stemming. Install with: pip install nltk"
                )
                self.use_stemming = False
    
    def tokenize(self, text: str) -> list[str]:
        """
        Tokenize text with normalization, stopword removal, and optional stemming.
        
        Args:
            text: Input text to tokenize
            
        Returns:
            List of processed tokens
        """
        if not text:
            return []
        
        # Lowercase
        text = text.lower()
        
        # Keep alphanumeric and spaces, replace others with space
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        # Split and filter
        tokens = text.split()
        
        # Remove stopwords and short tokens
        tokens = [
            t for t in tokens 
            if t not in self.STOPWORDS and len(t) > 1 and not t.isdigit()
        ]
        
        # Apply stemming
        if self.use_stemming and self._stemmer:
            tokens = [self._stemmer.stem(t) for t in tokens]
        
        # Generate bigrams if enabled
        if self.use_bigrams and len(tokens) > 1:
            bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
            tokens.extend(bigrams)
        
        return tokens


def _tokenize(text: str) -> list[str]:
    """
    Backward-compatible tokenization function.
    Uses the enhanced tokenizer with default settings.
    """
    tokenizer = EnhancedTokenizer(use_stemming=False, use_bigrams=False)
    return tokenizer.tokenize(text)


class BM25Retriever:
    """
    In-memory BM25 index built over all document chunks.

    BM25 handles queries with specific terms (names, places, dates) very
    well — cases where dense embeddings sometimes struggle.
    
    Enhanced with:
    - Advanced tokenization (optional stemming)
    - BM25Plus variant support (better for longer documents)
    - Configurable BM25 parameters (k1, b)
    - Score normalization options
    """

    def __init__(
        self,
        use_stemming: bool = True,
        use_bigrams: bool = False,
        variant: str = "okapi",  # "okapi" or "plus"
        k1: float = 1.5,  # Term frequency saturation
        b: float = 0.75,  # Length normalization
    ) -> None:
        """
        Initialize BM25 retriever.
        
        Args:
            use_stemming: Apply Porter stemming
            use_bigrams: Generate bigrams for phrase matching
            variant: BM25 variant ("okapi" or "plus")
            k1: Controls term frequency saturation (typical: 1.2-2.0)
            b: Controls length normalization (typical: 0.75)
        """
        self._index: BM25Okapi | BM25Plus | None = None
        self._documents: list[Document] = []
        self._tokenizer = EnhancedTokenizer(use_stemming, use_bigrams)
        self._variant = variant
        self._k1 = k1
        self._b = b
        self._is_ready = False

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def build_index(self, documents: list[Document]) -> None:
        """
        Build BM25 index from a list of Document chunks.
        
        Args:
            documents: List of Document objects to index
        """
        if not documents:
            logger.warning("BM25: no documents provided.")
            return

        self._documents = documents
        tokenized = [self._tokenizer.tokenize(doc.content) for doc in documents]

        logger.info(
            "Building BM25 index (%s) over %d chunks (stemming=%s, bigrams=%s)…",
            self._variant,
            len(tokenized),
            self._tokenizer.use_stemming,
            self._tokenizer.use_bigrams,
        )
        
        # Choose BM25 variant
        if self._variant == "plus":
            self._index = BM25Plus(tokenized, k1=self._k1, b=self._b)
        else:  # okapi (default)
            self._index = BM25Okapi(tokenized, k1=self._k1, b=self._b)
        
        self._is_ready = True
        logger.info("BM25 index ready (k1=%.2f, b=%.2f).", self._k1, self._b)

    def retrieve(
        self, 
        query: str, 
        k: int = 6,
        normalize_scores: bool = True,
    ) -> list[RetrievedChunk]:
        """
        Return top-k chunks ranked by BM25 score.
        
        Args:
            query: User query string
            k: Number of results to return
            normalize_scores: Whether to normalize scores to [0, 1]

        Returns:
            List of RetrievedChunk sorted by bm25_score (descending).
        """
        if not self._is_ready or self._index is None:
            logger.warning("BM25 index not built.")
            return []

        query_tokens = self._tokenizer.tokenize(query)
        if not query_tokens:
            logger.debug("BM25: Query produced no valid tokens after processing")
            return []

        scores = self._index.get_scores(query_tokens)

        # Get top-k indices
        top_k = min(k, len(self._documents))
        top_indices = sorted(
            range(len(scores)), 
            key=lambda i: scores[i], 
            reverse=True
        )[:top_k]

        chunks: list[RetrievedChunk] = []
        
        # Find max score for normalization
        max_score = max(scores[idx] for idx in top_indices) if top_indices else 1.0
        
        for idx in top_indices:
            score = scores[idx]
            if score <= 0:
                continue

            # Normalize score to [0, 1] if requested
            if normalize_scores and max_score > 0:
                normalized = score / max_score
            else:
                normalized = score

            chunks.append(
                RetrievedChunk(
                    content=self._documents[idx].content,
                    metadata=self._documents[idx].metadata,
                    bm25_score=normalized,
                )
            )
        
        logger.debug(
            "BM25 retrieved %d chunks (query_tokens=%d, top_score=%.3f)",
            len(chunks),
            len(query_tokens),
            chunks[0].bm25_score if chunks else 0.0,
        )

        return chunks

    def save(self, path: Path) -> None:
        """Persist the BM25 index to disk with tokenizer settings."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "index": self._index,
                    "documents": self._documents,
                    "use_stemming": self._tokenizer.use_stemming,
                    "use_bigrams": self._tokenizer.use_bigrams,
                    "variant": self._variant,
                    "k1": self._k1,
                    "b": self._b,
                }, 
                f
            )
        logger.info("BM25 index saved to %s", path)

    def load(self, path: Path) -> bool:
        """
        Load a previously saved BM25 index. Returns True on success.
        
        Automatically recreates tokenizer with saved settings.
        """
        if not path.exists():
            return False
        
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            
            self._index = data["index"]
            self._documents = data["documents"]
            
            # Restore tokenizer settings (with backward compatibility)
            use_stemming = data.get("use_stemming", False)
            use_bigrams = data.get("use_bigrams", False)
            self._tokenizer = EnhancedTokenizer(use_stemming, use_bigrams)
            
            # Restore BM25 parameters
            self._variant = data.get("variant", "okapi")
            self._k1 = data.get("k1", 1.5)
            self._b = data.get("b", 0.75)
            
            self._is_ready = True
            logger.info(
                "BM25 index loaded from %s (%d docs, variant=%s, stemming=%s)",
                path, len(self._documents), self._variant, use_stemming
            )
            return True
        except Exception as e:
            logger.error("Failed to load BM25 index from %s: %s", path, e)
            return False

    @property
    def document_count(self) -> int:
        return len(self._documents)
