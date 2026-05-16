'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, Form, Input, InputNumber, Select, Switch, Button, App, Space } from 'antd';
import { createProperty } from '@/lib/api';
import MapPicker from '@/components/MapPicker';
import { useI18n } from '@/i18n/i18n';
import type { PropertyCreate } from '@/types/property';

export default function NewPropertyPage() {
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const { t } = useI18n();

  const onFinish = async (values: Record<string, unknown>) => {
    setLoading(true);
    try {
      const data: PropertyCreate = {
        property_code: values.property_code as string,
        name: values.name as string,
        building_name: values.building_name as string,
        address: values.address as string,
        latitude: values.latitude as number,
        longitude: values.longitude as number,
        district: values.district as string,
        area: values.area as string,
        nearest_bts: values.nearest_bts as string,
        nearest_mrt: values.nearest_mrt as string,
        bedroom_count: values.bedroom_count as number,
        bathroom_count: values.bathroom_count as number,
        size_sqm: values.size_sqm as number,
        monthly_rent: values.monthly_rent as number,
        deposit_months: values.deposit_months as number | undefined,
        status: values.status as string,
        available_date: values.available_date as string,
        pet_allowed: values.pet_allowed as boolean,
        contact_person: values.contact_person as string,
        contact_line: values.contact_line as string,
        contact_phone: values.contact_phone as string,
        description: values.description as string,
        tags: values.tags ? (values.tags as string).split(',').map((t: string) => t.trim()) : [],
      };
      await createProperty(data);
      message.success(t('properties.create_success'));
      router.push('/dashboard/properties');
    } catch {
      message.error(t('properties.create_failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title={t('properties.create')}>
      <Form form={form} layout="vertical" onFinish={onFinish} style={{ maxWidth: 800 }}>
        <Form.Item name="property_code" label={t('properties.property_code')} rules={[{ required: true }]}>
          <Input placeholder="BKK-000007" />
        </Form.Item>
        <Form.Item name="name" label={t('properties.name')} rules={[{ required: true }]}>
          <Input placeholder="Ashton Asoke" />
        </Form.Item>
        <Form.Item name="building_name" label={t('properties.building_name')}>
          <Input />
        </Form.Item>
        <Form.Item name="address" label={t('properties.address')} rules={[{ required: true }]}>
          <Input.TextArea rows={2} />
        </Form.Item>

        <Form.Item label={t('properties.map_pick_location')} style={{ marginBottom: 8 }}>
          <MapPicker
            lat={form.getFieldValue('latitude')}
            lng={form.getFieldValue('longitude')}
            onChange={(lat, lng) => {
              form.setFieldsValue({ latitude: Math.round(lat * 10000) / 10000, longitude: Math.round(lng * 10000) / 10000 });
            }}
          />
        </Form.Item>

        <Space size="large">
          <Form.Item name="latitude" label={t('properties.latitude')} rules={[{ required: true }]}>
            <InputNumber step={0.0001} min={5} max={21} placeholder="13.7" style={{ width: 130 }} disabled />
          </Form.Item>
          <Form.Item name="longitude" label={t('properties.longitude')} rules={[{ required: true }]}>
            <InputNumber step={0.0001} min={97} max={106} placeholder="100.5" style={{ width: 130 }} disabled />
          </Form.Item>
          <Form.Item name="district" label={t('properties.district')} rules={[{ required: true }]}>
            <Input placeholder="Wattana" />
          </Form.Item>
          <Form.Item name="area" label={t('properties.area')} rules={[{ required: true }]}>
            <Input placeholder="Asoke" />
          </Form.Item>
        </Space>
        <Space size="large">
          <Form.Item name="nearest_bts" label={t('properties.nearest_bts')}>
            <Input placeholder="Asok" />
          </Form.Item>
          <Form.Item name="nearest_mrt" label={t('properties.nearest_mrt')}>
            <Input placeholder="Sukhumvit" />
          </Form.Item>
          <Form.Item name="bedroom_count" label={t('properties.bedroom_count')} rules={[{ required: true }]}>
            <InputNumber min={0} max={10} />
          </Form.Item>
          <Form.Item name="bathroom_count" label={t('properties.bathroom_count')} rules={[{ required: true }]}>
            <InputNumber min={0} max={10} />
          </Form.Item>
          <Form.Item name="size_sqm" label={t('properties.size_sqm')} rules={[{ required: true }]}>
            <InputNumber min={0} />
          </Form.Item>
        </Space>
        <Space size="large">
          <Form.Item name="monthly_rent" label={t('properties.monthly_rent')} rules={[{ required: true }]}>
            <InputNumber min={0} step={1000} style={{ width: 150 }} />
          </Form.Item>
          <Form.Item name="deposit_months" label={t('properties.deposit_months')}>
            <InputNumber min={1} max={12} />
          </Form.Item>
          <Form.Item name="status" label={t('common.status')} initialValue="available">
            <Select
              options={[
                { label: t('properties.status_available'), value: 'available' },
                { label: t('properties.status_pending'), value: 'pending' },
                { label: t('properties.status_rented'), value: 'rented' },
                { label: t('properties.status_offline'), value: 'offline' },
              ]}
            />
          </Form.Item>
          <Form.Item name="pet_allowed" label={t('properties.pet_allowed')} valuePropName="checked">
            <Switch />
          </Form.Item>
        </Space>
        <Space size="large">
          <Form.Item name="contact_person" label={t('properties.contact_person')} rules={[{ required: true }]}>
            <Input placeholder="Khun Somsak" />
          </Form.Item>
          <Form.Item name="contact_phone" label={t('properties.contact_phone')} rules={[{ required: true }]}>
            <Input placeholder="081-234-5678" />
          </Form.Item>
          <Form.Item name="contact_line" label={t('properties.contact_line')}>
            <Input placeholder="@somsak" />
          </Form.Item>
        </Space>
        <Form.Item name="description" label={t('properties.description')}>
          <Input.TextArea rows={3} />
        </Form.Item>
        <Form.Item name="tags" label={t('properties.tags_comma_hint')}>
          <Input placeholder="near_bts, pet_friendly, pool" />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>{t('common.create')}</Button>
            <Button onClick={() => router.back()}>{t('common.cancel')}</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
}
