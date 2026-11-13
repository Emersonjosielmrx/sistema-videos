import { getApiBase, getApiKey } from "./auth";
import type { CallStatus } from "@/types/call";
import type { SessionInfo, SessionState } from "@/types/session";

type CallListRow = {
  sessionId: string;
  callId: string;
  owner: string | null;
  direction: "outbound" | "inbound";
  peer: string;
  startedAt: number;
  status: CallStatus;
  endedAt?: number;
  endReason?: string;
};

export type BrokerEvent =
  | { type: "session-list"; sessions: SessionInfo[] }
  | { type: "session-qr"; sessionId: string; qr: string }
  | { type: "auth-state"; sessionId: string; paired: boolean; state: SessionState; connected: boolean; qr?: string; passkey?: unknown }
  | { type: "call-list"; calls: CallListRow[] }
  | { type: "call-status"; sessionId: string; id: string; owner: string | null; status: CallStatus; peer: string; startedAt: number }
  | { type: "call-ended"; sessionId: string; id: string; owner: string | null; reason: string; endedAt: number }
  | { type: "incoming"; sessionId: string; id: string; peer: string; offeredAt: number }
  | { type: "incoming-claimed"; sessionId: string; id: string; owner: string }
  | { type: "call-admin-summon"; callId: string; sid: string; phone: string; reason: string; summary: string; channel: string; mode: string; on?: string };

type Listener = (ev: BrokerEvent) => void;

class EventStream {
  #es: EventSource | null = null;
  #listeners = new Set<Listener>();
  #clientId = "";
  #retryMs = 2000;
  #retryTimer: ReturnType<typeof setTimeout> | null = null;

  connect(clientId: string): void {
    if (this.#es) return;
    this.#clientId = clientId;
    // JWT vai na query porque EventSource não aceita header de auth (limitação do navegador).
    const apiKey = getApiKey();
    const url = `${getApiBase()}/api/events?clientId=${encodeURIComponent(clientId)}&apiKey=${encodeURIComponent(apiKey)}`;
    const es = new EventSource(url);
    this.#es = es;
    es.onopen = () => { this.#retryMs = 2000; };
    es.onmessage = (ev) => {
      try {
        const parsed: BrokerEvent = JSON.parse(ev.data);
        for (const l of this.#listeners) l(parsed);
      } catch (e) {
        console.warn("[eventStream] evento inválido", e);
      }
    };
    // Queda de rede o navegador reconecta sozinho; mas se o servidor recusar (restart,
    // publicação nova, 401) o EventSource FECHA de vez e o painel parava de atualizar
    // sem aviso. Reabre com espera crescente (2s → 60s).
    es.onerror = () => {
      if (es.readyState !== EventSource.CLOSED || this.#es !== es) return;
      this.#es = null;
      if (this.#retryTimer) clearTimeout(this.#retryTimer);
      this.#retryTimer = setTimeout(() => {
        this.#retryTimer = null;
        if (getApiKey()) this.connect(this.#clientId);
      }, this.#retryMs);
      this.#retryMs = Math.min(this.#retryMs * 2, 60000);
    };
  }

  on(l: Listener): () => void {
    this.#listeners.add(l);
    return () => this.#listeners.delete(l);
  }

  close(): void {
    if (this.#retryTimer) clearTimeout(this.#retryTimer);
    this.#retryTimer = null;
    this.#es?.close();
    this.#es = null;
  }
}

export const eventStream = new EventStream();
