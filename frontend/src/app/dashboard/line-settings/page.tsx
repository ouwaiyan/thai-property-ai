'use client';

import { useEffect, useState } from 'react';
import {
  Card, Switch, Button, Table, Space, Tag, Modal, Form, Input, Upload, App, Spin, Descriptions,
} from 'antd';
import type { UploadFile } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import {
  SettingOutlined, MenuOutlined, RobotOutlined, PlusOutlined, DeleteOutlined, StarOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  getAutoReplySetting, setAutoReplySetting,
  getRichMenus, createRichMenu, setDefaultRichMenu, deleteRichMenu, uploadRichMenuImage,
} from '@/lib/api';
import { useI18n } from '@/i18n/i18n';
import type { RichMenuOut } from '@/types/report';

export default function LineSettingsPage() {
  const { message } = App.useApp();
  const { t } = useI18n();
  const [loading, setLoading] = useState(true);
  const [autoReply, setAutoReply] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [richMenus, setRichMenus] = useState<RichMenuOut[]>([]);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [imageFile, setImageFile] = useState<UploadFile | null>(null);
  const [createForm] = Form.useForm();

  const areaLabels: Record<string, string> = {
    'action=find_property': t('line.find_property'),
    'action=book_viewing': t('line.book_viewing'),
    '发送位置': t('line.send_location'),
    '咨询经纪人': t('line.contact_agent'),
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [ar, menus] = await Promise.all([getAutoReplySetting(), getRichMenus()]);
      setAutoReply(ar.enabled);
      setRichMenus(menus);
    } catch {
      message.error(t('line.settings_load_failed'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleToggleAutoReply = async (checked: boolean) => {
    setToggling(true);
    try {
      await setAutoReplySetting(checked);
      setAutoReply(checked);
      message.success(checked ? t('line.auto_reply_enabled') : t('line.auto_reply_disabled'));
    } catch {
      message.error(t('line.settings_load_failed'));
    } finally {
      setToggling(false);
    }
  };

  const handleCreateRichMenu = async () => {
    const values = await createForm.validateFields();
    setCreating(true);
    try {
      const result = await createRichMenu(values);
      const menuId = result.rich_menu_id;
      if (menuId && imageFile?.originFileObj) {
        await uploadRichMenuImage(menuId, imageFile.originFileObj as File);
      }
      message.success(t('line.menu_create_success'));
      setCreateModalOpen(false);
      createForm.resetFields();
      setImageFile(null);
      loadData();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      message.error(err?.response?.data?.detail || t('line.menu_create_failed'));
    } finally {
      setCreating(false);
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await setDefaultRichMenu(id);
      message.success(t('line.menu_set_default_success'));
      loadData();
    } catch {
      message.error(t('line.menu_set_default_failed'));
    }
  };

  const handleDelete = async (id: string) => {
    Modal.confirm({
      title: t('line.menu_delete_confirm_title'),
      content: t('line.menu_delete_confirm_content'),
      onOk: async () => {
        try {
          await deleteRichMenu(id);
          message.success(t('line.menu_delete_success'));
          loadData();
        } catch {
          message.error(t('line.menu_delete_failed'));
        }
      },
    });
  };

  const columns: ColumnsType<RichMenuOut> = [
    {
      title: t('line.menu_name'), dataIndex: 'name', key: 'name',
      render: (n: string, r: RichMenuOut) => (
        <Space>
          {n}
          {r.is_default && <Tag color="gold"><StarOutlined /> {t('line.menu_default_tag')}</Tag>}
        </Space>
      ),
    },
    {
      title: t('line.menu_chat_bar'), dataIndex: 'chat_bar_text', key: 'chat_bar_text', width: 120,
    },
    {
      title: t('line.menu_actions'), key: 'areas', width: 280,
      render: (_: unknown, r: RichMenuOut) => (
        <Space wrap>
          {r.areas?.map((a: Record<string, unknown>, i: number) => {
            const action = a.action as Record<string, string> | undefined;
            const label = action
              ? (areaLabels[action.data || action.text || ''] || action.label || t('line.btn_area', { n: i + 1 }))
              : t('line.btn_area', { n: i + 1 });
            return <Tag key={i}>{label}</Tag>;
          })}
        </Space>
      ),
    },
    {
      title: t('common.actions'), key: 'actions', width: 200,
      render: (_: unknown, r: RichMenuOut) => (
        <Space>
          {!r.is_default && r.rich_menu_id && (
            <Button size="small" icon={<StarOutlined />} onClick={() => handleSetDefault(r.rich_menu_id!)}>
              {t('line.set_default')}
            </Button>
          )}
          {r.rich_menu_id && (
            <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(r.rich_menu_id!)}>
              {t('common.delete')}
            </Button>
          )}
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
        <SettingOutlined /> {t('line.line_settings')}
      </h2>

      <Card
        title={<span><RobotOutlined /> {t('line.auto_reply')}</span>}
        style={{ marginBottom: 24 }}
      >
        <Space>
          <Switch
            checked={autoReply}
            onChange={handleToggleAutoReply}
            loading={toggling}
            checkedChildren={t('common.on')}
            unCheckedChildren={t('common.off')}
          />
          <span>
            {autoReply ? t('line.auto_reply_desc_on') : t('line.auto_reply_desc_off')}
          </span>
        </Space>
        {autoReply && (
          <p style={{ marginTop: 12, color: '#faad14' }}>
            {t('line.auto_reply_warning')}
          </p>
        )}
      </Card>

      <Card
        title={<span><MenuOutlined /> {t('line.rich_menu')}</span>}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
            {t('line.create_rich_menu')}
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={richMenus}
          rowKey="rich_menu_id"
          pagination={false}
          locale={{ emptyText: t('line.no_rich_menu') }}
        />

        <Descriptions style={{ marginTop: 24 }} title={t('line.default_menu_desc')} size="small" column={2}>
          <Descriptions.Item label={t('line.find_property')}>{t('line.default_menu_desc_find')}</Descriptions.Item>
          <Descriptions.Item label={t('line.book_viewing')}>{t('line.default_menu_desc_book')}</Descriptions.Item>
          <Descriptions.Item label={t('line.send_location')}>{t('line.default_menu_desc_location')}</Descriptions.Item>
          <Descriptions.Item label={t('line.contact_agent')}>{t('line.default_menu_desc_contact')}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Modal
        title={t('line.create_rich_menu')}
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        onOk={handleCreateRichMenu}
        confirmLoading={creating}
        okText={t('common.create')}
        cancelText={t('common.cancel')}
      >
        <Form form={createForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="name" label={t('line.menu_name')} rules={[{ required: true }]}>
            <Input placeholder={t('line.menu_name_placeholder')} />
          </Form.Item>
          <Form.Item name="chat_bar_text" label={t('line.menu_chat_bar')} initialValue={t('line.menu_chat_bar_default')}>
            <Input />
          </Form.Item>
          <Form.Item label={t('line.menu_image')}>
            <Upload
              listType="picture-card"
              maxCount={1}
              accept="image/jpeg,image/png"
              beforeUpload={(file) => {
                const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
                if (!isJpgOrPng) {
                  message.error(t('line.image_type_invalid'));
                  return Upload.LIST_IGNORE;
                }
                const isLt1M = file.size / 1024 / 1024 < 1;
                if (!isLt1M) {
                  message.error(t('line.image_too_large'));
                  return Upload.LIST_IGNORE;
                }
                setImageFile({ uid: '-1', name: file.name, status: 'done', originFileObj: file } as UploadFile);
                return false;
              }}
              onRemove={() => setImageFile(null)}
              fileList={imageFile ? [imageFile] : []}
            >
              {!imageFile && (
                <div>
                  <UploadOutlined />
                  <div style={{ marginTop: 8 }}>{t('common.upload_image')}</div>
                </div>
              )}
            </Upload>
          </Form.Item>
        </Form>
        <p style={{ color: '#888' }}>
          {t('line.menu_create_hint')}
        </p>
      </Modal>
    </div>
  );
}
