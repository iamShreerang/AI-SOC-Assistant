"""Elasticsearch service for alerts with fallback to in-memory storage."""

from datetime import datetime, timezone
from typing import Optional, List

from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.schemas.enums import AlertSeverity, AlertStatus
from app.utils.elasticsearch_client import get_es_client
from app.services import alert_service as memory_service

INDEX_NAME = "soc-alerts"


def create_alert(payload: AlertCreate) -> AlertResponse:
    """Create alert in Elasticsearch with fallback to memory."""
    alert_entry = memory_service.create_alert(payload)
    
    client = get_es_client()
    if client:
        try:
            doc = {
                "id": alert_entry.id,
                "title": alert_entry.title,
                "severity": alert_entry.severity.value,
                "status": alert_entry.status.value,
                "source": alert_entry.source,
                "description": alert_entry.description,
                "created_at": alert_entry.created_at.isoformat(),
            }
            
            client.index(index=INDEX_NAME, id=alert_entry.id, document=doc)
        except Exception as e:
            print(f"Failed to index alert in Elasticsearch: {e}")
    
    return alert_entry


def get_alerts(
    limit: int = 100,
    skip: int = 0,
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    source: Optional[str] = None,
) -> List[AlertResponse]:
    """Get alerts from Elasticsearch with fallback."""
    client = get_es_client()
    
    if not client:
        return memory_service.get_alerts(limit=limit, skip=skip, severity=severity, status=status, source=source)
    
    try:
        must_clauses = []
        
        if severity:
            must_clauses.append({"term": {"severity": severity.value}})
        if status:
            must_clauses.append({"term": {"status": status.value}})
        if source:
            must_clauses.append({"wildcard": {"source": f"*{source}*"}})
        
        query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}]
            }
        }
        
        response = client.search(
            index=INDEX_NAME,
            query=query,
            from_=skip,
            size=limit,
            sort=[{"created_at": {"order": "desc"}}]
        )
        
        alerts = []
        for hit in response["hits"]["hits"]:
            source_data = hit["_source"]
            alerts.append(AlertResponse(
                id=source_data["id"],
                title=source_data["title"],
                severity=AlertSeverity(source_data["severity"]),
                status=AlertStatus(source_data["status"]),
                source=source_data["source"],
                description=source_data.get("description"),
                created_at=datetime.fromisoformat(source_data["created_at"]),
            ))
        
        return alerts
    
    except Exception as e:
        print(f"Elasticsearch query failed: {e}")
        return memory_service.get_alerts(limit=limit, skip=skip, severity=severity, status=status, source=source)


def get_alert_by_id(alert_id: int) -> Optional[AlertResponse]:
    """Get alert by ID from Elasticsearch."""
    client = get_es_client()
    
    if not client:
        return memory_service.get_alert_by_id(alert_id)
    
    try:
        response = client.get(index=INDEX_NAME, id=alert_id)
        source_data = response["_source"]
        
        return AlertResponse(
            id=source_data["id"],
            title=source_data["title"],
            severity=AlertSeverity(source_data["severity"]),
            status=AlertStatus(source_data["status"]),
            source=source_data["source"],
            description=source_data.get("description"),
            created_at=datetime.fromisoformat(source_data["created_at"]),
        )
    
    except Exception as e:
        print(f"Elasticsearch get failed: {e}")
        return memory_service.get_alert_by_id(alert_id)


def update_alert_status(alert_id: int, payload: AlertUpdate) -> Optional[AlertResponse]:
    """Update alert status in Elasticsearch."""
    # Update in memory first
    alert = memory_service.update_alert_status(alert_id, payload)
    
    if not alert:
        return None
    
    # Update in Elasticsearch
    client = get_es_client()
    if client:
        try:
            client.update(
                index=INDEX_NAME,
                id=alert_id,
                doc={"status": payload.status.value}
            )
        except Exception as e:
            print(f"Failed to update alert in Elasticsearch: {e}")
    
    return alert


def get_alerts_count(
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    source: Optional[str] = None,
) -> int:
    """Get total count of alerts."""
    client = get_es_client()
    
    if not client:
        return memory_service.get_alerts_count(severity=severity, status=status, source=source)
    
    try:
        must_clauses = []
        
        if severity:
            must_clauses.append({"term": {"severity": severity.value}})
        if status:
            must_clauses.append({"term": {"status": status.value}})
        if source:
            must_clauses.append({"wildcard": {"source": f"*{source}*"}})
        
        query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}]
            }
        }
        
        response = client.count(index=INDEX_NAME, query=query)
        return response["count"]
    
    except Exception as e:
        print(f"Elasticsearch count failed: {e}")
        return memory_service.get_alerts_count(severity=severity, status=status, source=source)


def search_alerts_direct(query: str, limit: int = 50) -> Optional[List[AlertResponse]]:
    """Search alerts using Elasticsearch directly without recursive fallback."""
    client = get_es_client()
    if not client:
        return None
    
    try:
        search_query = {
            "multi_match": {
                "query": query,
                "fields": ["title^2", "description", "source"],
                "fuzziness": "AUTO"
            }
        }
        
        response = client.search(
            index=INDEX_NAME,
            query=search_query,
            size=limit,
            sort=[{"_score": {"order": "desc"}}]
        )
        
        alerts = []
        for hit in response["hits"]["hits"]:
            source_data = hit["_source"]
            alerts.append(AlertResponse(
                id=source_data["id"],
                title=source_data["title"],
                severity=AlertSeverity(source_data["severity"]),
                status=AlertStatus(source_data["status"]),
                source=source_data["source"],
                description=source_data.get("description"),
                created_at=datetime.fromisoformat(source_data["created_at"]),
            ))
        
        return alerts
    except Exception as e:
        print(f"Elasticsearch search failed: {e}")
        return None


def search_alerts(query: str, limit: int = 50) -> List[AlertResponse]:
    """Search alerts using Elasticsearch with fallback to memory."""
    res = search_alerts_direct(query, limit)
    if res is not None:
        return res
    # Fallback to simple in-memory search
    alerts = memory_service.get_alerts(limit=1000)
    matching = [
        alert for alert in alerts
        if query.lower() in alert.title.lower() or (alert.description and query.lower() in alert.description.lower())
    ]
    return matching[:limit]
