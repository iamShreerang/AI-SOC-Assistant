import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  LoginCredentials,
  RegisterData,
  AuthTokens,
  User,
  Alert,
  AlertCreateRequest,
  AlertUpdateRequest,
  AlertFilters,
  Incident,
  IncidentCreateRequest,
  IncidentStatusUpdate,
  IncidentFilters,
  LogEntry,
  LogCreateRequest,
  LogFilters,
  DashboardSummary,
  RecentActivity,
  AlertTrends,
  SearchResults,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ML Analytics shape returned by GET /stats/ml
export interface MLAnalyticsData {
  model_accuracy: number;
  predictions_today: number;
  anomalies_detected: number;
  anomaly_data: Array<{ name: string; value: number }>;
  threat_classification: Array<{ name: string; value: number; color?: string }>;
  predictions: Array<{
    id: string;
    alert_id: number;
    threat: string;
    confidence: number;
    severity: string;
  }>;
}

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: { 'Content-Type': 'application/json' },
    });
    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.api.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token');
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: AxiosError) => Promise.reject(error)
    );

    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              const response = await this.refreshToken(refreshToken);
              localStorage.setItem('access_token', response.access_token);
              localStorage.setItem('refresh_token', response.refresh_token);
              if (error.config) {
                error.config.headers.Authorization = `Bearer ${response.access_token}`;
                return this.api.request(error.config);
              }
            } catch {
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              window.location.href = '/login';
            }
          } else {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const res = await this.api.post<AuthTokens>('/auth/login', credentials);
    return res.data;
  }

  async register(data: RegisterData): Promise<User> {
    const res = await this.api.post<User>('/auth/register', data);
    return res.data;
  }

  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const res = await this.api.post<AuthTokens>('/auth/refresh', { refresh_token: refreshToken });
    return res.data;
  }

  async getCurrentUser(): Promise<User> {
    const res = await this.api.get<User>('/auth/users/me');
    return res.data;
  }

  // Alerts
  async getAlerts(filters?: AlertFilters): Promise<Alert[]> {
    const res = await this.api.get<{ alerts: Alert[] } | Alert[]>('/alerts', { params: filters });
    return Array.isArray(res.data) ? res.data : (res.data as any).alerts ?? [];
  }

  async getAlertById(id: number): Promise<Alert> {
    const res = await this.api.get<Alert>(`/alerts/${id}`);
    return res.data;
  }

  async createAlert(data: AlertCreateRequest): Promise<Alert> {
    const res = await this.api.post<Alert>('/alerts', data);
    return res.data;
  }

  async updateAlertStatus(id: number, data: AlertUpdateRequest): Promise<Alert> {
    const res = await this.api.patch<Alert>(`/alerts/${id}`, data);
    return res.data;
  }

  async bulkUpdateAlertStatus(ids: number[], status: string): Promise<Alert[]> {
    const res = await this.api.post<Alert[]>('/alerts/bulk', { alert_ids: ids, status });
    return res.data;
  }

  // Incidents
  async getIncidents(filters?: IncidentFilters): Promise<Incident[]> {
    const res = await this.api.get<{ incidents: Incident[] } | Incident[]>('/incidents', { params: filters });
    return Array.isArray(res.data) ? res.data : (res.data as any).incidents ?? [];
  }

  async getIncidentById(id: number): Promise<Incident> {
    const res = await this.api.get<Incident>(`/incidents/${id}`);
    return res.data;
  }

  async createIncident(data: IncidentCreateRequest): Promise<Incident> {
    const res = await this.api.post<Incident>('/incidents', data);
    return res.data;
  }

  async updateIncidentStatus(id: number, data: IncidentStatusUpdate): Promise<Incident> {
    const res = await this.api.patch<Incident>(`/incidents/${id}/status`, data);
    return res.data;
  }

  // Logs
  async getLogs(filters?: LogFilters): Promise<LogEntry[]> {
    const res = await this.api.get<{ logs: LogEntry[] } | LogEntry[]>('/logs', { params: filters });
    return Array.isArray(res.data) ? res.data : (res.data as any).logs ?? [];
  }

  async getLogById(id: number): Promise<LogEntry> {
    const res = await this.api.get<LogEntry>(`/logs/${id}`);
    return res.data;
  }

  async ingestLog(data: LogCreateRequest): Promise<LogEntry> {
    const res = await this.api.post<LogEntry>('/ingest/logs', data);
    return res.data;
  }

  // Statistics
  async getDashboardSummary(): Promise<DashboardSummary> {
    const res = await this.api.get<DashboardSummary>('/stats/summary');
    return res.data;
  }

  async getRecentActivity(hours = 24): Promise<RecentActivity> {
    const res = await this.api.get<RecentActivity>('/stats/activity', { params: { hours } });
    return res.data;
  }

  async getAlertTrends(): Promise<AlertTrends> {
    const res = await this.api.get<AlertTrends>('/stats/alerts/trends');
    return res.data;
  }

  // ML Analytics — real data from GET /stats/ml (no Math.random())
  async getMLAnalytics(): Promise<MLAnalyticsData> {
    const res = await this.api.get<MLAnalyticsData>('/stats/ml');
    return res.data;
  }

  // Search
  async search(query: string): Promise<SearchResults> {
    const res = await this.api.get<SearchResults>('/search', { params: { q: query } });
    return res.data;
  }

  // Export
  async exportLogs(params: Record<string, unknown>): Promise<Blob> {
    const res = await this.api.get('/export/logs', { params, responseType: 'blob' });
    return res.data;
  }

  async exportAlerts(params: Record<string, unknown>): Promise<Blob> {
    const res = await this.api.get('/export/alerts', { params, responseType: 'blob' });
    return res.data;
  }

  async exportIncidents(params: Record<string, unknown>): Promise<Blob> {
    const res = await this.api.get('/export/incidents', { params, responseType: 'blob' });
    return res.data;
  }

  // Health
  async checkHealth(): Promise<{ status: string; components: Record<string, unknown> }> {
    try {
      const res = await this.api.get<{ status: string; components?: Record<string, unknown> }>('/health');
      return {
        status: res.data.status,
        components: res.data.components ?? {
          database: res.data.status === 'ok',
          elasticsearch: { enabled: false, healthy: false },
          kafka: false,
          spark: false,
          ml_model: false,
          llm: false,
        },
      };
    } catch {
      return {
        status: 'error',
        components: {
          database: false,
          elasticsearch: { enabled: false, healthy: false },
          kafka: false,
          spark: false,
          ml_model: false,
          llm: false,
        },
      };
    }
  }
}

export const apiService = new ApiService();
