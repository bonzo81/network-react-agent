import pytest
from src.core.agent import NetworkReActAgent

def test_site_connectivity_query(network_agent, requests_mock):
    # Mock NetBox API response
    requests_mock.get(
        'http://netbox.test/api/dcim/cable-terminations/',
        json={
            'connections': [
                {
                    'site_a': {'name': 'Site A'},
                    'site_b': {'name': 'Site B'},
                    'device': 'switch-01'
                }
            ]
        }
    )
    
    response = network_agent.process_query(
        'Show me connections between sites'
    )
    
    assert 'Found 1 inter-site connections' in response
    assert 'Site A and Site B' in response