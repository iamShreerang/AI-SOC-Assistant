import { useState, FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { Shield, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';

export const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      setSuccess(true);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-soc-bg-primary p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-soc-accent-cyan/10 rounded-full mb-4">
            <Shield className="w-8 h-8 text-soc-accent-cyan" aria-hidden="true" />
          </div>
          <h1 className="text-3xl font-bold text-soc-text-primary">Reset Password</h1>
          <p className="text-soc-text-muted mt-2">Enter your email to reset your password</p>
        </div>

        <div className="bg-soc-bg-secondary border border-soc-border rounded-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {success && (
              <Alert variant="success">
                Password reset instructions have been sent to your email.
              </Alert>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-soc-text-secondary mb-2">
                Email Address
              </label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Sending...' : 'Send reset instructions'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 text-sm text-soc-accent-cyan hover:text-soc-accent-cyan/80 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
