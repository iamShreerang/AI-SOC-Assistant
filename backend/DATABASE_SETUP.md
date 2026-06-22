# Database Setup Guide - Supabase PostgreSQL Integration

## Overview

The AI SOC Assistant backend now uses **Supabase PostgreSQL** as the primary database, replacing in-memory storage. This guide covers setup, migration, and deployment.

---

## 1. Prerequisites

- Python 3.11+
- Supabase account (free tier available)
- pip packages: `SQLAlchemy>=2.0.0`, `psycopg2-binary==2.9.9`, `alembic>=1.13.0`

---

## 2. Supabase Setup

### Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up / Log in
3. Click **"New Project"**
4. Fill in:
   - **Name**: `ai-soc-assistant`
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your location
5. Wait 2-3 minutes for provisioning

### Step 2: Get Connection String

1. Go to **Project Settings** → **Database**
2. Scroll to **Connection String** section
3. Select **URI** tab
4. Copy the connection string (format: `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`)
5. Replace `[YOUR-PASSWORD]` with your actual database password

---

## 3. Backend Configuration

### Update `.env` File

```bash
# Database - Supabase PostgreSQL
DATABASE_URL=postgresql://postgres:your_password@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
```

**Security**: Never commit `.env` to git! Use `.env.example` as template.

---

## 4. Database Schema

### Tables Created

| Table | Purpose |
|---|---|
| `users` | Authentication & authorization |
| `logs` | Security log entries |
| `alerts` | Security alerts from ML/rules |
| `incidents` | Grouped investigations |
| `incident_alerts` | Many-to-many relationship |
| `ml_predictions` | ML model predictions |
| `audit_logs` | Administrative action tracking |

### Entity Relationships

```
users (1) ──< (N) incidents
          └──< (N) audit_logs

alerts (N) ──< (N) incidents [via incident_alerts]
       (1) ──< (N) ml_predictions

logs [standalone]
```

---

## 5. Database Migration

### Option A: Automatic Setup (Development)

The backend automatically creates tables on startup:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

**Output:**
```
[OK] Database connected
[OK] Tables initialized
[OK] Default users ready
```

### Option B: Alembic Migrations (Production Recommended)

```bash
cd backend

# Run migration
alembic upgrade head

# Verify migration
alembic current

# Rollback if needed
alembic downgrade -1
```

**Generate New Migration:**
```bash
# After modifying models in app/models/database.py
alembic revision --autogenerate -m "Add new column"
alembic upgrade head
```

---

## 6. Default Users

The system creates two default users on first startup:

| Username | Password | Role |
|---|---|---|
| `analyst` | `analyst123` | analyst |
| `admin` | `admin123` | admin |

**⚠️ CHANGE THESE PASSWORDS IN PRODUCTION!**

---

## 7. Code Architecture

### Service Layer (Database-backed)

All services now accept a `db: Session` parameter:

```python
from sqlalchemy.orm import Session
from app.database import get_db

@router.get("/logs/")
async def get_logs(db: Session = Depends(get_db)):
    logs = db_log_service.get_logs(db, limit=100)
    return {"logs": logs}
```

### New Database Services

| File | Purpose |
|---|---|
| `app/services/db_auth_service.py` | User authentication/management |
| `app/services/db_log_service.py` | Log CRUD operations |
| `app/services/db_alert_service.py` | Alert management |
| `app/services/db_incident_service.py` | Incident tracking |
| `app/services/db_audit_service.py` | Audit logging |
| `app/services/db_stats_service.py` | Dashboard statistics |

### Database Models

Located in `app/models/database.py`:
- Uses SQLAlchemy ORM
- Includes relationships and indexes
- Enum types for type safety

---

## 8. API Changes

### Routes Now Use Database Dependency

**Before (in-memory):**
```python
from app.services import log_service

@router.get("/logs/")
async def get_logs():
    return log_service.get_logs()
```

**After (database):**
```python
from app.database import get_db
from app.services import db_log_service

@router.get("/logs/")
async def get_logs(db: Session = Depends(get_db)):
    return db_log_service.get_logs(db)
```

### Response Format (Unchanged)

API responses remain the same for backward compatibility:

```json
{
  "logs": [...],
  "total": 100,
  "skip": 0,
  "limit": 100
}
```

---

## 9. Testing

### Run Tests with Database

```bash
cd backend
pytest tests/ -v
```

**Note**: Tests will use the `DATABASE_URL` from `.env`. Consider using a separate test database.

### Test Database Setup

Create `.env.test`:
```bash
DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres_test
```

---

## 10. Performance Optimization

### Connection Pooling

Configured in `app/database.py`:
```python
engine = create_engine(
    settings.database_url,
    pool_size=10,        # 10 connections in pool
    max_overflow=20,     # Max 30 total connections
    pool_pre_ping=True,  # Check connection health
    pool_recycle=3600,   # Recycle after 1 hour
)
```

### Indexes

All foreign keys and frequently queried columns have indexes for fast lookups.

---

## 11. Troubleshooting

### Connection Refused Error

**Issue**: `psycopg2.OperationalError: connection refused`

**Solutions**:
1. Check `DATABASE_URL` in `.env`
2. Verify Supabase project is running
3. Check firewall/network restrictions
4. Ensure password is correct

### Migration Conflicts

**Issue**: `alembic.util.exc.CommandError: Target database is not up to date`

**Solution**:
```bash
# Check current version
alembic current

# Stamp current version (if tables already exist)
alembic stamp head

# Or reset and re-run
alembic downgrade base
alembic upgrade head
```

### Slow Queries

**Solution**: Check query execution in logs:
```python
# In .env
DEBUG=true
```

This enables SQL query logging.

---

## 12. Production Deployment

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
SECRET_KEY=<generate-with-openssl-rand-hex-32>
REFRESH_SECRET_KEY=<generate-with-openssl-rand-hex-32>

# Optional
DEBUG=false
ELASTICSEARCH_ENABLED=true
```

### Pre-deployment Checklist

- [ ] Change default user passwords
- [ ] Set strong `SECRET_KEY` and `REFRESH_SECRET_KEY`
- [ ] Run Alembic migrations
- [ ] Enable SSL for database connection
- [ ] Set up database backups in Supabase
- [ ] Configure CORS for production frontend
- [ ] Test all endpoints with production database

### Database Backup

Supabase provides automatic daily backups. To manual backup:

1. Go to Supabase Dashboard → **Database** → **Backups**
2. Click **"Download Backup"**

---

## 13. Migration from In-Memory to Database

The backend maintains backward compatibility. No changes needed for:
- API endpoints
- Request/response formats
- Authentication flow

**What Changed**:
- Data is now persisted across restarts
- Supports concurrent users
- Transaction safety
- Relational integrity

---

## 14. Monitoring

### Database Health Check

```bash
curl http://localhost:8000/health
```

### View Active Connections

In Supabase Dashboard → **Database** → **Connection Pooling**

---

## 15. Next Steps

1. Set up Supabase project
2. Update `.env` with `DATABASE_URL`
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `alembic upgrade head`
5. Start backend: `uvicorn app.main:app --reload`
6. Test endpoints: http://localhost:8000/docs
7. Change default passwords!

---

## Support

For issues, check:
- [Supabase Documentation](https://supabase.com/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- Project README: `backend/README.md`
