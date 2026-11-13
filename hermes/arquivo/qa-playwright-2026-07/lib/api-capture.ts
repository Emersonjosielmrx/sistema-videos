// api-capture.ts — captura chamadas de API que a UI dispara ao clicar um botao.
// A forma mais robusta de provar "esse botao faz o que promete" e' confirmar que
// ele dispara o endpoint certo e recebe 2xx — sem depender de texto de tela ou de
// navegar wizards multi-step fragilmente.
import type { Page, Request, Response } from "@playwright/test";

export type ApiHit = { method: string; url: string; status: number; ok: boolean };

// Observa chamadas /api/* que casem com `pathRe` enquanto `action` roda.
// Retorna todas as que dispararam (com status da resposta).
export async function captureApi(
  page: Page,
  pathRe: RegExp,
  action: () => Promise<void>,
  waitMs = 6000,
): Promise<ApiHit[]> {
  const hits: ApiHit[] = [];
  const pending = new Set<Request>();
  const onReq = (req: Request) => {
    if (req.url().includes("/api/") && pathRe.test(req.url())) pending.add(req);
  };
  const onResp = (resp: Response) => {
    const req = resp.request();
    if (pending.has(req)) {
      hits.push({ method: req.method(), url: resp.url(), status: resp.status(), ok: resp.ok() });
      pending.delete(req);
    }
  };
  page.on("request", onReq);
  page.on("response", onResp);
  try {
    await action();
    // espera as respostas chegarem
    const t0 = Date.now();
    while (pending.size > 0 && Date.now() - t0 < waitMs) {
      await page.waitForTimeout(200);
    }
    // margem extra pra chamadas disparadas tardiamente
    await page.waitForTimeout(800);
  } finally {
    page.off("request", onReq);
    page.off("response", onResp);
  }
  return hits;
}
