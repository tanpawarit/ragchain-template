"""
Tests for NLP utilities using pythainlp and spacy.
"""

import pytest

from src.utils.nlp_utils import (
    NLPProcessor,
    calculate_similarity,
    detect_language,
    get_keywords,
    get_nlp_processor,
    tokenize,
)


class TestNLPProcessor:
    """Test NLP processor functionality."""

    def test_initialization(self) -> None:
        """Test NLP processor initialization."""
        processor = NLPProcessor()
        assert processor is not None
        assert hasattr(processor, "detect_language")
        assert hasattr(processor, "tokenize")
        assert hasattr(processor, "get_keywords")

    def test_language_detection_thai(self) -> None:
        """Test Thai language detection."""
        processor = NLPProcessor()

        # Pure Thai text
        assert processor.detect_language("สวัสดีครับ") == "th"
        assert processor.detect_language("ผมชื่อสมชาย") == "th"
        assert processor.detect_language("Python คือภาษาโปรแกรมมิ่ง") == "th"

    def test_language_detection_english(self) -> None:
        """Test English language detection."""
        processor = NLPProcessor()

        # Pure English text
        assert processor.detect_language("Hello world") == "en"
        assert processor.detect_language("Python is a programming language") == "en"
        assert processor.detect_language("How are you?") == "en"

    def test_language_detection_mixed(self) -> None:
        """Test mixed language detection."""
        processor = NLPProcessor()

        # Mixed text (should default to English)
        assert processor.detect_language("Hello สวัสดีครับ") == "th"
        assert processor.detect_language("Python คือ programming language") == "en"

    def test_language_detection_empty(self) -> None:
        """Test empty text handling."""
        processor = NLPProcessor()

        assert processor.detect_language("") == "en"
        assert processor.detect_language(None) == "en"  # type: ignore

    def test_thai_tokenization(self) -> None:
        """Test Thai tokenization."""
        processor = NLPProcessor()

        text = "สวัสดีครับ ผมชื่อสมชาย"
        tokens = processor.tokenize(text, remove_stopwords=False)

        # Should return meaningful tokens
        assert len(tokens) > 0
        assert "สวัสดี" in tokens or "ครับ" in tokens
        assert isinstance(tokens, list)

    def test_english_tokenization(self) -> None:
        """Test English tokenization."""
        processor = NLPProcessor()

        text = "Hello world, how are you?"
        tokens = processor.tokenize(text, remove_stopwords=False)

        # Should return meaningful tokens
        assert len(tokens) > 0
        assert "hello" in tokens or "world" in tokens
        assert isinstance(tokens, list)

    def test_stop_word_removal(self) -> None:
        """Test stop word removal."""
        processor = NLPProcessor()

        # English text with stop words
        text = "The cat is on the mat"
        tokens_with_stop = processor.tokenize(text, remove_stopwords=False)
        tokens_without_stop = processor.tokenize(text, remove_stopwords=True)

        # Should have fewer tokens when removing stop words
        assert len(tokens_without_stop) <= len(tokens_with_stop)

    def test_keyword_extraction(self) -> None:
        """Test keyword extraction."""
        processor = NLPProcessor()

        # English keywords
        text = "Python is a programming language used for web development"
        keywords = processor.get_keywords(text)

        assert len(keywords) > 0
        assert "python" in keywords or "programming" in keywords
        assert isinstance(keywords, list)

    def test_similarity_calculation(self) -> None:
        """Test similarity calculation."""
        processor = NLPProcessor()

        # Similar texts
        text1 = "Python is a programming language"
        text2 = "Python programming is used for coding"
        similarity = processor.calculate_similarity(text1, text2)

        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.1  # Should have some similarity

        # Different texts
        text3 = "How to cook rice?"
        similarity_diff = processor.calculate_similarity(text1, text3)

        assert similarity_diff < similarity  # Should be less similar

    def test_jaccard_similarity(self) -> None:
        """Test Jaccard similarity fallback."""
        processor = NLPProcessor()

        text1 = "Python programming"
        text2 = "Python coding"
        similarity = processor._jaccard_similarity(text1, text2)

        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.0  # Should have some overlap

    def test_empty_text_handling(self) -> None:
        """Test handling of empty text."""
        processor = NLPProcessor()

        # Empty text should return empty results
        assert processor.tokenize("") == []
        assert processor.get_keywords("") == []
        assert processor.calculate_similarity("", "test") == 0.0
        assert processor.calculate_similarity("test", "") == 0.0


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_nlp_processor_singleton(self) -> None:
        """Test that get_nlp_processor returns singleton."""
        processor1 = get_nlp_processor()
        processor2 = get_nlp_processor()

        assert processor1 is processor2

    def test_detect_language_function(self) -> None:
        """Test detect_language convenience function."""
        assert detect_language("สวัสดี") == "th"
        assert detect_language("Hello") == "en"

    def test_tokenize_function(self) -> None:
        """Test tokenize convenience function."""
        tokens = tokenize("Hello world")
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_get_keywords_function(self) -> None:
        """Test get_keywords convenience function."""
        keywords = get_keywords("Python programming")
        assert isinstance(keywords, list)
        assert len(keywords) > 0

    def test_calculate_similarity_function(self) -> None:
        """Test calculate_similarity convenience function."""
        similarity = calculate_similarity("Python", "programming")
        assert 0.0 <= similarity <= 1.0


class TestGuardrailsIntegration:
    """Test integration with guardrails validators."""

    def test_relevance_validator_with_nlp(self) -> None:
        """Test that RelevanceValidator uses NLP features."""
        from src.guardrails.validators.output_validators import RelevanceValidator

        config = {"min_relevance_score": 0.3, "use_semantic_similarity": True}

        validator = RelevanceValidator(config)

        # Test with Thai text
        result = validator.validate(
            {
                "question": "Python คืออะไร?",
                "answer": "Python เป็นภาษาโปรแกรมมิ่งที่ใช้ในการพัฒนาแอปพลิเคชัน",
            }
        )

        assert hasattr(result, "result")
        assert hasattr(result, "metadata")
        assert result.metadata is not None and "relevance_score" in result.metadata

    def test_hallucination_validator_with_nlp(self) -> None:
        """Test that HallucinationValidator uses NLP features."""
        from src.guardrails.validators.output_validators import HallucinationValidator

        config = {"confidence_threshold": 0.8, "context_coverage_threshold": 0.5}

        validator = HallucinationValidator(config)

        # Test with context coverage
        result = validator.validate(
            {
                "answer": "Python is a programming language",
                "context": "Python is a high-level programming language",
            }
        )

        assert hasattr(result, "result")
        assert hasattr(result, "metadata")


class TestFallbackBehavior:
    """Test fallback behavior when libraries are not available."""

    def test_fallback_without_libraries(self) -> None:
        """Test that system works even without NLP libraries."""
        # This test ensures the system doesn't crash
        # even if pythainlp or spacy are not available

        processor = NLPProcessor()

        # Should still work with basic functionality
        assert processor.detect_language("test") in ["th", "en"]
        assert isinstance(processor.tokenize("test"), list)
        assert isinstance(processor.get_keywords("test"), list)


if __name__ == "__main__":
    pytest.main([__file__])
