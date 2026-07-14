"""Multi-provider LLM client with Groq → Ollama → HuggingFace fallback chain.

Enhanced with:
- Improved system prompts with query-type awareness
- Answer quality validation and post-processing
- Citation extraction and verification
- Hallucination detection
"""

from __future__ import annotations

import logging
import os
import re
from abc import ABC, abstractmethod
from typing import AsyncIterator, Iterator

import httpx

from athar.config import settings

logger = logging.getLogger(__name__)


class AnswerPostProcessor:
    """
    Post-process LLM answers for quality and consistency.
    
    Features:
    - Citation validation
    - Hallucination detection
    - Answer quality checks
    - Formatting improvements
    """
    
    @staticmethod
    def validate_citations(answer: str, num_sources: int) -> tuple[str, list[str]]:
        """
        Validate and extract citations from the answer.
        
        Args:
            answer: Generated answer
            num_sources: Number of available sources
            
        Returns:
            Tuple of (cleaned_answer, list of warnings)
        """
        warnings = []
        
        # Find all citation patterns [1], [2], etc.
        citations = set(re.findall(r'\[(\d+)\]', answer))
        
        # Check for invalid citations
        for citation in citations:
            cite_num = int(citation)
            if cite_num > num_sources or cite_num < 1:
                warnings.append(f"Invalid citation [{citation}] (only {num_sources} sources available)")
                # Remove invalid citations
                answer = answer.replace(f"[{citation}]", "")
        
        # Check if factual claims lack citations
        # Simple heuristic: sentences with dates, names, or specific numbers
        sentences = re.split(r'[.!?]+', answer)
        uncited_facts = []
        
        for sentence in sentences:
            # Skip very short sentences
            if len(sentence.strip()) < 20:
                continue
            
            # Check for potential facts (dates, numbers, proper nouns)
            has_date = bool(re.search(r'\b\d{3,4}\b|\bcentury\b|\byear\b', sentence))
            has_number = bool(re.search(r'\b\d+\b', sentence))
            has_proper_noun = bool(re.search(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sentence))
            
            # Check if sentence has citations
            has_citation = bool(re.search(r'\[\d+\]', sentence))
            
            if (has_date or (has_number and has_proper_noun)) and not has_citation:
                uncited_facts.append(sentence.strip()[:60] + "...")
        
        if uncited_facts and len(uncited_facts) <= 2:
            warnings.append(f"Potential uncited facts: {'; '.join(uncited_facts)}")
        
        return answer.strip(), warnings
    
    @staticmethod
    def detect_hallucination_markers(answer: str, context: str) -> list[str]:
        """
        Detect potential hallucinations by checking for phrases not in context.
        
        This is a simple heuristic-based approach. More sophisticated methods
        would use NLI models.
        
        Args:
            answer: Generated answer
            context: Source context
            
        Returns:
            List of potential hallucination warnings
        """
        warnings = []
        
        # Common hallucination markers
        uncertain_phrases = [
            "according to my knowledge",
            "as far as i know",
            "i believe",
            "i think",
            "probably",
            "it is likely",
            "it seems",
        ]
        
        answer_lower = answer.lower()
        for phrase in uncertain_phrases:
            if phrase in answer_lower:
                warnings.append(f"Uncertain language detected: '{phrase}'")
        
        # Check for Wikipedia-like phrasing (model might be using memorized knowledge)
        wiki_markers = [
            "according to wikipedia",
            "as wikipedia states",
            "citation needed",
        ]
        
        for marker in wiki_markers:
            if marker in answer_lower:
                warnings.append(f"Possible external knowledge used: '{marker}'")
        
        return warnings
    
    @staticmethod
    def improve_formatting(answer: str) -> str:
        """
        Improve answer formatting for better readability.
        
        Args:
            answer: Raw answer
            
        Returns:
            Formatted answer
        """
        # Remove excessive whitespace
        answer = re.sub(r'\n{3,}', '\n\n', answer)
        answer = re.sub(r' {2,}', ' ', answer)
        
        # Ensure proper spacing after citations
        answer = re.sub(r'\[(\d+)\]([a-zA-Z])', r'[\1] \2', answer)
        
        # Remove trailing punctuation duplicates
        answer = re.sub(r'([.!?])\1+', r'\1', answer)
        
        return answer.strip()
    
    @staticmethod
    def check_answer_quality(answer: str, question: str) -> tuple[bool, list[str]]:
        """
        Check if the answer meets basic quality criteria.
        
        Args:
            answer: Generated answer
            question: Original question
            
        Returns:
            Tuple of (is_acceptable, list of issues)
        """
        issues = []
        
        # Check minimum length
        if len(answer) < 20:
            issues.append("Answer too short (< 20 characters)")
        
        # Check if it's just a refusal
        refusal_phrases = [
            "i cannot answer",
            "i don't have information",
            "the context does not provide",
            "there is no information",
        ]
        
        answer_lower = answer.lower()
        is_refusal = any(phrase in answer_lower for phrase in refusal_phrases)
        
        if is_refusal and len(answer) < 100:
            # Very short refusal might indicate a problem
            issues.append("Very brief refusal - context may be insufficient")
        
        # Check for repetition
        words = answer.lower().split()
        if len(words) > 10:
            # Check if same phrase appears 3+ times
            for i in range(len(words) - 3):
                phrase = ' '.join(words[i:i+3])
                if answer_lower.count(phrase) >= 3:
                    issues.append(f"Repetitive content detected: '{phrase}'")
                    break
        
        # Answer should not just repeat the question
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(question_words & answer_words)
        
        if overlap == len(question_words) and len(answer_words) < len(question_words) * 2:
            issues.append("Answer appears to just repeat the question")
        
        is_acceptable = len(issues) == 0
        return is_acceptable, issues
    
    @classmethod
    def process(
        cls,
        answer: str,
        question: str,
        context: str,
        num_sources: int,
    ) -> tuple[str, dict]:
        """
        Full post-processing pipeline.
        
        Args:
            answer: Raw LLM answer
            question: Original question
            context: Source context
            num_sources: Number of sources used
            
        Returns:
            Tuple of (processed_answer, metadata_dict)
        """
        # Step 1: Format improvements
        answer = cls.improve_formatting(answer)
        
        # Step 2: Validate citations
        answer, citation_warnings = cls.validate_citations(answer, num_sources)
        
        # Step 3: Check quality
        is_acceptable, quality_issues = cls.check_answer_quality(answer, question)
        
        # Step 4: Detect hallucinations
        hallucination_warnings = cls.detect_hallucination_markers(answer, context)
        
        # Compile metadata
        metadata = {
            "is_acceptable": is_acceptable,
            "citation_warnings": citation_warnings,
            "quality_issues": quality_issues,
            "hallucination_warnings": hallucination_warnings,
            "has_warnings": bool(citation_warnings or quality_issues or hallucination_warnings),
        }
        
        # Log warnings if any
        if metadata["has_warnings"]:
            logger.warning(
                "Answer quality concerns for query '%s': citations=%d, quality=%d, hallucination=%d",
                question[:50],
                len(citation_warnings),
                len(quality_issues),
                len(hallucination_warnings),
            )
        
        return answer, metadata


