import logging
from typing import Any, Dict, List, Optional, Type

from adapters.librenms_adapter import LibreNMSAdapter
from adapters.netbox_adapter import NetboxAdapter
from core.network_tool_adapter import NetworkToolAdapter
from utils.config_loader import ConfigLoader, ConfigurationError


class ToolInitializationError(Exception):
    """Raised when there's an error initializing a network tool."""

    pass


class ToolManager:
    """Manages the lifecycle and interaction with network tool adapters."""

    # Registry of available tool adapters
    TOOL_REGISTRY = {"netbox": NetboxAdapter, "librenms": LibreNMSAdapter}

    def __init__(self, config_dir: str = "config"):
        """Initialize the tool manager.

        Args:
            config_dir: Path to configuration directory
        """
        self.logger = logging.getLogger("ToolManager")
        self.config_loader = ConfigLoader(config_dir)
        self.tools: Dict[str, NetworkToolAdapter] = {}
        self.aliases: Dict[str, str] = {}
        self.active_tool: Optional[str] = None

        self._initialize_tools()

    def _initialize_tools(self) -> None:
        """Initialize all enabled tools from configuration."""
        try:
            config = self.config_loader.load_all()
            main_config = config["main"]

            for tool_name, tool_config in main_config.get("tools", {}).items():
                if not tool_config.get("enabled", False):
                    self.logger.debug(f"Tool {tool_name} is disabled, skipping")
                    continue

                if tool_name not in self.TOOL_REGISTRY:
                    self.logger.warning(f"Unknown tool {tool_name} in config, skipping")
                    continue

                try:
                    # Initialize the tool adapter
                    tool_cls = self.TOOL_REGISTRY[tool_name]
                    tool_instance = tool_cls(config["tools"].get(tool_name, {}))

                    # Validate connection
                    if not tool_instance.validate_connection():
                        raise ToolInitializationError(
                            f"Failed to connect to {tool_name}"
                        )

                    self.tools[tool_name] = tool_instance

                    # Register aliases
                    for alias in tool_config.get("aliases", []):
                        self.aliases[alias] = tool_name

                    self.logger.info(f"Successfully initialized {tool_name}")

                except Exception as e:
                    self.logger.error(f"Error initializing {tool_name}: {str(e)}")
                    raise ToolInitializationError(
                        f"Failed to initialize {tool_name}: {str(e)}"
                    )

        except ConfigurationError as e:
            self.logger.error(f"Configuration error: {str(e)}")
            raise ToolInitializationError(f"Configuration error: {str(e)}")

    def get_tool(self, tool_identifier: str) -> Optional[NetworkToolAdapter]:
        """Get a tool instance by name or alias.

        Args:
            tool_identifier: Tool name or alias

        Returns:
            NetworkToolAdapter if found, None otherwise
        """
        # First check if it's a direct tool name
        if tool_identifier in self.tools:
            return self.tools[tool_identifier]

        # Then check aliases
        if tool_identifier in self.aliases:
            return self.tools[self.aliases[tool_identifier]]

        return None

    def get_all_tools(self) -> List[NetworkToolAdapter]:
        """Get all initialized tools.

        Returns:
            List of all active tool instances
        """
        return list(self.tools.values())

    def select_tool(self, tool_identifier: Optional[str] = None) -> bool:
        """Select a tool for subsequent operations.

        Args:
            tool_identifier: Tool name or alias, None to clear selection

        Returns:
            bool: True if selection was successful, False otherwise
        """
        if tool_identifier is None:
            self.active_tool = None
            return True

        tool = self.get_tool(tool_identifier)
        if tool is not None:
            self.active_tool = (
                tool_identifier
                if tool_identifier in self.tools
                else self.aliases[tool_identifier]
            )
            return True

        return False

    def get_active_tool(self) -> Optional[NetworkToolAdapter]:
        """Get the currently active tool.

        Returns:
            Currently active tool instance or None if no tool is selected
        """
        return self.tools.get(self.active_tool) if self.active_tool else None

    def execute_query(
        self, tool: Optional[str], method: str, *args: Any, **kwargs: Any
    ) -> Dict[str, Any]:
        """Execute a query on specific tool(s).

        Args:
            tool: Tool identifier or None for all tools
            method: Method name to call on the tool(s)
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Dictionary mapping tool names to their results
        """
        results = {}

        # If tool is specified, query only that tool
        if tool:
            tool_instance = self.get_tool(tool)
            if tool_instance and hasattr(tool_instance, method):
                try:
                    func = getattr(tool_instance, method)
                    results[tool] = func(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Error executing {method} on {tool}: {str(e)}")
                    results[tool] = {"error": str(e)}
            else:
                results[tool] = {
                    "error": f"Method {method} not found or tool not available"
                }

        # If no tool specified, query all tools
        else:
            for tool_name, tool_instance in self.tools.items():
                if hasattr(tool_instance, method):
                    try:
                        func = getattr(tool_instance, method)
                        results[tool_name] = func(*args, **kwargs)
                    except Exception as e:
                        self.logger.error(
                            f"Error executing {method} on {tool_name}: {str(e)}"
                        )
                        results[tool_name] = {"error": str(e)}
                else:
                    results[tool_name] = {"error": f"Method {method} not found"}

        return results

    def register_tool(
        self,
        name: str,
        tool_class: Type[NetworkToolAdapter],
        config: Dict[str, Any],
        aliases: Optional[List[str]] = None,
    ) -> bool:
        """Register a new tool at runtime.

        Args:
            name: Name for the tool
            tool_class: Tool adapter class
            config: Configuration for the tool
            aliases: Optional list of aliases for the tool

        Returns:
            bool: True if registration was successful
        """
        try:
            # Initialize the tool
            tool_instance = tool_class(config)

            # Validate connection
            if not tool_instance.validate_connection():
                raise ToolInitializationError(f"Failed to connect to {name}")

            # Register the tool
            self.tools[name] = tool_instance
            self.TOOL_REGISTRY[name] = tool_class

            # Register aliases
            if aliases:
                for alias in aliases:
                    self.aliases[alias] = name

            self.logger.info(f"Successfully registered new tool: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Error registering tool {name}: {str(e)}")
            return False
