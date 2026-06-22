# AI SOC Assistant - System Architecture with Supabase PostgreSQL

## 🏗️ Complete System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                              │
│                    (React Dashboard - Port 3000)                    │
│                                                                      │
│  • Real-time monitoring dashboard                                   │
│  • Alert management interface                                       │
│  • Incident tracking                                                │
│  • User authentication UI                                           │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ HTTP/REST API
                               │ (All 41 endpoints)
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                      BACKEND API LAYER                              │
│                   (FastAPI - Port 8000)                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    API ROUTES (41 endpoints)                │   │
│  │                                                             │   │
│  │  • /auth/* (13)        Authentication & user management    │   │
│  │  • /logs/* (4)         Log ingestion & retrieval           │   │
│  │  • /alerts/* (6)       Alert management                    │   │
│  │  • /incidents/* (5)    Incident tracking                   │   │
│  │  • /stats/* (4)        Dashboard analytics                 │   │
│  │  • /search/* (4)       Full-text search                    │   │
│  │  • /export/* (3)       Data export (CSV/JSON)              │   │
│  │  • /audit/* (1)        Audit trail                         │   │
│  │  • /health (1)         Health check                        │   │
│  └────────────────────────────────────────────────────────────┘   │
│                               │                                     │
│                               ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                  SERVICE LAYER (Database-Backed)            │   │
│  │                                                             │   │
│  │  • db_auth_service.py      User authentication & mgmt      │   │
│  │  • db_log_service.py       Log CRUD operations             │   │
│  │  • db_alert_service.py     Alert management                │   │
│  │  • db_incident_service.py  Incident tracking               │   │
│  │  • db_audit_service.py     Audit logging                   │   │
│  │  • db_stats_service.py     Statistics & analytics          │   │
│  └────────────────────────────────────────────────────────────┘   │
│                               │                                     │
│                               ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                    ORM LAYER (SQLAlchemy)                   │   │
│  │                                                             │   │
│  │  • User model          UUID, username, role, password      │   │
│  │  • Log model           id, source, severity, message       │   │
│  │  • Alert model         id, title, severity, status         │   │
│  │  • Incident model      id, title, summary, assigned_to     │   │
│  │  • IncidentAlert       Many-to-many junction table         │   │
│  │  • MLPrediction        id, alert_id, prediction, score     │   │
│  │  • AuditLog            id, user_id, action, timestamp      │   │
│  └────────────────────────────────────────────────────────────┘   │
│                               │                                     │
│                               ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │            DATABASE CONNECTION (app/database.py)            │   │
│  │                                                             │   │
│  │  • SQLAlchemy engine with connection pooling               │   │
│  │  • Session management (SessionLocal)                       │   │
│  │  • FastAPI dependency injection (get_db)                   │   │
│  │  • Pool size: 10 base + 20 overflow                        │   │
│  │  • Health checks and error handling                        │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ PostgreSQL Protocol (SSL/TLS)
                               │ Connection String from .env
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                    SUPABASE POSTGRESQL                              │
│                   (Cloud Database - Port 5432)                      │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                      DATABASE TABLES                        │   │
│  │                                                             │   │
│  │  • users (UUID primary key)                                │   │
│  │    ├─> incidents (assigned_to foreign key)                 │   │
│  │    └─> audit_logs (user_id foreign key)                    │   │
│  │                                                             │   │
│  │  • logs (auto-increment id)                                │   │
│  │    - Indexed: source, severity, ingested_at                │   │
│  │                                                             │   │
│  │  • alerts (auto-increment id)                              │   │
│  │    ├─> ml_predictions (alert_id foreign key)               │   │
│  │    ├─> incident_alerts (many-to-many junction)             │   │
│  │    - Indexed: severity, status, source, created_at         │   │
│  │                                                             │   │
│  │  • incidents (auto-increment id)                           │   │
│  │    ├─> incident_alerts (many-to-many junction)             │   │
│  │    - Indexed: status, created_at                           │   │
│  │                                                             │   │
│  │  • incident_alerts (junction table)                        │   │
│  │    - Cascade deletes on both sides                         │   │
│  │                                                             │   │
│  │  • ml_predictions (UUID primary key)                       │   │
│  │    - Indexed: alert_id, created_at                         │   │
│  │                                                             │   │
│  │  • audit_logs (auto-increment id)                          │   │
│  │    - Indexed: username, action, resource_type, timestamp   │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                      FEATURES                               │   │
│  │                                                             │   │
│  │  • Auto-scaling (Supabase managed)                         │   │
│  │  • Automatic backups (daily)                               │   │
│  │  • Connection pooling                                      │   │
│  │  • SSL/TLS encryption                                      │   │
│  │  • Row-level security (optional)                           │   │
│  │  • Real-time subscriptions (optional)                      │   │
│  │  • PostgREST API (optional)                                │   │
│  └────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 External Integrations (Unchanged)

```
┌─────────────────────────────────────────────────────────────────┐
│                    KAFKA CONSUMER (Port 9092)                    │
│                     (Big Data Pipeline)                          │
│                                                                   │
│  • Consumes raw logs from Kafka topic                           │
│  • Parses and normalizes log entries                            │
│  • Sends to: POST /ingest/logs (no auth)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API                                 │
│                   POST /ingest/logs                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ML ANOMALY DETECTOR                            │
│                  (Machine Learning Module)                       │
│                                                                   │
│  • Analyzes logs for anomalies                                  │
│  • Generates alerts based on ML models                          │
│  • Sends to: POST /ingest/alerts (no auth)                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API                                 │
│                   POST /ingest/alerts                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LLM SUMMARIZER                              │
│                  (Groq API Integration)                          │
│                                                                   │
│  • Receives incident details                                    │
│  • Generates narrative summary using LLM                        │
│  • Sends to: POST /summaries (no auth)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API                                 │
│                     POST /summaries                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Data Flow Examples

### Example 1: Log Ingestion Flow

```
Firewall → Kafka → Consumer → POST /ingest/logs → db_log_service 
                                                         │
                                                         ▼
                                                   SQLAlchemy ORM
                                                         │
                                                         ▼
                                                  Supabase PostgreSQL
                                                         │
                                                         ▼
                                                  logs table (INSERT)
```

### Example 2: Alert Creation & ML Prediction Flow

```
ML Detector → POST /ingest/alerts → db_alert_service → SQLAlchemy
                                                             │
                                                             ▼
                                                    Supabase PostgreSQL
                                                             │
                                                             ├─> alerts table
                                                             └─> ml_predictions table
```

### Example 3: Incident Management Flow

```
Analyst → Dashboard → POST /incidents → db_incident_service
                                              │
                                              ▼
                                        SQLAlchemy ORM
                                              │
                                              ▼
                                     Supabase PostgreSQL
                                              │
                                              ├─> incidents table
                                              └─> incident_alerts table (junction)
```

### Example 4: Authentication Flow

```
User → Login Request → POST /auth/login → db_auth_service
                                                │
                                                ▼
                                          Query users table
                                                │
                                                ▼
                                        Verify password (bcrypt)
                                                │
                                                ▼
                                        Generate JWT token
                                                │
                                                ▼
                                       Return access_token
```

---

## 📊 Database Entity Relationships

```
┌──────────────┐
│    users     │
│  (UUID id)   │──────┐
└──────────────┘      │
       │              │
       │ 1:N          │ 1:N
       │              │
       ▼              ▼
┌──────────────┐  ┌──────────────┐
│  incidents   │  │  audit_logs  │
│  (int id)    │  │  (int id)    │
└──────────────┘  └──────────────┘
       │
       │ N:M via incident_alerts
       │
       ▼
┌──────────────┐      ┌──────────────────┐
│   alerts     │──────│ incident_alerts  │
│  (int id)    │      │  (junction)      │
└──────────────┘      └──────────────────┘
       │
       │ 1:N
       │
       ▼
┌──────────────┐
│ml_predictions│
│  (UUID id)   │
└──────────────┘

┌──────────────┐
│    logs      │
│  (int id)    │
│ (standalone) │
└──────────────┘
```

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                           │
└─────────────────────────────────────────────────────────────┘

Layer 1: Network Security
├─ SSL/TLS encryption (Supabase managed)
├─ HTTPS only for API
└─ IP allowlist (optional in Supabase)

Layer 2: Authentication
├─ JWT bearer tokens (15 min expiry)
├─ Refresh tokens (7 day expiry)
├─ OAuth2 integration (Google, GitHub)
└─ Bcrypt password hashing (12 rounds)

Layer 3: Authorization
├─ Role-based access control (analyst, admin)
├─ Route-level protection
└─ Resource-level permissions

Layer 4: Data Security
├─ SQL injection prevention (SQLAlchemy ORM)
├─ Input validation (Pydantic schemas)
├─ Password strength requirements
└─ Sensitive data hashing

Layer 5: Audit Trail
├─ All admin actions logged
├─ User activity tracking
├─ IP address logging
└─ Timestamp records
```

---

## 📈 Performance Optimizations

```
┌─────────────────────────────────────────────────────────────┐
│                 PERFORMANCE FEATURES                         │
└─────────────────────────────────────────────────────────────┘

Database Level:
├─ 24 indexes on frequently queried columns
├─ Foreign key indexes for joins
├─ Composite indexes where applicable
└─ Enum types for type safety and storage efficiency

Connection Level:
├─ Connection pooling (10 base connections)
├─ Pool overflow (20 additional connections)
├─ Connection pre-ping (health checks)
├─ Connection recycling (1 hour)
└─ Lazy connection initialization

Query Level:
├─ SQLAlchemy ORM query optimization
├─ Eager/lazy loading strategies
├─ Pagination for large result sets
└─ Count queries optimized separately

Application Level:
├─ FastAPI async support
├─ Response caching (where appropriate)
├─ Batch operations for bulk updates
└─ Transaction management
```

---

## 🔄 Migration & Deployment Strategy

```
Development:
├─ Tables auto-created on startup
├─ Default users initialized
├─ Debug mode enabled
└─ Local .env configuration

Testing:
├─ Separate test database
├─ Automated test suite (55 tests)
├─ CI/CD integration
└─ Mock data generation

Staging:
├─ Alembic migrations
├─ Production-like configuration
├─ Performance testing
└─ Security audits

Production:
├─ Alembic migrations only
├─ Connection pooling enabled
├─ Monitoring and alerting
├─ Automated backups
└─ Disaster recovery plan
```

---

## 📍 Technology Stack Summary

```
┌──────────────────────────────────────────────────────────────┐
│                   TECHNOLOGY STACK                            │
└──────────────────────────────────────────────────────────────┘

Frontend:
└─ React + TypeScript (Port 3000)

Backend:
├─ FastAPI 0.115+ (Python 3.11+)
├─ Pydantic v2 (validation)
├─ SQLAlchemy 2.0+ (ORM)
├─ Alembic (migrations)
├─ python-jose (JWT)
├─ bcrypt (password hashing)
├─ uvicorn (ASGI server)
└─ slowapi (rate limiting)

Database:
├─ Supabase PostgreSQL (managed)
├─ psycopg2-binary (driver)
└─ Connection pooling (QueuePool)

Integration:
├─ Apache Kafka (log ingestion)
├─ Apache Spark (stream processing)
├─ Elasticsearch (optional search)
└─ Groq API (LLM summaries)

Development:
├─ pytest (testing)
├─ python-dotenv (config)
└─ Git (version control)
```

---

## 🎯 Architecture Benefits

✅ **Separation of Concerns**: Clean layers (API → Service → ORM → Database)  
✅ **Scalability**: Connection pooling + Supabase auto-scaling  
✅ **Maintainability**: Type-safe models + versioned migrations  
✅ **Security**: Multiple layers of protection  
✅ **Performance**: Indexed queries + connection reuse  
✅ **Testability**: Dependency injection + mock support  
✅ **Reliability**: ACID transactions + automatic backups  
✅ **Flexibility**: Easy to add new features/endpoints  

---

**Architecture Status: PRODUCTION-READY ✅**
