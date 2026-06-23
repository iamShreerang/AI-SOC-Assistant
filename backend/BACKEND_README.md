# AI SOC Assistant Backend

FastAPI-based backend with Supabase PostgreSQL, Elasticsearch, and ML integration.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Supabase account (free tier)
- pip and virtualenv

### 1. Setup Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Unix/macOS)
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Database

**Option A: Interactive Setup (Recommended)**
```bash
python setup_supabase.py
```

**Option B: Manual Setup**
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your Supabase credentials
# Get connection string from: Supabase Dashboard → Project Settings → Database
```

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Verify Setup

```bash
python verify_supabase.py
```

### 6. Start Server

```bash
uvicorn app.main:app --reload
```

### 7. Access API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/              # API route handlers (deprecated, moved to routes/)
│   ├── models/           # SQLAlchemy ORM models
│   │   └── database.py   # Database models
│   ├── routes/           # FastAPI route handlers
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── logs.py       # Log management
│   │   ├── alerts.py     # Alert management
│   │   ├── incidents.py  # Incident tracking
│   │   ├── stats.py      # Statistics & analytics
│   │   ├── search.py     # Full-text search
│   │   ├── export.py     # Data export (CSV/JSON)
│   │   └── audit.py      # Audit trail
│   ├── schemas/          # Pydantic validation schemas
│   │   ├── enums.py      # Enum definitions
│   │   ├── auth.py       # Auth schemas
│   │   ├── log.py        # Log schemas
│   │   ├── alert.py      # Alert schemas
│   │   └── incident.py   # Incident schemas
│   ├── services/         # Business logic layer
│   │   ├── db_auth_service.py      # User management
│   │   ├── db_log_service.py       # Log CRUD
│   │   ├── db_alert_service.py     # Alert CRUD
│   │   ├── db_incident_service.py  # Incident CRUD
│   │   ├── db_stats_service.py     # Statistics
│   │   ├── db_audit_service.py     # Audit logging
│   │   ├── llm_service.py          # LLM integration
│   │   ├── search_service.py       # Search logic
│   │   └── export_service.py       # Export logic
│   ├── utils/            # Utilities
│   │   ├── config.py     # Settings management
│   │   ├── security.py   # JWT & password hashing
│   │   ├── oauth.py      # OAuth providers
│   │   └── elasticsearch_client.py
│   ├── database.py       # Database connection & session
│   └── main.py           # FastAPI application entry point
│
├── alembic/              # Database migrations
│   ├── versions/         # Migration scripts
│   │   └── 001_initial_schema.py
│   └── env.py            # Migration environment
│
├── tests/                # Test suite
│   ├── test_auth.py
│   ├── test_logs.py
│   ├── test_alerts.py
│   └── test_incidents.py
│
├── .env.example          # Environment template
├── .env                  # Your local config (create this)
├── alembic.ini           # Alembic configuration
├── requirements.txt      # Python dependencies
├── setup_supabase.py     # Interactive setup script
├── verify_supabase.py    # Database verification script
├── SUPABASE_SETUP.md     # Detailed setup guide
└── SUPABASE_IMPLEMENTATION.md  # Implementation docs
```

---

## 🔑 Environment Variables

Required variables in `.env`:

```env
# Application
APP_NAME=AI SOC Assistant
DEBUG=false

# JWT (generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=<your_secret_key>
REFRESH_SECRET_KEY=<your_refresh_key>
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Supabase PostgreSQL
DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres

# Optional: Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_ENABLED=true

# Optional: LLM (Groq)
GROQ_API_KEY=<your_groq_key>

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

---

## 🗄️ Database Schema

### Core Tables

| Table | Description |
|-------|-------------|
| `users` | Analysts and admins |
| `logs` | Security log entries |
| `alerts` | Detected anomalies |
| `incidents` | Grouped alert investigations |
| `incident_alerts` | Alert-incident relationships |
| `ml_predictions` | ML model outputs |
| `audit_logs` | Admin action tracking |

### Relationships

- Users → Incidents (assigned_to)
- Alerts ↔ Incidents (many-to-many)
- Alerts → ML Predictions (one-to-many)
- Users → Audit Logs (one-to-many)

---

## 🔐 Authentication

### Default Credentials

| Username | Password | Role |
|----------|----------|------|
| `analyst` | `analyst123` | Analyst |
| `admin` | `admin123` | Admin |

⚠️ **Change these in production!**

### API Authentication Flow

1. **Register** (optional):
   ```bash
   POST /auth/register
   {
     "username": "user1",
     "password": "Pass123!",
     "role": "analyst"
   }
   ```

2. **Login**:
   ```bash
   POST /auth/login
   {
     "username": "analyst",
     "password": "analyst123"
   }
   ```
   
   Returns:
   ```json
   {
     "access_token": "eyJhbGc...",
     "refresh_token": "eyJhbGc...",
     "token_type": "bearer"
   }
   ```

3. **Use Token**:
   ```bash
   GET /alerts
   Authorization: Bearer <access_token>
   ```

---

## 📡 API Endpoints

### Public Endpoints (No Auth)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/auth/register` | POST | Create account |
| `/auth/login` | POST | Get JWT token |
| `/ingest/logs` | POST | Kafka consumer endpoint |
| `/ingest/alerts` | POST | ML model endpoint |
| `/summaries` | POST | LLM endpoint |