# Enhanced system prompt with better instructions
SYSTEM_PROMPT = """You are Athar, a knowledgeable and careful research assistant specializing in cultural heritage and history.

Core Principles:
1. **Accuracy First**: Answer ONLY from the supplied context. Never introduce external knowledge or speculation.
2. **Cite Sources**: Support factual claims with source citations using square brackets [1], [2], etc.
3. **Acknowledge Gaps**: If the context lacks necessary information, explicitly state what is missing rather than guessing.
4. **Distinguish Certainty**: Separate established facts from uncertainty or disagreement among sources.
5. **Clarity**: Write in clear, accessible language appropriate for a general audience interested in history and culture.

Response Guidelines:
- Be concise but complete. Aim for 2-4 paragraphs unless the query requires more detail.
- Use multiple sources when available to provide a fuller picture.
- When sources disagree, present both perspectives with citations.
- For dates and names, be precise and cite the source.
- If a fact is uncertain or disputed in the sources, say so clearly.

Context:
{context}"""

# Query-type specific prompts for better responses
QUERY_TYPE_INSTRUCTIONS = {
    "factual": "Provide precise, fact-based answers with specific details (dates, names, places). Focus on accuracy.",
    "conceptual": "Explain the underlying concepts and reasons. Connect ideas and provide deeper understanding.",
    "temporal": "Focus on chronology and temporal relationships. Be precise with dates and time periods.",
    "comparative": "Highlight similarities and differences. Organize the comparison clearly.",
    "definition": "Provide a clear, comprehensive definition. Include examples if available in the context.",
    "listing": "Organize information as a structured list. Be complete but concise.",
}

