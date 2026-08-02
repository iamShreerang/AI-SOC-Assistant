import { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Check, X, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { apiService } from '@/services/api';
import { cn } from '@/utils/helpers';

// ── Password rules (must match backend validate_password_simple: min 8 chars) ─
interface PasswordRule {
  id: string;
  label: string;
  test: (pw: string) => boolean;
}

const PASSWORD_RULES: PasswordRule[] = [
  { id: 'length',    label: 'At least 8 characters',          test: (pw) => pw.length >= 8 },
  { id: 'uppercase', label: 'At least one uppercase letter',   test: (pw) => /[A-Z]/.test(pw) },
  { id: 'lowercase', label: 'At least one lowercase letter',   test: (pw) => /[a-z]/.test(pw) },
  { id: 'digit',     label: 'At least one number (0–9)',       test: (pw) => /\d/.test(pw) },
  { id: 'special',   label: 'At least one special character (!@#$%^&*)', test: (pw) => /[!@#$%^&*(),.?":{}|<>]/.test(pw) },
];

const getStrength = (pw: string): { score: number; label: string; color: string } => {
  const passed = PASSWORD_RULES.filter((r) => r.test(pw)).length;
  if (passed <= 1) return { score: passed, label: 'Very Weak',  color: 'bg-severity-critical' };
  if (passed === 2) return { score: passed, label: 'Weak',       color: 'bg-severity-high' };
  if (passed === 3) return { score: passed, label: 'Fair',       color: 'bg-severity-medium' };
  if (passed === 4) return { score: passed, label: 'Strong',     color: 'bg-soc-accent-blue' };
  return              { score: passed, label: 'Very Strong', color: 'bg-severity-low' };
};

export const Register = () => {
  const navigate = useNavigate();
  const [username, setUsername]               = useState('');
  const [password, setPassword]               = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword]       = useState(false);
  const [showConfirm, setShowConfirm]         = useState(false);
  const [loading, setLoading]                 = useState(false);
  const [error, setError]                     = useState('');
  const [success, setSuccess]                 = useState(false);

  const strength   = getStrength(password);
  const allPassed  = PASSWORD_RULES.every((r) => r.test(password));
  const passwordsMatch = password === confirmPassword && confirmPassword.length > 0;

  // ── Validate client-side before hitting the API ───────────────────────────
  const validate = (): string => {
    if (username.trim().length < 3)  return 'Username must be at least 3 characters.';
    if (!allPassed)                  return 'Password does not meet all requirements below.';
    if (password !== confirmPassword) return 'Passwords do not match.';
    return '';
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    try {
      await apiService.register({ username: username.trim(), password, role: 'analyst' });
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2500);
    } catch (err: any) {
      // Show the exact reason from the backend (e.g. "Username already taken")
      const detail = err.response?.data?.detail;
      if (err.response?.status === 409) {
        setError(`Username "${username}" is already taken. Please choose a different one.`);
      } else if (err.response?.status === 400) {
        setError(detail || 'Password does not meet server requirements.');
      } else if (err.response?.status === 422) {
        setError('Invalid input. Please check your username and password.');
      } else if (!err.response) {
        setError('Cannot reach the server. Make sure the backend is running on http://localhost:8000.');
      } else {
        setError(detail || 'Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-soc-bg-primary p-4">
      <div className="w-full max-w-md">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-soc-accent-cyan/10 rounded-full mb-4">
            <Shield className="w-8 h-8 text-soc-accent-cyan" aria-hidden="true" />
          </div>
          <h1 className="text-3xl font-bold text-soc-text-primary">Create Account</h1>
          <p className="text-soc-text-muted mt-2">Register for AI SOC Assistant</p>
        </div>

        <div className="bg-soc-bg-secondary border border-soc-border rounded-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-5" noValidate>

            {/* Error banner */}
            {error && (
              <Alert variant="error" onClose={() => setError('')}>
                {error}
              </Alert>
            )}

            {/* Success banner */}
            {success && (
              <Alert variant="success">
                Account created! Redirecting to login…
              </Alert>
            )}

            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-soc-text-secondary mb-2">
                Username
              </label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Choose a username (min 3 chars)"
                required
                autoComplete="username"
                minLength={3}
              />
              {username.length > 0 && username.trim().length < 3 && (
                <p className="mt-1 text-xs text-severity-critical">
                  Username must be at least 3 characters.
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-soc-text-secondary mb-2">
                Password
              </label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a strong password"
                  required
                  autoComplete="new-password"
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-soc-text-muted hover:text-soc-text-primary transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Strength bar — only shown once user starts typing */}
              {password.length > 0 && (
                <div className="mt-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-soc-text-muted">Password strength</span>
                    <span className={cn(
                      'text-xs font-semibold',
                      strength.score <= 1 && 'text-severity-critical',
                      strength.score === 2 && 'text-severity-high',
                      strength.score === 3 && 'text-severity-medium',
                      strength.score === 4 && 'text-soc-accent-blue',
                      strength.score === 5 && 'text-severity-low',
                    )}>
                      {strength.label}
                    </span>
                  </div>
                  {/* 5-segment bar */}
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((seg) => (
                      <div
                        key={seg}
                        className={cn(
                          'h-1.5 flex-1 rounded-full transition-all duration-300',
                          seg <= strength.score ? strength.color : 'bg-soc-bg-elevated'
                        )}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Password rules checklist */}
              <div className="mt-3 space-y-1.5 p-3 bg-soc-bg-tertiary rounded-lg">
                <p className="text-xs font-semibold text-soc-text-secondary mb-2">
                  Password requirements:
                </p>
                {PASSWORD_RULES.map((rule) => {
                  const passed = rule.test(password);
                  return (
                    <div key={rule.id} className="flex items-center gap-2">
                      {passed ? (
                        <Check className="w-3.5 h-3.5 text-severity-low flex-shrink-0" />
                      ) : (
                        <X className="w-3.5 h-3.5 text-soc-text-muted flex-shrink-0" />
                      )}
                      <span className={cn(
                        'text-xs transition-colors',
                        passed ? 'text-severity-low' : 'text-soc-text-muted'
                      )}>
                        {rule.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-soc-text-secondary mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirm ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your password"
                  required
                  autoComplete="new-password"
                  className={cn(
                    'pr-10',
                    confirmPassword.length > 0 && (passwordsMatch
                      ? 'border-severity-low focus:ring-severity-low'
                      : 'border-severity-critical focus:ring-severity-critical')
                  )}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-soc-text-muted hover:text-soc-text-primary transition-colors"
                  aria-label={showConfirm ? 'Hide password' : 'Show password'}
                >
                  {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {confirmPassword.length > 0 && (
                <p className={cn(
                  'mt-1 text-xs flex items-center gap-1',
                  passwordsMatch ? 'text-severity-low' : 'text-severity-critical'
                )}>
                  {passwordsMatch
                    ? <><Check className="w-3 h-3" /> Passwords match</>
                    : <><X className="w-3 h-3" /> Passwords do not match</>
                  }
                </p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={loading || success}
              isLoading={loading}
            >
              {loading ? 'Creating account…' : 'Create Account'}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center" aria-hidden="true">
              <div className="w-full border-t border-soc-border" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-soc-bg-secondary px-2 text-soc-text-muted">Or register with</span>
            </div>
          </div>

          {/* OAuth buttons */}
          <div className="grid grid-cols-2 gap-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
                window.location.href = `${base}/auth/login/google`;
              }}
              className="flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12.24 10.285V13.4h6.887C18.2 15.614 15.645 18 12.24 18c-3.86 0-7-3.14-7-7s3.14-7 7-7c1.7 0 3.3.6 4.6 1.8l2.4-2.4C17.3 1.7 14.9 1 12.24 1 6.58 1 2 5.58 2 11.24s4.58 10.24 10.24 10.24c5.79 0 10.24-4.06 10.24-10.24 0-.69-.06-1.35-.19-1.95H12.24z"/>
              </svg>
              Google
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
                window.location.href = `${base}/auth/login/github`;
              }}
              className="flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.164 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
              </svg>
              GitHub
            </Button>
          </div>

          <div className="mt-6 text-center">
            <p className="text-sm text-soc-text-muted">
              Already have an account?{' '}
              <Link to="/login" className="text-soc-accent-cyan hover:text-soc-accent-cyan/80 transition-colors font-medium">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
