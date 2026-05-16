import type { Metadata } from 'next';
import { AntdRegistry } from '@ant-design/nextjs-registry';
import 'leaflet/dist/leaflet.css';
import './globals.css';

export const metadata: Metadata = {
  title: 'ThaiEstate - 泰国房产中介系统',
  description: 'AI-powered property management for Thai real estate agents',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body>
        <AntdRegistry>{children}</AntdRegistry>
      </body>
    </html>
  );
}
