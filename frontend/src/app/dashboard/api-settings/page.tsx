'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, Switch, Space, Tag, App, Spin, Popconfirm, Select, Tooltip,
} from 'antd';
import {
  SettingOutlined, ApiOutlined, PlusOutlined, DeleteOutlined, ReloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getApiSettings, upsertApiSetting, deleteApiSetting, toggleApiSetting, testApiConnection } from '@/lib/api';
import { useI18n } from '@/i18n/i18n';

interface SettingItem {
  id: string;
  provider: string;
  key_name: string;
  value: string | null;
  has_value: boolean;
  config_json: Record<string, unknown> | null;
  is_active: boolean;
  updated_at: string | null;
}

const PROVIDERS = [
  { key: 'openai', label: 'OpenAI', color: 'green' },
  { key: 'google_maps', label: 'Google Maps', color: 'blue' },
  { key: 'line', label: 'LINE', color: 'cyan' },
  { key: 'object_storage', label: 'Object Storage', color: 'orange' },
  { key: 'n8n', label: 'n8n', color: 'purple' },
];

function formatTime(iso: string | null): string {
  if (!iso) return '-';
  const d = new Date(iso);
  return d.toLocaleString();
}

export default function ApiSettingsPage() {
  const { message } = App.useApp();
  const { t } = useI18n();
  const [loading, setLoading] = useState(true);
  const [settings, setSettings] = useState<Record<string, SettingItem[]>>({});
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [toggling, setToggling] = useState<string | null>(null);

  const loadSettings = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getApiSettings();
      setSettings(data);
    } catch {
      message.error(t('settings.load_failed'));
    } finally {
      setLoading(false);
    }
  }, [message, t]);

  useEffect(() => { loadSettings(); }, [loadSettings]);

  const handleUpsert = async () => {
    const values = await form.validateFields();
    setSaving(true);
    try {
      await upsertApiSetting(values);
      message.success(t('settings.save_success'));
      setModalOpen(false);
      form.resetFields();
      setEditingId(null);
      loadSettings();
    } catch {
      message.error(t('settings.save_failed'));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteApiSetting(id);
      message.success(t('settings.delete_success'));
      loadSettings();
    } catch {
      message.error(t('settings.delete_failed'));
    }
  };

  const handleToggle = async (id: string, checked: boolean) => {
    setToggling(id);
    try {
      await toggleApiSetting(id, checked);
      message.success(t('settings.toggle_success'));
      loadSettings();
    } catch {
      message.error(t('settings.toggle_failed'));
    } finally {
      setToggling(null);
    }
  };

  const handleTest = async (provider: string) => {
    setTesting(provider);
    try {
      const result = await testApiConnection(provider);
      if (result.success) {
        message.success(result.message);
      } else {
        message.warning(result.message);
      }
    } catch {
      message.error(t('settings.test_failed'));
    } finally {
      setTesting(null);
    }
  };

  const openCreateModal = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({ is_active: true });
    setModalOpen(true);
  };

  const openEditModal = (record: SettingItem) => {
    setEditingId(record.id);
    form.setFieldsValue({
      provider: record.provider,
      key_name: record.key_name,
      is_active: record.is_active,
    });
    setModalOpen(true);
  };

  const allItems: SettingItem[] = Object.values(settings).flat();

  const columns: ColumnsType<SettingItem> = [
    {
      title: t('settings.provider'), dataIndex: 'provider', key: 'provider', width: 130,
      render: (p: string) => {
        const info = PROVIDERS.find((x) => x.key === p);
        const label = info?.label ?? p;
        const color = info?.color ?? 'default';
        return <Tag color={color}>{label}</Tag>;
      },
    },
    { title: t('settings.key_name'), dataIndex: 'key_name', key: 'key_name', width: 180 },
    {
      title: t('settings.value'), dataIndex: 'value', key: 'value',
      render: (v: string | null, r: SettingItem) =>
        r.has_value ? (
          <code style={{ fontSize: 12, background: '#f5f5f5', padding: '2px 6px', borderRadius: 4 }}>{v || '***'}</code>
        ) : (
          <Tag color="red">{t('settings.not_configured')}</Tag>
        ),
    },
    {
      title: t('settings.enabled'), dataIndex: 'is_active', key: 'is_active', width: 80, align: 'center',
      render: (v: boolean, r: SettingItem) => (
        <Switch
          checked={v}
          loading={toggling === r.id}
          onChange={(checked) => handleToggle(r.id, checked)}
        />
      ),
    },
    {
      title: t('settings.updated_at'), dataIndex: 'updated_at', key: 'updated_at', width: 170,
      render: (v: string | null) => (
        <Tooltip title={formatTime(v)}>
          <span style={{ color: '#888', fontSize: 13 }}>{formatTime(v)}</span>
        </Tooltip>
      ),
    },
    {
      title: t('common.actions'), key: 'actions', width: 200, fixed: 'right',
      render: (_: unknown, r: SettingItem) => (
        <Space size="small">
          <Button
            size="small"
            icon={testing === r.provider ? <ReloadOutlined spin /> : <ApiOutlined />}
            loading={testing === r.provider}
            onClick={() => handleTest(r.provider)}
          >
            {t('settings.test_connection')}
          </Button>
          <Button size="small" onClick={() => openEditModal(r)}>
            {t('common.edit')}
          </Button>
          <Popconfirm title={t('settings.delete_confirm')} onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>
        <SettingOutlined /> {t('settings.title')}
      </h2>

      <Card
        title={t('settings.all_settings')}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
            {t('settings.add_new')}
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={allItems}
          rowKey="id"
          pagination={false}
          scroll={{ x: 860 }}
          locale={{ emptyText: t('settings.no_settings') }}
        />
      </Card>

      <Modal
        title={editingId ? t('settings.edit_setting') : t('settings.add_new')}
        open={modalOpen}
        onOk={handleUpsert}
        onCancel={() => { setModalOpen(false); form.resetFields(); setEditingId(null); }}
        confirmLoading={saving}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
        width={520}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="provider" label={t('settings.provider')} rules={[{ required: true, message: t('common.required') }]}>
            <Select
              showSearch
              placeholder={t('settings.provider')}
              options={PROVIDERS.map((p) => ({ value: p.key, label: p.label }))}
              disabled={!!editingId}
            />
          </Form.Item>
          <Form.Item name="key_name" label={t('settings.key_name')} rules={[{ required: true, message: t('common.required') }]}>
            <Input placeholder="api_key / model / auto_reply_enabled / ..." disabled={!!editingId} />
          </Form.Item>
          <Form.Item name="value" label={t('settings.secret_value')}>
            <Input.Password placeholder={t('settings.secret_placeholder')} />
          </Form.Item>
          <Form.Item name="is_active" label={t('settings.enabled')} valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
