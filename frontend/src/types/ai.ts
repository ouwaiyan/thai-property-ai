// Parse Lead
export interface ParseLeadRequest {
  message: string;
  language?: string;
  lead_id?: string;
}

export interface ParseLeadResponse {
  target_location: string | null;
  budget_min: number | null;
  budget_max: number | null;
  bedroom_count: number | null;
  pet_required: boolean;
  preferred_transport: string | null;
  tags: string[];
  missing_fields: string[];
  follow_up_questions: string[];
}

// Generate Tags
export interface GenerateTagsRequest {
  property_id: string;
  language?: string;
}

export interface GenerateTagsResponse {
  tags: string[];
  highlights: string[];
}

// Generate Sales Copy
export interface GenerateMessageRequest {
  lead_id: string;
  property_ids: string[];
  language?: string;
  tone?: string;
}

export interface GenerateMessageResponse {
  messages: Array<{ property_id: string; message: string }>;
}

// Recommendation Search
export interface RecommendationSearchRequest {
  lead_id: string;
  limit?: number;
  max_distance_meters?: number | null;
  route_mode?: string;
}

export interface RecommendationSearchResult {
  property_id: string;
  property_code: string;
  name: string;
  monthly_rent: number;
  bedroom_count: number;
  district: string;
  latitude: number | null;
  longitude: number | null;
  distance_meters: number | null;
  duration_minutes: number | null;
  match_score: number;
  score_breakdown: Record<string, number>;
  reasons: string[];
}

export interface RecommendationSearchResponse {
  lead_id: string;
  results: RecommendationSearchResult[];
  total_scanned: number;
}

// Recommendation History
export interface RecommendationOut {
  id: string;
  lead_id: string;
  property_id: string;
  property_code: string | null;
  property_name: string | null;
  monthly_rent: number | null;
  bedroom_count: number | null;
  district: string | null;
  distance_meters: number | null;
  duration_minutes: number | null;
  route_mode: string | null;
  match_score: number;
  reason_json: Record<string, unknown> | null;
  ai_message: string | null;
  sent_to_customer: boolean;
  created_at: string;
}

export interface SaveMessageRequest {
  ai_message: string;
}

// Mark Sent
export interface MarkSentResponse {
  recommendation_id: string;
  sent_to_customer: boolean;
}

// Data Cleaning
export interface CleanDataRequest {
  column_name: string;
  sample_values: string[];
  expected_type?: string;
}

export interface CleanDataResponse {
  suggestions: Array<Record<string, unknown>>;
  pattern_rule: string | null;
}
