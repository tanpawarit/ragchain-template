"""
Example usage of the RAGEvaluator.

This script demonstrates how to use the evaluation system
for evaluating RAG components.
"""

from evaluator import RAGEvaluator, load_test_data


def example_retrieval_evaluation():
    """Example of how to evaluate a retrieval system."""
    print("=== Retrieval Evaluation Example ===")

    # Initialize evaluator
    evaluator = RAGEvaluator()

    # Load test data
    test_data = load_test_data("test_data/golden_dataset_v1.json")

    # Mock vectorstore for demonstration
    class MockVectorstore:
        def similarity_search(self, query: str, k: int = 5):
            # Mock documents - in real usage, this would be your actual vectorstore
            class MockDoc:
                def __init__(self, content: str):
                    self.page_content = content

            # Return mock relevant documents
            return [
                MockDoc(
                    "ส่วน Introduction to Quant Offside 3X ระบุว่าเนื้อหาเน้น Data-Driven Trading และ AI Investing"
                ),
                MockDoc("คอร์สนี้มุ่งเน้นการเทรดที่ขับเคลื่อนด้วยข้อมูล"),
                MockDoc("การลงทุนด้วย AI ทำให้ผู้เรียนเข้าใจตลาดเชิงลึก"),
            ]

    # Evaluate retrieval
    vectorstore = MockVectorstore()
    results = evaluator.evaluate_retrieval(vectorstore, test_data[:3], k=3)

    print(f"Average Precision: {results['summary']['avg_precision']:.3f}")
    print(f"Average Recall: {results['summary']['avg_recall']:.3f}")
    print(f"Average F1 Score: {results['summary']['avg_f1_score']:.3f}")
    print(f"Average Relevance: {results['summary']['avg_relevance']:.3f}")

    # Save results
    evaluator.save_results(results, "results/retrieval_evaluation.json")
    print("Results saved to results/retrieval_evaluation.json\n")


def example_generation_evaluation():
    """Example of how to evaluate a generation system."""
    print("=== Generation Evaluation Example ===")

    # Initialize evaluator
    evaluator = RAGEvaluator()

    # Load test data
    test_data = load_test_data("test_data/golden_dataset_v1.json")

    # Mock generator function
    def mock_generator(question: str) -> str:
        # Mock generator - in real usage, this would be your actual generator
        if "จุดเด่น" in question:
            return (
                "คอร์สนี้เน้น Data-Driven Trading และ AI Investing เพื่อให้ผู้เรียนเข้าใจตลาดได้ดีขึ้น"
            )
        elif "rerun" in question:
            return "การ rerun ช่วยให้เทรดเดอร์ระดับผู้บริหารเข้าใจ Hedge Fund และ Quant Trading"
        else:
            return "ขออภัย ไม่สามารถตอบคำถามนี้ได้"

    # Evaluate generation
    results = evaluator.evaluate_generation(test_data[:3], mock_generator)

    print(f"Average Relevance: {results['summary']['avg_relevance']:.3f}")
    print(f"Average Coherence: {results['summary']['avg_coherence']:.3f}")
    print(f"Average Accuracy: {results['summary']['avg_accuracy']:.3f}")
    print(f"Average Overall Quality: {results['summary']['avg_overall_quality']:.3f}")

    # Save results
    evaluator.save_results(results, "results/generation_evaluation.json")
    print("Results saved to results/generation_evaluation.json\n")


def example_rag_evaluation():
    """Example of how to evaluate an end-to-end RAG system."""
    print("=== RAG System Evaluation Example ===")

    # Initialize evaluator
    evaluator = RAGEvaluator()

    # Load test data
    test_data = load_test_data("test_data/golden_dataset_v1.json")

    # Mock RAG system
    class MockRAGSystem:
        def query(self, question: str) -> dict:
            # Mock RAG response - in real usage, this would be your actual RAG system
            context = "ส่วน Introduction to Quant Offside 3X ระบุว่าเนื้อหาเน้น Data-Driven Trading และ AI Investing"

            if "จุดเด่น" in question:
                answer = "คอร์สนี้มุ่งเน้นการเทรดที่ขับเคลื่อนด้วยข้อมูล (Data-Driven Trading) และการลงทุนด้วย AI"
            elif "rerun" in question:
                answer = (
                    "การ rerun ช่วยให้เทรดเดอร์ระดับ CEO และ CFO เข้าใจพลวัตของ Hedge Fund"
                )
            else:
                answer = "ขออภัย ไม่สามารถตอบคำถามนี้ได้"

            return {
                "answer": answer,
                "context": context,
                "sources": ["mock_source_1", "mock_source_2"],
            }

    # Evaluate RAG system
    rag_system = MockRAGSystem()
    results = evaluator.evaluate_rag_system(test_data[:3], rag_system)

    print(f"Average Answer Relevance: {results['summary']['avg_answer_relevance']:.3f}")
    print(
        f"Average Context Relevance: {results['summary']['avg_context_relevance']:.3f}"
    )
    print(f"Average Accuracy: {results['summary']['avg_accuracy']:.3f}")
    print(f"Average Overall Quality: {results['summary']['avg_overall_quality']:.3f}")
    print(
        f"Successful Queries: {results['summary']['successful_queries']}/{results['summary']['total_queries']}"
    )

    # Save results
    evaluator.save_results(results, "results/rag_evaluation.json")
    print("Results saved to results/rag_evaluation.json\n")


def main():
    """Run all evaluation examples."""
    print("RAG Evaluator Examples")
    print("=" * 30)

    try:
        example_retrieval_evaluation()
        example_generation_evaluation()
        example_rag_evaluation()

        print("All evaluations completed successfully!")
        print("Check the 'results/' directory for detailed evaluation results.")

    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure you have:")
        print("1. OpenAI API key set in environment variables")
        print("2. Test data files in the correct location")
        print("3. Required dependencies installed (openai, numpy)")


if __name__ == "__main__":
    main()
