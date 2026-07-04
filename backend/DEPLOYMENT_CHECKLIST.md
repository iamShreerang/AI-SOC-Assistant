# ✅ Deployment Checklist - AI SOC Assistant Backend

## 🔒 Security First!

### Environment Variables ⚠️ CRITICAL
- [ ] `.env` file is in `.gitignore` ✅ (Already configured)
- [ ] `backend/.env` contains real API keys (NOT COMMITTED)
- [ ] `backend/.env.example` is committed (template only)
- [ ] Verified: `git status` does NOT show `.env`
- [ ] All secrets are strong random values (32+ bytes)

**Verify now**:
```bash
cd AI-SOC-Assistant
git check-ignore backend/.env  # Should return: backend/.env
git ls-files | grep "\.env$"   # Should return: nothing or only .env.example
```

---

## 🔑 API Keys Configuration

### Required Keys
Create `backend/.env` with real values:

```bash
# Generate secrets
SECRET_KEY=$(openssl rand -hex 32)
REFRESH_SECRET_KEY=$(openssl rand -hex 32)

# Get from providers
GROQ_API_KEY=gsk_xxxx              # From: https://console.groq.com/keys
GOOGLE_CLIENT_ID=xxx.apps.google   # From: https://console.cloud.google.com
GOOGLE_CLIENT_SECRET=xxx           # From: Google Cloud Console
GITHUB_CLIENT_ID=xxx               # From: https://github.com/settings/developers
GITHUB_CLIENT_SECRET=xxx           # From: GitHub Settings
```

### Optional Keys
```bash
# Elasticsearch (if using)
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_ENABLED=true

# CORS (adjust for your frontend)
CORS_ORIGINS=["http://localhost:3000","https://yourapp.com"]
```

**Documentation**: See `SECURITY.md` for detailed instructions

---

## 📦 Dependencies

### Python Dependencies
- [ ] Python 3.11+ installed
- [ ] Virtual environment created
- [ ] All requirements installed

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### External Services (Optional)
- [ ] Elasticsearch running (if enabled)
- [ ] Groq API key obtained (for AI summaries)
- [ ] OAuth apps configured (if using social login)

---

## 🚀 Startup Checklist

### 1. Environment Setup
```bash
cd backend
cp .env.example .env
# Edit .env with real values
```

### 2. Verify Configuration
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep fastapi  # Should show fastapi

# Test import
python -c "from app.main import app; print('✓ App loads successfully')"
```

### 3. Start Server
```bash
uvicorn app.main:app --reload
```

**Expected Output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete

# If Elasticsearch enabled:
✅ Elasticsearch initialized successfully
Created Elasticsearch index: soc-logs
Created Elasticsearch index: soc-alerts
Created Elasticsearch index: soc-incidents

# If Elasticsearch disabled:
ℹ️  Elasticsearch disabled - using in-memory storage
```

### 4. Verify Endpoints
```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs  # Or visit in browser
```

---

## 🧪 Testing

### Manual Testing
```bash
# 1. Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123","role":"analyst"}'

# 2. Login
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' \
  | jq -r '.access_token')

# 3. Test protected endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/stats/summary | jq
```

### Automated Testing
```bash
# Run test suite
pytest

# Run demo script
python demo_features.py

# Test enums
python test_enums.py
```

---

## 🌐 Production Deployment

### Environment Variables
**DO NOT use `.env` file in production!**

Instead, set environment variables:

**Docker**:
```bash
docker run -e SECRET_KEY=$SECRET_KEY -e GROQ_API_KEY=$GROQ_API_KEY ...
```

**Kubernetes**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: backend-secrets
type: Opaque
data:
  SECRET_KEY: <base64-encoded>
  GROQ_API_KEY: <base64-encoded>
```

**AWS/Azure/GCP**:
- Use AWS Secrets Manager
- Use Azure Key Vault
- Use GCP Secret Manager

### Production Settings
```bash
DEBUG=false
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_URL=https://production-es.example.com:9200
CORS_ORIGINS=["https://yourdomain.com"]
```

---

## 🔒 Security Checklist

### Before Deployment
- [ ] `.env` NOT committed to Git
- [ ] All secrets use strong random values
- [ ] Production secrets stored in vault (not .env)
- [ ] CORS origins restricted to your domain
- [ ] Debug mode disabled (`DEBUG=false`)
- [ ] TLS/SSL enabled for Elasticsearch (production)
- [ ] Rate limiting configured
- [ ] OAuth redirect URIs use HTTPS (production)

### After Deployment
- [ ] Test all endpoints work
- [ ] Verify authentication flow
- [ ] Check Elasticsearch connection (if enabled)
- [ ] Monitor logs for errors
- [ ] Test OAuth flows (if configured)
- [ ] Verify CORS headers
- [ ] Check rate limiting works

---

## 📊 Monitoring

### Health Checks
```bash
# Application health
curl https://your-api.com/health

