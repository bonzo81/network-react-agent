import pytest
from src.core.data_processor import process_connectivity_data  # You'll need to create this

def test_connectivity_data_processing():
    """Test processing of network connectivity data"""
    sample_data = {
        'results': [{
            'id': 1,
            'cable': {'id': 1},
            'device': {'name': 'switch-01'},
            'interface': {'name': 'eth0'},
            'site': {'name': 'Site A'}
        }]
    }
    
    processed = process_connectivity_data(sample_data)
    assert isinstance(processed, dict)
    assert 'devices' in processed
    assert 'connections' in processed

def test_data_validation():
    """Test validation of network data structures"""
    invalid_data = {'results': [{'id': 1}]}  # Missing required fields
    
    with pytest.raises(ValueError) as exc_info:
        process_connectivity_data(invalid_data)
    assert "Missing required fields" in str(exc_info.value)
