from typing import Dict, List, Optional, Any
from langchain.llms import OpenAI
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, ReActSingleInputOutputParser
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging
import re
from .query_planner import QueryPlanner
from .context_manager import ContextManager
from .tool_manager import ToolManager
from ..utils.config_loader import ConfigLoader

class NetworkReActAgent:
    # Regular expression for tool directives
    TOOL_DIRECTIVE_PATTERN = re.compile(r'^@([\w-]+)\s+(.*)$')

    def __init__(
        self,
        config_dir: str = 'config',
        semantic_mappings: Optional[Dict] = None
    ):
        self.logger = logging.getLogger("NetworkReActAgent")
        
        # Initialize configuration and managers
        self.config_loader = ConfigLoader(config_dir)
        self.config = self.config_loader.load_all()
        
        # Initialize tool manager
        self.tool_manager = ToolManager(config_dir)
        
        # Initialize LLM
        self.llm = OpenAI(
            api_key=self.config['main'].get('llm', {}).get('api_key'),
            base_url=self.config['main'].get('llm', {}).get('api_base'),
            model=self.config['main'].get('llm', {}).get('model', 'gpt-4'),
            temperature=self.config['main'].get('llm', {}).get('temperature', 0)
        )

        # Initialize other managers
        self.context_manager = ContextManager()
        self.planner = QueryPlanner(semantic_mappings, llm=self.llm)
        self.memory = ConversationBufferMemory(memory_key="chat_history")

        # Initialize agent components
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent()

    def _create_enhanced_prompt(self) -> PromptTemplate:
        # Get available tools for prompt
        available_tools = ", ".join([f"@{tool}" for tool in self.tool_manager.tools.keys()])
        
        prefix = f"""You are a network operations assistant with access to multiple network management tools.

        Available tools: {available_tools}
        You can target specific tools using @tool syntax, e.g., '@netbox show devices'

        Tool capabilities:
        {self._get_tool_capabilities()}

        Context:
        {{context_summary}}

        Available patterns:
        {{query_patterns}}

        When analyzing queries:
        1. Check if a specific tool is requested (@tool syntax)
        2. Consider which tool(s) have the required information
        3. Break down complex queries into steps
        4. Look for relationships between data from different tools
        5. Consider recent context for related information
        """

        suffix = """Question: {input}
        Thought: Let me analyze what information we need...
        {agent_scratchpad}"""

        return PromptTemplate(
            input_variables=["input", "context_summary", "query_patterns", "agent_scratchpad"],
            template=prefix + suffix
        )

    def _get_tool_capabilities(self) -> str:
        """Generate description of tool capabilities from config"""
        capabilities = []
        for tool_name, tool in self.tool_manager.tools.items():
            features = self.config['tools'].get(tool_name, {}).get('features', {})
            enabled_features = [k for k, v in features.items() if v]
            capabilities.append(f"- {tool_name}: {', '.join(enabled_features)}")
        return "\n".join(capabilities)

    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for each network operation"""
        return [
            Tool(
                name="query_tool",
                func=self._execute_tool_query,
                description="Query specific network tool or all tools"
            ),
            Tool(
                name="analyze_connectivity",
                func=self._analyze_connectivity,
                description="Analyze network connectivity between devices"
            )
        ]

    def _create_agent(self) -> AgentExecutor:
        prompt = self._create_enhanced_prompt()
        llm_chain = LLMChain(llm=self.llm, prompt=prompt)
        
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=ReActSingleInputOutputParser(),
            stop=["\nObservation:", "\nQuestion:"],
            allowed_tools=[tool.name for tool in self.tools]
        )

        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True
        )

    def _execute_tool_query(self, query: str) -> str:
        """Execute a query against specific tool(s)"""
        try:
            # Check for tool directive
            match = self.TOOL_DIRECTIVE_PATTERN.match(query)
            if match:
                tool_name, tool_query = match.groups()
                self.tool_manager.select_tool(tool_name)
            else:
                tool_name = None
                tool_query = query
                self.tool_manager.select_tool(None)  # Clear tool selection

            # Create and optimize query plan
            steps = self.planner.create_plan(tool_query)
            responses = []

            for step in self.planner.optimize_plan(steps):
                # Execute query through tool manager
                result = self.tool_manager.execute_query(
                    tool_name,
                    step.method,
                    filters=step.filters
                )

                if any('error' in r for r in result.values()):
                    errors = [f"{t}: {r['error']}" for t, r in result.items() if 'error' in r]
                    return f"Errors occurred: {'; '.join(errors)}"

                responses.append(result)

            # Record query in context
            self.context_manager.record_query(
                query=query,
                pattern="tool_query",
                success=True,
                results=responses
            )

            return self._format_responses(responses)

        except Exception as e:
            self.logger.error(f"Error executing tool query: {e}")
            return f"An error occurred: {str(e)}"

    def _analyze_connectivity(self, params: str) -> str:
        """Analyze network connectivity between devices"""
        try:
            source, target = self._parse_connectivity_params(params)
            
            # Get device information from available tools
            device_info = self.tool_manager.execute_query(
                None,  # Query all tools
                'get_devices',
                filters={'name__in': [source, target]}
            )
            
            # Get interface information
            interface_info = self.tool_manager.execute_query(
                None,
                'get_interfaces',
                device_id=source
            )
            
            # Analyze connectivity
            analysis = self._analyze_connection_data(device_info, interface_info)
            
            self.context_manager.set_current_focus(f"connectivity_{source}_{target}")
            return analysis

        except Exception as e:
            self.logger.error(f"Error in connectivity analysis: {e}")
            return f"An error occurred: {str(e)}"

    def _format_responses(self, responses: List[Dict[str, Any]]) -> str:
        """Format responses from multiple tools"""
        formatted = []
        for response in responses:
            for tool_name, data in response.items():
                formatted.append(f"[{tool_name}]\n{self._format_tool_data(data)}")
        return "\n\n".join(formatted)

    def _format_tool_data(self, data: Any) -> str:
        """Format data from a specific tool"""
        if isinstance(data, list):
            return "\n".join(f"- {item}" for item in data)
        elif isinstance(data, dict):
            return "\n".join(f"{k}: {v}" for k, v in data.items())
        return str(data)

    def process_query(self, query: str) -> str:
        try:
            # Parse tool directive if present
            match = self.TOOL_DIRECTIVE_PATTERN.match(query)
            if match:
                tool_name, actual_query = match.groups()
                if not self.tool_manager.select_tool(tool_name):
                    return f"Unknown tool: {tool_name}"
            else:
                actual_query = query
                self.tool_manager.select_tool(None)

            # Get pattern matches and context
            patterns = self.planner._get_pattern_matches(actual_query)
            self.context_manager.update_active_patterns([p.pattern for p in patterns])
            context = self.context_manager.get_context_summary()

            # Execute query
            results = self.agent_executor.run(
                input=actual_query,
                context_summary=context,
                query_patterns=patterns
            )

            # Validate and refine results
            success = self._validate_results(results, actual_query)
            if not success:
                refined_query = self._refine_query(results, actual_query)
                if refined_query:
                    additional_results = self.agent_executor.run(refined_query)
                    results = self._combine_results(results, additional_results)

            # Record query
            self.context_manager.record_query(
                query=query,
                pattern=patterns[0].pattern if patterns else "unknown",
                success=success,
                results=results
            )

            return results

        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            error_msg = f"An error occurred: {str(e)}"
            self.context_manager.record_query(
                query=query,
                pattern="error",
                success=False,
                results={"error": str(e)}
            )
            return error_msg