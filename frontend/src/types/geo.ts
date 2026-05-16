export interface GeocodeResult {
  latitude: number;
  longitude: number;
  display_name: string;
}

export interface GeocodeRequest {
  query: string;
}
