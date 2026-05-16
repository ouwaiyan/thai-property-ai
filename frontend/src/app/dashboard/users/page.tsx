'use client';

import { useRef, useState } from 'react';
import { ProTable } from '@ant-design/pro-components';
import type { ProColumns, ActionType } from '@ant-design/pro-components';
import { Button, Tag, Space, App, Modal, Form, Input, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getUsers, createUser, updateUser, deleteUser } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import PermissionButton from '@/components/PermissionButton';
import { useI18n } from '@/i18n/i18n';
import type { UserOut, UserCreate, UserUpdate } from '@/types/user';

const roleColor: Record<string, string> = { Admin: 'red', Manager: 'blue', Agent: 'green', Viewer: 'default' };

export default function UsersPage() {
  const actionRef = useRef<ActionType>();
  const user = useAuthStore((s) => s.user);
  const { message } = App.useApp();
  const { t } = useI18n();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserOut | null>(null);
  const [form] = Form.useForm();

  const openCreate = () => {
    setEditingUser(null);
    form.resetFields();
    form.setFieldsValue({ role: 'Agent' });
    setModalOpen(true);
  };

  const openEdit = (u: UserOut) => {
    setEditingUser(u);
    form.setFieldsValue({ name: u.name, email: u.email, role: u.role, status: u.status });
    setModalOpen(true);
  };

  const handleOk = async () => {
    const values = await form.validateFields();
    try {
      if (editingUser) {
        const data: UserUpdate = { name: values.name, email: values.email, role: values.role, status: values.status };
        if (values.password) data.password = values.password;
        await updateUser(editingUser.id, data);
        message.success(t('users.update_success'));
      } else {
        const data: UserCreate = { name: values.name, email: values.email, password: values.password, role: values.role };
        await createUser(data);
        message.success(t('users.create_success'));
      }
      setModalOpen(false);
      actionRef.current?.reload();
    } catch {
      message.error(t('users.operation_failed'));
    }
  };

  const handleDelete = (u: UserOut) => {
    Modal.confirm({
      title: t('users.deactivate_confirm_title'),
      content: t('users.deactivate_confirm_content', { name: u.name }),
      okText: t('users.deactivate_ok'),
      okType: 'danger',
      cancelText: t('common.cancel'),
      onOk: async () => {
        await deleteUser(u.id);
        message.success(t('users.deactivate_success'));
        actionRef.current?.reload();
      },
    });
  };

  const columns: ProColumns<UserOut>[] = [
    { title: t('users.name'), dataIndex: 'name', key: 'name', width: 150 },
    { title: t('users.email'), dataIndex: 'email', key: 'email', width: 200 },
    {
      title: t('users.role'), dataIndex: 'role', key: 'role', width: 100,
      valueEnum: {
        Admin: { text: 'Admin' },
        Manager: { text: 'Manager' },
        Agent: { text: 'Agent' },
        Viewer: { text: 'Viewer' },
      },
      render: (_, r) => <Tag color={roleColor[r.role]}>{t(`roles.${r.role}`)}</Tag>,
    },
    {
      title: t('users.status'), dataIndex: 'status', key: 'status', width: 80,
      valueEnum: { active: { text: t('users.status_active') }, inactive: { text: t('users.status_inactive') } },
      render: (_, r) => <Tag color={r.status === 'active' ? 'green' : 'red'}>{t(`users.status_${r.status}`)}</Tag>,
    },
    { title: t('common.created_at'), dataIndex: 'created_at', key: 'created_at', width: 150, search: false,
      render: (_, r) => new Date(r.created_at).toLocaleDateString(),
    },
    { title: t('common.actions'), key: 'action', width: 150, search: false,
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)}>{t('common.edit')}</Button>
          {record.id !== user?.id && (
            <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record)}>{t('users.deactivate_ok')}</Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <>
      <ProTable<UserOut>
        columns={columns}
        actionRef={actionRef}
        request={async (params) => {
          const { current, pageSize, ...filters } = params;
          const res = await getUsers({ ...filters, page: current, page_size: pageSize });
          return { data: res.items, total: res.total, success: true };
        }}
        rowKey="id"
        search={{ labelWidth: 'auto' }}
        pagination={{ pageSize: 20 }}
        headerTitle={t('users.title')}
        toolBarRender={() => [
          <PermissionButton key="create" requiredRole="Admin">
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>{t('users.create_user')}</Button>
          </PermissionButton>,
        ]}
      />

      <Modal
        title={editingUser ? t('users.edit_user') : t('users.create_user')}
        open={modalOpen}
        onOk={handleOk}
        onCancel={() => setModalOpen(false)}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label={t('users.name')} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label={t('users.email')} rules={[{ required: true, type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label={editingUser ? t('users.password_new_hint') : t('users.password')} rules={editingUser ? [] : [{ required: true, min: 6 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="role" label={t('users.role')} rules={[{ required: true }]}>
            <Select options={[
              { label: t('roles.Admin'), value: 'Admin' },
              { label: t('roles.Manager'), value: 'Manager' },
              { label: t('roles.Agent'), value: 'Agent' },
              { label: t('roles.Viewer'), value: 'Viewer' },
            ]} />
          </Form.Item>
          {editingUser && (
            <Form.Item name="status" label={t('users.status')}>
              <Select options={[
                { label: t('users.status_active'), value: 'active' },
                { label: t('users.status_inactive'), value: 'inactive' },
              ]} />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </>
  );
}
