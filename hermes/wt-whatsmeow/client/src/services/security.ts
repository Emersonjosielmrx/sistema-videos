import { apiGet, apiPost, apiPut, apiDelete } from "@/lib/api";
import type {
  AuditEntry,
  LoginSession,
  TwoFASetup,
  AccessEntry,
  ContactTag,
  ContactNote,
  LeadClassification,
  CallRecording,
  DailyStat,
  WeeklyReport,
  ChatMessage,
} from "@/types/security";
import type { ScheduleConfig, RateLimitConfig, IPWhitelistConfig } from "@/types/settings";

// Audit Log
export const getAuditLog = (limit = 50, offset = 0) =>
  apiGet<{ entries: AuditEntry[]; total: number }>(`/api/audit-log?limit=${limit}&offset=${offset}`);

// 2FA
export const setup2FA = () => apiPost<TwoFASetup>("/api/2fa/setup", {});
// Ligar/desligar exige a senha atual ("password"). Erros: 400 password_required/invalid_code,
// 403 invalid_password, 429 limite — todos com "message".
export const enable2FA = (secret: string, code: string, password: string) =>
  apiPost<{ status: string }>("/api/2fa/enable", { secret, code, password });
export const disable2FA = (code: string, password: string) =>
  apiPost<{ status: string }>("/api/2fa/disable", { code, password });
export const verify2FA = (code: string) => apiPost<{ status: string }>("/api/2fa/verify", { code });
// Recuperação (só admin da plataforma): desliga o 2FA de uma conta que perdeu o autenticador.
export const adminDisable2FA = (email: string) =>
  apiPost<{ ok?: boolean; email?: string }>("/api/admin/2fa/disable", { email: email.trim() });

// Login Sessions
export const getLoginSessions = () => apiGet<{ sessions: LoginSession[] }>("/api/security/sessions");
export const revokeSession = (sessionId: string) => apiPost<{ status: string }>("/api/security/sessions/revoke", { session_id: sessionId });
export const revokeAllSessions = (exceptCurrent?: boolean) => apiPost<{ status: string }>("/api/security/sessions/revoke-all", { except_current: exceptCurrent });

// IP Whitelist
export const getIPWhitelist = () => apiGet<IPWhitelistConfig>("/api/security/ip-whitelist");
export const updateIPWhitelist = (cfg: IPWhitelistConfig) => apiPut<{ status: string }>("/api/security/ip-whitelist", cfg);

// Access List
export const getAccessList = () => apiGet<{ mode: string; entries: AccessEntry[] }>("/api/access-list");
export const setAccessMode = (mode: string) => apiPut<{ status: string }>("/api/access-list/mode", { mode });
export const addAccessEntry = (jid: string, phone: string, label: string) => apiPost<{ status: string }>("/api/access-list/entry", { jid, phone, label });
export const removeAccessEntry = (jid: string) => apiPost<{ status: string }>("/api/access-list/entry/remove", { jid });

// Rate Limit
export const getRateLimit = () => apiGet<RateLimitConfig>("/api/settings/rate-limit");
export const updateRateLimit = (cfg: RateLimitConfig) => apiPut<{ status: string }>("/api/settings/rate-limit", cfg);

// Schedule
export const getSchedule = () => apiGet<ScheduleConfig>("/api/settings/schedule");
export const updateSchedule = (cfg: ScheduleConfig) => apiPut<{ status: string }>("/api/settings/schedule", cfg);

// Recordings
export const getRecordings = (limit = 20, offset = 0) =>
  apiGet<{ recordings: CallRecording[]; total: number }>(`/api/recordings?limit=${limit}&offset=${offset}`);
export const deleteRecording = (id: string) => apiDelete(`/api/recordings/${id}`);

// Contact Tags
export const getTags = () => apiGet<{ tags: ContactTag[] }>("/api/contacts/tags");
export const createTag = (name: string, color: string) => apiPost<ContactTag>("/api/contacts/tags", { name, color });
export const deleteTag = (id: string) => apiDelete(`/api/contacts/tags/${id}`);
export const assignTag = (jid: string, tagId: string) => apiPost<{ status: string }>("/api/contacts/tags/assign", { jid, tag_id: tagId });
export const unassignTag = (jid: string, tagId: string) => apiPost<{ status: string }>("/api/contacts/tags/unassign", { jid, tag_id: tagId });
export const getContactTags = (jid: string) => apiGet<{ tags: ContactTag[] }>(`/api/contacts/tags/by-contact?jid=${jid}`);

// Contact Notes
export const addNote = (jid: string, content: string) => apiPost<ContactNote>("/api/contacts/notes", { jid, content });
export const getNotes = (jid: string) => apiGet<{ notes: ContactNote[] }>(`/api/contacts/notes?jid=${jid}`);
export const deleteNote = (id: string) => apiDelete(`/api/contacts/notes/${id}`);

// Leads
export const setLead = (jid: string, score: number, stage: string, source: string, notes: string) =>
  apiPost<{ status: string }>("/api/contacts/leads", { jid, score, stage, source, notes });
export const getLeads = (stage?: string) => apiGet<{ leads: LeadClassification[] }>(`/api/contacts/leads${stage ? `?stage=${stage}` : ""}`);
export const getLead = (jid: string) => apiGet<LeadClassification>(`/api/contacts/leads/single?jid=${jid}`);

// Conversations
export const getConversation = (jid: string, limit = 50) =>
  apiGet<{ messages: ChatMessage[] }>(`/api/conversations?jid=${jid}&limit=${limit}`);
export const clearConversation = (jid: string) => apiPost<{ status: string }>("/api/conversations/clear", { jid });

// Analytics
export const getAnalytics = (days = 30) =>
  apiGet<{ daily: DailyStat[]; hourly: number[]; avg_response_ms: number }>(`/api/analytics?days=${days}`);
export const getWeeklyReport = () => apiGet<WeeklyReport>("/api/analytics/weekly");
