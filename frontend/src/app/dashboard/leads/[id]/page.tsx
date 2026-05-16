'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Card, Descriptions, Tag, Button, Space, Spin, Tabs, App, Empty, Modal,
} from 'antd';
import {
  ArrowLeftOutlined, RobotOutlined, SearchOutlined,
  SendOutlined, CopyOutlined, MessageOutlined, HistoryOutlined,
} from '@ant-design/icons';
import { getLead, parseLeadNeeds } from '@/lib/api';
import {
  searchRecommendations,
  getLeadRecommendations,
  saveRecommendationMessage,
  markRecommendationSent,
  aiGenerateMessage,
} from '@/lib/api';
import { useI18n } from '@/i18n/i18n';
import type { LeadOut } from '@/types/lead';
import type { RecommendationSearchResult, RecommendationOut } from '@/types/ai';

const statusColor: Record<string, string> = {
  new: 'default', parsed: 'blue', in_progress: 'orange', pending_reply: 'red', contacted: 'green', closed: 'purple',
};

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { message: msg } = App.useApp();
  const { t } = useI18n();

  const [lead, setLead] = useState<LeadOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [parsing, setParsing] = useState(false);
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<RecommendationSearchResult[]>([]);
  const [history, setHistory] = useState<RecommendationOut[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [generatingMsg, setGeneratingMsg] = useState<string | null>(null);
  const [sendingIds, setSendingIds] = useState<Set<string>>(new Set());
  const [savingMsg, setSavingMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('info');

  const loadLead = useCallback(async () => {
    try {
      const data = await getLead(id);
      setLead(data);
    } catch { msg.error(t('leads.load_failed')); }
    finally { setLoading(false); }
  }, [id, msg, t]);

  useEffect(() => { loadLead(); }, [loadLead]);

  const handleParse = async () => {
    setParsing(true);
    try {
      await parseLeadNeeds(id);
      msg.success(t('leads.parse_success'));
      await loadLead();
    } catch { msg.error(t('leads.parse_failed')); }
    finally { setParsing(false); }
  };

  const handleSearch = async () => {
    if (!lead) return;
    setSearching(true);
    setActiveTab('search');
    try {
      const res = await searchRecommendations({ lead_id: lead.id, limit: 10 });
      setSearchResults(res.results);
    } catch { msg.error(t('leads.reco_search_failed')); }
    finally { setSearching(false); }
  };

  const loadHistory = async () => {
    setHistoryLoading(true);
    setActiveTab('history');
    try {
      const data = await getLeadRecommendations(id);
      setHistory(data);
    } catch { msg.error(t('leads.load_failed')); }
    finally { setHistoryLoading(false); }
  };

  const handleGenerateMessage = async (propertyId: string) => {
    if (!lead) return;
    setGeneratingMsg(propertyId);
    try {
      const res = await aiGenerateMessage({
        lead_id: lead.id,
        property_ids: [propertyId],
        language: lead.language || 'zh',
        tone: 'friendly',
      });
      return res.messages[0]?.message || '';
    } catch { msg.error(t('leads.ai_generate_failed')); return ''; }
    finally { setGeneratingMsg(null); }
  };

  const handleSaveAndGenerate = async (propertyId: string) => {
    const aiMsg = await handleGenerateMessage(propertyId);
    if (!aiMsg) return;

    setSavingMsg(propertyId);
    try {
      const existingRec = history.find(h => h.property_id === propertyId && !h.ai_message);
      if (existingRec) {
        await saveRecommendationMessage(existingRec.id, { ai_message: aiMsg });
        msg.success(t('leads.message_saved'));
        await loadHistory();
        setActiveTab('history');
      } else {
        Modal.info({
          title: t('ai.generate_message'),
          width: 600,
          content: <div style={{ whiteSpace: 'pre-wrap', marginTop: 16 }}>{aiMsg}</div>,
          okText: t('common.close'),
        });
      }
    } catch { msg.error(t('leads.save_failed')); }
    finally { setSavingMsg(null); }
  };

  const handleMarkSent = async (recoId: string) => {
    setSendingIds(prev => new Set(prev).add(recoId));
    try {
      await markRecommendationSent(recoId);
      msg.success(t('leads.mark_sent_success'));
      await loadHistory();
    } catch { msg.error(t('leads.mark_sent_failed')); }
    finally {
      setSendingIds(prev => {
        const next = new Set(prev);
        next.delete(recoId);
        return next;
      });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => msg.success(t('leads.copy_success')));
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!lead) return <Card title={t('leads.not_found')}><Button onClick={() => router.back()}>{t('common.back')}</Button></Card>;

  const needs = lead.parsed_needs as Record<string, unknown> | null;

  const renderRecoCard = (
    item: RecommendationSearchResult | RecommendationOut,
    index: number,
    isHistory: boolean,
  ) => {
    const propId = 'property_id' in item ? item.property_id : '';
    const propName = 'property_name' in item ? item.property_name : ('name' in item ? (item as RecommendationSearchResult).name : '');
    const propCode = 'property_code' in item ? item.property_code : '';
    const rent = 'monthly_rent' in item ? (item.monthly_rent ?? 0) : 0;
    const bedrooms = 'bedroom_count' in item ? (item.bedroom_count ?? 0) : 0;
    const district = 'district' in item ? (item.district ?? '') : '';
    const distance = item.distance_meters;
    const duration = item.duration_minutes;
    const score = item.match_score;
    const reasons = ('reason_json' in item && item.reason_json)
      ? ((item.reason_json as Record<string, unknown>).reasons as string[] || [])
      : ('reasons' in item ? (item as RecommendationSearchResult).reasons : []);
    const aiMessage = 'ai_message' in item ? item.ai_message : null;
    const sent = 'sent_to_customer' in item ? item.sent_to_customer : false;
    const recoId = 'id' in item ? item.id : '';

    return (
      <Card
        key={isHistory ? recoId : propId}
        size="small"
        style={{ marginBottom: 12 }}
        title={
          <Space>
            <strong>#{index + 1}</strong>
            <span>{propName || propCode}</span>
            {propCode && <Tag color="blue">{propCode}</Tag>}
            {sent && <Tag color="green">{t('leads.reco_sent')}</Tag>}
          </Space>
        }
        extra={
          <Tag color={score >= 0.7 ? 'green' : score >= 0.4 ? 'orange' : 'red'}>
            {t('leads.match_score')} {(score * 100).toFixed(0)}%
          </Tag>
        }
      >
        <Descriptions size="small" column={4}>
          <Descriptions.Item label={t('properties.monthly_rent')}>{rent.toLocaleString()} ฿</Descriptions.Item>
          <Descriptions.Item label={t('properties.layout')}>{bedrooms}{t('properties.bedroom_unit', { n: bedrooms })}</Descriptions.Item>
          <Descriptions.Item label={t('properties.district')}>{district || '-'}</Descriptions.Item>
          <Descriptions.Item label={t('leads.distance')}>
            {distance != null
              ? distance < 1000 ? `${distance}m` : `${(distance / 1000).toFixed(1)}km`
              : '-'}
          </Descriptions.Item>
          <Descriptions.Item label={t('leads.commute')}>
            {duration != null ? `${duration}${t('common.time')}` : '-'}
          </Descriptions.Item>
        </Descriptions>

        {reasons.length > 0 && (
          <div style={{ marginTop: 8, marginBottom: 8 }}>
            {reasons.map((reason: string, i: number) => (
              <Tag key={i} color="green">{reason}</Tag>
            ))}
          </div>
        )}

        {aiMessage && (
          <div style={{
            background: '#f6ffed', padding: 12, borderRadius: 6,
            marginTop: 8, marginBottom: 8, whiteSpace: 'pre-wrap',
          }}>
            {aiMessage}
          </div>
        )}

        <Space style={{ marginTop: 8 }}>
          {!aiMessage && (
            <Button
              size="small"
              icon={<MessageOutlined />}
              loading={generatingMsg === propId || savingMsg === propId}
              onClick={() => handleSaveAndGenerate(propId)}
            >
              {t('leads.generate_copy')}
            </Button>
          )}
          {aiMessage && (
            <Button
              size="small"
              icon={<CopyOutlined />}
              onClick={() => copyToClipboard(aiMessage)}
            >
              {t('leads.copy_copy')}
            </Button>
          )}
          {isHistory && !sent && (
            <Button
              size="small"
              type="primary"
              icon={<SendOutlined />}
              loading={sendingIds.has(recoId)}
              onClick={() => handleMarkSent(recoId)}
            >
              {t('leads.mark_sent')}
            </Button>
          )}
        </Space>
      </Card>
    );
  };

  const tabItems = [
    {
      key: 'info',
      label: t('leads.basic_info'),
      children: (
        <Card>
          <Descriptions bordered column={2}>
            <Descriptions.Item label={t('leads.name')}>{lead.name}</Descriptions.Item>
            <Descriptions.Item label={t('leads.phone')}>{lead.phone || '-'}</Descriptions.Item>
            <Descriptions.Item label={t('leads.language')}>
              <Tag>{t(`leads.language_${lead.language}`)}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label={t('common.status')}>
              <Tag color={statusColor[lead.status]}>{t(`status.${lead.status}`)}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label={t('common.created_at')}>{new Date(lead.created_at).toLocaleString()}</Descriptions.Item>
            <Descriptions.Item label={t('common.updated_at')}>{lead.updated_at ? new Date(lead.updated_at).toLocaleString() : '-'}</Descriptions.Item>
            <Descriptions.Item label={t('leads.original_requirement')} span={2}>
              <div style={{ whiteSpace: 'pre-wrap' }}>{lead.original_message || '-'}</div>
            </Descriptions.Item>
          </Descriptions>
        </Card>
      ),
    },
    {
      key: 'needs',
      label: t('leads.ai_result'),
      children: (
        <Card
          extra={
            <Button icon={<RobotOutlined />} onClick={handleParse} loading={parsing}>
              {t('leads.reparse')}
            </Button>
          }
        >
          {needs ? (
            <Descriptions bordered column={2}>
              <Descriptions.Item label={t('leads.target_location')}>{lead.target_location || '-'}</Descriptions.Item>
              <Descriptions.Item label={t('leads.preferred_transport')}>{lead.preferred_transport || '-'}</Descriptions.Item>
              <Descriptions.Item label={t('leads.budget_min')}>{lead.budget_min?.toLocaleString() || '-'} ฿</Descriptions.Item>
              <Descriptions.Item label={t('leads.budget_max')}>{lead.budget_max?.toLocaleString() || '-'} ฿</Descriptions.Item>
              <Descriptions.Item label={t('leads.bedroom_count')}>{lead.bedroom_count != null ? `${lead.bedroom_count}${t('properties.bedroom_unit', { n: lead.bedroom_count })}` : '-'}</Descriptions.Item>
              <Descriptions.Item label={t('leads.pet_required')}>{lead.pet_required ? <Tag color="orange">{t('common.yes')}</Tag> : t('common.no')}</Descriptions.Item>
              <Descriptions.Item label={t('properties.tags')} span={2}>
                {lead.tags?.length ? lead.tags.map((tag: string) => <Tag key={tag}>{tag}</Tag>) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label={t('leads.full_parsed_json')} span={2}>
                <pre style={{ whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 8, borderRadius: 4, maxHeight: 200, overflow: 'auto' }}>
                  {JSON.stringify(needs, null, 2)}
                </pre>
              </Descriptions.Item>
            </Descriptions>
          ) : (
            <Empty description={t('leads.not_parsed')}>
              <Button icon={<RobotOutlined />} onClick={handleParse} loading={parsing}>
                {t('leads.start_parse')}
              </Button>
            </Empty>
          )}
        </Card>
      ),
    },
    {
      key: 'search',
      label: t('leads.reco_search'),
      children: (
        <Card
          extra={
            <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch} loading={searching}>
              {t('leads.search_properties')}
            </Button>
          }
        >
          {searching ? (
            <Spin style={{ display: 'block', margin: '40px auto' }} />
          ) : searchResults.length === 0 ? (
            <Empty description={t('leads.no_reco_yet')} />
          ) : (
            <div>
              {searchResults.map((r, i) => renderRecoCard(r, i, false))}
            </div>
          )}
        </Card>
      ),
    },
    {
      key: 'history',
      label: <span><HistoryOutlined /> {t('leads.reco_history')}</span>,
      children: (
        <Card
          extra={
            <Button onClick={loadHistory} loading={historyLoading}>
              {t('leads.refresh')}
            </Button>
          }
        >
          {historyLoading ? (
            <Spin style={{ display: 'block', margin: '40px auto' }} />
          ) : history.length === 0 ? (
            <Empty description={t('leads.no_reco_history')}>
              <Button type="primary" onClick={() => { setActiveTab('search'); handleSearch(); }}>
                {t('leads.start_search')}
              </Button>
            </Empty>
          ) : (
            <div>
              {history.map((r, i) => renderRecoCard(r, i, true))}
            </div>
          )}
        </Card>
      ),
    },
  ];

  return (
    <Card
      title={`${t('leads.detail')}: ${lead.name}`}
      extra={
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => router.push('/dashboard/leads')}>
            {t('leads.back_to_list')}
          </Button>
        </Space>
      }
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
    </Card>
  );
}
