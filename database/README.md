# Database Module

## Responsibilities
- PostgreSQL schema design and migrations
- Seed data for development and testing
- Elasticsearch index mappings

## Tables Planned
| Table | Purpose |
|-------|---------|
| `logs` | Raw and normalized log entries |
| `alerts` | ML-generated security alerts |
| `incidents` | Grouped alerts forming incidents |
| `users` | Analyst accounts |
| `audit_log` | System audit trail |

## TODO
- [ ] Initial schema migration (Phase 2)
- [ ] Elasticsearch index mappings (Phase 2)
- [ ] Seed data scripts (Phase 2)
- [ ] Alembic migration setup (Phase 2)
