from dataclasses import dataclass, field
from typing import List, Optional

"""
Configuration settings for evaluation modules.

This module contains default configuration settings for evaluation runs.
"""


@dataclass
class RetrieverEvaluationConfig:
    """Configuration for retriever evaluation."""

    # Retrieval parameters
    k_values: List[int] = field(default_factory=lambda: [1, 3, 5, 10])
    similarity_threshold: float = 0.7

    # Embedding model
    embedding_model: str = "text-embedding-3-small"

    # Evaluation model
    evaluation_model: str = "gpt-4o"

    # Processing parameters
    batch_size: int = 10
    max_contexts: Optional[int] = None

    # Output settings
    output_dir: str = "evaluation/results/retriever"
    save_format: str = "json"


@dataclass
class GeneratorEvaluationConfig:
    """Configuration for generator evaluation."""

    # Evaluation model
    evaluation_model: str = "gpt-4o"

    # Processing parameters
    batch_size: int = 10

    # Evaluation metrics
    metrics: List[str] = field(
        default_factory=lambda: [
            "relevance",
            "coherence",
            "factual_accuracy",
            "overall_quality",
        ]
    )

    # Output settings
    output_dir: str = "evaluation/results/generator"
    save_format: str = "json"


@dataclass
class E2EEvaluationConfig:
    """Configuration for end-to-end evaluation."""

    # Evaluation model
    evaluation_model: str = "gpt-4o"

    # Processing parameters
    batch_size: int = 5

    # Evaluation metrics
    metrics: List[str] = field(
        default_factory=lambda: [
            "answer_relevance",
            "context_relevance",
            "factual_accuracy",
            "hallucination",
            "overall_quality",
        ]
    )

    # Output settings
    output_dir: str = "evaluation/results/e2e"
    save_format: str = "json"


@dataclass
class EvaluationConfig:
    """Main configuration for all evaluation types."""

    # OpenAI API settings
    openai_api_key: Optional[str] = None

    # MLflow settings
    mlflow_tracking_uri: Optional[str] = None
    experiment_name: str = "typhoon_evaluation"

    # Component configurations
    retriever: RetrieverEvaluationConfig = field(
        default_factory=RetrieverEvaluationConfig
    )
    generator: GeneratorEvaluationConfig = field(
        default_factory=GeneratorEvaluationConfig
    )
    e2e: E2EEvaluationConfig = field(default_factory=E2EEvaluationConfig)

    # Test data paths
    retriever_test_data: str = "evaluation/test_data/retriever_test_data.json"
    generator_test_data: str = "evaluation/test_data/generator_test_data.json"
    e2e_test_data: str = "evaluation/test_data/e2e_test_data.json"

    # Cost tracking
    track_costs: bool = True


def load_config(config_path: Optional[str] = None) -> EvaluationConfig:
    """
    Load evaluation configuration from a file or use defaults.

    Parameters:
    -----------
    config_path: Optional[str]
        Path to configuration file (YAML or JSON)

    Returns:
    --------
    EvaluationConfig
        Loaded configuration
    """
    import os

    # Start with default configuration
    config = EvaluationConfig()

    # Load from file if provided
    if config_path and os.path.exists(config_path):
        import json

        import yaml

        file_ext = os.path.splitext(config_path)[1].lower()

        try:
            with open(config_path, "r") as f:
                if file_ext == ".yaml" or file_ext == ".yml":
                    loaded_config = yaml.safe_load(f)
                elif file_ext == ".json":
                    loaded_config = json.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {file_ext}")

            # Update configuration with loaded values
            # This is a simplified approach; in practice, you'd want to recursively update nested dataclasses
            for key, value in loaded_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        except Exception as e:
            print(f"Error loading configuration from {config_path}: {e}")
            print("Using default configuration")

    # Check for environment variables
    if not config.openai_api_key:
        config.openai_api_key = os.environ.get("OPENAI_API_KEY")

    return config
