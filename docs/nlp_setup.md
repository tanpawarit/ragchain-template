# NLP Setup Guide

This guide explains how to set up and use the advanced NLP features in the guardrails system using `pythainlp` (for Thai) and `spacy` (for English).

## Installation

### 1. Install Dependencies

```bash
uv add pythainlp spacy
```

### 2. Download Spacy Model

```bash
python -m spacy download en_core_web_md
```

### 3. (Optional) Thai Spacy Model

```bash
python -m spacy download th_core_news_sm
```

## Usage

- The system will automatically use pythainlp for Thai and spacy for English.
- For best results, use `en_core_web_md` as the default spacy model (it includes word vectors for better semantic similarity).

### Example

```python
from src.guardrails.nlp_utils import get_nlp_processor, detect_language, tokenize, get_keywords, calculate_similarity

nlp = get_nlp_processor()
print(detect_language("สวัสดีครับ"))  # 'th'
print(tokenize("Hello world"))       # ['hello', 'world']
print(get_keywords("Python programming"))
print(calculate_similarity("What is Python?", "Python is a programming language"))
```

## Troubleshooting

- **Spacy model not found**: Run `python -m spacy download en_core_web_md`
- **Pythainlp not installed**: Run `uv add pythainlp`
- **Thai tokenization issues**: Use pythainlp for best results

## Guardrails Integration

- The validators use these NLP features automatically. No extra configuration is needed for most use cases.

---
For more details, see the code comments or `README.md`. 