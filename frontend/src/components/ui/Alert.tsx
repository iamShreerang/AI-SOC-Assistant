import { useEffect, HTMLAttributes } from 'react';
import { X, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react';
import { cn } from '@/utils/helpers';
import { useNotificationStore } from '@/store';

// ── Inline alert banner (used in Settings etc.) ──────────────────────────────
interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'success' | 'error' | 'warning' | 'info';
  children: React.ReactNode;
  onClose?: () => void;
}

export const Alert = ({ variant = 'info', className, children, onClose, ...props }: AlertProps) => {
  const styles = {
    success: 'bg-severity-low/10 border-severity-low text-severity-low',
    error: 'bg-severity-critical/10 border-severity-critical text-severity-critical',
    warning: 'bg-severity-medium/10 border-severity-medium text-severity-medium',
    info: 'bg-severity-info/10 border-severity-info text-severity-info',
  };

  const icons = {
    success: <CheckCircle className="h-4 w-4 flex-shrink-0" />,
    error: <XCircle className="h-4 w-4 flex-shrink-0" />,
    warning: <AlertTriangle className="h-4 w-4 flex-shrink-0" />,
    info: <Info className="h-4 w-4 flex-shrink-0" />,
  };

  return (
    <div
      className={cn('flex items-center gap-3 p-4 rounded-lg border', styles[variant], className)}
      role="alert"
      {...props}
    >
      {icons[variant]}
      <span className="text-sm text-soc-text-primary flex-1">{children}</span>
      {onClose && (
        <button onClick={onClose} className="flex-shrink-0 text-soc-text-muted hover:text-soc-text-primary transition-colors" aria-label="Dismiss">
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
};

// ── Toast notification stack (rendered in MainLayout) ─────────────────────────
export const AlertNotification = () => {
  const { notifications, clearNotification } = useNotificationStore();

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 pointer-events-none">
      {notifications.slice(0, 5).map((notification) => (
        <AlertItem
          key={notification.id}
          {...notification}
          onClose={() => clearNotification(notification.id)}
        />
      ))}
    </div>
  );
};

interface AlertItemProps {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  onClose: () => void;
}

const AlertItem = ({ type, title, message, onClose }: AlertItemProps) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const icons = {
    success: <CheckCircle className="h-5 w-5" />,
    error: <XCircle className="h-5 w-5" />,
    warning: <AlertTriangle className="h-5 w-5" />,
    info: <Info className="h-5 w-5" />,
  };

  const styles = {
    success: 'border-severity-low text-severity-low',
    error: 'border-severity-critical text-severity-critical',
    warning: 'border-severity-medium text-severity-medium',
    info: 'border-severity-info text-severity-info',
  };

  return (
    <div
      className={cn(
        'pointer-events-auto min-w-[320px] max-w-md p-4 rounded-lg border shadow-lg',
        'bg-soc-bg-secondary animate-slide-down',
        styles[type]
      )}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">{icons[type]}</div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-soc-text-primary">{title}</h4>
          <p className="text-sm text-soc-text-secondary mt-1">{message}</p>
        </div>
        <button
          onClick={onClose}
          className="flex-shrink-0 text-soc-text-muted hover:text-soc-text-primary transition-colors"
          aria-label="Dismiss notification"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};
