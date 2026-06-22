"""
Comprehensive backend test — runs against live server at localhost:8000.
Tests: Auth, JWT, Refresh, Logout, Rate Limiting, RBAC, Logs, Alerts, Incidents
Usage: python test_all.py
"""

import requests

BASE = "http://localhost:8000"
PASS = "✅"
FAIL = "❌"

def check(label: str, condition: bool, extra: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status} {label}" + (f" — {extra}" if extra else ""))
    return condition

def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

results = []

# ── 1. Health ─────────────────────────────────────────────────────
section("1. HEALTH CHECK")
r = requests.get(f"{BASE}/health")
results.append(check("GET /health returns 200", r.status_code == 200))

# ── 2. Register ───────────────────────────────────────────────────
section("2. REGISTER")
r = requests.post(f"{BASE}/auth/register", json={"username": "testanalyst", "password": "Test@1234", "role": "analyst"})
results.append(check("Register new analyst", r.status_code == 201, r.json().get("username")))

r = requests.post(f"{BASE}/auth/register", json={"username": "testadmin", "password": "Admin@1234", "role": "admin"})
results.append(check("Register new admin", r.status_code == 201, r.json().get("username")))

r = requests.post(f"{BASE}/auth/register", json={"username": "testanalyst", "password": "Test@1234", "role": "analyst"})
results.append(check("Duplicate register returns 409", r.status_code == 409))

# ── 3. Login ──────────────────────────────────────────────────────
section("3. LOGIN")
r = requests.post(f"{BASE}/auth/login", json={"username": "testanalyst", "password": "Test@1234"})
results.append(check("Analyst login returns 200", r.status_code == 200))
analyst_token = r.json().get("access_token", "")
analyst_refresh = r.json().get("refresh_token", "")
results.append(check("Access token present", bool(analyst_token)))
results.append(check("Refresh token present", bool(analyst_refresh)))

r = requests.post(f"{BASE}/auth/login", json={"username": "testadmin", "password": "Admin@1234"})
results.append(check("Admin login returns 200", r.status_code == 200))
admin_token = r.json().get("access_token", "")
admin_refresh = r.json().get("refresh_token", "")

r = requests.post(f"{BASE}/auth/login", json={"username": "testanalyst", "password": "wrongpassword"})
results.append(check("Wrong password returns 401", r.status_code == 401))

# ── 4. /users/me ──────────────────────────────────────────────────
section("4. IDENTITY (/users/me)")
r = requests.get(f"{BASE}/auth/users/me", headers={"Authorization": f"Bearer {analyst_token}"})
results.append(check("GET /users/me with valid token", r.status_code == 200, r.json().get("username")))

r = requests.get(f"{BASE}/auth/users/me", headers={"Authorization": "Bearer invalidtoken"})
results.append(check("GET /users/me with invalid token returns 401", r.status_code == 401))

# ── 5. Refresh Token ──────────────────────────────────────────────
section("5. REFRESH TOKEN")
r = requests.post(f"{BASE}/auth/refresh", json={"refresh_token": analyst_refresh})
results.append(check("Refresh returns new access token", r.status_code == 200))
new_access = r.json().get("access_token", "")
results.append(check("New access token is different", new_access != analyst_token))

r = requests.post(f"{BASE}/auth/refresh", json={"refresh_token": "invalidrefresh"})
results.append(check("Invalid refresh token returns 401", r.status_code == 401))

# ── 6. Logout + Blacklist ─────────────────────────────────────────
section("6. LOGOUT + TOKEN BLACKLIST")
r = requests.post(f"{BASE}/auth/logout", headers={"Authorization": f"Bearer {analyst_token}"})
results.append(check("Logout returns 200", r.status_code == 200))

r = requests.get(f"{BASE}/auth/users/me", headers={"Authorization": f"Bearer {analyst_token}"})
results.append(check("Blacklisted token returns 401", r.status_code == 401))

# use new token going forward
analyst_token = new_access

# ── 7. Rate Limiting ──────────────────────────────────────────────
section("7. RATE LIMITING")
hit_429 = False
for i in range(12):
    r = requests.post(f"{BASE}/auth/login", json={"username": "x", "password": "y"})
    if r.status_code == 429:
        hit_429 = True
        break
results.append(check("Rate limit triggers 429 on /auth/login", hit_429))

# ── 8. RBAC ───────────────────────────────────────────────────────
section("8. RBAC")
analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
admin_headers   = {"Authorization": f"Bearer {admin_token}"}

# Create a log first (analyst can do this)
r = requests.post(f"{BASE}/logs/", json={"source": "firewall-01", "severity": "high", "message": "Test log"}, headers=analyst_headers)
results.append(check("Analyst can create log", r.status_code == 201))

# Create alert via ingest (no auth)
r = requests.post(f"{BASE}/ingest/alerts", json={"source": "ids-sensor", "severity": "critical", "message": "Test alert", "status": "open"})
results.append(check("Ingest alert (no auth)", r.status_code == 201))
alert_id = r.json().get("id")

# Analyst tries to update alert — should fail
r = requests.patch(f"{BASE}/alerts/{alert_id}", json={"status": "acknowledged"}, headers=analyst_headers)
results.append(check("Analyst cannot update alert (403)", r.status_code == 403))

# Admin updates alert — should pass
r = requests.patch(f"{BASE}/alerts/{alert_id}", json={"status": "acknowledged"}, headers=admin_headers)
results.append(check("Admin can update alert", r.status_code == 200, r.json().get("status")))

# Analyst tries to create incident — should fail
r = requests.post(f"{BASE}/incidents/", json={"title": "Test", "description": "Test", "alert_ids": [], "status": "open"}, headers=analyst_headers)
results.append(check("Analyst cannot create incident (403)", r.status_code == 403))

# Admin creates incident — should pass
r = requests.post(f"{BASE}/incidents/", json={"title": "Test Incident", "description": "Test", "alert_ids": [], "status": "open"}, headers=admin_headers)
results.append(check("Admin can create incident", r.status_code == 201))

# ── 9. Logs & Alerts read ─────────────────────────────────────────
section("9. LOGS & ALERTS READ (analyst)")
r = requests.get(f"{BASE}/logs/", headers=analyst_headers)
results.append(check("Analyst can read logs", r.status_code == 200))

r = requests.get(f"{BASE}/alerts/", headers=analyst_headers)
results.append(check("Analyst can read alerts", r.status_code == 200))

r = requests.get(f"{BASE}/incidents/", headers=analyst_headers)
results.append(check("Analyst can read incidents", r.status_code == 200))

# ── Summary ───────────────────────────────────────────────────────
passed = sum(results)
total  = len(results)
print(f"\n{'='*60}")
print(f"  RESULT: {passed}/{total} tests passed {'✅' if passed == total else '❌'}")
print(f"{'='*60}\n")
