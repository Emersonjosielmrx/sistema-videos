const TOKEN_KEY = "<SEGREDO_REMOVIDO>";
const USER_KEY = "hermes.user";

export const getToken = (): string => localStorage.getItem(TOKEN_KEY) || "";
export const getUser = (): any => {
  // FIX P2-002 (2026-07-25): JSON.parse pode quebrar (storage corrompido,
  // schema antigo, dado de outro user). Antes quebrava a página inteira
  // quando o JSON estava inválido. Agora retorna null silenciosamente.
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};
export const isAuthed = (): boolean => !!getToken();

// Admin da PLATAFORMA (a dona do Hermes), não o dono de uma conta. Vem do servidor no
// objeto do usuário (login e /api/auth/me). Sem o campo, vale como "não é admin".
export const isPlatformAdmin = (): boolean => getUser()?.is_platform_admin === true;

// Compat alias for existing services that import getApiKey
export const getApiKey = (): string => getToken();

export const setSession = (token: string, user: any): void => {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  // Reseta a trava anti-loop de reload (ver guard em lib/api.ts) num login novo.
  try { sessionStorage.removeItem("hermes.reloaded_on_401"); } catch {}
};

// Legacy compat
export const setAuth = (_url: string, key: string): void => {
  localStorage.setItem(TOKEN_KEY, key);
};

export const clearAuth = (): void => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

export const getApiBase = (): string => window.location.origin;
export const apiUrl = (path: string): string => getApiBase() + path;

export const authHeaders = (): Record<string, string> => {
  const token = getToken();
  if (token) return { Authorization: "Bearer " + token };
  return {};
};

// "offline" = servidor fora (502/503/rede): NÃO desloga; a tela avisa e tenta de novo.
export type AuthCheck = boolean | "trial_expired" | "payment_required" | "offline";

export const checkAuth = async (): Promise<AuthCheck> => {
  // Sem token salvo → nem tenta o /me: manda direto pra landing/login.
  if (!getToken()) return false;
  try {
    const r = await fetch(apiUrl("/api/auth/me"), { headers: authHeaders() });
    if (r.ok) {
      // Carregou bem: libera a trava anti-loop do 403 (ver guard em lib/api.ts).
      try { sessionStorage.removeItem("hermes.reloaded_on_403"); } catch { /* sem storage */ }
      // Atualiza o usuário guardado (ex.: is_platform_admin novo) sem mexer no token.
      const data = await r.json().catch(() => null);
      if (data?.user && typeof data.user === "object") {
        try { localStorage.setItem(USER_KEY, JSON.stringify(data.user)); } catch { /* sem storage */ }
      }
      return true;
    }
    // Trial expirado (403 com error "trial_expired") → tela de upgrade.
    if (r.status === 403) {
      const data = await r.json().catch(() => null);
      if (data?.error === "trial_expired") return "trial_expired";
      // Assinatura vencida além da tolerância → mesma tela, com opção de pagar.
      if (data?.error === "payment_required") return "payment_required";
      // Outros 403 (conta desativada, IP não permitido): sai da conta.
      clearAuth();
      return false;
    }
    // 401 → token inválido/expirado: limpa e volta pra landing.
    if (r.status === 401) {
      clearAuth();
      return false;
    }
    // 502/503/outros: servidor com problema — mantém a sessão e tenta de novo.
    return "offline";
  } catch {
    // Rede fora do ar: não desloga (evita expulsar o usuário por blip de conexão).
    return "offline";
  }
};

// Sair: avisa o servidor (encerra a sessão lá) e limpa o navegador. Se o servidor não
// responder em 3 s ou der erro, sai do mesmo jeito.
export const logout = async (): Promise<void> => {
  try {
    const ctrl = new AbortController();
    const t = window.setTimeout(() => ctrl.abort(), 3000);
    await fetch(apiUrl("/api/auth/logout"), { method: "POST", headers: authHeaders(), signal: ctrl.signal, keepalive: true })
      .catch(() => {})
      .finally(() => window.clearTimeout(t));
  } finally {
    clearAuth();
  }
};

// Retorno do login Google sem 2FA: o servidor volta com ?token=<jwt>. Guarda o token,
// tira o parâmetro da barra de endereço e deixa o /api/auth/me preencher o usuário.
export const consumeOAuthToken = (): boolean => {
  try {
    const u = new URL(window.location.href);
    const tok = u.searchParams.get("token");
    if (!tok) return false;
    localStorage.setItem(TOKEN_KEY, tok);
    localStorage.removeItem(USER_KEY);
    u.searchParams.delete("token");
    window.history.replaceState(null, "", u.pathname + u.search + u.hash);
    return true;
  } catch {
    return false;
  }
};

export const register = async (body: {
  email: string;
  password: string;
  name: string;
  whatsapp?: string;
  company?: string;
  plan: string;
  cpf_cnpj?: string;
}): Promise<{ user: any; token: string; payment_required?: boolean; invoice_url?: string }> => {
  const r = await fetch(apiUrl("/api/auth/register"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new RegisterError(r.status, data);
  if (data.token) setSession(data.token, data.user);
  return data;
};

// Erro do cadastro com o que o servidor mandou: {error, message?, field?}.
// Ex.: 400 {error, field:"cpf_cnpj"} → a tela mostra o erro embaixo do campo CPF/CNPJ.
export class RegisterError extends Error {
  status: number;
  code: string;
  field: string;
  serverMessage: string;
  constructor(status: number, data: any) {
    const code = typeof data?.error === "string" ? data.error : "";
    const serverMessage = typeof data?.message === "string" ? data.message : "";
    super(serverMessage || code || "Registration failed");
    this.status = status;
    this.code = code;
    this.field = typeof data?.field === "string" ? data.field : "";
    this.serverMessage = serverMessage;
  }
}

// --- Rotas públicas de conta (sem login) ---------------------------------------------
// Respondem {ok:true} ou {error:"mensagem"}. Devolvemos status + corpo para a tela decidir
// o texto (ex.: 404 = recurso ainda não publicado no servidor).
export type PublicResult<T = any> = { ok: boolean; status: number; data: T | null };

const publicPost = async <T = any>(path: string, body: unknown): Promise<PublicResult<T>> => {
  const r = await fetch(apiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = (await r.json().catch(() => null)) as T | null;
  return { ok: r.ok, status: r.status, data };
};

// Esqueci a senha: o servidor manda um código de 6 dígitos para o WhatsApp do cadastro.
// Sempre responde {ok:true} (não revela se o e-mail existe).
export const requestPasswordReset = (email: string) =>
  publicPost<{ ok?: boolean; error?: string; message?: string }>("/api/auth/forgot", { email: email.trim() });

export const resetPassword = (email: string, code: string, password: string) =>
  publicPost<{ ok?: boolean; error?: string; message?: string }>("/api/auth/reset", { email: email.trim(), code: code.trim(), password });

// Segundo passo do login com 2FA: responde igual a um login normal ({token, user}).
export const loginSecondFactor = (challenge: string, code: string) =>
  publicPost<any>("/api/auth/login/2fa", { challenge, code: code.trim() });
