"""Initial database schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE user_role AS ENUM ('analyst', 'admin')")
    op.execute("CREATE TYPE log_severity AS ENUM ('info', 'warning', 'error', 'critical')")
    op.execute("CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical')")
    op.execute("CREATE TYPE alert_status AS ENUM ('open', 'acknowledged', 'resolved')")
    op.execute("CREATE TYPE incident_status AS ENUM ('open', 'in-progress', 'closed')")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.Enum('analyst', 'admin', name='user_role'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'])
    
    # Create logs table
    op.create_table(
        'logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('source', sa.String(255), nullable=False),
        sa.Column('severity', sa.Enum('info', 'warning', 'error', 'critical', name='log_severity'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('raw', sa.Text(), nullable=True),
        sa.Column('ingested_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_logs_id', 'logs', ['id'])
    op.create_index('ix_logs_source', 'logs', ['source'])
    op.create_index('ix_logs_severity', 'logs', ['severity'])
    op.create_index('ix_logs_ingested_at', 'logs', ['ingested_at'])
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='alert_severity'), nullable=False),
        sa.Column('source', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('open', 'acknowledged', 'resolved', name='alert_status'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_alerts_id', 'alerts', ['id'])
    op.create_index('ix_alerts_severity', 'alerts', ['severity'])
    op.create_index('ix_alerts_source', 'alerts', ['source'])
    op.create_index('ix_alerts_status', 'alerts', ['status'])
    op.create_index('ix_alerts_created_at', 'alerts', ['created_at'])
    
    # Create incidents table
    op.create_table(
        'incidents',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('open', 'in-progress', 'closed', name='incident_status'), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id']),
    )
    op.create_index('ix_incidents_id', 'incidents', ['id'])
    op.create_index('ix_incidents_status', 'incidents', ['status'])
    op.create_index('ix_incidents_created_at', 'incidents', ['created_at'])
    
    # Create incident_alerts junction table
    op.create_table(
        'incident_alerts',
        sa.Column('incident_id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('incident_id', 'alert_id'),
    )
    
    # Create ml_predictions table
    op.create_table(
        'ml_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('alert_id', sa.Integer(), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('prediction', sa.String(100), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_ml_predictions_id', 'ml_predictions', ['id'])
    op.create_index('ix_ml_predictions_alert_id', 'ml_predictions', ['alert_id'])
    op.create_index('ix_ml_predictions_created_at', 'ml_predictions', ['created_at'])
    
    # Create service_heartbeats table (Spark liveness tracking)
    op.create_table(
        'service_heartbeats',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('service', sa.String(50), nullable=False, unique=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('last_seen', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_service_heartbeats_id', 'service_heartbeats', ['id'])
    op.create_index('ix_service_heartbeats_service', 'service_heartbeats', ['service'])
    op.create_index('ix_service_heartbeats_last_seen', 'service_heartbeats', ['last_seen'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])
    op.create_index('ix_audit_logs_username', 'audit_logs', ['username'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('service_heartbeats')
    op.drop_table('audit_logs')
    op.drop_table('ml_predictions')
    op.drop_table('incident_alerts')
    op.drop_table('incidents')
    op.drop_table('alerts')
    op.drop_table('logs')
    op.drop_table('users')
    
    # Drop enum types
    op.execute('DROP TYPE incident_status')
    op.execute('DROP TYPE alert_status')
    op.execute('DROP TYPE alert_severity')
    op.execute('DROP TYPE log_severity')
    op.execute('DROP TYPE user_role')
