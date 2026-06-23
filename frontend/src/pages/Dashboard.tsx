import { Activity, AlertTriangle, FileText, Shield } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { StatCard } from '@/components/dashboard/StatCard';
import { SystemHealth } from '@/components/dashboard/SystemHealth';
import { DonutChart, LineChartComponent, BarChartComponent } from '@/components/charts';
import { useFetch } from '@/hooks';
import { apiService } from '@/services/api';
import { Spinner } from '@/components/ui/Spinner';

export const Dashboard = () => {
  const { data: summary, loading } = useFetch(() => apiService.getDashboardSummary());

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <Spinner size="lg" />
        </div>
      </MainLayout>
    );
  }

  const severityData = summary?.alerts_by_severity
    ? [
        { name: 'Critical', value: summary.alerts_by_severity.critical, color: '#dc2626' },
        { name: 'High', value: summary.alerts_by_severity.high, color: '#ea580c' },
        { name: 'Medium', value: summary.alerts_by_severity.medium, color: '#f59e0b' },
        { name: 'Low', value: summary.alerts_by_severity.low, color: '#10b981' },
      ]
    : [];

  const statusData = summary?.alerts_by_status
    ? [
        { name: 'Open', value: summary.alerts_by_status.open, color: '#ef4444' },
        { name: 'Acknowledged', value: summary.alerts_by_status.acknowledged, color: '#f59e0b' },
        { name: 'Resolved', value: summary.alerts_by_status.resolved, color: '#10b981' },
      ]
    : [];

  const logSeverityData = summary?.logs_by_severity
    ? [
        { name: 'Critical', value: summary.logs_by_severity.critical },
        { name: 'Error', value: summary.logs_by_severity.error },
        { name: 'Warning', value: summary.logs_by_severity.warning },
        { name: 'Info', value: summary.logs_by_severity.info },
      ]
    : [];

  const healthData = {
    database: true,
    elasticsearch: true,
    kafka: true,
    spark: true,
    ml_model: true,
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-soc-text-primary">Security Dashboard</h1>
          <p className="text-soc-text-muted mt-2">Real-time overview of your security operations</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Events"
            value={summary?.total_logs.toLocaleString() || 0}
            icon={Activity}
            iconColor="text-soc-accent-blue"
          />
          <StatCard
            title="Active Threats"
            value={summary?.critical_alerts || 0}
            icon={AlertTriangle}
            iconColor="text-severity-critical"
          />
          <StatCard
            title="Open Alerts"
            value={summary?.open_alerts || 0}
            icon={Shield}
            iconColor="text-severity-medium"
          />
          <StatCard
            title="Open Incidents"
            value={summary?.open_incidents || 0}
            icon={FileText}
            iconColor="text-severity-high"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <DonutChart data={severityData} title="Alert Severity Distribution" />
            <BarChartComponent data={logSeverityData} title="Logs by Severity" />
          </div>

          <div className="space-y-6">
            <SystemHealth health={healthData} />
            <DonutChart data={statusData} title="Alert Status" />
          </div>
        </div>
      </div>
    </MainLayout>
  );
};
