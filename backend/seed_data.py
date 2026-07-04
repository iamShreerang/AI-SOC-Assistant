import sys
from datetime import datetime
from app.database import SessionLocal
from app.models.database import Log, Alert, Incident, IncidentAlert
from app.schemas.enums import LogSeverity, AlertSeverity, AlertStatus, IncidentStatus

def seed():
    db = SessionLocal()
    try:
        # Add Logs
        log1 = Log(source="firewall", severity=LogSeverity.INFO, message="Connection accepted from 192.168.1.5", raw='{"src": "192.168.1.5", "action": "accept"}', ingested_at=datetime.utcnow())
        log2 = Log(source="ids", severity=LogSeverity.CRITICAL, message="Multiple failed login attempts detected", raw='{"src": "10.0.0.8", "action": "deny"}', ingested_at=datetime.utcnow())
        db.add_all([log1, log2])
        db.commit()

        # Add Alerts
        alert1 = Alert(title="Suspicious Login Activity", severity=AlertSeverity.HIGH, source="auth-service", description="User admin failed to login 50 times in 10 minutes", status=AlertStatus.OPEN, created_at=datetime.utcnow())
        alert2 = Alert(title="Data Exfiltration", severity=AlertSeverity.CRITICAL, source="dlp", description="Large data transfer to external IP 104.22.45.1", status=AlertStatus.ACKNOWLEDGED, created_at=datetime.utcnow())
        db.add_all([alert1, alert2])
        db.commit()

        # Add Incident
        incident1 = Incident(title="Potential Account Compromise", description="Investigating multiple alerts related to admin account.", status=IncidentStatus.IN_PROGRESS, summary="AI Summary: High confidence account compromise.", created_at=datetime.utcnow())
        db.add(incident1)
        db.commit()

        # Link alert to incident
        ia = IncidentAlert(incident_id=incident1.id, alert_id=alert1.id)
        db.add(ia)
        db.commit()

        print(f"Seed complete. Created Alert IDs: {alert1.id}, {alert2.id}. Created Incident ID: {incident1.id}. Created Log IDs: {log1.id}, {log2.id}")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
