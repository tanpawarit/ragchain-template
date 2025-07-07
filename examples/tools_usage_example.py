#!/usr/bin/env python3
"""
Example script demonstrating RAG chatbot with tools enabled.

This script shows how to:
1. Configure tools in the model config
2. Use the RAG chatbot with tools enabled
3. Ask questions that can benefit from tool usage
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.components.ragchain_runner import RAGChainRunner
from src.utils.config.app_config import AppConfig
from src.utils.logger import get_logger
from src.utils.pipeline.vectorstore_manager import load_vectorstore

logger = get_logger(__name__)


def main() -> None:
    """Demonstrate RAG chatbot with tools."""

    # Load configuration
    cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")

    # Load vectorstore
    logger.info("🔄 Loading vectorstore...")
    vectorstore = load_vectorstore(cfg)

    # Create RAG runner
    rag = RAGChainRunner(cfg, vectorstore=vectorstore)

    # Print tool information
    if rag.tools_enabled:
        tool_info = rag.tool_manager.get_tool_info()
        print("🛠️  Tools enabled!")
        print(f"📊 Total tools: {tool_info['total_tools']}")
        print("📋 Available tools:")
        for tool in tool_info["tools"]:
            print(f"   • {tool['name']}: {tool['description']}")
    else:
        print("❌ Tools are disabled")

    print("\n" + "=" * 60)
    print("🤖 RAG Chatbot with Tools - Example Questions")
    print("=" * 60)

    # Example questions that can benefit from tools
    example_questions = [
        "What is 15 multiplied by 23?",
        "Calculate the expression: (100 + 50) * 2 - 25",
        "What is the 10th Fibonacci number?",
        "Analyze this text: 'Hello world! This is a sample text for analysis.'",
        "Count the words in this sentence: 'The quick brown fox jumps over the lazy dog.'",
        "Calculate statistics for these numbers: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]",
    ]

    print("\n📝 Example questions you can ask:")
    for i, question in enumerate(example_questions, 1):
        print(f"{i}. {question}")

    print(
        "\n💡 You can also ask questions about your documents combined with tool usage!"
    )
    print(
        "   For example: 'Based on the documents, calculate 25% of the total revenue'"
    )

    print("\n" + "-" * 60)
    print("🔍 Interactive Mode - Ask your questions!")
    print("   (Type 'quit', 'exit', or 'bye' to exit)")
    print("-" * 60)

    # Interactive loop
    question_count = 0
    while True:
        try:
            question = input("\n💬 Your question: ").strip()

            # Check for exit commands
            if question.lower() in ["quit", "exit", "bye", "ออก", "จบ", "เลิก"]:
                print("👋 Thank you for using the RAG Chatbot with Tools!")
                break

            # Skip empty questions
            if not question:
                print("⚠️  Please enter a question")
                continue

            question_count += 1
            print(f"\n🧠 Processing question #{question_count}...")

            # Get answer
            answer = rag.answer(question)
            print(f"\n🤖 Answer: {answer}")

        except KeyboardInterrupt:
            print("\n\n👋 Thank you for using the RAG Chatbot with Tools!")
            break
        except Exception as e:
            logger.error(f"Error occurred: {e}")
            print(f"❌ Error: {e}")
            print("💡 Try asking a different question or type 'quit' to exit")


if __name__ == "__main__":
    main()
