"""
Example usage of NLP features with guardrails.

This example demonstrates how to use pythainlp and spacy for better
text processing in the guardrails system.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import Any, Dict

from src.guardrails.validators.output_validators import (
    HallucinationValidator,
    OutputLengthValidator,
    RelevanceValidator,
)
from src.utils.nlp_utils import (
    calculate_similarity,
    detect_language,
    get_keywords,
    get_nlp_processor,
    tokenize,
)


def demonstrate_nlp_features() -> None:
    """Demonstrate basic NLP features."""
    print("=== NLP Features Demonstration ===\n")

    # Initialize NLP processor
    nlp = get_nlp_processor()

    # Test language detection
    print("1. Language Detection:")
    thai_text = "สวัสดีครับ ผมชื่อสมชาย"
    english_text = "Hello, my name is John"
    mixed_text = "Hello สวัสดีครับ"

    print(f"   Thai text: '{thai_text}' -> {detect_language(thai_text)}")
    print(f"   English text: '{english_text}' -> {detect_language(english_text)}")
    print(f"   Mixed text: '{mixed_text}' -> {detect_language(mixed_text)}")
    print()

    # Test tokenization
    print("2. Tokenization:")
    print(f"   Thai: {tokenize(thai_text, remove_stopwords=False)}")
    print(f"   English: {tokenize(english_text, remove_stopwords=False)}")
    print()

    # Test keyword extraction
    print("3. Keyword Extraction:")
    thai_keywords = get_keywords("สวัสดีครับ ผมชื่อสมชาย และผมทำงานเป็นโปรแกรมเมอร์")
    english_keywords = get_keywords("Hello, my name is John and I work as a programmer")

    print(f"   Thai keywords: {thai_keywords}")
    print(f"   English keywords: {english_keywords}")
    print()

    # Test similarity
    print("4. Semantic Similarity:")
    similar_texts = [
        ("Python คืออะไร?", "Python เป็นภาษาโปรแกรมมิ่ง"),
        ("What is Python?", "Python is a programming language"),
        ("Python คืออะไร?", "How to cook rice?"),
    ]

    for text1, text2 in similar_texts:
        similarity = calculate_similarity(text1, text2)
        print(f"   '{text1}' vs '{text2}' -> {similarity:.3f}")
    print()


def demonstrate_guardrails_with_nlp() -> None:
    """Demonstrate guardrails using NLP features."""
    print("=== Guardrails with NLP ===\n")

    # Configure validators with NLP features
    relevance_config: Dict[str, Any] = {
        "min_relevance_score": 0.3,
        "use_semantic_similarity": True,
        "irrelevant_phrases": ["ไม่ทราบ", "ไม่แน่ใจ", "i don't know", "i'm not sure"],
    }

    hallucination_config: Dict[str, Any] = {
        "confidence_threshold": 0.8,
        "context_coverage_threshold": 0.5,
        "uncertainty_phrases": ["ตามที่ฉันรู้", "น่าจะ", "อาจจะ", "probably", "likely"],
        "fabrication_indicators": ["ดังที่กล่าวไว้", "ตามที่พูดไว้", "as mentioned earlier"],
    }

    length_config: Dict[str, Any] = {"min_length": 10, "max_length": 1000}

    # Initialize validators
    relevance_validator = RelevanceValidator(relevance_config)
    hallucination_validator = HallucinationValidator(hallucination_config)
    length_validator = OutputLengthValidator(length_config)

    # Test cases
    test_cases = [
        {
            "name": "Good Thai Response",
            "question": "Python คืออะไร?",
            "answer": "Python เป็นภาษาโปรแกรมมิ่งที่ใช้ในการพัฒนาแอปพลิเคชัน มีความยืดหยุ่นและใช้งานง่าย เหมาะสำหรับผู้เริ่มต้น",
            "context": "Python is a high-level programming language known for its simplicity and readability.",
        },
        {
            "name": "Good English Response",
            "question": "What is machine learning?",
            "answer": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions without explicit programming.",
            "context": "Machine learning algorithms can learn patterns from data to make predictions or decisions.",
        },
        {
            "name": "Irrelevant Response",
            "question": "What is Python?",
            "answer": "I don't know about Python, but I can tell you about cooking rice.",
            "context": "Python is a programming language.",
        },
        {
            "name": "Potential Hallucination",
            "question": "What is the weather like?",
            "answer": "According to my knowledge, the weather is sunny today. As mentioned earlier, it's a beautiful day.",
            "context": "The weather information is not available in the provided context.",
        },
        {
            "name": "Too Short Response",
            "question": "Explain quantum computing",
            "answer": "It's complex.",
            "context": "Quantum computing uses quantum mechanical phenomena.",
        },
    ]

    # Run validations
    for test_case in test_cases:
        print(f"--- {test_case['name']} ---")

        # Length validation
        length_result = length_validator.validate(test_case["answer"])
        print(f"   Length: {length_result.result.value} - {length_result.message}")

        # Relevance validation
        relevance_result = relevance_validator.validate(
            {"question": test_case["question"], "answer": test_case["answer"]}
        )
        print(
            f"   Relevance: {relevance_result.result.value} - {relevance_result.message}"
        )
        if relevance_result.metadata and "relevance_score" in relevance_result.metadata:
            print(
                f"   Relevance Score: {relevance_result.metadata['relevance_score']:.3f}"
            )

        # Hallucination validation
        hallucination_result = hallucination_validator.validate(
            {"answer": test_case["answer"], "context": test_case["context"]}
        )
        print(
            f"   Hallucination: {hallucination_result.result.value} - {hallucination_result.message}"
        )

        print()


def demonstrate_performance_comparison() -> None:
    """Demonstrate performance improvements."""
    print("=== Performance Comparison ===\n")

    # Test text
    thai_text = "สวัสดีครับ ผมชื่อสมชาย และผมทำงานเป็นโปรแกรมเมอร์ที่บริษัทเทคโนโลยีแห่งหนึ่ง ผมชอบการเขียนโค้ดและเรียนรู้เทคโนโลยีใหม่ๆ"
    english_text = "Hello, my name is John and I work as a programmer at a technology company. I enjoy coding and learning new technologies."

    nlp = get_nlp_processor()

    print("1. Thai Text Processing:")
    print(f"   Original text: {thai_text}")
    print(f"   Language detected: {detect_language(thai_text)}")
    print(f"   Tokens (with stop words): {tokenize(thai_text, remove_stopwords=False)}")
    print(f"   Keywords (without stop words): {get_keywords(thai_text)}")
    print()

    print("2. English Text Processing:")
    print(f"   Original text: {english_text}")
    print(f"   Language detected: {detect_language(english_text)}")
    print(
        f"   Tokens (with stop words): {tokenize(english_text, remove_stopwords=False)}"
    )
    print(f"   Keywords (without stop words): {get_keywords(english_text)}")
    print()

    print("3. Similarity Analysis:")
    similar_pairs = [
        ("Python programming", "Coding with Python"),
        ("Machine learning", "AI algorithms"),
        ("Web development", "Cooking recipes"),
    ]

    for text1, text2 in similar_pairs:
        similarity = calculate_similarity(text1, text2)
        print(f"   '{text1}' vs '{text2}' -> {similarity:.3f}")
    print()


def main() -> None:
    """Main demonstration function."""
    print("NLP Features with Guardrails Demonstration")
    print("=" * 50)
    print()

    try:
        # Demonstrate basic NLP features
        demonstrate_nlp_features()

        # Demonstrate guardrails integration
        demonstrate_guardrails_with_nlp()

        # Demonstrate performance comparison
        demonstrate_performance_comparison()

        print("✅ All demonstrations completed successfully!")
        print("\nKey Benefits:")
        print("- Reduced hardcoded stop words")
        print("- Better Thai language support")
        print("- Semantic similarity analysis")
        print("- Language-agnostic processing")
        print("- Production-ready NLP capabilities")

    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        print("\nMake sure you have installed the required dependencies:")
        print("  uv add pythainlp spacy")
        print("  python -m spacy download en_core_web_sm")


if __name__ == "__main__":
    main()
