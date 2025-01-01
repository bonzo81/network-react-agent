from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class NetworkToolAdapter(ABC):
    """
    Abstract base class for network tool adapters.
    Defines the interface that all network tool implementations must follow.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the adapter with configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary for the tool
        """
        pass

    @abstractmethod
    def get_devices(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve devices from the network tool.
        
        Args:
            filters (Optional[Dict[str, Any]]): Optional filters to apply to the query
            
        Returns:
            List[Dict[str, Any]]: List of standardized device data
        """
        pass

    @abstractmethod
    def get_interfaces(self, device_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve interfaces for a specific device.
        
        Args:
            device_id (str): ID of the device to query
            
        Returns:
            List[Dict[str, Any]]: List of standardized interface data
        """
        pass

    @abstractmethod
    def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve alerts from the network tool.
        
        Args:
            severity (Optional[str]): Optional severity level to filter alerts
            
        Returns:
            List[Dict[str, Any]]: List of standardized alert data
        """
        pass

    @abstractmethod
    def get_topology(self, root_device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve network topology information.
        
        Args:
            root_device_id (Optional[str]): Optional root device to start topology from
            
        Returns:
            Dict[str, Any]: Standardized topology data
        """
        pass

    @abstractmethod
    def get_device_config(self, device_id: str) -> Dict[str, Any]:
        """
        Retrieve configuration for a specific device.
        
        Args:
            device_id (str): ID of the device to query
            
        Returns:
            Dict[str, Any]: Standardized device configuration data
        """
        pass

    @abstractmethod
    def get_performance_metrics(self, device_id: str, metric_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve performance metrics for a device.
        
        Args:
            device_id (str): ID of the device to query
            metric_type (Optional[str]): Optional type of metrics to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of standardized metric data
        """
        pass

    @abstractmethod
    def search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform a search across the tool's data.
        
        Args:
            query (str): Search query string
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionary of search results by category
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate the connection to the network tool.
        
        Returns:
            bool: True if connection is valid, False otherwise
        """
        pass