// cline-ponte (29/10/2026)
// Modelo "cline-..." do Claude Code -> API da Cline (api.cline.bot) usando o LOGIN QUE JA ESTA NO CLINE
// (~/.cline/data/settings/providers.json). O login nunca sai deste PC: a ponte le o arquivo a cada pedido e,
// quando o token vai vencer, renova do mesmo jeito que o Cline (POST /api/v1/auth/refresh) e grava de volta
// no mesmo arquivo, entao o Cline continua logado.
// Caminho: Claude Code -> proxy 20133 (VPS 157) -> tunel ssh -R (127.0.0.1:20160 na VPS) -> esta ponte -> Cline.
// Traduz Anthropic /v1/messages <-> OpenAI chat/completions (streaming, ferramentas, raciocinio, imagem, cache).
// Este processo tambem mantem o tunel aberto (ssh sem janela, refaz se cair).
import http from "node:http";
import https from "node:https";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const PASTA = path.dirname(fileURLToPath(import.meta.url));
const CONFIG = JSON.parse(fs.readFileSync(path.join(PASTA, "config.json"), "utf8"));
const PORTA = CONFIG.porta || 20160;
const CLINE = path.join(os.homedir(), ".cline", "data");
const PROVIDERS = path.join(CLINE, "settings", "providers.json");
const GLOBAL = path.join(CLINE, "globalState.json");
const API = "https://api.cline.bot/api/v1";
const ANTHROPIC = "https://api.anthropic.com";
const LOG = path.join(PASTA, "ponte.log");

// Qual provedor o Cline esta usando de verdade (o mesmo que a dona ve no Cline).
// "anthropic" = chave sk-ant dela (vai direto pra Anthropic, NAO gasta credito Cline);
// "cline" = login de creditos Cline (api.cline.bot).
function provedorAtivo() {
  try {
    const g = JSON.parse(fs.readFileSync(GLOBAL, "utf8"));
    return g.actModeApiProvider || g.planModeApiProvider || "anthropic";
  } catch { return "anthropic"; }
}

function chaveAnthropic() {
  const j = JSON.parse(fs.readFileSync(PROVIDERS, "utf8"));
  const k = j?.providers?.anthropic?.settings?.apiKey;
  if (!k) throw new Error("Cline sem chave Anthropic (abra o Cline e configure a chave sk-ant no provedor Anthropic)");
  return k;
}

function log(...a) {
  const linha = new Date().toISOString() + " " + a.join(" ") + "\n";
  try {
    if (fs.existsSync(LOG) && fs.statSync(LOG).size > 5e6) fs.renameSync(LOG, LOG + ".1");
    fs.appendFileSync(LOG, linha);
  } catch {}
}

// ---------- login do Cline ----------
function lerLogin() {
  const j = JSON.parse(fs.readFileSync(PROVIDERS, "utf8"));
  const auth = j?.providers?.cline?.settings?.auth;
  if (!auth?.accessToken) throw new Error("Cline sem login (abra o Cline e entre na conta Cline)");
  return { j, auth };
}

let renovando = null;
async function token(forcar = false) {
  const { auth } = lerLogin();
  if (!forcar && auth.expiresAt - Date.now() > 120000) return auth.accessToken;
  if (!renovando) renovando = renovar(auth.accessToken).finally(() => { renovando = null; });
  return renovando;
}

