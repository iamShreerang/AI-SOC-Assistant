"""Elasticsearch service for incidents with fallback to in-memory storage."""

from datetime import datetime, timezone
from typing import Optional, List

from app.schemas.incident import IncidentCreate, IncidentResponse
from app.schemas.enums import IncidentStatus
from app.utils.elasticsearch_client import get_es_client
from app.services import incident_service as memory_service

INDEX_NAME = "soc-incidents"


def create_incident(payload: IncidentCreate) -> IncidentResponse:
    """Create incident in Elasticsearch with fallback to memory."""
    incident_entry = memory_service.create_incident(payload)
    
    client = get_es_client()
    if client:
        try:
            doc = {
                "id": incident_entry.id,
                "title": incident_entry.title,
                "status": incident_entry.status.value,
                "description": incident_entry.description,
                "alert_ids": incident_entry.alert_ids,
                "summary": incident_entry.summary,
                "created_at": incident_entry.created_at.isoformat(),
            }
            
            client.index(index=INDEX_NAME, id=incident_entry.id, document=doc)
        except Exception as e:
            print(f"Failed to index incident in Elasticsearch: {e}")
    
    return incident_entry


def get_incidents(
    limit: int = 100,
    skip: int = 0,
    status: Optional[IncidentStatus] = None,
) -> List[IncidentResponse]:
    """Get incidents from Elasticsearch with fallback."""
    client = get_es_client()
    
    if not client:
        return memory_service.get_incidents(limit=limit, skip=skip, status=status)
    
    try:
        must_clauses = []
        
        if status:
            must_clauses.append({"term": {"status": status.value}})
        
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
        
        incidents = []
        for hit in response["hits"]["hits"]:
            source_data = hit["_source"]
            incidents.append(IncidentResponse(
                id=source_data["id"],
                title=source_data["title"],
                status=IncidentStatus(source_data["status"]),
                description=source_data.get("description"),
                alert_ids=source_data.get("alert_ids", []),
                summary=source_data.get("summary"),
                created_at=datetime.fromisoformat(source_data["created_at"]),
            ))
        
        return incidents
    
    except Exception as e:
        print(f"Elasticsearch query failed: {e}")
        return memory_service.get_incidents(limit=limit, skip=skip, status=status)


def get_incident_by_id(incident_id: int) -> Optional[IncidentResponse]:
    """Get incident by ID from Elasticsearch."""
    client = get_es_client()
    
    if not client:
        return memory_service.get_incident_by_id(incident_id)
    
    try:
        response = client.get(index=INDEX_NAME, id=incident_id)
        source_data = response["_source"]
        
        return IncidentResponse(
            id=source_data["id"],
            title=source_data["title"],
            status=IncidentStatus(source_data["status"]),
            description=source_data.get("description"),
            alert_ids=source_data.get("alert_ids", []),
            summary=source_data.get("summary"),
            created_at=datetime.fromisoformat(source_data["created_at"]),
        )
    
    except Exception as e:
        print(f"Elasticsearch get failed: {e}")
        return memory_service.get_incident_by_id(incident_id)


def attach_summary(incident_id: int, summary: str) -> Optional[IncidentResponse]:
    """Attach summary to incident in Elasticsearch."""
    # Update in memory first
    incident = memory_service.attach_summary(incident_id, summary)
    
    if not incident:
        return None
    
    # Update in Elasticsearch
    client = get_es_client()
    if client:
        try:
            client.update(
                index=INDEX_NAME,
                id=incident_id,
                doc={"summary": summary}
            )
        except Exception as e:
            print(f"Failed to update incident in Elasticsearch: {e}")
    
    return incident


def update_incident_status(incident_id: int, status: IncidentStatus) -> Optional[IncidentResponse]:
    """Update incident status in Elasticsearch."""
    # Update in memory first
    incident = memory_service.update_incident_status(incident_id, status)
    
    if not incident:
        return None
    
    # Update in Elasticsearch
    client = get_es_client()
    if client:
        try:
            client.update(
                index=INDEX_NAME,
                id=incident_id,
                doc={"status": status.value}
            )
        except Exception as e:
            print(f"Failed to update incident in Elasticsearch: {e}")
    
    return incident


def get_incidents_count(status: Optional[IncidentStatus] = None) -> int:
    """Get total count of incidents."""
    client = get_es_client()
    
    if not client:
        return memory_service.get_incidents_count(status=status)
    
    try:
        must_clauses = []
        
        if status:
            must_clauses.append({"term": {"status": status.value}})
        
        query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}]
            }
        }
        
        response = client.count(index=INDEX_NAME, query=query)
        return response["count"]
    
    except Exception as e:
        print(f"Elasticsearch count failed: {e}")
        return memory_service.get_incidents_count(status=status)


def search_incidents(query: str, limit: int = 50) -> List[IncidentResponse]:
    """Search incidents using Elasticsearch."""
    client = get_es_client()
    
    if not client:
        from app.services import search_service
        return search_service.search_incidents(query, limit)
    
    try:
        search_query = {
            "multi_match": {
                "query": query,
                "fields": ["title^2", "description", "summary"],
                "fuzziness": "AUTO"
            }
        }
        
        response = client.search(
            index=INDEX_NAME,
            query=search_query,
            size=limit,
            sort=[{"_score": {"order": "desc"}}]
        )
        
        incidents = []
        for hit in response["hits"]["hits"]:
            source_data = hit["_source"]
            incidents.append(IncidentResponse(
                id=source_data["id"],
                title=source_data["title"],
                status=IncidentStatus(source_data["status"]),
                description=source_data.get("description"),
                alert_ids=source_data.get("alert_ids", []),
                summary=source_data.get("summary"),
                created_at=datetime.fromisoformat(source_data["created_at"]),
            ))
        
        return incidents
    
    except Exception as e:
        print(f"Elasticsearch search failed: {e}")
        from app.services import search_service
        return search_service.search_incidents(query, limit)
