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

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
