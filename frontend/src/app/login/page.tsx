'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Form, Input, Button, Card, App } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/stores/authStore';
import { useI18n } from '@/i18n/i18n';
import LanguageSwitcher from '@/components/LanguageSwitcher';

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const router = useRouter();
  const { message: msg } = App.useApp();
  const { t } = useI18n();

  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      const result = await login(values.email, values.password);
      console.log('[Login] success, user:', result);
      msg.success(t('auth.login_success'));
      router.push('/dashboard');
    } catch (e: unknown) {
      console.error('[Login] error:', e);
      const detail = e instanceof Error ? e.message : String(e || '');
      const translated = detail.startsWith('auth.') || detail.startsWith('common.') || detail.startsWith('settings.') ? t(detail) : detail;
      msg.error(translated || t('auth.invalid_credentials'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>{t('auth.login_title')}</span>
            <LanguageSwitcher />
          </div>
        }
        style={{ width: 420 }}
      >
        <p style={{ textAlign: 'center', color: '#888', marginBottom: 24 }}>
          {t('auth.login_subtitle')}
        </p>
        <Form name="login" onFinish={onFinish} size="large">
          <Form.Item name="email" rules={[{ required: true, message: t('auth.email_placeholder') }]}>
            <Input prefix={<UserOutlined />} placeholder={t('auth.email_placeholder')} />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: t('auth.password_placeholder') }]}>
            <Input.Password prefix={<LockOutlined />} placeholder={t('auth.password_placeholder')} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              {t('auth.login_button')}
            </Button>
          </Form.Item>
        </Form>
        <div style={{ fontSize: 12, color: '#999', textAlign: 'center' }}>
          admin@thaiestate.com / admin123
        </div>
      </Card>
    </div>
  );
}
