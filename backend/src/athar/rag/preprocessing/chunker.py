"""
RecursiveCharacterTextSplitter — proper text chunking with sentence awareness.
Respects paragraph → sentence → word boundaries for clean semantic chunks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """Represents a text chunk with associated metadata."""
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.content)


class RecursiveCharacterTextSplitter:
    """
    Splits text recursively by trying progressively smaller separators.
    Priority: paragraph → sentence → clause → word.

    This ensures chunks don't break mid-sentence, which improves
    retrieval quality significantly over naive word splitting.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 600,
        chunk_overlap: int = 100,
        separators: list[str] | None = None,
        length_function: Any = len,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.DEFAULT_SEPARATORS
        self.length_function = length_function

    def split_text(self, text: str) -> list[str]:
        """Split text into chunks respecting semantic boundaries."""
        return self._split_text_recursive(text, self.separators)

    def _split_text_recursive(self, text: str, separators: list[str]) -> list[str]:
        """Try each separator in order until chunks are small enough."""
        final_chunks: list[str] = []

        # Pick the first separator that actually splits the text
        separator = separators[-1]  # fallback: character-level
        new_separators: list[str] = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        splits = self._split_on_separator(text, separator)
        good_splits: list[str] = []

        for split in splits:
            if self.length_function(split) < self.chunk_size:
                good_splits.append(split)
            else:
                # This split is still too long — recurse
                if good_splits:
                    merged = self._merge_splits(good_splits, separator)
                    final_chunks.extend(merged)
                    good_splits = []
                if not new_separators:
                    final_chunks.append(split)
                else:
                    other_info = self._split_text_recursive(split, new_separators)
                    final_chunks.extend(other_info)

        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            final_chunks.extend(merged)

        return final_chunks

    def _split_on_separator(self, text: str, separator: str) -> list[str]:
        """Split text on separator, keeping the separator attached."""
        if separator:
            parts = text.split(separator)
            # Re-attach separator to each part (except the last)
            result = []
            for i, part in enumerate(parts):
                if i < len(parts) - 1:
                    result.append(part + separator)
                else:
                    result.append(part)
            return [p for p in result if p.strip()]
        else:
            return list(text)

    def _merge_splits(self, splits: list[str], separator: str) -> list[str]:
        """Merge small splits into chunks with overlap."""
        chunks: list[str] = []
        current_doc: list[str] = []
        current_len = 0

        for split in splits:
            split_len = self.length_function(split)

            if current_len + split_len > self.chunk_size and current_doc:
                # Finalize current chunk
                chunk = "".join(current_doc).strip()
                if chunk:
                    chunks.append(chunk)

                # Overlap: keep the tail of the current doc
                while current_len > self.chunk_overlap and current_doc:
                    removed = current_doc.pop(0)
                    current_len -= self.length_function(removed)

            current_doc.append(split)
            current_len += split_len

        # Remaining splits
        if current_doc:
            chunk = "".join(current_doc).strip()
            if chunk:
                chunks.append(chunk)

        return chunks

    def create_documents(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> list[Document]:
        """Split multiple texts and pair each chunk with its metadata."""
        _metadatas = metadatas or [{} for _ in texts]
        documents: list[Document] = []

        for text, meta in zip(texts, _metadatas):
            chunks = self.split_text(text)
            for i, chunk in enumerate(chunks):
                chunk_meta = {**meta, "chunk_index": i, "total_chunks": len(chunks)}
                documents.append(Document(content=chunk, metadata=chunk_meta))

        return documents


def clean_text(text: str) -> str:
    """Clean extracted text before chunking."""
    # Remove excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    # Remove Wikipedia-style citation markers [1], [2], etc.
    text = re.sub(r"\[\d+\]", "", text)
    # Remove edit section markers
    text = re.sub(r"\[edit\]", "", text)
    return text.strip()
