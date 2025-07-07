from datetime import datetime

from src.components.ragchain_runner import RAGChainRunner
from src.utils.config.app_config import AppConfig
from src.utils.config.config_manager import get_config
from src.utils.logger import get_logger
from src.utils.pipeline.mlflow_tracker import MLflowTracker
from src.utils.pipeline.vectorstore_manager import load_vectorstore

logger = get_logger(__name__)


def main() -> None:
    cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")

    # รับข้อมูลผู้ใช้
    user_id = input("👤 User ID (กด Enter เพื่อข้าม): ")

    # Load MLflow config
    mlflow_config = get_config("config.yaml").get("mlflow", {})
    experiment_name = mlflow_config.get("experiment_name", "default")

    with MLflowTracker(
        experiment_name=experiment_name, run_name="rag_chat_session"
    ) as tracker:
        # บันทึกข้อมูลผู้ใช้
        if user_id:
            tracker.log_params({"user_id": user_id})

        # Load the vectorstore first
        logger.info("🔄 Loading vectorstore...")
        vectorstore = load_vectorstore(cfg, mlflow_tracker=tracker)

        rag = RAGChainRunner(cfg, mlflow_tracker=tracker, vectorstore=vectorstore)

        # Set session ID for tracking multiple queries in this chat session
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        rag.set_session_id(session_id)

        logger.info(f"📊 Chat session started with ID: {session_id}")

        print("🤖 RAG Chatbot พร้อมใช้งานแล้ว! (พิมพ์ 'quit', 'exit', หรือ 'bye' เพื่อออก)")
        print("-" * 50)

        # Interactive chat loop
        question_count = 0
        while True:
            try:
                question = input("💬 คำถาม: ").strip()

                # Check for exit commands
                if question.lower() in ["quit", "exit", "bye", "ออก", "จบ", "เลิก"]:
                    print("👋 ขอบคุณที่ใช้งาน RAG Chatbot!")
                    logger.info(
                        f"Chat session ended. Total questions: {question_count}"
                    )
                    break

                # Skip empty questions
                if not question:
                    print("⚠️  กรุณาใส่คำถาม")
                    continue

                question_count += 1
                logger.info(
                    f"🧠 Processing question #{question_count}: {question[:50]}..."
                )

                answer = rag.answer(question, user_id=user_id if user_id else None)
                print(f"🤖 {answer}")
                print("-" * 50)

            except KeyboardInterrupt:
                print("\n👋 ขอบคุณที่ใช้งาน RAG Chatbot!")
                logger.info(
                    f"Chat session interrupted. Total questions: {question_count}"
                )
                break
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาด: {e}")
                print(f"❌ เกิดข้อผิดพลาด: {e}")
                print("💡 ลองถามคำถามใหม่ หรือพิมพ์ 'quit' เพื่อออก")


if __name__ == "__main__":  # pragma: no cover
    main()