QUERY_TEMPLATE = "{question}"


class BaseLLM(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    def generate(
        self, 
        question: str, 
        context: str,
        query_type: str | None = None,
    ) -> str:
        """Generate a complete answer."""

    @abstractmethod
    def stream(
        self, 
        question: str, 
        context: str,
        query_type: str | None = None,
    ) -> Iterator[str]:
        """Stream answer tokens."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider name (groq, ollama, huggingface)."""
    
    def _build_system_prompt(self, context: str, query_type: str | None = None) -> str:
        """
        Build system prompt with optional query-type specific instructions.
        
        Args:
            context: Retrieved context
            query_type: Optional query type for tailored instructions
            
        Returns:
            Complete system prompt
        """
        base_prompt = SYSTEM_PROMPT.format(context=context)
        
        if query_type and query_type in QUERY_TYPE_INSTRUCTIONS:
            instruction = QUERY_TYPE_INSTRUCTIONS[query_type]
            base_prompt += f"\n\nQuery Type Guidance: {instruction}"
        
        return base_prompt


# ── Groq Provider ─────────────────────────────────────────────────────────────


class GroqLLM(BaseLLM):
    """Groq API client using the OpenAI-compatible endpoint."""

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self) -> None:
        self._api_key = settings.groq_api_key
        if not self._api_key:
            raise ValueError("GROQ_API_KEY not set.")

    def _build_messages(
        self, 
        question: str, 
        context: str,
        query_type: str | None = None,
    ) -> list[dict]:
        return [
            {
                "role": "system",
                "content": self._build_system_prompt(context, query_type),
            },
            {
                "role": "user",
                "content": QUERY_TEMPLATE.format(question=question),
            },
        ]

    def generate(
        self, 
        question: str, 
        context: str,
        query_type: str | None = None,
    ) -> str:
        with httpx.Client(timeout=settings.llm_timeout) as client:
            resp = client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": self._build_messages(question, context, query_type),
                    "temperature": settings.llm_temperature,
                    "max_tokens": settings.llm_max_tokens,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()

    def stream(
        self, 
        question: str, 
        context: str,
        query_type: str | None = None,
    ) -> Iterator[str]:
        with httpx.Client(timeout=settings.llm_timeout) as client:
            with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": self._build_messages(question, context, query_type),
                    "temperature": settings.llm_temperature,
                    "max_tokens": settings.llm_max_tokens,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        import json
                        data = json.loads(line[6:])
                        delta = data["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta

    @property
    def model_name(self) -> str:
        return settings.groq_model

    @property
    def provider_name(self) -> str:
        return "groq"


# ── Ollama Provider ───────────────────────────────────────────────────────────


class OllamaLLM(BaseLLM):
    """Ollama local LLM client. Requires Ollama running at the configured URL."""

    def __init__(self) -> None:
        self._base_url = settings.ollama_base_url
        self._model = settings.ollama_model

    def _check_available(self) -> bool:
        try:
            with httpx.Client(timeout=3) as client:
                resp = client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def generate(
        self, 
        question: str, 
        context: str,
        query_type: str | None = None,
    ) -> str:
        prompt = (
            self._build_system_prompt(context, query_type)
            + "\n\n"
            + QUERY_TEMPLATE.format(question=question)
        )
        with httpx.Client(timeout=settings.llm_timeout) as client:
            resp = client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": settings.llm_temperature,
                        "num_predict": settings.llm_max_tokens,
                    },
                },
            )
            resp.raise_for_status()
            return resp.json()["response"].strip()

    def stream(
        self, 
        question: str, 
        context: str,
        query_type: str | None = None,
    ) -> Iterator[str]:
        import json
        prompt = (
            self._build_system_prompt(context, query_type)
            + "\n\n"
            + QUERY_TEMPLATE.format(question=question)
        )
        with httpx.Client(timeout=settings.llm_timeout) as client:
            with client.stream(
                "POST",
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {"temperature": settings.llm_temperature},
                },
            ) as response:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token
                        if data.get("done"):
                            break

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "ollama"


