export interface LeadOut {
  id: string;
  name: string;
  phone: string | null;
  language: string;
  original_message: string;
  parsed_needs: Record<string, unknown> | null;
  target_location: string | null;
  budget_min: number | null;
  budget_max: number | null;
  bedroom_count: number | null;
  pet_required: boolean;
  preferred_transport: string | null;
  tags: string[] | null;
  status: string;
  source: string;
  line_user_id: string | null;
  assigned_agent_id: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface LeadCreate {
  name: string;
  phone?: string;
  language?: string;
  original_message: string;
  source?: string;
  line_user_id?: string;
  assigned_agent_id?: string;
}

export interface LeadUpdate {
  name?: string;
  phone?: string | null;
  status?: string;
  assigned_agent_id?: string | null;
}

export interface LeadFilter {
  page?: number;
  page_size?: number;
  status?: string;
  search?: string;
  source?: string;
  line_user_id?: string;
  assigned_agent_id?: string;
}