async function renovar(tokenVelho) {
  // rele: o Cline pode ter renovado sozinho agora
  const { j, auth } = lerLogin();
  if (auth.accessToken !== tokenVelho && auth.expiresAt - Date.now() > 120000) return auth.accessToken;
  const r = await fetch(API + "/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refreshToken: auth.refreshToken, grantType: "refresh_token" }),
    signal: AbortSignal.timeout(30000),
  });
  const txt = await r.text();
  if (!r.ok) throw new Error("renovar login do Cline falhou " + r.status + ": " + txt.slice(0, 300));
  const d = JSON.parse(txt);
  const t = d.data ?? d;
  if (!t.accessToken) throw new Error("renovar login: resposta sem accessToken: " + txt.slice(0, 300));
  const exp = typeof t.expiresAt === "number" ? t.expiresAt : Date.parse(t.expiresAt);
  // o Cline guarda e envia o token com o prefixo "workos:" (sem ele a API responde 401)
  auth.accessToken = /^workos:/i.test(t.accessToken) ? t.accessToken : "<SEGREDO_REMOVIDO>" + t.accessToken;
  if (t.refreshToken) auth.refreshToken = t.refreshToken;
  if (exp) auth.expiresAt = exp;
  if (t.userInfo && auth.metadata) auth.metadata.userInfo = t.userInfo;
  j.providers.cline.updatedAt = new Date().toISOString();
  const tmp = PROVIDERS + ".ponte-tmp";
  fs.writeFileSync(tmp, JSON.stringify(j, null, 2));
  fs.renameSync(tmp, PROVIDERS);
  log("login do Cline renovado, vence", new Date(auth.expiresAt).toISOString());
  return auth.accessToken;
}

// ---------- nome do modelo ----------
// cline-opus-5-5 -> anthropic/claude-opus-5.5 ; cline/anthropic/x -> anthropic/x
function modeloCline(m) {
  let s = String(m || "").replace(/^cline[-/]/, "");
  if (s.includes("/")) return s;
  if (!s.startsWith("claude-")) s = "claude-" + s;
  return "anthropic/" + s.replace(/-(\d+)-(\d+)$/, "-$1.$2");
}

// ---------- Anthropic -> OpenAI ----------
function parteTexto(b) {
  const p = { type: "text", text: b.text ?? "" };
  if (b.cache_control) p.cache_control = b.cache_control;
  return p;
}

function parteImagem(b) {
  const s = b.source || {};
  const url = s.type === "base64" ? `data:${s.media_type};base64,${s.data}` : s.url;
  return { type: "image_url", image_url: { url } };
}

function conteudoResultado(c) {
  if (typeof c === "string") return { partes: [{ type: "text", text: c }], imagens: [] };
  const partes = [], imagens = [];
  for (const b of c || []) {
    if (b.type === "text") partes.push(parteTexto(b));
    else if (b.type === "image") imagens.push(parteImagem(b));
  }
  if (!partes.length) partes.push({ type: "text", text: imagens.length ? "(imagem abaixo)" : "" });
  return { partes, imagens };
}

