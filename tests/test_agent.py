# tests/test_agent.py
import pytest
from src.core.agent import NetworkReActAgent

def test_pattern_matching(network_agent):
    """Test keyword-based pattern matching without LLM"""
    test_cases = [
        ("Show me connections between sites", "site_connectivity"),
        ("Check the link status", "site_connectivity"),
        ("Display all connected interfaces", "site_connectivity")
    ]
    
    for query, expected in test_cases:
        pattern = network_agent.planner._match_pattern(query)
        assert pattern == expected

def test_semantic_mapping_validation(semantic_mappings):
    """Test the structure of semantic mappings"""
    assert 'query_patterns' in semantic_mappings
    assert 'site_connectivity' in semantic_mappings['query_patterns']
    pattern = semantic_mappings['query_patterns']['site_connectivity']
    assert 'keywords' in pattern
    assert 'optimal_endpoints' in pattern

def test_network_client_interface(mock_network_client):
    """Test NetworkClient interface methods"""
    client = mock_network_client(
        base_url='http://test.com',
        api_token='test-token'
    )
    assert client.base_url == 'http://test.com'
    assert client.api_token == 'test-token'
    
    # Test mock response
    response = client.get('/api/dcim/cable-terminations/')
    assert 'results' in response
    assert len(response['results']) > 0
