// visao.mjs (29/10/2026) — "olhos" para modelos que NÃO recebem imagem (Sonnet web do claude.ai e Argon).
// Usado pelo proxy.mjs (:20133). Para cada imagem do pedido (inclusive dentro de tool_result, que é como o Read do
// Claude Code devolve um .png), pede ao Gemini 3.8 (gemini-fila do OmniRoute, enxerga) uma descrição fiel e INSERE
// um bloco de texto logo depois da imagem. A imagem continua no pedido: se o combo cair no Claude Code de verdade
// (que vê imagem), nada se perde. Descrição em cache por hash (o Claude Code reenvia o histórico a cada turno).
import http from "node:http";
import crypto from "node:crypto";

const UP_HOST = process.env.UP_HOST || "127.0.0.1";
const UP_PORT = +(process.env.UP_PORT || 20128);
const MODELO_OLHOS = process.env.VISAO_MODELO || "agy/gemini-3.8-flash-high";
const MARCA = "[Descrição automática da imagem acima";
const CACHE = new Map(); // hash -> texto
const CACHE_MAX = 500;

const PROMPT =
  "Descreva esta imagem para alguém que NÃO pode vê-la e precisa trabalhar com ela. Em português. " +
  "1) Transcreva LITERALMENTE todo texto visível (código, mensagens de erro, rótulos, números, URLs), mantendo quebras de linha. " +
  "2) Descreva o layout e os elementos (janelas, botões, tabelas, gráficos, pessoas, objetos) com posição e cores. " +
  "3) Aponte qualquer coisa fora do normal (erro, aviso, elemento cortado, desalinhado). " +
  "Seja fiel: não invente o que não dá para ler; diga 'ilegível' quando for o caso.";

// Modelos que não enxergam: Sonnet das contas web (cw/ e os nomes mapeados para a sonnet-fila) e a família Argon.
export function precisaOlhos(model) {
  if (typeof model !== "string") return false;
  return /^cw\//.test(model) || /claude-sonnet-5-5$/.test(model) || /argon|^gweb\//.test(model) || /^hx-/.test(model);
}

function ehImagem(b) {
  return b && ((b.type === "image" && b.source) || (b.type === "image_url" && b.image_url));
}

// Percorre mensagens: blocos de conteúdo e conteúdos aninhados de tool_result. Marca as listas de tool_result
// (`TROCAR`): ali a imagem SAI e fica só a descrição — o claude-web devolve 400 "No user message found" quando o
// resultado de ferramenta traz um bloco de imagem (teste 29/10; com só texto funciona).
const TROCAR = new WeakSet();
function listas(body) {
  const out = [];
  for (const m of body.messages || []) {
    if (!m || !Array.isArray(m.content)) continue;
    out.push(m.content);
    for (const b of m.content) {
      if (b && b.type === "tool_result" && Array.isArray(b.content)) {
        TROCAR.add(b.content);
        out.push(b.content);
      }
    }
  }
  return out;
}

export function temImagem(body) {
  return listas(body).some((l) => l.some(ehImagem));
}

function chave(b) {
  const dado = b.type === "image" ? (b.source.data || b.source.url || "") : (b.image_url.url || "");
  return crypto.createHash("sha1").update(dado).digest("hex");
}

function pedirDescricao(b, headers) {
  const img = b.type === "image" ? b
    : (() => { // OpenAI image_url -> bloco Anthropic
        const u = b.image_url.url || "";
        const m = u.match(/^data:([^;]+);base64,(.*)$/);
        return m ? { type: "image", source: { type: "base64", media_type: m[1], data: m[2] } }
          : { type: "image", source: { type: "url", url: u } };
      })();
  const corpo = Buffer.from(JSON.stringify({
    model: MODELO_OLHOS, max_tokens: 2000,
    messages: [{ role: "user", content: [img, { type: "text", text: PROMPT }] }],
  }));
  const h = { "content-type": "application/json", "anthropic-version": "2023-06-01", "content-length": String(corpo.length) };
  if (headers["x-api-key"]) h["x-api-key"] = headers["x-api-key"];
  if (headers["authorization"]) h["authorization"] = headers["authorization"];
  return new Promise((ok) => {
    const r = http.request({ host: UP_HOST, port: UP_PORT, method: "POST", path: "/v1/messages", headers: h }, (ur) => {
      const partes = [];
      ur.on("data", (c) => partes.push(c));
      ur.on("end", () => {
        try {
          const j = JSON.parse(Buffer.concat(partes).toString("utf8"));
          const t = (j.content || []).filter((x) => x.type === "text").map((x) => x.text).join("\n").trim();
          ok(t || null);
        } catch { ok(null); }
      });
    });
    r.on("error", () => ok(null));
    r.setTimeout(90000, () => { r.destroy(); ok(null); });
    r.end(corpo);
  });
}

// Insere a descrição depois de cada imagem. Devolve quantas imagens foram tratadas.
export async function descreverImagens(body, headers, log = () => {}) {
  const tarefas = [];
  for (const lista of listas(body)) {
    for (let i = 0; i < lista.length; i++) {
      const b = lista[i];
      if (!ehImagem(b)) continue;
      const prox = lista[i + 1];
      if (prox && prox.type === "text" && String(prox.text || "").startsWith(MARCA)) continue; // já descrita
      tarefas.push({ lista, b, k: chave(b) });
    }
  }
  if (!tarefas.length) return 0;
  const novas = [...new Set(tarefas.filter((t) => !CACHE.has(t.k)).map((t) => t.k))];
  const porChave = Object.fromEntries(tarefas.map((t) => [t.k, t.b]));
  const t0 = Date.now();
  await Promise.all(novas.map(async (k) => {
    const d = await pedirDescricao(porChave[k], headers);
    if (d) {
      if (CACHE.size >= CACHE_MAX) CACHE.delete(CACHE.keys().next().value);
      CACHE.set(k, d);
    }
  }));
  // insere de trás pra frente em cada lista (os índices não andam)
  for (const lista of new Set(tarefas.map((t) => t.lista))) {
    for (let i = lista.length - 1; i >= 0; i--) {
      const b = lista[i];
      if (!ehImagem(b)) continue;
      const prox = lista[i + 1];
      if (prox && prox.type === "text" && String(prox.text || "").startsWith(MARCA)) continue;
      const d = CACHE.get(chave(b));
      const bloco = { type: "text", text: d
        ? `${MARCA} (feita pelo Gemini porque este modelo não recebe a imagem)]\n${d}`
        : `${MARCA}: falhou — a imagem não pôde ser lida agora; peça para reenviar ou descrever]` };
      if (TROCAR.has(lista)) lista.splice(i, 1, bloco); // resultado de ferramenta: troca a imagem pelo texto
      else lista.splice(i + 1, 0, bloco); // mensagem normal: mantém a imagem e põe o texto depois
    }
  }
  log(`visao: ${tarefas.length} imagem(ns), ${novas.length} nova(s) descrita(s) em ${Date.now() - t0} ms`);
  return tarefas.length;
}
