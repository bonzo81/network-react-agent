from pathlib import Path
from typing import Any, Dict

import yaml

from .env_handler import EnvHandler


class ConfigLoader:
    """Handles loading and validation of configuration files for network tools."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.main_config = None
        self.tool_configs = {}
        self.mapping_configs = {}

    def load_all(self) -> Dict[str, Any]:
        """Load and process all configuration files"""
        # Load main configuration
        self.main_config = self._load_yaml("main.yaml")

        # Check if environment variable substitution is enabled
        enable_env_vars = self.main_config.get("security", {}).get(
            "enable_env_vars", False
        )

        # Load tool-specific configurations
        for tool, tool_config in self.main_config.get("tools", {}).items():
            if tool_config.get("enabled", False):
                config_file = tool_config.get("config_file")
                if config_file:
                    self.tool_configs[tool] = self._load_yaml(config_file)

                mapping_file = tool_config.get("mappings_file")
                if mapping_file:
                    self.mapping_configs[tool] = self._load_yaml(mapping_file)

        # Apply environment variable substitution if enabled
        if enable_env_vars:
            try:
                # Validate all required environment variables are present
                EnvHandler.validate_required_env_vars(self.tool_configs)

                # Substitute environment variables
                self.tool_configs = EnvHandler.substitute_env_vars(self.tool_configs)
            except ValueError as e:
                raise ConfigurationError(f"Environment variable error: {str(e)}")

        return {
            "main": self.main_config,
            "tools": self.tool_configs,
            "mappings": self.mapping_configs,
        }

    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load and parse a YAML file"""
        full_path = self.config_dir / file_path
        try:
            with open(full_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationError(f"Error loading {full_path}: {str(e)}")


class ConfigurationError(Exception):
    """Raised when there is an error in configuration loading or processing."""

    pass
