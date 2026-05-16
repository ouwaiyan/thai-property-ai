export interface LineMessageOut {
  id: string;
  line_user_id: string;
  lead_id: string | null;
  message_text: string;
  direction: 'incoming' | 'outgoing';
  message_type: string;
  source_type: string;
  reply_status: string | null;
  created_at: string;
}

export interface LineConversationOut {
  line_user_id: string;
  lead_id: string | null;
  lead_name: string | null;
  messages: LineMessageOut[];
  latest_message_at: string | null;
}

export interface LineConversationSummary {
  line_user_id: string;
  lead_id: string | null;
  lead_name: string;
  lead_status: string;
  latest_message_at: string;
  message_count: number;
}

export interface LineAIReplyResponse {
  suggested_reply: string;
  lead_context: Record<string, unknown> | null;
}

export interface LineReplyRequest {
  reply_token: string;
  message_text: string;
}

export interface LinePushRequest {
  line_user_id: string;
  message_text: string;
}
