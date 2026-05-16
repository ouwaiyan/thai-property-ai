import { setOptions, importLibrary } from '@googlemaps/js-api-loader';
import type { APIOptions } from '@googlemaps/js-api-loader';

let initialized = false;
let cachedKey: string | null = null;

async function fetchApiKeyFromBackend(): Promise<string> {
  try {
    const { getApiSettings } = await import('@/lib/api');
    const settings = await getApiSettings();
    const googleSettings = settings['google_maps'] || settings['google'] || [];
    const keySetting = googleSettings.find(
      (s: { key_name: string; value: string | null }) =>
        s.key_name === 'api_key' || s.key_name === 'js_api_key',
    );
    if (keySetting?.value) {
      return keySetting.value;
    }
  } catch {
    // Fall through to env var
  }
  return '';
}

export async function getGoogleMapsApiKey(): Promise<string> {
  if (cachedKey) return cachedKey;

  if (typeof window !== 'undefined') {
    const backendKey = await fetchApiKeyFromBackend();
    if (backendKey) {
      cachedKey = backendKey;
      return cachedKey;
    }
  }

  const envKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || '';
  cachedKey = envKey;
  return cachedKey;
}

export function setGoogleMapsApiKey(key: string) {
  cachedKey = key;
  initialized = false;
}

function ensureOptions(apiKey: string) {
  if (!initialized) {
    const opts: APIOptions = { key: apiKey, libraries: ['places', 'geometry'] };
    setOptions(opts);
    initialized = true;
  }
}

export async function getGoogleMaps(): Promise<google.maps.MapsLibrary> {
  const key = await getGoogleMapsApiKey();
  ensureOptions(key);
  try {
    return await importLibrary('maps');
  } catch {
    initialized = false;
    ensureOptions(key);
    return importLibrary('maps');
  }
}

export { importLibrary };

export function openGoogleMapsDirections(lat: number, lng: number) {
  window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
}
