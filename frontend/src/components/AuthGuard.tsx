'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { Spin } from 'antd';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, initialized, initialize } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!initialized) {
      initialize();
    }
  }, [initialized, initialize]);

  useEffect(() => {
    if (initialized && !user && pathname !== '/login') {
      router.push('/login');
    }
  }, [initialized, user, pathname, router]);

  if (!initialized) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!user && pathname !== '/login') return null;

  return <>{children}</>;
}
