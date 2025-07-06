"""
Text analyzer tools using langchain_core.tools decorator.

Simple text processing operations that can be used by LangChain agents.
"""

import re
from typing import Any, Dict

from langchain_core.tools import tool


@tool
def count_words(text: str) -> Dict[str, Any]:
    """Count words and characters in text.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with word count, character count, and other statistics
    """
    if not text:
        return {
            "word_count": 0,
            "character_count": 0,
            "character_count_no_spaces": 0,
            "sentence_count": 0,
            "average_word_length": 0,
        }

    # Count words
    words = text.split()
    word_count = len(words)

    # Count characters
    character_count = len(text)
    character_count_no_spaces = len(text.replace(" ", ""))

    # Count sentences (simple approach)
    sentence_count = len(re.findall(r"[.!?]+", text))

    # Calculate average word length
    average_word_length = (
        round(sum(len(word.strip(".,!?;:")) for word in words) / word_count, 2)
        if word_count > 0
        else 0
    )

    return {
        "word_count": word_count,
        "character_count": character_count,
        "character_count_no_spaces": character_count_no_spaces,
        "sentence_count": sentence_count,
        "average_word_length": average_word_length,
    }


@tool
def analyze_text(text: str) -> Dict[str, Any]:
    """Analyze text and provide comprehensive statistics.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with comprehensive text analysis
    """
    if not text:
        return {
            "basic_stats": {},
            "language_detected": "unknown",
            "contains_thai": False,
            "contains_english": False,
            "most_common_words": [],
            "readability_score": "unknown",
        }

    # Get basic statistics
    basic_stats = count_words.invoke({"text": text})

    # Language detection (simple approach)
    thai_chars = re.findall(r"[\u0E00-\u0E7F]", text)
    english_chars = re.findall(r"[a-zA-Z]", text)

    contains_thai = len(thai_chars) > 0
    contains_english = len(english_chars) > 0

    if contains_thai and contains_english:
        language_detected = "mixed"
    elif contains_thai:
        language_detected = "thai"
    elif contains_english:
        language_detected = "english"
    else:
        language_detected = "unknown"

    # Find most common words (simple approach)
    words = text.lower().split()
    # Remove punctuation
    clean_words = [re.sub(r"[^\w]", "", word) for word in words if word]
    word_freq = {}
    for word in clean_words:
        if len(word) > 2:  # Only count words longer than 2 characters
            word_freq[word] = word_freq.get(word, 0) + 1

    # Get top 5 most common words
    most_common_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]

    # Simple readability score (based on average word length and sentence length)
    avg_word_length = basic_stats.get("average_word_length", 0)
    sentence_count = basic_stats.get("sentence_count", 1)
    word_count = basic_stats.get("word_count", 0)
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

    if avg_word_length < 4 and avg_sentence_length < 15:
        readability_score = "easy"
    elif avg_word_length < 6 and avg_sentence_length < 20:
        readability_score = "medium"
    else:
        readability_score = "difficult"

    return {
        "basic_stats": basic_stats,
        "language_detected": language_detected,
        "contains_thai": contains_thai,
        "contains_english": contains_english,
        "most_common_words": most_common_words,
        "readability_score": readability_score,
        "average_sentence_length": round(avg_sentence_length, 2),
    }
