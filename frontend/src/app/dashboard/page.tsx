'use client';

import { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic } from 'antd';
import { HomeOutlined, UserOutlined, DollarOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { getProperties } from '@/lib/api';
import PropertyMap from '@/components/PropertyMap';
import type { PropertyMarker } from '@/components/PropertyMap';
import { useI18n } from '@/i18n/i18n';
import type { PropertyListOut } from '@/types/property';

export default function DashboardPage() {
  const { t } = useI18n();
  const [stats, setStats] = useState({ total: 0, available: 0, pending: 0 });
  const [markers, setMarkers] = useState<PropertyMarker[]>([]);

  useEffect(() => {
    getProperties({ page_size: 1 }).then((r) => setStats((s) => ({ ...s, total: r.total })));
    getProperties({ page_size: 1, status: 'available' }).then((r) => setStats((s) => ({ ...s, available: r.total })));
    getProperties({ page_size: 1, status: 'pending' }).then((r) => setStats((s) => ({ ...s, pending: r.total })));
    getProperties({ page_size: 100 }).then((r) => {
      const items = r.items as PropertyListOut[];
      setMarkers(
        items
          .filter((p) => p.latitude != null && p.longitude != null)
          .map((p) => ({
            id: p.id, name: p.name, latitude: p.latitude!, longitude: p.longitude!,
            monthly_rent: p.monthly_rent, district: p.district,
            nearest_bts: p.nearest_bts, nearest_mrt: p.nearest_mrt,
          })),
      );
    });
  }, []);

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>{t('dashboard.title')}</h2>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic title={t('dashboard.total_properties')} value={stats.total} prefix={<HomeOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title={t('dashboard.available_properties')} value={stats.available} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title={t('dashboard.pending_properties')} value={stats.pending} prefix={<UserOutlined />} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title={t('common.loading')} value={stats.total > 0 ? Math.round(stats.available / stats.total * 100) + '%' : '-'} prefix={<DollarOutlined />} />
          </Card>
        </Col>
      </Row>
      {markers.length > 0 && (
        <Card title={t('dashboard.property_distribution')} style={{ marginTop: 24 }}>
          <PropertyMap markers={markers} height={400} />
        </Card>
      )}
    </div>
  );
}
