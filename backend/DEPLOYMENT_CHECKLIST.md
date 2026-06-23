# Supabase Integration - Deployment Checklist

Use this checklist to ensure your Supabase PostgreSQL integration is properly configured and deployed.

---

## ✅ Pre-Deployment Checklist

### 1. Supabase Project Setup
- [ ] Created Supabase account
- [ ] Created new project in Supabase
- [ ] Saved database password securely
- [ ] Noted project reference ID
- [ ] Verified project is active and running

### 2. Environment Configuration
- [ ] Created `.env` file from `.env.example`
- [ ] Generated secure `SECRET_KEY` (64 chars)
- [ ] Generated secure `REFRESH_SECRET_KEY` (64 chars)
- [ ] Added Supabase `DATABASE_URL`
- [ ] Configured CORS origins
- [ ] Set `DEBUG=false` for production
- [ ] Added `.env` to `.gitignore`

### 3. Database Setup
- [ ] Installed Python dependencies (`pip install -r requirements.txt`)
- [ ] Verified database connection (`python verify_supabase.py`)
- [ ] Ran Alembic migrations (`alembic upgrade head`)
- [ ] Verified tables created in Supabase dashboard
- [ ] Created default users
- [ ] Changed default passwords

### 4. Application Testing
- [ ] Server starts without errors (`uvicorn app.main:app --reload`)
- [ ] Health endpoint responds (`/health`)
- [ ] Can register new user (`POST /auth/register`)
- [ ] Can login (`POST /auth/login`)
- [ ] Can create log entry (`POST /logs`)
- [ ] Can create alert (`POST /alerts`)
- [ ] Can create incident (`POST /incidents`)
- [ ] Statistics endpoint works (`GET /stats/summary`)
- [ ] Search functionality works (`GET /search`)

### 5. API Documentation
- [ ] Swagger UI accessible (`/docs`)
- [ ] ReDoc accessible (`/redoc`)
- [ ] All endpoints documented
- [ ] Request/response examples present
- [ ] Authentication flow documented

### 6. Security Review
- [ ] All passwords hashed with bcrypt
- [ ] JWT tokens properly signed
- [ ] No sensitive data in logs
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] SQL injection prevention (SQLAlchemy ORM)
- [ ] Input validation (Pydantic schemas)

---

## 🔧 Post-Deployment Checklist

### 7. Production Configuration
- [ ] Set `DEBUG=false`
- [ ] Use production-grade `SECRET_KEY`
- [ ] SSL enabled for database (`sslmode=require`)
- [ ] Connection pooling configured
- [ ] Environment variables secured
- [ ] Logging configured
- [ ] Error tracking set up

### 8. Database Optimization
- [ ] Indexes created on frequently queried columns
- [ ] Connection pool sized appropriately
- [ ] Query performance tested
- [ ] Database backups configured
- [ ] Backup restoration tested

### 9. Monitoring & Alerts
- [ ] Server health monitoring
- [ ] Database connection monitoring
- [ ] Error rate tracking
- [ ] Performance metrics
- [ ] Disk space monitoring
- [ ] Alert thresholds configured

### 10. Integration Testing
- [ ] Kafka consumer can push logs (`POST /ingest/logs`)
- [ ] ML model can create alerts (`POST /ingest/alerts`)
- [ ] LLM can add summaries (`POST /summaries`)
- [ ] Frontend can fetch dashboard data
- [ ] All CRUD operations working

---

## 📋 Deployment Steps

### Development Environment

```bash
# 1. Clone repository
git clone https://github.com/iamShreerang/AI-SOC-Assistant.git
cd AI-SOC-Assistant/backend

# 2. Setup virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure database
python setup_supabase.py

# 5. Run migrations
alembic upgrade head

# 6. Verify setup
python verify_supabase.py

# 7. Start server
uvicorn app.main:app --reload
```

### Production Environment

```bash
# 1. Set production environment variables
export DEBUG=false
export DATABASE_URL="postgresql://..."
export SECRET_KEY="..."

# 2. Install production dependencies
pip install -r requirements.txt --no-dev

# 3. Run migrations
alembic upgrade head

# 4. Start with production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 🧪 Verification Commands

### Test Database Connection
```bash
python -c "from app.database import check_connection; exit(0 if check_connection() else 1)"
```

### Check Migration Status
```bash
alembic current
```

### Test Authentication
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"analyst","password":"analyst123"}'
```

