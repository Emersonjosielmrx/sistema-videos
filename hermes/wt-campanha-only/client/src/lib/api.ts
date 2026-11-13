import { getClientId } from "./client-id";
import { apiUrl, authHeaders, clearAuth, getToken } from "./auth";

const baseHeaders = (): HeadersInit => ({
  "X-Client-Id": getClientId(),
  ...authHeaders(),
  "Content-Type": "application/json",
});

// Em 401 (key inválida/expirada) limpa a auth e volta pra tela de login.
// IMPORTANTE: só recarrega se REALMENTE havia um token (senão entra em loop de reload
// quando não há sessão — vários pollings dão 401 a cada poucos segundos e a página
// ficava recarregando sozinha sem parar). Sem token, apenas ignora e deixa o erro subir.
const guard = (status: number) => {
  // 403 no meio do uso pode ser teste vencido / cobrança vencida: confere no /me e, se for,
  // recarrega UMA vez pra o AuthGate mostrar a tela de assinatura (antes a UI só quebrava).
  if (status === 403 && getToken() && !sessionStorage.getItem("hermes.reloaded_on_403")) {
    import("./auth").then(({ checkAuth }) => checkAuth()).then((res) => {
      if (res === "trial_expired" || res === "payment_required") {
        sessionStorage.setItem("hermes.reloaded_on_403", "1");
        location.reload();
      }
    }).catch(() => {});
  }
  if (status === 401 && getToken()) {
    clearAuth();
    // Trava anti-loop: recarrega no máximo UMA vez por carregamento de página.
    // Sem isso, se algo pós-reload ainda desse 401, a página recarregava sem parar.
    if (!sessionStorage.getItem("hermes.reloaded_on_401")) {
      sessionStorage.setItem("hermes.reloaded_on_401", "1");
      location.reload();
    }
  }
};

export const apiGet = async <T>(path: string): Promise<T> => {
  const r = await fetch(apiUrl(path), { headers: baseHeaders() });
  if (!r.ok) {
    guard(r.status);
    const text = await r.text().catch(() => "");
    throw new Error(`${path} ${r.status} ${text}`.trimEnd());
  }
  return r.json() as Promise<T>;
};

export const apiPost = async <T>(path: string, body: unknown): Promise<T> => {
  const r = await fetch(apiUrl(path), { method: "POST", headers: baseHeaders(), body: JSON.stringify(body) });
  if (!r.ok) {
    guard(r.status);
    const text = await r.text().catch(() => "");
    throw new Error(`${path} ${r.status} ${text}`);
  }
  return r.json() as Promise<T>;
};

export const apiDelete = async (path: string): Promise<void> => {
  const r = await fetch(apiUrl(path), { method: "DELETE", headers: baseHeaders() });
  if (!r.ok) {
    guard(r.status);
    // Repassa o corpo ({error, message}) para a tela mostrar a mensagem do servidor.
    const text = await r.text().catch(() => "");
    throw new Error(`${path} ${r.status} ${text}`.trimEnd());
  }
};

// POST sem corpo/resposta (logout, pair). Passa pelo guard: em 401 (token expirado)
// limpa a auth e volta pro login, em vez de estourar "Falha 401" na tela.
export const apiPostVoid = async (path: string): Promise<void> => {
  const r = await fetch(apiUrl(path), { method: "POST", headers: baseHeaders(), body: "{}" });
  if (!r.ok) {
    guard(r.status);
    throw new Error(`${path} ${r.status}`);
  }
};

// Upload multipart (arquivo). NÃO seta Content-Type: o browser põe o boundary sozinho.
export const apiUpload = async <T>(path: string, form: FormData): Promise<T> => {
  const headers: HeadersInit = { "X-Client-Id": getClientId(), ...authHeaders() };
  const r = await fetch(apiUrl(path), { method: "POST", headers, body: form });
  if (!r.ok) {
    guard(r.status);
    const text = await r.text().catch(() => "");
    throw new Error(`${path} ${r.status} ${text}`);
  }
  return r.json() as Promise<T>;
};

export const apiPut = async <T>(path: string, body: unknown): Promise<T> => {
  const r = await fetch(apiUrl(path), { method: "PUT", headers: baseHeaders(), body: JSON.stringify(body) });
  if (!r.ok) {
    guard(r.status);
    const text = await r.text().catch(() => "");
    throw new Error(`${path} ${r.status} ${text}`);
  }
  return r.json() as Promise<T>;
};

// --- Leitura amigável de erros das funções acima -------------------------------------
// As funções lançam Error("<rota> <status> <corpo>"). Estes ajudantes tiram dali o status
// HTTP e a mensagem {"error": "..."} do servidor, para a tela mostrar algo legível.
const parseApiError = (e: unknown): { status: number | null; body: string } => {
  const msg = e instanceof Error ? e.message : String(e ?? "");
  const m = /^\S+ (\d{3})(?: ([\s\S]*))?$/.exec(msg);
  if (!m) return { status: null, body: "" };
  return { status: Number(m[1]), body: (m[2] || "").trim() };
};

// Corpo JSON do erro ({error, message, field...}) ou null.
export const apiErrorBody = (e: unknown): Record<string, any> | null => {
  const { body } = parseApiError(e);
  if (!body) return null;
  try {
    const j = JSON.parse(body);
    return j && typeof j === "object" ? j : null;
  } catch {
    return null;
  }
};

// Status HTTP do erro (ex.: 403, 404) ou null se foi erro de rede/outro.
export const apiErrorStatus = (e: unknown): number | null => parseApiError(e).status;

// Mensagem do servidor ({"error"} ou {"message"}) ou o texto padrão informado.
export const apiErrorMessage = (e: unknown, fallback: string): string => {
  const { body } = parseApiError(e);
  if (!body) return fallback;
  try {
    const j = JSON.parse(body);
    const txt = j?.message || j?.error;
    return typeof txt === "string" && txt.trim() ? txt : fallback;
  } catch {
    // corpo não-JSON (ex.: página de erro do proxy) não é mostrado
    return fallback;
  }
};
