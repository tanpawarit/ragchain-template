from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.prompts.prompt_manager import PromptManager
from src.utils.config.manager import get_config

"""Centralised application configuration model.

Loads YAML config files once and exposes strongly-typed attributes for the
rest of the codebase.  This avoids scattering YAML-parsing logic throughout the
project and makes unit-testing easier by allowing the config object to be
constructed directly in memory.

Usage
-----
>>> cfg = AppConfig.from_files("configs/model_config.yaml", "config.yaml")
>>> cfg.embedding_model_name  # => "text-embedding-3-small"
"""


@dataclass(slots=True)
class AppConfig:
    """Application-wide, read-only configuration."""

    embedding_model_name: str
    llm_model_name: str
    data_folder: str
    file_names: List[str]
    faiss_index_path: str
    retriever_search_type: str
    retriever_k_value: int
    openai_token: str
    prompt_template: str
    prompt_template_name: str
    prompt_template_version: Optional[str]

    # ---------------------------------------------------------------------
    # Construction helpers
    # ---------------------------------------------------------------------
    @classmethod
    def from_files(
        cls, model_config_path: str, environment_config_path: str
    ) -> AppConfig:
        """Create :class:`AppConfig` from two YAML files.

        Parameters
        ----------
        model_config_path : str
            Path to *model*-level configuration (e.g. ``configs/model_config.yaml``).
        environment_config_path : str
            Path to environment/secret configuration (e.g. ``config.yaml``).
        """
        model_cfg = get_config(model_config_path)
        env_cfg = get_config(environment_config_path)

        # Get prompt template info from config
        prompt_template_name = ""
        prompt_template_version = None
        prompt_template = ""

        if "prompt_config" in model_cfg:
            prompt_template_name = model_cfg["prompt_config"].get("template_name", "")
            prompt_template_version = model_cfg["prompt_config"].get("version")

            # Load the prompt template if name is provided
            if prompt_template_name:
                try:
                    prompt_manager = PromptManager()
                    prompt_template = prompt_manager.get_template(
                        prompt_template_name, prompt_template_version
                    )
                except Exception as e:
                    print(f"Error loading prompt template: {e}")
        else:
            # Fallback to legacy template format
            prompt_template = model_cfg.get("template", "")

        return cls(
            embedding_model_name=model_cfg["models"]["embedding"],
            llm_model_name=model_cfg["models"]["llm"],
            data_folder=model_cfg["paths"]["data_folder"],
            file_names=model_cfg["paths"]["file_names"],
            faiss_index_path=model_cfg["paths"]["faiss_index"],
            retriever_search_type=model_cfg["retriever"]["search_type"],
            retriever_k_value=model_cfg["retriever"]["k_value"],
            openai_token=env_cfg["openai"]["token"],
            prompt_template=prompt_template,
            prompt_template_name=prompt_template_name,
            prompt_template_version=prompt_template_version,
        )

    # Convenience pretty-print ------------------------------------------------
    def __repr__(self) -> str:  # debug helper
        attrs = (
            "embedding_model_name",
            "llm_model_name",
            "data_folder",
            "file_names",
            "faiss_index_path",
            "retriever_search_type",
            "retriever_k_value",
            "openai_token",
            "prompt_template",
            "prompt_template_name",
            "prompt_template_version",
        )
        joined = ", ".join(f"{a}={getattr(self, a)!r}" for a in attrs)
        return f"{self.__class__.__name__}({joined})"
