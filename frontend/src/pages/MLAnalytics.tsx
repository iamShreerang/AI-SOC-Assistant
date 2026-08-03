import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LineChartComponent, DonutChart } from '@/components/charts';
import { Brain, TrendingUp, Target } from 'lucide-react';
import { useFetch } from '@/hooks';
import { apiService } from '@/services/api';
import { Spinner } from '@/components/ui/Spinner';

export const MLAnalytics = () => {
  const { data: ml, loading } = useFetch(() => apiService.getMLAnalytics());

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <Spinner size="lg" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-soc-text-primary">Analytics</h1>
          <p className="text-soc-text-muted mt-2">Machine learning insights derived from live security data</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-soc-accent-purple/10 flex items-center justify-center">
                  <Brain className="w-6 h-6 text-soc-accent-purple" />
                </div>
                <div>
                  <p className="text-sm text-soc-text-muted">Resolution Rate</p>
                  <p className="text-2xl font-bold text-soc-text-primary">
                    {ml?.model_accuracy ?? 0}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-soc-accent-cyan/10 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-soc-accent-cyan" />
                </div>
                <div>
                  <p className="text-sm text-soc-text-muted">Total Alerts</p>
                  <p className="text-2xl font-bold text-soc-text-primary">
                    {ml?.predictions_today?.toLocaleString() ?? 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-severity-critical/10 flex items-center justify-center">
                  <Target className="w-6 h-6 text-severity-critical" />
                </div>
                <div>
                  <p className="text-sm text-soc-text-muted">Unresolved Critical</p>
                  <p className="text-2xl font-bold text-soc-text-primary">
                    {ml?.anomalies_detected ?? 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LineChartComponent
            data={ml?.anomaly_data ?? []}
            title="Alert Activity (Last 6 Hours)"
            color="#8b5cf6"
          />
          <DonutChart
            data={ml?.threat_classification ?? []}
            title="Alerts by Severity"
          />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Recent High-Risk Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            {(!ml?.predictions || ml.predictions.length === 0) ? (
              <p className="text-center text-soc-text-muted py-12">No high-risk alerts found</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-soc-border">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Alert ID</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Threat Type</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Confidence</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-soc-text-secondary">Severity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ml.predictions.map((pred) => (
                      <tr key={pred.id} className="border-b border-soc-border hover:bg-soc-bg-tertiary transition-colors">
                        <td className="py-3 px-4 text-soc-text-primary font-mono text-sm">#{pred.alert_id}</td>
                        <td className="py-3 px-4 text-soc-text-primary">{pred.threat}</td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-soc-bg-tertiary rounded-full h-2 max-w-[120px]">
                              <div
                                className="bg-soc-accent-cyan h-2 rounded-full"
                                style={{ width: `${pred.confidence * 100}%` }}
                              />
                            </div>
                            <span className="text-soc-text-primary text-sm font-medium">
                              {(pred.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <Badge variant={pred.severity as any}>{pred.severity}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};
