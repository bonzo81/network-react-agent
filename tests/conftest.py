# tests/conftest.py
import pytest
from src.api.network_client import NetworkClient
from src.core.agent import NetworkReActAgent

@pytest.fixture
def mock_api_responses():
    return {
        'cable_terminations': {
            'results': [{
                'id': 1,
                'cable': {'id': 1},
                'device': {'name': 'switch-01'},
                'interface': {'name': 'eth0'},
                'site': {'name': 'Site A'}
            }]
        },
        'interfaces': {
            'results': [{
                'id': 1,
                'name': 'eth0',
                'type': '1000base-t',
                'enabled': True
            }]
        }
    }

@pytest.fixture
def mock_network_client(mock_api_responses):
    class MockNetworkClient:
        def __init__(self, base_url, api_token):
            self.base_url = base_url
            self.api_token = api_token
            self.mock_responses = mock_api_responses

        def get(self, endpoint):
            if 'cable-terminations' in endpoint:
                return self.mock_responses['cable_terminations']
            elif 'interfaces' in endpoint:
                return self.mock_responses['interfaces']
            return {}

    return MockNetworkClient

@pytest.fixture
def semantic_mappings():
    return {
        'query_patterns': {
            'site_connectivity': {
                'keywords': ['connection', 'connected', 'link'],
                'optimal_endpoints': {
                    'primary': {
                        'system': 'netbox',
                        'endpoint': '/api/dcim/cable-terminations/',
                        'filters': {'termination_type': 'dcim.interface'},
                        'purpose': 'analyze_site_connections'
                    }
                }
            }
        }
    }

@pytest.fixture
def network_agent(mock_network_client, semantic_mappings):
    netbox = mock_network_client(
        base_url='http://netbox.test',
        api_token='test-token'
    )
    librenms = mock_network_client(
        base_url='http://librenms.test',
        api_token='test-token'
    )
    return NetworkReActAgent(netbox, librenms, semantic_mappings)
