from typing import Dict, List, Optional, Any
from langchain.llms import OpenAI
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging
from .query_planner import QueryPlanner
from ..api.network_client import NetworkClient, APIResponse
from ..utils.config import Configuration

class NetworkReActAgent:
    """ReAct agent for network operations"""

    def __init__(
        self,
        config_path: Optional[str] = None,
        semantic_mappings: Optional[Dict] = None
    ):
        # Load configuration
        self.config = Configuration(config_path)
        self.logger = logging.getLogger("NetworkReActAgent")

        # Initialize API clients
        self.netbox = NetworkClient(
            base_url=self.config.get('netbox.base_url'),
            api_token=self.config.get('netbox.api_token'),
            timeout=self.config.get('netbox.timeout', 30),
            verify_ssl=self.config.get('netbox.verify_ssl', True)
        )

        self.librenms = NetworkClient(
            base_url=self.config.get('librenms.base_url'),
            api_token=self.config.get('librenms.api_token'),
            timeout=self.config.get('librenms.timeout', 30),
            verify_ssl=self.config.get('librenms.verify_ssl', True)
        )

        # Initialize query planner
        self.planner = QueryPlanner(semantic_mappings)

        # Initialize LLM
        self.llm = OpenAI(
            api_key=self.config.get('llm.api_key'),
            base_url=self.config.get('llm.api_base'),
            model=self.config.get('llm.model', 'gpt-4'),
            temperature=self.config.get('llm.temperature', 0)
        )
        self.memory = ConversationBufferMemory(memory_key="chat_history")

        # Initialize agent components
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent()

    @classmethod
    def from_env(cls, semantic_mappings: Optional[Dict] = None):
        """Create agent instance using environment variables"""
        return cls(config_path=None, semantic_mappings=semantic_mappings)

    @classmethod
    def from_config(cls, config_path: str, semantic_mappings: Optional[Dict] = None):
        """Create agent instance using config file"""
        return cls(config_path=config_path, semantic_mappings=semantic_mappings)

    def _create_tools(self) -> List[Tool]:
        """Create tools available to the agent"""
        return [
            Tool(
                name="query_netbox",
                func=self._query_netbox,
                description="Query NetBox API to get network infrastructure information"
            ),
            Tool(
                name="query_librenms",
                func=self._query_librenms,
                description="Query LibreNMS API to get network monitoring and performance data"
            ),
            Tool(
                name="analyze_connectivity",
                func=self._analyze_connectivity,
                description="Analyze connectivity between network elements"
            )
        ]

    [Rest of the agent implementation remains the same...]