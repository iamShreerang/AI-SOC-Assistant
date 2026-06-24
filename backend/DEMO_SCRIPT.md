# Live Demonstration Script
## Backend Mid-Evaluation Demo

---

## ⚙️ Pre-Demo Setup (Do this BEFORE evaluation)

```bash
# 1. Navigate to backend
cd backend

# 2. Activate virtual environment
venv\Scripts\activate

# 3. Start server
uvicorn app.main:app --reload

# 4. Verify server is running
# Open browser: http://localhost:8000/health
# Should see: {"status": "healthy", ...}

# 5. Open Swagger UI
# Browser: http://localhost:8000/docs

# 6. Open code editor with these files:
# - app/main.py
# - app/routes/alerts.py
# - app/services/db_alert_service.py
# - app/models/database.py
```

✅ Server running on: http://localhost:8000
✅ API docs available at: http://localhost:8000/docs

---

## 🎬 Demo Part 1: Introduction (1 minute)

### What to Say:
"Hello, I'm Shreerang Kolhe, Backend + Integration Lead for the AI SOC Assistant project. I've built the FastAPI backend that serves as the central hub for our security operations platform. Let me show you what I've implemented."

### What to Show:
1. Open `app/main.py` in code editor
2. Scroll to show router includes (lines 180-190)
3. Point out:
   - "Here's the main FastAPI application"
   - "These are all the routers I've implemented"
   - "Notice the separation between authenticated and integration endpoints"

```python
# Point to these lines
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(logs_router, prefix="/logs", tags=["Logs"])
app.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
app.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])

# Internal integration endpoints (no auth)
app.include_router(logs_ingest_router, tags=["Ingest"])
app.include_router(alerts_ingest_router, tags=["Ingest"])
app.include_router(summaries_router, tags=["Ingest"])
```

---

## 🎬 Demo Part 2: API Documentation (1 minute)

### What to Say:
"FastAPI automatically generates interactive API documentation. This makes it easy for team members to understand and test the endpoints."

### What to Show:
1. Switch to browser with http://localhost:8000/docs
2. Scroll through the endpoint groups:
   - Health
   - Auth
   - Logs
   - Alerts
   - Incidents
   - Ingest (highlight: "no auth required")
   - Statistics
   - Search
   - Export
   - Audit

3. Point out:
   - "35+ endpoints organized by functionality"
   - "Each endpoint has request/response schemas"
   - "You can test endpoints right here"

---

## 🎬 Demo Part 3: Authentication Flow (2 minutes)

### What to Say:
"Let me demonstrate the security layer. I've implemented JWT-based authentication with role-based access control."

### Steps:

#### Step 1: Login
1. In Swagger UI, find `POST /auth/login`
2. Click "Try it out"
3. Enter credentials:
```json
{
  "username": "analyst",
  "password": "analyst123"
}
```
4. Click "Execute"
5. Show the response:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### Step 2: Authorize
1. Copy the `access_token` value (without quotes)
2. Click the green "Authorize" button at the top
3. Paste token in the format: `Bearer <token>` (or just the token)
4. Click "Authorize"
5. Point out: "Now all protected endpoints will include this token"

#### Step 3: Get Current User
1. Find `GET /auth/users/me`
2. Click "Try it out"
3. Click "Execute"
4. Show response:
```json
{
  "id": 1,
  "username": "analyst",
  "role": "analyst",
  "created_at": "2024-..."
}
```

### What to Say:
"The token is valid for 15 minutes. After that, the user can use the refresh token to get a new access token without logging in again. This provides security without sacrificing user experience."

---

## 🎬 Demo Part 4: CRUD Operations - Alerts (2 minutes)

### What to Say:
"Let me demonstrate the core functionality - managing security alerts. This is what a SOC analyst would use daily."

#### Step 1: Create Alert
1. Find `POST /alerts`
2. Click "Try it out"
3. Enter:
```json
{
  "title": "Suspicious Login Attempt",
  "severity": "high",
  "source": "firewall",
  "message": "Multiple failed SSH login attempts detected from IP 192.168.1.100",
  "detection_method": "signature"
}
```
4. Click "Execute"
5. Show response with created alert and ID
6. Point out: "Alert created with ID: 1, status is 'open' by default"

#### Step 2: List Alerts
1. Find `GET /alerts`
2. Click "Try it out"
3. Show filter options:
   - severity
   - status
   - source
   - skip/limit (pagination)
