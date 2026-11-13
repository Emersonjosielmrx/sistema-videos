// e2e-zzz-clean.spec.ts — roda por ULTIMO (ordem alfabetica "zzz"): confirma que a
// conta trial ficou LIMPA depois de todos os ciclos criar/verificar/limpar.
// Remove qualquer residuo QA_* que tenha escapado e reporta o estado.
import { test, expect } from "@playwright/test";
import { createTrialAccount, type Account } from "../lib/session.js";
import { listAgents, listCredentials, listKeys, listProducts, listAppointments, listFollowups, apiDelete, pickArray } from "../lib/backend.js";

let account: Account;
test.beforeAll(async () => { test.setTimeout(120_000); account = await createTrialAccount(); });

test("conta trial esta' limpa de residuos QA_* (varre e remove sobras)", async ({}, info) => {
  const isQa = (x: any) => /^QA[_ ]/i.test(x?.name || x?.label || "");
  const sweeps: Array<{ area: string; list: () => Promise<any>; key: string; del: (id: string) => string }> = [
    { area: "agentes", list: () => listAgents(account), key: "profiles", del: (id) => `/api/agent-profiles/${id}` },
    { area: "credenciais", list: () => listCredentials(account), key: "credentials", del: (id) => `/api/credentials/${id}` },
    { area: "chaves", list: () => listKeys(account), key: "keys", del: (id) => `/api/keys/${id}` },
    { area: "produtos", list: () => listProducts(account), key: "products", del: (id) => `/api/catalog/products/${id}` },
    { area: "eventos", list: () => listAppointments(account), key: "appointments", del: (id) => `/api/agenda/appointments/${id}` },
    { area: "followups", list: () => listFollowups(account), key: "rules", del: (id) => `/api/followup/sequences/${id}` },
  ];
  const report: string[] = [];
  for (const s of sweeps) {
    const r = await s.list();
    const residuos = pickArray(r.data, s.key).filter(isQa);
    for (const item of residuos) await apiDelete(account, s.del(item.id));
    report.push(`${s.area}: ${residuos.length} residuo(s) removido(s)`);
  }
  info.annotations.push({ type: "cleanup-final", description: report.join(" | ") });
  // Revarre e confirma zero residuos QA_*.
  let sobrou = 0;
  for (const s of sweeps) {
    const r = await s.list();
    sobrou += pickArray(r.data, s.key).filter(isQa).length;
  }
  expect(sobrou, "conta deveria ficar sem residuos QA_*").toBe(0);
});
