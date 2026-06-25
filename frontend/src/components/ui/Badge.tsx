import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/utils/helpers';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'critical' | 'high' | 'medium' | 'low' | 'info';
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    const variants = {
      default: 'bg-soc-bg-elevated text-soc-text-secondary border-soc-border',
      critical: 'bg-severity-critical/10 text-severity-critical border-severity-critical/50',
      high: 'bg-severity-high/10 text-severity-high border-severity-high/50',
      medium: 'bg-severity-medium/10 text-severity-medium border-severity-medium/50',
      low: 'bg-severity-low/10 text-severity-low border-severity-low/50',
      info: 'bg-severity-info/10 text-severity-info border-severity-info/50',
    };

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border uppercase tracking-wide',
          variants[variant],
          className
        )}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';
