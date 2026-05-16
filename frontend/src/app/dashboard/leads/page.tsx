'use client';

import { useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProTable } from '@ant-design/pro-components';
import type { ProColumns, ActionType } from '@ant-design/pro-components';
import { Button, Tag, Space, App, Modal, Form, Input, Select, Descriptions, Spin } from 'antd';
import { PlusOutlined, RobotOutlined, SearchOutlined, SendOutlined, EyeOutlined } from '@ant-design/icons';
import {
  getLeads,
  createLead,
  updateLead,
  parseLeadNeeds,
  searchRecommendations,
  markRecommendationSent,
} from '@/lib/api';
import PermissionButton from '@/components/PermissionButton';
import { useI18n } from '@/i18n/i18n';
import type { LeadOut, LeadCreate, LeadUpdate } from '@/types/lead';
import type { RecommendationSearchResult } from '@/types/ai';

const statusColor: Record<string, string> = {
  new: 'default',
  parsed: 'blue',
  in_progress: 'orange',
  pending_reply: 'red',
  contacted: 'green',
  closed: 'purple',
};

export default function LeadsPage() {
  const router = useRouter();
  const actionRef = useRef<ActionType>();
  const { message: msg } = App.useApp();
  const { t } = useI18n();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingLead, setEditingLead] = useState<LeadOut | null>(null);
  const [form] = Form.useForm();
  const [parsing, setParsing] = useState<string | null>(null);
  const [recoOpen, setRecoOpen] = useState(false);
  const [recoResults, setRecoResults] = useState<RecommendationSearchResult[]>([]);
  const [recoLoading, setRecoLoading] = useState(false);
  const [currentLead, setCurrentLead] = useState<LeadOut | null>(null);
  const [sendingIds, setSendingIds] = useState<Set<string>>(new Set());

  const openCreate = () => {
    setEditingLead(null);
    form.resetFields();
    form.setFieldsValue({ language: 'zh' });
    setModalOpen(true);
  };

  const openEdit = (lead: LeadOut) => {
    setEditingLead(lead);
    form.setFieldsValue({
      name: lead.name,
      phone: lead.phone,
      status: lead.status,
      assigned_agent_id: lead.assigned_agent_id,
    });
    setModalOpen(true);
  };

  const handleOk = async () => {
    const values = await form.validateFields();
    try {
      if (editingLead) {
        const data: LeadUpdate = {
          name: values.name,
          phone: values.phone,
          status: values.status,
          assigned_agent_id: values.assigned_agent_id,
        };
        await updateLead(editingLead.id, data);
        msg.success(t('leads.update_success'));
      } else {
        const data: LeadCreate = {
          name: values.name,
          phone: values.phone,
          language: values.language,
          original_message: values.original_message,
          assigned_agent_id: values.assigned_agent_id,
        };
        await createLead(data);
        msg.success(t('leads.create_success'));
      }
      setModalOpen(false);
      actionRef.current?.reload();
    } catch {
      msg.error(t('leads.operation_failed'));
    }
  };

  const handleParse = async (leadId: string) => {
    setParsing(leadId);
    try {
      await parseLeadNeeds(leadId);
      msg.success(t('leads.parse_success'));
      actionRef.current?.reload();
    } catch {
      msg.error(t('leads.parse_failed'));
    } finally {
      setParsing(null);
    }
  };

  const handleSearchReco = async (lead: LeadOut) => {
    setCurrentLead(lead);
    setRecoOpen(true);
    setRecoLoading(true);
    try {
      const res = await searchRecommendations({ lead_id: lead.id, limit: 10 });
      setRecoResults(res.results);
    } catch {
      msg.error(t('leads.reco_search_failed'));
      setRecoResults([]);
    } finally {
      setRecoLoading(false);
    }
  };

  const handleMarkSent = async (recoId: string) => {
    setSendingIds((prev) => new Set(prev).add(recoId));
    try {
      await markRecommendationSent(recoId);
      msg.success(t('leads.mark_sent_success'));
      setRecoResults((prev) =>
        prev.map((r) =>
          r.property_id === recoId ? { ...r } : r
        )
      );
    } catch {
      msg.error(t('leads.mark_sent_failed'));
    } finally {
      setSendingIds((prev) => {
        const next = new Set(prev);
        next.delete(recoId);
        return next;
      });
    }
  };

  const columns: ProColumns<LeadOut>[] = [
    { title: t('leads.name'), dataIndex: 'name', key: 'name', width: 120 },
    { title: t('leads.phone'), dataIndex: 'phone', key: 'phone', width: 120, search: false },
    {
      title: t('leads.language'), dataIndex: 'language', key: 'language', width: 60,
      valueEnum: { zh: { text: t('leads.language_zh') }, en: { text: t('leads.language_en') }, th: { text: t('leads.language_th') } },
    },
    {
      title: t('common.status'), dataIndex: 'status', key: 'status', width: 80,
      valueEnum: {
        new: { text: t('status.new') },
        parsed: { text: t('status.parsed') },
        in_progress: { text: t('status.in_progress') },
        contacted: { text: t('status.contacted') },
        closed: { text: t('status.closed') },
      },
      render: (_, r) => <Tag color={statusColor[r.status]}>{t(`status.${r.status}`)}</Tag>,
    },
    {
      title: t('leads.target_location'), dataIndex: 'target_location', key: 'target_location', width: 150, search: false,
      render: (_, r) => r.target_location || '-',
    },
    {
      title: t('leads.budget_range'), key: 'budget', width: 120, search: false,
      render: (_, r) =>
        r.budget_min || r.budget_max
          ? `${r.budget_min ? r.budget_min.toLocaleString() : '?'} - ${r.budget_max ? r.budget_max.toLocaleString() : '?'} ฿`
          : '-',
    },
    {
      title: t('leads.bedroom_count'), dataIndex: 'bedroom_count', key: 'bedroom_count', width: 60, search: false,
      render: (_, r) => (r.bedroom_count != null ? `${r.bedroom_count}${t('properties.bedroom_unit', { n: r.bedroom_count })}` : '-'),
    },
    {
      title: t('leads.pet_required'), dataIndex: 'pet_required', key: 'pet_required', width: 60, search: false,
      render: (_, r) => (r.pet_required ? <Tag color="orange">{t('leads.pet_tag')}</Tag> : '-'),
    },
    {
      title: t('properties.tags'), dataIndex: 'tags', key: 'tags', width: 150, search: false,
      render: (_, r) => r.tags?.slice(0, 3).map((tag) => <Tag key={tag}>{tag}</Tag>),
    },
    {
      title: t('common.created_at'), dataIndex: 'created_at', key: 'created_at', width: 150, search: false,
      render: (_, r) => new Date(r.created_at).toLocaleDateString(),
    },
    {
      title: t('common.actions'), key: 'action', width: 260, search: false,
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => router.push(`/dashboard/leads/${record.id}`)}>
            {t('common.view')}
          </Button>
          <Button size="small" onClick={() => openEdit(record)}>{t('common.edit')}</Button>
          <Button
            size="small"
            icon={<RobotOutlined />}
            loading={parsing === record.id}
            onClick={() => handleParse(record.id)}
            disabled={!record.original_message}
          >
            {t('leads.ai_parse_btn')}
          </Button>
          <Button
            size="small"
            type="primary"
            icon={<SearchOutlined />}
            onClick={() => handleSearchReco(record)}
            disabled={record.status === 'closed'}
          >
            {t('leads.search_reco')}
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <>
      <ProTable<LeadOut>
        columns={columns}
        actionRef={actionRef}
        request={async (params) => {
          const { current, pageSize, ...filters } = params;
          const res = await getLeads({
            ...filters,
            page: current,
            page_size: pageSize,
          });
          return { data: res.items as LeadOut[], total: res.total, success: true };
        }}
        rowKey="id"
        search={{ labelWidth: 'auto' }}
        pagination={{ pageSize: 20 }}
        headerTitle={t('leads.title')}
        toolBarRender={() => [
          <PermissionButton key="create" requiredRole="Agent">
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              {t('leads.create')}
            </Button>
          </PermissionButton>,
        ]}
      />

      <Modal
        title={editingLead ? t('leads.edit') : t('leads.create')}
        open={modalOpen}
        onOk={handleOk}
        onCancel={() => setModalOpen(false)}
        width={640}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label={t('leads.name')} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label={t('leads.phone')}>
            <Input placeholder="0812345678" />
          </Form.Item>
          {!editingLead && (
            <>
              <Form.Item name="language" label={t('leads.language')} rules={[{ required: true }]}>
                <Select
                  options={[
                    { label: t('leads.language_zh'), value: 'zh' },
                    { label: t('leads.language_en'), value: 'en' },
                    { label: t('leads.language_th'), value: 'th' },
                  ]}
                />
              </Form.Item>
              <Form.Item name="original_message" label={t('leads.original_message')} rules={[{ required: true }]}>
                <Input.TextArea rows={4} />
              </Form.Item>
            </>
          )}
          <Form.Item name="status" label={t('common.status')}>
            <Select
              options={[
                { label: t('status.new'), value: 'new' },
                { label: t('status.parsed'), value: 'parsed' },
                { label: t('status.in_progress'), value: 'in_progress' },
                { label: t('status.pending_reply'), value: 'pending_reply' },
                { label: t('status.contacted'), value: 'contacted' },
                { label: t('status.closed'), value: 'closed' },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={t('leads.reco_title', { name: currentLead?.name || '' })}
        open={recoOpen}
        onCancel={() => setRecoOpen(false)}
        footer={null}
        width={900}
      >
        {recoLoading ? (
          <div style={{ textAlign: 'center', padding: 48 }}><Spin size="large" /></div>
        ) : recoResults.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 48, color: '#999' }}>{t('leads.no_reco_match')}</div>
        ) : (
          <div style={{ maxHeight: 500, overflow: 'auto' }}>
            {recoResults.map((r, idx) => (
              <div
                key={r.property_id}
                style={{
                  border: '1px solid #f0f0f0',
                  borderRadius: 8,
                  padding: 16,
                  marginBottom: 12,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Space>
                    <strong>#{idx + 1}</strong>
                    <strong>{r.name}</strong>
                    <Tag color="blue">{r.property_code}</Tag>
                  </Space>
                  <Button
                    size="small"
                    type="primary"
                    icon={<SendOutlined />}
                    loading={sendingIds.has(r.property_id)}
                    onClick={() => handleMarkSent(r.property_id)}
                  >
                    {t('leads.mark_sent')}
                  </Button>
                </div>
                <Descriptions size="small" column={4}>
                  <Descriptions.Item label={t('properties.monthly_rent')}>{r.monthly_rent.toLocaleString()} ฿</Descriptions.Item>
                  <Descriptions.Item label={t('properties.bedroom_count')}>{r.bedroom_count}</Descriptions.Item>
                  <Descriptions.Item label={t('properties.district')}>{r.district}</Descriptions.Item>
                  <Descriptions.Item label={t('leads.match_score')}>
                    <Tag color={r.match_score >= 0.7 ? 'green' : r.match_score >= 0.4 ? 'orange' : 'red'}>
                      {(r.match_score * 100).toFixed(0)}%
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label={t('leads.distance')}>
                    {r.distance_meters != null
                      ? r.distance_meters < 1000
                        ? `${r.distance_meters}m`
                        : `${(r.distance_meters / 1000).toFixed(1)}km`
                      : '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label={t('leads.commute')}>
                    {r.duration_minutes != null ? `${r.duration_minutes}${t('common.time')}` : '-'}
                  </Descriptions.Item>
                </Descriptions>
                {r.reasons.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    {r.reasons.map((reason, i) => (
                      <Tag key={i} color="green">{reason}</Tag>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Modal>
    </>
  );
}
