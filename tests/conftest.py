import pytest
from src.api.network_client import NetworkClient
from src.core.agent import NetworkReActAgent

@pytest.fixture
def netbox_client():
    return NetworkClient(
        base_url='http://netbox.test',
        api_token='test-token'
    )

@pytest.fixture
def librenms_client():
    return NetworkClient(
        base_url='http://librenms.test',
        api_token='test-token'
    )

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
def network_agent(netbox_client, librenms_client, semantic_mappings):
    return NetworkReActAgent(netbox_client, librenms_client, semantic_mappings)