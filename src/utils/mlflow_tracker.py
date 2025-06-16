from __future__ import annotations

"""Thin wrapper around **MLflow** to keep call-sites minimal and testable."""

from pathlib import Path
from typing import Any, Dict, Optional

import mlflow


class MLflowTracker:
    """Utility that standardises MLflow logging calls across the codebase."""

    def __init__(self, experiment_name: str = "default", run_name: Optional[str] = None) -> None:
        mlflow.set_experiment(experiment_name)
        self._run = mlflow.start_run(run_name=run_name)

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    def log_params(self, params: Dict[str, Any]) -> None:
        mlflow.log_params(params)

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        mlflow.log_metrics(metrics, step=step)

    def log_artifact(self, path: str | Path, artifact_path: Optional[str] = None) -> None:
        mlflow.log_artifact(str(path), artifact_path=artifact_path)

    # ------------------------------------------------------------------
    # Context manager helpers
    # ------------------------------------------------------------------
    def end(self) -> None:
        if self._run is not None:
            mlflow.end_run()
            self._run = None

    def __enter__(self) -> MLflowTracker:
        return self

    def __exit__(self, exc_type, exc, tb):   
        self.end() 
        return False
