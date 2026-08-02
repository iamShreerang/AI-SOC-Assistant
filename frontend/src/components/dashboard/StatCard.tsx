import { LucideIcon } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';
import { cn } from '@/utils/helpers';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
  iconColor?: string;
}

export const StatCard = ({
  title,
  value,
  icon: Icon,
  trend,
  className,
  iconColor = 'text-soc-accent-cyan',
}: StatCardProps) => {
  return (
    <Card className={cn('hover:border-soc-accent-cyan/50 transition-all', className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm text-soc-text-muted uppercase tracking-wide">{title}</p>
            <p className="text-3xl font-bold text-soc-text-primary mt-2">{value}</p>
            {trend && (
              <p
                className={cn(
                  'text-sm mt-2',
                  trend.isPositive ? 'text-severity-low' : 'text-severity-critical'
                )}
              >
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
              </p>
            )}
          </div>
          <div
            className={cn(
              'w-12 h-12 rounded-lg flex items-center justify-center bg-soc-bg-tertiary',
              iconColor
            )}
          >
            <Icon className="w-6 h-6" aria-hidden="true" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