function paraOpenAI(body) {
  const msgs = [];
  if (body.system) {
    const partes = typeof body.system === "string" ? [{ type: "text", text: body.system }] : body.system.map(parteTexto);
    msgs.push({ role: "system", content: partes });
  }
  for (const m of body.messages || []) {
    const blocos = typeof m.content === "string" ? [{ type: "text", text: m.content }] : m.content || [];
    if (m.role === "assistant") {
      const textos = [], chamadas = [], raciocinio = [];
      for (const b of blocos) {
        if (b.type === "text" && b.text) textos.push(b.text);
        else if (b.type === "tool_use") chamadas.push({ id: b.id, type: "function", function: { name: b.name, arguments: JSON.stringify(b.input ?? {}) } });
        else if (b.type === "thinking") raciocinio.push({ type: "reasoning.text", text: b.thinking, signature: b.signature, format: "anthropic-claude-v1", index: raciocinio.length });
        else if (b.type === "redacted_thinking") raciocinio.push({ type: "reasoning.encrypted", data: b.data, format: "anthropic-claude-v1", index: raciocinio.length });
      }
      const a = { role: "assistant", content: textos.length ? textos.join("\n\n") : (chamadas.length ? null : "") };
      if (chamadas.length) a.tool_calls = chamadas;
      if (raciocinio.length) a.reasoning_details = raciocinio;
      msgs.push(a);
      continue;
    }
    // usuario: resultados de ferramenta viram mensagens "tool" (logo depois do assistente), o resto vem depois
    const partes = [], imagensDepois = [];
    for (const b of blocos) {
      if (b.type === "tool_result") {
        const { partes: p, imagens } = conteudoResultado(b.content);
        if (b.is_error) p.unshift({ type: "text", text: "[erro]" });
        const temCache = p.some((x) => x.cache_control) || b.cache_control;
        if (b.cache_control) p[p.length - 1].cache_control = b.cache_control;
        msgs.push({ role: "tool", tool_call_id: b.tool_use_id, content: temCache ? p : p.map((x) => x.text).join("\n") });
        imagensDepois.push(...imagens);
      } else if (b.type === "text") partes.push(parteTexto(b));
      else if (b.type === "image") partes.push(parteImagem(b));
      else if (b.type === "document" && b.source?.type === "text") partes.push({ type: "text", text: b.source.data });
    }
    if (imagensDepois.length) partes.unshift({ type: "text", text: "Imagens dos resultados das ferramentas:" }, ...imagensDepois);
    if (partes.length) msgs.push({ role: "user", content: partes });
  }

  const o = { model: modeloCline(body.model), messages: msgs, stream: true, stream_options: { include_usage: true } };
  if (body.max_tokens) o.max_tokens = body.max_tokens;
  if (body.stop_sequences?.length) o.stop = body.stop_sequences;
  const th = body.thinking;
  if (th?.type === "enabled") o.reasoning = { max_tokens: th.budget_tokens || 8000 };
  else if (th?.type === "adaptive") {
    const e = body.output_config?.effort || "medium";
    o.reasoning = { effort: ["low", "medium", "high"].includes(e) ? e : "high" };
  } else {
    if (body.temperature != null) o.temperature = body.temperature;
    if (body.top_p != null) o.top_p = body.top_p;
  }
  const ferramentas = (body.tools || []).filter((t) => t.input_schema);
  if (ferramentas.length) {
    o.tools = ferramentas.map((t) => {
      const f = { type: "function", function: { name: t.name, description: t.description || "", parameters: t.input_schema } };
      if (t.cache_control) f.cache_control = t.cache_control;
      return f;
    });
    const tc = body.tool_choice;
    if (tc?.type === "any") o.tool_choice = "required";
    else if (tc?.type === "tool") o.tool_choice = { type: "function", function: { name: tc.name } };
    else if (tc?.type === "none") o.tool_choice = "none";
    if (tc?.disable_parallel_tool_use) o.parallel_tool_calls = false;
  }
  return o;
}

// ---------- OpenAI (streaming) -> eventos Anthropic ----------
const PARADA = { stop: "end_turn", tool_calls: "tool_use", length: "max_tokens", content_filter: "refusal",
  end_turn: "end_turn", tool_use: "tool_use", max_tokens: "<SEGREDO_REMOVIDO>", stop_sequence: "stop_sequence", refusal: "refusal" };

class Tradutor {
  constructor(modelo, emitir) {
    this.emitir = emitir;
    this.idx = -1;
    this.tipo = null;
    this.ferr = new Map(); // indice openai -> indice do bloco
    this.parada = null;
    this.uso = null;
    this.emitir("message_start", { type: "message_start", message: { id: "msg_cline_" + Date.now().toString(36), type: "message",
      role: "assistant", model: modelo, content: [], stop_reason: null, stop_sequence: null,
      usage: { input_tokens: 0, output_tokens: 0, cache_creation_input_tokens: 0, cache_read_input_tokens: 0 } } });
  }
  fechar() {
    if (this.tipo) this.emitir("content_block_stop", { type: "content_block_stop", index: this.idx });
    this.tipo = null;
  }
  abrir(tipo, bloco) {
    this.fechar();
    this.idx++;
    this.tipo = tipo;
    this.emitir("content_block_start", { type: "content_block_start", index: this.idx, content_block: bloco });
  }
  delta(d) { this.emitir("content_block_delta", { type: "content_block_delta", index: this.idx, delta: d }); }

