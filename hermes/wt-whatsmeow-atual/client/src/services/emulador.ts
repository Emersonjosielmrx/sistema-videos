import { apiGet, apiPost } from "@/lib/api";
import { apiUrl, authHeaders } from "@/lib/auth";
import { getClientId } from "@/lib/client-id";

// "Conectar sem celular": o servidor registra o numero num celular virtual (servico
// ativador) e pareia a linha. O painel so digita o numero e, quando o aviso pedir, o
// codigo de SMS que chegou. Tudo passa pelo proprio Hermes (nunca fala com o ativador).

export type EmuStatus = {
  disponivel: boolean;      // o recurso esta ligado neste servidor
  ativo?: boolean;          // ha uma ativacao em andamento para esta linha
  state?: string;           // estado do ativador (awaiting_sms, pairing, ...)
  notice?: string;          // recado que nao e erro (ex.: codigo recusado, mande outro)
  error?: string;           // erro da ativacao
  registered?: boolean;     // o numero ja entrou no WhatsApp do celular virtual
  phone?: string;           // numero sendo ativado (so digitos)
  act_id?: string;
};

export const getEmuStatus = (sid: string) =>
  apiGet<EmuStatus>(`/api/sessions/${sid}/emulador`);

export const startEmu = (sid: string, phone: string) =>
  apiPost<EmuStatus>(`/api/sessions/${sid}/emulador`, { phone });

export const sendEmuCode = async (sid: string, code: string): Promise<void> => {
  const r = await fetch(apiUrl(`/api/sessions/${sid}/emulador/codigo`), {
    method: "POST",
    headers: { "X-Client-Id": getClientId(), ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  if (!r.ok) {
    const t = await r.text().catch(() => "");
    let msg = `codigo ${r.status}`;
    try { const j = JSON.parse(t); if (j?.error) msg = j.error; } catch { /* nao-json */ }
    throw new Error(msg);
  }
};

export const cancelEmu = async (sid: string): Promise<void> => {
  const r = await fetch(apiUrl(`/api/sessions/${sid}/emulador`), {
    method: "DELETE",
    headers: { "X-Client-Id": getClientId(), ...authHeaders() },
  });
  if (!r.ok && r.status !== 404) {
    const t = await r.text().catch(() => "");
    let msg = `cancelar ${r.status}`;
    try { const j = JSON.parse(t); if (j?.error) msg = j.error; } catch { /* nao-json */ }
    throw new Error(msg);
  }
};

// Toca num ponto da tela do celular virtual (coordenadas da imagem em tamanho real).
export const tapEmu = async (sid: string, x: number, y: number): Promise<void> => {
  const r = await fetch(apiUrl(`/api/sessions/${sid}/emulador/toque`), {
    method: "POST",
    headers: { "X-Client-Id": getClientId(), ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ x: Math.round(x), y: Math.round(y) }),
  });
  if (!r.ok) {
    const t = await r.text().catch(() => "");
    let msg = `toque ${r.status}`;
    try { const j = JSON.parse(t); if (j?.error) msg = j.error; } catch { /* nao-json */ }
    throw new Error(msg);
  }
};

// Busca a tela (png) do celular virtual agora e devolve um object URL para um <img>. A
// rota exige Bearer, por isso nao da para apontar o <img> direto nela. Quem chama precisa
// dar URL.revokeObjectURL no valor antigo para nao vazar memoria.
export const fetchEmuScreen = async (sid: string): Promise<string> => {
  const r = await fetch(apiUrl(`/api/sessions/${sid}/emulador/tela`), {
    headers: { "X-Client-Id": getClientId(), ...authHeaders() },
  });
  if (!r.ok) {
    const t = await r.text().catch(() => "");
    let msg = `tela ${r.status}`;
    try { const j = JSON.parse(t); if (j?.error) msg = j.error; } catch { /* nao-json */ }
    throw new Error(msg);
  }
  return URL.createObjectURL(await r.blob());
};
