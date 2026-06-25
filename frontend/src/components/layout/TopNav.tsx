import { useState, useEffect, useRef } from 'react';
import { Menu, Search, Bell, User, LogOut, Loader2, FileText, Shield, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore, useNotificationStore, useUIStore } from '@/store';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { formatRelativeTime } from '@/utils/helpers';
import { apiService } from '@/services/api';
import { useDebounce } from '@/hooks';
import type { SearchResults } from '@/types';

export const TopNav = () => {
  const { user, clearAuth } = useAuthStore();
  const { notifications, markAsRead } = useNotificationStore();
  const { toggleSidebar } = useUIStore();
  const navigate = useNavigate();
  
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  
  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const handleLogout = () => {
    clearAuth();
    window.location.href = '/login';
  };

  // Handle outside click for search dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSearchResults(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Perform search
  useEffect(() => {
    const performSearch = async () => {
      if (debouncedSearchQuery.trim().length === 0) {
        setSearchResults(null);
        setIsSearching(false);
        return;
      }
      
      setIsSearching(true);
      try {
        const results = await apiService.search(debouncedSearchQuery);
        setSearchResults(results);
        setShowSearchResults(true);
      } catch (error) {
        console.error('Global search failed:', error);
      } finally {
        setIsSearching(false);
      }
    };

    performSearch();
  }, [debouncedSearchQuery]);

  const totalResults = searchResults 
    ? (searchResults.logs?.length || 0) + (searchResults.alerts?.length || 0) + (searchResults.incidents?.length || 0) 
    : 0;

  return (
    <header className="sticky top-0 z-30 h-16 bg-soc-bg-secondary border-b border-soc-border">
      <div className="flex items-center justify-between h-full px-4">
        <div className="flex items-center gap-4 flex-1">
          <Button variant="ghost" size="sm" onClick={toggleSidebar} aria-label="Toggle sidebar">
            <Menu className="w-5 h-5" />
          </Button>

          <div className="relative flex-1 max-w-md" ref={searchRef}>
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-soc-text-muted" aria-hidden="true" />
            <Input
              type="search"
              placeholder="Search logs, alerts, incidents..."
              className="pl-10"
              aria-label="Search"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setShowSearchResults(true);
              }}
              onFocus={() => {
                if (searchQuery.trim().length > 0) setShowSearchResults(true);
              }}
            />
            {isSearching && (
              <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-soc-text-muted animate-spin" />
            )}
            
            {/* Search Results Dropdown */}
            {showSearchResults && searchQuery.trim().length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-soc-bg-tertiary border border-soc-border rounded-lg shadow-xl overflow-hidden z-50">
                {isSearching && !searchResults ? (
                  <div className="p-4 text-center text-sm text-soc-text-muted">Searching...</div>
                ) : totalResults === 0 ? (
                  <div className="p-4 text-center text-sm text-soc-text-muted">No results found for "{searchQuery}"</div>
                ) : (
                  <div className="max-h-[400px] overflow-y-auto scrollbar-thin">
                    {/* Alerts */}
                    {searchResults?.alerts && searchResults.alerts.length > 0 && (
                      <div className="p-2 border-b border-soc-border">
                        <div className="text-xs font-bold uppercase text-soc-text-muted mb-2 px-2 flex items-center gap-2">
                          <Shield className="w-3 h-3" /> Alerts
                        </div>
                        {searchResults.alerts.map(alert => (
                          <button
                            key={`alert-${alert.id}`}
                            onClick={() => { setShowSearchResults(false); navigate(`/alerts/${alert.id}`); }}
                            className="w-full text-left px-3 py-2 rounded hover:bg-soc-bg-elevated text-sm text-soc-text-primary transition-colors flex justify-between items-center"
                          >
                            <span className="truncate pr-4">{alert.title}</span>
                            <Badge variant={alert.severity as any}>{alert.severity}</Badge>
                          </button>
                        ))}
                      </div>
                    )}
                    
                    {/* Incidents */}
                    {searchResults?.incidents && searchResults.incidents.length > 0 && (
                      <div className="p-2 border-b border-soc-border">
                        <div className="text-xs font-bold uppercase text-soc-text-muted mb-2 px-2 flex items-center gap-2">
                          <AlertTriangle className="w-3 h-3" /> Incidents
                        </div>
                        {searchResults.incidents.map(inc => (
                          <button
                            key={`inc-${inc.id}`}
                            onClick={() => { setShowSearchResults(false); navigate(`/incidents/${inc.id}`); }}
                            className="w-full text-left px-3 py-2 rounded hover:bg-soc-bg-elevated text-sm text-soc-text-primary transition-colors flex justify-between items-center"
                          >
                            <span className="truncate pr-4">{inc.title}</span>
                            <span className="text-xs text-soc-text-muted uppercase">{inc.status}</span>
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Logs */}
                    {searchResults?.logs && searchResults.logs.length > 0 && (
                      <div className="p-2">
                        <div className="text-xs font-bold uppercase text-soc-text-muted mb-2 px-2 flex items-center gap-2">
                          <FileText className="w-3 h-3" /> Logs
                        </div>
                        {searchResults.logs.map(log => (
                          <button
                            key={`log-${log.id}`}
                            onClick={() => { setShowSearchResults(false); navigate('/log-explorer'); }}
                            className="w-full text-left px-3 py-2 rounded hover:bg-soc-bg-elevated text-sm text-soc-text-primary transition-colors"
                          >
                            <div className="truncate">{log.message}</div>
                            <div className="text-xs text-soc-text-muted mt-1 font-mono">{log.source}</div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
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
              <div className="absolute right-0 mt-2 w-80 bg-soc-bg-tertiary border border-soc-border rounded-lg shadow-lg overflow-hidden z-50">
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
              <div className="absolute right-0 mt-2 w-48 bg-soc-bg-tertiary border border-soc-border rounded-lg shadow-lg overflow-hidden z-50">
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
