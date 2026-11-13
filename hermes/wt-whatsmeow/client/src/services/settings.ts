import { apiGet, apiPut, apiPost, apiDelete } from "@/lib/api";
import type { AllSettings, TelegramSettings, AISettings, VoiceSettings, WebhookSettings, AgentChatSettings, CallAISettings, Credential } from "@/types/settings";

export async function getCredentials(): Promise<Credential[]> {
  const res = await apiGet<{ credentials: Credential[] }>("/api/credentials");
  return res.credentials || [];
}

export async function createCredential(c: Partial<Credential>): Promise<string> {
  const res = await apiPost<{ id: string }>("/api/credentials", c);
  return res.id;
}

export async function updateCredential(id: string, c: Partial<Credential>): Promise<void> {
  await apiPut(`/api/credentials/${id}`, c);
}

export async function deleteCredential(id: string): Promise<void> {
  await apiDelete(`/api/credentials/${id}`);
}

export async function getSettings(): Promise<AllSettings> {
  return apiGet<AllSettings>("/api/settings");
}

export async function updateTelegram(cfg: TelegramSettings): Promise<void> {
  await apiPut("/api/settings/telegram", cfg);
}

export async function updateAI(cfg: AISettings): Promise<void> {
  await apiPut("/api/settings/ai", cfg);
}

export interface BudgetConfig {
  enabled: boolean;
  monthly_brl: number;
  hard_limit: boolean;
  warn_at_pct: number;
}

export async function updateBudget(cfg: BudgetConfig): Promise<void> {
  await apiPut("/api/settings/budget", cfg);
}

export interface AICostSummary {
  rows: { model: string; calls: number; tokens_in: number; tokens_out: number; cost_brl: number }[];
  total_brl: number;
  month_brl: number;
  budget_enabled: boolean;
  budget_monthly: number;
  budget_hard: boolean;
  budget_warn_pct: number;
}

export async function getAICost(): Promise<AICostSummary> {
  return apiGet<AICostSummary>("/api/ai-cost");
}

// Pode mandar só os campos que mudaram: o servidor mantém o resto (mergeOnStored).
export async function updateVoice(cfg: Partial<VoiceSettings>): Promise<void> {
  await apiPut("/api/settings/voice", cfg);
}

export async function updateCallAI(cfg: CallAISettings): Promise<void> {
  await apiPut("/api/settings/call-ai", cfg);
}

export async function updateWebhook(cfg: WebhookSettings): Promise<void> {
  await apiPut("/api/settings/webhook", cfg);
}

export async function updateAgentChat(cfg: AgentChatSettings): Promise<void> {
  await apiPut("/api/settings/agent-chat", cfg);
}

// agentChatSemRoteamento: cópia sem default_profile_id/voice_profile_id (o roteamento é salvo
// pela tela de agentes). Telas que não mexem nele não mandam esses campos: a foto lida quando a
// tela abriu desfazia a troca feita em outra aba. O servidor mantém o que não veio.
export function agentChatSemRoteamento(cfg: AgentChatSettings): AgentChatSettings {
  const c = { ...cfg };
  delete c.default_profile_id;
  delete c.voice_profile_id;
  return c;
}

export async function createAgentGroup(name: string, welcomeMsg: string): Promise<{ ok: boolean; group_jid: string; name: string }> {
  return apiPost("/api/settings/agent-chat/create-group", { name, welcome_msg: welcomeMsg });
}

export interface WhatsAppGroup {
  jid: string;
  name: string;
}

export async function getAgentGroups(): Promise<WhatsAppGroup[]> {
  return apiGet<WhatsAppGroup[]>("/api/settings/agent-chat/groups");
}

export async function testTelegram(chatId?: number): Promise<{ ok: boolean; chat_id: number }> {
  return apiPost("/api/settings/telegram/test", { chat_id: chatId ?? 0 });
}

export async function testWebhook(): Promise<{ ok: boolean; status_code: number }> {
  return apiPost("/api/settings/webhook/test", {});
}
