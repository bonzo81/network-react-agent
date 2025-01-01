# Network ReAct Agent

A ReAct (Reasoning + Acting) agent for network operations that integrates with multiple network management and monitoring tools using Large Language Models.

## Overview

This project implements a ReAct pattern for network operations, enabling intelligent analysis and querying of network infrastructure using natural language. It provides a modular architecture that supports multiple network management tools (such as NetBox and LibreNMS) and can be extended to support additional tools.

## Key Features

- ReAct pattern implementation for network operations
- Modular adapter-based architecture for multiple network tools
- Built-in support for NetBox and LibreNMS
- Extensible interface for adding new network tool adapters
- Standardized data mapping across different tools
- Environment variable support for secure configuration
- Tool-specific querying with aliasing support
- Multi-tool query aggregation
- Intelligent context handling

## Prerequisites

- Python 3.8 or higher
- Access to supported network management tools (e.g., NetBox, LibreNMS)
- Access to an LLM provider

## Installation

1. Clone the repository:
```bash
git clone https://github.com/bonzo81/network-react-agent.git
cd network-react-agent
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install package and dependencies:
```bash
# For users
pip install .

# For developers
pip install -e ".[dev]"
```

## Configuration

The agent uses a hierarchical configuration system:

### Main Configuration (config/main.yaml)

Defines which tools are enabled and global settings:

```yaml
tools:
  netbox:
    enabled: true
    aliases: ["nx", "nbox"]
    config_file: "tools/netbox.yaml"
    mappings_file: "mappings/netbox_mappings.yaml"

  librenms:
    enabled: true
    aliases: ["libre", "lnms"]
    config_file: "tools/librenms.yaml"
    mappings_file: "mappings/librenms_mappings.yaml"

settings:
  default_behavior:
    query_all_enabled: true
    concurrent_queries: true
    maintain_context: true
    context_timeout: 300
```

### Tool Configuration (config/tools/)

Each tool has its own configuration file:

```yaml
# config/tools/netbox.yaml
api:
  url: "${NETBOX_URL}"
  token: "${NETBOX_TOKEN}"
  version: "3.5"
  verify_ssl: true
  timeout: 30

settings:
  device_query_limit: 1000
  cache_enabled: true

features:
  topology: true
  config_backup: true
  performance_metrics: true
```

### Data Mappings (config/mappings/)

Defines how tool-specific data is mapped to standardized format:

```yaml
# config/mappings/netbox_mappings.yaml
device:
  standard_fields:
    name: "name"
    status: "status.value"
    model: "device_type.model"
```

### Environment Variables

Sensitive configuration can use environment variables:

```bash
# Required for NetBox
NETBOX_URL=https://netbox.example.com
NETBOX_TOKEN=your_netbox_token

# Required for LibreNMS
LIBRENMS_URL=https://librenms.example.com
LIBRENMS_TOKEN=your_librenms_token
```

## Usage

### Basic Usage

```python
from network_agent import NetworkReActAgent

# Initialize the agent
agent = NetworkReActAgent()

# Query all configured tools
response = agent.process_query(
    "Show me all devices in the main datacenter"
)

# Query specific tool using alias
response = agent.process_query(
    "@nx show me all devices in rack A1"
)
```

### Tool-Specific Queries

You can target specific tools using the @tool syntax:

```python
# Query NetBox specifically
agent.process_query("@nx list all devices in site NYC")

# Query LibreNMS specifically
agent.process_query("@lnms show current alerts")

# Multi-tool query
agent.process_query("Show me all devices with critical alerts")
```

### Query Context

The agent maintains context across queries:

```python
# Initial query sets context
agent.process_query("@nx show devices in rack A1")

# Follow-up queries maintain context
agent.process_query("What are their interface statuses?")
agent.process_query("Any alerts from these devices?")
```

## Extending with New Tools

### Creating a New Adapter

1. Create a new adapter class implementing the NetworkToolAdapter interface:

```python
from core.network_tool_adapter import NetworkToolAdapter

class NewToolAdapter(NetworkToolAdapter):
    def __init__(self, config):
        self.config = config
        # Initialize tool-specific client

    def validate_connection(self) -> bool:
        # Validate API connection
        return True

    def get_devices(self, filters=None):
        # Implement device retrieval
        pass

    # Implement other required methods
```

2. Add tool configuration:

```yaml
# config/tools/new_tool.yaml
api:
  url: "${NEW_TOOL_URL}"
  token: "${NEW_TOOL_TOKEN}"

features:
  topology: true
  alerts: true
```

3. Add data mappings:

```yaml
# config/mappings/new_tool_mappings.yaml
device:
  standard_fields:
    name: "device_name"
    status: "device_status"
```

4. Enable the tool in main configuration:

```yaml
# config/main.yaml
tools:
  new_tool:
    enabled: true
    aliases: ["nt"]
    config_file: "tools/new_tool.yaml"
    mappings_file: "mappings/new_tool_mappings.yaml"
```

### Runtime Tool Registration

You can also register tools at runtime:

```python
from network_agent import NetworkReActAgent
from my_tools import CustomToolAdapter

agent = NetworkReActAgent()

# Register new tool
config = {
    'api': {
        'url': 'http://custom-tool.example.com',
        'token': 'my-token'
    }
}

agent.tool_manager.register_tool(
    name='custom_tool',
    tool_class=CustomToolAdapter,
    config=config,
    aliases=['ct']
)
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src
```

### Project Structure

```
network-react-agent/
├── config/                 # Configuration files
│   ├── main.yaml          # Main configuration
│   ├── tools/             # Tool-specific configs
│   └── mappings/          # Data mapping configs
├── src/
│   ├── core/              # Core components
│   │   ├── network_tool_adapter.py
│   │   ├── tool_manager.py
│   │   └── context_manager.py
│   ├── adapters/          # Tool implementations
│   │   ├── netbox_adapter.py
│   │   └── librenms_adapter.py
│   ├── utils/             # Utilities
│   │   ├── config_loader.py
│   │   └── data_mapper.py
│   └── network_agent/     # Main package
├── tests/                 # Test suite
└── README.md             # Documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Make your changes
5. Run tests
6. Submit a pull request

## License

MIT License - see LICENSE file for details