import { Link } from 'react-router-dom';
import { Shield, Home } from 'lucide-react';
import { Button } from '@/components/ui/Button';

const NotFound = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-soc-bg-primary p-4">
      <div className="text-center">
        <div className="inline-flex items-center justify-center h-20 w-20 rounded-2xl bg-gradient-to-br from-soc-accent-cyan to-soc-accent-blue shadow-glow mb-6">
          <Shield className="h-12 w-12 text-white" />
        </div>
        <h1 className="text-6xl font-bold text-soc-text-primary mb-4">404</h1>
        <h2 className="text-2xl font-semibold text-soc-text-primary mb-2">
          Page Not Found
        </h2>
        <p className="text-soc-text-muted mb-8 max-w-md">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link to="/dashboard">
          <Button variant="primary" size="lg" className="gap-2">
            <Home className="h-5 w-5" />
            Back to Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
