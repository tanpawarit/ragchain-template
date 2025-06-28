from __future__ import annotations

import os
from typing import Any, Dict

import yaml

from src.utils.logger import get_logger

"""Thin wrapper around **YAML** to keep call-sites minimal and testable."""

logger = get_logger(__name__)

DEFAULT_CONFIG_PATH: str = os.path.join(os.getcwd(), "config.yaml")


def get_config(config_path: str | None = None) -> Dict[str, Any]:
    """Load and return configuration from a YAML file.

    Parameters
    ----------
    config_path: str | None, optional
        Path to the YAML configuration file.
        When None, defaults to "config.yaml" in the current working directory.

    Returns
    -------
    Dict[str, Any]
        Configuration values from the YAML file.

    Raises
    ------
    FileNotFoundError
        If the configuration file doesn't exist.
    yaml.YAMLError
        If the YAML file has invalid syntax.
    """
    # Use provided path or default
    cfg_path: str = config_path or DEFAULT_CONFIG_PATH

    # Check if file exists
    if not os.path.isfile(cfg_path):
        raise FileNotFoundError(f"Configuration file not found: {cfg_path}")

    logger.info(f"Loading configuration from {cfg_path}")

    # Load and return config
    with open(cfg_path, "r", encoding="utf-8") as fp:
        try:
            config: Dict[str, Any] = yaml.safe_load(fp) or {}
            return config
        except yaml.YAMLError as exc:
            logger.error(f"Failed to parse YAML configuration: {exc}")
            raise
