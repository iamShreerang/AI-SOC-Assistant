import { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { apiService } from '@/services/api';

export const Register = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      await apiService.register({ username, password, role: 'analyst' });
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
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
          <h1 className="text-3xl font-bold text-soc-text-primary">Create Account</h1>
          <p className="text-soc-text-muted mt-2">Register for AI SOC Assistant</p>
        </div>

        <div className="bg-soc-bg-secondary border border-soc-border rounded-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <Alert variant="error" onClose={() => setError('')}>
                {error}
              </Alert>
            )}
            {success && (
              <Alert variant="success">
                Registration successful! Redirecting to login...
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
                placeholder="Choose a username"
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
                placeholder="Create a password"
                required
                autoComplete="new-password"
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-soc-text-secondary mb-2">
                Confirm Password
              </label>
              <Input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm your password"
                required
                autoComplete="new-password"
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Creating account...' : 'Create account'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-soc-text-muted">
              Already have an account?{' '}
              <Link
                to="/login"
                className="text-soc-accent-cyan hover:text-soc-accent-cyan/80 transition-colors"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
