// e2e-data.spec.ts — Etapa 5: CRM, Agenda, Vitrine do comeco ao fim.
// Ciclo criar -> verificar no BACKEND (GET) -> limpar (DELETE). Payloads validados ao vivo.
import { test, expect } from "@playwright/test";
import { createTrialAccount, type Account } from "../lib/session.js";
import { apiPost, listStages, listAppointments, listProducts, pickArray } from "../lib/backend.js";
import { tracker } from "../lib/cleanup.js";

let account: Account;
test.beforeAll(async () => { test.setTimeout(180_000); account = await createTrialAccount(); });

test.describe("Dados — criar, verificar no backend, limpar", () => {
  test("CRM: criar etapa -> aparece em GET /api/crm/board -> deletar", async ({}, info) => {
    const t = tracker(account);
    const name = "QA_Etapa_" + Date.now();
    const created = await apiPost(account, "/api/crm/stages", { name });
    expect(created.ok, `create etapa falhou: ${JSON.stringify(created)}`).toBeTruthy();
    const id = created.data?.id;
    expect(id).toBeTruthy();
    t.track("etapa " + name, `/api/crm/stages/${id}`);

    const back = await listStages(account);
    const stages = pickArray(back.data, "stages");
    expect(stages.find((s: any) => s.id === id || s.name === name), "etapa deveria aparecer no board").toBeTruthy();
    info.annotations.push({ type: "backend", description: `etapa ${id} confirmada no board` });

    const cleaned = await t.cleanupAll();
    info.annotations.push({ type: "cleanup", description: JSON.stringify(cleaned) });
    const back2 = await listStages(account);
    expect(pickArray(back2.data, "stages").find((s: any) => s.id === id), "etapa deveria sumir").toBeFalsy();
  });

  test("Agenda: criar evento -> aparece em GET /api/agenda/appointments -> deletar", async ({}, info) => {
    const t = tracker(account);
    const name = "QA_Evento_" + Date.now();
    const start = new Date(Date.now() + 86_400_000).toISOString();
    const created = await apiPost(account, "/api/agenda/appointments", { name, start_at: start });
    expect(created.ok, `create evento falhou: ${JSON.stringify(created)}`).toBeTruthy();
    const id = created.data?.id;
    expect(id).toBeTruthy();
    t.track("evento " + name, `/api/agenda/appointments/${id}`);

    const back = await listAppointments(account);
    const appts = pickArray(back.data, "appointments");
    expect(appts.find((a: any) => a.id === id || a.name === name), "evento deveria aparecer na agenda").toBeTruthy();
    info.annotations.push({ type: "backend", description: `evento ${id} confirmado` });

    const cleaned = await t.cleanupAll();
    info.annotations.push({ type: "cleanup", description: JSON.stringify(cleaned) });
    const back2 = await listAppointments(account);
    expect(pickArray(back2.data, "appointments").find((a: any) => a.id === id), "evento deveria sumir").toBeFalsy();
  });

  test("Vitrine: criar produto -> aparece em GET /api/catalog/products -> deletar", async ({}, info) => {
    const t = tracker(account);
    const name = "QA_Produto_" + Date.now();
    const created = await apiPost(account, "/api/catalog/products", { name, price: 99.9 });
    expect(created.ok, `create produto falhou: ${JSON.stringify(created)}`).toBeTruthy();
    const id = created.data?.id;
    expect(id).toBeTruthy();
    t.track("produto " + name, `/api/catalog/products/${id}`);

    const back = await listProducts(account);
    const prods = pickArray(back.data, "products");
    expect(prods.find((p: any) => p.id === id || p.name === name), "produto deveria aparecer na vitrine").toBeTruthy();
    info.annotations.push({ type: "backend", description: `produto ${id} confirmado` });

    const cleaned = await t.cleanupAll();
    info.annotations.push({ type: "cleanup", description: JSON.stringify(cleaned) });
    // Catalog e' soft-delete (vai pra lixeira) — some da lista principal.
    const back2 = await listProducts(account);
    expect(pickArray(back2.data, "products").find((p: any) => p.id === id), "produto deveria sumir da lista").toBeFalsy();
  });
});