  pedaco(c) {
    if (c.usage) this.uso = c.usage;
    const ch = c.choices?.[0];
    if (!ch) return;
    const d = ch.delta || {};
    const detalhes = Array.isArray(d.reasoning_details) ? d.reasoning_details : null;
    if (detalhes?.length) {
      for (const r of detalhes) {
        if (r.type === "reasoning.encrypted") {
          this.abrir("redacted", { type: "redacted_thinking", data: r.data || "" });
          this.fechar();
          continue;
        }
        const txt = r.type === "reasoning.summary" ? r.summary : r.text;
        if (this.tipo !== "thinking") this.abrir("thinking", { type: "thinking", thinking: "", signature: "" });
        if (txt) this.delta({ type: "thinking_delta", thinking: txt });
        if (r.signature) this.delta({ type: "signature_delta", signature: r.signature });
      }
    } else if (d.reasoning) {
      if (this.tipo !== "thinking") this.abrir("thinking", { type: "thinking", thinking: "", signature: "" });
      this.delta({ type: "thinking_delta", thinking: d.reasoning });
    }
    if (d.content) {
      if (this.tipo !== "text") this.abrir("text", { type: "text", text: "" });
      this.delta({ type: "text_delta", text: d.content });
    }
    for (const t of d.tool_calls || []) {
      const i = t.index ?? 0;
      if (!this.ferr.has(i) || (t.id && this.ferr.get(i).id !== t.id)) {
        const id = t.id || "toolu_cline_" + Date.now().toString(36) + i;
        this.abrir("tool", { type: "tool_use", id, name: t.function?.name || "", input: {} });
        this.ferr.set(i, { id, bloco: this.idx });
      }
      const a = t.function?.arguments;
      if (a && this.ferr.get(i).bloco === this.idx) this.delta({ type: "input_json_delta", partial_json: a });
    }
    const fim = ch.native_finish_reason || ch.finish_reason;
    if (fim) this.parada = PARADA[fim] || "end_turn";
  }

  terminar() {
    this.fechar();
    const u = this.uso || {};
    const lido = u.prompt_tokens_details?.cached_tokens || 0;
    const escrito = u.prompt_tokens_details?.cache_write_tokens || 0;
    this.emitir("message_delta", { type: "message_delta",
      delta: { stop_reason: this.parada || (this.ferr.size ? "tool_use" : "end_turn"), stop_sequence: null },
      usage: { input_tokens: Math.max(0, (u.prompt_tokens || 0) - lido - escrito), output_tokens: u.completion_tokens || 0,
        cache_read_input_tokens: lido, cache_creation_input_tokens: escrito } });
    this.emitir("message_stop", { type: "message_stop" });
  }
}

// junta os eventos numa mensagem so (pedido sem stream)
function juntar(eventos) {
  let msg = null;
  for (const [, e] of eventos) {
    if (e.type === "message_start") msg = e.message;
    else if (e.type === "content_block_start") msg.content[e.index] = { ...e.content_block, _json: "" };
    else if (e.type === "content_block_delta") {
      const b = msg.content[e.index], d = e.delta;
      if (d.type === "text_delta") b.text += d.text;
      else if (d.type === "thinking_delta") b.thinking += d.thinking;
      else if (d.type === "signature_delta") b.signature += d.signature;
      else if (d.type === "input_json_delta") b._json += d.partial_json;
    } else if (e.type === "message_delta") { msg.stop_reason = e.delta.stop_reason; msg.usage = e.usage; }
  }
  for (const b of msg.content) {
    if (b.type === "tool_use") { try { b.input = b._json ? JSON.parse(b._json) : {}; } catch { b.input = {}; } }
    delete b._json;
  }
  return msg;
}

