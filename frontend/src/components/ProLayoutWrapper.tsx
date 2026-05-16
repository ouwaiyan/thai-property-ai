'use client';

import { useRouter, usePathname } from 'next/navigation';
import { ProLayout } from '@ant-design/pro-components';
import {
  DashboardOutlined,
  HomeOutlined,
  UserOutlined,
  AuditOutlined,
  PlusOutlined,
  LogoutOutlined,
  ImportOutlined,
  ContactsOutlined,
  RobotOutlined,
  MessageOutlined,
  BarChartOutlined,
  SettingOutlined,
  ApiOutlined,
  EnvironmentOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import { hasRole } from '@/lib/permissions';
import type { UserRole } from '@/types/auth';
import { Dropdown, Avatar, Space } from 'antd';
import { useState, useRef } from 'react';
import LanguageSwitcher from './LanguageSwitcher';
import { useI18n } from '@/i18n/i18n';

export default function ProLayoutWrapper({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuthStore();
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const routerRef = useRef(router);
  routerRef.current = router;
  const { t } = useI18n();

  const menuItemRender = (item: { path?: string }, dom: React.ReactNode) => (
    <div
      onClick={() => item.path && routerRef.current.push(item.path)}
      style={{ cursor: 'pointer' }}
    >
      {dom}
    </div>
  );

  if (!user) return <>{children}</>;

  const role = user.role as UserRole;

  const route: { path: string; routes: Array<{ path: string; name: string; icon: React.ReactNode }> } = {
    path: '/dashboard',
    routes: [
      { path: '/dashboard', name: t('dashboard.title'), icon: <DashboardOutlined /> },
      { path: '/dashboard/properties', name: t('properties.title'), icon: <HomeOutlined /> },
    ],
  };

  if (hasRole(role, 'Agent')) {
    route.routes.push({ path: '/dashboard/import', name: t('import.title'), icon: <ImportOutlined /> });
    route.routes.push({ path: '/dashboard/leads', name: t('leads.title'), icon: <ContactsOutlined /> });
    route.routes.push({ path: '/dashboard/ai-tools', name: t('ai.title'), icon: <RobotOutlined /> });
    route.routes.push({ path: '/dashboard/recommendations', name: '推荐结果', icon: <EnvironmentOutlined /> });
    route.routes.push({ path: '/dashboard/line-review', name: t('line.title'), icon: <MessageOutlined /> });
    route.routes.push({ path: '/dashboard/reports', name: t('reports.title'), icon: <BarChartOutlined /> });
  }

  if (hasRole(role, 'Manager')) {
    route.routes.push({ path: '/dashboard/users', name: t('users.title'), icon: <UserOutlined /> });
  }
  if (hasRole(role, 'Admin')) {
    route.routes.push({ path: '/dashboard/audit-logs', name: t('audit.title'), icon: <AuditOutlined /> });
    route.routes.push({ path: '/dashboard/line-settings', name: t('line.line_settings'), icon: <SettingOutlined /> });
    route.routes.push({ path: '/dashboard/api-settings', name: 'API 配置', icon: <ApiOutlined /> });
  }

  return (
    <ProLayout
      title={t('common.app_name')}
      logo={null}
      collapsed={collapsed}
      onCollapse={setCollapsed}
      location={{ pathname }}
      route={route}
      menuItemRender={menuItemRender}
      rightContentRender={() => (
        <Space>
          <LanguageSwitcher />
          <PlusOutlined
            onClick={() => router.push('/dashboard/properties/new')}
            style={{ fontSize: 18, cursor: 'pointer' }}
          />
          <Dropdown
            menu={{
              items: [
                { key: 'role', label: `${t('common.role')}: ${t(`roles.${user.role}`)}`, disabled: true },
                { type: 'divider' },
                {
                  key: 'logout',
                  label: t('common.logout'),
                  icon: <LogoutOutlined />,
                  danger: true,
                },
              ],
              onClick: ({ key }) => {
                if (key === 'logout') {
                  logout();
                  router.push('/login');
                }
              },
            }}
          >
            <Avatar style={{ backgroundColor: '#1677ff', cursor: 'pointer' }}>
              {user.name.charAt(0)}
            </Avatar>
          </Dropdown>
        </Space>
      )}
    >
      <div style={{ padding: 24, minHeight: '100vh' }}>{children}</div>
    </ProLayout>
  );
}
