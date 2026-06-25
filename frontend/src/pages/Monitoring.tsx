import { useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Spinner } from '@/components/ui/Spinner';
import { usePolling } from '@/hooks';
import { apiService } from '@/services/api';
import { formatRelativeTime, getSeverityBgColor } from '@/utils/helpers';
import { Search, Activity } from 'lucide-react';
import { LogEntry } from '@/types';

export const Monitoring = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const { data: logs, loading } = usePolling(() => apiService.getLogs({ limit: 50 }), 5000);

  const filteredLogs = logs?.filter(
    (log) =>
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.source.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-soc-text-primary">Real-Time Monitoring</h1>
            <p className="text-soc-text-muted mt-2">Live security event stream</p>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-soc-accent-cyan animate-pulse" aria-hidden="true" />
            <span className="text-sm text-soc-text-muted">Live</span>
          </div>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Security Events</CardTitle>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-soc-text-muted" aria-hidden="true" />
                <Input
                  type="search"
                  placeholder="Search events..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading && !logs ? (
              <div className="flex justify-center py-12">
                <Spinner size="lg" />
              </div>
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto scrollbar-thin">
                {filteredLogs?.map((log) => (
                  <div
                    key={log.id}
                    className={`p-4 rounded-lg border ${getSeverityBgColor(log.severity)} hover:border-soc-accent-cyan/50 transition-all`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant={log.severity as any}>{log.severity}</Badge>
                          <span className="text-sm text-soc-text-muted">{log.source}</span>
                        </div>
                        <p className="text-soc-text-primary font-medium">{log.message}</p>
                        <p className="text-sm text-soc-text-muted mt-2">
                          {formatRelativeTime(log.ingested_at)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
                {filteredLogs?.length === 0 && (
                  <p className="text-center text-soc-text-muted py-12">No events found</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};
