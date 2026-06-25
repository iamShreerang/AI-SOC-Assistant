import { useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { useFetch } from '@/hooks';
import { apiService } from '@/services/api';
import { formatDate, getSeverityBgColor } from '@/utils/helpers';
import { Search, Filter, Download } from 'lucide-react';
import { LogSeverity } from '@/types';

export const LogExplorer = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<LogSeverity | ''>('');

  const { data: logs, loading } = useFetch(() =>
    apiService.getLogs({
      severity: severityFilter || undefined,
      limit: 100,
    }),
    [severityFilter]
  );

  const filteredLogs = logs?.filter(
    (log) =>
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.source.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleExport = async () => {
    try {
      const blob = await apiService.exportLogs({ format: 'csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `logs-${new Date().toISOString()}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed', error);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-soc-text-primary">Log Explorer</h1>
            <p className="text-soc-text-muted mt-2">Search and analyze security logs</p>
          </div>
          <Button variant="secondary" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>

        <Card>
          <CardHeader>
            <div className="flex flex-col md:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-soc-text-muted" aria-hidden="true" />
                <Input
                  type="search"
                  placeholder="Search logs by message or source..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="flex items-center gap-3">
                <Filter className="w-5 h-5 text-soc-text-muted flex-shrink-0" aria-hidden="true" />
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value as LogSeverity)}
                  className="px-3 py-2 bg-soc-bg-tertiary border border-soc-border rounded-lg text-soc-text-primary focus:outline-none focus:ring-2 focus:ring-soc-accent-cyan"
                  aria-label="Filter by severity"
                >
                  <option value="">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="error">Error</option>
                  <option value="warning">Warning</option>
                  <option value="info">Info</option>
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
              <div className="space-y-2 max-h-[700px] overflow-y-auto scrollbar-thin">
                {filteredLogs?.map((log) => (
                  <div
                    key={log.id}
                    className={`p-4 rounded-lg border ${getSeverityBgColor(log.severity)} hover:border-soc-accent-cyan/50 transition-all`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant={log.severity as any}>{log.severity}</Badge>
                          <span className="text-sm text-soc-text-muted font-mono">{log.source}</span>
                          <span className="text-xs text-soc-text-muted">ID: {log.id}</span>
                        </div>
                        <p className="text-soc-text-primary font-mono text-sm break-words">{log.message}</p>
                        {log.raw && (
                          <details className="mt-2">
                            <summary className="text-xs text-soc-accent-cyan cursor-pointer hover:text-soc-accent-cyan/80">
                              View raw log
                            </summary>
                            <pre className="mt-2 text-xs bg-soc-bg-primary p-3 rounded overflow-x-auto scrollbar-thin">
                              {log.raw}
                            </pre>
                          </details>
                        )}
                        <p className="text-xs text-soc-text-muted mt-2">{formatDate(log.ingested_at)}</p>
                      </div>
                    </div>
                  </div>
                ))}
                {filteredLogs?.length === 0 && (
                  <p className="text-center text-soc-text-muted py-12">No logs found</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};
