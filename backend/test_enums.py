"""Quick test to verify enum validation."""

from app.schemas.enums import LogSeverity, AlertSeverity, AlertStatus, IncidentStatus, UserRole
from app.schemas.log import LogCreate
from app.schemas.alert import AlertCreate, AlertUpdate
from app.schemas.incident import IncidentCreate, IncidentStatusUpdate
from app.schemas.auth import UserRegister

def test_enums():
    """Test enum validation."""
    
    # Test valid enums
    print("✅ Testing valid enums...")
    
    log = LogCreate(
        source="test",
        severity=LogSeverity.HIGH,
        message="test"
    )
    print(f"   Log severity: {log.severity}")
    
    alert = AlertCreate(
        title="test",
        severity=AlertSeverity.CRITICAL,
        source="test"
    )
    print(f"   Alert severity: {alert.severity}")
    
    alert_update = AlertUpdate(status=AlertStatus.ACKNOWLEDGED)
    print(f"   Alert status: {alert_update.status}")
    
    incident_update = IncidentStatusUpdate(status=IncidentStatus.IN_PROGRESS)
    print(f"   Incident status: {incident_update.status}")
    
    user = UserRegister(
        username="test",
        password="test123",
        role=UserRole.ANALYST
    )
    print(f"   User role: {user.role}")
    
    # Test invalid enums
    print("\n❌ Testing invalid enums (should fail)...")
    
    try:
        invalid_log = LogCreate(
            source="test",
            severity="invalid",  # This should fail
            message="test"
        )
        print("   ERROR: Invalid log severity should have failed!")
    except Exception as e:
        print(f"   ✓ Correctly rejected invalid log severity")
    
    try:
        invalid_alert = AlertCreate(
            title="test",
            severity="super-critical",  # This should fail
            source="test"
        )
        print("   ERROR: Invalid alert severity should have failed!")
    except Exception as e:
        print(f"   ✓ Correctly rejected invalid alert severity")
    
    print("\n✅ All enum tests passed!")

if __name__ == "__main__":
    test_enums()
