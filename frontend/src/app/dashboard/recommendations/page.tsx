'use client';

import { useEffect, useState } from 'react';
import {
  Card, Select, Button, Space, Tag, Descriptions, App, Spin, Modal, Tabs, message,
} from 'antd';
import {
  SearchOutlined, RobotOutlined, CopyOutlined, SendOutlined,
  EnvironmentOutlined, CompassOutlined,
} from '@ant-design/icons';
import {
  getLeads, searchRecommendations, aiGenerateMessage, markRecommendationSent, getLeadRecommendations,
} from '@/lib/api';
import { useI18n } from '@/i18n/i18n';
import PropertyMap from '@/components/PropertyMap';
import type { PropertyMarker } from '@/components/PropertyMap';
import type { LeadOut } from '@/types/lead';
import type { RecommendationSearchResult, RecommendationOut } from '@/types/ai';

const statusColor: Record<string, string> = {
  new: 'default', parsed: 'blue', recommended: 'orange',
  contacted: 'green', closed: 'purple',
};

export default function RecommendationsPage() {
  const { t } = useI18n();
  const { message: msg } = App.useApp();

  const [leads, setLeads] = useState<LeadOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState<LeadOut | null>(null);

  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<RecommendationSearchResult[]>([]);
  const [totalScanned, setTotalScanned] = useState(0);

  const [history, setHistory] = useState<RecommendationOut[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [generating, setGenerating] = useState<string | null>(null);
  const [generatedMessages, setGeneratedMessages] = useState<Record<string, string>>({});
  const [sending, setSending] = useState<string | null>(null);

  useEffect(() => {
    loadLeads();
  }, []);

  const loadLeads = async () => {
    setLoading(true);
    try {
      const res = await getLeads({ page: 1, page_size: 200 });
      setLeads(res.items as LeadOut[]);
    } catch {
      msg.error('加载客户列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!selectedLead) return;
    setSearching(true);
    try {
      const res = await searchRecommendations({ lead_id: selectedLead.id, limit: 20 });
      setResults(res.results);
      setTotalScanned(res.total_scanned);
      setGeneratedMessages({});
    } catch {
      msg.error('推荐搜索失败');
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleGenerateMessage = async (propertyId: string) => {
    if (!selectedLead) return;
    setGenerating(propertyId);
    try {
      const res = await aiGenerateMessage({
        lead_id: selectedLead.id,
        property_ids: [propertyId],
        language: selectedLead.language || 'zh',
        tone: 'friendly',
      });
      const msgItem = res.messages[0];
      if (msgItem) {
        setGeneratedMessages((prev) => ({ ...prev, [propertyId]: msgItem.message }));
      }
      msg.success('话术生成完成');
    } catch {
      msg.error('话术生成失败');
    } finally {
      setGenerating(null);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    msg.success('已复制');
  };

  const handleMarkSent = async (result: RecommendationSearchResult) => {
    setSending(result.property_id);
    try {
      await markRecommendationSent(result.property_id);
      msg.success('已标记发送');
    } catch {
      msg.error('标记失败');
    } finally {
      setSending(null);
    }
  };

  const loadHistory = async () => {
    if (!selectedLead) return;
    setHistoryLoading(true);
    try {
      const res = await getLeadRecommendations(selectedLead.id);
      setHistory(res);
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  }

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>
        <EnvironmentOutlined /> 推荐结果
      </h2>

      <Card style={{ marginBottom: 24 }}>
        <Space wrap style={{ width: '100%' }}>
          <Select
            showSearch
            placeholder="选择客户"
            style={{ width: 320 }}
            value={selectedLead?.id}
            onChange={(id) => {
              const lead = leads.find((l) => l.id === id) || null;
              setSelectedLead(lead);
              setResults([]);
              setGeneratedMessages({});
              setHistory([]);
            }}
            filterOption={(input, option) =>
              (option?.label as string)?.toLowerCase().includes(input.toLowerCase())
            }
            options={leads.map((l) => ({
              label: `${l.name} - ${l.target_location || '未知地点'}`,
              value: l.id,
            }))}
          />
          <Button
            type="primary"
            icon={<SearchOutlined />}
            onClick={handleSearch}
            loading={searching}
            disabled={!selectedLead}
          >
            搜索匹配房源
          </Button>
          {selectedLead && (
            <Button onClick={loadHistory} loading={historyLoading}>
              查看推荐历史
            </Button>
          )}
        </Space>

        {selectedLead && (
          <Descriptions size="small" style={{ marginTop: 16 }} column={5}>
            <Descriptions.Item label="预算">
              {selectedLead.budget_min?.toLocaleString() || '?'} - {selectedLead.budget_max?.toLocaleString() || '?'} ฿
            </Descriptions.Item>
            <Descriptions.Item label="户型">{selectedLead.bedroom_count ? `${selectedLead.bedroom_count}卧` : '不限'}</Descriptions.Item>
            <Descriptions.Item label="目标位置">{selectedLead.target_location || '未指定'}</Descriptions.Item>
            <Descriptions.Item label="宠物">{selectedLead.pet_required ? '需要' : '不限'}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={statusColor[selectedLead.status]}>{t(`status.${selectedLead.status}`)}</Tag></Descriptions.Item>
          </Descriptions>
        )}
      </Card>

      <Tabs
        items={[
          {
            key: 'results',
            label: `搜索结果 (${results.length})`,
            children: (
              <>
                {searching ? (
                  <div style={{ textAlign: 'center', padding: 48 }}><Spin size="large" /></div>
                ) : results.length === 0 ? (
                  <Card><p style={{ textAlign: 'center', color: '#999' }}>选择客户后点击「搜索匹配房源」查看推荐结果</p></Card>
                ) : (
                  <>
                    <p style={{ marginBottom: 12, color: '#888' }}>共扫描 {totalScanned} 套房源，显示前 {results.length} 套匹配结果</p>
                    {results.map((r, idx) => (
                      <Card
                        key={r.property_id}
                        style={{ marginBottom: 12 }}
                        title={
                          <Space>
                            <strong>#{idx + 1}</strong>
                            <strong>{r.name}</strong>
                            <Tag color="blue">{r.property_code}</Tag>
                            <Tag color={r.match_score >= 0.7 ? 'green' : r.match_score >= 0.4 ? 'orange' : 'red'}>
                              {(r.match_score * 100).toFixed(0)}%
                            </Tag>
                          </Space>
                        }
                        extra={
                          <Space>
                            <Button
                              size="small"
                              icon={<RobotOutlined />}
                              loading={generating === r.property_id}
                              onClick={() => handleGenerateMessage(r.property_id)}
                            >
                              生成话术
                            </Button>
                            <Button
                              size="small"
                              type="primary"
                              icon={<SendOutlined />}
                              loading={sending === r.property_id}
                              onClick={() => handleMarkSent(r)}
                            >
                              标记发送
                            </Button>
                          </Space>
                        }
                      >
                        <Descriptions size="small" column={4}>
                          <Descriptions.Item label="月租">{r.monthly_rent.toLocaleString()} ฿</Descriptions.Item>
                          <Descriptions.Item label="户型">{r.bedroom_count}卧</Descriptions.Item>
                          <Descriptions.Item label="区域">{r.district}</Descriptions.Item>
                          <Descriptions.Item label="距离">
                            {r.distance_meters != null
                              ? r.distance_meters < 1000 ? `${r.distance_meters}m` : `${(r.distance_meters / 1000).toFixed(1)}km`
                              : '-'}
                          </Descriptions.Item>
                          <Descriptions.Item label="通勤时间">
                            {r.duration_minutes != null ? `约${r.duration_minutes}分钟` : '-'}
                          </Descriptions.Item>
                        </Descriptions>

                        {r.reasons.length > 0 && (
                          <div style={{ marginTop: 8 }}>
                            {r.reasons.map((reason, i) => (
                              <Tag key={i} color="green">{reason}</Tag>
                            ))}
                          </div>
                        )}

                        {r.score_breakdown && (
                          <div style={{ marginTop: 8 }}>
                            <Space wrap size={[4, 4]}>
                              {Object.entries(r.score_breakdown).map(([k, v]) => (
                                <Tag key={k} color="geekblue">{k}: {(v * 100).toFixed(0)}%</Tag>
                              ))}
                            </Space>
                          </div>
                        )}

                        {generatedMessages[r.property_id] && (
                          <Card
                            size="small"
                            style={{ marginTop: 12, background: '#f6ffed' }}
                            extra={
                              <Button
                                size="small"
                                icon={<CopyOutlined />}
                                onClick={() => handleCopy(generatedMessages[r.property_id])}
                              >
                                复制
                              </Button>
                            }
                          >
                            <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{generatedMessages[r.property_id]}</p>
                          </Card>
                        )}
                      </Card>
                    ))}
                  </>
                )}
              </>
            ),
          },
          {
            key: 'map',
            label: <span><CompassOutlined /> 地图 ({results.filter(r => r.latitude != null).length})</span>,
            children: (
              <>
                {results.filter(r => r.latitude != null).length === 0 ? (
                  <Card><p style={{ textAlign: 'center', color: '#999' }}>暂无带坐标的匹配房源</p></Card>
                ) : (
                  <PropertyMap
                    markers={results
                      .filter(r => r.latitude != null && r.longitude != null)
                      .map(r => ({
                        id: r.property_id,
                        name: r.name,
                        latitude: r.latitude!,
                        longitude: r.longitude!,
                        monthly_rent: r.monthly_rent,
                        district: r.district,
                        status: r.match_score >= 0.7 ? '高匹配' : r.match_score >= 0.4 ? '中匹配' : '低匹配',
                      })) as PropertyMarker[]}
                    height={500}
                    showStreetView
                  />
                )}
              </>
            ),
          },
          {
            key: 'history',
            label: `推荐历史 (${history.length})`,
            children: (
              <>
                {historyLoading ? (
                  <div style={{ textAlign: 'center', padding: 48 }}><Spin size="large" /></div>
                ) : history.length === 0 ? (
                  <Card><p style={{ textAlign: 'center', color: '#999' }}>暂无推荐记录，选择客户后点击「查看推荐历史」</p></Card>
                ) : (
                  history.map((h) => (
                    <Card
                      key={h.id}
                      style={{ marginBottom: 12 }}
                      title={
                        <Space>
                          <strong>{h.property_name || h.property_code || '-'}</strong>
                          <Tag color={h.sent_to_customer ? 'green' : 'default'}>
                            {h.sent_to_customer ? '已发送' : '未发送'}
                          </Tag>
                        </Space>
                      }
                    >
                      <Descriptions size="small" column={4}>
                        <Descriptions.Item label="月租">{h.monthly_rent?.toLocaleString() || '-'} ฿</Descriptions.Item>
                        <Descriptions.Item label="匹配分数"><Tag color="blue">{(h.match_score * 100).toFixed(0)}%</Tag></Descriptions.Item>
                        <Descriptions.Item label="距离">
                          {h.distance_meters != null
                            ? h.distance_meters < 1000 ? `${h.distance_meters}m` : `${(h.distance_meters / 1000).toFixed(1)}km`
                            : '-'}
                        </Descriptions.Item>
                        <Descriptions.Item label="时间">{new Date(h.created_at).toLocaleDateString()}</Descriptions.Item>
                      </Descriptions>
                      {h.ai_message && (
                        <Card size="small" style={{ marginTop: 12, background: '#f6ffed' }}>
                          <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{h.ai_message}</p>
                        </Card>
                      )}
                    </Card>
                  ))
                )}
              </>
            ),
          },
        ]}
      />
    </div>
  );
}