4. Click "Execute"
5. Show the list with our newly created alert

#### Step 3: Update Alert Status
1. Find `PATCH /alerts/{id}/status`
2. Click "Try it out"
3. Enter alert_id: `1`
4. Enter:
```json
{
  "status": "acknowledged"
}
```
5. Click "Execute"
6. Show updated alert

### What to Say:
"Notice the status workflow: open → acknowledged → resolved. This matches real-world SOC operations where analysts triage and resolve alerts."

---

## 🎬 Demo Part 5: Incident Management (1.5 minutes)

### What to Say:
"Incidents group related alerts. This helps analysts investigate coordinated attacks."

#### Step 1: Create Incident
1. Find `POST /incidents`
2. Click "Try it out"
3. Enter:
```json
{
  "title": "Brute Force Attack Investigation",
  "description": "Investigating coordinated SSH login attempts from multiple IPs",
  "severity": "high",
  "alert_ids": [1]
}
```
4. Click "Execute"
5. Show created incident

#### Step 2: Get Incident Details
1. Find `GET /incidents/{id}`
2. Click "Try it out"
3. Enter incident_id: `1`
4. Click "Execute"
5. Point out the response shows:
   - Incident details
   - All linked alerts
   - Current status

### What to Say:
"The many-to-many relationship allows one incident to track multiple alerts, and one alert can be part of multiple investigations if needed."

---

## 🎬 Demo Part 6: Integration Endpoints (1.5 minutes)

### What to Say:
"Now let me show the integration layer - how other modules send data to the backend. These endpoints don't require authentication because they're for internal pipeline use."

#### For ML Model Integration
1. Click "Authorize" button and logout/clear token
2. Find `POST /ingest/alerts`
3. Click "Try it out"
4. Enter:
```json
{
  "title": "ML Anomaly Detection",
  "severity": "critical",
  "source": "ml_model",
  "message": "Unusual network traffic pattern detected: 500% increase in outbound connections",
  "detection_method": "anomaly",
  "anomaly_score": 0.95
}
```
5. Click "Execute"
6. Show successful creation WITHOUT authentication

### What to Say:
"This is how Sayog's ML model sends detected anomalies. The `anomaly_score` field stores the confidence level. No authentication needed because this is internal communication."

#### For Kafka Integration
1. Find `POST /ingest/logs`
2. Click "Try it out"
3. Enter:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "severity": "warning",
  "source": "firewall",
  "message": "Connection blocked from blacklisted IP",
  "raw_data": {
    "src_ip": "203.0.113.45",
    "dst_ip": "192.168.1.10",
    "port": 22
  }
}
```
4. Click "Execute"

### What to Say:
"This is Ayush's endpoint - his Kafka consumer sends parsed logs here. The `raw_data` field can store any JSON structure, making it flexible for different log formats."

---

## 🎬 Demo Part 7: Dashboard Statistics (1 minute)

### What to Say:
"For the frontend dashboard, I created statistics endpoints that provide real-time metrics."

#### Get Summary Statistics
1. Re-authorize with token (login again if needed)
2. Find `GET /stats/summary`
3. Click "Try it out"
4. Click "Execute"
5. Show response:
```json
{
  "total_logs": 1,
  "total_alerts": 2,
  "total_incidents": 1,
  "open_alerts": 1,
  "open_incidents": 1,
  "critical_alerts": 1,
  "recent_activity": [...]
}
```

### What to Say:
"Aryan's frontend dashboard will use this to show overview metrics. There are also endpoints for trends, breakdowns by severity, and activity feeds."

---

## 🎬 Demo Part 8: Code Architecture (1 minute)

### What to Say:
"Let me show you the code architecture - I followed a clean 3-layer design pattern."

### What to Show:
1. Open `app/routes/alerts.py` in code editor
2. Show the route handler:
```python
@router.post("/", response_model=AlertResponse, status_code=201)
async def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_with_role())
):
    return alert_service.create_alert(db, alert, created_by_id=current_user.id)
