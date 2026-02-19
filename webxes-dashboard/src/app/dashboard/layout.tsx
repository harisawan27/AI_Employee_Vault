'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/useAuth';
import { useWebSocket } from '@/lib/useWebSocket';
import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '@/lib/api';
import Sidebar from '@/components/Sidebar';
import ToastContainer from '@/components/Toast';
import MobileMenuButton from '@/components/MobileMenuButton';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { authenticated, loading, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  useWebSocket();

  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => getDashboardStats().then((r) => r.data),
    enabled: authenticated,
    refetchInterval: 30_000,
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!authenticated) return null;

  return (
    <div className="flex min-h-screen">
      <MobileMenuButton onClick={() => setMobileOpen(true)} />
      <Sidebar
        approvalCount={stats?.approvals_waiting || 0}
        inboxCount={stats?.pending_tasks || 0}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
        onLogout={logout}
      />
      <main className="flex-1 lg:ml-64 ml-0 p-4 sm:p-6 pt-14 lg:pt-6 transition-all">
        {children}
      </main>
      <ToastContainer />
    </div>
  );
}
