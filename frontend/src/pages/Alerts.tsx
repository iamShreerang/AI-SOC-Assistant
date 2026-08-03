import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { usePolling } from '@/hooks';
import { apiService } from '@/services/api';
import { formatDate, getSeverityBgColor, getStatusBgColor } from '@/utils/helpers';
import { Filter, ExternalLink } from 'lucide-react';
import { AlertSeverity, AlertStatus } from '@/types';

export const Alerts = () => {
  const navigate = useNavigate();
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | ''>('');
  const [statusFilter, setStatusFilter] = useState<AlertStatus | ''>('');

  const { data: alerts, loading, refetch } = usePolling(() =>
    apiService.getAlerts({
      severity: severityFilter || undefined,
      status: statusFilter || undefined,
    }),
    10000
  );

  const handleStatusUpdate = async (id: number, status: AlertStatus) => {
    try {
      await apiService.updateAlertStatus(id, { status });
      refetch();
    } catch (error) {
      console.error('Failed to update alert status', error);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-soc-text-primary">Alert Management</h1>
          <p className="text-soc-text-muted mt-2">Monitor and manage security alerts</p>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between flex-wrap gap-4">
              <CardTitle>All Alerts</CardTitle>
              <div className="flex items-center gap-3">
                <Filter className="w-5 h-5 text-soc-text-muted" aria-hidden="true" />
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value as AlertSeverity)}
                  className="px-3 py-2 bg-soc-bg-tertiary border border-soc-border rounded-lg text-soc-text-primary focus:outline-none focus:ring-2 focus:ring-soc-accent-cyan"
                  aria-label="Filter by severity"
                >
                  <option value="">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as AlertStatus)}
                  className="px-3 py-2 bg-soc-bg-tertiary border border-soc-border rounded-lg text-soc-text-primary focus:outline-none focus:ring-2 focus:ring-soc-accent-cyan"
                  aria-label="Filter by status"
                >
                  <option value="">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="acknowledged">Acknowledged</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-12">
                <Spinner size="lg" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-soc-border">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">ID</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Title</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Source</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Severity</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Status</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Created</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {alerts?.map((alert) => (
                      <tr
                        key={alert.id}
                        className="border-b border-soc-border hover:bg-soc-bg-tertiary transition-colors"
                      >
                        <td className="py-3 px-4 text-soc-text-primary font-mono text-sm">{alert.id}</td>
                        <td className="py-3 px-4 text-soc-text-primary">{alert.title}</td>
                        <td className="py-3 px-4 text-soc-text-muted text-sm">{alert.source}</td>
                        <td className="py-3 px-4">
                          <Badge variant={alert.severity as any}>{alert.severity}</Badge>
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant="default" className={getStatusBgColor(alert.status)}>
                            {alert.status}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-soc-text-muted text-sm">
                          {formatDate(alert.created_at)}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            {alert.status === 'open' && (
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => handleStatusUpdate(alert.id, 'acknowledged')}
                              >
                                Acknowledge
                              </Button>
                            )}
                            {alert.status === 'acknowledged' && (
                              <Button
                                size="sm"
                                variant="primary"
                                onClick={() => handleStatusUpdate(alert.id, 'resolved')}
                              >
                                Resolve
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => navigate(`/alerts/${alert.id}`)}
                              aria-label="View details"
                            >
                              <ExternalLink className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {alerts?.length === 0 && (
                  <p className="text-center text-soc-text-muted py-12">No alerts found</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};
