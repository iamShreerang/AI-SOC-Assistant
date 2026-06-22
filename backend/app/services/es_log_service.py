"""Elasticsearch service for logs with fallback to in-memory storage."""

from datetime import datetime, timezone
from typing import Optional, List
from elasticsearch import exceptions as es_exceptions

from app.schemas.log import LogCreate, LogResponse
from app.schemas.enums import LogSeverity
from app.utils.elasticsearch_client import get_es_client
from app.services import log_service as memory_service

INDEX_NAME = "soc-logs"


def create_log(payload: LogCreate) -> LogResponse:
    """Create log entry in Elasticsearch with fallback to memory."""
    # Create in memory first (for ID generation)
    log_entry = memory_service.create_log(payload)
    
    # Try to index in Elasticsearch
    client = get_es_client()
    if client:
        try:
            doc = {
                "id": log_entry.id,
                "source": log_entry.source,
                "severity": log_entry.severity.value,
                "message": log_entry.message,
                "timestamp": log_entry.timestamp.isoformat() if log_entry.timestamp else None,
                "raw": log_entry.raw,
                "ingested_at": log_entry.ingested_at.isoformat(),
            }
            
            client.index(index=INDEX_NAME, id=log_entry.id, document=doc)
        except Exception as e:
            print(f"Failed to index log in Elasticsearch: {e}")
    
    return log_entry


def get_logs(
    limit: int = 100,
    skip: int = 0,
    severity: Optional[LogSeverity] = None,
    source: Optional[str] = None,
) -> List[LogResponse]:
    """Get logs from Elasticsearch with fallback to memory."""
    client = get_es_client()
    
    if not client:
        # Fallback to memory
        return memory_service.get_logs(limit=limit, skip=skip, severity=severity, source=source)
    
    try:
        # Build query
        must_clauses = []
        
        if severity:
            must_clauses.append({"term": {"severity": severity.value}})
        
        if source:
            must_clauses.append({"wildcard": {"source": f"*{source}*"}})
        
        query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}]
            }
        }
        
        # Execute search
        response = client.search(
            index=INDEX_NAME,
            query=query,
            from_=skip,
            size=limit,
            sort=[{"ingested_at": {"order": "desc"}}]
        )
        
        # Convert hits to LogResponse objects
        logs = []
        for hit in response["hits"]["hits"]:
            source_data = hit["_source"]
            logs.append(LogResponse(
                id=source_data["id"],
                source=source_data["source"],
                severity=LogSeverity(source_data["severity"]),
                message=source_data["message"],
                timestamp=datetime.fromisoformat(source_data["timestamp"]) if source_data.get("timestamp") else None,
                raw=source_data.get("raw"),
                ingested_at=datetime.fromisoformat(source_data["ingested_at"]),
            ))
        
        return logs
    
    except Exception as e:
        print(f"Elasticsearch query failed, falling back to memory: {e}")
        return memory_service.get_logs(limit=limit, skip=skip, severity=severity, source=source)


def get_log_by_id(log_id: int) -> Optional[LogResponse]:
    """Get log by ID from Elasticsearch with fallback to memory."""
    client = get_es_client()
    
    if not client:
        return memory_service.get_log_by_id(log_id)
    
    try:
        response = client.get(index=INDEX_NAME, id=log_id)
        source_data = response["_source"]
        
        return LogResponse(
            id=source_data["id"],
            source=source_data["source"],
            severity=LogSeverity(source_data["severity"]),
            message=source_data["message"],
            timestamp=datetime.fromisoformat(source_data["timestamp"]) if source_data.get("timestamp") else None,
            raw=source_data.get("raw"),
            ingested_at=datetime.fromisoformat(source_data["ingested_at"]),
        )
    
    except es_exceptions.NotFoundError:
        return None
    except Exception as e:
        print(f"Elasticsearch get failed, falling back to memory: {e}")
        return memory_service.get_log_by_id(log_id)


def get_logs_count(
    severity: Optional[LogSeverity] = None,
    source: Optional[str] = None,
) -> int:
    """Get total count of logs from Elasticsearch with fallback."""
    client = get_es_client()
    
    if not client:
        return memory_service.get_logs_count(severity=severity, source=source)
    
    try:
        must_clauses = []
        
        if severity:
            must_clauses.append({"term": {"severity": severity.value}})
        
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
        print(f"Elasticsearch count failed, falling back to memory: {e}")
        return memory_service.get_logs_count(severity=severity, source=source)


def search_logs(query: str, limit: int = 50) -> List[LogResponse]:
    """Search logs using Elasticsearch full-text search."""
    client = get_es_client()
    
    if not client:
        # Fallback to simple in-memory search
        from app.services import search_service
        return search_service.search_logs(query, limit)
    
    try:
        search_query = {
            "multi_match": {
                "query": query,
                "fields": ["message^2", "raw", "source"],
                "fuzziness": "AUTO"
            }
        }
        
        response = client.search(
            index=INDEX_NAME,
            query=search_query,
            size=limit,
            sort=[{"_score": {"order": "desc"}}]
        )
        
        logs = []
        for hit in response["hits"]["hits"]:
            source_data = hit["_source"]
            logs.append(LogResponse(
                id=source_data["id"],
                source=source_data["source"],
                severity=LogSeverity(source_data["severity"]),
                message=source_data["message"],
                timestamp=datetime.fromisoformat(source_data["timestamp"]) if source_data.get("timestamp") else None,
                raw=source_data.get("raw"),
                ingested_at=datetime.fromisoformat(source_data["ingested_at"]),
            ))
        
        return logs
    
    except Exception as e:
        print(f"Elasticsearch search failed: {e}")
        from app.services import search_service
        return search_service.search_logs(query, limit)
