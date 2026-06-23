# Supabase PostgreSQL Integration Guide

This guide covers the complete setup of Supabase Cloud PostgreSQL for the AI SOC Assistant backend.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Supabase Project Setup](#supabase-project-setup)
3. [Database Configuration](#database-configuration)
4. [Running Migrations](#running-migrations)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3.11+
- Supabase account (free tier works fine)
- Backend dependencies installed: `pip install -r requirements.txt`

---

## Supabase Project Setup

### 1. Create a Supabase Project

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Click **New Project**
3. Fill in the details:
   - **Name**: `ai-soc-assistant`
   - **Database Password**: Choose a strong password (save it!)
   - **Region**: Select the closest to your location
   - **Pricing Plan**: Free tier is sufficient for development

4. Wait 2-3 minutes for the project to be provisioned

### 2. Get Your Database Connection String

1. In your Supabase project dashboard, go to:
   - **Project Settings** (gear icon) → **Database**

2. Scroll to **Connection String** section

3. Choose **Connection pooling** for production or **Direct connection** for development:

   **Option A: Connection Pooling (Recommended for Production)**
   ```
   postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres
   ```

   **Option B: Direct Connection (Good for Development)**
   ```
   postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
   ```

4. Copy the connection string and replace `PASSWORD` with your database password

---

## Database Configuration

### 1. Create `.env` File

In the `backend/` directory, create a `.env` file:

```bash
cd backend
cp .env.example .env
```

### 2. Edit `.env` File

Open `.env` and update the following:

```env
# Generate secure JWT keys
# Run: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<your_generated_secret_key>
REFRESH_SECRET_KEY=<your_generated_refresh_secret_key>

# Supabase PostgreSQL Connection
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxxxxxxxxxxxx.supabase.co:5432/postgres
```

**Generate secure keys**:
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('REFRESH_SECRET_KEY=' + secrets.token_hex(32))"
```

### 3. Verify Configuration

Test database connection:
```bash
python -c "from app.database import check_connection; print('✓ Connected!' if check_connection() else '✗ Failed')"
```

---

## Running Migrations

### 1. Initialize Database Schema

Apply all migrations to create tables:

```bash
# From backend/ directory
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial, Initial database schema
```

### 2. Verify Tables in Supabase

1. Go to **Supabase Dashboard** → **Table Editor**
2. You should see these tables:
   - `users`
   - `logs`
   - `alerts`
   - `incidents`
   - `incident_alerts`
   - `ml_predictions`
   - `audit_logs`

### 3. Create Default Users

The application automatically creates default users on startup, but you can also run:

```bash
python -c "from app.database import SessionLocal; from app.services.db_auth_service import create_default_users; db = SessionLocal(); create_default_users(db); db.close(); print('✓ Default users created')"
```

**Default credentials:**
- **Analyst**: `analyst` / `analyst123`
- **Admin**: `admin` / `admin123`

⚠️ **Important**: Change these passwords in production!

---

## Verification

### 1. Run Backend Server

```bash
# From backend/ directory
uvicorn app.main:app --reload
```

### 2. Check Startup Logs

You should see:
```
INFO: Checking database connection...
INFO: [OK] Database connected
INFO: [OK] Tables initialized
INFO: [OK] Default users ready
INFO: [OK] Elasticsearch ready (if enabled)
```

### 3. Test API Endpoints

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Register a User:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user", "password": "Test123!", "role": "analyst"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst", "password": "analyst123"}'
```

**Expected response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 4. Access API Documentation

Open your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Database Schema Overview

### Tables Structure

```
users
├── id (UUID, PK)
├── username (String, Unique)
├── hashed_password (String)
├── role (Enum: analyst, admin)
├── is_active (Boolean)
├── created_at (DateTime)
└── updated_at (DateTime)

logs
├── id (Integer, PK)
├── source (String)
├── severity (Enum: info, warning, error, critical)
├── message (Text)
├── timestamp (DateTime)
├── raw (Text)
└── ingested_at (DateTime)

alerts
├── id (Integer, PK)
├── title (String)
├── severity (Enum: low, medium, high, critical)
├── source (String)
├── description (Text)
├── status (Enum: open, acknowledged, resolved)
├── created_at (DateTime)
└── updated_at (DateTime)

incidents
├── id (Integer, PK)
├── title (String)
├── description (Text)
├── status (Enum: open, in-progress, closed)
├── summary (Text)
├── assigned_to (UUID, FK → users.id)
├── created_at (DateTime)
├── resolved_at (DateTime)
└── updated_at (DateTime)

incident_alerts (Many-to-Many Junction)
├── incident_id (Integer, FK → incidents.id)
├── alert_id (Integer, FK → alerts.id)
└── created_at (DateTime)

ml_predictions
├── id (UUID, PK)
├── alert_id (Integer, FK → alerts.id)
├── model_version (String)
├── prediction (String)
├── confidence_score (Float)
└── created_at (DateTime)

audit_logs
├── id (Integer, PK)
├── user_id (UUID, FK → users.id)
├── username (String)
├── action (String)
├── resource_type (String)
├── resource_id (String)
├── details (Text)
├── ip_address (String)
└── timestamp (DateTime)
```

---

## Alembic Migration Commands

### Common Commands

**Create a new migration** (after modifying models):
```bash
alembic revision --autogenerate -m "description of changes"
```

**Apply all pending migrations**:
```bash
alembic upgrade head
```

**Rollback one migration**:
```bash
alembic downgrade -1
```

**Show current database version**:
```bash
alembic current
```

**Show migration history**:
```bash
alembic history
```

**Downgrade to specific revision**:
```bash
alembic downgrade <revision_id>
```

---

## Troubleshooting

### Connection Refused

**Symptom**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution**:
1. Verify your Supabase project is active
2. Check `DATABASE_URL` in `.env` is correct
3. Ensure password has no special characters that need URL encoding
4. Try connection pooling URL instead of direct connection

### SSL Certificate Issues

**Symptom**: `SSL SYSCALL error` or certificate verification errors

**Solution**: Append `?sslmode=require` to your connection string:
```env
DATABASE_URL=postgresql://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres?sslmode=require
```

### Password URL Encoding

If your password contains special characters, URL-encode them:
- `@` → `%40`
- `#` → `%23`
- `$` → `%24`
- `%` → `%25`
- `&` → `%26`

Or use Python to encode:
```python
from urllib.parse import quote_plus
password = "P@ssw#rd123"
encoded = quote_plus(password)
print(f"postgresql://postgres:{encoded}@db.xxx.supabase.co:5432/postgres")
```

### Enum Type Already Exists

**Symptom**: `DuplicateObject: type "alert_severity" already exists`

**Solution**: Drop and recreate enum types:
```bash
alembic downgrade base
alembic upgrade head
```

### Tables Already Exist

**Symptom**: Migration fails because tables exist

**Solution**: 
1. Check current revision: `alembic current`
2. If blank, stamp as current: `alembic stamp head`

---

## Production Checklist

- [ ] Use connection pooling URL
- [ ] Change default user passwords
- [ ] Set `DEBUG=false` in `.env`
- [ ] Use strong `SECRET_KEY` and `REFRESH_SECRET_KEY`
- [ ] Enable SSL (`sslmode=require`)
- [ ] Set up database backups in Supabase
- [ ] Monitor connection pool usage
- [ ] Set up proper logging
- [ ] Configure CORS for production domain
- [ ] Use environment-specific credentials

---

## Next Steps

1. **Test the API** using Postman or the included collection in `.github/postman_collection.json`
2. **Integrate Kafka** consumer to push logs via `POST /ingest/logs`
3. **Connect ML models** to push alerts via `POST /ingest/alerts`
4. **Integrate LLM** to generate summaries via `POST /summaries`
5. **Build frontend** to consume the API

---

## Support

For issues:
1. Check [DATABASE_README.md](./DATABASE_README.md)
2. Review [ARCHITECTURE.md](./ARCHITECTURE.md)
3. Open an issue on GitHub

**Supabase Resources**:
- [Documentation](https://supabase.com/docs)
- [Support](https://supabase.com/support)
