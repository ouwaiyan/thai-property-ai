export interface PropertyStats {
  total: number;
  by_status: Record<string, number>;
  rental_rate: number;
  availability_rate: number;
  price: { min: number; max: number; avg: number };
  bedroom_distribution: Record<string, number>;
}

export interface LeadFunnelStage {
  stage: string;
  count: number;
}

export interface LeadFunnel {
  period_days: number;
  total_leads: number;
  funnel: LeadFunnelStage[];
  by_source: Record<string, number>;
}

export interface TopProperty {
  name: string;
  property_code: string;
  recommendation_count: number;
}

export interface DailyTrend {
  date: string;
  count: number;
}

export interface RecommendationStats {
  period_days: number;
  total_recommendations: number;
  sent_to_customer: number;
  send_rate: number;
  average_match_score: number;
  top_properties: TopProperty[];
  daily_trend: DailyTrend[];
}

export interface RichMenuOut {
  rich_menu_id: string | null;
  name: string;
  chat_bar_text: string;
  areas: Record<string, unknown>[];
  selected: boolean;
  is_default: boolean;
}

export interface AutoReplyStatus {
  enabled: boolean;
}
