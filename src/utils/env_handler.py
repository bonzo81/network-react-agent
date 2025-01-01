import os
from typing import Any, Dict, Union
import re

class EnvHandler:
    """Handle environment variable substitution in configuration files."""

    ENV_VAR_PATTERN = re.compile(r'\${([^}]+)}') # Matches ${VAR_NAME} pattern
    
    @classmethod
    def substitute_env_vars(cls, config: Union[Dict, str]) -> Union[Dict, str]:
        """Recursively substitute environment variables in configuration.

        Args:
            config: Configuration dictionary or string

        Returns:
            Configuration with environment variables substituted
        """
        if isinstance(config, dict):
            return {k: cls.substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, str):
            return cls._replace_env_vars(config)
        return config

    @classmethod
    def _replace_env_vars(cls, value: str) -> str:
        """Replace environment variables in a string.

        Args:
            value: String potentially containing environment variables

        Returns:
            String with environment variables substituted
        """
        def replace_var(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            if env_value is None:
                raise ValueError(f"Environment variable '{var_name}' not found")
            return env_value

        try:
            return cls.ENV_VAR_PATTERN.sub(replace_var, value)
        except ValueError as e:
            raise ValueError(f"Error substituting environment variables: {str(e)}")

    @classmethod
    def validate_required_env_vars(cls, config: Dict[str, Any]) -> None:
        """Validate that all required environment variables are present.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValueError: If any required environment variable is missing
        """
        missing_vars = set()
        
        def check_value(value):
            if isinstance(value, str):
                matches = cls.ENV_VAR_PATTERN.findall(value)
                for var_name in matches:
                    if os.getenv(var_name) is None:
                        missing_vars.add(var_name)
            elif isinstance(value, dict):
                for v in value.values():
                    check_value(v)

        check_value(config)
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )