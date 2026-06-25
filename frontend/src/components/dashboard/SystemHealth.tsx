import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface SystemHealthProps {
  health: {
    database: boolean;
    elasticsearch: boolean;
    kafka: boolean;
    spark: boolean;
    ml_model: boolean;
  };
}

export const SystemHealth = ({ health }: SystemHealthProps) => {
  const systems = [
    { name: 'Database', key: 'database' as const },
    { name: 'Elasticsearch', key: 'elasticsearch' as const },
    { name: 'Kafka', key: 'kafka' as const },
    { name: 'Spark', key: 'spark' as const },
    { name: 'ML Model', key: 'ml_model' as const },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Health</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {systems.map(({ name, key }) => (
            <div
              key={key}
              className="flex items-center justify-between p-3 rounded-lg bg-soc-bg-tertiary"
            >
              <span className="text-soc-text-secondary font-medium">{name}</span>
              {health[key] ? (
                <div className="flex items-center gap-2 text-severity-low">
                  <CheckCircle className="w-4 h-4" aria-hidden="true" />
                  <span className="text-sm">Operational</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-severity-critical">
                  <XCircle className="w-4 h-4" aria-hidden="true" />
                  <span className="text-sm">Down</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
