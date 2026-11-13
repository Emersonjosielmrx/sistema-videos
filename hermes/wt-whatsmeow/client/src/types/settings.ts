export interface Credential {
  id: string;
  name: string;
  type: string;
  provider: string;
  api_key: string;
  base_url: string;
  created_at?: string;
}

export interface TelegramSettings {
  token: string;
  enabled: boolean;
  chat_ids: number[];
}

export interface AISettings {
  credential_id?: string;
  provider: string;
  model: string;
  api_key: string;
  api_base_url: string;
  system_message: string;
  enabled: boolean;
  allow_send_message: boolean;
  allow_send_audio: boolean;
  allow_send_link: boolean;
}

export interface VoiceSettings {
  stt_credential_id?: string;
  stt_provider: string;
  stt_api_key: string;
  stt_base_url: string;
  stt_model: string;
  tts_credential_id?: string;
  tts_provider: string;
  tts_api_key: string;
  tts_base_url: string;
  tts_voice: string;
  vad_silence_ms: number;
  vad_threshold: number;
  auto_answer: boolean;
  callback_missed: boolean;
  filler_enabled: boolean;
  filler_words: string[];
  barge_in_enabled?: boolean;
  barge_in_sensitivity?: string;
  // Aviso no Telegram quando lead de campanha responde no WhatsApp. null/ausente = ligado.
  return_campaign_mode?: boolean | null;
  // Monitor de grupos: aviso no Telegram de oportunidade em grupo. null/ausente = desligado.
  group_monitor?: boolean | null;
  barge_ack_words?: string[];
  ambient_mode?: string;
  background_noise?: string;
  background_noise_volume?: number;
}

export interface CallAISettings {
  credential_id?: string;
  enabled: boolean;
  provider: string;
  model: string;
  api_key: string;
  api_base_url: string;
  system_message: string;
}

export interface WebhookSettings {
  url: string;
  events: string[];
  notification_channel: "webhook" | "telegram" | "whatsapp" | "app";
  whatsapp_notify_number: string;
}

export interface OpenClawConfig {
  enabled: boolean;
  url: string;
  api_key: string;
}

export interface AgentChatSettings {
  enabled: boolean;
  mode: string;
  group_jid: string;
  group_name: string;
  welcome_msg: string;
  notify_telegram: boolean;
  owner_message_enabled: boolean;
  outbound_only: boolean;
  openclaw: OpenClawConfig;
  default_profile_id?: string; // Roteamento Nível 1: agente padrão de mensagens
  voice_profile_id?: string;   // quem ATENDE ligações recebidas (as que o dono pede usam /api/call-agent/default)
}

export interface ScheduleConfig {
  enabled: boolean;
  timezone: string;
  days: Record<string, { enabled: boolean; start: string; end: string }>;
}

export interface RateLimitConfig {
  enabled: boolean;
  max_messages: number;
  window_seconds: number;
  cooldown_message: string;
}

export interface IPWhitelistConfig {
  enabled: boolean;
  ips: string[];
}

export interface AgentConfig {
  enabled: boolean;
  provider: string;
  model: string;
  api_key: string;
  base_url: string;
  system_message: string;
  credential_id?: string;
}

export interface AllSettings {
  telegram: TelegramSettings;
  ai: AISettings;
  voice: VoiceSettings;
  webhook: WebhookSettings;
  agent_chat: AgentChatSettings;
  attendant?: AgentConfig;
  manager?: AgentConfig;
  schedule?: ScheduleConfig;
  rate_limit?: RateLimitConfig;
  ip_whitelist?: IPWhitelistConfig;
  call_ai?: CallAISettings;
}

export interface DashboardData {
  sessions: { total: number; paired: number };
  calls: { active: number; today: number; avg_duration_ms: number; answer_rate: number };
  // Blocos reais (agregados de campaign_results / call_transcripts). Opcionais p/
  // compatibilidade com respostas antigas do backend.
  range?: string;
  funnel?: { attempts: number; answered: number; engaged: number; leads: number };
  sentiment?: { name: string; value: number }[];
  timeseries?: { bucket: string; calls: number; answered: number }[];
  cost?: { ai_brl_month: number };
  services: {
    telegram: { enabled: boolean; running: boolean };
    ai: { enabled: boolean; provider: string; model: string };
    voice: { enabled: boolean; stt_provider: string };
  };
  timestamp: number;
}
