# Troubleshooting Guide - Evaluation Day
## Quick Fixes for Common Errors

---

## ❌ Error: "Unprocessable Entity" (422) during Login

### Possible Causes:

#### 1. Wrong Request Format in Swagger UI

**Problem**: Login endpoint expects `application/x-www-form-urlencoded`, not JSON

**Fix for Swagger UI**:
- The login endpoint might use OAuth2 form format
- Look for a different interface in Swagger UI

**Check your auth.py endpoint**:
```python
# Should be using OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordRequestForm

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # ... authentication logic
```

**How to use in Swagger**:
1. Find the `POST /auth/login`
2. Click "Try it out"
3. You'll see fields for `username` and `password` separately (not JSON)
4. Enter:
   - username: `analyst`
   - password: `analyst123`
5. Click "Execute"

---

#### 2. Database Not Initialized

**Problem**: Default users don't exist

**Quick Fix**:
```bash
# Run this in backend directory
python -c "from app.database import SessionLocal; from app.services.db_auth_service import create_default_users; db = SessionLocal(); create_default_users(db); db.close()"
```

Or restart the server (users are created on startup):
```bash
# Stop server (Ctrl+C)
# Start again
uvicorn app.main:app --reload
```

**Verify users exist**:
```bash
python -c "from app.database import SessionLocal; from app.models.database import User; db = SessionLocal(); users = db.query(User).all(); print([u.username for u in users]); db.close()"
```

Should output: `['analyst', 'admin']`

---

#### 3. Database Connection Issue

**Problem**: Cannot connect to Supabase

**Check**:
```bash
# Test connection
python verify_supabase.py
```

**Fix**:
1. Open `.env` file
2. Verify `DATABASE_URL` is correct
3. Check Supabase project is active at https://supabase.com/dashboard

---

## ❌ Error: "Unauthorized" (401)

### Fix 1: Token Expired
**Problem**: JWT token expired (15 minutes)

**Solution**: Login again to get a new token

### Fix 2: Wrong Authorization Format
**Problem**: Token format incorrect in Swagger

**Correct Format**:
- When you click "Authorize" in Swagger
- Just paste the token value (without "Bearer")
- Swagger adds "Bearer" automatically

### Fix 3: Not Authorized
**Problem**: Forgot to authorize after login

**Solution**:
1. Login via `POST /auth/login`
2. Copy the `access_token` from response
3. Click green "Authorize" button at top
4. Paste token
5. Click "Authorize"

---

## ❌ Error: Database Connection Failed

### Quick Checks:

```bash
# 1. Check if .env exists
dir .env

# 2. Check DATABASE_URL
type .env | findstr DATABASE_URL

# 3. Test connection
python -c "from app.database import check_connection; print('Connected!' if check_connection() else 'Failed')"
```

### Fix:
1. Open `.env`
2. Verify `DATABASE_URL` format:
```
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
```
3. Get correct URL from Supabase Dashboard → Settings → Database

---

## ❌ Error: Port 8000 Already in Use

### Fix (Windows):
```bash
# Find process
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID_NUMBER> /F
```

### Alternative: Use Different Port
```bash
uvicorn app.main:app --reload --port 8001
```

Then access: http://localhost:8001/docs

---

## ❌ Error: Module Not Found

### Fix:
```bash
# Activate virtual environment
cd backend
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## ❌ Error: Table Does Not Exist

### Fix:
```bash
# Run migrations
alembic upgrade head

# Or create tables directly (development)
python -c "from app.database import create_tables; create_tables()"
```

---

## 🔧 Quick Reset (Nuclear Option)

If everything is broken:

```bash
# 1. Stop server (Ctrl+C)

# 2. Recreate database tables
alembic downgrade base
alembic upgrade head

# 3. Recreate default users
python -c "from app.database import SessionLocal; from app.services.db_auth_service import create_default_users; db = SessionLocal(); create_default_users(db); db.close()"

# 4. Restart server
uvicorn app.main:app --reload

# 5. Test health
curl http://localhost:8000/health
```

---

## ✅ Pre-Demo Health Check

Run this before your evaluation:

```bash
# 1. Activate environment
cd backend
venv\Scripts\activate

# 2. Start server
uvicorn app.main:app --reload

# In another terminal:

# 3. Check health
curl http://localhost:8000/health

