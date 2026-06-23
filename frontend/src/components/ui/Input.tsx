import { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/utils/helpers';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', error, ...props }, ref) => {
    return (
      <div className="w-full">
        <input
          type={type}
          ref={ref}
          className={cn(
            'w-full px-4 py-2 bg-soc-bg-tertiary border rounded-lg text-soc-text-primary placeholder:text-soc-text-muted',
            'focus:outline-none focus:ring-2 focus:ring-soc-accent-cyan focus:border-transparent',
            'disabled:opacity-50 disabled:cursor-not-allowed transition-all',
            error ? 'border-severity-critical' : 'border-soc-border',
            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1 text-sm text-severity-critical">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
