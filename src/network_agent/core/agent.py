from typing import Dict, List, Optional, Any
from langchain.llms import OpenAI
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging
from .query_planner import QueryPlanner
from ..api.network_client import NetworkClient, APIResponse

class NetworkReActAgent:
    """ReAct agent for network operations"""

    def __init__(
        self,
        netbox_client: NetworkClient,
        librenms_client: NetworkClient,
        semantic_mappings: Dict,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0
    ):
        self.netbox = netbox_client
        self.librenms = librenms_client
        self.planner = QueryPlanner(semantic_mappings)
        self.logger = logging.getLogger("NetworkReActAgent")

        # Initialize LLM
        self.llm = OpenAI(
            base_url=api_base,
            api_key=api_key,
            model=model,
            temperature=temperature
        )
        self.memory = ConversationBufferMemory(memory_key="chat_history")

        # Initialize agent components
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent()

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
        """Create the ReAct agent"""
        template = """
You are a network operations assistant. Your goal is to help analyze and understand 
network connectivity and performance using NetBox and LibreNMS data.

Available Tools:
{tools}

Use this format:
Thought: Consider what information you need
Action: Tool to use
Action Input: Input parameters
Observation: Tool result
... (repeat Thought/Action/Observation N times)
Thought: I have enough information
Final Answer: Detailed response

Previous conversation:
{chat_history}

New question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["tools", "chat_history", "input", "agent_scratchpad"]
        )

        llm_chain = LLMChain(llm=self.llm, prompt=prompt)

        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            allowed_tools=[tool.name for tool in self.tools],
            memory=self.memory
        )

        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

    def process_query(self, query: str) -> str:
        """Process a network operations query"""
        try:
            return self.agent_executor.run(query)
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return f"Error processing query: {str(e)}"

    def _query_netbox(self, query_input: str) -> str:
        """Execute a NetBox query"""
        try:
            # Create query plan
            steps = self.planner.create_plan(query_input)
            if not steps:
                return "Could not determine how to query NetBox for this request"

            # Execute relevant steps
            results = []
            for step in steps:
                if step.system == "netbox":
                    response = self.netbox.query(
                        endpoint=step.endpoint,
                        params=step.filters
                    )
                    if response.success:
                        results.append(response.data)
                    else:
                        return f"Error querying NetBox: {response.error}"

            return str(results)
        except Exception as e:
            return f"Error in NetBox query: {str(e)}"

    def _query_librenms(self, query_input: str) -> str:
        """Execute a LibreNMS query"""
        try:
            # Create query plan
            steps = self.planner.create_plan(query_input)
            if not steps:
                return "Could not determine how to query LibreNMS for this request"

            # Execute relevant steps
            results = []
            for step in steps:
                if step.system == "librenms":
                    response = self.librenms.query(
                        endpoint=step.endpoint,
                        params=step.filters
                    )
                    if response.success:
                        results.append(response.data)
                    else:
                        return f"Error querying LibreNMS: {response.error}"

            return str(results)
        except Exception as e:
            return f"Error in LibreNMS query: {str(e)}"

    def _analyze_connectivity(self, context: str) -> str:
        """Analyze network connectivity based on combined data"""
        try:
            # Get physical connectivity from NetBox
            netbox_response = self._query_netbox(context)
            if "Error" in netbox_response:
                return netbox_response

            # Get performance data from LibreNMS
            librenms_response = self._query_librenms(context)
            if "Error" in librenms_response:
                return librenms_response

            # Combine and analyze data
            analysis = (
                f"Physical Connectivity: {netbox_response}\n\n"
                f"Performance Data: {librenms_response}"
            )

            return analysis
        except Exception as e:
            return f"Error analyzing connectivity: {str(e)}"
