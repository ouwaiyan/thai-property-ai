'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, Form, Input, InputNumber, Select, Switch, Button, App, Space, Spin, Upload } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { getProperty, updateProperty, uploadPropertyImages, deletePropertyImage } from '@/lib/api';
import MapPicker from '@/components/MapPicker';
import { useI18n } from '@/i18n/i18n';
import type { PropertyOut } from '@/types/property';

export default function EditPropertyPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { message } = App.useApp();
  const { t } = useI18n();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [property, setProperty] = useState<PropertyOut | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    getProperty(id).then((p) => {
      setProperty(p);
      form.setFieldsValue({
        ...p,
        tags: p.tags?.join(', ') || '',
      });
    }).finally(() => setFetching(false));
  }, [id, form]);

  const onFinish = async (values: Record<string, unknown>) => {
    setLoading(true);
    try {
      const data = {
        ...values,
        tags: values.tags ? (values.tags as string).split(',').map((t: string) => t.trim()) : [],
      };
      await updateProperty(id, data);
      message.success(t('properties.update_success'));
      router.push(`/dashboard/properties/${id}`);
    } catch {
      message.error(t('properties.update_failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      await uploadPropertyImages(id, [file]);
      message.success(t('properties.upload_success'));
      const p = await getProperty(id);
      setProperty(p);
    } catch {
      message.error(t('properties.upload_failed'));
    } finally {
      setUploading(false);
    }
    return false;
  };

  if (fetching) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const existingImages = property?.images || [];
  const backendBase = 'http://localhost:8000/static';

  return (
    <Card title={`${t('properties.edit')}: ${property?.name}`}>
      <Form form={form} layout="vertical" onFinish={onFinish} style={{ maxWidth: 800 }}>
        <Form.Item name="property_code" label={t('properties.property_code')} rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="name" label={t('properties.name')} rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="building_name" label={t('properties.building_name')}><Input /></Form.Item>
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
            <InputNumber step={0.0001} style={{ width: 130 }} disabled />
          </Form.Item>
          <Form.Item name="longitude" label={t('properties.longitude')} rules={[{ required: true }]}>
            <InputNumber step={0.0001} style={{ width: 130 }} disabled />
          </Form.Item>
          <Form.Item name="district" label={t('properties.district')} rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="area" label={t('properties.area')} rules={[{ required: true }]}><Input /></Form.Item>
        </Space>
        <Space size="large">
          <Form.Item name="nearest_bts" label={t('properties.nearest_bts')}><Input /></Form.Item>
          <Form.Item name="nearest_mrt" label={t('properties.nearest_mrt')}><Input /></Form.Item>
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
          <Form.Item name="deposit_months" label={t('properties.deposit_months')}><InputNumber min={1} max={12} /></Form.Item>
          <Form.Item name="status" label={t('common.status')}>
            <Select options={[
              { label: t('properties.status_available'), value: 'available' },
              { label: t('properties.status_pending'), value: 'pending' },
              { label: t('properties.status_rented'), value: 'rented' },
              { label: t('properties.status_offline'), value: 'offline' },
            ]} />
          </Form.Item>
          <Form.Item name="pet_allowed" label={t('properties.pet_allowed')} valuePropName="checked"><Switch /></Form.Item>
        </Space>
        <Space size="large">
          <Form.Item name="contact_person" label={t('properties.contact_person')} rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="contact_phone" label={t('properties.contact_phone')} rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="contact_line" label={t('properties.contact_line')}><Input /></Form.Item>
        </Space>
        <Form.Item name="description" label={t('properties.description')}><Input.TextArea rows={3} /></Form.Item>
        <Form.Item name="tags" label={t('properties.tags_comma_hint')}><Input /></Form.Item>

        <Form.Item label={t('properties.images')}>
          {existingImages.map((img) => (
            <div key={img.id} style={{ display: 'inline-block', margin: 4, position: 'relative' }}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`${backendBase}/properties/${id}/${img.image_url.split('/').pop()}`}
                alt="property"
                style={{ width: 100, height: 100, objectFit: 'cover', borderRadius: 4 }}
                onError={(e) => { (e.target as HTMLImageElement).src = `http://localhost:8000/static${img.image_url}`; }}
              />
              <Button
                size="small"
                danger
                style={{ position: 'absolute', top: 0, right: 0 }}
                onClick={() => deletePropertyImage(img.id).then(() => {
                  message.success(t('properties.delete_success'));
                  getProperty(id).then(setProperty);
                })}
              >
                X
              </Button>
            </div>
          ))}
          <Upload beforeUpload={(f) => { handleUpload(f); return false; }} showUploadList={false}>
            <Button icon={<UploadOutlined />} loading={uploading}>{t('properties.upload_image')}</Button>
          </Upload>
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>{t('common.save')}</Button>
            <Button onClick={() => router.back()}>{t('common.cancel')}</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
}
