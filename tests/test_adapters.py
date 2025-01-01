import pytest
from unittest.mock import Mock, patch
from src.adapters.netbox_adapter import NetboxAdapter
from src.adapters.librenms_adapter import LibreNMSAdapter
from src.network_agent.api.network_client import APIResponse
from .fixtures.netbox_responses import DEVICE_RESPONSE as NETBOX_DEVICE_RESPONSE
from .fixtures.librenms_responses import DEVICE_RESPONSE as LIBRENMS_DEVICE_RESPONSE

@pytest.fixture
def netbox_config():
    return {
        'api': {
            'url': 'http://netbox.example.com',
            'token': 'test-token',
            'timeout': 30,
            'verify_ssl': True
        }
    }

@pytest.fixture
def librenms_config():
    return {
        'api': {
            'url': 'http://librenms.example.com',
            'token': 'test-token',
            'timeout': 30,
            'verify_ssl': True
        },
        'settings': {
            'alert_severity_mapping': {
                'critical': 5,
                'warning': 4,
                'info': 3
            }
        }
    }

class TestNetboxAdapter:
    def test_get_devices(self, netbox_config):
        with patch('src.network_agent.api.network_client.NetworkClient') as mock_client:
            # Setup mock response
            mock_client.return_value.query.return_value = APIResponse(
                success=True,
                data=NETBOX_DEVICE_RESPONSE,
                status_code=200
            )

            adapter = NetboxAdapter(netbox_config)
            devices = adapter.get_devices()

            assert len(devices) == 1
            device = devices[0]
            assert device['name'] == 'test-device-01'
            assert device['status'] == 'active'
            assert device['model'] == 'Cisco Catalyst 3750'

    def test_get_devices_failed_response(self, netbox_config):
        with patch('src.network_agent.api.network_client.NetworkClient') as mock_client:
            mock_client.return_value.query.return_value = APIResponse(
                success=False,
                error='API Error',
                status_code=500
            )

            adapter = NetboxAdapter(netbox_config)
            devices = adapter.get_devices()

            assert len(devices) == 0

class TestLibreNMSAdapter:
    def test_get_devices(self, librenms_config):
        with patch('src.network_agent.api.network_client.NetworkClient') as mock_client:
            mock_client.return_value.query.return_value = APIResponse(
                success=True,
                data=LIBRENMS_DEVICE_RESPONSE,
                status_code=200
            )

            adapter = LibreNMSAdapter(librenms_config)
            devices = adapter.get_devices()

            assert len(devices) == 1
            device = devices[0]
            assert device['name'] == 'test-device-01'
            assert device['status'] == 'active'
            assert device['model'] == 'Cisco Catalyst 3750'

    def test_get_devices_failed_response(self, librenms_config):
        with patch('src.network_agent.api.network_client.NetworkClient') as mock_client:
            mock_client.return_value.query.return_value = APIResponse(
                success=False,
                error='API Error',
                status_code=500
            )

            adapter = LibreNMSAdapter(librenms_config)
            devices = adapter.get_devices()

            assert len(devices) == 0