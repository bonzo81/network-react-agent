from typing import Any, Dict, List, Optional

from src.core.network_tool_adapter import NetworkToolAdapter
from network_agent.api.network_client import APIResponse, NetworkClient


class LibreNMSAdapter(NetworkToolAdapter):
    """Adapter for LibreNMS network monitoring system."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize LibreNMS adapter with configuration.

        Args:
            config: Configuration dictionary containing LibreNMS settings
        """
        self.config = config
        self.client = NetworkClient(
            base_url=config["api"]["url"],
            api_token=config["api"]["token"],
            timeout=config["api"].get("timeout", 30),
            verify_ssl=config["api"].get("verify_ssl", True),
        )
        # LibreNMS uses a different header for authentication
        self.client.session.headers.update({"X-Auth-Token": config["api"]["token"]})

    def get_devices(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve devices from LibreNMS.

        Args:
            filters: Optional filters to apply to the query

        Returns:
            List of standardized device data
        """
        response = self.client.query("devices", params=filters)
        if not response.success:
            return []

        devices = []
        for device in response.data.get("devices", []):
            devices.append(
                {
                    "name": device.get("hostname"),
                    "id": str(device.get("device_id")),
                    "status": "active" if device.get("status") == 1 else "inactive",
                    "model": device.get("hardware"),
                    "serial": device.get("serial"),
                    "site": device.get("location"),
                    "ip_address": device.get("ip"),
                }
            )
        return devices

    def get_interfaces(self, device_id: str) -> List[Dict[str, Any]]:
        """Retrieve interfaces for a specific device.

        Args:
            device_id: ID of the device to query

        Returns:
            List of standardized interface data
        """
        response = self.client.query(f"devices/{device_id}/ports")
        if not response.success:
            return []

        interfaces = []
        for interface in response.data.get("ports", []):
            interfaces.append(
                {
                    "name": interface.get("ifName"),
                    "type": interface.get("ifType"),
                    "enabled": interface.get("ifAdminStatus") == "up",
                    "mtu": interface.get("ifMtu"),
                    "mac_address": interface.get("ifPhysAddress"),
                    "description": interface.get("ifAlias"),
                    "speed": interface.get("ifSpeed"),
                    "stats": {
                        "in_bytes": interface.get("ifInOctets"),
                        "out_bytes": interface.get("ifOutOctets"),
                        "in_errors": interface.get("ifInErrors"),
                        "out_errors": interface.get("ifOutErrors"),
                    },
                }
            )
        return interfaces

    def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve alerts from LibreNMS.

        Args:
            severity: Optional severity level to filter alerts

        Returns:
            List of standardized alert data
        """
        params = {}
        if severity:
            severity_map = self.config["settings"]["alert_severity_mapping"]
            if severity in severity_map:
                params["severity"] = severity_map[severity]

        response = self.client.query("alerts", params=params)
        if not response.success:
            return []

        alerts = []
        for alert in response.data.get("alerts", []):
            alerts.append(
                {
                    "id": str(alert.get("id")),
                    "title": alert.get("rule_name"),
                    "severity": alert.get("severity"),
                    "status": alert.get("state"),
                    "created": alert.get("timestamp"),
                    "updated": alert.get("lastchange"),
                    "device_id": str(alert.get("device_id")),
                    "message": alert.get("msg"),
                }
            )
        return alerts

    def get_topology(self, root_device_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve network topology information.

        Args:
            root_device_id: Optional root device to start topology from

        Returns:
            Standardized topology data
        """
        # LibreNMS provides topology via LLDP/CDP neighbors
        params = {}
        if root_device_id:
            params["device_id"] = root_device_id

        response = self.client.query("links", params=params)
        if not response.success:
            return {"nodes": [], "links": []}

        topology = {"nodes": [], "links": []}

        # Process LLDP/CDP links
        for link in response.data.get("links", []):
            topology["links"].append(
                {
                    "source": str(link.get("local_device_id")),
                    "target": str(link.get("remote_device_id")),
                    "local_port": link.get("local_port_id"),
                    "remote_port": link.get("remote_port_id"),
                    "type": link.get("protocol", "unknown"),
                }
            )

        return topology

    def get_device_config(self, device_id: str) -> Dict[str, Any]:
        """Retrieve configuration for a specific device.

        Args:
            device_id: ID of the device to query

        Returns:
            Standardized device configuration data
        """
        # Check if Oxidized integration is enabled
        response = self.client.query(f"devices/{device_id}/oxidized")
        if not response.success:
            return {"message": "Device configuration not available"}

        return {
            "config": response.data.get("config", ""),
            "last_updated": response.data.get("last_update"),
            "status": response.data.get("status"),
        }

    def get_performance_metrics(
        self, device_id: str, metric_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve performance metrics for a device.

        Args:
            device_id: ID of the device to query
            metric_type: Optional type of metrics to retrieve

        Returns:
            List of standardized metric data
        """
        params = {"device_id": device_id}
        if metric_type:
            params["type"] = metric_type

        # Get both health metrics and port statistics
        health_response = self.client.query(f"devices/{device_id}/health")
        port_response = self.client.query(f"devices/{device_id}/ports")

        metrics = []

        # Process health metrics
        if health_response.success:
            for metric in health_response.data.get("health", []):
                metrics.append(
                    {
                        "type": "health",
                        "metric": metric.get("metric"),
                        "value": metric.get("value"),
                        "unit": metric.get("unit"),
                        "timestamp": metric.get("timestamp"),
                    }
                )

        # Process port statistics
        if port_response.success:
            for port in port_response.data.get("ports", []):
                metrics.append(
                    {
                        "type": "interface",
                        "interface": port.get("ifName"),
                        "metrics": {
                            "in_traffic": port.get("ifInOctets_rate"),
                            "out_traffic": port.get("ifOutOctets_rate"),
                            "errors": port.get("ifInErrors_rate"),
                            "utilization": port.get("ifOutOctets_perc"),
                        },
                    }
                )

        return metrics

    def search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Perform a search across LibreNMS data.

        Args:
            query: Search query string

        Returns:
            Dictionary of search results by category
        """
        # LibreNMS doesn't have a unified search endpoint, so we search in multiple areas
        results = {"devices": [], "ports": [], "alerts": []}

        # Search devices
        device_response = self.client.query("devices", params={"searchquery": query})
        if device_response.success:
            results["devices"] = device_response.data.get("devices", [])

        # Search ports (interfaces)
        port_response = self.client.query("ports", params={"searchquery": query})
        if port_response.success:
            results["ports"] = port_response.data.get("ports", [])

        # Search alerts
        alert_response = self.client.query("alerts", params={"searchquery": query})
        if alert_response.success:
            results["alerts"] = alert_response.data.get("alerts", [])

        return results

    def validate_connection(self) -> bool:
        """Validate the connection to LibreNMS.

        Returns:
            bool: True if connection is valid, False otherwise
        """
        return self.client.test_connection()
