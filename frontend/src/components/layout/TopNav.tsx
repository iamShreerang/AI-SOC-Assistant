import { useState } from 'react';
import { Menu, Search, Bell, User, LogOut } from 'lucide-react';
import { useAuthStore, useNotificationStore, useUIStore } from '@/store';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { formatRelativeTime } from '@/utils/helpers';

export const TopNav = () => {
  const { user, clearAuth } = useAuthStore();
  const { notifications, markAsRead } = useNotificationStore();
  const { toggleSidebar } = useUIStore();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const handleLogout = () => {
    clearAuth();
    window.location.href = '/login';
  };

  return (
    <header className="sticky top-0 z-30 h-16 bg-soc-bg-secondary border-b border-soc-border">
      <div className="flex items-center justify-between h-full px-4">
        <div className="flex items-center gap-4 flex-1">
          <Button variant="ghost" size="sm" onClick={toggleSidebar} aria-label="Toggle sidebar">
            <Menu className="w-5 h-5" />
          </Button>

          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-soc-text-muted" aria-hidden="true" />
            <Input
              type="search"
              placeholder="Search logs, alerts, incidents..."
              className="pl-10"
              aria-label="Search"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowNotifications(!showNotifications)}
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-severity-critical rounded-full text-xs flex items-center justify-center text-white">
                  {unreadCount}
                </span>
              )}
            </Button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-soc-bg-tertiary border border-soc-border rounded-lg shadow-lg overflow-hidden">
                <div className="p-3 border-b border-soc-border">
                  <h3 className="font-semibold text-soc-text-primary">Notifications</h3>
                </div>
                <div className="max-h-96 overflow-y-auto scrollbar-thin">
                  {notifications.length === 0 ? (
                    <p className="p-4 text-center text-soc-text-muted">No notifications</p>
                  ) : (
                    notifications.slice(0, 5).map((notification) => (
                      <button
                        key={notification.id}
                        onClick={() => markAsRead(notification.id)}
                        className="w-full p-3 text-left hover:bg-soc-bg-elevated transition-colors border-b border-soc-border last:border-0"
                      >
                        <div className="flex items-start gap-2">
                          <Badge variant={notification.type as any} className="mt-1">
                            {notification.type}
                          </Badge>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-soc-text-primary text-sm">
                              {notification.title}
                            </p>
                            <p className="text-xs text-soc-text-muted mt-1">
                              {notification.message}
                            </p>
                            <p className="text-xs text-soc-text-muted mt-1">
                              {formatRelativeTime(notification.timestamp)}
                            </p>
                          </div>
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2"
              aria-label="User menu"
            >
              <User className="w-5 h-5" />
              <span className="hidden md:inline text-sm">{user?.username}</span>
            </Button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-soc-bg-tertiary border border-soc-border rounded-lg shadow-lg overflow-hidden">
                <div className="p-3 border-b border-soc-border">
                  <p className="font-medium text-soc-text-primary">{user?.username}</p>
                  <p className="text-xs text-soc-text-muted uppercase">{user?.role}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-soc-bg-elevated transition-colors text-severity-critical"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
