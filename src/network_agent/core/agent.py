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

    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent executor"""
        prefix = """You are a network specialist assistant tasked with answering questions about network infrastructure and performance.
        You have access to NetBox for infrastructure data and LibreNMS for monitoring data.
        For each query, think step by step about what information you need and which systems to query.
        
        Available tools:
        {tools}
        
        Previous conversation:
        {chat_history}
        """

        suffix = """Begin by analyzing what information you need to answer the question.
        Break down complex queries into steps and use the appropriate tools for each step.
        Question: {input}
        Thought: Let me think about what information I need...
        {agent_scratchpad}"""

        prompt = PromptTemplate(
            input_variables=["input", "chat_history", "tools", "agent_scratchpad"],
            template=prefix + suffix
        )

        llm_chain = LLMChain(llm=self.llm, prompt=prompt)

        # Create agent that uses LLM to decide next action
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=self._get_output_parser(),
            stop=["\nObservation:", "\nQuestion:"],
            allowed_tools=[tool.name for tool in self.tools]
        )

        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

    def _query_netbox(self, query: str) -> str:
        """Query NetBox API using query planner"""
        try:
            # Use query planner to optimize the query
            steps = self.planner.create_plan(query)
            responses = []

            for step in self.planner.optimize_plan(steps):
                if step.system != "netbox":
                    continue

                response = self.netbox.query(
                    endpoint=step.endpoint,
                    params=step.filters
                )

                if response.success:
                    responses.append(response.data)
                else:
                    self.logger.error(f"NetBox query failed: {response.error}")
                    return f"Error querying NetBox: {response.error}"

            # Process and combine responses
            return self._format_responses(responses)

        except Exception as e:
            self.logger.error(f"Error in NetBox query: {e}")
            return f"An error occurred: {str(e)}"

    def _query_librenms(self, query: str) -> str:
        """Query LibreNMS API using query planner"""
        try:
            steps = self.planner.create_plan(query)
            responses = []

            for step in self.planner.optimize_plan(steps):
                if step.system != "librenms":
                    continue

                response = self.librenms.query(
                    endpoint=step.endpoint,
                    params=step.filters
                )

                if response.success:
                    responses.append(response.data)
                else:
                    self.logger.error(f"LibreNMS query failed: {response.error}")
                    return f"Error querying LibreNMS: {response.error}"

            return self._format_responses(responses)

        except Exception as e:
            self.logger.error(f"Error in LibreNMS query: {e}")
            return f"An error occurred: {str(e)}"

    def _analyze_connectivity(self, params: str) -> str:
        """Analyze network connectivity between elements"""
        try:
            # Parse parameters
            source, target = self._parse_connectivity_params(params)

            # Query device information from NetBox
            source_info = self._query_netbox(f"device:{source}")
            target_info = self._query_netbox(f"device:{target}")

            # Query interface status from LibreNMS
            source_status = self._query_librenms(f"ports:{source}")
            target_status = self._query_librenms(f"ports:{target}")

            # Analyze connectivity
            analysis = self._analyze_connection_data(
                source_info, target_info,
                source_status, target_status
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Error in connectivity analysis: {e}")
            return f"An error occurred during analysis: {str(e)}"

    def _format_responses(self, responses: List[Dict]) -> str:
        """Format API responses into readable text"""
        if not responses:
            return "No data found"

        # Get response template if available
        template = self.planner.semantics.get("response_templates", {}).get(
            responses[0].get("type", "default"), None
        )

        if template:
            # Use template to format response
            return template["template"].format(**responses[0])
        else:
            # Basic formatting
            formatted = []
            for response in responses:
                for key, value in response.items():
                    formatted.append(f"{key}: {value}")
            return "\n".join(formatted)

    def _parse_connectivity_params(self, params: str) -> tuple:
        """Parse connectivity analysis parameters"""
        try:
            source, target = params.split(",")
            return source.strip(), target.strip()
        except ValueError:
            raise ValueError(
                "Invalid connectivity parameters. Expected format: source,target"
            )

    def _analyze_connection_data(
        self,
        source_info: str,
        target_info: str,
        source_status: str,
        target_status: str
    ) -> str:
        """Analyze connection data and return findings"""
        # TODO: Implement detailed connection analysis
        return f"""Connection Analysis:
        Source Device: {source_info}
        Target Device: {target_info}
        Source Status: {source_status}
        Target Status: {target_status}
        """

    def _get_output_parser(self):
        """Get the output parser for the agent"""
        # TODO: Implement custom output parser if needed
        from langchain.agents import ReActSingleInputOutputParser
        return ReActSingleInputOutputParser()

    def process_query(self, query: str) -> str:
        """Process a user query and return the response"""
        try:
            return self.agent_executor.run(query)
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return f"An error occurred while processing your query: {str(e)}"