# Elasticsearch health (if using)
curl http://localhost:9200/_cluster/health

# API response time
time curl https://your-api.com/stats/summary
```

### Logs
```bash
# Check for errors
tail -f /var/log/backend.log | grep ERROR

# Monitor authentication
tail -f /var/log/backend.log | grep auth

# Watch Elasticsearch
tail -f /var/log/backend.log | grep -i elastic
```

---

## 🐛 Troubleshooting

### Common Issues

**"Module not found" error**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**"Elasticsearch not available"**:
```bash
# Check if Elasticsearch is running
curl http://localhost:9200

# Or disable Elasticsearch temporarily
# In .env: ELASTICSEARCH_ENABLED=false
```

**"Invalid token" error**:
```bash
# Token might be expired (15 min lifetime)
# Use refresh token or re-login
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
```

**CORS errors**:
```bash
# Add your frontend URL to .env
CORS_ORIGINS=["http://localhost:3000","https://yourfrontend.com"]
```

---

## 📁 File Structure Check

Verify these files exist:

```
backend/
├── .env                    # YOUR SECRETS (NOT IN GIT)
├── .env.example            # Template (IN GIT)
├── app/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   ├── schemas/
│   └── utils/
├── requirements.txt
├── SECURITY.md             # Read this!
├── COMPLETE_FEATURES.md
└── ELASTICSEARCH.md
```

---

## ✅ Pre-Deployment Verification

Run this checklist before deploying:

```bash
# 1. Environment check
[ -f backend/.env ] && echo "✓ .env exists" || echo "✗ .env missing"

# 2. Git check
git check-ignore backend/.env && echo "✓ .env ignored" || echo "✗ .env NOT ignored!"

# 3. Secrets check
grep -q "your_actual" backend/.env && echo "✗ Using template values!" || echo "✓ Real keys configured"

# 4. Dependencies check
pip list | grep -q "fastapi" && echo "✓ Dependencies installed" || echo "✗ Missing dependencies"

# 5. Startup check
python -c "from app.main import app" && echo "✓ App imports successfully" || echo "✗ Import error"
```

All checks should show ✓

---

## 🎯 Quick Start (Development)

```bash
# 1. Clone repo
git clone https://github.com/iamShreerang/AI-SOC-Assistant.git
cd AI-SOC-Assistant/backend

# 2. Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure secrets
cp .env.example .env
# Edit .env with real values (see SECURITY.md)

# 4. Start server
uvicorn app.main:app --reload

# 5. Test
open http://localhost:8000/docs
```

---

## 🎯 Quick Start (Production)

```bash
# 1. Set environment variables (DO NOT use .env file)
export SECRET_KEY="your-secret"
export REFRESH_SECRET_KEY="your-refresh-secret"
export GROQ_API_KEY="your-groq-key"
# ... set all required vars

# 2. Start with production settings
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Or use Docker
docker run -p 8000:8000 \
  -e SECRET_KEY=$SECRET_KEY \
  -e GROQ_API_KEY=$GROQ_API_KEY \
  your-backend-image
```

---

## 📚 Documentation

- **SECURITY.md** - Environment security guide (READ THIS FIRST!)
- **COMPLETE_FEATURES.md** - All features list
- **ELASTICSEARCH.md** - Elasticsearch setup
- **QUICKSTART.md** - Quick examples
- **ENHANCEMENTS.md** - Feature documentation

---

## ✅ Final Checklist

Before marking as complete:

- [ ] Read `SECURITY.md` completely
- [ ] `.env` file created with real keys
- [ ] `.env` is NOT committed to Git
- [ ] All dependencies installed
- [ ] Server starts without errors
- [ ] Health endpoint responds
- [ ] API docs accessible at `/docs`
- [ ] Can login and get token
- [ ] Protected endpoints work with token
- [ ] Elasticsearch connected (if enabled)
- [ ] Team knows not to commit `.env`

---

## 🎉 Ready to Deploy!

Your backend is **production-ready** with:
- ✅ 45+ API endpoints
- ✅ Enterprise features
- ✅ Elasticsearch support
- ✅ Security best practices
- ✅ Comprehensive documentation

**Next**: Deploy and integrate with frontend/Kafka/ML! 🚀
