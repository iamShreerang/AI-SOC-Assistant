import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/utils/helpers';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', children, disabled, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium transition-all rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-soc-bg-primary disabled:opacity-50 disabled:cursor-not-allowed';
    
    const variants = {
      primary: 'bg-soc-accent-cyan hover:bg-soc-accent-cyan/80 text-white focus:ring-soc-accent-cyan',
      secondary: 'bg-soc-bg-tertiary hover:bg-soc-bg-elevated text-soc-text-primary border border-soc-border focus:ring-soc-accent-blue',
      danger: 'bg-severity-critical hover:bg-severity-critical/80 text-white focus:ring-severity-critical',
      ghost: 'hover:bg-soc-bg-tertiary text-soc-text-secondary focus:ring-soc-accent-cyan',
    };

    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-6 py-3 text-lg',
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
