'use client';

import { useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProTable } from '@ant-design/pro-components';
import type { ProColumns, ActionType } from '@ant-design/pro-components';
import { Button, Tag, Space, App, Select, Input } from 'antd';
import { PlusOutlined, EyeOutlined, EditOutlined, DeleteOutlined, DownloadOutlined } from '@ant-design/icons';
import { getProperties, deleteProperty, computeRouteMatrix, exportPropertiesCSV, bulkUpdateProperties } from '@/lib/api';
import { useAuthStore } from '@/stores/authStore';
import { canEditProperty, canDeleteProperty } from '@/lib/permissions';
import PermissionButton from '@/components/PermissionButton';
import NearbySearch from '@/components/NearbySearch';
import dynamic from 'next/dynamic';
const PropertyMap = dynamic(() => import('@/components/PropertyMap'), { ssr: false });
import { useI18n } from '@/i18n/i18n';
import type { PropertyListOut } from '@/types/property';
import type { UserRole } from '@/types/auth';
import type { TravelMode, RouteMatrixItem } from '@/types/transit';

const statusColor: Record<string, string> = {
  available: 'green',
  pending: 'orange',
  rented: 'blue',
  offline: 'default',
};

export default function PropertiesPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const actionRef = useRef<ActionType>();
  const { message, modal } = App.useApp();
  const { t } = useI18n();
  const [geoParams, setGeoParams] = useState<{ lat: number; lng: number; radius: number; travelMode: TravelMode } | null>(null);
  const [routeData, setRouteData] = useState<Map<string, RouteMatrixItem>>(new Map());
  const [selectedRows, setSelectedRows] = useState<PropertyListOut[]>([]);
  const [batchStatus, setBatchStatus] = useState<string | undefined>();
  const [batchTags, setBatchTags] = useState<string>('');
  const [exporting, setExporting] = useState(false);

  const handleDelete = (record: PropertyListOut) => {
    modal.confirm({
      title: t('properties.confirm_delete_title'),
      content: t('properties.confirm_delete_content', { name: record.name }),
      okText: t('properties.confirm_delete_ok'),
      okType: 'danger',
      cancelText: t('common.cancel'),
      onOk: async () => {
        await deleteProperty(record.id);
        message.success(t('properties.delete_success'));
        actionRef.current?.reload();
      },
    });
  };

  const handleNearbySearch = (lat: number, lng: number, radius: number, travelMode: TravelMode) => {
    setGeoParams({ lat, lng, radius, travelMode });
    setRouteData(new Map());
    actionRef.current?.reload();
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await exportPropertiesCSV();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'properties_export.csv';
      a.click();
      window.URL.revokeObjectURL(url);
      message.success(t('properties.export_success'));
    } catch {
      message.error(t('properties.export_failed'));
    } finally {
      setExporting(false);
    }
  };

  const handleBatchUpdate = async () => {
    if (selectedRows.length === 0) return;
    const ids = selectedRows.map((r) => r.id);
    try {
      await bulkUpdateProperties({
        property_ids: ids,
        status: batchStatus || undefined,
        tags: batchTags ? batchTags.split(',').map((t) => t.trim()).filter(Boolean) : undefined,
      });
      message.success(t('properties.bulk_update_success', { n: ids.length }));
      setSelectedRows([]);
      setBatchStatus(undefined);
      setBatchTags('');
      actionRef.current?.reload();
    } catch {
      message.error(t('properties.bulk_update_failed'));
    }
  };

  const columns: ProColumns<PropertyListOut>[] = [
    { title: t('properties.code'), dataIndex: 'property_code', key: 'property_code', width: 120 },
    { title: t('properties.name'), dataIndex: 'name', key: 'name', width: 200 },
    { title: t('properties.district'), dataIndex: 'district', key: 'district', width: 100, search: true },
    { title: t('properties.layout'), key: 'layout', width: 100, search: false,
      render: (_, r) => `${r.bedroom_count}${t('properties.bedroom_unit', { n: r.bedroom_count })}${r.bathroom_count}${t('properties.bathroom_unit', { n: r.bathroom_count })}`,
    },
    { title: t('properties.size_sqm'), dataIndex: 'size_sqm', key: 'size_sqm', width: 80, search: false },
    { title: t('properties.monthly_rent'), dataIndex: 'monthly_rent', key: 'monthly_rent', width: 100, search: false,
      render: (_, r) => r.monthly_rent.toLocaleString(),
    },
    ...(geoParams ? [
      {
        title: t('properties.straight_distance'), key: 'straight_dist', width: 100, search: false,
        render: (_: unknown, r: PropertyListOut) =>
          r.distance_meters != null ? `${r.distance_meters < 1000 ? `${r.distance_meters}m` : `${(r.distance_meters / 1000).toFixed(1)}km`}` : '-',
      },
      {
        title: t('properties.route_time', { mode: t(`transit.${geoParams.travelMode}`) }), key: 'route_time', width: 100, search: false,
        render: (_: unknown, r: PropertyListOut) => {
          const rd = routeData.get(r.id);
          if (!rd) return '-';
          const mins = Math.round(rd.duration_seconds / 60);
          return mins < 60 ? `${mins}${t('common.time')}` : `${Math.floor(mins / 60)}${t('common.time')}${mins % 60}${t('common.time')}`;
        },
      },
      {
        title: t('properties.route_distance'), key: 'route_dist', width: 100, search: false,
        render: (_: unknown, r: PropertyListOut) => {
          const rd = routeData.get(r.id);
          if (!rd) return '-';
          const m = rd.distance_meters;
          return m < 1000 ? `${m}m` : `${(m / 1000).toFixed(1)}km`;
        },
      },
    ] : []),
    { title: t('common.status'), dataIndex: 'status', key: 'status', width: 80,
      valueEnum: {
        available: { text: t('status.available') },
        pending: { text: t('status.pending') },
        rented: { text: t('status.rented') },
        offline: { text: t('status.offline') },
      },
      render: (_, r) => <Tag color={statusColor[r.status] || 'default'}>{t(`status.${r.status}`)}</Tag>,
    },
    { title: t('properties.tags'), dataIndex: 'tags', key: 'tags', width: 200, search: false,
      render: (_, r) => r.tags?.slice(0, 3).map((tag) => <Tag key={tag}>{tag}</Tag>),
    },
    { title: t('common.created_at'), dataIndex: 'created_at', key: 'created_at', width: 150, search: false,
      render: (_, r) => new Date(r.created_at).toLocaleDateString(),
    },
    { title: t('common.actions'), key: 'action', width: 180, search: false,
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => router.push(`/dashboard/properties/${record.id}`)}>
            {t('common.view')}
          </Button>
          {canEditProperty(user?.role || null, record.created_by, user?.id || '') && (
            <Button size="small" icon={<EditOutlined />} onClick={() => router.push(`/dashboard/properties/${record.id}/edit`)}>
              {t('common.edit')}
            </Button>
          )}
          {canDeleteProperty(user?.role as UserRole | null) && (
            <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record)}>
              {t('common.delete')}
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const [markers, setMarkers] = useState<Array<{
    id: string;
    name: string;
    latitude: number;
    longitude: number;
    monthly_rent: number;
    district: string;
  }>>([]);

  return (
    <>
      <NearbySearch onSearch={handleNearbySearch} />
      <ProTable<PropertyListOut>
        columns={columns}
        actionRef={actionRef}
        request={async (params) => {
          const { current, pageSize, ...filters } = params;
          const res = await getProperties({
            ...filters,
            page: current,
            page_size: pageSize,
            ...(geoParams ? { lat: geoParams.lat, lng: geoParams.lng, radius_meters: geoParams.radius } : {}),
            ...(geoParams ? { sort_by: 'distance', sort_order: 'asc' } : {}),
          });
          const items = res.items as PropertyListOut[];

          if (geoParams && items.length > 0) {
            const idsWithCoords = items
              .filter((p) => p.latitude != null && p.longitude != null)
              .map((p) => p.id)
              .slice(0, 50);

            if (idsWithCoords.length > 0) {
              try {
                const matrix = await computeRouteMatrix({
                  origin_lat: geoParams.lat,
                  origin_lng: geoParams.lng,
                  property_ids: idsWithCoords,
                  travel_mode: geoParams.travelMode,
                });
                const routeMap = new Map<string, RouteMatrixItem>();
                matrix.results.forEach((r) => routeMap.set(r.property_id, r));
                setRouteData(routeMap);
              } catch {
                setRouteData(new Map());
              }
            }

            setMarkers(
              items
                .filter((p) => p.latitude != null && p.longitude != null)
                .map((p) => ({
                  id: p.id,
                  name: p.name,
                  latitude: p.latitude!,
                  longitude: p.longitude!,
                  monthly_rent: p.monthly_rent,
                  district: p.district,
                })),
            );
          }

          return { data: items, total: res.total, success: true };
        }}
        rowKey="id"
        search={{ labelWidth: 'auto' }}
        pagination={{ pageSize: 20 }}
        headerTitle={
          selectedRows.length > 0
            ? t('properties.selected_count', { n: selectedRows.length })
            : t('properties.title')
        }
        rowSelection={{
          selectedRowKeys: selectedRows.map((r) => r.id),
          onChange: (_keys, rows) => setSelectedRows(rows),
        }}
        toolbar={{
          actions: [
            <PermissionButton key="create" requiredRole="Agent">
              <Button type="primary" icon={<PlusOutlined />} onClick={() => router.push('/dashboard/properties/new')}>
                {t('properties.create')}
              </Button>
            </PermissionButton>,
            <Button key="export" icon={<DownloadOutlined />} onClick={handleExport} loading={exporting}>
              {t('properties.export_csv')}
            </Button>,
          ],
        }}
        tableAlertOptionRender={({ selectedRowKeys, onCleanSelected }) => (
          <Space size={16}>
            <Select
              placeholder={t('properties.batch_status')}
              value={batchStatus}
              onChange={setBatchStatus}
              allowClear
              style={{ width: 120 }}
              options={[
                { label: t('status.available'), value: 'available' },
                { label: t('status.pending'), value: 'pending' },
                { label: t('status.rented'), value: 'rented' },
                { label: t('status.offline'), value: 'offline' },
              ]}
            />
            <Input
              placeholder={t('properties.batch_tags_placeholder')}
              value={batchTags}
              onChange={(e) => setBatchTags(e.target.value)}
              style={{ width: 180 }}
            />
            <Button type="primary" onClick={handleBatchUpdate}>
              {t('properties.batch_apply', { n: selectedRowKeys.length })}
            </Button>
            <a onClick={() => { onCleanSelected(); setSelectedRows([]); }}>
              {t('common.cancel')}
            </a>
          </Space>
        )}
      />
      {markers.length > 0 && <PropertyMap markers={markers} />}
    </>
  );
}
