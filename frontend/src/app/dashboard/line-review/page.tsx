'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Table, Tag, Space, Typography, Select, Card } from 'antd';
import { MessageOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getLineConversations } from '@/lib/api';
import { useI18n } from '@/i18n/i18n';
import type { LineConversationSummary } from '@/types/line';

const statusColor: Record<string, string> = {
  new: 'default', parsed: 'blue', in_progress: 'orange', pending_reply: 'red', contacted: 'green', closed: 'purple',
};

export default function LineReviewPage() {
  const router = useRouter();
  const { t } = useI18n();
  const [data, setData] = useState<LineConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string | undefined>(undefined);
  const pageSize = 20;

  useEffect(() => {
    setLoading(true);
    getLineConversations({ page, page_size: pageSize, status })
      .then((res) => {
        setData(res.items);
        setTotal(res.total);
      })
      .finally(() => setLoading(false));
  }, [page, status]);

  const columns: ColumnsType<LineConversationSummary> = [
    {
      title: t('line.customer'), dataIndex: 'lead_name', width: 200,
      render: (name: string, r) => (
        <Space direction="vertical" size={0}>
          <Typography.Text strong>{name}</Typography.Text>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>{r.line_user_id}</Typography.Text>
        </Space>
      ),
    },
    {
      title: t('common.status'), dataIndex: 'lead_status', width: 100,
      render: (s: string) => <Tag color={statusColor[s] || 'default'}>{t(`status.${s}`)}</Tag>,
    },
    {
      title: t('line.message_count'), dataIndex: 'message_count', width: 80, align: 'center',
    },
    {
      title: t('line.latest_message'), dataIndex: 'latest_message_at', width: 180,
      render: (v: string) => v ? new Date(v).toLocaleString() : '-',
    },
    {
      title: t('common.actions'), width: 120,
      render: (_, r) => (
        <a onClick={() => router.push(`/dashboard/line-review/${r.line_user_id}`)}>
          <MessageOutlined /> {t('line.view_conversation')}
        </a>
      ),
    },
  ];

  return (
    <Card title={t('line.title')} extra={<MessageOutlined />}>
      <Space style={{ marginBottom: 16 }}>
        <Select
          allowClear
          placeholder={t('line.filter_status')}
          style={{ width: 140 }}
          value={status}
          onChange={(v) => { setStatus(v); setPage(1); }}
          options={[
            { label: t('status.pending_reply'), value: 'pending_reply' },
            { label: t('status.new'), value: 'new' },
            { label: t('status.parsed'), value: 'parsed' },
            { label: t('status.in_progress'), value: 'in_progress' },
            { label: t('status.contacted'), value: 'contacted' },
          ]}
        />
      </Space>
      <Table
        columns={columns}
        dataSource={data}
        rowKey="line_user_id"
        loading={loading}
        pagination={{
          current: page,
          pageSize,
          total,
          onChange: (p) => setPage(p),
          showTotal: (total) => t('common.total', { count: total }),
        }}
        onRow={(r) => ({
          onClick: () => router.push(`/dashboard/line-review/${r.line_user_id}`),
          style: { cursor: 'pointer' },
        })}
      />
    </Card>
  );
}
