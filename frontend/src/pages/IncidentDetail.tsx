import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertCircle, Lightbulb } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { useFetch } from '@/hooks';
import { apiService } from '@/services/api';
import { formatDate } from '@/utils/helpers';

export const IncidentDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: incident, loading } = useFetch(() => apiService.getIncidentById(Number(id)), [id]);

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <Spinner size="lg" />
        </div>
      </MainLayout>
    );
  }

  if (!incident) {
    return (
      <MainLayout>
        <div className="text-center py-12">
          <p className="text-soc-text-muted">Incident not found</p>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => navigate('/incidents')} className="mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Incidents
        </Button>

        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-2xl">{incident.title}</CardTitle>
                <p className="text-soc-text-muted mt-2">Incident ID: {incident.id}</p>
              </div>
              <Badge variant="default">{incident.status}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-semibold text-soc-text-secondary mb-2">Related Alerts</h3>
                <p className="text-soc-text-primary">{incident.alert_ids.length} alert(s)</p>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-soc-text-secondary mb-2">Created At</h3>
                <p className="text-soc-text-primary">{formatDate(incident.created_at)}</p>
              </div>
            </div>

            {incident.description && (
              <div>
                <h3 className="text-sm font-semibold text-soc-text-secondary mb-2 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Description
                </h3>
                <p className="text-soc-text-primary bg-soc-bg-tertiary p-4 rounded-lg">
                  {incident.description}
                </p>
              </div>
            )}

            {incident.summary && (
              <div className="border-t border-soc-border pt-6">
                <h3 className="text-lg font-semibold text-soc-text-primary mb-4 flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-soc-accent-cyan" />
                  AI-Generated Summary
                </h3>
                <div className="bg-soc-accent-cyan/5 border border-soc-accent-cyan/20 p-4 rounded-lg">
                  <p className="text-soc-text-primary leading-relaxed">{incident.summary}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};
