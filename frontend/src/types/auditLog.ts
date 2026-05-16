export interface AuditLogOut {
  id: string;
  user_id: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  before_json: Record<string, unknown> | null;
  after_json: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}
