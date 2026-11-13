// backend.ts — cliente HTTP autenticado pros GET/DELETE de VERIFICACAO e CLEANUP.
// A regra do dono: nao confiar so' na UI — reler no backend com o token do usuario
// pra confirmar que o efeito realmente aconteceu. Multi-tenant: o token so' ve/apaga
// o proprio dado. Endpoints mapeados do backend Go (httpapi.go).
import { BASE_URL } from "../config.js";
import type { Account } from "./session.js";

async function req(acc: Account, method: string, path: string, body?: any) {
  const r = await fetch(BASE_URL + path, {
    method,
    headers: {
      Authorization: "Bearer " + acc.token,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  let data: any = null;
  const txt = await r.text();
  try { data = txt ? JSON.parse(txt) : null; } catch { data = txt; }
  return { status: r.status, ok: r.ok, data };
}

export const apiGet = (acc: Account, path: string) => req(acc, "GET", path);
export const apiPost = (acc: Account, path: string, body?: any) => req(acc, "POST", path, body);
export const apiPut = (acc: Account, path: string, body?: any) => req(acc, "PUT", path, body);
export const apiDelete = (acc: Account, path: string) => req(acc, "DELETE", path);

// ---- Helpers de READ-BACK (confirmar que persistiu) ----
export const listAgents = (acc: Account) => apiGet(acc, "/api/agent-profiles");        // {profiles:[...]}
export const listCredentials = (acc: Account) => apiGet(acc, "/api/credentials");      // {credentials:[...]}
export const listKeys = (acc: Account) => apiGet(acc, "/api/keys");                    // {keys:[...]}
export const getSettings = (acc: Account) => apiGet(acc, "/api/settings");             // todos os blocos
export const getManagerWizard = (acc: Account) => apiGet(acc, "/api/easy-manager/wizard"); // {config:{...}}
export const listStages = (acc: Account) => apiGet(acc, "/api/crm/board");             // {stages:[...],leads:{}}
export const listAppointments = (acc: Account) =>
  apiGet(acc, "/api/agenda/appointments?from=2000-01-01&to=2100-01-01");               // {appointments:[...]}
export const listProducts = (acc: Account) => apiGet(acc, "/api/catalog/products");    // {products:[...]}
export const listFollowups = (acc: Account) => apiGet(acc, "/api/followup/sequences"); // {rules:[...]}

// Extrai o array de um envelope conhecido ({profiles}/{credentials}/etc) ou array puro.
export function pickArray(data: any, ...keys: string[]): any[] {
  if (Array.isArray(data)) return data;
  for (const k of keys) if (Array.isArray(data?.[k])) return data[k];
  return [];
}
