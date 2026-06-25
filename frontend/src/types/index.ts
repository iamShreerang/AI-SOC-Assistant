// User and Authentication Types
export interface User {
  username: string;
  role: UserRole;
  is_active: boolean;
}

export type UserRole = 'analyst' | 'admin';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  password: string;
  role?: UserRole;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Log Types
export type LogSeverity = 'info' | 'warning' | 'error' | 'critical';

export interface LogEntry {
  id: number;
  source: string;
  severity: LogSeverity;
  message: string;
  timestamp: string | null;
  raw: string | null;
  ingested_at: string;
}

export interface LogCreateRequest {
  source: string;
  severity: LogSeverity;
  message: string;
  timestamp?: string;
  raw?: string;
}

// Alert Types
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type AlertStatus = 'open' | 'acknowledged' | 'resolved';

export interface Alert {
  id: number;
  title: string;
  severity: AlertSeverity;
  source: string;
  description: string | null;
  status: AlertStatus;
  created_at: string;
}

export interface AlertCreateRequest {
  title: string;
  severity: AlertSeverity;
  source: string;
  description?: string;
}

export interface AlertUpdateRequest {
  status: AlertStatus;
}

// Incident Types
export type IncidentStatus = 'open' | 'in-progress' | 'closed';

export interface Incident {
  id: number;
  title: string;
  description: string | null;
  alert_ids: number[];
  status: IncidentStatus;
  summary: string | null;
  created_at: string;
}

export interface IncidentCreateRequest {
  title: string;
  description?: string;
  alert_ids?: number[];
}

export interface IncidentStatusUpdate {
  status: IncidentStatus;
}

// Statistics Types
export interface DashboardSummary {
  total_logs: number;
  total_alerts: number;
  total_incidents: number;
  open_alerts: number;
  open_incidents: number;
  critical_alerts: number;
  alerts_by_severity: SeverityBreakdown;
  alerts_by_status: StatusBreakdown;
  incidents_by_status: IncidentStatusBreakdown;
  logs_by_severity: LogSeverityBreakdown;
}

export interface SeverityBreakdown {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

export interface StatusBreakdown {
  open: number;
  acknowledged: number;
  resolved: number;
}

export interface IncidentStatusBreakdown {
  open: number;
  'in-progress': number;
  closed: number;
}

export interface LogSeverityBreakdown {
  info: number;
  warning: number;
  error: number;
  critical: number;
}

export interface RecentActivity {
  time_window_hours: number;
  logs_count: number;
  alerts_count: number;
  incidents_count: number;
  critical_alerts_count: number;
}

export interface AlertTrends {
  total_alerts: number;
  resolved_alerts: number;
  resolution_rate_percent: number;
  top_sources: SourceCount[];
}

export interface SourceCount {
  source: string;
  count: number;
}

// Search Types
export interface SearchResults {
  logs: LogEntry[];
  alerts: Alert[];
  incidents: Incident[];
}

// API Response Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface ApiError {
  detail: string;
  status?: number;
}

// Chart Data Types
export interface ChartDataPoint {
  name: string;
  value: number;
  color?: string;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  count: number;
  severity?: AlertSeverity;
}

// Filter Types
export interface LogFilters {
  severity?: LogSeverity;
  source?: string;
  limit?: number;
  skip?: number;
}

export interface AlertFilters {
  severity?: AlertSeverity;
  status?: AlertStatus;
  source?: string;
  limit?: number;
  skip?: number;
}

export interface IncidentFilters {
  status?: IncidentStatus;
  limit?: number;
  skip?: number;
}

// System Health Types
export interface SystemHealth {
  database: boolean;
  elasticsearch: boolean;
  kafka: boolean;
  spark: boolean;
  ml_model: boolean;
}

// Notification Types
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// Settings Types
export interface UserSettings {
  notifications_enabled: boolean;
  email_notifications: boolean;
  auto_refresh: boolean;
  refresh_interval: number;
  theme: 'dark' | 'light';
}

// ML Analytics Types
export interface MLPrediction {
  id: string;
  alert_id: number;
  model_version: string;
  prediction: string;
  confidence_score: number;
  created_at: string;
}

export interface AnomalyDetectionResult {
  timestamp: string;
  anomaly_score: number;
  is_anomaly: boolean;
  features: Record<string, number>;
}

// Export Types
export type ExportFormat = 'csv' | 'json';

export interface ExportParams {
  format: ExportFormat;
  start_date?: string;
  end_date?: string;
  severity?: AlertSeverity;
  status?: AlertStatus;
}
