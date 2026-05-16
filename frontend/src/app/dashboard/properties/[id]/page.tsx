'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, Descriptions, Tag, Button, Space, Spin, Image } from 'antd';
import { EditOutlined, ArrowLeftOutlined, EnvironmentOutlined } from '@ant-design/icons';
import StreetViewModal from '@/components/StreetViewModal';
import { getProperty } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import { canEditProperty } from '@/lib/permissions';
import PropertyMap from '@/components/PropertyMap';
import { useI18n } from '@/i18n/i18n';
import type { PropertyOut } from '@/types/property';

const statusColor: Record<string, string> = { available: 'green', pending: 'orange', rented: 'blue', offline: 'default' };

export default function PropertyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const { t } = useI18n();
  const [property, setProperty] = useState<PropertyOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [svOpen, setSvOpen] = useState(false);

  useEffect(() => {
    getProperty(id).then(setProperty).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  if (!property) return <Card title={t('properties.not_found')}><Button onClick={() => router.back()}>{t('common.back')}</Button></Card>;

  const coverImage = property.images?.find((i) => i.is_cover)?.image_url ?? property.images?.[0]?.image_url;

  return (
    <Card
      title={property.name}
      extra={
        <Space>
          {canEditProperty(user?.role || null, property.created_by, user?.id || '') && (
            <Button icon={<EditOutlined />} onClick={() => router.push(`/dashboard/properties/${id}/edit`)}>
              {t('common.edit')}
            </Button>
          )}
          <Button icon={<ArrowLeftOutlined />} onClick={() => router.back()}>{t('common.back')}</Button>
        </Space>
      }
    >
      {coverImage && (
        <Image src={coverImage} alt={property.name} style={{ maxHeight: 300, objectFit: 'cover', marginBottom: 16 }} />
      )}
      {property.latitude != null && property.longitude != null && (
        <>
          <div style={{ position: 'relative' }}>
            <PropertyMap
              markers={[{
                id: property.id,
                name: property.name,
                latitude: property.latitude,
                longitude: property.longitude,
                monthly_rent: property.monthly_rent,
                district: property.district,
                nearest_bts: property.nearest_bts,
                nearest_mrt: property.nearest_mrt,
              }]}
              height={300}
            />
            <Button
              size="small"
              icon={<EnvironmentOutlined />}
              style={{ position: 'absolute', top: 8, right: 8, zIndex: 1000 }}
              onClick={() => setSvOpen(true)}
            >
              {t('common.street_view')}
            </Button>
          </div>
          <StreetViewModal
            open={svOpen}
            lat={property.latitude}
            lng={property.longitude}
            title={property.name}
            onClose={() => setSvOpen(false)}
          />
        </>
      )}
      <Descriptions bordered column={2} style={{ marginTop: 16 }}>
        <Descriptions.Item label={t('properties.code')}>{property.property_code}</Descriptions.Item>
        <Descriptions.Item label={t('properties.building_name')}>{property.building_name}</Descriptions.Item>
        <Descriptions.Item label={t('properties.address')}>{property.address}</Descriptions.Item>
        <Descriptions.Item label={t('common.status')}><Tag color={statusColor[property.status]}>{t(`status.${property.status}`)}</Tag></Descriptions.Item>
        <Descriptions.Item label={t('properties.district')}>{property.district} / {property.area}</Descriptions.Item>
        <Descriptions.Item label={t('properties.layout')}>{property.bedroom_count}{t('properties.bedroom_unit', { n: property.bedroom_count })} {property.bathroom_count}{t('properties.bathroom_unit', { n: property.bathroom_count })}</Descriptions.Item>
        <Descriptions.Item label={t('properties.size_sqm')}>{property.size_sqm} m²</Descriptions.Item>
        <Descriptions.Item label={t('properties.monthly_rent')}>฿{property.monthly_rent.toLocaleString()}</Descriptions.Item>
        <Descriptions.Item label={t('properties.nearest_bts')}>{property.nearest_bts || '-'}</Descriptions.Item>
        <Descriptions.Item label={t('properties.nearest_mrt')}>{property.nearest_mrt || '-'}</Descriptions.Item>
        <Descriptions.Item label={t('properties.pet_allowed')}>{property.pet_allowed ? t('properties.pet_yes') : t('properties.pet_no')}</Descriptions.Item>
        <Descriptions.Item label={t('properties.deposit_months')}>{property.deposit_months ? t('properties.months_unit', { n: property.deposit_months }) : '-'}</Descriptions.Item>
        <Descriptions.Item label={t('properties.contact_person')}>{property.contact_person}</Descriptions.Item>
        <Descriptions.Item label={t('properties.contact_phone')}>{property.contact_phone}</Descriptions.Item>
        <Descriptions.Item label={t('properties.contact_line')}>{property.contact_line || '-'}</Descriptions.Item>
        <Descriptions.Item label={t('properties.description')} span={2}>{property.description}</Descriptions.Item>
        <Descriptions.Item label={t('properties.tags')} span={2}>
          {property.tags?.map((tag) => <Tag key={tag}>{tag}</Tag>)}
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
}
