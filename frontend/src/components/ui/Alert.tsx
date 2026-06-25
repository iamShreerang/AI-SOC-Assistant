import { HTMLAttributes } from 'react';
import { AlertCircle, CheckCircle, Info, XCircle, X } from 'lucide-react';
import { cn } from '@/utils/helpers';

interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  onClose?: () => void;
}

export const Alert = ({
  className,
  variant = 'info',
  title,
  children,
  onClose,
  ...props
}: AlertProps) => {
  const variants = {
    info: {
      container: 'bg-severity-info/10 border-severity-info/50 text-severity-info',
      icon: Info,
    },
    success: {
      container: 'bg-severity-low/10 border-severity-low/50 text-severity-low',
      icon: CheckCircle,
    },
    warning: {
      container: 'bg-severity-medium/10 border-severity-medium/50 text-severity-medium',
      icon: AlertCircle,
    },
    error: {
      container: 'bg-severity-critical/10 border-severity-critical/50 text-severity-critical',
      icon: XCircle,
    },
  };

  const { container, icon: Icon } = variants[variant];

  return (
    <div
      className={cn(
        'relative rounded-lg border p-4 flex items-start gap-3',
        container,
        className
      )}
      role="alert"
      {...props}
    >
      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div className="flex-1">
        {title && <h4 className="font-semibold mb-1">{title}</h4>}
        <div className="text-sm text-soc-text-secondary">{children}</div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="flex-shrink-0 hover:opacity-70 transition-opacity"
          aria-label="Close"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
