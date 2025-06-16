from src.components.ragchain_runner import RAGChainRunner
from src.utils.app_config import AppConfig
from src.utils.mlflow_tracker import MLflowTracker 
 
def main() -> None:
    cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")
    with MLflowTracker(run_name="rag_run") as tracker:
        rag = RAGChainRunner(cfg, mlflow_tracker=tracker)
        question = input("💬 Question: ")
        print("🧠 Thinking...")
        answer = rag.answer(question)
        print("🤖", answer)


if __name__ == "__main__":  # pragma: no cover
    main()


  