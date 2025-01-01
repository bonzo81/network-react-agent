# Network ReAct Agent

A ReAct (Reasoning + Acting) agent for network operations that integrates with NetBox and LibreNMS APIs using Large Language Models.

## Overview

This project implements a ReAct pattern for network operations, enabling intelligent analysis and querying of network infrastructure using natural language. It combines NetBox (network source of truth) and LibreNMS (network monitoring) data with LLM-powered reasoning to provide intelligent network analysis and operations assistance.

## Key Features

- ReAct pattern implementation for network operations
- Integration with NetBox and LibreNMS APIs
- Support for OpenAI-compatible LLM endpoints (OpenAI, Anthropic, Ollama)
- Flexible query handling for complex network analysis
- Optimized endpoint usage based on expert patterns
- Multiple configuration methods (environment variables, YAML, or both)
- Intelligent handling of network queries and data analysis
- Support for both physical and logical network analysis

## Prerequisites

- Python 3.8 or higher
- Access to a NetBox instance
- Access to a LibreNMS instance
- Access to an OpenAI-compatible LLM (OpenAI API, Ollama, etc.)

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

The agent supports multiple configuration methods:

### 1. Environment Variables (Recommended for sensitive data)

```bash
# Copy the example .env file
cp .env.example .env

# Edit with your values
vim .env
```

Required environment variables:
```bash
# NetBox Configuration
NETBOX_URL=https://netbox.example.com
NETBOX_TOKEN=your_netbox_token

# LibreNMS Configuration
LIBRENMS_URL=https://librenms.example.com
LIBRENMS_TOKEN=your_librenms_token

# LLM Configuration
OPENAI_API_KEY=your_openai_key
```

Optional environment variables:
```bash
# NetBox optional settings
NETBOX_TIMEOUT=30

# LibreNMS optional settings
LIBRENMS_TIMEOUT=30

# LLM optional settings
OPENAI_API_BASE=http://localhost:11434/v1  # For Ollama
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0
```

### 2. YAML Configuration (Recommended for complex settings)

```bash
# Copy the example configuration
cp config/config.example.yaml config/config.yaml

# Edit with your values
vim config/config.yaml
```

Example configuration:
```yaml
netbox:
  base_url: "https://netbox.example.com"
  api_token: "your_netbox_token"
  timeout: 30
  verify_ssl: true

librenms:
  base_url: "https://librenms.example.com"
  api_token: "your_librenms_token"
  timeout: 30
  verify_ssl: true

llm:
  api_key: "your_openai_key"
  model: "gpt-4"
  temperature: 0
```

### Configuration Priority

The configuration system follows this priority order:
1. Environment variables (highest priority)
2. .env file values
3. YAML config file values
4. Default values (lowest priority)

## Usage

### Basic Usage

```python
from network_agent import NetworkReActAgent

# Using environment variables
agent = NetworkReActAgent.from_env()

# Simple connectivity query
response = agent.process_query(
    "Does Site A have any high-bandwidth connections to other sites?"
)
print(response)

# Complex analysis query
response = agent.process_query(
    "Analyze the performance of all inter-site links and identify any "
    "potential bottlenecks or underutilized connections"
)
print(response)
```

### Using Configuration File

```python
from network_agent import NetworkReActAgent

# Initialize agent using config file
agent = NetworkReActAgent.from_config('config/config.yaml')

# Query with specific context
response = agent.process_query(
    "What is the current utilization of links between datacenter sites?"
)
print(response)
```

### Using Different LLM Providers

The agent supports any OpenAI-compatible endpoint. Configure via environment variables or YAML:

```python
# Using Ollama (via environment variables)
# In .env:
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=not-needed-for-ollama
LLM_MODEL=llama2

# Using Anthropic (via config file)
# In config.yaml:
llm:
  api_base: "your-anthropic-compatible-endpoint"
  api_key: "your-anthropic-key"
  model: "claude-3-opus-20240229"
```

### Example Queries

The agent can handle various types of network analysis queries:

```python
# Physical connectivity analysis
agent.process_query("What are all the connections between our datacenter sites?")

# Performance analysis
agent.process_query("Are any inter-site links showing signs of congestion?")

# Capacity planning
agent.process_query("Do we have enough bandwidth between Site A and Site B for a new 10G service?")

# Network inventory
agent.process_query("List all devices in Site A that have 100G capable interfaces")

# Complex analysis
agent.process_query(
    "Analyze our backbone connectivity and identify any single points of "
    "failure or paths that need redundancy"
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
│       │   └── network_client.py
│       ├── core/           # Core logic
│       │   ├── agent.py
│       │   └── query_planner.py
│       └── utils/          # Utilities
│           ├── config.py
│           └── logger.py
├── tests/                  # Test suite
│   ├── conftest.py
│   ├── test_agent.py
│   └── test_api_client.py
├── .env.example           # Environment variables example
├── setup.py               # Package setup
└── README.md             # Documentation
```

## Advanced Usage

### Custom Query Patterns

You can add custom query patterns by modifying the semantic mappings:

```python
# Load custom patterns
with open('my_patterns.json') as f:
    custom_patterns = json.load(f)

# Initialize agent with custom patterns
agent = NetworkReActAgent.from_env(semantic_mappings=custom_patterns)
```

### Error Handling

The agent provides detailed error information:

```python
try:
    response = agent.process_query("Complex query")
except Exception as e:
    print(f"Error type: {type(e).__name__}")
    print(f"Error details: {str(e)}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `pip install -e ".[dev]"`
4. Make your changes
5. Run tests: `pytest`
6. Submit a pull request

## Troubleshooting

### Common Issues

1. API Authentication:
   - Verify API tokens are correct
   - Check API endpoint URLs
   - Ensure proper permissions in NetBox/LibreNMS

2. LLM Configuration:
   - Verify API key is valid
   - Check model availability
   - Confirm API endpoint compatibility

3. Query Issues:
   - Review semantic mappings
   - Check API response patterns
   - Verify data availability

### Getting Help

- Open an issue for bugs or feature requests
- Check existing issues for solutions
- Review the documentation

## License

MIT License - see LICENSE file for details