function erroAnthropic(res, status, msg) {
  const tipo = status === 401 ? "authentication_error" : status === 429 ? "rate_limit_error" : status === 400 ? "invalid_request_error"
    : status === 404 ? "not_found_error" : status >= 500 ? "api_error" : "invalid_request_error";
  if (!res.headersSent) res.writeHead(status, { "content-type": "application/json" });
  res.end(JSON.stringify({ type: "error", error: { type: tipo, message: "cline-ponte: " + msg } }));
}

async function chamarCline(o, sinal, tentouRenovar = false) {
  let t = await token(tentouRenovar);
  if (!/^workos:/i.test(t)) t = "workos:" + t;
  const r = await fetch(API + "/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + t, "HTTP-Referer": "https://cline.bot", "X-Title": "Cline" },
    body: JSON.stringify(o),
    signal: sinal,
  });
  if (r.status === 401 && !tentouRenovar) { await r.text().catch(() => ""); return chamarCline(o, sinal, true); }
  return r;
}

// cline-opus-5-5 -> claude-opus-5-5 (so tira o prefixo cline-)
function modeloAnthropic(m) {
  let s = String(m || "").replace(/^cline-/, "");
  if (!s.startsWith("claude-")) s = "claude-" + s;
  return s;
}

// 29/10: a Anthropic tambem reconhece o Claude Code pela assinatura DENTRO do prompt de sistema
// ("x-anthropic-billing-header: ..." e "You are Claude Code, Anthropic's official CLI for Claude.") e cobra
// pelo caminho Claude Code (sem credito) -> "credit balance is too low". Tira essas linhas (mesma lista do proxy 20133).
// Linha de billing: some inteira. Frase de identidade (qualquer variante, inclusive "..., running within the Claude Agent SDK."):
// tira so a frase, ate o primeiro ponto, e mantem o resto da linha (prompts de subagentes seguem com "Given the user's message, ...").
const BILLING_CC = /^x-anthropic-billing-header:/i;
const FRASE_CC = /^You are (a )?Claude (Code|agent)\b[^.]*\.\s*/i;
// 29/10: sem o beta claude-code, a Anthropic confere a assinatura dos blocos de thinking contra o prefixo EXATO da
// conversa ("The system prompt differs from the one this block was created with"); como o prompt de sistema do Claude
// Code muda entre turnos, pedimos "drop_block" (descarta o bloco velho em vez de responder 400). Exige este beta.
const BETA_BINDING = "thinking-binding-controls-2026-08-01";
// Diagnostico quando a Anthropic recusa: o que de assinatura ainda sobrou no system e quais headers foram.
function diagAssinatura(buf, headers, erroTxt) {
  try {
    const j = JSON.parse(buf.toString("utf8"));
    const s = j.system;
    const txt = typeof s === "string" ? s : Array.isArray(s) ? s.map((b) => (b && b.text) || "").join("\n") : "";
    const linhas = txt.split("\n").filter((l) => /billing|claude code|claude agent|agent sdk/i.test(l)).slice(0, 6);
    // qual bloco a Anthropic apontou (messages.N.content.K) e se e o do ultimo turno do assistente
    let bloco = null;
    const m = /messages\.(\d+)\.content\.(\d+)/.exec(String(erroTxt || ""));
    if (m && Array.isArray(j.messages)) {
      const i = +m[1], k = +m[2], msg = j.messages[i];
      const b = msg && Array.isArray(msg.content) ? msg.content[k] : null;
      let ultimo = -1; for (let x = 0; x < j.messages.length; x++) if (j.messages[x] && j.messages[x].role === "assistant") ultimo = x;
      bloco = { i, k, role: msg && msg.role, tipo: b && b.type, thinkingLen: b && typeof b.thinking === "string" ? b.thinking.length : null,
        sigLen: b && b.signature ? String(b.signature).length : null, ultimoAssistente: ultimo, totalMsgs: j.messages.length };
    }
    return JSON.stringify({ bloco, linhas, betas: headers["anthropic-beta"] || "", ua: headers["user-agent"] || "" });
  } catch (e) { return "diag erro " + e.message; }
}
function limparTexto(t) {
  return String(t).split("\n").map((l) => {
    const s = l.trim();
    if (BILLING_CC.test(s)) return null;
    if (FRASE_CC.test(s)) return s.replace(FRASE_CC, "");
    return l;
  }).filter((l) => l !== null).join("\n");
}
function limparBlocos(arr) {
  const out = [];
  for (const b of arr) {
    if (b && b.type === "text" && typeof b.text === "string") {
      const t = limparTexto(b.text);
      if (t.trim()) out.push({ ...b, text: t });
    } else out.push(b);
  }
  return out;
}
// 29/10: so o ULTIMO turno do assistente precisa devolver os blocos de thinking (a API descarta os anteriores do
// contexto de qualquer jeito). Tirar os antigos evita "Invalid signature in thinking block" em blocos la atras.
function tirarThinkingAntigo(j) {
  if (!Array.isArray(j.messages)) return;
  let ultimo = -1;
  for (let i = 0; i < j.messages.length; i++) if (j.messages[i] && j.messages[i].role === "assistant") ultimo = i;
  for (let i = 0; i < j.messages.length; i++) {
    const m = j.messages[i];
    if (!m || m.role !== "assistant" || i === ultimo || !Array.isArray(m.content)) continue;
    const c = m.content.filter((b) => !(b && (b.type === "thinking" || b.type === "redacted_thinking")));
    if (c.length) m.content = c;
  }
}
function limparAssinaturaClaudeCode(j) {
  if (Array.isArray(j.system)) { const s = limparBlocos(j.system); if (s.length) j.system = s; else delete j.system; }
  else if (typeof j.system === "string") { const t = limparTexto(j.system); if (t.trim()) j.system = t; else delete j.system; }
  if (Array.isArray(j.messages)) for (const m of j.messages) {
    if (!m || m.role !== "system") continue;
    if (typeof m.content === "string") m.content = limparTexto(m.content);
    else if (Array.isArray(m.content)) m.content = limparBlocos(m.content);
  }
}

