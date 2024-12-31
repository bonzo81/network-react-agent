import pytest
from src.core.agent import NetworkReActAgent
from src.api.network_client import NetworkClient

def test_netbox_client_initialization():
    """Test NetworkClient initialization with NetBox"""
    client = NetworkClient(
        base_url="http://netbox.test",
        api_token="test-token"
    )
    assert client.base_url == "http://netbox.test"
    assert client.api_token == "test-token"

def test_agent_query_execution(network_agent, requests_mock):
    """Test agent executing a simple query"""
    # Mock NetBox cable-terminations endpoint
    requests_mock.get(
        "http://netbox.test/api/dcim/cable-terminations/",
        json={
            "count": 1,
            "results": [{
                "id": 1,
                "cable": {"id": 1},
                "device": {"name": "switch-01"},
                "interface": {"name": "eth0"},
                "site": {"name": "Site A"}
            }]
        }
    )
    
    # Mock LibreNMS metrics endpoint
    requests_mock.get(
        "http://librenms.test/api/v0/ports/switch-01/eth0",
        json={
            "status": "up",
            "in_rate": 1000000,
            "out_rate": 500000
        }
    )
    
    response = network_agent.process_query(
        "Show me the status of connections from Site A"
    )
    
    assert "Site A" in response
    assert "switch-01" in response

def test_error_handling(network_agent, requests_mock):
    """Test agent handling API errors"""
    # Mock failed API call
    requests_mock.get(
        "http://netbox.test/api/dcim/cable-terminations/",
        status_code=500,
        text="Internal Server Error"
    )
    
    with pytest.raises(Exception) as exc_info:
        network_agent.process_query("Show me connections")
    
    assert "Error" in str(exc_info.value)

def test_query_planning(network_agent):
    """Test query planning logic"""
    query = "Show me high bandwidth connections between sites"
    plan = network_agent.planner.create_plan(query)
    
    assert len(plan) > 0
    assert plan[0].endpoint == "/api/dcim/cable-terminations/"
    assert "site" in plan[0].filters

@pytest.mark.parametrize("query,expected_pattern", [
    ("Show me connections between sites", "site_connectivity"),
    ("List all links from Site A", "site_connectivity"),
    ("Display bandwidth usage", "performance_monitoring")
])
def test_pattern_matching(network_agent, query, expected_pattern):
    """Test pattern matching for different queries"""
    pattern = network_agent.planner._match_pattern(query)
    assert pattern == expected_pattern

def test_llm_integration(network_agent, mocker):
    """Test LLM integration"""
    # Mock LLM response
    mock_llm = mocker.patch.object(network_agent, 'llm')
    mock_llm.predict.return_value = "Thought: I should check cable terminations"
    
    response = network_agent.process_query(
        "Are there any connectivity issues between sites?"
    )
    
    assert mock_llm.predict.called
    assert isinstance(response, str)

def test_complex_query_workflow(network_agent, requests_mock):
    """Test handling of complex queries requiring multiple API calls"""
    # Mock NetBox endpoints
    requests_mock.get(
        "http://netbox.test/api/dcim/cable-terminations/",
        json={"results": [{
            "id": 1,
            "cable": {"id": 1},
            "device": {"name": "switch-01"},
            "interface": {"name": "eth0"},
            "site": {"name": "Site A"}
        }]}
    )
    
    requests_mock.get(
        "http://netbox.test/api/dcim/interfaces/",
        json={"results": [{
            "id": 1,
            "name": "eth0",
            "type": "1000base-t",
            "enabled": True
        }]}
    )
    
    # Mock LibreNMS endpoints
    requests_mock.get(
        "http://librenms.test/api/v0/devices/switch-01/metrics",
        json={
            "status": "ok",
            "metrics": {
                "cpu": 45,
                "memory": 60
            }
        }
    )
    
    response = network_agent.process_query(
        "Check if Site A has any high-bandwidth connections with performance issues"
    )
    
    assert "Site A" in response
    assert "switch-01" in response
    assert "bandwidth" in response.lower() or "performance" in response.lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])