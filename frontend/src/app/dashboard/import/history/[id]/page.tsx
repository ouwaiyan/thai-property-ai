'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, Table, Tag, Button, Space, Descriptions } from 'antd';
import { getImportJob, getImportErrors } from '@/lib/api';
import { useI18n } from '@/i18n/i18n';
import type { ImportJobDetail, ImportErrorOut } from '@/types/import';
import type { ColumnsType } from 'antd/es/table';

export default function ImportJobDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { t } = useI18n();
  const [job, setJob] = useState<ImportJobDetail | null>(null);
  const [errors, setErrors] = useState<ImportErrorOut[]>([]);
  const [loading, setLoading] = useState(true);

  const statusMap: Record<string, { text: string; color: string }> = {
    uploaded: { text: t('import.status_uploaded'), color: 'default' },
    mapped: { text: t('import.status_mapped'), color: 'blue' },
    importing: { text: t('import.status_importing'), color: 'orange' },
    imported: { text: t('import.status_imported'), color: 'green' },
    failed: { text: t('import.status_failed'), color: 'red' },
  };

  useEffect(() => {
    const load = async () => {
      try {
        const [jobData, errorData] = await Promise.all([
          getImportJob(id),
          getImportErrors(id),
        ]);
        setJob(jobData);
        setErrors(errorData);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  const errorColumns: ColumnsType<ImportErrorOut> = [
    { title: t('import.row_number'), dataIndex: 'row_number', key: 'row_number', width: 80 },
    {
      title: t('import.error_message'),
      dataIndex: 'error_messages',
      key: 'error_messages',
      render: (msgs: string[]) => (
        <Space direction="vertical" size={2}>
          {msgs.map((m, i) => (
            <Tag key={i} color="error">{m}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: t('import.field_name'), dataIndex: 'field_name', key: 'field_name', width: 120,
      render: (v: string | null) => v || '-',
    },
    {
      title: t('common.time'), dataIndex: 'created_at', key: 'created_at', width: 160,
      render: (v: string) => new Date(v).toLocaleString(),
    },
  ];

  return (
    <Card title={t('import.job_detail')} loading={loading} extra={
      <Button onClick={() => router.push('/dashboard/import/history')}>{t('import.back_to_list')}</Button>
    }>
      {job && (
        <>
          <Descriptions bordered column={3} style={{ marginBottom: 24 }}>
            <Descriptions.Item label={t('import.filename')}>{job.original_filename}</Descriptions.Item>
            <Descriptions.Item label={t('common.status')}>
              <Tag color={statusMap[job.status]?.color}>{statusMap[job.status]?.text}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label={t('common.created_at')}>{new Date(job.created_at).toLocaleString()}</Descriptions.Item>
            <Descriptions.Item label={t('import.total_rows')}>{job.total_rows}</Descriptions.Item>
            <Descriptions.Item label={t('import.success_rows')}><span style={{ color: '#52c41a' }}>{job.success_rows}</span></Descriptions.Item>
            <Descriptions.Item label={t('import.error_rows')}><span style={{ color: job.error_rows > 0 ? '#ff4d4f' : '#999' }}>{job.error_rows}</span></Descriptions.Item>
          </Descriptions>

          {errors.length > 0 && (
            <>
              <h4 style={{ marginBottom: 12 }}>{t('import.error_records', { count: errors.length })}</h4>
              <Table
                columns={errorColumns}
                dataSource={errors}
                rowKey="id"
                size="small"
                pagination={{ pageSize: 20 }}
              />
            </>
          )}
        </>
      )}
    </Card>
  );
}