// Modo Anthropic direto: o Claude Code ja fala /v1/messages nativo; so repassamos o corpo
// para api.anthropic.com trocando a chave pela sk-ant da dona e ajustando o nome do modelo.
// Sem traducao de formato, sem gastar credito Cline.
function anthropicDireto(req, res, buf, chave) {
  // Troca o nome "cline-..." pelo nome real da Anthropic no corpo
  let corpo = buf.toString("utf8");
  let temThinking = false;
  try {
    const j = JSON.parse(corpo);
    j.model = modeloAnthropic(j.model);
    limparAssinaturaClaudeCode(j);
    tirarThinkingAntigo(j);
    if (j.thinking && typeof j.thinking === "object") {
      temThinking = true;
      if (!j.thinking.block_binding) j.thinking.block_binding = { prefix_mismatch_behavior: "drop_block" };
    }
    corpo = JSON.stringify(j); buf = Buffer.from(corpo, "utf8");
  } catch {}
  const u = new URL(ANTHROPIC + req.url);
  const headers = { ...req.headers, host: u.host, "x-api-key": chave, "content-length": Buffer.byteLength(buf) };
  delete headers.authorization;
  delete headers["accept-encoding"];
  if (!headers["anthropic-version"]) headers["anthropic-version"] = "2023-06-01";
  // 29/10: a Anthropic, ao reconhecer o pedido como "Claude Code" (beta claude-code-*/oauth-*, x-app, user-agent
  // claude-cli), cobra pelo caminho do Claude Code/assinatura — que nao tem credito — e responde "credit balance is
  // too low" mesmo com saldo na chave sk-ant. Tira a identidade: vira um pedido normal de API cobrado na chave.
  delete headers["x-app"];
  delete headers["user-agent"];
  delete headers["x-claude-code-session-id"];
  {
    const betas = String(headers["anthropic-beta"] || "").split(",").map((s) => s.trim())
      .filter((b) => b && !/^(claude-code|oauth)-/i.test(b));
    if (temThinking && !betas.includes(BETA_BINDING)) betas.push(BETA_BINDING);
    if (betas.length) headers["anthropic-beta"] = betas.join(","); else delete headers["anthropic-beta"];
  }
  const inicio = Date.now();
  https.request(u, { method: req.method, headers }, (ur) => {
    res.writeHead(ur.statusCode || 502, ur.headers);
    ur.pipe(res);
    if (ur.statusCode >= 400) {
      let t = "";
      ur.on("data", (c) => (t += c));
      ur.on("end", () => log("Anthropic respondeu", ur.statusCode, body_model(buf), t.slice(0, 300), "| diag:", diagAssinatura(buf, headers, t)));
    } else {
      ur.on("end", () => log("ok (anthropic)", body_model(buf), ((Date.now() - inicio) / 1000).toFixed(1) + "s"));
    }
  }).on("error", (e) => { log("erro Anthropic:", e.message); erroAnthropic(res, 502, e.message); })
    .end(buf);
}
function body_model(buf) { try { return JSON.parse(buf.toString("utf8")).model; } catch { return "?"; } }

