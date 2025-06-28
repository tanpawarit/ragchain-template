from pathlib import Path
from typing import Any, Dict, Optional

import yaml

"""
Prompt Manager module for handling prompt versioning and loading.
"""


class PromptManager:
    """
    A class to manage prompt templates with versioning support.
    Loads prompt templates from YAML files in the templates directory.
    """

    def __init__(self, templates_dir: Optional[str] = None) -> None:
        """
        Initialize the PromptManager with a templates directory.

        Args:
            templates_dir: Path to templates directory. If None, uses default path.
        """
        if templates_dir is None:
            # Use the default templates directory relative to this file
            self.templates_dir = Path(__file__).parent / "templates"
        else:
            self.templates_dir = Path(templates_dir)

        # Dictionary to cache loaded templates
        self._templates_cache: Dict[str, Dict[str, Any]] = {}

    def get_template(self, template_name: str, version: Optional[str] = None) -> str:
        """
        Get a prompt template by name and optional version.

        Args:
            template_name: Base name of the template
            version: Version string (e.g., 'v1', 'v2'). If None, uses latest version.

        Returns:
            The prompt template string

        Raises:
            FileNotFoundError: If template file doesn't exist
            KeyError: If template key is not found in the file
        """
        # Determine template file path
        if version:
            template_file = f"{template_name}_{version}.yaml"
        else:
            # Find the latest version if not specified
            template_file = self._find_latest_version(template_name)

        # Load template from file if not in cache
        if template_file not in self._templates_cache:
            file_path = self.templates_dir / template_file
            if not file_path.exists():
                raise FileNotFoundError(f"Template file not found: {file_path}")

            with open(file_path, "r", encoding="utf-8") as f:
                self._templates_cache[template_file] = yaml.safe_load(f)

        # Extract template from loaded data
        template_data = self._templates_cache[template_file]
        if "template" not in template_data:
            raise KeyError(f"Template key not found in {template_file}")

        return template_data["template"]

    def list_available_templates(self) -> Dict[str, list]:
        """
        List all available templates and their versions.

        Returns:
            Dictionary mapping template names to lists of available versions
        """
        templates: Dict[str, list] = {}

        # Scan template directory for YAML files
        for file_path in self.templates_dir.glob("*.yaml"):
            filename = file_path.name
            # Parse template name and version from filename
            parts = filename.replace(".yaml", "").split("_")

            if len(parts) >= 2 and parts[-1].startswith("v"):
                # Template with version: name_v1.yaml
                template_name = "_".join(parts[:-1])
                version = parts[-1]

                if template_name not in templates:
                    templates[template_name] = []
                templates[template_name].append(version)
            else:
                # Template without version: name.yaml
                template_name = filename.replace(".yaml", "")
                if template_name not in templates:
                    templates[template_name] = ["default"]

        return templates

    def _find_latest_version(self, template_name: str) -> str:
        """
        Find the latest version of a template.

        Args:
            template_name: Base name of the template

        Returns:
            Filename of the latest version

        Raises:
            FileNotFoundError: If no matching template files are found
        """
        template_files = list(self.templates_dir.glob(f"{template_name}_v*.yaml"))

        if not template_files:
            # Try without version suffix
            template_file = self.templates_dir / f"{template_name}.yaml"
            if template_file.exists():
                return template_file.name
            raise FileNotFoundError(f"No template files found for {template_name}")

        # Sort by version number (assuming vX format where X is an integer)
        template_files.sort(key=lambda p: int(p.stem.split("_v")[-1]), reverse=True)
        return template_files[0].name

    def format_template(
        self, template_name: str, version: Optional[str] = None, **kwargs: Any
    ) -> str:
        """
        Get and format a template with the provided variables.

        Args:
            template_name: Name of the template
            version: Optional version string
            **kwargs: Variables to format the template with

        Returns:
            Formatted template string
        """
        template = self.get_template(template_name, version)
        return template.format(**kwargs)
