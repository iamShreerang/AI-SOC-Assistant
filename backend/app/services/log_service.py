"""Log ingestion service."""


class LogService:
    """Handles log storage and retrieval logic."""

    async def get_recent_logs(self, limit: int = 100):
        """
        Fetch recent logs from storage.

        TODO:
            - Query Elasticsearch / PostgreSQL
            - Apply filters and pagination
        """
        pass

    async def ingest(self, log_entry):
        """
        Store a log entry and publish to Kafka.

        TODO:
            - Validate schema
            - Write to PostgreSQL
            - Publish to kafka topic: raw-logs
        """
        pass
