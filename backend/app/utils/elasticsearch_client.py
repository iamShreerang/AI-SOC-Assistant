"""Elasticsearch client configuration and initialization."""

import logging
from typing import Optional
from elasticsearch import Elasticsearch, exceptions
from app.utils.config import settings

logger = logging.getLogger(__name__)

_client: Optional[Elasticsearch] = None


def get_es_client() -> Optional[Elasticsearch]:
    """Get or create Elasticsearch client."""
    global _client
    
    if _client is None:
        try:
            _client = Elasticsearch(
                [settings.elasticsearch_url],
                verify_certs=False,  # For local development
                request_timeout=30,
            )
            
            # Test connection
            if _client.ping():
                logger.info(f"Connected to Elasticsearch at {settings.elasticsearch_url}")
            else:
                logger.warning("Elasticsearch ping failed")
                _client = None
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            _client = None
    
    return _client


def check_es_connection() -> bool:
    """Check if Elasticsearch is available."""
    client = get_es_client()
    return client is not None and client.ping()


def create_indices():
    """Create Elasticsearch indices with mappings."""
    client = get_es_client()
    if not client:
        logger.warning("Elasticsearch not available, skipping index creation")
        return
    
    # Logs index
    logs_mapping = {
        "mappings": {
            "properties": {
                "source": {"type": "keyword"},
                "severity": {"type": "keyword"},
                "message": {"type": "text"},
                "timestamp": {"type": "date"},
                "raw": {"type": "text"},
                "ingested_at": {"type": "date"},
            }
        }
    }
    
    # Alerts index
    alerts_mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "severity": {"type": "keyword"},
                "status": {"type": "keyword"},
                "source": {"type": "keyword"},
                "description": {"type": "text"},
                "created_at": {"type": "date"},
            }
        }
    }
    
    # Incidents index
    incidents_mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "status": {"type": "keyword"},
                "description": {"type": "text"},
                "alert_ids": {"type": "integer"},
                "summary": {"type": "text"},
                "created_at": {"type": "date"},
            }
        }
    }
    
    # Create indices if they don't exist
    indices = {
        "soc-logs": logs_mapping,
        "soc-alerts": alerts_mapping,
        "soc-incidents": incidents_mapping,
    }
    
    for index_name, mapping in indices.items():
        try:
            if not client.indices.exists(index=index_name):
                client.indices.create(index=index_name, body=mapping)
                logger.info(f"Created Elasticsearch index: {index_name}")
            else:
                logger.info(f"Index already exists: {index_name}")
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")


def close_es_client():
    """Close Elasticsearch client connection."""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("Closed Elasticsearch connection")
