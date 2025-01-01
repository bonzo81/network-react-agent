from typing import Dict, List, Optional, Any
from langchain.llms import OpenAI
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, ReActSingleInputOutputParser
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import logging
from .query_planner import QueryPlanner
from .context_manager import ContextManager
from ..api.network_client import NetworkClient, APIResponse
from ..utils.config import Configuration

class NetworkReActAgent:
    def __init__(
        self,
        config_path: Optional[str] = None,
        semantic_mappings: Optional[Dict] = None
    ):
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

        # Initialize LLM
        self.llm = OpenAI(
            api_key=self.config.get('llm.api_key'),
            base_url=self.config.get('llm.api_base'),
            model=self.config.get('llm.model', 'gpt-4'),
            temperature=self.config.get('llm.temperature', 0)
        )

        # Initialize managers
        self.context_manager = ContextManager()
        self.planner = QueryPlanner(semantic_mappings, llm=self.llm)
        self.memory = ConversationBufferMemory(memory_key="chat_history")

        # Initialize agent components
        self.tools = self._create_tools()
        self.agent_executor = self._create_agent()

    def _create_enhanced_prompt(self) -> PromptTemplate:
        prefix = """You are a network specialist assistant with access to NetBox and LibreNMS APIs.

        Key capabilities:
        - NetBox provides: device inventory, rack locations, IP addresses, circuits
        - LibreNMS provides: performance metrics, alerts, interface status

        Context:
        {context_summary}

        Available patterns:
        {query_patterns}

        When analyzing queries:
        1. Consider which system(s) will have the required information
        2. Break down complex queries into smaller steps
        3. Look for relationships between data from different systems
        4. Consider recent context for related information
        """

        suffix = """Question: {input}
        Thought: Let me analyze what information we need...
        {agent_scratchpad}"""

        return PromptTemplate(
            input_variables=["input", "context_summary", "query_patterns", "agent_scratchpad"],
            template=prefix + suffix
        )

    def _create_tools(self) -> List[Tool]:
        return [
            Tool(
                name="query_netbox",
                func=self._query_netbox,
                description="Query NetBox for infrastructure information"
            ),
            Tool(
                name="query_librenms",
                func=self._query_librenms,
                description="Query LibreNMS for monitoring data"
            ),
            Tool(
                name="analyze_connectivity",
                func=self._analyze_connectivity,
                description="Analyze network connectivity"
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

    def _query_netbox(self, query: str) -> str:
        try:
            steps = self.planner.create_plan(query)
            responses = []

            for step in self.planner.optimize_plan(steps):
                if step.system != "netbox":
                    continue

                self.logger.debug(f"Executing NetBox step: {step.purpose}")
                response = self.netbox.query(
                    endpoint=step.endpoint,
                    params=step.filters
                )

                if response.success:
                    responses.append(response.data)
                    self.context_manager.record_query(
                        query=query,
                        pattern="netbox_query",
                        success=True,
                        results=response.data
                    )
                else:
                    self.logger.error(f"NetBox query failed: {response.error}")
                    self.context_manager.record_query(
                        query=query,
                        pattern="netbox_query",
                        success=False,
                        results={"error": response.error}
                    )
                    return f"Error querying NetBox: {response.error}"

            return self._format_responses(responses)

        except Exception as e:
            self.logger.error(f"Error in NetBox query: {e}")
            return f"An error occurred: {str(e)}"

    def _query_librenms(self, query: str) -> str:
        try:
            steps = self.planner.create_plan(query)
            responses = []

            for step in self.planner.optimize_plan(steps):
                if step.system != "librenms":
                    continue

                self.logger.debug(f"Executing LibreNMS step: {step.purpose}")
                response = self.librenms.query(
                    endpoint=step.endpoint,
                    params=step.filters
                )

                if response.success:
                    responses.append(response.data)
                    self.context_manager.record_query(
                        query=query,
                        pattern="librenms_query",
                        success=True,
                        results=response.data
                    )
                else:
                    self.logger.error(f"LibreNMS query failed: {response.error}")
                    self.context_manager.record_query(
                        query=query,
                        pattern="librenms_query",
                        success=False,
                        results={"error": response.error}
                    )
                    return f"Error querying LibreNMS: {response.error}"

            return self._format_responses(responses)

        except Exception as e:
            self.logger.error(f"Error in LibreNMS query: {e}")
            return f"An error occurred: {str(e)}"

    def _analyze_connectivity(self, params: str) -> str:
        try:
            source, target = self._parse_connectivity_params(params)
            
            # Query device information
            source_info = self._query_netbox(f"device:{source}")
            target_info = self._query_netbox(f"device:{target}")
            
            # Get interface status
            source_status = self._query_librenms(f"ports:{source}")
            target_status = self._query_librenms(f"ports:{target}")
            
            # Analyze connectivity
            analysis = self._analyze_connection_data(
                source_info, target_info,
                source_status, target_status
            )
            
            self.context_manager.set_current_focus(f"connectivity_{source}_{target}")
            return analysis

        except Exception as e:
            self.logger.error(f"Error in connectivity analysis: {e}")
            return f"An error occurred: {str(e)}"

    def _validate_results(self, results: Dict, query: str) -> bool:
        validation_prompt = f"""Query: "{query}"
        Results: {results}
        
        Do these results fully answer the query?
        Consider:
        1. All requested information is present
        2. Data is clear and complete
        3. Necessary context is included
        4. Technical accuracy for network operations
        
        Respond with:
        Valid: Yes/No
        Missing: [list any missing elements]
        Improvements: [if any]
        """
        
        try:
            validation = self.llm(validation_prompt)
            parsed = self._parse_validation_response(validation)
            return parsed.get('valid', False)
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False

    def _refine_query(self, results: Dict, query: str) -> Optional[str]:
        refinement_prompt = f"""Given:
        Original Query: "{query}"
        Current Results: {results}
        Recent Context: {self.context_manager.get_context_summary()}
        
        Analyze if additional information would help:
        1. Missing context
        2. Related metrics needed
        3. Connected devices/services
        
        If more information needed, specify what and why.
        If current results sufficient, respond with "COMPLETE"
        """
        
        try:
            refinement = self.llm(refinement_prompt)
            if refinement.strip() == "COMPLETE":
                return None
            return refinement
        except Exception as e:
            self.logger.error(f"Refinement error: {e}")
            return None

    def process_query(self, query: str) -> str:
        try:
            # Get pattern matches and context
            patterns = self.planner._get_pattern_matches(query)
            self.context_manager.update_active_patterns([p.pattern for p in patterns])
            context = self.context_manager.get_context_summary()

            # Execute initial query
            results = self.agent_executor.run(
                input=query,
                context_summary=context,
                query_patterns=patterns
            )

            # Validate results
            success = self._validate_results(results, query)
            
            # Refine if needed
            if not success:
                refined_query = self._refine_query(results, query)
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

    def _combine_results(self, initial_results: Dict, additional_results: Dict) -> Dict:
        """Combine initial and additional results intelligently"""
        return {
            "primary_response": initial_results,
            "additional_context": additional_results,
            "combined_analysis": self._analyze_combined_results(
                initial_results, 
                additional_results
            )
        }

    def _analyze_combined_results(self, initial: Dict, additional: Dict) -> str:
        """Analyze and summarize combined results"""
        analysis_prompt = f"""Given:
        Initial Results: {initial}
        Additional Context: {additional}
        
        Provide a concise summary that:
        1. Integrates both sets of information
        2. Highlights key relationships
        3. Provides technical context
        """
        
        try:
            return self.llm(analysis_prompt)
        except Exception as e:
            self.logger.error(f"Analysis error: {e}")
            return "Error combining results"