from typing import List, Dict, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class QueryStep(BaseModel):
    """Represents a single step in a query execution plan"""
    system: str  # 'netbox' or 'librenms'
    endpoint: str
    filters: Dict
    purpose: str
    depends_on: Optional[List[str]] = None

class QueryPlanner:
    """Plans and optimizes query execution based on semantic patterns"""
    
    def __init__(self, semantic_mappings: Dict):
        self.semantics = semantic_mappings
        self.logger = logging.getLogger("QueryPlanner")
    
    def create_plan(self, query: str) -> List[QueryStep]:
        """Create an optimized query plan based on the input query"""
        # Match query against known patterns
        pattern = self._match_pattern(query)
        if not pattern:
            self.logger.warning(f"No matching pattern found for query: {query}")
            return []
        
        # Get optimal endpoints for the pattern
        pattern_info = self.semantics["query_patterns"][pattern]
        endpoints = pattern_info["optimal_endpoints"]
        
        # Create steps based on pattern
        steps = []
        
        # Add primary query steps
        if "primary" in endpoints:
            primary = endpoints["primary"]
            steps.append(
                QueryStep(
                    system=primary.get("system", "netbox"),
                    endpoint=primary["endpoint"],
                    filters=primary.get("filters", {}),
                    purpose=f"primary_{pattern}_query"
                )
            )
        
        # Add any secondary/dependent queries
        if "secondary" in endpoints:
            for secondary in endpoints["secondary"]:
                steps.append(
                    QueryStep(
                        system=secondary.get("system", "netbox"),
                        endpoint=secondary["endpoint"],
                        filters=secondary.get("filters", {}),
                        purpose=secondary.get("purpose", "secondary_query"),
                        depends_on=[step.purpose for step in steps]
                    )
                )
        
        self.logger.info(f"Created plan with {len(steps)} steps for pattern: {pattern}")
        return steps
    
    def _match_pattern(self, query: str) -> Optional[str]:
        """Match query against known patterns"""
        query_lower = query.lower()
        
        for pattern, info in self.semantics["query_patterns"].items():
            # Check keywords
            if any(keyword in query_lower for keyword in info["keywords"]):
                self.logger.debug(f"Matched pattern: {pattern}")
                return pattern
            
            # Check additional pattern matching logic if defined
            if "patterns" in info:
                for pattern_regex in info["patterns"]:
                    if pattern_regex.search(query_lower):
                        self.logger.debug(f"Matched regex pattern: {pattern}")
                        return pattern
        
        return None
    
    def validate_step(self, step: QueryStep) -> bool:
        """Validate a query step against semantic mappings"""
        # Check if system is valid
        if step.system not in ["netbox", "librenms"]:
            self.logger.error(f"Invalid system: {step.system}")
            return False
        
        # Check if endpoint exists in mappings
        pattern_endpoints = []
        for pattern in self.semantics["query_patterns"].values():
            for endpoint_info in pattern["optimal_endpoints"].values():
                if isinstance(endpoint_info, list):
                    pattern_endpoints.extend(e["endpoint"] for e in endpoint_info)
                else:
                    pattern_endpoints.append(endpoint_info["endpoint"])
        
        if step.endpoint not in pattern_endpoints:
            self.logger.error(f"Unknown endpoint: {step.endpoint}")
            return False
        
        return True
    
    def optimize_plan(self, steps: List[QueryStep]) -> List[QueryStep]:
        """Optimize a query plan by combining or reordering steps"""
        if not steps:
            return steps
        
        optimized = []
        current_system = None
        
        # Group steps by system to minimize system switches
        for step in sorted(steps, key=lambda s: (s.system, bool(s.depends_on))):
            if step.system != current_system and optimized:
                # Add system switch marker if needed
                self.logger.debug(f"System switch: {current_system} -> {step.system}")
            current_system = step.system
            optimized.append(step)
        
        return optimized