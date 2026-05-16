'use client';

import { useEffect, useState } from 'react';
import {
  Card, Col, Progress, Row, Select, Statistic, Table, Tag, Spin, Space,
} from 'antd';
import {
  HomeOutlined, UserOutlined, SendOutlined, RiseOutlined,
  DollarOutlined, PercentageOutlined,
} from '@ant-design/icons';
import { getPropertyStats, getLeadFunnel, getRecommendationStats } from '@/lib/api';
import { useI18n } from '@/i18n/i18n';
import type { PropertyStats, LeadFunnel, RecommendationStats } from '@/types/report';

const stageColors: Record<string, string> = {
  new: 'default', parsed: 'blue', recommended: 'orange',
  contacted: 'cyan', viewing: 'purple', closed: 'green',
};

export default function ReportsPage() {
  const { t } = useI18n();
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [propertyStats, setPropertyStats] = useState<PropertyStats | null>(null);
  const [leadFunnel, setLeadFunnel] = useState<LeadFunnel | null>(null);
  const [recStats, setRecStats] = useState<RecommendationStats | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getPropertyStats(),
      getLeadFunnel(days),
      getRecommendationStats(days),
    ])
      .then(([props, leads, recs]) => {
        setPropertyStats(props);
        setLeadFunnel(leads);
        setRecStats(recs);
      })
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  }

  const maxFunnel = leadFunnel ? Math.max(...leadFunnel.funnel.map((s) => s.count), 1) : 1;

  const topPropColumns = [
    { title: t('reports.rank'), key: 'rank', width: 60, render: (_: unknown, __: unknown, i: number) => i + 1 },
    { title: t('properties.property_code'), dataIndex: 'property_code', key: 'code' },
    { title: t('properties.name'), dataIndex: 'name', key: 'name' },
    { title: t('reports.recommendation_count'), dataIndex: 'recommendation_count', key: 'count', align: 'center' as const },
  ];

  const trendColumns = [
    { title: t('reports.date'), dataIndex: 'date', key: 'date' },
    { title: t('reports.count'), dataIndex: 'count', key: 'count', align: 'center' as const },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 24 }}>
        <h2 style={{ margin: 0 }}>{t('reports.title')}</h2>
        <Select value={days} onChange={setDays}
          options={[
            { label: t('reports.period_7d'), value: 7 },
            { label: t('reports.period_30d'), value: 30 },
            { label: t('reports.period_90d'), value: 90 },
            { label: t('reports.period_365d'), value: 365 },
          ]}
        />
      </Space>

      <Card title={<span><HomeOutlined /> {t('reports.property_stats')}</span>} style={{ marginBottom: 24 }}>
        {propertyStats && (
          <>
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Statistic title={t('reports.total_properties')} value={propertyStats.total} prefix={<HomeOutlined />} />
              </Col>
              <Col span={6}>
                <Statistic title={t('reports.availability_rate')} value={propertyStats.availability_rate} suffix="%" prefix={<PercentageOutlined />} valueStyle={{ color: '#3f8600' }} />
              </Col>
              <Col span={6}>
                <Statistic title={t('reports.rental_rate')} value={propertyStats.rental_rate} suffix="%" prefix={<RiseOutlined />} valueStyle={{ color: '#1677ff' }} />
              </Col>
              <Col span={6}>
                <Statistic title={t('reports.avg_price')} value={propertyStats.price.avg} prefix={<DollarOutlined />} />
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={12}>
                <h4>{t('reports.status_distribution')}</h4>
                {Object.entries(propertyStats.by_status).map(([status, count]) => (
                  <div key={status} style={{ marginBottom: 8 }}>
                    <Tag>{t(`status.${status}`)}</Tag>
                    <Progress
                      percent={Math.round((count / propertyStats.total) * 100)}
                      format={() => t('reports.units', { n: count })}
                      size="small"
                      style={{ width: 200, marginLeft: 8 }}
                    />
                  </div>
                ))}
              </Col>
              <Col span={12}>
                <h4>{t('reports.bedroom_distribution')}</h4>
                {Object.entries(propertyStats.bedroom_distribution).map(([bed, count]) => (
                  <div key={bed} style={{ marginBottom: 8 }}>
                    <Tag>{bed === '0' ? 'Studio' : t('properties.bedroom_unit', { n: parseInt(bed) })}</Tag>
                    <Progress
                      percent={Math.round((count / propertyStats.total) * 100)}
                      format={() => t('reports.units', { n: count })}
                      size="small"
                      style={{ width: 200, marginLeft: 8 }}
                    />
                  </div>
                ))}
              </Col>
            </Row>
            <Row style={{ marginTop: 16 }}>
              <Col span={24}>
                <p style={{ color: '#888' }}>
                  {t('reports.price_range', { min: propertyStats.price.min?.toLocaleString() || '-', max: propertyStats.price.max?.toLocaleString() || '-', avg: propertyStats.price.avg?.toLocaleString() || '-' })}
                </p>
              </Col>
            </Row>
          </>
        )}
      </Card>

      <Card title={<span><UserOutlined /> {t('reports.lead_funnel', { days })}</span>} style={{ marginBottom: 24 }}>
        {leadFunnel && (
          <>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={6}>
                <Statistic title={t('reports.total_leads')} value={leadFunnel.total_leads} />
              </Col>
            </Row>
            {leadFunnel.funnel.map((stage) => (
              <div key={stage.stage} style={{ marginBottom: 12 }}>
                <Tag color={stageColors[stage.stage] || 'default'}>{t(`status.${stage.stage}`)}</Tag>
                <Progress
                  percent={Math.round((stage.count / maxFunnel) * 100)}
                  format={() => `${stage.count}`}
                  style={{ width: 300, marginLeft: 8 }}
                />
              </div>
            ))}
            <h4 style={{ marginTop: 16 }}>{t('reports.source_distribution')}</h4>
            {Object.entries(leadFunnel.by_source).map(([source, count]) => (
              <Tag key={source} style={{ margin: 4 }}>
                {source}: {count}
              </Tag>
            ))}
          </>
        )}
      </Card>

      <Card title={<span><SendOutlined /> {t('reports.recommendation_stats', { days })}</span>} style={{ marginBottom: 24 }}>
        {recStats && (
          <>
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={6}>
                <Statistic title={t('reports.total_recommendations')} value={recStats.total_recommendations} prefix={<SendOutlined />} />
              </Col>
              <Col span={6}>
                <Statistic title={t('reports.sent_to_customer')} value={recStats.sent_to_customer} suffix={`/ ${recStats.total_recommendations}`} valueStyle={{ color: '#3f8600' }} />
              </Col>
              <Col span={6}>
                <Statistic title={t('reports.send_rate')} value={recStats.send_rate} suffix="%" />
              </Col>
              <Col span={6}>
                <Statistic title={t('reports.avg_match_score')} value={recStats.average_match_score} precision={2} />
              </Col>
            </Row>
            <Row gutter={24}>
              <Col span={12}>
                <h4>{t('reports.top_properties')}</h4>
                <Table
                  dataSource={recStats.top_properties as unknown as Record<string, unknown>[]}
                  columns={topPropColumns}
                  rowKey="property_code"
                  size="small"
                  pagination={false}
                  style={{ marginTop: 8 }}
                />
              </Col>
              <Col span={12}>
                <h4>{t('reports.daily_trend')}</h4>
                <Table
                  dataSource={recStats.daily_trend as unknown as Record<string, unknown>[]}
                  columns={trendColumns}
                  rowKey="date"
                  size="small"
                  pagination={false}
                  style={{ marginTop: 8 }}
                  scroll={{ y: 360 }}
                />
              </Col>
            </Row>
          </>
        )}
      </Card>
    </div>
  );
}
