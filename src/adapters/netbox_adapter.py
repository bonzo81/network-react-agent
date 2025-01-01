from typing import Dict, List, Optional, Any
from ..core.network_tool_adapter import NetworkToolAdapter
from ..network_agent.api.network_client import NetworkClient, APIResponse

class NetboxAdapter(NetworkToolAdapter):
    """Adapter for NetBox network management system."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize NetBox adapter with configuration.

        Args:
            config: Configuration dictionary containing NetBox settings
        """
        self.config = config
        self.client = NetworkClient(
            base_url=config['api']['url'],
            api_token=config['api']['token'],
            timeout=config['api'].get('timeout', 30),
            verify_ssl=config['api'].get('verify_ssl', True)
        )

    def get_devices(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve devices from NetBox.

        Args:
            filters: Optional filters to apply to the query

        Returns:
            List of standardized device data
        """
        response = self.client.query('api/dcim/devices/', params=filters)
        if not response.success:
            return []

        # Transform to standard format using mappings
        devices = []
        for device in response.data.get('results', []):
            devices.append({
                'name': device.get('name'),
                'id': str(device.get('id')),
                'status': device.get('status', {}).get('value'),
                'model': device.get('device_type', {}).get('model'),
                'serial': device.get('serial'),
                'site': device.get('site', {}).get('name'),
                'rack': device.get('rack', {}).get('name'),
                'position': device.get('position'),
                'primary_ip': device.get('primary_ip4', {}).get('address')
            })
        return devices

    def get_interfaces(self, device_id: str) -> List[Dict[str, Any]]:
        """Retrieve interfaces for a specific device.

        Args:
            device_id: ID of the device to query

        Returns:
            List of standardized interface data
        """
        response = self.client.query(f'api/dcim/interfaces/', params={'device_id': device_id})
        if not response.success:
            return []

        interfaces = []
        for interface in response.data.get('results', []):
            interfaces.append({
                'name': interface.get('name'),
                'type': interface.get('type', {}).get('value'),
                'enabled': interface.get('enabled'),
                'mtu': interface.get('mtu'),
                'mac_address': interface.get('mac_address'),
                'description': interface.get('description')
            })
        return interfaces

    def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve alerts from NetBox.

        Args:
            severity: Optional severity level to filter alerts

        Returns:
            List of standardized alert data
        """
        params = {}
        if severity:
            params['priority'] = severity

        response = self.client.query('api/extras/events/', params=params)
        if not response.success:
            return []

        alerts = []
        for alert in response.data.get('results', []):
            alerts.append({
                'id': str(alert.get('id')),
                'title': alert.get('name'),
                'severity': alert.get('priority', {}).get('label'),
                'status': alert.get('status', {}).get('value'),
                'created': alert.get('created'),
                'updated': alert.get('last_updated')
            })
        return alerts

    def get_topology(self, root_device_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve network topology information.

        Args:
            root_device_id: Optional root device to start topology from

        Returns:
            Standardized topology data
        """
        # Implementation depends on how topology data is stored in NetBox
        # This is a basic implementation that might need enhancement
        params = {}
        if root_device_id:
            params['device_id'] = root_device_id

        response = self.client.query('api/dcim/cables/', params=params)
        if not response.success:
            return {'nodes': [], 'links': []}

        # Transform to topology format
        topology = {
            'nodes': [],
            'links': []
        }

        # Process cable connections
        for cable in response.data.get('results', []):
            if cable.get('termination_a_type') == 'dcim.interface' and \
               cable.get('termination_b_type') == 'dcim.interface':
                topology['links'].append({
                    'source': str(cable.get('termination_a')),
                    'target': str(cable.get('termination_b')),
                    'type': 'cable'
                })

        return topology

    def get_device_config(self, device_id: str) -> Dict[str, Any]:
        """Retrieve configuration for a specific device.

        Args:
            device_id: ID of the device to query

        Returns:
            Standardized device configuration data
        """
        # NetBox might not store device configurations directly
        # This is a placeholder that might need to be integrated with other systems
        return {'message': 'Device configuration not available in NetBox'}

    def get_performance_metrics(self, device_id: str, metric_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve performance metrics for a device.

        Args:
            device_id: ID of the device to query
            metric_type: Optional type of metrics to retrieve

        Returns:
            List of standardized metric data
        """
        # NetBox doesn't typically store performance metrics
        # This is a placeholder that might need to be integrated with other systems
        return []

    def search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Perform a search across NetBox data.

        Args:
            query: Search query string

        Returns:
            Dictionary of search results by category
        """
        response = self.client.query('api/extras/search/', params={'q': query})
        if not response.success:
            return {}

        results = {
            'devices': [],
            'interfaces': [],
            'racks': [],
            'sites': []
        }

        # Process results by object type
        for item in response.data.get('results', []):
            obj_type = item.get('object_type')
            if obj_type == 'dcim.device':
                results['devices'].append(item)
            elif obj_type == 'dcim.interface':
                results['interfaces'].append(item)
            elif obj_type == 'dcim.rack':
                results['racks'].append(item)
            elif obj_type == 'dcim.site':
                results['sites'].append(item)

        return results

    def validate_connection(self) -> bool:
        """Validate the connection to NetBox.

        Returns:
            bool: True if connection is valid, False otherwise
        """
        return self.client.test_connection()