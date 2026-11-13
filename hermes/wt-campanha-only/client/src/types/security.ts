export interface AuditEntry {
  id: string;
  user_id: string;
  action: string;
  detail: string;
  ip: string;
  user_agent: string;
  created_at: string;
}

export interface LoginSession {
  id: string;
  user_id: string;
  ip: string;
  user_agent: string;
  last_active: string;
  created_at: string;
  is_current?: boolean;
}

export interface TwoFASetup {
  secret: string;
  uri: string;
}

export interface AccessEntry {
  jid: string;
  phone: string;
  label: string;
  added_at: string;
}

export interface ContactTag {
  id: string;
  user_id: string;
  name: string;
  color: string;
  created_at: string;
}

export interface ContactNote {
  id: string;
  user_id: string;
  jid: string;
  content: string;
  created_at: string;
}

export interface LeadClassification {
  id: string;
  user_id: string;
  jid: string;
  score: number;
  stage: string;
  source: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface CallRecording {
  id: string;
  user_id: string;
  session_id: string;
  call_id: string;
  remote_jid: string;
  direction: string;
  duration_sec: number;
  file_size: number;
  file_path: string;
  transcription: string;
  ai_summary: string;
  created_at: string;
}

export interface DailyStat {
  date: string;
  messages_in: number;
  messages_out: number;
  calls_in: number;
  calls_out: number;
  avg_response_ms: number;
}

export interface WeeklyReport {
  total_messages: number;
  total_calls: number;
  avg_response_ms: number;
  busiest_hour: number;
  top_contacts: { jid: string; count: number }[];
}

export interface ChatMessage {
  role: string;
  content: string;
  created_at: string;
}
