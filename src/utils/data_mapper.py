from typing import Dict, Any, Optional
from pathlib import Path

class DataMapper:
    """Utility class for mapping data between different network tools and standard format."""

    def __init__(self, mapping_config: Dict[str, Any]):
        """Initialize the data mapper with mapping configurations.

        Args:
            mapping_config: Dictionary containing field mappings for different tools
        """
        self.mappings = mapping_config

    def map_device_data(self, tool_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map device data from tool-specific format to standard format.

        Args:
            tool_name: Name of the network tool
            data: Raw device data from the tool

        Returns:
            Standardized device data
        """
        if tool_name not in self.mappings:
            return data

        device_mappings = self.mappings[tool_name].get('device', {}).get('standard_fields', {})
        return self._apply_mapping(data, device_mappings)

    def map_interface_data(self, tool_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map interface data from tool-specific format to standard format.

        Args:
            tool_name: Name of the network tool
            data: Raw interface data from the tool

        Returns:
            Standardized interface data
        """
        if tool_name not in self.mappings:
            return data

        interface_mappings = self.mappings[tool_name].get('interface', {}).get('standard_fields', {})
        return self._apply_mapping(data, interface_mappings)

    def map_alert_data(self, tool_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map alert data from tool-specific format to standard format.

        Args:
            tool_name: Name of the network tool
            data: Raw alert data from the tool

        Returns:
            Standardized alert data
        """
        if tool_name not in self.mappings:
            return data

        alert_mappings = self.mappings[tool_name].get('alert', {}).get('standard_fields', {})
        return self._apply_mapping(data, alert_mappings)

    def _apply_mapping(self, data: Dict[str, Any], field_mappings: Dict[str, str]) -> Dict[str, Any]:
        """Apply field mappings to data.

        Args:
            data: Raw data to map
            field_mappings: Dictionary of field mappings

        Returns:
            Mapped data
        """
        result = {}
        for standard_field, source_field in field_mappings.items():
            # Handle nested fields with dot notation
            value = self._get_nested_value(data, source_field)
            if value is not None:
                result[standard_field] = value

        return result

    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Optional[Any]:
        """Get value from nested dictionary using dot notation.

        Args:
            data: Dictionary to extract value from
            field_path: Path to the value using dot notation

        Returns:
            Value if found, None otherwise
        """
        current = data
        for part in field_path.split('.'):
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current