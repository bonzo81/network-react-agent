# Mock responses for NetBox API tests

DEVICE_RESPONSE = {
    'count': 1,
    'results': [{
        'id': 1,
        'name': 'test-device-01',
        'status': {'value': 'active'},
        'device_type': {'model': 'Cisco Catalyst 3750'},
        'serial': 'ABC123XYZ',
        'site': {'name': 'Main DC'},
        'rack': {'name': 'Rack-01'},
        'position': 42,
        'primary_ip4': {'address': '192.168.1.1'}
    }]
}

INTERFACE_RESPONSE = {
    'count': 2,
    'results': [{
        'name': 'GigabitEthernet1/0/1',
        'type': {'value': '1000base-t'},
        'enabled': True,
        'mtu': 1500,
        'mac_address': '00:11:22:33:44:55',
        'description': 'Uplink to Core'
    }, {
        'name': 'GigabitEthernet1/0/2',
        'type': {'value': '1000base-t'},
        'enabled': True,
        'mtu': 1500,
        'mac_address': '00:11:22:33:44:56',
        'description': 'Server Connection'
    }]
}

ALERT_RESPONSE = {
    'count': 1,
    'results': [{
        'id': 1,
        'name': 'High CPU Usage',
        'priority': {'label': 'high'},
        'status': {'value': 'active'},
        'created': '2024-01-01T00:00:00Z',
        'last_updated': '2024-01-01T00:01:00Z'
    }]
}