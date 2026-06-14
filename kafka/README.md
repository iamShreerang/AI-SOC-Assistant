# Kafka Module

## Responsibilities
- Log producer: ship raw security logs to Kafka topics
- Log consumer: consume and forward to Spark

## Topics
| Topic | Purpose |
|-------|---------|
| `raw-logs` | Raw inbound security logs |
| `processed-logs` | Spark-processed log events |
| `alerts` | ML-generated alert events |

## TODO
- [ ] Implement log producer (Phase 3)
- [ ] Implement log consumer (Phase 3)
- [ ] Configure topic partitions and retention
