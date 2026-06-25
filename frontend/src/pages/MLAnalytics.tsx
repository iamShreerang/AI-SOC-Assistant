import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LineChartComponent, DonutChart } from '@/components/charts';
import { Brain, TrendingUp, Target, AlertTriangle } from 'lucide-react';

export const MLAnalytics = () => {
  const anomalyData = [
    { name: '00:00', value: 0.2 },
    { name: '04:00', value: 0.3 },
    { name: '08:00', value: 0.5 },
    { name: '12:00', value: 0.8 },
    { name: '16:00', value: 0.4 },
    { name: '20:00', value: 0.3 },
  ];

  const threatClassification = [
    { name: 'Malware', value: 35, color: '#dc2626' },
    { name: 'Phishing', value: 28, color: '#ea580c' },
    { name: 'DDoS', value: 20, color: '#f59e0b' },
    { name: 'Unauthorized Access', value: 17, color: '#10b981' },
  ];

  const predictions = [
    { id: 1, alert_id: 1023, threat: 'SQL Injection', confidence: 0.94, severity: 'critical' },
    { id: 2, alert_id: 1024, threat: 'XSS Attack', confidence: 0.87, severity: 'high' },
    { id: 3, alert_id: 1025, threat: 'Brute Force', confidence: 0.76, severity: 'medium' },
    { id: 4, alert_id: 1026, threat: 'Port Scan', confidence: 0.65, severity: 'low' },
  ];

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-soc-text-primary">ML Analytics</h1>
          <p className="text-soc-text-muted mt-2">Machine learning insights and predictions</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-soc-accent-purple/10 flex items-center justify-center">
                  <Brain className="w-6 h-6 text-soc-accent-purple" />
                </div>
                <div>
                  <p className="text-sm text-soc-text-muted">Model Accuracy</p>
                  <p className="text-2xl font-bold text-soc-text-primary">94.7%</p>
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
                  <p className="text-sm text-soc-text-muted">Predictions Today</p>
                  <p className="text-2xl font-bold text-soc-text-primary">1,247</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-severity-critical/10 flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-severity-critical" />
                </div>
                <div>
                  <p className="text-sm text-soc-text-muted">Anomalies Detected</p>
                  <p className="text-2xl font-bold text-soc-text-primary">23</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <LineChartComponent data={anomalyData} title="Anomaly Detection Score" color="#8b5cf6" />
          <DonutChart data={threatClassification} title="Threat Classification" />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Recent Predictions</CardTitle>
          </CardHeader>
          <CardContent>
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
                  {predictions.map((pred) => (
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
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};
