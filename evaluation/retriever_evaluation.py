from typing import Any, Dict, List, Optional
import json
import numpy as np
from pathlib import Path
from tqdm import tqdm
from openai import OpenAI
import mlflow
from deepeval import evaluate
from deepeval.metrics import ContextualRelevancyMetric, FaithfulnessMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

from src.utils.mlflow_tracker import MLflowTracker
from src.utils.app_config import AppConfig


def evaluate_retriever_evaluation(
    vectorstore,
    test_data: List[Dict[str, Any]],
    k_value: int = 3,
    similarity_threshold: float = 0.5,
    embedding_model: str = "text-embedding-3-small",
    evaluation_model: str = "gpt-4o",
    batch_size: int = 10,
    config: Optional[Any] = None,
    mlflow_tracker: Optional[Any] = None,
    experiment_name: Optional[str] = None,
    max_contexts: Optional[int] = None,
    cost_tracker: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Evaluate precision and recall of a retriever using DeepEval metrics.
    
    Parameters:
    -----------
    vectorstore: Any
        The vector store to evaluate
    test_data: List[Dict[str, Any]]
        List of test cases with "question" (query) and "ideal_context" (expected relevant content)
    k_value: int
        Number of documents to retrieve for each query
    similarity_threshold: float
        Threshold for considering a document relevant (used for traditional metrics)
    embedding_model: str
        OpenAI embedding model to use for traditional evaluation (used for traditional metrics)
    batch_size: int
        Batch size for processing test data
    openai_client: Optional[OpenAI]
        Pre-initialized OpenAI client (will create one if None)
    evaluation_model: str
        The model to use for DeepEval metrics evaluation
    mlflow_tracker: Optional[MLflowTracker]
        MLflow tracker instance for logging metrics and artifacts
    experiment_name: str
        Name of the MLflow experiment to use if creating a new tracker
    config: Optional[AppConfig]
        Application configuration containing OpenAI API key
    max_contexts: Optional[int]
        Maximum number of contexts to use for mock answer creation (None means use all)
        
    Returns:
    --------
    Dict[str, Any]
        Evaluation results including per-query metrics and averages
    """
    
    # Create OpenAI client
    if config and hasattr(config, 'openai_api_key') and config.openai_api_key:
        client = OpenAI(api_key=config.openai_api_key)
    elif config and hasattr(config, 'openai_token') and config.openai_token:
        # Set environment variable for OpenAI API key
        import os
        os.environ["OPENAI_API_KEY"] = config.openai_token
        client = OpenAI(api_key=config.openai_token)
    else:
        # Fall back to environment variable if set
        client = OpenAI()
    
    # Use cost tracker if provided
    if cost_tracker is None:
        from src.utils.cost_tracker import OpenAICostTracker
        cost_tracker = OpenAICostTracker()
    
    # Create or use provided MLflow tracker
    use_internal_mlflow = False
    if mlflow_tracker is None:
        # Check if we're already in an MLflow run (e.g., from a context manager)
        active_run = mlflow.active_run()
        if active_run:
            # Use the active run directly
            mlflow_tracker = None  # We'll use mlflow directly
        elif experiment_name:  # Only create a new tracker if experiment_name is provided
            mlflow_tracker = MLflowTracker(experiment_name=experiment_name, run_name=f"retriever_eval_{embedding_model}")
            use_internal_mlflow = True
    
    # Log evaluation parameters if MLflow is available
    params = {
        "k_value": k_value,
        "similarity_threshold": similarity_threshold,
        "embedding_model": embedding_model,
        "evaluation_model": evaluation_model,
        "batch_size": batch_size,
        "test_data_size": len(test_data),
        "vectorstore_type": type(vectorstore).__name__,
        "max_contexts": max_contexts
    }
    
    # Use either MLflowTracker or direct mlflow API
    if mlflow_tracker:
        mlflow_tracker.log_params(params)
    elif mlflow.active_run():  # If we're in an active run but no tracker provided
        for key, value in params.items():
            mlflow.log_param(key, value)
    
    # Initialize metrics
    contextual_relevancy_metric = ContextualRelevancyMetric(
        threshold=similarity_threshold,
        model=evaluation_model
    )
    
    answer_relevancy_metric = AnswerRelevancyMetric(
        threshold=similarity_threshold,
        model=evaluation_model
    )
    
    faithfulness_metric = FaithfulnessMetric(
        threshold=similarity_threshold,
        model=evaluation_model
    )
    
    test_cases = []
    traditional_results = []
    
    # Process test data in batches
    for i in tqdm(range(0, len(test_data), batch_size), desc="Preparing test cases"):
        batch = test_data[i:i+batch_size]
        
        for item in batch:
            question = item["question"]
            expected_output = item["ideal_context"][0] if item["ideal_context"] else ""
            
            # Retrieve documents from vectorstore
            retrieved_docs = vectorstore.similarity_search(question, k=k_value)
            retrieved_contents = [doc.page_content for doc in retrieved_docs]
            
            # Check if item has a specific max_contexts value (for ablation studies)
            item_max_contexts = item.get("max_contexts", max_contexts)
            
            # Create a mock answer based on retrieved content, limiting contexts if specified
            if item_max_contexts is not None:
                contexts_to_use = retrieved_contents[:item_max_contexts]
            else:
                contexts_to_use = retrieved_contents
                
            mock_answer = f"Answer based on: {', '.join(contexts_to_use)}"
            
            # Create DeepEval test case
            test_case = LLMTestCase(
                input=question,
                actual_output=mock_answer,
                expected_output=expected_output,  # Optional
                context=item["ideal_context"],
                retrieval_context=retrieved_contents
            )
            test_cases.append(test_case)
            
            # Calculate traditional metrics for comparison
            # Get embeddings for expected output
            if expected_output:
                # Track embedding cost for expected output
                cost_tracker.track_embedding_cost(embedding_model, expected_output)
                
                expected_embedding_response = client.embeddings.create(
                    model=embedding_model,
                    input=[expected_output]
                )
                expected_embedding = expected_embedding_response.data[0].embedding
                
                # Track embedding cost for retrieved documents
                for content in retrieved_contents:
                    cost_tracker.track_embedding_cost(embedding_model, content)
                
                # Get embeddings for retrieved documents
                retrieved_embedding_response = client.embeddings.create(
                    model=embedding_model,
                    input=retrieved_contents
                )
                retrieved_embeddings = [item.embedding for item in retrieved_embedding_response.data]
                
                # Calculate similarities
                similarities = []
                for retrieved_embedding in retrieved_embeddings:
                    expected_array = np.array(expected_embedding).reshape(1, -1)
                    retrieved_array = np.array(retrieved_embedding).reshape(1, -1)
                    similarity = float(np.dot(expected_array, retrieved_array.T)[0][0])
                    similarities.append(similarity)
                
                # Calculate traditional metrics
                relevant_docs = [sim for sim in similarities if sim > similarity_threshold]
                precision = len(relevant_docs) / len(retrieved_contents) if retrieved_contents else 0
                recall = 1.0 if relevant_docs else 0.0  # Assuming one relevant document
                f1_score = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0
                
                traditional_results.append({
                    "question": question,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1_score,
                    "max_similarity": max(similarities) if similarities else 0,
                })
    
    # Run DeepEval evaluation
    metrics = [
        contextual_relevancy_metric,
        answer_relevancy_metric,
        faithfulness_metric
    ]
    
    # Track evaluation costs for DeepEval metrics
    # DeepEval uses the evaluation_model for its metrics
    for test_case in test_cases:
        # Track cost for input (query) evaluation
        if hasattr(test_case, 'input') and test_case.input:
            cost_tracker.track_evaluation_cost(evaluation_model, test_case.input, "")
        
        # Track cost for context evaluation
        if hasattr(test_case, 'context') and test_case.context:
            cost_tracker.track_evaluation_cost(evaluation_model, test_case.context, "")
            
        # Track cost for retrieval context evaluation
        if hasattr(test_case, 'retrieval_context') and test_case.retrieval_context:
            for context in test_case.retrieval_context:
                cost_tracker.track_evaluation_cost(evaluation_model, context, "")
                
        # Track cost for expected output evaluation
        if hasattr(test_case, 'expected_output') and test_case.expected_output:
            cost_tracker.track_evaluation_cost(evaluation_model, test_case.expected_output, "")
            
    evaluation_result = evaluate(
        test_cases=test_cases,
        metrics=metrics
    )
    
    # Process DeepEval results
    deepeval_results = []
    for result in evaluation_result.test_results:
        result_dict = {
            "question": result.input,
            "metrics": {}
        }
        
        for metric_data in result.metrics_data:
            result_dict["metrics"][metric_data.name] = {
                "score": metric_data.score,
                "success": metric_data.success,
                "reason": metric_data.reason
            }
        
        deepeval_results.append(result_dict)
        
    # Save evaluation results to JSON file for MLflow logging
    if mlflow_tracker:
        results_path = Path("./tmp_evaluation_results.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(deepeval_results, f, ensure_ascii=False, indent=2)
        mlflow_tracker.log_artifact(results_path) 
        try:
            results_path.unlink(missing_ok=True)
        except Exception as e:
            print(f"Warning: failed to delete temp file {results_path}: {e}")
    
    # Calculate traditional averages (if available)
    traditional_metrics = {}
    if traditional_results:
        traditional_metrics = {
            "average_precision": sum(r["precision"] for r in traditional_results) / len(traditional_results),
            "average_recall": sum(r["recall"] for r in traditional_results) / len(traditional_results),
            "average_f1": sum(r["f1_score"] for r in traditional_results) / len(traditional_results),
            "average_max_similarity": sum(r["max_similarity"] for r in traditional_results) / len(traditional_results),
        }
    
    # Calculate DeepEval averages
    deepeval_averages = {}
    for metric_name in ["Contextual Relevancy", "Answer Relevancy", "Faithfulness"]:
        scores = [
            r["metrics"].get(metric_name, {}).get("score", 0) 
            for r in deepeval_results 
            if metric_name in r["metrics"]
        ]
        if scores:
            deepeval_averages[f"average_{metric_name.lower().replace(' ', '_')}"] = sum(scores) / len(scores)
    
    # Log metrics to MLflow if available
    metrics = {
        # Traditional metrics
        "average_precision": traditional_metrics.get("average_precision", 0),
        "average_recall": traditional_metrics.get("average_recall", 0),
        "average_f1": traditional_metrics.get("average_f1", 0),
        "average_similarity": traditional_metrics.get("average_max_similarity", 0)
    }
    
    # Add DeepEval metrics
    if deepeval_averages:
        metrics.update({
            "average_contextual_relevancy": deepeval_averages.get("average_contextual_relevancy", 0),
            "average_answer_relevancy": deepeval_averages.get("average_answer_relevancy", 0),
            "average_faithfulness": deepeval_averages.get("average_faithfulness", 0)
        })
    
    # Log metrics using either MLflowTracker or direct mlflow API
    if mlflow_tracker:
        mlflow_tracker.log_metrics(metrics)
    elif mlflow.active_run():  # If we're in an active run but no tracker provided
        for key, value in metrics.items():
            mlflow.log_metric(key, value)
    
    # End MLflow run if we created it
    if use_internal_mlflow and mlflow_tracker:
        mlflow_tracker.end_run()
    
    return {
        "deepeval_results": deepeval_results,
        "deepeval_averages": deepeval_averages,
        "traditional_results": traditional_results,
        "traditional_metrics": traditional_metrics,
        "total_queries": len(test_cases),
        "threshold_used": similarity_threshold
    }
