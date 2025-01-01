import pytest
from src.utils.data_mapper import DataMapper

@pytest.fixture
def sample_mappings():
    return {
        'netbox': {
            'device': {
                'standard_fields': {
                    'name': 'name',
                    'status': 'status.value',
                    'model': 'device_type.model'
                }
            },
            'interface': {
                'standard_fields': {
                    'name': 'name',
                    'type': 'type.value',
                    'enabled': 'enabled'
                }
            }
        },
        'librenms': {
            'device': {
                'standard_fields': {
                    'name': 'hostname',
                    'status': 'status',
                    'model': 'hardware'
                }
            },
            'interface': {
                'standard_fields': {
                    'name': 'ifName',
                    'type': 'ifType',
                    'enabled': 'ifAdminStatus'
                }
            }
        }
    }

class TestDataMapper:
    def test_map_device_data_netbox(self, sample_mappings):
        mapper = DataMapper(sample_mappings)
        raw_data = {
            'name': 'test-device',
            'status': {'value': 'active'},
            'device_type': {'model': 'Cisco 3750'}
        }

        mapped_data = mapper.map_device_data('netbox', raw_data)

        assert mapped_data['name'] == 'test-device'
        assert mapped_data['status'] == 'active'
        assert mapped_data['model'] == 'Cisco 3750'

    def test_map_device_data_librenms(self, sample_mappings):
        mapper = DataMapper(sample_mappings)
        raw_data = {
            'hostname': 'test-device',
            'status': 1,
            'hardware': 'Cisco 3750'
        }

        mapped_data = mapper.map_device_data('librenms', raw_data)

        assert mapped_data['name'] == 'test-device'
        assert mapped_data['status'] == 1
        assert mapped_data['model'] == 'Cisco 3750'

    def test_map_interface_data(self, sample_mappings):
        mapper = DataMapper(sample_mappings)
        raw_data = {
            'name': 'GigabitEthernet1/0/1',
            'type': {'value': '1000base-t'},
            'enabled': True
        }

        mapped_data = mapper.map_interface_data('netbox', raw_data)

        assert mapped_data['name'] == 'GigabitEthernet1/0/1'
        assert mapped_data['type'] == '1000base-t'
        assert mapped_data['enabled'] is True

    def test_missing_field_handling(self, sample_mappings):
        mapper = DataMapper(sample_mappings)
        raw_data = {
            'name': 'test-device'
            # Missing other fields
        }

        mapped_data = mapper.map_device_data('netbox', raw_data)

        assert mapped_data['name'] == 'test-device'
        assert 'status' not in mapped_data
        assert 'model' not in mapped_data

    def test_unknown_tool_handling(self, sample_mappings):
        mapper = DataMapper(sample_mappings)
        raw_data = {'name': 'test-device'}

        # Should return original data for unknown tool
        mapped_data = mapper.map_device_data('unknown_tool', raw_data)

        assert mapped_data == raw_data