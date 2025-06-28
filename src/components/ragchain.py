from src.components.ragchain_runner import RAGChainRunner
from src.utils.config.app_config import AppConfig
from src.utils.pipeline.mlflow_tracker import MLflowTracker
from src.utils.pipeline.vectorstore_manager import load_vectorstore


def main() -> None:
    cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")

    # รับข้อมูลผู้ใช้
    user_id = input("👤 User ID (กด Enter เพื่อข้าม): ")

    with MLflowTracker(run_name="rag_run") as tracker:
        # บันทึกข้อมูลผู้ใช้
        if user_id:
            tracker.log_params({"user_id": user_id})

        # Load the vectorstore first
        vectorstore = load_vectorstore(
            cfg, data_version="latest", mlflow_tracker=tracker
        )

        rag = RAGChainRunner(cfg, mlflow_tracker=tracker, vectorstore=vectorstore)
        question = input("💬 Question: ")
        print("🧠 Thinking...")
        answer = rag.answer(question, user_id=user_id if user_id else None)
        print("🤖", answer)


if __name__ == "__main__":  # pragma: no cover
    main()
