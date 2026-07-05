import { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { apiService } from '@/services/api';
import { useAuthStore } from '@/store';

export const Login = () => {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const tokens = await apiService.login({ username, password });
      // Store tokens temporarily so apiService.getCurrentUser() can use them
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      
      const user = await apiService.getCurrentUser();
      setAuth(user, tokens);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-soc-bg-primary p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-soc-accent-cyan/10 rounded-full mb-4">
            <Shield className="w-8 h-8 text-soc-accent-cyan" aria-hidden="true" />
          </div>
          <h1 className="text-3xl font-bold text-soc-text-primary">AI SOC Assistant</h1>
          <p className="text-soc-text-muted mt-2">Sign in to your account</p>
        </div>

        <div className="bg-soc-bg-secondary border border-soc-border rounded-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <Alert variant="error" onClose={() => setError('')}>
                {error}
              </Alert>
            )}

            <div>
              <label htmlFor="username" className="block text-sm font-medium text-soc-text-secondary mb-2">
                Username
              </label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
                autoComplete="username"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-soc-text-secondary mb-2">
                Password
              </label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                autoComplete="current-password"
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center" aria-hidden="true">
              <div className="w-full border-t border-soc-border"></div>
            </div>
            <div className="relative flex justify-center text-sm font-medium">
              <span className="bg-soc-bg-secondary px-2 text-soc-text-muted">Or continue with</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
                window.location.href = `${apiBase}/auth/login/google`;
              }}
              className="flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5 text-soc-text-primary" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12.24 10.285V13.4h6.887C18.2 15.614 15.645 18 12.24 18c-3.86 0-7-3.14-7-7s3.14-7 7-7c1.7 0 3.3.6 4.6 1.8l2.4-2.4C17.3 1.7 14.9 1 12.24 1 6.58 1 2 5.58 2 11.24s4.58 10.24 10.24 10.24c5.79 0 10.24-4.06 10.24-10.24 0-.69-.06-1.35-.19-1.95H12.24z"/>
              </svg>
              Google
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
                window.location.href = `${apiBase}/auth/login/github`;
              }}
              className="flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5 text-soc-text-primary" viewBox="0 0 24 24" fill="currentColor">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.164 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
              </svg>
              GitHub
            </Button>
          </div>

          <div className="mt-6 text-center space-y-2">
            <Link
              to="/forgot-password"
              className="text-sm text-soc-accent-cyan hover:text-soc-accent-cyan/80 transition-colors"
            >
              Forgot password?
            </Link>
            <p className="text-sm text-soc-text-muted">
              Don't have an account?{' '}
              <Link
                to="/register"
                className="text-soc-accent-cyan hover:text-soc-accent-cyan/80 transition-colors"
              >
                Register
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
