"""Search service for full-text search across entities."""

from typing import List, Optional
from app.schemas.log import LogResponse
from app.schemas.alert import AlertResponse
from app.schemas.incident import IncidentResponse
from app.utils.config import settings

# Use Elasticsearch search if enabled
if settings.elasticsearch_enabled:
    from app.services import es_log_service, es_alert_service, es_incident_service
    
    def search_logs(query: str, limit: int = 50) -> List[LogResponse]:
        return es_log_service.search_logs(query, limit)
    
    def search_alerts(query: str, limit: int = 50) -> List[AlertResponse]:
        return es_alert_service.search_alerts(query, limit)
    
    def search_incidents(query: str, limit: int = 50) -> List[IncidentResponse]:
        return es_incident_service.search_incidents(query, limit)

else:
    # Fallback to in-memory search
    from app.services import log_service, alert_service, incident_service
    
    def search_logs(query: str, limit: int = 50) -> List[LogResponse]:
        """Search logs by message content."""
        all_logs = log_service.get_logs(limit=10000)
        query_lower = query.lower()
        
        matching_logs = [
            log for log in all_logs
            if query_lower in log.message.lower() or
               (log.raw and query_lower in log.raw.lower()) or
               query_lower in log.source.lower()
        ]
        
        return matching_logs[:limit]
    
    
    def search_alerts(query: str, limit: int = 50) -> List[AlertResponse]:
        """Search alerts by title or description."""
        all_alerts = alert_service.get_alerts(limit=10000)
        query_lower = query.lower()
        
        matching_alerts = [
            alert for alert in all_alerts
            if query_lower in alert.title.lower() or
               (alert.description and query_lower in alert.description.lower()) or
               query_lower in alert.source.lower()
        ]
        
        return matching_alerts[:limit]
    
    
    def search_incidents(query: str, limit: int = 50) -> List[IncidentResponse]:
        """Search incidents by title, description, or summary."""
        all_incidents = incident_service.get_incidents(limit=10000)
        query_lower = query.lower()
        
        matching_incidents = [
            incident for incident in all_incidents
            if query_lower in incident.title.lower() or
               (incident.description and query_lower in incident.description.lower()) or
               (incident.summary and query_lower in incident.summary.lower())
        ]
        
        return matching_incidents[:limit]


def global_search(query: str) -> dict:
    """Search across all entities."""
    return {
        "query": query,
        "logs": search_logs(query, limit=10),
        "alerts": search_alerts(query, limit=10),
        "incidents": search_incidents(query, limit=10),
    }
