"""
NLP utilities for guardrails using pythainlp and spacy.

This module provides language-agnostic NLP functions for text processing,
tokenization, and analysis that work well with both Thai and English.
"""

import logging
import re
from typing import List, Optional, Set, Tuple

# Spacy imports
import spacy

# Pythainlp imports
from pythainlp import sent_tokenize, word_tokenize
from pythainlp.corpus.common import thai_stopwords
from pythainlp.util import isthai
from spacy.language import Language

logger = logging.getLogger(__name__)


class NLPProcessor:
    """
    Language-agnostic NLP processor using pythainlp and spacy.

    Provides unified interface for Thai and English text processing.
    """

    def __init__(self, spacy_model: str = "en_core_web_md") -> None:
        """
        Initialize NLP processor.

        Args:
            spacy_model: Spacy model name for English processing
        """
        self.spacy_model = spacy_model
        self._spacy_nlp: Optional[Language] = None
        self._thai_stopwords: Set[str] = set()
        self._english_stopwords: Set[str] = set()

        self._initialize_processors()

    def _initialize_processors(self) -> None:
        """Initialize spacy and pythainlp processors."""
        # Initialize spacy for English
        try:
            self._spacy_nlp = spacy.load(self.spacy_model)
            # Get English stop words from spacy
            self._english_stopwords = set(self._spacy_nlp.Defaults.stop_words)
            logger.info(f"Loaded spacy model: {self.spacy_model}")
        except OSError:
            logger.warning(
                f"Spacy model {self.spacy_model} not found. Install with: python -m spacy download {self.spacy_model}"
            )
            self._spacy_nlp = None

        # Initialize pythainlp for Thai
        try:
            self._thai_stopwords = set(thai_stopwords())
            logger.info("Loaded pythainlp Thai stop words")
        except Exception as e:
            logger.warning(f"Failed to load pythainlp stop words: {e}")

    def detect_language(self, text: str) -> str:
        """
        Detect if text is primarily Thai or English.

        Args:
            text: Input text

        Returns:
            'th' for Thai, 'en' for English
        """
        if not text:
            return "en"

        # Count Thai characters
        thai_chars = sum(1 for char in text if isthai(char))
        total_chars = len([char for char in text if char.isalpha()])

        if total_chars > 0 and thai_chars / total_chars > 0.3:
            return "th"

        return "en"

    def tokenize(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """
        Tokenize text using appropriate method for the language.

        Args:
            text: Input text
            remove_stopwords: Whether to remove stop words

        Returns:
            List of tokens
        """
        if not text:
            return []

        language = self.detect_language(text)

        if language == "th":
            # Use pythainlp for Thai
            tokens = word_tokenize(text, engine="newmm")
            if remove_stopwords:
                tokens = [
                    token for token in tokens if token not in self._thai_stopwords
                ]
        else:
            # Use spacy for English or fallback
            if self._spacy_nlp:
                doc = self._spacy_nlp(text)
                tokens = [token.text.lower() for token in doc if not token.is_space]
                if remove_stopwords:
                    tokens = [
                        token
                        for token in tokens
                        if token not in self._english_stopwords
                    ]
            else:
                # Fallback to simple regex tokenization
                tokens = re.findall(r"\b\w+\b", text.lower())

        return tokens

    def get_keywords(self, text: str, min_length: int = 2) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Input text
            min_length: Minimum token length

        Returns:
            List of keywords
        """
        tokens = self.tokenize(text, remove_stopwords=True)
        return [token for token in tokens if len(token) >= min_length]

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not text1 or not text2:
            return 0.0

        # Use spacy for semantic similarity if available
        if self._spacy_nlp:
            try:
                doc1 = self._spacy_nlp(text1)
                doc2 = self._spacy_nlp(text2)
                return doc1.similarity(doc2)
            except Exception as e:
                logger.warning(f"Spacy similarity failed: {e}")

        # Fallback to keyword-based Jaccard similarity
        return self._jaccard_similarity(text1, text2)

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate Jaccard similarity based on keywords.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Jaccard similarity score
        """
        keywords1 = set(self.get_keywords(text1))
        keywords2 = set(self.get_keywords(text2))

        if not keywords1 and not keywords2:
            return 1.0
        if not keywords1 or not keywords2:
            return 0.0

        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)

        return intersection / union if union > 0 else 0.0

    def extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """
        Extract named entities from text.

        Args:
            text: Input text

        Returns:
            List of (entity_text, entity_type) tuples
        """
        if not self._spacy_nlp:
            return []

        try:
            doc = self._spacy_nlp(text)
            return [(ent.text, ent.label_) for ent in doc.ents]
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            return []

    def get_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        if not text:
            return []

        language = self.detect_language(text)

        if language == "th":
            # Use pythainlp for Thai sentence tokenization
            return sent_tokenize(text, engine="whitespace+newline")
        elif self._spacy_nlp:
            # Use spacy for English
            doc = self._spacy_nlp(text)
            return [sent.text.strip() for sent in doc.sents]
        else:
            # Fallback to simple sentence splitting
            return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


# Global instance for easy access
_nlp_processor: Optional[NLPProcessor] = None


def get_nlp_processor() -> NLPProcessor:
    """
    Get global NLP processor instance.

    Returns:
        NLPProcessor instance
    """
    global _nlp_processor
    if _nlp_processor is None:
        _nlp_processor = NLPProcessor()
    return _nlp_processor


def detect_language(text: str) -> str:
    """Convenience function to detect language."""
    return get_nlp_processor().detect_language(text)


def tokenize(text: str, remove_stopwords: bool = True) -> List[str]:
    """Convenience function to tokenize text."""
    return get_nlp_processor().tokenize(text, remove_stopwords)


def get_keywords(text: str, min_length: int = 2) -> List[str]:
    """Convenience function to extract keywords."""
    return get_nlp_processor().get_keywords(text, min_length)


def calculate_similarity(text1: str, text2: str) -> float:
    """Convenience function to calculate similarity."""
    return get_nlp_processor().calculate_similarity(text1, text2)
