import { apiGet, apiPost } from "@/lib/api";

// Busca os modelos reais disponíveis para uma chave/provider.
// base_url opcional — o backend usa o padrão do provider se vazio.
export const fetchAIModels = (provider: string, apiKey: string, baseUrl?: string, credentialId?: string) => {
  const p = new URLSearchParams({ provider });
  if (apiKey) p.set("api_key", apiKey);
  if (baseUrl) p.set("base_url", baseUrl);
  // credential_id: o backend resolve a chave real server-side (a lista de credenciais só
  // devolve chave mascarada). Antes esse arg era ignorado e "buscar modelos" só com
  // credencial selecionada falhava pedindo api_key.
  if (credentialId) p.set("credential_id", credentialId);
  return apiGet<{ models: string[]; base_url: string }>(`/api/ai/models?${p.toString()}`).then((r) => r.models ?? []);
};

// Testa a chave/modelo fazendo uma chamada REAL mínima no provider.
// Funciona pra qualquer provider (inclusive proxy custom).
export const testAIKey = (provider: string, apiKey: string, baseUrl?: string, model?: string) =>
  apiPost<{ ok: boolean; error?: string; hint?: string; reason?: string }>("/api/ai/test", {
    provider,
    api_key: apiKey,
    base_url: baseUrl || "",
    model: model || "",
  });

// Prompts padrão dos agentes (pra pré-preencher os campos vazios)
export const fetchDefaultPrompts = () =>
  apiGet<{ attendant: string; manager: string; ai: string }>("/api/ai/default-prompts");
