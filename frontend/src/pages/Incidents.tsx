import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { usePolling } from '@/hooks';
import { apiService } from '@/services/api';
import { formatDate, getStatusBgColor } from '@/utils/helpers';
import { Filter, ExternalLink, Plus, X } from 'lucide-react';
import { IncidentStatus } from '@/types';
import { useNotificationStore } from '@/store';

export const Incidents = () => {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<IncidentStatus | ''>('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [alertIdsInput, setAlertIdsInput] = useState('');
  const [creating, setCreating] = useState(false);
  const { addNotification } = useNotificationStore();

  const { data: incidents, loading, refetch } = usePolling(
    () => apiService.getIncidents({ status: statusFilter || undefined }),
    3000
  );

  const handleStatusUpdate = async (id: number, status: IncidentStatus) => {
    try {
      await apiService.updateIncidentStatus(id, { status });
      refetch();
    } catch (error) {
      console.error('Failed to update incident status', error);
    }
  };

  const handleCreateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    try {
      setCreating(true);
      const alertIds = alertIdsInput
        .split(',')
        .map((id) => parseInt(id.trim(), 10))
        .filter((num) => !isNaN(num));

      await apiService.createIncident({
        title: title.trim(),
        description: description.trim(),
        alert_ids: alertIds,
      });

      addNotification({
        type: 'success',
        title: 'Incident Created',
        message: 'Security incident created successfully with Groq AI summary.',
      });

      setTitle('');
      setDescription('');
      setAlertIdsInput('');
      setIsModalOpen(false);
      refetch();
    } catch (err: any) {
      addNotification({
        type: 'error',
        title: 'Creation Failed',
        message: err.response?.data?.detail || err.message || 'Failed to create incident',
      });
    } finally {
      setCreating(false);
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
          <Button variant="primary" onClick={() => setIsModalOpen(true)}>
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

      {/* Create Incident Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-soc-bg-secondary border border-soc-border rounded-xl w-full max-w-lg shadow-2xl p-6 relative animate-in fade-in zoom-in duration-200">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-soc-text-muted hover:text-soc-text-primary"
            >
              <X className="w-5 h-5" />
            </button>
            <h2 className="text-xl font-bold text-soc-text-primary mb-4">Create Security Incident</h2>

            <form onSubmit={handleCreateIncident} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-soc-text-secondary mb-1">
                  Incident Title <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Critical Ransomware Activity Detected on Host"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-soc-bg-tertiary border border-soc-border rounded-lg text-soc-text-primary focus:outline-none focus:ring-2 focus:ring-soc-accent-cyan"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-soc-text-secondary mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe the incident details, affected systems, or context..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-soc-bg-tertiary border border-soc-border rounded-lg text-soc-text-primary focus:outline-none focus:ring-2 focus:ring-soc-accent-cyan"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-soc-text-secondary mb-1">
                  Related Alert IDs (comma separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 38, 39, 40"
                  value={alertIdsInput}
                  onChange={(e) => setAlertIdsInput(e.target.value)}
                  className="w-full px-3 py-2 bg-soc-bg-tertiary border border-soc-border rounded-lg text-soc-text-primary focus:outline-none focus:ring-2 focus:ring-soc-accent-cyan"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" disabled={creating}>
                  {creating ? <Spinner size="sm" className="mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                  Create & Generate AI Summary
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </MainLayout>
  );
};
