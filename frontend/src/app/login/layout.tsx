'use client';

import { App, ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return (
    <ConfigProvider locale={zhCN}>
      <App>{children}</App>
    </ConfigProvider>
  );
}
