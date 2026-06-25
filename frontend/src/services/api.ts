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

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token');
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: AxiosError) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired, try to refresh
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              const response = await this.refreshToken(refreshToken);
              localStorage.setItem('access_token', response.access_token);
              localStorage.setItem('refresh_token', response.refresh_token);
              
              // Retry original request
              if (error.config) {
                error.config.headers.Authorization = `Bearer ${response.access_token}`;
                return this.api.request(error.config);
              }
            } catch (refreshError) {
              // Refresh failed, logout user
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              window.location.href = '/login';
            }
          } else {
            // No refresh token, logout
            localStorage.removeItem('access_token');
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await this.api.post<AuthTokens>('/auth/login', credentials);
    return response.data;
  }

  async register(data: RegisterData): Promise<User> {
    const response = await this.api.post<User>('/auth/register', data);
    return response.data;
  }

  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await this.api.post<AuthTokens>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get<User>('/auth/users/me');
    return response.data;
  }

  // Alerts
  async getAlerts(filters?: AlertFilters): Promise<Alert[]> {
    const response = await this.api.get<{alerts: Alert[]}>('/alerts', { params: filters });
    return response.data.alerts;
  }

  async getAlertById(id: number): Promise<Alert> {
    const response = await this.api.get<Alert>(`/alerts/${id}`);
    return response.data;
  }

  async createAlert(data: AlertCreateRequest): Promise<Alert> {
    const response = await this.api.post<Alert>('/alerts', data);
    return response.data;
  }

  async updateAlertStatus(id: number, data: AlertUpdateRequest): Promise<Alert> {
    const response = await this.api.patch<Alert>(`/alerts/${id}/status`, data);
    return response.data;
  }

  async bulkUpdateAlertStatus(ids: number[], status: string): Promise<Alert[]> {
    const response = await this.api.post<Alert[]>('/alerts/bulk-status', {
      alert_ids: ids,
      status,
    });
    return response.data;
  }

  // Incidents
  async getIncidents(filters?: IncidentFilters): Promise<Incident[]> {
    const response = await this.api.get<{incidents: Incident[]}>('/incidents', { params: filters });
    return response.data.incidents;
  }

  async getIncidentById(id: number): Promise<Incident> {
    const response = await this.api.get<Incident>(`/incidents/${id}`);
    return response.data;
  }

  async createIncident(data: IncidentCreateRequest): Promise<Incident> {
    const response = await this.api.post<Incident>('/incidents', data);
    return response.data;
  }

  async updateIncidentStatus(id: number, data: IncidentStatusUpdate): Promise<Incident> {
    const response = await this.api.patch<Incident>(`/incidents/${id}/status`, data);
    return response.data;
  }

  // Logs
  async getLogs(filters?: LogFilters): Promise<LogEntry[]> {
    const response = await this.api.get<{logs: LogEntry[]}>('/logs', { params: filters });
    return response.data.logs;
  }

  async getLogById(id: number): Promise<LogEntry> {
    const response = await this.api.get<LogEntry>(`/logs/${id}`);
    return response.data;
  }

  async ingestLog(data: LogCreateRequest): Promise<LogEntry> {
    const response = await this.api.post<LogEntry>('/ingest/logs', data);
    return response.data;
  }

  // Statistics
  async getDashboardSummary(): Promise<DashboardSummary> {
    const response = await this.api.get<DashboardSummary>('/stats/summary');
    return response.data;
  }

  async getRecentActivity(hours: number = 24): Promise<RecentActivity> {
    const response = await this.api.get<RecentActivity>('/stats/activity', {
      params: { hours },
    });
    return response.data;
  }

  async getAlertTrends(): Promise<AlertTrends> {
    const response = await this.api.get<AlertTrends>('/stats/trends');
    return response.data;
  }

  // Search
  async search(query: string): Promise<SearchResults> {
    const response = await this.api.get<SearchResults>('/search/all', {
      params: { q: query },
    });
    return response.data;
  }

  // Export
  async exportLogs(params: any): Promise<Blob> {
    const response = await this.api.get('/export/logs', {
      params,
      responseType: 'blob',
    });
    return response.data;
  }

  async exportAlerts(params: any): Promise<Blob> {
    const response = await this.api.get('/export/alerts', {
      params,
      responseType: 'blob',
    });
    return response.data;
  }

  async exportIncidents(params: any): Promise<Blob> {
    const response = await this.api.get('/export/incidents', {
      params,
      responseType: 'blob',
    });
    return response.data;
  }

  // Health Check
  async checkHealth(): Promise<{ status: string }> {
    const response = await this.api.get<{ status: string }>('/health');
    return response.data;
  }
}

export const apiService = new ApiService();
