import yaml
from typing import Dict, Any
from pathlib import Path

class ConfigLoader:
    """
    Handles loading and validation of configuration files for network tools.
    """

    def __init__(self, config_dir: str = 'config'):
        self.config_dir = Path(config_dir)
        self.main_config = None
        self.tool_configs = {}
        self.mapping_configs = {}

    def load_all(self) -> Dict[str, Any]:
        """Load all configuration files"""
        self.main_config = self._load_yaml(self.config_dir / 'main.yaml')
        
        # Load tool configs
        tools_dir = self.config_dir / 'tools'
        for tool_file in tools_dir.glob('*.yaml'):
            tool_name = tool_file.stem
            self.tool_configs[tool_name] = self._load_yaml(tool_file)

        # Load mapping configs
        mappings_dir = self.config_dir / 'mappings'
        for mapping_file in mappings_dir.glob('*.yaml'):
            tool_name = mapping_file.stem.replace('_mappings', '')
            self.mapping_configs[tool_name] = self._load_yaml(mapping_file)

        return {
            'main': self.main_config,
            'tools': self.tool_configs,
            'mappings': self.mapping_configs
        }

    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a YAML file"""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f'Error loading {file_path}: {str(e)}')