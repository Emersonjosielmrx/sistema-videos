import { apiGet, apiPost, apiDelete, apiPut } from "@/lib/api";

// Config anti-bloqueio da campanha de áudio.
export type BroadcastConfig = {
  name?: string;
  audio_base64?: string;
  audio_url?: string;
  audio_id?: string;        // reusa um áudio salvo na biblioteca
  save_audio_as?: string;   // salva o áudio desta campanha na biblioteca
  tts_message?: string;     // gera áudio por texto (variante A)
  tts_message_b?: string;   // A/B: texto da variante B (alterna com a A)
  audio_id_b?: string;      // A/B: áudio salvo da variante B
  numbers: string[];
  concurrency?: number;
  gap_min_ms?: number;
  gap_max_ms?: number;
  max_ring_ms?: number;
  hangup_after_ms?: number;
  respect_schedule?: boolean;
  start_hour?: number;
  end_hour?: number;
  max_per_run?: number;
  capture_reply?: boolean;
  names?: string[];
  pre_notify?: boolean;
  batch_size?: number;
  pre_notify_sec?: number;
  // Campanha v2 — modo de disparo:
  //   "immediate" = dispara já (padrão). "paced" = ao longo do dia. "multiline" = várias linhas.
  mode?: "immediate" | "paced" | "multiline";
  per_day?: number;     // alvo/dia (paced)
  per_min?: number;     // ligações por minuto (paced)
  ramp_start?: number;  // cadência inicial/dia; sobe gradual até per_day
  session_ids?: string[]; // linhas do modo multiline
};

export const startBroadcast = (sid: string, cfg: BroadcastConfig) =>
  apiPost<{ campaignId: string; total: number; seconds: number }>(`/api/sessions/${sid}/broadcast`, cfg);

// ---------- Padrões de campanha (modo/ritmo salvos, reusados a cada disparo) ----------
export type CampaignDefaults = {
  mode: "immediate" | "paced" | "multiline";
  per_day: number;
  per_min: number;
  ramp_start: number;
  start_hour: number;
  end_hour: number;
  gap_min_sec: number;
  gap_max_sec: number;
};

export const getCampaignDefaults = () =>
  apiGet<CampaignDefaults>("/api/settings/campaign-defaults");

export const saveCampaignDefaults = (cfg: CampaignDefaults) =>
  apiPut<{ status: string }>("/api/settings/campaign-defaults", cfg);

export const getBroadcastStatus = (sid: string, cid: string) =>
  apiGet<{ campaignId: string; total: number; done: boolean; paused: boolean; results: any[] }>(`/api/sessions/${sid}/broadcast/${cid}`);

export const pauseBroadcast = (sid: string, cid: string) =>
  apiPost<{ ok: boolean; paused: boolean }>(`/api/sessions/${sid}/broadcast/${cid}/pause`, {});

export const resumeBroadcast = (sid: string, cid: string) =>
  apiPost<{ ok: boolean; paused: boolean }>(`/api/sessions/${sid}/broadcast/${cid}/resume`, {});

// ---------- Listas personalizadas ----------
export type ContactList = {
  id: string;
  name: string;
  phones: string[];
  count: number;
  created_at: string;
};

export const listContactLists = () =>
  apiGet<{ lists: ContactList[] }>("/api/contact-lists").then((r) => r.lists ?? []);

export const createContactList = (name: string, phones: string[]) =>
  apiPost<ContactList>("/api/contact-lists", { name, phones });

export const getContactList = (id: string) => apiGet<ContactList>(`/api/contact-lists/${id}`);

export const deleteContactList = (id: string) => apiDelete(`/api/contact-lists/${id}`);

export const appendToContactList = (id: string, phones: string[]) =>
  apiPost<ContactList>(`/api/contact-lists/${id}/append`, { phones });

// ---------- Histórico/score por contato ----------
export type ContactStat = {
  number: string;
  calls: number;
  answered: number;
  completed: number;
  avg_listen: number;
  max_listen: number;
  interested: boolean;
  last_reply: string;
  score: number;
};

export const getContactStats = () =>
  apiGet<{ stats: Record<string, ContactStat> }>("/api/contacts/stats").then((r) => r.stats ?? {});

// ---------- Analytics agregado de chamadas ----------
export type CallAnalytics = {
  total_campaigns: number;
  total_calls: number;
  answered: number;
  no_answer: number;
  failed: number;
  answer_rate: number;
  avg_listen_pct: number;
  full_listen: number;
  interested: number;
  total_listen_sec: number;
};

export const getCallAnalytics = () => apiGet<CallAnalytics>("/api/analytics/calls");

// ---------- TTS: gerar áudio por IA a partir de texto ----------
export const generateTTS = (text: string, voice?: string) =>
  apiPost<{ audio_base64: string; voice: string; bytes: number }>("/api/tts/generate", { text, voice });

// ---------- Biblioteca de áudios pré-gravados (por conta) ----------
export type SavedAudio = {
  id: string;
  name: string;
  mime: string;
  bytes: number;
  duration_ms: number;
  voice?: string;
  source: string;
  created_at: string;
  audio_base64?: string; // só vem no getAudio
};

export const listAudios = () =>
  apiGet<{ audios: SavedAudio[] }>("/api/audios").then((r) => r.audios ?? []);

export const getAudio = (id: string) => apiGet<SavedAudio>(`/api/audios/${id}`);

export const createAudio = (payload: {
  name: string;
  audio_base64: string;
  mime?: string;
  duration_ms?: number;
  voice?: string;
  source?: string;
}) => apiPost<SavedAudio>("/api/audios", payload);

export const deleteAudio = (id: string) => apiDelete(`/api/audios/${id}`);
