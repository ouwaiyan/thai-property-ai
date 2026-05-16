'use client';

import { useState } from 'react';
import { Input, Select, Button } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { geocodeAddress } from '@/lib/api';
import { useI18n } from '@/i18n/i18n';
import type { GeocodeResult } from '@/types/geo';
import type { TravelMode } from '@/types/transit';

interface NearbySearchProps {
  onSearch: (lat: number, lng: number, radius: number, travelMode: TravelMode) => void;
  loading?: boolean;
}

const radiusOptions = [
  { label: '500m', value: 500 },
  { label: '1km', value: 1000 },
  { label: '2km', value: 2000 },
  { label: '3km', value: 3000 },
  { label: '5km', value: 5000 },
];

export default function NearbySearch({ onSearch, loading }: NearbySearchProps) {
  const { t } = useI18n();
  const [query, setQuery] = useState('');
  const [radius, setRadius] = useState(1000);
  const [travelMode, setTravelMode] = useState<TravelMode>('DRIVE');
  const [searching, setSearching] = useState(false);

  const travelModeOptions = [
    { label: t('transit.DRIVE'), value: 'DRIVE' },
    { label: t('transit.WALK'), value: 'WALK' },
    { label: t('transit.TRANSIT'), value: 'TRANSIT' },
  ];

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const results: GeocodeResult[] = await geocodeAddress({ query: query.trim() });
      if (results.length > 0) {
        onSearch(results[0].latitude, results[0].longitude, radius, travelMode);
      }
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="nearby-search-bar">
      <Input
        placeholder={t('nearby.placeholder')}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onPressEnter={handleSearch}
        style={{ width: 300 }}
        prefix={<SearchOutlined />}
      />
      <Select
        value={radius}
        onChange={setRadius}
        options={radiusOptions}
        style={{ width: 120 }}
      />
      <Select
        value={travelMode}
        onChange={setTravelMode}
        options={travelModeOptions}
        style={{ width: 100 }}
      />
      <Button
        type="primary"
        onClick={handleSearch}
        loading={searching || loading}
      >
        {t('nearby.search_button')}
      </Button>
    </div>
  );
}
