#!/usr/bin/env python3
"""Verification script to check all backend components."""

import sys

def test_imports():
    """Test all critical imports."""
    print("Testing imports...")
    
    try:
        # Core
        from app.main import app
        print("  [OK] Main app")
        
        # Routes
        from app.routes import health, auth, stats, search, export, audit
        from app.routes.logs import router as logs_router
        from app.routes.alerts import router as alerts_router
        from app.routes.incidents import router as incidents_router
        print("  [OK] All routes")
        
        # Services
        from app.services import (
            log_service, alert_service, incident_service,
            auth_service, llm_service, stats_service,
            search_service, export_service, audit_service
        )
        print("  [OK] Core services")
        
        # Elasticsearch services
        from app.services import (
            es_log_service, es_alert_service, es_incident_service
        )
        print("  [OK] Elasticsearch services")
        
        # Schemas
        from app.schemas.enums import (
            LogSeverity, AlertSeverity, AlertStatus,
            IncidentStatus, UserRole
        )
        print("  [OK] Enums")
        
        # Utils
        from app.utils.config import settings
        from app.utils.security import hash_password, verify_password
        from app.utils.elasticsearch_client import get_es_client
        from app.utils.password_validator import validate_password_simple
        print("  [OK] Utils")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Import failed: {e}")
        return False


def test_enums():
    """Test enum values."""
    print("\nTesting enums...")
    
    try:
        from app.schemas.enums import (
            LogSeverity, AlertSeverity, AlertStatus,
            IncidentStatus, UserRole
        )
        
        # Test log severity
        assert LogSeverity.INFO.value == "info"
        assert LogSeverity.CRITICAL.value == "critical"
        print("  [OK] LogSeverity")
        
        # Test alert severity
        assert AlertSeverity.LOW.value == "low"
        assert AlertSeverity.CRITICAL.value == "critical"
        print("  [OK] AlertSeverity")
        
        # Test alert status
        assert AlertStatus.OPEN.value == "open"
        assert AlertStatus.RESOLVED.value == "resolved"
        print("  [OK] AlertStatus")
        
        # Test incident status
        assert IncidentStatus.OPEN.value == "open"
        assert IncidentStatus.CLOSED.value == "closed"
        print("  [OK] IncidentStatus")
        
        # Test user role
        assert UserRole.ANALYST.value == "analyst"
        assert UserRole.ADMIN.value == "admin"
        print("  [OK] UserRole")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Enum test failed: {e}")
        return False


def test_config():
    """Test configuration."""
    print("\nTesting configuration...")
    
    try:
        from app.utils.config import settings
        
        # Check required settings exist
        assert hasattr(settings, 'secret_key')
        assert hasattr(settings, 'elasticsearch_enabled')
        assert hasattr(settings, 'cors_origins')
        print("  [OK] Config loaded")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Config test failed: {e}")
        return False


def test_password_validation():
    """Test password validation."""
    print("\nTesting password validation...")
    
    try:
        from app.utils.password_validator import validate_password_simple
        
        # Test valid password
        valid, msg = validate_password_simple("password123")
        assert valid == True
        print("  [OK] Valid password accepted")
        
        # Test short password
        valid, msg = validate_password_simple("short")
        assert valid == False
        assert "8 characters" in msg
        print("  [OK] Short password rejected")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Password validation test failed: {e}")
        return False


def test_services_structure():
    """Test service structure."""
    print("\nTesting service structure...")
    
    try:
        from app.services import log_service, alert_service, incident_service
        
        # Check functions exist
        assert hasattr(log_service, 'create_log')
        assert hasattr(log_service, 'get_logs')
        assert hasattr(alert_service, 'create_alert')
        assert hasattr(incident_service, 'create_incident')
        print("  [OK] Service functions exist")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Service structure test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Backend Verification Script")
    print("="*60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Enums", test_enums()))
    results.append(("Configuration", test_config()))
    results.append(("Password Validation", test_password_validation()))
    results.append(("Service Structure", test_services_structure()))
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "[OK]" if passed else "[FAIL]"
        print(f"{symbol} {name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n[OK] All checks passed! Backend is ready.")
        return 0
    else:
        print("\n[FAIL] Some checks failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
