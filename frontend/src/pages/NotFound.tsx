import { useNavigate } from 'react-router-dom';
import { Shield, Home } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-soc-bg-primary p-4">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-soc-accent-cyan/10 rounded-full mb-6">
          <Shield className="w-10 h-10 text-soc-accent-cyan" aria-hidden="true" />
        </div>
        <h1 className="text-6xl font-bold text-soc-text-primary mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-soc-text-primary mb-4">Page Not Found</h2>
        <p className="text-soc-text-muted mb-8 max-w-md">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Button onClick={() => navigate('/dashboard')}>
          <Home className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>
      </div>
    </div>
  );
};
