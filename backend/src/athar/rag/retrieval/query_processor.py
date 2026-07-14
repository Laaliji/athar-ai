"""
Advanced query preprocessing and expansion for improved retrieval.

This module implements multiple query enhancement techniques:
1. Query cleaning (normalization, noise removal)
2. Query expansion (synonyms, related terms)
3. Query classification (factual, temporal, conceptual, etc.)
4. Multi-query generation for diverse retrieval
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Classification of query types for adaptive processing."""
    FACTUAL = "factual"          # Who, what, when, where questions
    CONCEPTUAL = "conceptual"    # Why, how, explain questions
    TEMPORAL = "temporal"        # Time-specific queries
    COMPARATIVE = "comparative"  # Comparison queries
    LISTING = "listing"          # List-based queries
    DEFINITION = "definition"    # What is X?


@dataclass
class ProcessedQuery:
    """Processed query with metadata and expansions."""
    original: str
    cleaned: str
    expanded: list[str]
    query_type: QueryType
    key_entities: list[str]
    is_complex: bool


class QueryCleaner:
    """Clean and normalize user queries."""
    
    # Common filler words that don't add semantic value
    FILLER_PATTERNS = [
        r'\b(please|kindly|can you|could you|would you)\b',
        r'\b(tell me|show me|explain to me|let me know)\b',
        r'\b(i want to know|i would like to know)\b',
        r'\b(about|regarding)\b',
    ]
    
    # Patterns for excessive punctuation
    PUNCTUATION_PATTERNS = [
        (r'\.{2,}', '.'),    # Multiple periods
        (r'\?{2,}', '?'),    # Multiple question marks
        (r'!{2,}', '!'),     # Multiple exclamation marks
        (r'\s+', ' '),       # Multiple spaces
    ]
    
    @classmethod
    def clean(cls, query: str) -> str:
        """
        Clean query by removing filler words and normalizing punctuation.
        
        Args:
            query: Raw user query
            
        Returns:
            Cleaned query string
        """
        if not query or not query.strip():
            return ""
        
        cleaned = query.strip()
        
        # Remove filler patterns (case-insensitive)
        for pattern in cls.FILLER_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Normalize punctuation
        for pattern, replacement in cls.PUNCTUATION_PATTERNS:
            cleaned = re.sub(pattern, replacement, cleaned)
        
        # Remove leading/trailing punctuation and whitespace
        cleaned = cleaned.strip(' .,!?;:')
        
        # Ensure first letter is capitalized
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        return cleaned


class QueryClassifier:
    """Classify query type for adaptive retrieval."""
    
    # Keywords indicating different query types
    FACTUAL_KEYWORDS = ['who', 'what', 'when', 'where', 'which']
    CONCEPTUAL_KEYWORDS = ['why', 'how', 'explain', 'describe', 'discuss']
    TEMPORAL_KEYWORDS = ['year', 'century', 'period', 'era', 'date', 'time', 'during']
    COMPARATIVE_KEYWORDS = ['compare', 'difference', 'versus', 'vs', 'similar', 'contrast']
    LISTING_KEYWORDS = ['list', 'name', 'examples', 'types of', 'kinds of']
    DEFINITION_KEYWORDS = ['define', 'meaning', 'what is', 'what are', 'definition']
    
    @classmethod
    def classify(cls, query: str) -> QueryType:
        """
        Classify query into one of the defined types.
        
        Args:
            query: Cleaned query string
            
        Returns:
            QueryType enum value
        """
        query_lower = query.lower()
        
        # Check each category (order matters - more specific first)
        if any(kw in query_lower for kw in cls.DEFINITION_KEYWORDS):
            return QueryType.DEFINITION
        
        if any(kw in query_lower for kw in cls.COMPARATIVE_KEYWORDS):
            return QueryType.COMPARATIVE
        
        if any(kw in query_lower for kw in cls.LISTING_KEYWORDS):
            return QueryType.LISTING
        
        # Check temporal BEFORE factual (when has both temporal and factual keywords)
        if any(kw in query_lower for kw in cls.TEMPORAL_KEYWORDS):
            return QueryType.TEMPORAL
        
        if any(kw in query_lower for kw in cls.CONCEPTUAL_KEYWORDS):
            return QueryType.CONCEPTUAL
        
        # Default to factual for who/what/when/where or unknown
        return QueryType.FACTUAL


