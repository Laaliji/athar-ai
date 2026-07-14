"""
Advanced context building and compression for RAG pipeline.

Features:
- Intelligent chunk reordering based on relevance
- Context compression to fit within token limits
- Redundancy removal
- Source diversity optimization
- Query-aware context formatting
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from athar.models.schemas import ConversationMessage, RetrievedChunk

logger = logging.getLogger(__name__)


@dataclass
class ContextChunk:
    """Processed context chunk with metadata."""
    content: str
    source_title: str
    score: float
    position: int
    token_count: int


class ContextCompressor:
    """
    Compress retrieved context to fit within token limits.
    
    Strategies:
    - Remove redundant information
    - Trim less relevant sentences
    - Prioritize unique information
    """
    
    # Rough estimate: 1 token ≈ 4 characters for English text
    CHARS_PER_TOKEN = 4
    
    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """
        Estimate token count from character count.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        return len(text) // cls.CHARS_PER_TOKEN
    
    @classmethod
    def compress_chunk(
        cls,
        chunk: RetrievedChunk,
        max_tokens: int = 150,
        preserve_structure: bool = True,
    ) -> str:
        """
        Compress a single chunk to target token count.
        
        Args:
            chunk: Retrieved chunk to compress
            max_tokens: Maximum tokens to keep
            preserve_structure: Keep sentence boundaries
            
        Returns:
            Compressed text
        """
        content = chunk.content.strip()
        current_tokens = cls.estimate_tokens(content)
        
        if current_tokens <= max_tokens:
            return content
        
        if preserve_structure:
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', content)
            
            # Keep sentences until we hit the limit
            compressed_sentences = []
            token_count = 0
            
            for sentence in sentences:
                sentence_tokens = cls.estimate_tokens(sentence)
                if token_count + sentence_tokens <= max_tokens:
                    compressed_sentences.append(sentence)
                    token_count += sentence_tokens
                else:
                    break
            
            if compressed_sentences:
                return ' '.join(compressed_sentences)
        
        # Fallback: character-based truncation
        target_chars = max_tokens * cls.CHARS_PER_TOKEN
        return content[:target_chars] + "…"
    
    @classmethod
    def remove_redundancy(cls, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """
        Remove highly similar chunks to reduce redundancy.
        
        Uses simple n-gram overlap detection.
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            Deduplicated chunks
        """
        if len(chunks) <= 1:
            return chunks
        
        def get_ngrams(text: str, n: int = 3) -> set[str]:
            """Extract character n-grams from text."""
            text = text.lower()
            return {text[i:i+n] for i in range(len(text) - n + 1)}
        
        def similarity(text1: str, text2: str) -> float:
            """Calculate Jaccard similarity between two texts."""
            ngrams1 = get_ngrams(text1)
            ngrams2 = get_ngrams(text2)
            
            if not ngrams1 or not ngrams2:
                return 0.0
            
            intersection = len(ngrams1 & ngrams2)
            union = len(ngrams1 | ngrams2)
            
            return intersection / union if union > 0 else 0.0
        
        # Keep first chunk, compare others
        unique_chunks = [chunks[0]]
        
        for chunk in chunks[1:]:
            # Check similarity with already selected chunks
            is_redundant = False
            for selected in unique_chunks:
                sim = similarity(chunk.content, selected.content)
                if sim > 0.7:  # 70% similarity threshold
                    is_redundant = True
                    logger.debug(
                        "Removing redundant chunk (similarity=%.2f with %s)",
                        sim, selected.metadata.get('title', 'unknown')[:30]
                    )
                    break
            
            if not is_redundant:
                unique_chunks.append(chunk)
        
        return unique_chunks


class ContextBuilder:
    """
    Build optimized context from retrieved chunks.
    
    Features:
    - Relevance-based ordering
    - Source diversity optimization
    - Token budget management
    - Conversation history integration
    """
    
    def __init__(
        self,
        max_context_tokens: int = 2000,
        max_history_tokens: int = 500,
        chunk_max_tokens: int = 150,
    ):
        """
        Initialize context builder.
        
        Args:
            max_context_tokens: Maximum total context tokens
            max_history_tokens: Maximum tokens for conversation history
            chunk_max_tokens: Maximum tokens per chunk
        """
        self.max_context_tokens = max_context_tokens
        self.max_history_tokens = max_history_tokens
        self.chunk_max_tokens = chunk_max_tokens
        self.compressor = ContextCompressor()
    
    def build(
        self,
        chunks: list[RetrievedChunk],
        conversation_history: list[ConversationMessage] | None = None,
        remove_redundancy: bool = True,
    ) -> str:
        """
        Build complete context string from chunks and history.
        
        Args:
            chunks: Retrieved chunks
            conversation_history: Optional conversation history
            remove_redundancy: Whether to remove redundant chunks
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return ""
        
        # Step 1: Remove redundancy if requested
        if remove_redundancy:
            chunks = self.compressor.remove_redundancy(chunks)
            logger.debug("After redundancy removal: %d chunks", len(chunks))
        
        # Step 2: Reorder chunks for optimal context
        ordered_chunks = self._reorder_chunks(chunks)
        
        # Step 3: Format conversation history
        history_text = ""
        history_tokens = 0
        if conversation_history:
            history_text = self._format_history(conversation_history)
            history_tokens = self.compressor.estimate_tokens(history_text)
            
            # Trim history if too long
            if history_tokens > self.max_history_tokens:
                logger.debug(
                    "Trimming conversation history from %d to %d tokens",
                    history_tokens, self.max_history_tokens
                )
                history_text = self._trim_history(history_text, self.max_history_tokens)
                history_tokens = self.max_history_tokens
        
        # Step 4: Calculate available tokens for chunks
        available_tokens = self.max_context_tokens - history_tokens
        
        # Step 5: Build document context with compression
        doc_context = self._build_document_context(ordered_chunks, available_tokens)
        
        # Step 6: Combine history and documents
        if history_text:
            context = f"{history_text}\n\n---\n\nKnowledge base:\n\n{doc_context}"
        else:
            context = doc_context
        
        final_tokens = self.compressor.estimate_tokens(context)
        logger.debug(
            "Context built: %d tokens (history=%d, docs=%d, chunks=%d)",
            final_tokens, history_tokens, final_tokens - history_tokens, len(ordered_chunks)
        )
        
        return context
    
    def _reorder_chunks(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """
        Reorder chunks for optimal context.
        
        Strategy:
        - Highest-scoring chunk first (most relevant)
        - Alternate between different sources for diversity
        - Keep very high-scoring chunks near the start
        
        Args:
            chunks: Original chunks
            
        Returns:
            Reordered chunks
        """
        if len(chunks) <= 2:
            return chunks
        
        # Group by source
        by_source: dict[str, list[tuple[int, RetrievedChunk]]] = defaultdict(list)
        for i, chunk in enumerate(chunks):
            source_title = chunk.metadata.get('title', 'unknown')
            score = self._get_combined_score(chunk)
            by_source[source_title].append((i, chunk))
        
        # Sort each source's chunks by score
        for source in by_source:
            by_source[source].sort(key=lambda x: self._get_combined_score(x[1]), reverse=True)
        
        # Interleave chunks from different sources
        reordered = []
        source_keys = list(by_source.keys())
        source_index = 0
        
        while any(by_source.values()):
            source = source_keys[source_index % len(source_keys)]
            
            if by_source[source]:
                _, chunk = by_source[source].pop(0)
                reordered.append(chunk)
            
            source_index += 1
            
            # Remove empty sources
            if not by_source[source]:
                del by_source[source]
                source_keys = list(by_source.keys())
                if not source_keys:
                    break
        
        return reordered
    
    def _get_combined_score(self, chunk: RetrievedChunk) -> float:
        """
        Calculate combined relevance score.
        
        Priority: rerank_score > hybrid_score > max(semantic, bm25)
        """
        if chunk.rerank_score > 0:
            return chunk.rerank_score
        if chunk.hybrid_score > 0:
            return chunk.hybrid_score
        return max(chunk.semantic_score, chunk.bm25_score)
    
    def _build_document_context(
        self,
        chunks: list[RetrievedChunk],
        available_tokens: int,
    ) -> str:
        """
        Build document context within token budget.
        
        Args:
            chunks: Ordered chunks
            available_tokens: Token budget
            
        Returns:
            Formatted document context
        """
        context_parts = []
        used_tokens = 0
        
        for i, chunk in enumerate(chunks, 1):
            # Calculate tokens needed for this chunk (with formatting)
            title = chunk.metadata.get('title', 'Source')
            chunk_prefix = f"[{i}] {title}\n"
            prefix_tokens = self.compressor.estimate_tokens(chunk_prefix)
            
            # Determine how many tokens we can use for content
            chunk_budget = min(
                self.chunk_max_tokens,
                available_tokens - used_tokens - prefix_tokens - 10  # buffer
            )
            
            if chunk_budget < 30:  # Minimum useful chunk size
                logger.debug("Token budget exhausted after %d chunks", i - 1)
                break
            
            # Compress chunk if needed
            compressed_content = self.compressor.compress_chunk(
                chunk,
                max_tokens=chunk_budget,
                preserve_structure=True,
            )
            
            chunk_text = f"{chunk_prefix}{compressed_content}"
            context_parts.append(chunk_text)
            
            used_tokens += self.compressor.estimate_tokens(chunk_text)
        
        return "\n\n---\n\n".join(context_parts)
    
    def _format_history(self, history: list[ConversationMessage]) -> str:
        """
        Format conversation history.
        
        Args:
            history: Conversation messages
            
        Returns:
            Formatted history string
        """
        if not history:
            return ""
        
        formatted = ["Previous conversation:"]
        
        for msg in history[-6:]:  # Last 3 turns (6 messages)
            role = msg.role.capitalize()
            content = msg.content[:300]  # Trim long messages
            if len(msg.content) > 300:
                content += "…"
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _trim_history(self, history_text: str, max_tokens: int) -> str:
        """
        Trim history to fit token budget.
        
        Args:
            history_text: Formatted history
            max_tokens: Token budget
            
        Returns:
            Trimmed history
        """
        target_chars = max_tokens * self.compressor.CHARS_PER_TOKEN
        
        if len(history_text) <= target_chars:
            return history_text
        
        # Try to keep whole turns
        lines = history_text.split('\n')
        trimmed_lines = [lines[0]]  # Keep header
        current_chars = len(lines[0])
        
        for line in lines[1:]:
            if current_chars + len(line) + 1 <= target_chars:
                trimmed_lines.append(line)
                current_chars += len(line) + 1
            else:
                break
        
        return '\n'.join(trimmed_lines)


# Global instance
_context_builder: ContextBuilder | None = None


def get_context_builder() -> ContextBuilder:
    """Get or create global context builder instance."""
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
    return _context_builder
