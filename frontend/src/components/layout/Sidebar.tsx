import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Activity, AlertTriangle, FileText, Brain, Search, Settings, Shield } from 'lucide-react';
import { cn } from '@/utils/helpers';
import { useUIStore } from '@/store';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Monitoring', href: '/monitoring', icon: Activity },
  { name: 'Alerts', href: '/alerts', icon: AlertTriangle },
  { name: 'Incidents', href: '/incidents', icon: FileText },
  { name: 'Analytics', href: '/ml-analytics', icon: Brain },
  { name: 'Log Explorer', href: '/log-explorer', icon: Search },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export const Sidebar = () => {
  const { sidebarOpen } = useUIStore();

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-full bg-soc-bg-secondary border-r border-soc-border z-40 transition-all duration-300',
        sidebarOpen ? 'w-64' : 'w-20'
      )}
    >
      <div className="flex flex-col h-full">
        <div className="flex items-center h-16 px-4 border-b border-soc-border">
          <Shield className="w-8 h-8 text-soc-accent-cyan flex-shrink-0" aria-hidden="true" />
          {sidebarOpen && (
            <span className="ml-3 text-xl font-bold text-soc-text-primary">
              AI SOC
            </span>
          )}
        </div>

        <nav className="flex-1 p-4 space-y-2 overflow-y-auto scrollbar-thin" aria-label="Main navigation">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all group',
                  isActive
                    ? 'bg-soc-accent-cyan text-white'
                    : 'text-soc-text-muted hover:bg-soc-bg-tertiary hover:text-soc-text-primary'
                )
              }
            >
              <item.icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
              {sidebarOpen && <span className="font-medium">{item.name}</span>}
            </NavLink>
          ))}
        </nav>
      </div>
    </aside>
  );
};