class QueryExpander:
    """
    Expand queries with related terms and reformulations.
    
    This implementation uses pattern-based expansion. For production,
    consider integrating a language model or WordNet for richer expansions.
    """
    
    # Domain-specific synonym mapping for Islamic heritage
    DOMAIN_SYNONYMS = {
        'mosque': ['masjid', 'islamic temple', 'prayer hall'],
        'quran': ['koran', 'holy book', 'islamic scripture'],
        'prophet': ['messenger', 'rasul', 'nabi'],
        'caliph': ['khalifa', 'islamic leader', 'successor'],
        'architecture': ['building', 'structure', 'construction', 'design'],
        'art': ['artwork', 'artistic', 'craftsmanship'],
        'dynasty': ['empire', 'kingdom', 'period', 'era'],
        'civilization': ['culture', 'society', 'people'],
    }
    
    @classmethod
    def expand(cls, query: str, query_type: QueryType, max_expansions: int = 2) -> list[str]:
        """
        Generate query expansions for improved retrieval diversity.
        
        Args:
            query: Cleaned query string
            query_type: Classification of the query
            max_expansions: Maximum number of expanded queries to generate
            
        Returns:
            List of expanded query strings (may be empty)
        """
        expansions = []
        query_lower = query.lower()
        
        # Strategy 1: Add domain-specific synonyms
        for term, synonyms in cls.DOMAIN_SYNONYMS.items():
            if term in query_lower:
                for synonym in synonyms[:max_expansions]:
                    expanded = query_lower.replace(term, synonym)
                    if expanded != query_lower:
                        expansions.append(expanded.capitalize())
                break  # Only expand first matching term to avoid explosion
        
        # Strategy 2: Query type-specific reformulations
        if query_type == QueryType.DEFINITION and len(expansions) < max_expansions:
            # "What is X?" → "Definition of X", "X explanation"
            match = re.search(r'what (?:is|are) (.*)\??', query_lower)
            if match:
                entity = match.group(1).strip()
                expansions.append(f"Definition of {entity}")
                if len(expansions) < max_expansions:
                    expansions.append(f"{entity.capitalize()} explanation")
        
        elif query_type == QueryType.TEMPORAL and len(expansions) < max_expansions:
            # Add "history" if not present
            if 'history' not in query_lower:
                expansions.append(f"History of {query}")
        
        elif query_type == QueryType.CONCEPTUAL and len(expansions) < max_expansions:
            # "Why/How..." → "Reason for...", "Explanation of..."
            for keyword in ['why', 'how']:
                if query_lower.startswith(keyword):
                    rest = query[len(keyword):].strip()
                    if keyword == 'why':
                        expansions.append(f"Reason for {rest}")
                    else:  # how
                        expansions.append(f"Process of {rest}")
                    break
        
        # Limit to max_expansions
        return expansions[:max_expansions]


