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
