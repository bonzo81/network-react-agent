# Network ReAct Agent

A ReAct (Reasoning + Acting) agent for network operations that integrates with NetBox and LibreNMS APIs using Large Language Models.

## Features

- ReAct pattern implementation for network operations
- Integration with NetBox and LibreNMS APIs
- Support for OpenAI-compatible LLM endpoints
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

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
export OPENAI_API_KEY="your-key"
export NETBOX_TOKEN="your-token"
export LIBRENMS_TOKEN="your-token"
```

## Configuration

1. Copy the example configuration:
```bash
cp config/config.example.yaml config/config.yaml
```

2. Update the configuration with your settings:
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
from network_agent.agent import NetworkReActAgent
from network_agent.api import NetworkClient

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
# Using Ollama (local deployment)
agent = NetworkReActAgent(
    netbox_client=netbox_client,
    librenms_client=librenms_client,
    api_base="http://localhost:11434/v1",
    api_key="not-needed-for-ollama",
    model="llama2"
)

# Using other OpenAI-compatible providers
agent = NetworkReActAgent(
    netbox_client=netbox_client,
    librenms_client=librenms_client,
    api_base="https://your-provider-endpoint/v1",
    api_key="your-provider-key",
    model="your-model-name"
)
```

## Testing

Run the test suite:
```bash
pytest
```

Run specific tests:
```bash
pytest tests/test_agent.py -v
```

## Project Structure

```
network_agent/
├── config/
│   ├── config.example.yaml
│   └── semantic_mappings.json
├── src/
│   ├── api/
│   │   ├── network_client.py
│   │   ├── netbox.py
│   │   └── librenms.py
│   ├── core/
│   │   ├── query_planner.py
│   │   ├── semantic_engine.py
│   │   └── agent.py
│   └── utils/
│       └── logger.py
└── tests/
    ├── conftest.py
    ├── test_api_client.py
    ├── test_query_planner.py
    └── test_agent.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details