async function mensagens(req, res, body) {
  const o = paraOpenAI(body);
  const controle = new AbortController();
  res.on("close", () => { if (!res.writableFinished) controle.abort(); });
  const inicio = Date.now();
  let r;
  try { r = await chamarCline(o, controle.signal); }
  catch (e) { log("erro ao chamar a Cline:", e.message); return erroAnthropic(res, 502, e.message); }
  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    let msg = txt;
    try { const j = JSON.parse(txt); msg = j.error?.message || (typeof j.error === "string" ? j.error : txt); } catch {}
    log("Cline respondeu", r.status, o.model, msg.slice(0, 300));
    return erroAnthropic(res, r.status === 402 ? 429 : r.status, msg.slice(0, 1000));
  }

  const stream = !!body.stream;
  const guardados = [];
  let ping = null;
  const emitir = stream
    ? (ev, dados) => res.write(`event: ${ev}\ndata: ${JSON.stringify(dados)}\n\n`)
    : (ev, dados) => guardados.push([ev, dados]);
  if (stream) {
    res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-cache", connection: "keep-alive" });
    ping = setInterval(() => res.write(`event: ping\ndata: {"type":"ping"}\n\n`), 15000);
  }
  const tr = new Tradutor(body.model, emitir);
  let resto = "", erro = null;
  try {
    const dec = new TextDecoder();
    for await (const pedaco of r.body) {
      resto += dec.decode(pedaco, { stream: true });
      let n;
      while ((n = resto.indexOf("\n")) >= 0) {
        const linha = resto.slice(0, n).trim();
        resto = resto.slice(n + 1);
        if (!linha.startsWith("data:")) continue;
        const dado = linha.slice(5).trim();
        if (dado === "[DONE]") continue;
        let c;
        try { c = JSON.parse(dado); } catch { continue; }
        if (c.error) { erro = c.error.message || JSON.stringify(c.error); continue; }
        tr.pedaco(c.data?.choices ? c.data : c);
      }
    }
  } catch (e) { erro = erro || e.message; }
  clearInterval(ping);
  if (controle.signal.aborted) return;
  if (erro && tr.idx < 0) {
    log("erro no streaming:", o.model, erro);
    if (stream) {
      res.write(`event: error\ndata: ${JSON.stringify({ type: "error", error: { type: "api_error", message: "cline-ponte: " + erro } })}\n\n`);
      return res.end();
    }
    return erroAnthropic(res, 502, erro);
  }
  tr.terminar();
  const u = tr.uso || {};
  log("ok", o.model, ((Date.now() - inicio) / 1000).toFixed(1) + "s", "entrada", u.prompt_tokens || 0, "cache", u.prompt_tokens_details?.cached_tokens || 0,
    "saida", u.completion_tokens || 0, erro ? "(erro no fim: " + erro + ")" : "");
  if (stream) return res.end();
  res.writeHead(200, { "content-type": "application/json" });
  res.end(JSON.stringify(juntar(guardados)));
}

