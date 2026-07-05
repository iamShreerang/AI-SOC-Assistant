"""
Database verification script for Supabase PostgreSQL integration.
Tests connection, migrations, and basic CRUD operations.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import check_connection, SessionLocal, engine
from app.services.db_auth_service import create_default_users, register_user
from app.services.db_log_service import create_log, get_logs
from app.services.db_alert_service import create_alert, get_alerts
from app.services.db_incident_service import create_incident, get_incidents
from app.services.db_stats_service import get_dashboard_summary
from app.schemas.auth import UserRegister
from app.schemas.log import LogCreate
from app.schemas.alert import AlertCreate
from app.schemas.incident import IncidentCreate
from app.schemas.enums import UserRole, LogSeverity, AlertSeverity
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_connection():
    """Test database connection."""
    logger.info("=" * 60)
    logger.info("STEP 1: Testing Database Connection")
    logger.info("=" * 60)
    
    if check_connection():
        logger.info("✓ Database connection successful!")
        return True
    else:
        logger.error("✗ Database connection failed!")
        logger.error("Check your DATABASE_URL in .env file")
        return False


def test_tables():
    """Verify all tables exist."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Verifying Database Tables")
    logger.info("=" * 60)
    
    expected_tables = [
        "users", "logs", "alerts", "incidents", 
        "incident_alerts", "ml_predictions", "audit_logs"
    ]
    
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name")
            )
            existing_tables = [row[0] for row in result]
        
        logger.info(f"Found {len(existing_tables)} tables:")
        for table in existing_tables:
            if table in expected_tables:
                logger.info(f"  ✓ {table}")
            else:
                logger.info(f"  • {table}")
        
        missing = set(expected_tables) - set(existing_tables)
        if missing:
            logger.warning(f"\nMissing tables: {', '.join(missing)}")
            logger.warning("Run: alembic upgrade head")
            return False
        
        logger.info("\n✓ All required tables exist!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Table verification failed: {e}")
        return False


def test_users():
    """Test user operations."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Testing User Operations")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Create default users
        create_default_users(db)
        logger.info("✓ Default users created/verified")
        
        # Create test user
        test_user = UserRegister(
            username=f"test_user_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            password="Test123!",
            role=UserRole.ANALYST
        )
        result = register_user(db, test_user)
        
        if result:
            logger.info(f"✓ Created test user: {result.username}")
            return True
        else:
            logger.warning("User might already exist")
            return True
            
    except Exception as e:
        logger.error(f"✗ User operations failed: {e}")
        return False
    finally:
        db.close()


def test_logs():
    """Test log operations."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: Testing Log Operations")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Create test log
        log = LogCreate(
            source="test-source",
            severity=LogSeverity.INFO,
            message="Test log entry for verification",
            timestamp=datetime.utcnow(),
            raw="RAW LOG DATA"
        )
        result = create_log(db, log)
        logger.info(f"✓ Created log with ID: {result.id}")
        
        # Retrieve logs
        logs = get_logs(db, limit=5)
        logger.info(f"✓ Retrieved {len(logs)} recent logs")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Log operations failed: {e}")
        return False
    finally:
        db.close()


def test_alerts():
    """Test alert operations."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 5: Testing Alert Operations")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Create test alert
        alert = AlertCreate(
            title="Test Alert - Verification",
            severity=AlertSeverity.MEDIUM,
            source="test-detector",
            description="This is a test alert for database verification"
        )
        result = create_alert(db, alert)
        logger.info(f"✓ Created alert with ID: {result.id}")
        
        # Retrieve alerts
        alerts = get_alerts(db, limit=5)
        logger.info(f"✓ Retrieved {len(alerts)} recent alerts")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Alert operations failed: {e}")
        return False
    finally:
        db.close()


def test_incidents():
    """Test incident operations."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 6: Testing Incident Operations")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Create test incident
        incident = IncidentCreate(
            title="Test Incident - Verification",
            description="This is a test incident for database verification",
            alert_ids=[]
        )
        result = create_incident(db, incident)
        logger.info(f"✓ Created incident with ID: {result.id}")
        
        # Retrieve incidents
        incidents = get_incidents(db, limit=5)
        logger.info(f"✓ Retrieved {len(incidents)} recent incidents")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Incident operations failed: {e}")
        return False
    finally:
        db.close()


def test_statistics():
    """Test statistics operations."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 7: Testing Statistics Operations")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        stats = get_dashboard_summary(db)
        
        logger.info("Dashboard Statistics:")
        logger.info(f"  • Total Logs: {stats['total_logs']}")
        logger.info(f"  • Total Alerts: {stats['total_alerts']}")
        logger.info(f"  • Total Incidents: {stats['total_incidents']}")
        logger.info(f"  • Open Alerts: {stats['open_alerts']}")
        logger.info(f"  • Critical Alerts: {stats['critical_alerts']}")
        
        logger.info("\n✓ Statistics retrieved successfully!")
        return True
        
    except Exception as e:
        logger.error(f"✗ Statistics operations failed: {e}")
        return False
    finally:
        db.close()


def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("AI SOC ASSISTANT - DATABASE VERIFICATION")
    print("=" * 60)
    print("\nThis script will verify your Supabase PostgreSQL setup.\n")
    
    tests = [
        ("Connection", test_connection),
        ("Tables", test_tables),
        ("Users", test_users),
        ("Logs", test_logs),
        ("Alerts", test_alerts),
        ("Incidents", test_incidents),
        ("Statistics", test_statistics),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
            if not success:
                logger.error(f"\nTest '{name}' failed. Fix the issue before continuing.")
                break
        except Exception as e:
            logger.error(f"\n✗ Test '{name}' crashed: {e}")
            results.append((name, False))
            break
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"  {status} - {name}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Result: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("\n🎉 All tests passed! Your database is ready.")
        logger.info("\nNext steps:")
        logger.info("1. Start the server: uvicorn app.main:app --reload")
        logger.info("2. Visit API docs: http://localhost:8000/docs")
        logger.info("3. Test with Postman collection in .github/")
        return 0
    else:
        logger.error("\n❌ Some tests failed. Review the errors above.")
        logger.error("\nCommon fixes:")
        logger.error("1. Check DATABASE_URL in .env file")
        logger.error("2. Run migrations: alembic upgrade head")
        logger.error("3. Verify Supabase project is active")
        return 1


if __name__ == "__main__":
    sys.exit(main())
