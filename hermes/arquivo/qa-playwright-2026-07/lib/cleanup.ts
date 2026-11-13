// cleanup.ts — registra recursos criados durante um teste e os apaga no fim,
// mesmo que o teste falhe no meio (garante conta trial limpa entre runs).
import { apiDelete } from "./backend.js";
import type { Account } from "./session.js";

type Pending = { label: string; path: string };

// Acumulador por teste. Uso: const t = tracker(account); t.track("agente X", `/api/agent-profiles/${id}`);
export function tracker(acc: Account) {
  const pending: Pending[] = [];
  return {
    track(label: string, deletePath: string) {
      pending.push({ label, path: deletePath });
    },
    // Apaga tudo que foi registrado; devolve o resultado por item (pra log).
    async cleanupAll(): Promise<Array<{ label: string; status: number; ok: boolean }>> {
      const out: Array<{ label: string; status: number; ok: boolean }> = [];
      // Apaga em ordem inversa (ultimo criado primeiro), como um stack.
      for (const p of pending.reverse()) {
        try {
          const r = await apiDelete(acc, p.path);
          out.push({ label: p.label, status: r.status, ok: r.ok });
        } catch (e: any) {
          out.push({ label: p.label, status: -1, ok: false });
        }
      }
      pending.length = 0;
      return out;
    },
    count() { return pending.length; },
  };
}
