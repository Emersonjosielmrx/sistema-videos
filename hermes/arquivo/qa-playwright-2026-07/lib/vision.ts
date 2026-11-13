// vision.ts — verificacao semantica de screenshots via Gemini (proxy OmniRoute).
// O proxy e OpenAI-compat mas SEMPRE responde em SSE, mesmo com stream:false.
// Por isso lemos os chunks "data:" na mao.
import { readFileSync } from "node:fs";
import { VISION } from "../config.js";

type AskResult = { ok: boolean; text: string; status: number; model: string };

async function callModel(model: string, prompt: string, pngPath?: string): Promise<AskResult> {
  const content: any[] = [{ type: "text", text: prompt }];
  if (pngPath) {
    const b64 = readFileSync(pngPath).toString("base64");
    content.push({ type: "image_url", image_url: { url: "data:image/png;base64," + b64 } });
  }
  const r = await fetch(VISION.baseUrl + "/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model, stream: true, max_tokens: 300, messages: [{ role: "user", content }] }),
  });
  const raw = await r.text();
  let out = "";
  for (const line of raw.split("\n")) {
    if (!line.startsWith("data:")) continue;
    const d = line.slice(5).trim();
    if (d === "[DONE]" || !d) continue;
    try {
      const j = JSON.parse(d);
      out += j.choices?.[0]?.delta?.content || j.choices?.[0]?.message?.content || "";
    } catch { /* chunk parcial, ignora */ }
  }
  return { ok: r.status === 200 && out.trim() !== "", text: out.trim(), status: r.status, model };
}

// Tenta o modelo principal e cai pros fallbacks se der 503 / vazio.
async function ask(prompt: string, pngPath?: string): Promise<AskResult> {
  const models = [VISION.model, ...VISION.fallbackModels];
  let last: AskResult = { ok: false, text: "", status: 0, model: "" };
  for (const m of models) {
    try {
      last = await callModel(m, prompt, pngPath);
      if (last.ok) return last;
    } catch (e: any) {
      last = { ok: false, text: String(e?.message || e), status: -1, model: m };
    }
  }
  return last;
}

// verifySemantic — pergunta ao modelo se o screenshot bate com a expectativa.
// Retorna {pass, verdict, raw}. Se a visao estiver desligada, pass=null (pula).
export async function verifySemantic(
  pngPath: string,
  expectation: string,
): Promise<{ pass: boolean | null; verdict: string; raw: string }> {
  if (!VISION.enabled) return { pass: null, verdict: "SKIP (visao desligada)", raw: "" };
  const prompt =
    `Voce e um QA analisando um screenshot de um painel web.\n` +
    `EXPECTATIVA: ${expectation}\n\n` +
    `A tela cumpre a expectativa? Responda estritamente em JSON:\n` +
    `{"pass": true|false, "motivo": "curto, em portugues"}`;
  const res = await ask(prompt, pngPath);
  if (!res.ok) return { pass: false, verdict: `ERRO visao [${res.status}] ${res.model}`, raw: res.text };
  const m = res.text.match(/\{[\s\S]*\}/);
  if (m) {
    try {
      const j = JSON.parse(m[0]);
      return { pass: !!j.pass, verdict: (j.pass ? "PASS: " : "FAIL: ") + (j.motivo || ""), raw: res.text };
    } catch { /* cai pro heuristico */ }
  }
  const pass = /"?pass"?\s*[:=]\s*true/i.test(res.text) || /\bpass\b/i.test(res.text);
  return { pass, verdict: res.text.slice(0, 200), raw: res.text };
}

export const visionAsk = ask;
