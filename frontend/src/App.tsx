import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store';
import { apiService } from '@/services/api';
import {
  Login,
  Register,
  ForgotPassword,
  AuthCallback,
  Dashboard,
  Monitoring,
  Alerts,
  AlertDetail,
  Incidents,
  IncidentDetail,
  MLAnalytics,
  LogExplorer,
  Settings,
  NotFound,
} from '@/pages';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuthStore();
  return !isAuthenticated ? <>{children}</> : <Navigate to="/dashboard" replace />;
};

function App() {
  const { isAuthenticated, setAuth, clearAuth } = useAuthStore();
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (accessToken && refreshToken && !isAuthenticated) {
        try {
          const user = await apiService.getCurrentUser();
          setAuth(user, { access_token: accessToken, refresh_token: refreshToken });
        } catch (error) {
          clearAuth();
        }
      }
      setIsInitializing(false);
    };
    
    initAuth();
  }, [isAuthenticated, setAuth, clearAuth]);

  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-soc-bg-primary">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-soc-accent-cyan"></div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          }
        />
        <Route
          path="/forgot-password"
          element={
            <PublicRoute>
              <ForgotPassword />
            </PublicRoute>
          }
        />
        <Route
          path="/auth/callback"
          element={
            <PublicRoute>
              <AuthCallback />
            </PublicRoute>
          }
        />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/monitoring"
          element={
            <ProtectedRoute>
              <Monitoring />
            </ProtectedRoute>
          }
        />
        <Route
          path="/alerts"
          element={
            <ProtectedRoute>
              <Alerts />
            </ProtectedRoute>
          }
        />
        <Route
          path="/alerts/:id"
          element={
            <ProtectedRoute>
              <AlertDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/incidents"
          element={
            <ProtectedRoute>
              <Incidents />
            </ProtectedRoute>
          }
        />
        <Route
          path="/incidents/:id"
          element={
            <ProtectedRoute>
              <IncidentDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/ml-analytics"
          element={
            <ProtectedRoute>
              <MLAnalytics />
            </ProtectedRoute>
          }
        />
        <Route
          path="/log-explorer"
          element={
            <ProtectedRoute>
              <LogExplorer />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App;
