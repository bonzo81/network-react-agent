import pytest
import os
from src.utils.env_handler import EnvHandler

@pytest.fixture
def setup_env_vars():
    # Setup test environment variables
    os.environ['TEST_API_URL'] = 'http://test.example.com'
    os.environ['TEST_API_TOKEN'] = 'test-token-123'
    yield
    # Cleanup
    del os.environ['TEST_API_URL']
    del os.environ['TEST_API_TOKEN']

class TestEnvHandler:
    def test_simple_substitution(self, setup_env_vars):
        config = {
            'api': {
                'url': '${TEST_API_URL}',
                'token': '${TEST_API_TOKEN}'
            }
        }
        
        result = EnvHandler.substitute_env_vars(config)
        
        assert result['api']['url'] == 'http://test.example.com'
        assert result['api']['token'] == 'test-token-123'

    def test_missing_env_var(self):
        config = {'api_key': '${NONEXISTENT_VAR}'}
        
        with pytest.raises(ValueError) as exc_info:
            EnvHandler.substitute_env_vars(config)
        
        assert 'NONEXISTENT_VAR' in str(exc_info.value)

    def test_partial_substitution(self, setup_env_vars):
        config = {
            'url': 'prefix-${TEST_API_URL}/suffix',
            'static': 'no-substitution-needed'
        }
        
        result = EnvHandler.substitute_env_vars(config)
        
        assert result['url'] == 'prefix-http://test.example.com/suffix'
        assert result['static'] == 'no-substitution-needed'

    def test_validation(self, setup_env_vars):
        config = {
            'present': '${TEST_API_URL}',
            'missing': '${MISSING_VAR}'
        }
        
        with pytest.raises(ValueError) as exc_info:
            EnvHandler.validate_required_env_vars(config)
        
        assert 'MISSING_VAR' in str(exc_info.value)
        assert 'TEST_API_URL' not in str(exc_info.value)