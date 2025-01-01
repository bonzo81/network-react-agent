import pytest
from unittest.mock import Mock, patch
from src.network_agent.core.tool_manager import ToolManager, ToolInitializationError
from src.core.network_tool_adapter import NetworkToolAdapter
from .fixtures.tool_configs import MAIN_CONFIG, NETBOX_CONFIG, LIBRENMS_CONFIG

# Mock adapters for testing
class MockNetboxAdapter(NetworkToolAdapter):
    def __init__(self, config):
        self.config = config

    def validate_connection(self):
        return True

    def get_devices(self, filters=None):
        return [{"name": "test-device", "status": "active"}]

    def get_interfaces(self, device_id):
        return [{"name": "eth0", "status": "up"}]

class MockLibreNMSAdapter(NetworkToolAdapter):
    def __init__(self, config):
        self.config = config

    def validate_connection(self):
        return True

    def get_devices(self, filters=None):
        return [{"hostname": "test-device", "status": 1}]

    def get_alerts(self, severity=None):
        return [{"title": "Test Alert", "severity": "critical"}]

# Test fixtures
@pytest.fixture
def mock_config_loader():
    with patch('src.utils.config_loader.ConfigLoader') as mock:
        mock.return_value.load_all.return_value = {
            'main': MAIN_CONFIG,
            'tools': {
                'netbox': NETBOX_CONFIG,
                'librenms': LIBRENMS_CONFIG
            }
        }
        yield mock

@pytest.fixture
def tool_manager(mock_config_loader):
    manager = ToolManager(config_dir='test_config')
    manager.TOOL_REGISTRY = {
        'netbox': MockNetboxAdapter,
        'librenms': MockLibreNMSAdapter
    }
    return manager

class TestToolManager:
    def test_initialization(self, tool_manager):
        assert len(tool_manager.tools) == 2
        assert 'netbox' in tool_manager.tools
        assert 'librenms' in tool_manager.tools

    def test_aliases(self, tool_manager):
        assert tool_manager.aliases['nx'] == 'netbox'
        assert tool_manager.aliases['lnms'] == 'librenms'

    def test_get_tool_by_name(self, tool_manager):
        tool = tool_manager.get_tool('netbox')
        assert isinstance(tool, MockNetboxAdapter)

    def test_get_tool_by_alias(self, tool_manager):
        tool = tool_manager.get_tool('nx')
        assert isinstance(tool, MockNetboxAdapter)

    def test_get_nonexistent_tool(self, tool_manager):
        tool = tool_manager.get_tool('nonexistent')
        assert tool is None

    def test_select_tool(self, tool_manager):
        assert tool_manager.select_tool('netbox')
        assert tool_manager.active_tool == 'netbox'

    def test_select_tool_by_alias(self, tool_manager):
        assert tool_manager.select_tool('nx')
        assert tool_manager.active_tool == 'netbox'

    def test_clear_tool_selection(self, tool_manager):
        tool_manager.select_tool('netbox')
        assert tool_manager.select_tool(None)
        assert tool_manager.active_tool is None

    def test_get_all_tools(self, tool_manager):
        tools = tool_manager.get_all_tools()
        assert len(tools) == 2
        assert all(isinstance(tool, NetworkToolAdapter) for tool in tools)

    def test_execute_query_specific_tool(self, tool_manager):
        results = tool_manager.execute_query('netbox', 'get_devices')
        assert 'netbox' in results
        assert results['netbox'][0]['name'] == 'test-device'

    def test_execute_query_all_tools(self, tool_manager):
        results = tool_manager.execute_query(None, 'get_devices')
        assert len(results) == 2
        assert 'netbox' in results
        assert 'librenms' in results

    def test_execute_query_nonexistent_method(self, tool_manager):
        results = tool_manager.execute_query('netbox', 'nonexistent_method')
        assert 'error' in results['netbox']

    def test_execute_query_with_error(self, tool_manager):
        with patch.object(MockNetboxAdapter, 'get_devices', side_effect=Exception('Test error')):
            results = tool_manager.execute_query('netbox', 'get_devices')
            assert 'error' in results['netbox']

    def test_register_new_tool(self, tool_manager):
        class NewToolAdapter(NetworkToolAdapter):
            def __init__(self, config):
                self.config = config
            def validate_connection(self):
                return True

        config = {'api': {'url': 'http://test', 'token': 'test'}}
        assert tool_manager.register_tool('new_tool', NewToolAdapter, config, ['nt'])
        assert 'new_tool' in tool_manager.tools
        assert tool_manager.aliases['nt'] == 'new_tool'

    def test_register_tool_with_validation_failure(self, tool_manager):
        class FailingAdapter(NetworkToolAdapter):
            def __init__(self, config):
                self.config = config
            def validate_connection(self):
                return False

        config = {'api': {'url': 'http://test', 'token': 'test'}}
        assert not tool_manager.register_tool('failing', FailingAdapter, config)
        assert 'failing' not in tool_manager.tools

    def test_tool_initialization_error(self, mock_config_loader):
        mock_config_loader.return_value.load_all.side_effect = Exception('Config error')
        with pytest.raises(ToolInitializationError):
            ToolManager(config_dir='test_config')

    def test_method_execution_across_tools(self, tool_manager):
        # Test that methods specific to certain tools work correctly
        netbox_results = tool_manager.execute_query('netbox', 'get_interfaces', 'test-device')
        assert 'netbox' in netbox_results
        assert netbox_results['netbox'][0]['name'] == 'eth0'

        librenms_results = tool_manager.execute_query('librenms', 'get_alerts')
        assert 'librenms' in librenms_results
        assert librenms_results['librenms'][0]['severity'] == 'critical'