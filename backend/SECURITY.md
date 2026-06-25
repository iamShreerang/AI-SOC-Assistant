# 🔒 Environment Security Guide

## ⚠️ CRITICAL: Never Commit Secrets!

Your `.env` file contains sensitive API keys and secrets. **NEVER** commit it to Git!

---

## ✅ What's Protected

Your `.gitignore` already excludes:
```
.env
backend/.env
backend/.env.local
*.env.local
*.env.production
```

---

## 🔧 Setup Instructions

### 1. Copy the Template
```bash
cd backend
cp .env.example .env
```

### 2. Add Your Real Keys

Edit `backend/.env` and replace placeholders:

```bash
# REPLACE THESE WITH REAL VALUES!
GROQ_API_KEY=gsk_your_actual_groq_key_here
GOOGLE_CLIENT_ID=your_app_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_actual_google_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# Generate secure secrets:
SECRET_KEY=generate_with_openssl_rand_hex_32
REFRESH_SECRET_KEY=generate_different_secret_here
```

### 3. Generate Secure Keys
```bash
# On Linux/Mac:
openssl rand -hex 32

# On Windows (PowerShell):
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Or use Python:
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🔑 Where to Get API Keys

### Groq API Key
1. Visit: https://console.groq.com/keys
2. Sign up/Login
3. Click "Create API Key"
4. Copy and paste into `.env`

```bash
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Google OAuth
1. Visit: https://console.cloud.google.com/apis/credentials
2. Create Project → Create OAuth 2.0 Client ID
3. Application type: Web application
4. Authorized redirect URIs:
   - `http://localhost:8000/auth/callback/google`
   - Add your production URL
5. Copy Client ID and Client Secret

```bash
GOOGLE_CLIENT_ID=123456789-xxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx
```

### GitHub OAuth
1. Visit: https://github.com/settings/developers
2. Click "New OAuth App"
3. Application name: AI SOC Assistant
4. Homepage URL: `http://localhost:8000`
5. Authorization callback URL: `http://localhost:8000/auth/callback/github`
6. Copy Client ID and generate Client Secret

```bash
GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 📋 Complete .env Template

Create `backend/.env` with:

```bash
# ======================================
# AI SOC Assistant - Backend Configuration
# ⚠️ NEVER COMMIT THIS FILE TO GIT!
# ======================================

# Application
APP_NAME=AI SOC Assistant
DEBUG=false

# JWT Configuration
SECRET_KEY=your_32_byte_hex_secret_here
REFRESH_SECRET_KEY=your_different_32_byte_hex_secret_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database (PostgreSQL) - Future
DATABASE_URL=postgresql://user:password@localhost:5432/soc_db

# Kafka Integration - Team's Scope
KAFKA_BROKER=localhost:9092
KAFKA_TOPIC_RAW_LOGS=raw-logs

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_ENABLED=true

# LLM - Groq API
# Get your key from: https://console.groq.com/keys
GROQ_API_KEY=gsk_your_actual_key_here

# OAuth - Google
# Get credentials from: https://console.cloud.google.com/apis/credentials
GOOGLE_CLIENT_ID=your_app_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_secret_here

# OAuth - GitHub
# Get credentials from: https://github.com/settings/developers
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_secret_here

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:8080"]
```

---

## ✅ Verify It's Ignored

Check that `.env` is NOT tracked:

```bash
cd backend
git status

# Should NOT show .env file
# If it does, run:
git rm --cached .env
git commit -m "Remove .env from tracking"
```

---

## 🚨 If You Accidentally Committed Secrets

### 1. Immediately Rotate All Keys
- Generate new SECRET_KEY and REFRESH_SECRET_KEY
- Revoke and regenerate all API keys:
  - Groq: https://console.groq.com/keys
  - Google: https://console.cloud.google.com/apis/credentials
  - GitHub: https://github.com/settings/developers

### 2. Remove from Git History
```bash
# Remove file from history (DANGEROUS - rewrites history)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (only if repo is not shared yet)
git push origin --force --all
```

### 3. Add to .gitignore (if not already)
```bash
echo "backend/.env" >> .gitignore
git add .gitignore
git commit -m "Add .env to gitignore"
```

---

## 🔐 Security Best Practices

### DO ✅
- ✅ Keep `.env` local only
- ✅ Use different keys for dev/staging/prod
- ✅ Use strong, random secrets (32+ bytes)
- ✅ Rotate keys regularly
- ✅ Use environment-specific files (`.env.production`, `.env.staging`)
- ✅ Store production secrets in secure vaults (AWS Secrets Manager, Azure Key Vault)

### DON'T ❌
- ❌ Never commit `.env` to Git
- ❌ Never share `.env` via Slack/email
- ❌ Never use the same key in multiple environments
- ❌ Never hardcode secrets in code
- ❌ Never screenshot `.env` files
- ❌ Never store secrets in plaintext on shared drives

---

## 🏢 Production Deployment

### Option 1: Environment Variables (Recommended)
Set directly in your deployment platform:

**AWS Elastic Beanstalk**:
```bash
eb setenv SECRET_KEY=xxx GROQ_API_KEY=yyy
```

**Docker**:
```bash
docker run -e SECRET_KEY=xxx -e GROQ_API_KEY=yyy ...
```

**Kubernetes**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: soc-backend-secrets
data:
  SECRET_KEY: base64_encoded_secret
  GROQ_API_KEY: base64_encoded_key
```

### Option 2: Secrets Manager
**AWS Secrets Manager**:
```python
import boto3
import json

client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='soc-backend-secrets')
secrets = json.loads(response['SecretString'])

settings.secret_key = secrets['SECRET_KEY']
settings.groq_api_key = secrets['GROQ_API_KEY']
```

**Azure Key Vault**, **HashiCorp Vault**, etc.

---

## 📝 Team Sharing (Without Exposing Secrets)

### For Development
Share `.env.example` with teammates:
```bash
git add backend/.env.example
git commit -m "Add environment template"
git push
```

Then teammates create their own `.env`:
```bash
cp .env.example .env
# Edit with their own keys
```

### For Production
Use a secure password manager:
- **1Password** - Shared Vaults
- **LastPass** - Shared Folders
- **Bitwarden** - Organizations
- **AWS Secrets Manager**
- **Azure Key Vault**

---

## ✅ Security Checklist

Before pushing code:
- [ ] `.env` is in `.gitignore`
- [ ] `git status` does NOT show `.env`
- [ ] All secrets use strong random values
- [ ] `.env.example` has placeholders (no real keys)
- [ ] Production uses environment variables or secrets manager
- [ ] Team knows not to commit `.env`

---

## 🆘 Emergency: Leaked Keys

If keys are exposed publicly:

1. **Immediately revoke ALL keys**
2. **Generate new keys**
3. **Update `.env` with new keys**
4. **Restart the application**
5. **Check for unauthorized usage**
6. **Review access logs**
7. **Consider security audit**

---

## 📞 Questions?

- Check if `.env` is ignored: `git check-ignore backend/.env` (should return the path)
- See what's tracked: `git ls-files | grep .env` (should return nothing)
- Test without committing: `git add backend/.env --dry-run` (should warn)

---

## 🎯 Summary

✅ **Correct Setup**:
```
backend/
├── .env                 # YOUR REAL KEYS (gitignored)
├── .env.example         # TEMPLATE (committed)
└── .env.example.new     # UPDATED TEMPLATE (committed)
```

❌ **Wrong**:
```
backend/
├── .env                 # COMMITTED TO GIT ⚠️ DANGER!
```

**Remember**: When in doubt, DON'T COMMIT!

---

## 🔒 Your secrets are now protected! 🔒
