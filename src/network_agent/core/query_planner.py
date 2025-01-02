import logging
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class QueryStep(BaseModel):
    """Represents a single step in a query execution plan"""

    system: str  # 'netbox' or 'librenms'
    endpoint: str
    filters: Dict
    purpose: str
    depends_on: Optional[List[str]] = None


class PatternMatch(BaseModel):
    """Represents a matched pattern with confidence score"""

    pattern: str
    confidence: float
    source: str  # 'keyword', 'semantic', 'regex'
    reasoning: Optional[str] = None


class QueryPlanner:
    """Plans and optimizes query execution based on semantic patterns"""

    def __init__(self, semantic_mappings: Dict, llm: Any = None):
        self.semantics = semantic_mappings
        self.llm = llm  # LLM instance for semantic analysis
        self.logger = logging.getLogger("QueryPlanner")

    def create_plan(self, query: str) -> List[QueryStep]:
        """Create an optimized query plan based on the input query"""
        # Get pattern matches with confidence scores
        matches = self._get_pattern_matches(query)
        if not matches:
            self.logger.warning(f"No matching pattern found for query: {query}")
            return []

        # Use best matching pattern
        best_match = matches[0]
        pattern = best_match.pattern
        pattern_info = self.semantics["query_patterns"][pattern]

        # Get optimal endpoints and create plan
        return self._create_plan_from_pattern(pattern_info, query)

    def _get_pattern_matches(self, query: str) -> List[PatternMatch]:
        """Get all matching patterns with confidence scores"""
        matches = []

        # Get keyword/regex matches
        direct_matches = self._match_pattern(query)
        if direct_matches:
            matches.extend(direct_matches)

        # Get semantic matches if LLM is available
        if self.llm:
            semantic_matches = self._identify_semantic_matches(query)
            matches.extend(semantic_matches)

        # Rank and deduplicate matches
        return self._rank_pattern_matches(matches)

    def _match_pattern(self, query: str) -> List[PatternMatch]:
        """Match query against known patterns using keywords and regex"""
        print(f"Starting pattern matching for query: {query}")
        query_lower = query.lower()
        matches = []

        for pattern, info in self.semantics["query_patterns"].items():
            print(f"Checking pattern: {pattern}")
            # Check keywords
            keyword_matches = [
                keyword for keyword in info["keywords"] if keyword in query_lower
            ]
            print(f"Found keyword matches: {keyword_matches}")
            if keyword_matches:
                confidence = len(keyword_matches) / len(info["keywords"])
                print(f"Adding keyword match with confidence: {confidence}")
                matches.append(
                    PatternMatch(
                        pattern=pattern,
                        confidence=confidence,
                        source="keyword",
                        reasoning=f"Matched keywords: {', '.join(keyword_matches)}",
                    )
                )

            # Check regex patterns
            if "patterns" in info:
                print(f"Checking regex patterns for {pattern}")
                for pattern_regex in info["patterns"]:
                    if pattern_regex.search(query_lower):
                        print(f"Found regex match for pattern: {pattern}")
                        matches.append(
                            PatternMatch(
                                pattern=pattern,
                                confidence=0.8,  # High confidence for regex match
                                source="regex",
                                reasoning="Matched regex pattern",
                            )
                        )

        print(f"Returning {len(matches)} matches")
        return matches
    def _identify_semantic_matches(self, query: str) -> List[PatternMatch]:
        """Use LLM to identify semantic matches to query patterns"""
        if not self.llm:
            return []

        prompt = f"""Given the user query: "{query}"
        And these available patterns: {self.semantics['query_patterns']}
        
        Analyze how this query might match our patterns semantically.
        Consider:
        1. The underlying intent of the query
        2. Required information types
        3. Implicit relationships
        
        Format your response as:
        pattern_name: confidence_score (0-1), reasoning
        """

        try:
            analysis = self.llm(prompt)
            return self._parse_semantic_matches(analysis)
        except Exception as e:
            self.logger.error(f"Error in semantic matching: {e}")
            return []

    def _rank_pattern_matches(self, matches: List[PatternMatch]) -> List[PatternMatch]:
        """Rank and combine pattern matches"""
        # Combine matches with same pattern
        combined = {}
        for match in matches:
            if match.pattern not in combined:
                combined[match.pattern] = match
            else:
                # Keep match with higher confidence
                if match.confidence > combined[match.pattern].confidence:
                    combined[match.pattern] = match

        # Sort by confidence
        ranked = sorted(combined.values(), key=lambda x: x.confidence, reverse=True)

        return ranked

    def _create_plan_from_pattern(
        self, pattern_info: Dict, query: str
    ) -> List[QueryStep]:
        """Create query steps from pattern information"""
        steps = []
        endpoints = pattern_info["optimal_endpoints"]

        # Add primary query steps
        if "primary" in endpoints:
            primary = endpoints["primary"]
            steps.append(
                QueryStep(
                    system=primary.get("system", "netbox"),
                    endpoint=primary["endpoint"],
                    filters=primary.get("filters", {}),
                    purpose=f"primary_{pattern_info['description']}_query",
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
                        depends_on=[step.purpose for step in steps],
                    )
                )

        # If LLM available, get suggestions for additional steps
        if self.llm:
            additional_steps = self._suggest_additional_steps(query, steps)
            steps.extend(additional_steps)

        return self.optimize_plan(steps)

    def _suggest_additional_steps(
        self, query: str, current_steps: List[QueryStep]
    ) -> List[QueryStep]:
        """Use LLM to suggest additional query steps"""
        if not self.llm:
            return []

        prompt = f"""Given:
        User query: "{query}"
        Current steps: {current_steps}
        Available endpoints: {self.semantics['query_patterns']}
        
        Would additional query steps help answer the query more completely?
        Consider:
        1. Related information that might be useful
        2. Performance metrics or status information
        3. Historical data if relevant
        
        If yes, suggest additional steps in the format:
        system: [netbox/librenms]
        endpoint: [endpoint]
        purpose: [purpose]
        depends_on: [list of dependencies]
        """

        try:
            suggestions = self.llm(prompt)
            return self._parse_step_suggestions(suggestions)
        except Exception as e:
            self.logger.error(f"Error getting step suggestions: {e}")
            return []

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
                self.logger.debug(f"System switch: {current_system} -> {step.system}")
            current_system = step.system
            optimized.append(step)

        return optimized
