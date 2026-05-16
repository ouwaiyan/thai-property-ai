'use client';

import { App, ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import AuthGuard from '@/components/AuthGuard';
import ProLayoutWrapper from '@/components/ProLayoutWrapper';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ConfigProvider locale={zhCN}>
      <App>
        <AuthGuard>
          <ProLayoutWrapper>{children}</ProLayoutWrapper>
        </AuthGuard>
      </App>
    </ConfigProvider>
  );
}
