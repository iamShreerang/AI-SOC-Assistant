import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store';
import { apiService } from '@/services/api';

export const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setAuth } = useAuthStore();

  useEffect(() => {
    const handleCallback = async () => {
      const searchParams = new URLSearchParams(location.search);
      const accessToken = searchParams.get('access_token');
      const refreshToken = searchParams.get('refresh_token');

      if (accessToken && refreshToken) {
        try {
          // Temporarily store in localStorage so getCurrentUser can use it
          localStorage.setItem('access_token', accessToken);
          localStorage.setItem('refresh_token', refreshToken);

          const user = await apiService.getCurrentUser();
          setAuth(user, { access_token: accessToken, refresh_token: refreshToken });
          navigate('/dashboard');
        } catch (error) {
          console.error('Failed to login via OAuth callback:', error);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          navigate('/login?error=oauth_failed');
        }
      } else {
        navigate('/login');
      }
    };

    handleCallback();
  }, [location, navigate, setAuth]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-soc-bg-primary">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-soc-accent-cyan mx-auto mb-4"></div>
        <p className="text-soc-text-secondary">Completing secure sign-in...</p>
      </div>
    </div>
  );
};
