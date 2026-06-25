import { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { TopNav } from './TopNav';
import { useUIStore } from '@/store';
import { cn } from '@/utils/helpers';

interface MainLayoutProps {
  children: ReactNode;
}

export const MainLayout = ({ children }: MainLayoutProps) => {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="min-h-screen bg-soc-bg-primary">
      <Sidebar />
      <div
        className={cn(
          'transition-all duration-300',
          sidebarOpen ? 'ml-64' : 'ml-20'
        )}
      >
        <TopNav />
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
};
