'use client';

import { useEffect, useRef } from 'react';
import { Modal } from 'antd';
import { EnvironmentOutlined } from '@ant-design/icons';
import { importLibrary } from '@/lib/googleMaps';

interface StreetViewModalProps {
  open: boolean;
  lat: number;
  lng: number;
  title?: string;
  onClose: () => void;
}

export default function StreetViewModal({ open, lat, lng, title, onClose }: StreetViewModalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const panoramaRef = useRef<google.maps.StreetViewPanorama | null>(null);

  useEffect(() => {
    if (!open || !containerRef.current) return;

    let cancelled = false;

    async function loadStreetView() {
      try {
        await importLibrary('maps');
        await importLibrary('streetView');
      } catch {
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML =
            '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999">Google Maps 加载失败</div>';
        }
        return;
      }

      if (cancelled || !containerRef.current) return;

      const sv = new google.maps.StreetViewService();
      sv.getPanorama(
        { location: { lat, lng }, radius: 50, source: google.maps.StreetViewSource.OUTDOOR },
        (data, status) => {
          if (cancelled || !containerRef.current) return;
          if (status === google.maps.StreetViewStatus.OK && data?.location?.pano) {
            panoramaRef.current = new google.maps.StreetViewPanorama(containerRef.current!, {
              position: data.location.latLng,
              pov: { heading: 0, pitch: 0 },
              zoom: 1,
              addressControl: false,
              linksControl: true,
              panControl: true,
            });
          } else {
            containerRef.current.innerHTML =
              `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999">
                 <span>${title ? `"${title}" ` : ''}附近无街景</span>
               </div>`;
          }
        },
      );
    }

    loadStreetView();

    return () => {
      cancelled = true;
      if (panoramaRef.current) {
        panoramaRef.current.setVisible(false);
        panoramaRef.current = null;
      }
    };
  }, [open, lat, lng, title]);

  return (
    <Modal
      title={<span><EnvironmentOutlined /> {title || '街景'}</span>}
      open={open}
      onCancel={onClose}
      footer={null}
      width={800}
      destroyOnClose
    >
      <div ref={containerRef} style={{ height: 500, borderRadius: 8, background: '#f0f0f0' }} />
    </Modal>
  );
}
