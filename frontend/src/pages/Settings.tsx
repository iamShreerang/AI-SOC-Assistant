import { useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert } from '@/components/ui/Alert';
import { useAuthStore, useSettingsStore } from '@/store';
import { User, Bell, Palette, RefreshCw } from 'lucide-react';

export const Settings = () => {
  const { user } = useAuthStore();
  const { settings, updateSettings } = useSettingsStore();
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-soc-text-primary">Settings</h1>
          <p className="text-soc-text-muted mt-2">Manage your account and preferences</p>
        </div>

        {saved && (
          <Alert variant="success">
            Settings saved successfully
          </Alert>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              Profile Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-soc-text-secondary mb-2">
                Username
              </label>
              <Input value={user?.username || ''} disabled />
            </div>
            <div>
              <label className="block text-sm font-medium text-soc-text-secondary mb-2">
                Role
              </label>
              <Input value={user?.role || ''} disabled />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Notification Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-soc-text-primary">Enable Notifications</p>
                <p className="text-sm text-soc-text-muted">Receive alerts and updates</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.notifications_enabled}
                  onChange={(e) => updateSettings({ notifications_enabled: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-soc-bg-elevated peer-focus:ring-2 peer-focus:ring-soc-accent-cyan rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-soc-accent-cyan"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-soc-text-primary">Email Notifications</p>
                <p className="text-sm text-soc-text-muted">Receive email alerts</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.email_notifications}
                  onChange={(e) => updateSettings({ email_notifications: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-soc-bg-elevated peer-focus:ring-2 peer-focus:ring-soc-accent-cyan rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-soc-accent-cyan"></div>
              </label>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RefreshCw className="w-5 h-5" />
              Auto Refresh
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-soc-text-primary">Enable Auto Refresh</p>
                <p className="text-sm text-soc-text-muted">Automatically refresh dashboard data</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.auto_refresh}
                  onChange={(e) => updateSettings({ auto_refresh: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-soc-bg-elevated peer-focus:ring-2 peer-focus:ring-soc-accent-cyan rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-soc-accent-cyan"></div>
              </label>
            </div>

            {settings.auto_refresh && (
              <div>
                <label className="block text-sm font-medium text-soc-text-secondary mb-2">
                  Refresh Interval (seconds)
                </label>
                <Input
                  type="number"
                  min="10"
                  max="300"
                  value={settings.refresh_interval / 1000}
                  onChange={(e) => updateSettings({ refresh_interval: Number(e.target.value) * 1000 })}
                />
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button onClick={handleSave}>
            Save Changes
          </Button>
        </div>
      </div>
    </MainLayout>
  );
};
