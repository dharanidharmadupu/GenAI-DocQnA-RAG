"""Metrics tracking for the application."""

from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json


@dataclass
class QueryMetrics:
    """Metrics for a single query."""
    
    query: str
    timestamp: datetime = field(default_factory=datetime.now)
    retrieval_time: float = 0.0
    generation_time: float = 0.0
    total_time: float = 0.0
    num_results: int = 0
    tokens_used: int = 0
    relevance_score: Optional[float] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "timestamp": self.timestamp.isoformat(),
            "retrieval_time": self.retrieval_time,
            "generation_time": self.generation_time,
            "total_time": self.total_time,
            "num_results": self.num_results,
            "tokens_used": self.tokens_used,
            "relevance_score": self.relevance_score,
            "error": self.error
        }


class MetricsCollector:
    """Collect and aggregate application metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.queries: List[QueryMetrics] = []
        self.total_queries = 0
        self.total_tokens = 0
        self.total_errors = 0
    
    def record_query(self, metrics: QueryMetrics) -> None:
        """
        Record metrics for a query.
        
        Args:
            metrics: Query metrics to record
        """
        self.queries.append(metrics)
        self.total_queries += 1
        self.total_tokens += metrics.tokens_used
        
        if metrics.error:
            self.total_errors += 1
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics.
        
        Returns:
            Dictionary with summary metrics
        """
        if not self.queries:
            return {
                "total_queries": 0,
                "total_tokens": 0,
                "total_errors": 0,
                "avg_latency": 0.0,
                "avg_tokens_per_query": 0.0,
                "error_rate": 0.0
            }
        
        total_time = sum(q.total_time for q in self.queries)
        avg_latency = total_time / len(self.queries)
        avg_tokens = self.total_tokens / len(self.queries)
        error_rate = self.total_errors / len(self.queries)
        
        return {
            "total_queries": self.total_queries,
            "total_tokens": self.total_tokens,
            "total_errors": self.total_errors,
            "avg_latency": round(avg_latency, 2),
            "avg_tokens_per_query": round(avg_tokens, 2),
            "error_rate": round(error_rate * 100, 2)
        }
    
    def get_recent_queries(self, n: int = 10) -> List[Dict]:
        """
        Get recent queries.
        
        Args:
            n: Number of recent queries to return
        
        Returns:
            List of recent query metrics
        """
        return [q.to_dict() for q in self.queries[-n:]]
    
    def export_to_json(self, filepath: str) -> None:
        """
        Export metrics to JSON file.
        
        Args:
            filepath: Path to output file
        """
        data = {
            "summary": self.get_summary(),
            "queries": [q.to_dict() for q in self.queries]
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.queries.clear()
        self.total_queries = 0
        self.total_tokens = 0
        self.total_errors = 0


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get global metrics collector instance.
    
    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
