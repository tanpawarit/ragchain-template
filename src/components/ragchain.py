from src.components.ragchain_runner import RAGChainRunner
from src.utils.app_config import AppConfig
from src.utils.mlflow_tracker import MLflowTracker 
from typing import Optional
 
def main() -> None:
    cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")
    
    # รับข้อมูลผู้ใช้
    user_id = input("👤 User ID (กด Enter เพื่อข้าม): ")
    
    with MLflowTracker(run_name="rag_run") as tracker:
        # บันทึกข้อมูลผู้ใช้
        if user_id:
            tracker.log_params({"user_id": user_id})
            
        rag = RAGChainRunner(cfg, mlflow_tracker=tracker)
        question = input("💬 Question: ")
        print("🧠 Thinking...")
        answer = rag.answer(question, user_id=user_id if user_id else None)
        print("🤖", answer)


if __name__ == "__main__":  # pragma: no cover
    main()
  