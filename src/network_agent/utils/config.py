from typing import Dict, Any, Optional
import os
import yaml
from dotenv import load_dotenv
import logging

class ConfigurationError(Exception):
    """Raised when there's an error loading configuration"""
    pass

class Configuration:
    """Configuration handler that supports both env vars and YAML
    
    Priority order:
    1. Environment variables
    2. .env file
    3. YAML config file
    4. Default values
    """
    
    # Environment variable mappings
    ENV_MAPPINGS = {
        "NETBOX_URL": "netbox.base_url",
        "NETBOX_TOKEN": "netbox.api_token",
        "NETBOX_TIMEOUT": "netbox.timeout",
        "LIBRENMS_URL": "librenms.base_url",
        "LIBRENMS_TOKEN": "librenms.api_token",
        "LIBRENMS_TIMEOUT": "librenms.timeout",
        "OPENAI_API_KEY": "llm.api_key",
        "OPENAI_API_BASE": "llm.api_base",
        "LLM_MODEL": "llm.model",
        "LLM_TEMPERATURE": "llm.temperature"
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger("Configuration")
        self.config: Dict[str, Any] = {}
        
        # Load configuration in order
        self._load_defaults()
        if config_path:
            self._load_yaml(config_path)
        self._load_env()
    
    def _load_defaults(self):
        """Load default configuration values"""
        self.config = {
            "netbox": {
                "timeout": 30,
                "verify_ssl": True
            },
            "librenms": {
                "timeout": 30,
                "verify_ssl": True
            },
            "llm": {
                "model": "gpt-4",
                "temperature": 0
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    
    def _load_yaml(self, config_path: str):
        """Load configuration from YAML file"""
        try:
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f)
                self._update_nested(self.config, yaml_config)
                self.logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            self.logger.warning(f"Could not load YAML config: {e}")
    
    def _load_env(self):
        """Load configuration from environment variables"""
        # Load .env file if it exists
        load_dotenv(override=True)
        
        # Update config from environment variables
        for env_var, config_path in self.ENV_MAPPINGS.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_value(config_path, value)
    
    def _update_nested(self, target: Dict, source: Dict):
        """Update nested dictionary with another dictionary"""
        for key, value in source.items():
            if isinstance(value, dict):
                target.setdefault(key, {})
                self._update_nested(target[key], value)
            else:
                target[key] = value
    
    def _set_nested_value(self, path: str, value: Any):
        """Set value in nested dictionary using dot notation path"""
        current = self.config
        *parts, final = path.split('.')
        
        for part in parts:
            current = current.setdefault(part, {})
        
        # Convert value to appropriate type
        if isinstance(current.get(final), bool):
            current[final] = value.lower() in ('true', '1', 'yes')
        elif isinstance(current.get(final), int):
            try:
                current[final] = int(value)
            except ValueError:
                self.logger.warning(f"Could not convert {value} to int for {path}")
        elif isinstance(current.get(final), float):
            try:
                current[final] = float(value)
            except ValueError:
                self.logger.warning(f"Could not convert {value} to float for {path}")
        else:
            current[final] = value
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation path"""
        try:
            current = self.config
            for part in path.split('.'):
                current = current[part]
            return current
        except KeyError:
            return default
    
    @property
    def netbox_config(self) -> Dict[str, Any]:
        """Get NetBox configuration"""
        return self.config.get('netbox', {})
    
    @property
    def librenms_config(self) -> Dict[str, Any]:
        """Get LibreNMS configuration"""
        return self.config.get('librenms', {})
    
    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self.config.get('llm', {})