### Protected Endpoints (Requires Auth)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/users/me` | GET | Current user info |
| `/logs` | GET | List logs (paginated) |
| `/logs/{id}` | GET | Get specific log |
| `/alerts` | GET | List alerts (filtered) |
| `/alerts` | POST | Create alert |
| `/alerts/{id}` | GET | Get specific alert |
| `/alerts/{id}/status` | PATCH | Update status |
| `/alerts/bulk-status` | POST | Bulk update |
| `/incidents` | GET | List incidents |
| `/incidents` | POST | Create incident |
| `/incidents/{id}` | GET | Get incident |
| `/incidents/{id}/status` | PATCH | Update status |
| `/stats/summary` | GET | Dashboard stats |
| `/stats/activity` | GET | Recent activity |
| `/stats/trends` | GET | Alert trends |
| `/search` | GET | Full-text search |
| `/export/logs` | GET | Export logs |
| `/export/alerts` | GET | Export alerts |
| `/export/incidents` | GET | Export incidents |
| `/audit` | GET | Audit logs (admin) |

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_alerts.py -v

# Run with output
pytest -s
```

---

## 🛠️ Development Commands

### Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

---

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Database Connection

```python
python -c "from app.database import check_connection; print(check_connection())"
```

### View Logs

```bash
# In development (with --reload)
# Logs appear in terminal

# In production
# Configure logging in app/main.py
```

---

## 🐋 Docker Deployment

```bash
# Build image
docker build -t ai-soc-backend .

# Run container
docker run -p 8000:8000 --env-file .env ai-soc-backend
```

---

## 📚 Documentation

- **[SUPABASE_SETUP.md](./SUPABASE_SETUP.md)** - Step-by-step Supabase setup
- **[SUPABASE_IMPLEMENTATION.md](./SUPABASE_IMPLEMENTATION.md)** - Complete implementation details
- **[DATABASE_README.md](./DATABASE_README.md)** - Database schema and operations
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture overview
- **[SECURITY.md](./SECURITY.md)** - Security considerations

---

## 🤝 Integration Points

### For Kafka Team (Ayush)
- **Endpoint**: `POST /ingest/logs`
- **Format**: See `app/schemas/log.py` - `LogCreate`
- **No Auth Required**

### For ML Team (Sayog)
- **Alert Endpoint**: `POST /ingest/alerts`
- **Format**: See `app/schemas/alert.py` - `AlertCreate`
- **Summary Endpoint**: `POST /summaries`
- **Format**: See `app/schemas/incident.py` - `LLMSummary`
- **No Auth Required**

### For Frontend Team (Aryan)
- **Base URL**: `http://localhost:8000`
- **Auth**: JWT Bearer token
- **Docs**: `http://localhost:8000/docs`
- **Postman Collection**: `.github/postman_collection.json`

---

## 🔥 Troubleshooting

### Issue: Cannot connect to database
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
python verify_supabase.py

# Verify Supabase project is active
# Visit: https://supabase.com/dashboard
```

### Issue: Tables don't exist
```bash
# Run migrations
alembic upgrade head

# Verify tables in Supabase Dashboard → Table Editor
```

### Issue: Authentication fails
```bash
# Check if default users exist
python -c "from app.database import SessionLocal; from app.services.db_auth_service import create_default_users; db = SessionLocal(); create_default_users(db); db.close()"

# Try login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"analyst","password":"analyst123"}'
```

### Issue: Port 8000 already in use
```bash
# Find process using port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Unix/macOS

# Kill process
taskkill /PID <pid> /F        # Windows
kill -9 <pid>                 # Unix/macOS

# Or use different port
uvicorn app.main:app --reload --port 8001
```

---

## 🚀 Production Deployment

1. Set `DEBUG=false` in `.env`
2. Use strong `SECRET_KEY` and `REFRESH_SECRET_KEY`
3. Change default user passwords
4. Enable SSL for database (`sslmode=require`)
5. Configure proper CORS origins
6. Set up monitoring and logging
7. Use connection pooling
8. Enable rate limiting
9. Set up automated backups

---

## 📝 License

GNU Affero General Public License v3.0 - see [LICENSE](../LICENSE)

---

## 👥 Team

- **Shreerang Kolhe** - Backend + Integration
- **Sayog Shendre** - AI/ML
- **Ayush Dandge** - Big Data Pipeline
- **Aryan Dandge** - Frontend
- **Sumiran Bagul** - Database

---

**Need Help?** Check [SUPABASE_SETUP.md](./SUPABASE_SETUP.md) or open an issue on GitHub.