class KeyEntityExtractor:
    """Extract key entities and terms from queries."""
    
    # Common stopwords (more comprehensive than BM25 tokenizer)
    STOPWORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'been', 'but', 'by',
        'for', 'from', 'has', 'have', 'he', 'her', 'him', 'his', 'how',
        'i', 'in', 'is', 'it', 'its', 'me', 'my', 'of', 'on', 'or', 'our',
        'she', 'so', 'than', 'that', 'the', 'their', 'them', 'they', 'this',
        'to', 'up', 'was', 'we', 'were', 'what', 'when', 'which', 'who',
        'will', 'with', 'you', 'your', 'about', 'can', 'could', 'did', 'do',
        'does', 'during', 'each', 'had', 'having', 'into', 'more', 'most',
        'other', 'should', 'such', 'would',
    }
    
    @classmethod
    def extract(cls, query: str) -> list[str]:
        """
        Extract meaningful entities from the query.
        
        Identifies capitalized terms, quoted phrases, and significant words.
        
        Args:
            query: Cleaned query string
            
        Returns:
            List of key entities
        """
        entities = []
        
        # Strategy 1: Extract quoted phrases
        quoted = re.findall(r'"([^"]+)"', query)
        entities.extend(quoted)
        
        # Strategy 2: Extract capitalized terms (proper nouns)
        # Match words starting with capital letter (but not at sentence start)
        words = query.split()
        for i, word in enumerate(words):
            # Skip first word unless it's part of a multi-word capitalized phrase
            if i > 0 and word[0].isupper() and len(word) > 1:
                entities.append(word)
        
        # Strategy 3: Extract significant words (long, not stopwords)
        query_lower = query.lower()
        for word in re.findall(r'\b\w+\b', query_lower):
            if (len(word) > 4 and 
                word not in cls.STOPWORDS and 
                not word.isdigit()):
                entities.append(word)
        
        # Deduplicate while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            entity_clean = entity.strip('.,!?;:').lower()
            if entity_clean and entity_clean not in seen:
                seen.add(entity_clean)
                unique_entities.append(entity)
        
        return unique_entities[:10]  # Limit to top 10


class QueryProcessor:
    """
    Main query processing pipeline.
    
    Orchestrates cleaning, classification, expansion, and entity extraction.
    """
    
    def __init__(self) -> None:
        self.cleaner = QueryCleaner()
        self.classifier = QueryClassifier()
        self.expander = QueryExpander()
        self.entity_extractor = KeyEntityExtractor()
    
    def process(self, query: str, enable_expansion: bool = True) -> ProcessedQuery:
        """
        Full query processing pipeline.
        
        Args:
            query: Raw user query
            enable_expansion: Whether to generate query expansions
            
        Returns:
            ProcessedQuery with all enhancements
        """
        if not query or not query.strip():
            return ProcessedQuery(
                original=query,
                cleaned="",
                expanded=[],
                query_type=QueryType.FACTUAL,
                key_entities=[],
                is_complex=False,
            )
        
        # Step 1: Clean
        cleaned = self.cleaner.clean(query)
        if not cleaned:
            cleaned = query.strip()
        
        # Step 2: Classify
        query_type = self.classifier.classify(cleaned)
        
        # Step 3: Extract key entities
        entities = self.entity_extractor.extract(cleaned)
        
        # Step 4: Expand (if enabled)
        expanded = []
        if enable_expansion:
            expanded = self.expander.expand(cleaned, query_type)
        
        # Step 5: Assess complexity
        # Complex queries have multiple clauses or many entities
        is_complex = (
            len(entities) > 3 or
            len(cleaned.split()) > 12 or
            query_type in (QueryType.COMPARATIVE, QueryType.CONCEPTUAL)
        )
        
        logger.debug(
            "Query processed: type=%s, entities=%d, complex=%s, expansions=%d",
            query_type.value, len(entities), is_complex, len(expanded)
        )
        
        return ProcessedQuery(
            original=query,
            cleaned=cleaned,
            expanded=expanded,
            query_type=query_type,
            key_entities=entities,
            is_complex=is_complex,
        )


# Convenience singleton
_processor: QueryProcessor | None = None


def get_query_processor() -> QueryProcessor:
    """Get or create the global query processor instance."""
    global _processor
    if _processor is None:
        _processor = QueryProcessor()
    return _processor


def process_query(query: str, enable_expansion: bool = True) -> ProcessedQuery:
    """Convenience function for query processing."""
    return get_query_processor().process(query, enable_expansion)
