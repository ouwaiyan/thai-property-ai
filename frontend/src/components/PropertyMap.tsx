'use client';

import { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Button, Space } from 'antd';
import { EnvironmentOutlined, CompassOutlined } from '@ant-design/icons';

import 'leaflet/dist/leaflet.css';
import StreetViewModal from './StreetViewModal';

delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export interface PropertyMarker {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  monthly_rent?: number;
  status?: string;
  district?: string;
  nearest_bts?: string | null;
  nearest_mrt?: string | null;
}

function FitBounds({ markers }: { markers: PropertyMarker[] }) {
  const map = useMap();
  useEffect(() => {
    if (markers.length === 0) return;
    if (markers.length === 1) {
      map.setView([markers[0].latitude, markers[0].longitude], 15);
    } else {
      const bounds = L.latLngBounds(
        markers.map((m) => [m.latitude, m.longitude] as [number, number]),
      );
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [map, markers]);
  return null;
}

// Square-cluster markers when many markers are nearby
function clusterMarkers(markers: PropertyMarker[], gridSize: number = 0.005): Array<PropertyMarker | (PropertyMarker[] & { _cluster: true; center_lat: number; center_lng: number })> {
  if (markers.length <= 3) return markers;

  const grid: Record<string, PropertyMarker[]> = {};
  for (const m of markers) {
    const key = `${Math.round(m.latitude / gridSize)},${Math.round(m.longitude / gridSize)}`;
    if (!grid[key]) grid[key] = [];
    grid[key].push(m);
  }

  const result: Array<PropertyMarker | (PropertyMarker[] & { _cluster: true; center_lat: number; center_lng: number })> = [];
  for (const cell of Object.values(grid)) {
    if (cell.length === 1) {
      result.push(cell[0]);
    } else {
      const avgLat = cell.reduce((s, m) => s + m.latitude, 0) / cell.length;
      const avgLng = cell.reduce((s, m) => s + m.longitude, 0) / cell.length;
      const cluster = Object.assign(cell, { _cluster: true as const, center_lat: avgLat, center_lng: avgLng });
      result.push(cluster);
    }
  }
  return result;
}

interface PropertyMapProps {
  markers: PropertyMarker[];
  height?: number;
  showStreetView?: boolean;
}

export default function PropertyMap({ markers, height = 400, showStreetView = true }: PropertyMapProps) {
  const [svOpen, setSvOpen] = useState(false);
  const [svLat, setSvLat] = useState(13.7563);
  const [svLng, setSvLng] = useState(100.5018);
  const [svTitle, setSvTitle] = useState('');

  const center = useMemo(() => {
    if (markers.length === 1) return [markers[0].latitude, markers[0].longitude] as [number, number];
    return [13.7563, 100.5018] as [number, number];
  }, [markers]);

  const clustered = useMemo(() => clusterMarkers(markers), [markers]);

  const openStreetView = (m: PropertyMarker) => {
    setSvLat(m.latitude);
    setSvLng(m.longitude);
    setSvTitle(m.name);
    setSvOpen(true);
  };

  const openDirections = (m: PropertyMarker) => {
    window.open(
      `https://www.google.com/maps/dir/?api=1&destination=${m.latitude},${m.longitude}`,
      '_blank',
    );
  };

  return (
    <>
      <div style={{ height, borderRadius: 8, overflow: 'hidden' }}>
        <MapContainer
          center={center}
          zoom={12}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <FitBounds markers={markers} />
          {clustered.map((item, idx) => {
            if ('_cluster' in item && item._cluster) {
              const cluster = item as PropertyMarker[] & { _cluster: true; center_lat: number; center_lng: number };
              const countIcon = L.divIcon({
                className: 'marker-cluster',
                html: `<div style="background:#1890ff;color:white;border-radius:50%;width:40px;height:40px;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:14px;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3)">${cluster.length}</div>`,
                iconSize: [40, 40],
                iconAnchor: [20, 20],
              });
              return (
                <Marker key={`cluster-${idx}`} position={[cluster.center_lat, cluster.center_lng]} icon={countIcon}>
                  <Popup>
                    <div style={{ minWidth: 180, maxHeight: 200, overflowY: 'auto' }}>
                      <strong>{cluster.length} 套房源</strong>
                      {cluster.map((m) => (
                        <div key={m.id} style={{ fontSize: 12, padding: '2px 0', borderBottom: '1px solid #f0f0f0' }}>
                          {m.name}
                          {m.monthly_rent != null && <span style={{ float: 'right' }}>฿{m.monthly_rent.toLocaleString()}</span>}
                        </div>
                      ))}
                    </div>
                  </Popup>
                </Marker>
              );
            }
            const m = item as PropertyMarker;
            return (
              <Marker key={m.id} position={[m.latitude, m.longitude]}>
                <Popup>
                  <div style={{ minWidth: 180 }}>
                    <strong>{m.name}</strong><br />
                    {m.district && <span>{m.district}<br /></span>}
                    {m.monthly_rent != null && <span>฿{m.monthly_rent.toLocaleString()}<br /></span>}
                    {(m.nearest_bts || m.nearest_mrt) && (
                      <span style={{ fontSize: 12, color: '#666' }}>
                        {m.nearest_bts ? `BTS ${m.nearest_bts}` : ''}
                        {m.nearest_bts && m.nearest_mrt ? ' / ' : ''}
                        {m.nearest_mrt ? `MRT ${m.nearest_mrt}` : ''}
                        <br />
                      </span>
                    )}
                    <Space size={4} style={{ marginTop: 6 }}>
                      {showStreetView && (
                        <Button
                          size="small"
                          icon={<EnvironmentOutlined />}
                          onClick={() => openStreetView(m)}
                        >
                          街景
                        </Button>
                      )}
                      <Button
                        size="small"
                        icon={<CompassOutlined />}
                        onClick={() => openDirections(m)}
                      >
                        导航
                      </Button>
                    </Space>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>
      {showStreetView && (
        <StreetViewModal
          open={svOpen}
          lat={svLat}
          lng={svLng}
          title={svTitle}
          onClose={() => setSvOpen(false)}
        />
      )}
    </>
  );
}
