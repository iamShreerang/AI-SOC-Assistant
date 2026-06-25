-- AI SOC Assistant Database Schema for Supabase
-- Run this script in Supabase SQL Editor: https://supabase.com/dashboard/project/_/sql

-- Create enum types
CREATE TYPE user_role AS ENUM ('analyst', 'admin');
CREATE TYPE log_severity AS ENUM ('info', 'warning', 'error', 'critical');
CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE alert_status AS ENUM ('open', 'acknowledged', 'resolved');
CREATE TYPE incident_status AS ENUM ('open', 'in-progress', 'closed');

-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_users_id ON users(id);
CREATE INDEX ix_users_username ON users(username);

-- Create logs table
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    severity log_severity NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP,
    raw TEXT,
    ingested_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_logs_id ON logs(id);
CREATE INDEX ix_logs_source ON logs(source);
CREATE INDEX ix_logs_severity ON logs(severity);
CREATE INDEX ix_logs_ingested_at ON logs(ingested_at);

-- Create alerts table
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    severity alert_severity NOT NULL,
    source VARCHAR(255) NOT NULL,
    description TEXT,
    status alert_status NOT NULL DEFAULT 'open',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_alerts_id ON alerts(id);
CREATE INDEX ix_alerts_severity ON alerts(severity);
CREATE INDEX ix_alerts_source ON alerts(source);
CREATE INDEX ix_alerts_status ON alerts(status);
CREATE INDEX ix_alerts_created_at ON alerts(created_at);

-- Create incidents table
CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status incident_status NOT NULL DEFAULT 'open',
    summary TEXT,
    assigned_to UUID REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_incidents_id ON incidents(id);
CREATE INDEX ix_incidents_status ON incidents(status);
CREATE INDEX ix_incidents_created_at ON incidents(created_at);

-- Create incident_alerts junction table
CREATE TABLE incident_alerts (
    incident_id INTEGER NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (incident_id, alert_id)
);

-- Create ml_predictions table
CREATE TABLE ml_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
    model_version VARCHAR(50) NOT NULL,
    prediction VARCHAR(100) NOT NULL,
    confidence_score FLOAT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ml_predictions_id ON ml_predictions(id);
CREATE INDEX ix_ml_predictions_alert_id ON ml_predictions(alert_id);
CREATE INDEX ix_ml_predictions_created_at ON ml_predictions(created_at);

-- Create audit_logs table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    details TEXT,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_audit_logs_id ON audit_logs(id);
CREATE INDEX ix_audit_logs_username ON audit_logs(username);
CREATE INDEX ix_audit_logs_action ON audit_logs(action);
CREATE INDEX ix_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX ix_audit_logs_timestamp ON audit_logs(timestamp);

-- Insert default users (passwords are hashed with bcrypt)
-- Default analyst: username=analyst, password=analyst123
-- Default admin: username=admin, password=admin123
INSERT INTO users (username, hashed_password, role) VALUES
('analyst', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lkYFZdJcGf5u', 'analyst'),
('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'admin');

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database schema created successfully!';
    RAISE NOTICE 'Default users created:';
    RAISE NOTICE '  - analyst / analyst123';
    RAISE NOTICE '  - admin / admin123';
END $$;
