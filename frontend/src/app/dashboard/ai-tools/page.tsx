'use client';

import { useState } from 'react';
import { Tabs, Card, Form, Input, Select, Button, App, Tag, Descriptions } from 'antd';
import { RobotOutlined, TagsOutlined, MessageOutlined, ClearOutlined } from '@ant-design/icons';
import { getProperties } from '@/lib/api';
import {
  aiParseLead,
  aiGenerateTags,
  aiGenerateMessage,
  aiCleanData,
} from '@/lib/api';
import { useI18n } from '@/i18n/i18n';
import type { ParseLeadResponse, GenerateTagsResponse, GenerateMessageResponse } from '@/types/ai';
import type { PropertyListOut } from '@/types/property';

const { TextArea } = Input;

export default function AIToolsPage() {
  const { message: msg } = App.useApp();
  const { t } = useI18n();

  const [parseLoading, setParseLoading] = useState(false);
  const [parseResult, setParseResult] = useState<ParseLeadResponse | null>(null);
  const [parseForm] = Form.useForm();

  const handleParse = async () => {
    const values = await parseForm.validateFields();
    setParseLoading(true);
    try {
      const res = await aiParseLead({ message: values.message, language: values.language });
      setParseResult(res);
      msg.success(t('ai.parse_success'));
    } catch {
      msg.error(t('ai.parse_failed'));
      setParseResult(null);
    } finally {
      setParseLoading(false);
    }
  };

  const [tagsLoading, setTagsLoading] = useState(false);
  const [tagsResult, setTagsResult] = useState<GenerateTagsResponse | null>(null);
  const [tagForm] = Form.useForm();
  const [properties, setProperties] = useState<PropertyListOut[]>([]);

  const loadProperties = async () => {
    if (properties.length > 0) return;
    try {
      const res = await getProperties({ page: 1, page_size: 200 });
      setProperties(res.items as PropertyListOut[]);
    } catch {
      // ignore
    }
  };

  const handleGenerateTags = async () => {
    const values = await tagForm.validateFields();
    setTagsLoading(true);
    try {
      const res = await aiGenerateTags({ property_id: values.property_id, language: values.language });
      setTagsResult(res);
      msg.success(t('ai.tags_success'));
    } catch {
      msg.error(t('ai.tags_failed'));
      setTagsResult(null);
    } finally {
      setTagsLoading(false);
    }
  };

  const [msgLoading, setMsgLoading] = useState(false);
  const [msgResult, setMsgResult] = useState<GenerateMessageResponse | null>(null);
  const [msgForm] = Form.useForm();

  const handleGenerateMessage = async () => {
    const values = await msgForm.validateFields();
    setMsgLoading(true);
    try {
      const res = await aiGenerateMessage({
        lead_id: values.lead_id,
        property_ids: values.property_ids,
        language: values.language,
        tone: values.tone,
      });
      setMsgResult(res);
      msg.success(t('ai.message_success'));
    } catch {
      msg.error(t('ai.message_failed'));
      setMsgResult(null);
    } finally {
      setMsgLoading(false);
    }
  };

  const [cleanLoading, setCleanLoading] = useState(false);
  const [cleanResult, setCleanResult] = useState<string | null>(null);
  const [cleanForm] = Form.useForm();

  const handleClean = async () => {
    const values = await cleanForm.validateFields();
    setCleanLoading(true);
    try {
      const res = await aiCleanData({
        column_name: values.column_name,
        sample_values: values.sample_values.split('\n').filter(Boolean),
        expected_type: values.expected_type,
      });
      setCleanResult(JSON.stringify(res, null, 2));
      msg.success(t('ai.clean_success'));
    } catch {
      msg.error(t('ai.clean_failed'));
      setCleanResult(null);
    } finally {
      setCleanLoading(false);
    }
  };

  const tabItems = [
    {
      key: 'parse',
      label: <span><RobotOutlined /> {t('ai.parse_lead')}</span>,
      children: (
        <Card>
          <Form form={parseForm} layout="vertical">
            <Form.Item name="language" label={t('ai.language')} initialValue="zh">
              <Select
                options={[
                  { label: t('leads.language_zh'), value: 'zh' },
                  { label: t('leads.language_en'), value: 'en' },
                  { label: t('leads.language_th'), value: 'th' },
                ]}
              />
            </Form.Item>
            <Form.Item name="message" label={t('ai.message')} rules={[{ required: true }]}>
              <TextArea rows={6} placeholder={t('ai.parse_placeholder')} />
            </Form.Item>
            <Button type="primary" icon={<RobotOutlined />} onClick={handleParse} loading={parseLoading}>
              {t('ai.btn_parse')}
            </Button>
          </Form>
          {parseResult && (
            <Card title={t('ai.parse_result')} style={{ marginTop: 16 }}>
              <Descriptions column={2} size="small">
                <Descriptions.Item label={t('ai.target_location')}>{parseResult.target_location || '-'}</Descriptions.Item>
                <Descriptions.Item label={t('ai.preferred_transport')}>{parseResult.preferred_transport || '-'}</Descriptions.Item>
                <Descriptions.Item label={t('ai.budget_lower')}>{parseResult.budget_min?.toLocaleString() || '-'} ฿</Descriptions.Item>
                <Descriptions.Item label={t('ai.budget_upper')}>{parseResult.budget_max?.toLocaleString() || '-'} ฿</Descriptions.Item>
                <Descriptions.Item label={t('ai.bedrooms')}>{parseResult.bedroom_count != null ? `${parseResult.bedroom_count}${t('properties.bedroom_unit', { n: parseResult.bedroom_count })}` : '-'}</Descriptions.Item>
                <Descriptions.Item label={t('ai.pet_needed')}>{parseResult.pet_required ? t('common.yes') : t('common.no')}</Descriptions.Item>
              </Descriptions>
              <div style={{ marginTop: 12 }}>
                <strong>{t('properties.tags')}: </strong>
                {parseResult.tags?.length > 0
                  ? parseResult.tags.map((tag) => <Tag key={tag}>{tag}</Tag>)
                  : '-'}
              </div>
              {parseResult.missing_fields?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <strong>{t('ai.missing_fields')}: </strong>
                  {parseResult.missing_fields.map((f) => <Tag key={f} color="red">{f}</Tag>)}
                </div>
              )}
              {parseResult.follow_up_questions?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <strong>{t('ai.follow_up')}: </strong>
                  <ul>
                    {parseResult.follow_up_questions.map((q, i) => (
                      <li key={i}>{q}</li>
                    ))}
                  </ul>
                </div>
              )}
            </Card>
          )}
        </Card>
      ),
    },
    {
      key: 'tags',
      label: <span><TagsOutlined /> {t('ai.generate_tags')}</span>,
      children: (
        <Card>
          <Form form={tagForm} layout="vertical">
            <Form.Item name="language" label={t('ai.language')} initialValue="zh">
              <Select
                options={[
                  { label: t('leads.language_zh'), value: 'zh' },
                  { label: t('leads.language_en'), value: 'en' },
                  { label: t('leads.language_th'), value: 'th' },
                ]}
              />
            </Form.Item>
            <Form.Item name="property_id" label={t('ai.select_property')} rules={[{ required: true }]}>
              <Select
                showSearch
                placeholder={t('ai.search_property')}
                filterOption={(input, option) =>
                  (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
                }
                options={properties.map((p) => ({
                  label: `${p.property_code} - ${p.name}`,
                  value: p.id,
                }))}
                onFocus={loadProperties}
              />
            </Form.Item>
            <Button type="primary" icon={<TagsOutlined />} onClick={handleGenerateTags} loading={tagsLoading}>
              {t('ai.btn_tags')}
            </Button>
          </Form>
          {tagsResult && (
            <Card title={t('ai.tags_result')} style={{ marginTop: 16 }}>
              <div style={{ marginBottom: 12 }}>
                <strong>{t('properties.tags')}: </strong>
                {tagsResult.tags.map((tag) => (
                  <Tag key={tag} color="blue">{tag}</Tag>
                ))}
              </div>
              <div>
                <strong>{t('ai.highlights')}: </strong>
                <ul>
                  {tagsResult.highlights.map((h, i) => (
                    <li key={i}>{h}</li>
                  ))}
                </ul>
              </div>
            </Card>
          )}
        </Card>
      ),
    },
    {
      key: 'message',
      label: <span><MessageOutlined /> {t('ai.generate_message')}</span>,
      children: (
        <Card>
          <Form form={msgForm} layout="vertical">
            <Form.Item name="language" label={t('ai.language')} initialValue="zh">
              <Select
                options={[
                  { label: t('leads.language_zh'), value: 'zh' },
                  { label: t('leads.language_en'), value: 'en' },
                  { label: t('leads.language_th'), value: 'th' },
                ]}
              />
            </Form.Item>
            <Form.Item name="tone" label={t('ai.tone')} initialValue="friendly">
              <Select
                options={[
                  { label: t('ai.tone_friendly'), value: 'friendly' },
                  { label: t('ai.tone_professional'), value: 'professional' },
                  { label: t('ai.tone_urgent'), value: 'urgent' },
                ]}
              />
            </Form.Item>
            <Form.Item name="lead_id" label={t('ai.lead_id')} rules={[{ required: true }]}>
              <Input placeholder="UUID" />
            </Form.Item>
            <Form.Item name="property_ids" label={t('ai.property_ids_hint')} rules={[{ required: true }]}>
              <Input placeholder="UUID1, UUID2, UUID3" />
            </Form.Item>
            <Button type="primary" icon={<MessageOutlined />} onClick={handleGenerateMessage} loading={msgLoading}>
              {t('ai.btn_message')}
            </Button>
          </Form>
          {msgResult && (
            <div style={{ marginTop: 16 }}>
              {msgResult.messages.map((item, i) => (
                <Card key={i} title={t('ai.property_card_title', { n: i + 1 })} style={{ marginBottom: 12 }}>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{item.message}</p>
                </Card>
              ))}
            </div>
          )}
        </Card>
      ),
    },
    {
      key: 'clean',
      label: <span><ClearOutlined /> {t('ai.clean_data')}</span>,
      children: (
        <Card>
          <Form form={cleanForm} layout="vertical">
            <Form.Item name="column_name" label={t('ai.column_name')} rules={[{ required: true }]}>
              <Input placeholder={t('ai.column_name_placeholder')} />
            </Form.Item>
            <Form.Item name="expected_type" label={t('ai.expected_type')} initialValue="auto">
              <Select
                options={[
                  { label: t('ai.type_auto'), value: 'auto' },
                  { label: t('ai.type_price'), value: 'price' },
                  { label: t('ai.type_phone'), value: 'phone' },
                  { label: t('ai.type_address'), value: 'address' },
                  { label: t('ai.type_district'), value: 'district' },
                  { label: t('ai.type_name'), value: 'name' },
                ]}
              />
            </Form.Item>
            <Form.Item name="sample_values" label={t('ai.sample_values')} rules={[{ required: true }]}>
              <TextArea rows={6} placeholder={t('ai.clean_placeholder')} />
            </Form.Item>
            <Button type="primary" icon={<ClearOutlined />} onClick={handleClean} loading={cleanLoading}>
              {t('ai.btn_clean')}
            </Button>
          </Form>
          {cleanResult && (
            <Card title={t('ai.clean_result')} style={{ marginTop: 16 }}>
              <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
                {cleanResult}
              </pre>
            </Card>
          )}
        </Card>
      ),
    },
  ];

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>{t('ai.title')}</h2>
      <Tabs defaultActiveKey="parse" items={tabItems} />
    </div>
  );
}
