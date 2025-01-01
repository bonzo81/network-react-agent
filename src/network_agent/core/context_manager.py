from typing import Dict, List, Optional
from datetime import datetime
import logging
from pydantic import BaseModel

class QueryRecord(BaseModel):
    """Record of a query execution"""
    query: str
    pattern: str
    success: bool
    timestamp: datetime
    results: Optional[Dict] = None
    
class QueryContext(BaseModel):
    """Context for query execution"""
    recent_queries: List[QueryRecord] = []
    active_patterns: List[str] = []
    current_focus: Optional[str] = None

class ContextManager:
    """Manages query context and history"""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.context = QueryContext()
        self.logger = logging.getLogger("ContextManager")
        
    def record_query(self, query: str, pattern: str, success: bool, results: Optional[Dict] = None):
        """Record a query execution"""
        record = QueryRecord(
            query=query,
            pattern=pattern,
            success=success,
            timestamp=datetime.now(),
            results=results
        )
        
        self.context.recent_queries.append(record)
        if len(self.context.recent_queries) > self.max_history:
            self.context.recent_queries.pop(0)
            
        self.logger.debug(f"Recorded query: {query} with pattern: {pattern}")
        
    def get_recent_context(self, limit: int = 3) -> List[QueryRecord]:
        """Get recent query records"""
        return self.context.recent_queries[-limit:]
    
    def update_active_patterns(self, patterns: List[str]):
        """Update currently active patterns"""
        self.context.active_patterns = patterns
        self.logger.debug(f"Updated active patterns: {patterns}")
        
    def set_current_focus(self, focus: str):
        """Set the current query focus"""
        self.context.current_focus = focus
        self.logger.debug(f"Set current focus: {focus}")
        
    def get_context_summary(self) -> Dict:
        """Get a summary of current context"""
        return {
            "recent_queries": [
                {
                    "query": r.query,
                    "pattern": r.pattern,
                    "success": r.success,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.get_recent_context()
            ],
            "active_patterns": self.context.active_patterns,
            "current_focus": self.context.current_focus
        }