import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { useFetch } from '@/hooks';
import { apiService } from '@/services/api';
import { formatDate, getStatusBgColor } from '@/utils/helpers';
import { Filter, ExternalLink, Plus } from 'lucide-react';
import { IncidentStatus } from '@/types';

export const Incidents = () => {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<IncidentStatus | ''>('');

  const { data: incidents, loading, refetch } = useFetch(() =>
    apiService.getIncidents({
      status: statusFilter || undefined,
    }),
    [statusFilter]
  );

  const handleStatusUpdate = async (id: number, status: IncidentStatus) => {
    try {
      await apiService.updateIncidentStatus(id, { status });
      refetch();
    } catch (error) {
      console.error('Failed to update incident status', error);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-soc-text-primary">Incident Management</h1>
            <p className="text-soc-text-muted mt-2">Track and manage security incidents</p>
          </div>
          <Button variant="primary">
            <Plus className="w-4 h-4 mr-2" />
            Create Incident
          </Button>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between flex-wrap gap-4">
              <CardTitle>All Incidents</CardTitle>
              <div className="flex items-center gap-3">
                <Filter className="w-5 h-5 text-soc-text-muted" aria-hidden="true" />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as IncidentStatus)}
                  className="px-3 py-2 bg-soc-bg-tertiary border border-soc-border rounded-lg text-soc-text-primary focus:outline-none focus:ring-2 focus:ring-soc-accent-cyan"
                  aria-label="Filter by status"
                >
                  <option value="">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="in-progress">In Progress</option>
                  <option value="closed">Closed</option>
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
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Alerts</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Status</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Created</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incidents?.map((incident) => (
                      <tr
                        key={incident.id}
                        className="border-b border-soc-border hover:bg-soc-bg-tertiary transition-colors"
                      >
                        <td className="py-3 px-4 text-soc-text-primary font-mono text-sm">{incident.id}</td>
                        <td className="py-3 px-4 text-soc-text-primary">{incident.title}</td>
                        <td className="py-3 px-4 text-soc-text-muted text-sm">
                          {incident.alert_ids.length} alert(s)
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant="default" className={getStatusBgColor(incident.status)}>
                            {incident.status}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-soc-text-muted text-sm">
                          {formatDate(incident.created_at)}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            {incident.status === 'open' && (
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => handleStatusUpdate(incident.id, 'in-progress')}
                              >
                                Start
                              </Button>
                            )}
                            {incident.status === 'in-progress' && (
                              <Button
                                size="sm"
                                variant="primary"
                                onClick={() => handleStatusUpdate(incident.id, 'closed')}
                              >
                                Close
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => navigate(`/incidents/${incident.id}`)}
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
                {incidents?.length === 0 && (
                  <p className="text-center text-soc-text-muted py-12">No incidents found</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};
