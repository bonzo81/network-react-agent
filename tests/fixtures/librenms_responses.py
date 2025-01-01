# Mock responses for LibreNMS API tests

DEVICE_RESPONSE = {
    'status': 'ok',
    'devices': [{
        'device_id': '1',
        'hostname': 'test-device-01',
        'status': 1,
        'hardware': 'Cisco Catalyst 3750',
        'serial': 'ABC123XYZ',
        'location': 'Main DC',
        'ip': '192.168.1.1'
    }]
}

INTERFACE_RESPONSE = {
    'status': 'ok',
    'ports': [{
        'ifName': 'GigabitEthernet1/0/1',
        'ifType': '1000base-t',
        'ifAdminStatus': 'up',
        'ifMtu': 1500,
        'ifPhysAddress': '00:11:22:33:44:55',
        'ifAlias': 'Uplink to Core',
        'ifSpeed': 1000000000,
        'ifInOctets': 1000000,
        'ifOutOctets': 2000000,
        'ifInErrors': 0,
        'ifOutErrors': 0
    }]
}

ALERT_RESPONSE = {
    'status': 'ok',
    'alerts': [{
        'id': '1',
        'rule_name': 'High CPU Usage',
        'severity': 'critical',
        'state': 'active',
        'timestamp': '2024-01-01 00:00:00',
        'lastchange': '2024-01-01 00:01:00',
        'device_id': '1',
        'msg': 'CPU usage above threshold'
    }]
}