```

3. Point out:
   - "Route receives request and validates with Pydantic"
   - "Depends(get_db) injects database session"
   - "Depends(get_current_user...) handles authentication"
   - "Business logic delegated to service layer"

4. Open `app/services/db_alert_service.py`
5. Show the service function:
```python
def create_alert(db: Session, alert: AlertCreate, created_by_id: int = None):
    db_alert = Alert(
        title=alert.title,
        severity=alert.severity.value,
        source=alert.source,
        message=alert.message,
        ...
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert
```

6. Point out: "Service handles database operations using SQLAlchemy ORM"

7. Open `app/models/database.py`
8. Show the Alert model:
```python
class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    ...
```

### What to Say:
"Three layers: Routes handle HTTP, Services contain business logic, Models define database structure. This makes the code testable, maintainable, and follows industry best practices."

---

## 🎬 Demo Part 9: Testing (30 seconds)

### What to Say:
"I've also written comprehensive tests to ensure everything works correctly."

### What to Show:
1. Open terminal
2. Run:
```bash
pytest tests/test_alerts.py -v
```
3. Show passing tests:
```
test_create_alert PASSED
test_get_alerts PASSED
test_update_alert_status PASSED
...
```

### What to Say:
"Tests cover authentication, CRUD operations, error handling, and integration endpoints. This ensures reliability as the codebase grows."

---

## 🎬 Demo Part 10: Database Schema (Optional - 1 minute)

### What to Say:
"Let me quickly show the database schema I designed with Sumiran."

### What to Show:
**Option A**: Open Supabase Dashboard
1. Go to Supabase.com
2. Show Table Editor
3. Point out tables: users, logs, alerts, incidents, incident_alerts

**Option B**: Show code
1. Open `app/models/database.py`
2. Scroll through models
3. Point out relationships:
```python
class Alert(Base):
    # Foreign key to logs
    log_id = Column(Integer, ForeignKey("logs.id"))
    
    # Foreign key to user
    assigned_to = Column(Integer, ForeignKey("users.id"))
    
    # Many-to-many with incidents
    incidents = relationship("Incident", secondary=incident_alerts, back_populates="alerts")
```

### What to Say:
"The schema supports the full workflow: logs can trigger alerts, alerts can be grouped into incidents, users can be assigned, and ML predictions are linked. All properly normalized with foreign keys."

---

## 🎬 Demo Part 11: Closing Summary (30 seconds)

### What to Say:
"To summarize what I've built:

✅ **Complete REST API** with 35+ endpoints
✅ **JWT authentication** with role-based access
✅ **PostgreSQL database** on Supabase with proper schema
✅ **Integration endpoints** ready for Kafka, ML model, and LLM
✅ **Search, export, and audit** capabilities
✅ **Comprehensive tests** with pytest
✅ **Production-ready** with Docker, migrations, error handling

All integration points are live. Ayush can push logs from Kafka, Sayog can send alerts from ML and summaries from LLM, Aryan can build the frontend dashboard, and everything is documented.

The backend is ready for the next phase."

---

## 🎯 Quick Recovery Phrases

If something goes wrong during demo:

### If server is down:
"Let me quickly restart the server - this is what uvicorn's reload feature handles automatically in development."

### If authentication fails:
"Let me re-login to get a fresh token - tokens expire after 15 minutes for security."

### If database error:
"Let me check the database connection - in production we have retry logic and health monitoring."

### If wrong data:
"Let me reset the demo data - I have seed scripts for this."

---

## ✅ Post-Demo Checklist

After demo, be ready to answer:

- [ ] "Can you explain the database schema?"
- [ ] "How does the ML integration work?"
- [ ] "What security measures did you implement?"
- [ ] "How do you handle errors?"
- [ ] "How would you scale this?"
- [ ] "Why did you choose FastAPI?"
- [ ] "How do you test the endpoints?"

**Key**: Always refer to actual code, not theory!

---

## 💡 Confidence Boosters

Remember:
- ✅ You built a COMPLETE, WORKING backend
- ✅ All integration points are READY
- ✅ Code is CLEAN and ORGANIZED
- ✅ Tests are PASSING
- ✅ Documentation is THOROUGH
- ✅ You understand EVERY line of code

**You've got this! 🚀**

---

## 📞 Emergency Commands

If you need to reset during demo:

```bash
# Restart server
# Press Ctrl+C in terminal
uvicorn app.main:app --reload

# Re-initialize database (if needed)
python setup_database.py

# Run specific test
pytest tests/test_alerts.py::test_create_alert -v

# Check health
curl http://localhost:8000/health
```

---

**GOOD LUCK! You're well-prepared! 💪**
