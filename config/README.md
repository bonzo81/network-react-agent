# Configuration Directory

This directory contains all configuration files for the network-react-agent.

## Structure

- `main.yaml`: Main configuration file defining enabled tools and global settings
- `tools/`: Directory containing tool-specific configurations
- `mappings/`: Directory containing data mapping configurations

## Environment Variables

Sensitive configuration values can use environment variables using the ${VAR_NAME} syntax in the YAML files.

Required environment variables for default tools:

```bash
# NetBox
NETBOX_URL=https://netbox.example.com
NETBOX_TOKEN=your_netbox_token

# LibreNMS
LIBRENMS_URL=https://librenms.example.com
LIBRENMS_TOKEN=your_librenms_token
```