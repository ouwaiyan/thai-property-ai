'use client';

import { useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ProTable } from '@ant-design/pro-components';
import type { ProColumns, ActionType } from '@ant-design/pro-components';
import { Button, Tag } from 'antd';
import { EyeOutlined, PlusOutlined } from '@ant-design/icons';
import { getImportJobs } from '@/lib/api';
import { useI18n } from '@/i18n/i18n';
import type { ImportJobOut } from '@/types/import';

export default function ImportHistoryPage() {
  const router = useRouter();
  const actionRef = useRef<ActionType>();
  const { t } = useI18n();

  const statusMap: Record<string, { text: string; color: string }> = {
    uploaded: { text: t('import.status_uploaded'), color: 'default' },
    mapped: { text: t('import.status_mapped'), color: 'blue' },
    importing: { text: t('import.status_importing'), color: 'orange' },
    imported: { text: t('import.status_imported'), color: 'green' },
    failed: { text: t('import.status_failed'), color: 'red' },
  };

  const columns: ProColumns<ImportJobOut>[] = [
    { title: t('import.filename'), dataIndex: 'original_filename', key: 'original_filename', width: 280 },
    {
      title: t('common.status'), dataIndex: 'status', key: 'status', width: 100,
      valueEnum: {
        uploaded: { text: t('import.status_uploaded') },
        mapped: { text: t('import.status_mapped') },
        importing: { text: t('import.status_importing') },
        imported: { text: t('import.status_imported') },
        failed: { text: t('import.status_failed') },
      },
      render: (_, r) => (
        <Tag color={statusMap[r.status]?.color || 'default'}>
          {statusMap[r.status]?.text || r.status}
        </Tag>
      ),
    },
    { title: t('import.total_rows'), dataIndex: 'total_rows', key: 'total_rows', width: 80, search: false },
    {
      title: t('import.success_rows'), dataIndex: 'success_rows', key: 'success_rows', width: 80, search: false,
      render: (_, r) => <span style={{ color: '#52c41a' }}>{r.success_rows}</span>,
    },
    {
      title: t('import.error_rows'), dataIndex: 'error_rows', key: 'error_rows', width: 80, search: false,
      render: (_, r) => (
        <span style={{ color: r.error_rows > 0 ? '#ff4d4f' : '#999' }}>{r.error_rows}</span>
      ),
    },
    {
      title: t('common.created_at'), dataIndex: 'created_at', key: 'created_at', width: 160, search: false,
      render: (_, r) => new Date(r.created_at).toLocaleString(),
    },
    {
      title: t('common.actions'), key: 'action', width: 100, search: false,
      render: (_, record) => (
        <Button
          size="small"
          icon={<EyeOutlined />}
          onClick={() => router.push(`/dashboard/import/history/${record.id}`)}
        >
          {t('common.detail')}
        </Button>
      ),
    },
  ];

  return (
    <ProTable<ImportJobOut>
      columns={columns}
      actionRef={actionRef}
      request={async (params) => {
        const { current, pageSize } = params;
        const res = await getImportJobs({ page: current, page_size: pageSize });
        return { data: res.items, total: res.total, success: true };
      }}
      rowKey="id"
      search={{ labelWidth: 'auto' }}
      pagination={{ pageSize: 20 }}
      headerTitle={t('import.history')}
      toolBarRender={() => [
        <Button key="new-import" type="primary" icon={<PlusOutlined />} onClick={() => router.push('/dashboard/import')}>
          {t('import.new_import')}
        </Button>,
      ]}
    />
  );
}