### Test CRUD Operations
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"analyst","password":"analyst123"}' | jq -r .access_token)

# Create alert
curl -X POST http://localhost:8000/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","severity":"high","source":"test"}'

# Get alerts
curl -X GET http://localhost:8000/alerts \
  -H "Authorization: Bearer $TOKEN"
```

### Check Statistics
```bash
curl -X GET http://localhost:8000/stats/summary \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🐛 Common Issues & Solutions

### Issue: Database connection timeout
**Solution**: 
- Verify Supabase project is running
- Check DATABASE_URL is correct
- Test connection from command line
- Try connection pooling URL

### Issue: Migration fails
**Solution**:
- Check current migration: `alembic current`
- Downgrade and re-run: `alembic downgrade -1 && alembic upgrade head`
- Verify enum types don't already exist
- Check for table name conflicts

### Issue: Authentication errors
**Solution**:
- Verify SECRET_KEY is set
- Check token expiration
- Ensure user exists in database
- Verify password is correct

### Issue: CORS errors
**Solution**:
- Add frontend URL to CORS_ORIGINS
- Verify middleware is configured
- Check browser console for specific error
- Test with curl first (bypasses CORS)

---

## 📊 Performance Benchmarks

### Expected Performance (Development)

| Operation | Expected Time |
|-----------|---------------|
| Health check | < 50ms |
| Login | < 200ms |
| Create alert | < 100ms |
| List alerts (100) | < 300ms |
| Dashboard stats | < 500ms |
| Search | < 1000ms |

### Connection Pool Settings

```python
# app/database.py
pool_size = 10          # Base connections
max_overflow = 20       # Additional connections
pool_recycle = 3600     # Recycle after 1 hour
pool_pre_ping = True    # Test before use
```

---

## 🔐 Security Checklist

- [ ] No hardcoded credentials
- [ ] All secrets in environment variables
- [ ] JWT tokens have expiration
- [ ] Passwords hashed with bcrypt
- [ ] SQL injection protected (ORM)
- [ ] XSS protection enabled
- [ ] CSRF tokens for state-changing operations
- [ ] Rate limiting configured
- [ ] Input validation on all endpoints
- [ ] Error messages don't leak sensitive data
- [ ] HTTPS enforced in production
- [ ] Database connection encrypted (SSL)

---

## 📈 Scaling Considerations

### Database Scaling
- [ ] Connection pooling sized for load
- [ ] Read replicas configured (if needed)
- [ ] Query optimization completed
- [ ] Indexes on all foreign keys
- [ ] Partition large tables

### Application Scaling
- [ ] Stateless application design
- [ ] Load balancer configured
- [ ] Multiple application instances
- [ ] Shared session storage
- [ ] Caching layer implemented

---

## 🎯 Success Criteria

Your deployment is successful when:

✅ All endpoints respond correctly  
✅ Authentication works end-to-end  
✅ CRUD operations complete successfully  
✅ Statistics calculations are accurate  
✅ Search returns relevant results  
✅ No errors in application logs  
✅ Database connection is stable  
✅ Response times meet benchmarks  
✅ Integration points work (Kafka, ML, LLM)  
✅ Frontend can consume all APIs  

---

## 📞 Support Resources

- **Documentation**: [SUPABASE_SETUP.md](./SUPABASE_SETUP.md)
- **Implementation Guide**: [SUPABASE_IMPLEMENTATION.md](./SUPABASE_IMPLEMENTATION.md)
- **Backend Guide**: [BACKEND_README.md](./BACKEND_README.md)
- **Supabase Docs**: https://supabase.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org

---

## ✨ Next Steps After Deployment

1. **Monitor Performance**: Set up application monitoring
2. **Load Testing**: Test with realistic traffic
3. **Backup Strategy**: Verify automated backups
4. **Documentation**: Update team documentation
5. **Training**: Train team on new system
6. **Rollout Plan**: Plan production rollout
7. **Incident Response**: Prepare incident playbook

---

**Deployment Date**: __________  
**Deployed By**: __________  
**Environment**: [ ] Development [ ] Staging [ ] Production  
**Status**: [ ] In Progress [ ] Complete [ ] Blocked  

---

**Notes**:

_______________________________________________________________________

_______________________________________________________________________

_______________________________________________________________________
