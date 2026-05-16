'use client';

import { useCallback, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface MapPickerProps {
  lat?: number | null;
  lng?: number | null;
  onChange: (lat: number, lng: number) => void;
}

function MapClickHandler({ onClick }: { onClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export default function MapPicker({ lat, lng, onChange }: MapPickerProps) {
  const center: [number, number] = useMemo(() => {
    if (lat != null && lng != null) return [lat, lng];
    return [13.7563, 100.5018]; // Bangkok
  }, [lat, lng]);

  const handleClick = useCallback(
    (clickedLat: number, clickedLng: number) => {
      onChange(clickedLat, clickedLng);
    },
    [onChange],
  );

  return (
    <div className="map-picker-container">
      <MapContainer
        center={center}
        zoom={12}
        style={{ height: '100%', width: '100%', borderRadius: 8 }}
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapClickHandler onClick={handleClick} />
        {lat != null && lng != null && (
          <Marker position={[lat, lng]} />
        )}
      </MapContainer>
    </div>
  );
}
