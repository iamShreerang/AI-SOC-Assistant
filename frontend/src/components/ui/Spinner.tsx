import { HTMLAttributes } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/utils/helpers';

interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
}

export const Spinner = ({ className, size = 'md', ...props }: SpinnerProps) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div className={cn('flex items-center justify-center', className)} {...props}>
      <Loader2 className={cn('animate-spin text-soc-accent-cyan', sizes[size])} />
    </div>
  );
};

export const LoadingOverlay = ({ message = 'Loading...' }: { message?: string }) => (
  <div className="fixed inset-0 bg-soc-bg-primary/80 backdrop-blur-sm flex items-center justify-center z-50">
    <div className="text-center">
      <Spinner size="lg" />
      <p className="mt-4 text-soc-text-secondary">{message}</p>
    </div>
  </div>
);
