import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { useFetch } from '@/hooks';
import { apiService } from '@/services/api';
import { formatDate } from '@/utils/helpers';

export const AlertDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: alert, loading } = useFetch(() => apiService.getAlertById(Number(id)), [id]);

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <Spinner size="lg" />
        </div>
      </MainLayout>
    );
  }

  if (!alert) {
    return (
      <MainLayout>
        <div className="text-center py-12">
          <p className="text-soc-text-muted">Alert not found</p>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => navigate('/alerts')} className="mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Alerts
        </Button>

        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-2xl">{alert.title}</CardTitle>
                <p className="text-soc-text-muted mt-2">Alert ID: {alert.id}</p>
              </div>
              <div className="flex gap-2">
                <Badge variant={alert.severity as any}>{alert.severity}</Badge>
                <Badge variant="default">{alert.status}</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-semibold text-soc-text-secondary mb-2">Source</h3>
                <p className="text-soc-text-primary">{alert.source}</p>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-soc-text-secondary mb-2">Created At</h3>
                <p className="text-soc-text-primary">{formatDate(alert.created_at)}</p>
              </div>
            </div>

            {alert.description && (
              <div>
                <h3 className="text-sm font-semibold text-soc-text-secondary mb-2">Description</h3>
                <p className="text-soc-text-primary bg-soc-bg-tertiary p-4 rounded-lg">
                  {alert.description}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};
