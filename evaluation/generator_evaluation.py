"""
Generator evaluation module for the Typhoon RAG system.

This module contains functions to evaluate the quality of generated responses
using various metrics such as relevance, coherence, and factual accuracy.
"""

from typing import Dict, List, Any, Optional, Tuple
from openai import OpenAI
import numpy as np
from tqdm import tqdm


def evaluate_generator(
    test_data: List[Dict[str, Any]],
    generator_fn: callable,
    evaluation_model: str = "gpt-4o",
    batch_size: int = 10,
    openai_client: Optional[OpenAI] = None,
    config: Optional[Any] = None,
    mlflow_tracker: Optional[Any] = None,
    experiment_name: Optional[str] = None,
    cost_tracker: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Evaluate the quality of generated responses using LLM-based evaluation.
    
    Parameters:
    -----------
    test_data: List[Dict[str, Any]]
        List of test cases with "question" and "ground_truth" (expected answer)
    generator_fn: callable
        Function that takes a question and returns a generated response
    evaluation_model: str
        The model to use for evaluation
    batch_size: int
        Batch size for processing test data
    openai_client: Optional[OpenAI]
        Pre-initialized OpenAI client (will create one if None)
    config: Optional[Any]
        Application configuration containing OpenAI API key
    mlflow_tracker: Optional[Any]
        MLflow tracker instance for logging metrics and artifacts
    experiment_name: str
        Name of the MLflow experiment to use if creating a new tracker
    cost_tracker: Optional[Any]
        Cost tracker for monitoring API usage
        
    Returns:
    --------
    Dict[str, Any]
        Evaluation results including per-query metrics and averages
    """
    # Create OpenAI client if not provided
    if openai_client is None:
        if config and hasattr(config, 'openai_api_key') and config.openai_api_key:
            openai_client = OpenAI(api_key=config.openai_api_key)
        else:
            openai_client = OpenAI()
    
    # Initialize MLflow tracking if requested
    if mlflow_tracker is None and experiment_name is not None:
        from mlflow import MlflowClient
        client = MlflowClient()
        experiment = client.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = client.create_experiment(experiment_name)
        else:
            experiment_id = experiment.experiment_id
        
        # Start a new run
        from mlflow import start_run
        run = start_run(experiment_id=experiment_id)
        mlflow_tracker = run
    
    results: Dict[str, Any] = {
        "per_query": [],
        "metrics": {
            "relevance": [],
            "coherence": [],
            "factual_accuracy": [],
            "overall_quality": []
        }
    }
    
    # Process test data in batches
    for i in tqdm(range(0, len(test_data), batch_size), desc="Evaluating generator"):
        batch = test_data[i:i+batch_size]
        
        for item in batch:
            question = item["question"]
            ground_truth = item.get("ground_truth", "")
            
            # Generate response using the provided function
            generated_response = generator_fn(question)
            
            # Evaluate the generated response
            evaluation_result = evaluate_response_quality(
                question=question,
                generated_response=generated_response,
                ground_truth=ground_truth,
                openai_client=openai_client,
                evaluation_model=evaluation_model,
                cost_tracker=cost_tracker
            )
            
            # Store individual result
            query_result = {
                "question": question,
                "generated_response": generated_response,
                "ground_truth": ground_truth,
                "metrics": evaluation_result
            }
            results["per_query"].append(query_result)
            
            # Accumulate metrics
            for metric_name, metric_value in evaluation_result.items():
                if metric_name in results["metrics"]:
                    results["metrics"][metric_name].append(metric_value)
    
    # Calculate average metrics
    for metric_name, values in results["metrics"].items():
        if values:
            results[f"avg_{metric_name}"] = np.mean(values)
    
    # Log metrics to MLflow if tracker is provided
    if mlflow_tracker:
        for metric_name, avg_value in [(f"avg_{k}", v) for k, v in results["metrics"].items()]:
            if isinstance(avg_value, (int, float)):
                mlflow_tracker.log_metric(metric_name, float(avg_value))
    
    return results


def evaluate_response_quality(
    question: str,
    generated_response: str,
    ground_truth: str,
    openai_client: OpenAI,
    evaluation_model: str = "gpt-4o",
    cost_tracker: Optional[Any] = None
) -> Dict[str, float]:
    """
    Evaluate the quality of a generated response using LLM-based evaluation.
    
    Parameters:
    -----------
    question: str
        The original question
    generated_response: str
        The response generated by the system
    ground_truth: str
        The expected correct answer
    openai_client: OpenAI
        OpenAI client for making API calls
    evaluation_model: str
        The model to use for evaluation
    cost_tracker: Optional[Any]
        Cost tracker for monitoring API usage
        
    Returns:
    --------
    Dict[str, float]
        Dictionary with evaluation metrics
    """
    prompt = f"""
    You are an expert evaluator for question-answering systems. Please evaluate the following response to a question.
    
    Question: {question}
    
    Generated Response: {generated_response}
    
    Reference Answer: {ground_truth}
    
    Please evaluate the generated response on the following criteria on a scale of 1-10:
    1. Relevance: How relevant is the response to the question? (1: completely irrelevant, 10: perfectly relevant)
    2. Coherence: How coherent and well-structured is the response? (1: incoherent, 10: perfectly coherent)
    3. Factual Accuracy: How factually accurate is the response compared to the reference answer? (1: completely inaccurate, 10: perfectly accurate)
    4. Overall Quality: Overall quality of the response considering all factors. (1: poor quality, 10: excellent quality)
    
    Provide your evaluation as a JSON object with the following format:
    {{
        "relevance": <score>,
        "coherence": <score>,
        "factual_accuracy": <score>,
        "overall_quality": <score>
    }}
    
    Only return the JSON object, nothing else.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model=evaluation_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Track costs if a cost tracker is provided
        if cost_tracker:
            cost_tracker.track_completion(
                model=evaluation_model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )
        
        # Parse the evaluation result
        import json
        evaluation_result = json.loads(response.choices[0].message.content)
        
        return evaluation_result
    
    except Exception as e:
        print(f"Error during evaluation: {e}")
        # Return default values in case of error
        return {
            "relevance": 0.0,
            "coherence": 0.0,
            "factual_accuracy": 0.0,
            "overall_quality": 0.0
        }