# 4. Test login
curl -X POST "http://localhost:8000/auth/login" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=analyst&password=analyst123"

# Should return token
```

Expected output:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

---

## 🎯 Working Login in Swagger UI

**Step-by-step**:

1. Go to http://localhost:8000/docs

2. Find `POST /auth/login` under "Auth" section

3. Click "Try it out"

4. **If you see JSON format**:
```json
{
  "username": "analyst",
  "password": "analyst123"
}
```
Then your endpoint uses JSON body - just fill and execute.

5. **If you see form fields**:
- username: `analyst`
- password: `analyst123`
- Leave other fields empty
Then your endpoint uses OAuth2 form - fill fields and execute.

6. Copy the `access_token` from response (without quotes)

7. Click green "Authorize" button at top of page

8. Paste token in the "Value" field

9. Click "Authorize", then "Close"

10. Now try any protected endpoint (like `GET /alerts`)

---

## 📝 Alternative: Use curl for Demo

If Swagger is problematic:

```bash
# 1. Login
curl -X POST "http://localhost:8000/auth/login" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=analyst&password=analyst123"

# Copy the token from response

# 2. Create alert
curl -X POST "http://localhost:8000/alerts" ^
  -H "Authorization: Bearer YOUR_TOKEN_HERE" ^
  -H "Content-Type: application/json" ^
  -d "{\"title\":\"Test Alert\",\"severity\":\"high\",\"source\":\"firewall\",\"message\":\"Test\",\"detection_method\":\"signature\"}"

# 3. Get alerts
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" ^
  "http://localhost:8000/alerts"
```

---

## 🔍 Debug Mode

Add this temporarily to see detailed errors:

In `app/main.py`, after creating the FastAPI app:

```python
app = FastAPI(
    # ... existing config
    debug=True  # Add this temporarily
)
```

This will show detailed error traces in the browser.

---

## 💡 Common Swagger UI Issues

### Issue: Can't find where to enter credentials

**Solution**: 
- Look for the lock icon 🔒 next to endpoints
- OR the "Authorize" button at the top
- OR form fields directly in the login endpoint

### Issue: Token not working after authorization

**Solution**:
1. Logout (click "Authorize" → "Logout")
2. Login again
3. Get fresh token
4. Authorize with new token

### Issue: "detail": "Not authenticated"

**Solution**: You forgot to authorize or token expired
- Login again
- Click "Authorize"
- Paste token
- Try request again

---

## 🚨 Emergency Demo Backup Plan

If Swagger UI completely fails:

### Option 1: Use Postman
- Import: `.github/postman_collection.json`
- Set environment variable for token
- Run requests from collection

### Option 2: Show Code Instead
- Open files: `app/routes/alerts.py`, `app/services/db_alert_service.py`
- Walk through the code logic
- Run pytest to show tests passing
- Show database tables in Supabase dashboard

### Option 3: Use Python Script
Create quick demo script:

```python
# demo_live.py
import requests

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": "analyst", "password": "analyst123"}
)
token = response.json()["access_token"]
print(f"✅ Logged in successfully")

# Create alert
headers = {"Authorization": f"Bearer {token}"}
alert = {
    "title": "Demo Alert",
    "severity": "high",
    "source": "firewall",
    "message": "Test alert",
    "detection_method": "signature"
}
response = requests.post(f"{BASE_URL}/alerts", json=alert, headers=headers)
print(f"✅ Alert created: ID {response.json()['id']}")

# Get alerts
response = requests.get(f"{BASE_URL}/alerts", headers=headers)
print(f"✅ Retrieved {len(response.json())} alerts")
```

Run: `python demo_live.py`

---

## 📞 Last Resort Checklist

If nothing works during evaluation:

1. ✅ Show the code architecture (main.py, routes, services, models)
2. ✅ Run pytest to show tests passing
3. ✅ Show database schema in Supabase dashboard
4. ✅ Walk through the README documentation
5. ✅ Explain integration points with diagrams
6. ✅ Show requirements.txt to demonstrate tech stack

**Remember**: You built it, you know how it works. Code and tests are proof enough!

---

## ✨ Positive Mindset

- The code is solid ✅
- Tests are passing ✅
- Documentation is complete ✅
- You understand everything ✅

**Demo hiccups happen to everyone. Your implementation is sound!** 💪

---

**Keep this file open during evaluation for quick reference!**
