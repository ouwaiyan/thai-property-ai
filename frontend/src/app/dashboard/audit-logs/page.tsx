'use client';

import { useRef } from 'react';
import { ProTable } from '@ant-design/pro-components';
import type { ProColumns, ActionType } from '@ant-design/pro-components';
import { Tag } from 'antd';
import { getAuditLogs } from '@/lib/api';
import { useI18n } from '@/i18n/i18n';
import type { AuditLogOut } from '@/types/auditLog';

const actionColor: Record<string, string> = {
  CREATE: 'green',
  UPDATE: 'blue',
  DELETE: 'red',
  LOGIN: 'purple',
};

export default function AuditLogsPage() {
  const actionRef = useRef<ActionType>();
  const { t } = useI18n();

  const columns: ProColumns<AuditLogOut>[] = [
    { title: t('common.time'), dataIndex: 'created_at', key: 'created_at', width: 160, search: false,
      render: (_, r) => new Date(r.created_at).toLocaleString(),
    },
    { title: t('audit.user'), dataIndex: 'user_id', key: 'user_id', width: 280, search: true,
      render: (_, r) => <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{r.user_id}</span>,
    },
    {
      title: t('audit.action'), dataIndex: 'action', key: 'action', width: 100,
      valueEnum: {
        CREATE: { text: t('audit.action_create') },
        UPDATE: { text: t('audit.action_update') },
        DELETE: { text: t('audit.action_delete') },
        LOGIN: { text: t('audit.action_login') },
      },
      render: (_, r) => <Tag color={actionColor[r.action] || 'default'}>{r.action}</Tag>,
    },
    { title: t('audit.entity_type'), dataIndex: 'entity_type', key: 'entity_type', width: 120,
      valueEnum: {
        user: { text: t('audit.entity_user') },
        property: { text: t('audit.entity_property') },
        property_image: { text: t('audit.entity_property_image') },
      },
    },
    { title: t('audit.entity_id'), dataIndex: 'entity_id', key: 'entity_id', width: 280, search: false,
      render: (_, r) => r.entity_id ? <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{r.entity_id}</span> : '-',
    },
    { title: t('audit.before'), dataIndex: 'before_json', key: 'before_json', search: false, width: 200,
      render: (_, r) => r.before_json ? (
        <pre style={{ fontSize: 11, maxHeight: 60, overflow: 'auto', margin: 0 }}>
          {JSON.stringify(r.before_json, null, 1)}
        </pre>
      ) : '-',
    },
    { title: t('audit.after'), dataIndex: 'after_json', key: 'after_json', search: false, width: 200,
      render: (_, r) => r.after_json ? (
        <pre style={{ fontSize: 11, maxHeight: 60, overflow: 'auto', margin: 0 }}>
          {JSON.stringify(r.after_json, null, 1)}
        </pre>
      ) : '-',
    },
  ];

  return (
    <ProTable<AuditLogOut>
      columns={columns}
      actionRef={actionRef}
      request={async (params) => {
        const { current, pageSize, ...filters } = params;
        const res = await getAuditLogs({ ...filters, page: current, page_size: pageSize });
        return { data: res.items, total: res.total, success: true };
      }}
      rowKey="id"
      search={{ labelWidth: 'auto' }}
      pagination={{ pageSize: 20 }}
      headerTitle={t('audit.title')}
    />
  );
}
