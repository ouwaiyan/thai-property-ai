'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, Steps, Upload, Button, Table, Select, Space, Alert, Checkbox, Result, App, Tag, Spin } from 'antd';
import { InboxOutlined, CheckCircleOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { uploadImportFile, getImportColumns, previewImport, mapImportFields, confirmImport } from '@/lib/api';
import { useI18n } from '@/i18n/i18n';
import type { ImportJobOut, ColumnInfo, PreviewRow, PreviewResponse, ImportResult } from '@/types/import';

const { Dragger } = Upload;

export default function ImportPage() {
  const router = useRouter();
  const { message } = App.useApp();
  const { t } = useI18n();

  const [currentStep, setCurrentStep] = useState(0);
  const [job, setJob] = useState<ImportJobOut | null>(null);
  const [columns, setColumns] = useState<ColumnInfo[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [overwrite, setOverwrite] = useState(false);

  const PROPERTY_FIELD_OPTIONS = [
    { label: t('import.ignore_field'), value: '' },
    { label: t('properties.property_code'), value: 'property_code' },
    { label: t('properties.name'), value: 'name' },
    { label: t('properties.building_name'), value: 'building_name' },
    { label: t('properties.address'), value: 'address' },
    { label: t('properties.latitude'), value: 'latitude' },
    { label: t('properties.longitude'), value: 'longitude' },
    { label: t('properties.district'), value: 'district' },
    { label: t('properties.area'), value: 'area' },
    { label: t('properties.nearest_bts'), value: 'nearest_bts' },
    { label: t('properties.nearest_mrt'), value: 'nearest_mrt' },
    { label: t('properties.bedroom_count'), value: 'bedroom_count' },
    { label: t('properties.bathroom_count'), value: 'bathroom_count' },
    { label: t('properties.size_sqm'), value: 'size_sqm' },
    { label: t('properties.monthly_rent'), value: 'monthly_rent' },
    { label: t('properties.deposit_months'), value: 'deposit_months' },
    { label: t('common.status'), value: 'status' },
    { label: t('properties.available_date'), value: 'available_date' },
    { label: t('properties.pet_allowed'), value: 'pet_allowed' },
    { label: t('properties.contact_person'), value: 'contact_person' },
    { label: t('properties.contact_phone'), value: 'contact_phone' },
    { label: t('properties.contact_line'), value: 'contact_line' },
    { label: t('properties.description'), value: 'description' },
    { label: t('properties.internal_note'), value: 'internal_note' },
    { label: t('properties.tags'), value: 'tags' },
  ];

  const handleUpload = async (file: File) => {
    setLoading(true);
    try {
      const jobData = await uploadImportFile(file);
      setJob(jobData);
      const cols = await getImportColumns(jobData.id);
      setColumns(cols.columns);
      const initialMapping: Record<string, string> = {};
      cols.columns.forEach((c) => {
        if (c.auto_detected_field) {
          initialMapping[c.header] = c.auto_detected_field;
        }
      });
      setMapping(initialMapping);
      setCurrentStep(1);
      message.success(t('import.upload_success_msg', { filename: jobData.original_filename, rows: cols.total_rows }));
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      message.error(err?.response?.data?.detail || t('import.upload_failed_msg'));
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    if (!job) return;
    setLoading(true);
    try {
      const result = await previewImport(job.id, { mapping });
      setPreview(result);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      message.error(err?.response?.data?.detail || t('import.preview_failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleNextStep = async () => {
    if (!job) return;
    setLoading(true);
    try {
      await mapImportFields(job.id, { mapping });
      setCurrentStep(2);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      message.error(err?.response?.data?.detail || t('import.save_mapping_failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!job) return;
    setLoading(true);
    try {
      const result = await confirmImport(job.id, overwrite);
      setImportResult(result);
      message.success(t('import.import_complete'));
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      message.error(err?.response?.data?.detail || t('import.import_failed'));
    } finally {
      setLoading(false);
    }
  };

  const mappingColumns: ColumnsType<ColumnInfo> = [
    { title: t('import.column_header'), dataIndex: 'header', key: 'header', width: 200 },
    {
      title: t('import.target_field'),
      key: 'target',
      render: (_, record) => (
        <Select
          style={{ width: 180 }}
          placeholder={t('import.select_field')}
          value={mapping[record.header] === undefined ? undefined : (mapping[record.header] || '')}
          onChange={(val) => setMapping((prev) => ({ ...prev, [record.header]: val || '' }))}
          options={PROPERTY_FIELD_OPTIONS}
        />
      ),
    },
    {
      title: t('import.auto_detected'),
      dataIndex: 'auto_detected_field',
      key: 'detected',
      render: (val) =>
        val ? <Tag color="blue">{val}</Tag> : <Tag color="default">{t('import.not_recognized')}</Tag>,
    },
  ];

  const previewColumns: ColumnsType<PreviewRow> = [
    { title: '#', key: 'row_number', render: (_, record) => record.row_number, width: 60 },
    ...columns.map((col) => ({
      title: col.header,
      key: col.header,
      render: (_: unknown, record: PreviewRow) => {
        const val = record.data[col.header];
        return <span style={{ color: record.errors.length > 0 && !val ? '#ff4d4f' : 'inherit' }}>{val || '-'}</span>;
      },
    })),
    {
      title: t('import.validation_errors'),
      key: 'errors',
      width: 220,
      render: (_: unknown, record: PreviewRow) =>
        record.errors.length > 0 ? (
          <Space direction="vertical" size={2}>
            {record.errors.map((e, i) => (
              <Tag key={i} color="error" style={{ fontSize: 12, whiteSpace: 'normal', maxWidth: 200 }}>{e}</Tag>
            ))}
          </Space>
        ) : (
          <Tag color="success" icon={<CheckCircleOutlined />}>{t('import.validation_pass')}</Tag>
        ),
    },
  ];

  const errorCount = preview?.rows.filter((r) => r.errors.length > 0).length ?? 0;

  return (
    <Card title={t('import.title')}>
      <Steps
        current={currentStep}
        items={[{ title: t('import.step_upload') }, { title: t('import.step_mapping') }, { title: t('import.step_confirm') }]}
        style={{ marginBottom: 24 }}
      />

      {currentStep === 0 && (
        <div style={{ maxWidth: 600, margin: '0 auto', textAlign: 'center' }}>
          <Dragger
            accept=".csv,.xlsx,.xls"
            beforeUpload={(file) => {
              handleUpload(file);
              return false;
            }}
            showUploadList={false}
            disabled={loading}
          >
            <p className="ant-upload-drag-icon"><InboxOutlined /></p>
            <p className="ant-upload-text">{t('import.drag_hint')}</p>
            <p className="ant-upload-hint">{t('import.format_hint')}</p>
          </Dragger>
          {loading && <Spin style={{ marginTop: 16 }} />}
        </div>
      )}

      {currentStep === 1 && (
        <>
          <Table
            columns={mappingColumns}
            dataSource={columns}
            rowKey="header"
            pagination={false}
            size="small"
            style={{ marginBottom: 16 }}
            title={() => t('import.mapping_title')}
          />
          <Space>
            <Button type="primary" onClick={handlePreview} loading={loading}>
              {t('import.preview_data')}
            </Button>
            <Button onClick={handleNextStep} disabled={!preview}>
              {t('import.confirm_mapping')}
            </Button>
          </Space>
          {preview && (
            <div style={{ marginTop: 16 }}>
              <Alert
                message={t('import.preview_summary', {
                  total: preview.total_rows,
                  preview: preview.preview_count,
                  errorInfo: errorCount > 0 ? `，${errorCount} ${t('import.error_rows')}` : '',
                })}
                type={errorCount > 0 ? 'warning' : 'success'}
                showIcon
                style={{ marginBottom: 8 }}
              />
              <Table
                columns={previewColumns}
                dataSource={preview.rows}
                rowKey="row_number"
                pagination={{ pageSize: 20 }}
                scroll={{ x: 'max-content' }}
                size="small"
                rowClassName={(record) => record.errors.length > 0 ? 'import-error-row' : ''}
              />
            </div>
          )}
        </>
      )}

      {currentStep === 2 && (
        <>
          {!importResult ? (
            <div style={{ textAlign: 'center', padding: 48 }}>
              <Alert
                message={t('import.import_alert_before', { total: preview?.total_rows || job?.total_rows || 0 })}
                description={
                  errorCount > 0
                    ? t('import.import_alert_errors', { error: errorCount })
                    : t('import.import_alert_ok')
                }
                type={errorCount > 0 ? 'warning' : 'success'}
                showIcon
                style={{ marginBottom: 24, textAlign: 'left' }}
              />
              <Checkbox checked={overwrite} onChange={(e) => setOverwrite(e.target.checked)} style={{ marginBottom: 24 }}>
                {t('import.overwrite_confirm')}
              </Checkbox>
              <br />
              <Space size="large">
                <Button type="primary" size="large" icon={<CheckCircleOutlined />} onClick={handleConfirm} loading={loading}>
                  {t('import.start_import')}
                </Button>
                <Button size="large" onClick={() => setCurrentStep(1)}>
                  {t('import.back_to_mapping')}
                </Button>
              </Space>
            </div>
          ) : (
            <Result
              status={importResult.error_rows === 0 ? 'success' : 'warning'}
              title={t('import.import_complete')}
              subTitle={t('import.import_complete_desc', { total: importResult.total_rows, success: importResult.success_rows, error: importResult.error_rows })}
              extra={[
                <Button type="primary" key="history" onClick={() => router.push('/dashboard/import/history')}>
                  {t('import.view_history')}
                </Button>,
                <Button key="properties" onClick={() => router.push('/dashboard/properties')}>
                  {t('import.view_properties')}
                </Button>,
                <Button
                  key="new"
                  onClick={() => {
                    setCurrentStep(0);
                    setJob(null);
                    setColumns([]);
                    setMapping({});
                    setPreview(null);
                    setImportResult(null);
                    setOverwrite(false);
                  }}
                >
                  {t('import.continue_import')}
                </Button>,
              ]}
            />
          )}
        </>
      )}
    </Card>
  );
}
