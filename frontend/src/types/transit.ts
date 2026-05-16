export type TravelMode = 'DRIVE' | 'WALK' | 'TRANSIT';

export interface RouteMatrixRequest {
  origin_lat: number;
  origin_lng: number;
  property_ids: string[];
  travel_mode: TravelMode;
}

export interface RouteMatrixItem {
  property_id: string;
  distance_meters: number;
  duration_seconds: number;
  travel_mode: TravelMode;
}

export interface RouteMatrixResponse {
  origin_lat: number;
  origin_lng: number;
  travel_mode: TravelMode;
  results: RouteMatrixItem[];
  cached_count: number;
  api_call_made: boolean;
}