# ── HuggingFace Provider ──────────────────────────────────────────────────────


class HuggingFaceLLM(BaseLLM):
    """Local HuggingFace model — offline fallback using FLAN-T5."""

    def __init__(self) -> None:
        from transformers import pipeline

        logger.info("Loading HuggingFace model: %s", settings.hf_model)
        self._pipe = pipeline(
            "text2text-generation",
            model=settings.hf_model,
            device=settings.hf_device,
            max_new_tokens=512,
        )
        logger.info("HuggingFace model loaded.")

    def _build_prompt(self, question: str, context: str, query_type: str | None = None) -> str:
        # FLAN-T5 responds well to direct task description
        ctx_short = context[:2000]  # Limit context for small model
        base_prompt = (
            "Answer only from the context. Cite factual claims as [1], [2], etc. "
            "If the context is insufficient, say so.\n\n"
            f"Context:\n{ctx_short}\n\nQuestion: {question}\n\nAnswer:"
        )
        
        if query_type and query_type in QUERY_TYPE_INSTRUCTIONS:
            instruction = QUERY_TYPE_INSTRUCTIONS[query_type]
            base_prompt = f"{instruction}\n\n{base_prompt}"
        
        return base_prompt

    def generate(
        self, 
        question: str, 
        context: str,
        query_type: str | None = None,
    ) -> str:
        prompt = self._build_prompt(question, context, query_type)
        result = self._pipe(prompt, max_new_tokens=512, do_sample=False)
        return result[0]["generated_text"].strip()

    def stream(
        self, 
        question: str, 
        context: str,
        query_type: str | None = None,
    ) -> Iterator[str]:
        # HuggingFace doesn't have native streaming for text2text
        # Simulate by yielding the full response word by word
        answer = self.generate(question, context, query_type)
        for word in answer.split(" "):
            yield word + " "

    @property
    def model_name(self) -> str:
        return settings.hf_model

    @property
    def provider_name(self) -> str:
        return "huggingface"


# ── Factory ───────────────────────────────────────────────────────────────────


def create_llm() -> BaseLLM:
    """Instantiate the best available LLM. Tries Groq → Ollama → HuggingFace."""
    provider = settings.llm_provider

    if provider == "groq" or (provider == "auto" and settings.groq_api_key):
        try:
            llm = GroqLLM()
            logger.info("Using Groq (%s)", settings.groq_model)
            return llm
        except Exception as e:
            logger.warning("Groq unavailable: %s", e)
            if provider == "groq":
                raise

    if provider == "ollama" or provider == "auto":
        try:
            llm = OllamaLLM()
            if llm._check_available():
                logger.info("Using Ollama (%s)", settings.ollama_model)
                return llm
            logger.warning("Ollama not reachable at %s", settings.ollama_base_url)
        except Exception as e:
            logger.warning("Ollama unavailable: %s", e)
            if provider == "ollama":
                raise

    logger.info("Using HuggingFace fallback (%s)", settings.hf_model)
    return HuggingFaceLLM()
