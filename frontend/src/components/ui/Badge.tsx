import { HTMLAttributes } from 'react';
import { cn, getSeverityBgColor, getSeverityColor, getStatusBgColor, getStatusColor } from '@/utils/helpers';
import type { AlertSeverity, LogSeverity, AlertStatus, IncidentStatus } from '@/types';

type SeverityVariant = AlertSeverity | LogSeverity;
type StatusVariant = AlertStatus | IncidentStatus;

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'severity' | 'status' | SeverityVariant | StatusVariant;
  severity?: AlertSeverity | LogSeverity;
  status?: AlertStatus | IncidentStatus;
}

const SEVERITY_VALUES = ['low', 'medium', 'high', 'critical', 'info', 'warning', 'error'];
const STATUS_VALUES = ['open', 'acknowledged', 'resolved', 'in-progress', 'closed'];

export const Badge = ({
  className,
  variant = 'default',
  severity,
  status,
  children,
  ...props
}: BadgeProps) => {
  const base = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize';

  const resolvedSeverity: SeverityVariant | undefined =
    severity ?? (SEVERITY_VALUES.includes(variant as string) ? (variant as SeverityVariant) : undefined);
  const resolvedStatus: StatusVariant | undefined =
    status ?? (STATUS_VALUES.includes(variant as string) ? (variant as StatusVariant) : undefined);

  let badgeClasses = base;

  if (resolvedSeverity) {
    badgeClasses = cn(base, getSeverityBgColor(resolvedSeverity), getSeverityColor(resolvedSeverity), 'border border-current border-opacity-20');
  } else if (resolvedStatus) {
    badgeClasses = cn(base, getStatusBgColor(resolvedStatus), getStatusColor(resolvedStatus), 'border border-current border-opacity-20');
  } else {
    badgeClasses = cn(base, 'bg-soc-bg-elevated text-soc-text-secondary');
  }

  return (
    <span className={cn(badgeClasses, className)} {...props}>
      {children ?? resolvedSeverity ?? resolvedStatus}
    </span>
  );
};
