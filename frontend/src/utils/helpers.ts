import { format, formatDistanceToNow } from 'date-fns';
import { AlertSeverity, AlertStatus, IncidentStatus, LogSeverity } from '@/types';

const ensureUtcDate = (date: string | Date): Date => {
  if (date instanceof Date) return date;
  if (!date) return new Date();
  let str = String(date).trim();
  // If string has no timezone suffix ('Z' or '+/-HH:MM'), append 'Z' so JS treats as UTC
  if (!str.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(str)) {
    str += 'Z';
  }
  return new Date(str);
};

export const formatDate = (date: string | Date): string => {
  const d = ensureUtcDate(date);
  return format(d, 'MMM dd, yyyy HH:mm:ss');
};

export const formatRelativeTime = (date: string | Date): string => {
  const d = ensureUtcDate(date);
  return formatDistanceToNow(d, { addSuffix: true });
};

export const getSeverityColor = (severity: AlertSeverity | LogSeverity): string => {
  const colors: Record<string, string> = {
    critical: 'text-severity-critical',
    high: 'text-severity-high',
    medium: 'text-severity-medium',
    low: 'text-severity-low',
    info: 'text-severity-info',
    warning: 'text-severity-medium',
    error: 'text-severity-high',
  };
  return colors[severity] || 'text-soc-text-muted';
};

export const getSeverityBgColor = (severity: AlertSeverity | LogSeverity): string => {
  const colors: Record<string, string> = {
    critical: 'bg-severity-critical/10 border-severity-critical/50',
    high: 'bg-severity-high/10 border-severity-high/50',
    medium: 'bg-severity-medium/10 border-severity-medium/50',
    low: 'bg-severity-low/10 border-severity-low/50',
    info: 'bg-severity-info/10 border-severity-info/50',
    warning: 'bg-severity-medium/10 border-severity-medium/50',
    error: 'bg-severity-high/10 border-severity-high/50',
  };
  return colors[severity] || 'bg-soc-bg-tertiary';
};

export const getStatusColor = (status: AlertStatus | IncidentStatus): string => {
  const colors: Record<string, string> = {
    open: 'text-severity-high',
    acknowledged: 'text-severity-medium',
    'in-progress': 'text-severity-medium',
    resolved: 'text-severity-low',
    closed: 'text-severity-low',
  };
  return colors[status] || 'text-soc-text-muted';
};

export const getStatusBgColor = (status: AlertStatus | IncidentStatus): string => {
  const colors: Record<string, string> = {
    open: 'bg-severity-high/10 border-severity-high/50',
    acknowledged: 'bg-severity-medium/10 border-severity-medium/50',
    'in-progress': 'bg-severity-medium/10 border-severity-medium/50',
    resolved: 'bg-severity-low/10 border-severity-low/50',
    closed: 'bg-severity-low/10 border-severity-low/50',
  };
  return colors[status] || 'bg-soc-bg-tertiary';
};

export const truncateText = (text: string, maxLength: number): string => {
  return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
};

export const downloadBlob = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

export const cn = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(' ');
};
