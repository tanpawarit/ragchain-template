"""
End-to-end evaluation module for the Typhoon RAG system.

This module contains functions to evaluate the complete RAG pipeline
from query to final response, measuring overall system performance.
"""

from typing import Dict, List, Any, Optional, Callable, Union
from openai import OpenAI
import numpy as np
from tqdm import tqdm


def evaluate_e2e_system(
    test_data: List[Dict[str, Any]],
    rag_system: Union[Callable, Any],
    evaluation_model: str = "gpt-4o",
    batch_size: int = 10,
    openai_client: Optional[OpenAI] = None,
    config: Optional[Any] = None,
    mlflow_tracker: Optional[Any] = None,
    experiment_name: Optional[str] = None,
    cost_tracker: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Evaluate the end-to-end performance of a RAG system.
    
    Parameters:
    -----------
    test_data: List[Dict[str, Any]]
        List of test cases with "question", "ground_truth", and optionally "context"
    rag_system: Union[Callable, Any]
        Function or object with a query method that takes a question and returns a response
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
    
    # Define the query function based on the type of rag_system
    if callable(rag_system):
        query_fn = rag_system
    elif hasattr(rag_system, 'query'):
        query_fn = rag_system.query
    else:
        raise ValueError("rag_system must be a callable or have a 'query' method")
    
    results: Dict[str, Any] = {
        "per_query": [],
        "metrics": {
            "answer_relevance": [],
            "context_relevance": [],
            "factual_accuracy": [],
            "hallucination": [],
            "overall_quality": []
        }
    }
    
    # Process test data in batches
    for i in tqdm(range(0, len(test_data), batch_size), desc="Evaluating E2E system"):
        batch = test_data[i:i+batch_size]
        
        for item in batch:
            question = item["question"]
            ground_truth = item.get("ground_truth", "")
            
            # Get system response
            try:
                system_response = query_fn(question)
                
                # Extract answer and context if response is a dictionary
                if isinstance(system_response, dict):
                    answer = system_response.get("answer", "")
                    contexts = system_response.get("contexts", [])
                    context_text = "\n\n".join(contexts) if contexts else ""
                else:
                    # Assume response is the answer text
                    answer = system_response
                    context_text = ""
                
                # Evaluate the response
                evaluation_result = evaluate_rag_response(
                    question=question,
                    answer=answer,
                    context=context_text,
                    ground_truth=ground_truth,
                    openai_client=openai_client,
                    evaluation_model=evaluation_model,
                    cost_tracker=cost_tracker
                )
                
                # Store individual result
                query_result = {
                    "question": question,
                    "answer": answer,
                    "context": context_text,
                    "ground_truth": ground_truth,
                    "metrics": evaluation_result
                }
                
            except Exception as e:
                print(f"Error processing question '{question}': {e}")
                evaluation_result = {
                    "answer_relevance": 0.0,
                    "context_relevance": 0.0,
                    "factual_accuracy": 0.0,
                    "hallucination": 10.0,  # High hallucination score for errors
                    "overall_quality": 0.0
                }
                
                query_result = {
                    "question": question,
                    "answer": f"ERROR: {str(e)}",
                    "context": "",
                    "ground_truth": ground_truth,
                    "metrics": evaluation_result,
                    "error": str(e)
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


def evaluate_rag_response(
    question: str,
    answer: str,
    context: str,
    ground_truth: str,
    openai_client: OpenAI,
    evaluation_model: str = "gpt-4o",
    cost_tracker: Optional[Any] = None
) -> Dict[str, float]:
    """
    Evaluate a RAG system response using LLM-based evaluation.
    
    Parameters:
    -----------
    question: str
        The original question
    answer: str
        The answer generated by the RAG system
    context: str
        The context retrieved and used by the RAG system
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
    You are an expert evaluator for RAG (Retrieval-Augmented Generation) systems. Please evaluate the following response to a question.
    
    Question: {question}
    
    Retrieved Context: {context}
    
    Generated Answer: {answer}
    
    Reference Answer: {ground_truth}
    
    Please evaluate the response on the following criteria on a scale of 1-10:
    1. Answer Relevance: How relevant is the answer to the question? (1: completely irrelevant, 10: perfectly relevant)
    2. Context Relevance: How relevant is the retrieved context to the question? (1: completely irrelevant, 10: perfectly relevant)
    3. Factual Accuracy: How factually accurate is the answer compared to the reference? (1: completely inaccurate, 10: perfectly accurate)
    4. Hallucination: Does the answer contain information not supported by the context? (1: no hallucination, 10: severe hallucination)
    5. Overall Quality: Overall quality of the RAG response considering all factors. (1: poor quality, 10: excellent quality)
    
    Provide your evaluation as a JSON object with the following format:
    {{
        "answer_relevance": <score>,
        "context_relevance": <score>,
        "factual_accuracy": <score>,
        "hallucination": <score>,
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
            "answer_relevance": 0.0,
            "context_relevance": 0.0,
            "factual_accuracy": 0.0,
            "hallucination": 10.0,  # High hallucination score for errors
            "overall_quality": 0.0
        }
