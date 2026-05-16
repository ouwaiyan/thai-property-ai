export interface PropertyImageOut {
  id: string;
  image_url: string;
  sort_order: number;
  is_cover: boolean;
}

export interface PropertyOut {
  id: string;
  property_code: string;
  name: string;
  building_name: string;
  address: string;
  latitude: number;
  longitude: number;
  district: string;
  area: string;
  nearest_bts: string | null;
  nearest_mrt: string | null;
  bedroom_count: number;
  bathroom_count: number;
  size_sqm: number;
  monthly_rent: number;
  deposit_months: number | null;
  status: string;
  available_date: string | null;
  pet_allowed: boolean;
  contact_person: string;
  contact_line: string | null;
  contact_phone: string;
  description: string;
  internal_note: string | null;
  tags: string[];
  created_by: string;
  assigned_agent_id: string | null;
  created_at: string;
  updated_at: string;
  images: PropertyImageOut[];
}

export interface PropertyListOut {
  id: string;
  property_code: string;
  name: string;
  building_name?: string;
  address: string;
  latitude?: number;
  longitude?: number;
  district: string;
  area: string;
  nearest_bts?: string | null;
  nearest_mrt?: string | null;
  bedroom_count: number;
  bathroom_count: number;
  size_sqm: number;
  monthly_rent: number;
  status: string;
  pet_allowed?: boolean;
  contact_person?: string;
  contact_line?: string | null;
  contact_phone?: string;
  tags: string[];
  distance_meters?: number;
  created_by: string;
  assigned_agent_id: string | null;
  created_at: string;
  updated_at?: string;
  images: PropertyImageOut[];
}

export interface PropertyCreate {
  property_code: string;
  name: string;
  building_name?: string;
  address: string;
  latitude: number;
  longitude: number;
  district: string;
  area: string;
  nearest_bts?: string;
  nearest_mrt?: string;
  bedroom_count: number;
  bathroom_count: number;
  size_sqm: number;
  monthly_rent: number;
  deposit_months?: number;
  status?: string;
  available_date?: string;
  pet_allowed?: boolean;
  contact_person: string;
  contact_line?: string;
  contact_phone: string;
  description?: string;
  internal_note?: string;
  tags?: string[];
  assigned_agent_id?: string;
}

export interface PropertyUpdate {
  property_code?: string;
  name?: string;
  building_name?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  district?: string;
  area?: string;
  nearest_bts?: string;
  nearest_mrt?: string;
  bedroom_count?: number;
  bathroom_count?: number;
  size_sqm?: number;
  monthly_rent?: number;
  deposit_months?: number;
  status?: string;
  available_date?: string;
  pet_allowed?: boolean;
  contact_person?: string;
  contact_line?: string;
  contact_phone?: string;
  description?: string;
  internal_note?: string;
  tags?: string[];
  assigned_agent_id?: string;
}

export interface PropertyFilter {
  search?: string;
  status?: string;
  min_price?: number;
  max_price?: number;
  min_bedrooms?: number;
  max_bedrooms?: number;
  district?: string;
  assigned_agent_id?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
  lat?: number;
  lng?: number;
  radius_meters?: number;
}
