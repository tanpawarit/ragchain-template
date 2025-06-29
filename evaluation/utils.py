import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

"""
Utility functions for evaluation modules.

This module contains common utility functions used across different evaluation modules.
"""


def save_evaluation_results(
    results: Dict[str, Any],
    output_dir: str,
    prefix: str = "evaluation",
    format_type: str = "json",
) -> str:
    """
    Save evaluation results to a file.

    Parameters:
    -----------
    results: Dict[str, Any]
        Evaluation results to save
    output_dir: str
        Directory to save results to
    prefix: str
        Prefix for the output filename
    format_type: str
        Format to save results in ('json' or 'csv')

    Returns:
    --------
    str
        Path to the saved file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format_type.lower() == "json":
        # Save as JSON
        filename = f"{prefix}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

    elif format_type.lower() == "csv":
        # Save as CSV (only per-query results)
        filename = f"{prefix}_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)

        if "per_query" in results:
            # Convert per-query results to DataFrame
            rows = []
            for item in results["per_query"]:
                row = {"question": item.get("question", "")}

                # Add metrics
                if "metrics" in item and isinstance(item["metrics"], dict):
                    for metric_name, metric_value in item["metrics"].items():
                        row[metric_name] = metric_value

                rows.append(row)

            df = pd.DataFrame(rows)
            df.to_csv(filepath, index=False)
        else:
            # Just save the metrics
            pd.DataFrame([results]).to_csv(filepath, index=False)
    else:
        raise ValueError(f"Unsupported format type: {format_type}")

    return filepath


def load_test_data(
    filepath: str, required_fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Load test data from a JSON or CSV file.

    Parameters:
    -----------
    filepath: str
        Path to the test data file
    required_fields: Optional[List[str]]
        List of fields that must be present in each test case

    Returns:
    --------
    List[Dict[str, Any]]
        List of test cases
    """
    file_ext = os.path.splitext(filepath)[1].lower()

    if file_ext == ".json":
        with open(filepath, "r") as f:
            data = json.load(f)

        # Handle both list and dict formats
        if isinstance(data, dict) and "test_cases" in data:
            test_data = data["test_cases"]
        elif isinstance(data, list):
            test_data = data
        else:
            raise ValueError(f"Unsupported JSON format in {filepath}")

    elif file_ext == ".csv":
        test_data = pd.read_csv(filepath).to_dict(orient="records")

    else:
        raise ValueError(f"Unsupported file extension: {file_ext}")

    # Validate required fields if specified
    if required_fields:
        for i, item in enumerate(test_data):
            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields:
                raise ValueError(
                    f"Test case {i} is missing required fields: {missing_fields}"
                )

    return test_data


def calculate_confidence_intervals(
    metrics: List[float], confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence intervals for a list of metric values.

    Parameters:
    -----------
    metrics: List[float]
        List of metric values
    confidence_level: float
        Confidence level (default: 0.95 for 95% confidence)

    Returns:
    --------
    Tuple[float, float]
        Lower and upper bounds of the confidence interval
    """
    import scipy.stats as stats

    if not metrics:
        return (float(0.0), float(0.0))

    mean = np.mean(metrics)
    std_err = stats.sem(metrics)

    if np.isnan(std_err):
        return (float(mean), float(mean))

    # Calculate confidence interval
    h = std_err * stats.t.ppf((1 + confidence_level) / 2, len(metrics) - 1)

    return (mean - h, mean + h)


class CostTracker:
    """
    Utility class to track API usage costs during evaluation.
    """

    # Cost per 1K tokens in USD (approximate as of 2023)
    MODEL_COSTS = {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    }

    def __init__(self):
        self.total_cost: float = 0.0
        self.model_usage: Dict[str, Dict[str, Union[int, float]]] = {}

    def track_completion(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> None:
        """
        Track the cost of an API call.

        Parameters:
        -----------
        model: str
            The model used for the API call
        prompt_tokens: int
            Number of tokens in the prompt
        completion_tokens: int
            Number of tokens in the completion
        """
        # Initialize model usage if not already tracked
        if model not in self.model_usage:
            self.model_usage[model] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cost": 0.0,
            }

        # Update token counts
        self.model_usage[model]["prompt_tokens"] += prompt_tokens
        self.model_usage[model]["completion_tokens"] += completion_tokens

        # Calculate cost
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        # Update costs
        self.model_usage[model]["cost"] += cost
        self.total_cost += cost

    def _calculate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """
        Calculate the cost of an API call.

        Parameters:
        -----------
        model: str
            The model used for the API call
        prompt_tokens: int
            Number of tokens in the prompt
        completion_tokens: int
            Number of tokens in the completion

        Returns:
        --------
        float
            Cost in USD
        """
        # Get cost rates for the model
        if model in self.MODEL_COSTS:
            rates = self.MODEL_COSTS[model]
        else:
            # Use GPT-3.5 rates as default
            rates = self.MODEL_COSTS["gpt-3.5-turbo"]

        # Calculate cost
        prompt_cost = (prompt_tokens / 1000) * rates["input"]
        completion_cost = (completion_tokens / 1000) * rates["output"]

        return prompt_cost + completion_cost

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of API usage and costs.

        Returns:
        --------
        Dict[str, Any]
            Summary of API usage and costs
        """
        return {"total_cost_usd": self.total_cost, "model_usage": self.model_usage}

    def print_summary(self) -> None:
        """
        Print a summary of API usage and costs.
        """
        print("\n=== API Usage Cost Summary ===")
        print(f"Total Cost: ${self.total_cost:.4f} USD")
        print("\nBreakdown by Model:")

        for model, usage in self.model_usage.items():
            print(f"\n{model}:")
            print(f"  Prompt Tokens: {usage['prompt_tokens']}")
            print(f"  Completion Tokens: {usage['completion_tokens']}")
            print(f"  Cost: ${usage['cost']:.4f} USD")
