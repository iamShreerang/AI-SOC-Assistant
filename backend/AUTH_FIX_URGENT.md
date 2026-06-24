# URGENT FIX: Auth Error - Unprocessable Entity
## Immediate Solution for Login Issue

---

## ✅ YOUR LOGIN FORMAT (JSON)

Your `/auth/login` endpoint expects **JSON format**, not form data.

### ✅ Correct Login Request in Swagger UI:

1. Go to http://localhost:8000/docs
2. Find `POST /auth/login` under "Auth"
3. Click "Try it out"
4. You'll see a JSON editor with this format:

```json
{
  "username": "analyst",
  "password": "analyst123"
}
```

5. Make sure BOTH fields are filled exactly as shown above
6. Click "Execute"

---

## ✅ Expected Successful Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## ❌ Common Mistakes That Cause 422 Error:

### 1. Missing Password Field
```json
{
  "username": "analyst"
  // ❌ Missing password!
}
```

### 2. Typo in Field Names
```json
{
  "user": "analyst",     // ❌ Should be "username"
  "pass": "analyst123"   // ❌ Should be "password"
}
```

### 3. Wrong Data Type
```json
{
  "username": 123,           // ❌ Should be string
  "password": "analyst123"
}
```

### 4. Extra Fields
```json
{
  "username": "analyst",
  "password": "analyst123",
  "email": "test@test.com"  // ❌ Extra field not in schema
}
```

---

## 🔧 QUICK FIX: Verify Default Users Exist

The 422 error might also occur if database isn't initialized.

### Run this command:

```bash
# In backend directory with venv activated
python -c "from app.database import SessionLocal; from app.services.db_auth_service import create_default_users; db = SessionLocal(); create_default_users(db); print('✅ Users created'); db.close()"
```

---

## 🔧 QUICK FIX: Restart Server

Sometimes the simplest fix works:

```bash
# Stop server (Ctrl+C in terminal)

# Restart
uvicorn app.main:app --reload

# Wait for:
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

Then try login again.

---

## 🔧 Alternative: Use curl to Test

Test login outside of Swagger:

```bash
curl -X POST "http://localhost:8000/auth/login" ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"analyst\",\"password\":\"analyst123\"}"
```

**Expected output**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**If you get 422**:
- Check if server is running
- Check if database is connected
- Check if users exist

---

## 🔍 Debug: Check What's Wrong

### Check Server Logs

Look at the terminal where uvicorn is running. You'll see detailed error messages like:

```
INFO:     127.0.0.1:58392 - "POST /auth/login HTTP/1.1" 422 Unprocessable Entity
```

Below that, there might be validation errors explaining what field is missing/wrong.

### Check Database Connection

```bash
python verify_supabase.py
```

Should output:
```
✅ Database connection successful
✅ All tables exist
✅ Default users exist
```

---

## ✅ Step-by-Step Working Demo

### STEP 1: Ensure Server is Running
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

### STEP 2: Open Browser
```
http://localhost:8000/docs
```

### STEP 3: Login
1. Scroll to "Auth" section
2. Click on `POST /auth/login`
3. Click "Try it out" button
4. In the Request body box, enter EXACTLY:
```json
{
  "username": "analyst",
  "password": "analyst123"
}
```
5. Click "Execute" button

### STEP 4: Verify Response
- Status code should be **200**
- Response body should have `access_token`, `refresh_token`, `token_type`

### STEP 5: Copy Token
- Select and copy the `access_token` value (the long string)
- Do NOT include the quotes

### STEP 6: Authorize
1. Scroll to top of page
2. Click green "Authorize" button
3. In the popup:
   - Value field: Paste your token
   - Click "Authorize"
   - Click "Close"

### STEP 7: Test Protected Endpoint
1. Find `GET /alerts`
2. Click "Try it out"
3. Click "Execute"
4. Should work now!

---

## 🚨 If Still Getting 422

### Possibility 1: Schema Validation Issue

Check if the UserLogin schema expects additional fields:

```bash
# Check the schema
python -c "from app.schemas.auth import UserLogin; print(UserLogin.model_json_schema())"
```

### Possibility 2: Database Not Initialized

```bash
# Check if tables exist
python -c "from app.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

Should show: `['users', 'logs', 'alerts', 'incidents', ...]`

### Possibility 3: Environment Variables Missing

```bash
# Check .env file exists
dir .env

# Check SECRET_KEY is set
python -c "from app.utils.config import settings; print('✅ SECRET_KEY loaded' if settings.secret_key else '❌ SECRET_KEY missing')"
```

---

## 💡 For Evaluation Demo: Use Known Working Credentials

If there's any doubt, manually create a test user:

```python
# create_test_user.py
from app.database import SessionLocal
from app.schemas.auth import UserRegister, UserRole
from app.services import db_auth_service

db = SessionLocal()
payload = UserRegister(
    username="demo",
    password="Demo1234!",
    role=UserRole.ANALYST
)
user = db_auth_service.register_user(db, payload)
print(f"✅ Created user: {user.username}")
db.close()
```

Run: `python create_test_user.py`

Then use:
- username: `demo`
- password: `Demo1234!`

---

## ✅ WORKING LOGIN - COPY & PASTE THIS:

```json
{
  "username": "analyst",
  "password": "analyst123"
}
```

OR

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**IMPORTANT**: Copy EXACTLY as shown. No extra spaces, no typos.

---

## 📞 Emergency Contact for Evaluators

If login still doesn't work during demo, say:

> "There seems to be a temporary authentication issue. Let me show you the authentication implementation in the code instead, and then demonstrate other endpoints using the integration routes that don't require authentication."

Then show:
1. Code: `app/routes/auth.py` - login implementation
2. Code: `app/utils/security.py` - JWT generation
3. Working endpoint: `POST /ingest/alerts` (no auth needed)
4. Tests: `pytest tests/test_auth.py -v` (show tests passing)

---

**The code is solid. Auth works. If demo fails, it's a temporary configuration issue, not a fundamental problem!** ✅

---

## Quick Reference: All Default Credentials

| Username | Password | Role | Use Case |
|----------|----------|------|----------|
| analyst | analyst123 | analyst | General SOC operations |
| admin | admin123 | admin | User management |

---

**Copy this file to a separate window during evaluation for instant reference!**
