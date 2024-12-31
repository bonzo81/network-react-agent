# Network ReAct Agent

A ReAct (Reasoning + Acting) agent for network operations that integrates with NetBox and LibreNMS APIs using Large Language Models.

## Overview

This project implements a ReAct pattern for network operations, enabling intelligent analysis and querying of network infrastructure using natural language. It combines NetBox (network source of truth) and LibreNMS (network monitoring) data with LLM-powered reasoning.

## Features

- ReAct pattern implementation for network operations
- Integration with NetBox and LibreNMS APIs
- Support for OpenAI-compatible LLM endpoints (OpenAI, Anthropic, Ollama)
- Flexible query handling for complex network analysis
- Optimized endpoint usage based on expert patterns

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

1. Create configuration file:
```bash
cp config/config.example.yaml config/config.yaml
```

2. Set up environment variables:
```bash
# Create .env file
cat > .env << EOL
NETBOX_TOKEN=your_netbox_token
LIBRENMS_TOKEN=your_librenms_token
OPENAI_API_KEY=your_openai_key
EOL
```

3. Update configuration in `config/config.yaml`:
```yaml
netbox:
  base_url: "https://your-netbox-instance"
  timeout: 30

librenms:
  base_url: "https://your-librenms-instance"
  timeout: 30
```

## Usage

### Basic Usage

```python
from network_agent import NetworkReActAgent, NetworkClient

# Initialize clients
netbox_client = NetworkClient(
    base_url="https://netbox.example.com",
    api_token="your-token"
)

librenms_client = NetworkClient(
    base_url="https://librenms.example.com",
    api_token="your-token"
)

# Initialize agent
agent = NetworkReActAgent(
    netbox_client=netbox_client,
    librenms_client=librenms_client,
    api_key="your-llm-api-key"
)

# Process a query
response = agent.process_query(
    "Does Site A have any high-bandwidth connections to other sites?"
)
print(response)
```

### Using Different LLM Providers

The agent supports any OpenAI-compatible endpoint:

```python
# Using Ollama
agent = NetworkReActAgent(
    netbox_client=netbox_client,
    librenms_client=librenms_client,
    api_base="http://localhost:11434/v1",
    api_key="not-needed-for-ollama",
    model="llama2"
)

# Using Anthropic (via OpenAI-compatible endpoint)
agent = NetworkReActAgent(
    netbox_client=netbox_client,
    librenms_client=librenms_client,
    api_base="your-anthropic-compatible-endpoint",
    api_key="your-anthropic-key",
    model="claude-3-opus-20240229"
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

# Run specific tests
pytest tests/test_agent.py

# Run tests continuously
ptw
```

### Project Structure

```
network_agent/
├── config/                  # Configuration files
│   ├── config.example.yaml
│   └── semantic_mappings.json
├── src/
│   └── network_agent/      # Main package
│       ├── api/            # API clients
│       ├── core/           # Core logic
│       └── utils/          # Utilities
├── tests/                  # Test suite
│   ├── conftest.py
│   └── test_*.py
├── setup.py               # Package setup
└── README.md             # Documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `pip install -e ".[dev]"`
4. Make your changes
5. Run tests: `pytest`
6. Submit a pull request

## License

MIT License - see LICENSE file for details