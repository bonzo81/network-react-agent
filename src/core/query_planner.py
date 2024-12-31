from typing import List, Dict, Optional
from pydantic import BaseModel

class QueryStep(BaseModel):
    system: str
    endpoint: str
    filters: Dict
    purpose: str

class QueryPlanner:
    def __init__(self, semantic_mappings: Dict):
        self.semantics = semantic_mappings
    
    def create_plan(self, query: str) -> List[QueryStep]:
        # Match query against patterns
        pattern = self._match_pattern(query)
        if not pattern:
            return []
        
        # Get optimal endpoints
        endpoints = self.semantics['query_patterns'][pattern]['optimal_endpoints']
        
        # Create steps
        steps = []
        for endpoint_info in endpoints.values():
            steps.append(
                QueryStep(
                    system=endpoint_info.get('system', 'netbox'),
                    endpoint=endpoint_info['endpoint'],
                    filters=endpoint_info.get('filters', {}),
                    purpose=endpoint_info.get('purpose', 'query')
                )
            )
        
        return steps
    
    def _match_pattern(self, query: str) -> Optional[str]:
        for pattern, info in self.semantics['query_patterns'].items():
            if any(keyword in query.lower() for keyword in info['keywords']):
                return pattern
        return None