// ---------- servidor ----------
function autorizado(req) {
  const k = req.headers["x-api-key"] || String(req.headers.authorization || "").replace(/^Bearer\s+/i, "");
  return (CONFIG.chaves || []).includes(k);
}

const servidor = http.createServer((req, res) => {
  if (req.method === "GET" && req.url === "/saude") {
    const ativo = provedorAtivo();
    let detalhe = ativo;
    try {
      if (ativo === "anthropic") { chaveAnthropic(); detalhe = "anthropic (chave sk-ant da dona, direto)"; }
      else { const { auth } = lerLogin(); detalhe = "cline (creditos, login vence " + new Date(auth.expiresAt).toISOString() + ")"; }
    } catch (e) { detalhe = ativo + " - " + e.message; }
    res.writeHead(200, { "content-type": "application/json" });
    return res.end(JSON.stringify({ ok: true, provedor: detalhe, tunel: tunelVivo }));
  }
  if (!autorizado(req)) return erroAnthropic(res, 401, "chave invalida");
  const partes = [];
  req.on("data", (c) => partes.push(c));
  req.on("end", () => {
    const buf = Buffer.concat(partes);
    const url = req.url || "";
    // Provedor ativo no Cline manda: anthropic = repasse direto (chave da dona); cline = creditos Cline.
    if (provedorAtivo() === "anthropic") {
      let chave;
      try { chave = chaveAnthropic(); } catch (e) { return erroAnthropic(res, 401, e.message); }
      return anthropicDireto(req, res, buf, chave);
    }
    let body;
    try { body = JSON.parse(buf.toString("utf8")); } catch { return erroAnthropic(res, 400, "JSON invalido"); }
    if (/\/messages\/count_tokens/.test(url)) {
      res.writeHead(200, { "content-type": "application/json" });
      return res.end(JSON.stringify({ input_tokens: Math.ceil(JSON.stringify({ s: body.system, m: body.messages, t: body.tools }).length / 3.5) }));
    }
    if (/\/messages(\?|$)/.test(url)) return mensagens(req, res, body).catch((e) => { log("falha:", e.stack); erroAnthropic(res, 500, e.message); });
    erroAnthropic(res, 404, "so /v1/messages");
  });
});
servidor.requestTimeout = 0;
servidor.timeout = 0;
servidor.on("error", (e) => { log("servidor:", e.message); process.exit(1); }); // porta ocupada = ja tem outra ponte rodando
servidor.listen(PORTA, "127.0.0.1", () => { log("ponte ouvindo 127.0.0.1:" + PORTA); tunel(); });

// ---------- tunel ate a VPS 157 ----------
let tunelVivo = false;
function tunel() {
  const t = CONFIG.tunel;
  if (!t) return;
  const ssh = fs.existsSync("C:\\Windows\\System32\\OpenSSH\\ssh.exe") ? "C:\\Windows\\System32\\OpenSSH\\ssh.exe" : "ssh";
  const p = spawn(ssh, ["-N", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=20",
    "-o", "ServerAliveCountMax=3", "-o", "ConnectTimeout=15", "-R", `127.0.0.1:${t.porta_vps}:127.0.0.1:${PORTA}`, t.host],
  { windowsHide: true, stdio: ["ignore", "ignore", "pipe"] });
  const aberto = setTimeout(() => { tunelVivo = true; log("tunel aberto ->", t.host + ":" + t.porta_vps); }, 8000);
  p.stderr.on("data", (d) => log("ssh:", String(d).trim().slice(0, 300)));
  p.on("exit", (c) => {
    clearTimeout(aberto);
    tunelVivo = false;
    log("tunel caiu (codigo " + c + "), refazendo em 15 s");
    setTimeout(tunel, 15000);
  });
}
