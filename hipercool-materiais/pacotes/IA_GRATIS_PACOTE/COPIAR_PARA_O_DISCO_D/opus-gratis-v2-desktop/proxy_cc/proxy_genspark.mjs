// proxy_genspark.mjs (31/10/2026) — cópia LOCAL do proxy do Argon (D:\gemini-argo\proxy_vps.mjs) para o Genspark.
// Roda só neste PC (127.0.0.1:20166). Modelos genspark/* usam o protocolo de ferramentas do Argon com a ponte
// genspark_http.py (:20165, Chrome do cofre); todo o resto vai ao OmniRoute da VPS 157 (:20128) sem alteração.
// Diferenças do original: isArgonModel aceita "genspark/", a ponte recebe o nome do modelo pedido, escuta só em
// 127.0.0.1 e não descreve imagens (visao.mjs local é um stub).
// --- cabeçalho original ---
// antigravity-cc-proxy (2026-09-27, argon 2026-10-26)
// Fica na frente do OmniRoute. Em pedidos de modelo "antigravity/...", remove do
// prompt de sistema as linhas de assinatura do Claude Code que o Google (Antigravity)
// rejeita com um 429 "Resource has been exhausted" falso:
//   "x-anthropic-billing-header: ..." e "You are a Claude agent, built on Anthropic's Claude Agent SDK."
// 2026-10-20: em /v1/messages, traduz a recusa por tamanho do OmniRoute e do Kiro para
// "prompt is too long: N tokens > M maximum", o unico texto com que o Claude Code encurta a
// conversa e resume de novo (com o texto original ele desiste: "automatic compaction failed").
// 2026-10-26: modelos gweb/* e gemini-4-argon vao para o proxy local (porta 20141 = HTTP puro,
// sem navegador) com traducao Anthropic <-> OpenAI on the fly.
// 2026-10-27: com ferramentas no pedido, o Argon chama tool_use por um protocolo de texto (forwardToArgonTools).
// 2026-10-27: modelos hibridos argon-kiro/argon-gemini/argon-opus/argon-sonnet: Argon pensa, reserva executa ferramentas
// quando o Argon nao gera tool_call. O Argon e o cerebro; o reserva e as maos.
// Todo o resto (outros modelos, /v1/models, streaming) passa sem alteracao.
import http from "node:http";
import zlib from "node:zlib";
import fs from "node:fs";
import { AsyncLocalStorage } from "node:async_hooks";
import { precisaOlhos, temImagem, descreverImagens } from "./visao.mjs";

const LISTEN = +(process.env.LISTEN || 20166);
const UP_HOST = process.env.UP_HOST || "IP_DA_SUA_VPS";
const UP_PORT = +(process.env.UP_PORT || 20128);
const ARGON_PORT = +(process.env.ARGON_PORT || 20165); // ponte = genspark_http.py
const STRIP = [
  /^x-anthropic-billing-header:/i,
  /^You are a Claude agent, built on Anthropic's Claude Agent SDK\.?$/i,
  /^You are Claude Code, Anthropic's official CLI for Claude\.?$/i,
];

// "argon-flash": o Flash (com ferramentas) trabalha e delega o dificil ao Argon pela ferramenta MCP ask_argon
const FLASH_MODELO = "agy/gemini-3.8-flash-high";
const FLASH_INSTRUCAO = "Voce tem a ferramenta mcp__gemini-argon__ask_argon (Gemini 4 Argon, raciocinio Alto, 1 a 5 min). " +
  "Faca voce mesmo o trabalho com as ferramentas (ler, editar, rodar). Para decidir arquitetura, depurar algo que nao saiu " +
  "em 2 tentativas, matematica/algoritmo dificil ou revisar uma mudanca grande, chame ask_argon mandando o contexto " +
  "inteiro (trechos de codigo, erro, objetivo), pois ele nao ve os arquivos; depois aplique a resposta.";

function argonFlash(body) {
  if (body.model !== "argon-flash") return false;
  body.model = FLASH_MODELO;
  const bloco = { type: "text", text: FLASH_INSTRUCAO };
  if (Array.isArray(body.system)) body.system.push(bloco);
  else if (typeof body.system === "string" && body.system) body.system = [{ type: "text", text: body.system }, bloco];
  else body.system = [bloco];
  return true;
}

const ARGON_MODELS = new Set(["gemini-4-argon", "gweb/gemini-4-argon", "gweb/gemini-3.1-pro"]);

function isArgonModel(model) {
  if (!model) return false;
  return model.startsWith("genspark/");
}

// 2026-10-27: modelos hibridos — Argon pensa, reserva executa ferramentas
// argon-kiro: reserva = Kiro Sonnet 4.5 (free, ilimitado) — melhor custo-beneficio
// argon-gemini: reserva = Gemini 3.8 Flash (free) — mais rapido, menos capaz
// argon-opus: reserva = Opus 4.6 thinking (free Antigravity) — mais capaz, mais lento
// argon-sonnet: reserva = Sonnet 5.5 web (claude.ai, sem imagem) — rapido, forte em texto
const HIBRIDOS = {
  "argon-kiro":   { reserva: "kr/claude-sonnet-4.5",                 label: "Kiro Sonnet 4.5" },
  "argon-gemini": { reserva: "agy/gemini-3.8-flash-high",            label: "Gemini 3.8 Flash" },
  "argon-opus":   { reserva: "antigravity/claude-opus-4-6-thinking",  label: "Opus 4.6" },
  "argon-sonnet": { reserva: "cw/claude-sonnet-5-5",                   label: "Sonnet 5.5 web" },
};

function isHibrido(model) {
  return model && HIBRIDOS[model];
}

// 2026-10-27: o Argon (Gemini web) nao tem tool calling nativo. O proxy ensina um protocolo de texto: ele pede
// ferramenta escrevendo um bloco ```tool_call {"name","input"}```; o proxy converte em tool_use do Anthropic
// e o Claude Code executa. No historico, tool_use volta ao mesmo formato e tool_result vira texto.
function blocoTexto(b) {
  if (!b) return "";
  if (b.type === "text") return b.text || "";
  if (b.type === "tool_use") return "```tool_call\n" + JSON.stringify({ name: b.name, input: b.input || {} }) + "\n```";
  if (b.type === "tool_result") {
    const r = typeof b.content === "string" ? b.content
      : Array.isArray(b.content) ? b.content.map(blocoTexto).join("\n") : "";
    return "[resultado da ferramenta" + (b.is_error ? " (ERRO)" : "") + "]\n" + r.slice(0, 30000) + "\n[fim do resultado]";
  }
  return "";
}

function instrucaoFerramentas(tools) {
  const lista = tools.map((t) => {
    const sch = t.input_schema || {};
    const desc = String(t.description || "").replace(/\s+/g, " ").slice(0, 600);
    return "- " + t.name + ": " + desc + "\n  esquema: " + JSON.stringify({ properties: sch.properties || {}, required: sch.required || [] });
  }).join("\n");
  return "FERRAMENTAS: voce roda dentro de um agente que EXECUTA ferramentas no computador do usuario.\n" +
    "Para usar uma, escreva um bloco exatamente neste formato (pode haver texto curto antes e varios blocos seguidos):\n" +
    "```tool_call\n{\"name\": \"NomeDaFerramenta\", \"input\": {\"parametro\": \"valor\"}}\n```\n" +
    "Regras: o JSON tem que ser valido e seguir o esquema da ferramenta; depois dos blocos PARE e espere, o resultado " +
    "chega na proxima mensagem entre [resultado da ferramenta] e [fim do resultado]; nunca invente resultado; use " +
    "caminhos absolutos; leia o arquivo (Read) antes de editar (Edit); quando a tarefa estiver feita, responda so em " +
    "texto, sem bloco tool_call.\n" +
    // 27/10 (monitoramento): 1/3 dos turnos terminava descrevendo o conserto sem fazer (calc.py: 40 min, nada editado)
    "IMPORTANTE: se o pedido e fazer, consertar, criar ou rodar algo, FACA com as ferramentas ate o fim e confira " +
    "(ex.: rode o teste depois do Edit). Nunca termine so explicando o que deveria ser feito: a resposta so em texto " +
    "encerra a tarefa. No Edit, old_string tem que ser copiado EXATO do que o Read mostrou (mesmos espacos e quebras).\n" +
    // 29/10 (dona: "chamarem o maximo possivel"): metade dos turnos do Argon/Pro puros saia so em texto
    "USE AS FERRAMENTAS SEMPRE QUE PUDER: nunca responda de memoria sobre arquivo, codigo, log ou estado do sistema; " +
    "abra/procure/rode e responda com base no resultado. Se voce for escrever \"vou ler\", \"vou rodar\", \"vou editar\", " +
    "escreva o bloco tool_call NA MESMA resposta em vez de anunciar. Pode mandar varios blocos de uma vez quando forem " +
    "independentes (ex.: ler 3 arquivos).\n" +
    // 30/10 (argon_relatorio, 48 h): WebFetch voltou com erro 136 vezes ("Credit balance is too low") e ele repetia
    "SE UMA FERRAMENTA VOLTOU COM ERRO, nao chame a mesma do mesmo jeito de novo: leia o erro e mude a abordagem. " +
    "Se o WebFetch falhar, busque a pagina com o Bash (curl -sL \"URL\" | head -c 20000) ou com a ferramenta de shell " +
    "disponivel.\n" +
    "Ferramentas disponiveis:\n" + lista;
}

const LEMBRETE_FERRAMENTAS = "[LEMBRETE DO AGENTE] Voce ESTA conectado ao computador do usuario por meio das " +
  "ferramentas listadas nas instrucoes (secao FERRAMENTAS). Voce consegue sim ler, procurar, editar e rodar: para isso " +
  "responda com um ou mais blocos ```tool_call {\"name\": ..., \"input\": {...}}``` e PARE; o resultado chega na " +
  "proxima mensagem. Nunca diga que nao tem acesso ou que nao foi possivel sem antes tentar a ferramenta.";

// 31/10 (Genspark): resposta so em texto dizendo que nao consegue/nao tem acesso, sem ter chamado ferramenta
const NEGOU_ACESSO = /(n[aã]o (foi poss[ií]vel|consigo|tenho acesso|posso (ler|acessar|abrir|executar|rodar))|sem acesso|unable to|i (can'?t|cannot|don'?t have access))/i;

// 29/10: resposta so em texto que anuncia acao ("vou ler...", "let me run") sem bloco = o modelo esqueceu de chamar
const PROMETEU_ACAO = /\b(vou|irei|vamos|preciso|deixe-me|deixa eu|agora (?:vou|leio|rodo|edito)|let me|i'?ll|i will|next,? i)\b[^.\n]{0,60}\b(ler|abrir|rodar|executar|editar|verificar|conferir|procurar|buscar|criar|escrever|testar|read|run|open|check|edit|search|look|create|write|test)/i;

// Acha os blocos ```tool_call (ou ```json com name de ferramenta conhecida). O JSON pode conter ``` dentro
// (ex.: escrever um .md), entao tenta cada ``` seguinte ate o JSON fechar.
function extrairChamadas(texto, nomes) {
  const chamadas = [];
  const trechos = [];
  const abre = /```(tool_call|json)?[ \t]*\n/g;
  let m, ultimo = 0;
  while ((m = abre.exec(texto))) {
    const ini = m.index + m[0].length;
    let fim = texto.indexOf("```", ini), achou = null;
    while (fim !== -1) {
      try {
        const o = JSON.parse(texto.slice(ini, fim));
        if (o && typeof o.name === "string" && nomes.has(o.name) && (m[1] === "tool_call" || o.input)) achou = o;
      } catch {}
      if (achou) break;
      fim = texto.indexOf("```", fim + 3);
    }
    if (!achou) continue;
    trechos.push(texto.slice(ultimo, m.index));
    chamadas.push({ type: "tool_use", id: "toolu_argon_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8),
                    name: achou.name, input: achou.input && typeof achou.input === "object" ? achou.input : {} });
    ultimo = fim + 3;
    abre.lastIndex = ultimo;
  }
  trechos.push(texto.slice(ultimo));
  return { texto: trechos.join("").trim(), chamadas };
}

// 27/10: monitoramento — um JSON por turno do Argon com ferramentas, lido pelo argon_relatorio.py
const TURNOS_ARQ = new URL("./argon_turnos.jsonl", import.meta.url);

function registrarTurno(body, extra) {
  try {
    const ultimo = (body.messages || []).at(-1);
    const resultados = ultimo && Array.isArray(ultimo.content) ? ultimo.content.filter((b) => b.type === "tool_result") : [];
    const nomesPorId = {};
    for (const m of body.messages || []) {
      if (m.role === "assistant" && Array.isArray(m.content)) for (const b of m.content) if (b.type === "tool_use") nomesPorId[b.id] = b.name;
    }
    const comErro = resultados.filter((b) => b.is_error).map((b) => ({ ferramenta: nomesPorId[b.tool_use_id] || "?",
      erro: textoDe(b.content).slice(0, 300) }));
    fs.appendFileSync(TURNOS_ARQ, JSON.stringify({ ts: new Date().toISOString(), modelo: body.model,
      turno: (body.messages || []).length, ferramentas_anteriores_com_erro: comErro, ...extra }) + "\n");
  } catch (e) { console.log("registrarTurno:", e.message); }
}

function enviarEvento(res, ev) {
  res.write("event: " + ev.type + "\ndata: " + JSON.stringify(ev) + "\n\n");
}

// Com ferramentas: pede a resposta inteira ao Argon (sem stream), extrai as chamadas e devolve no formato Anthropic.
// Em stream, o cabecalho e o message_start saem na hora e um ping a cada 15 s segura a conexao enquanto ele pensa.
// 27/10: tool_choice obrigatorio sem chamada = pede de novo 1x; saida em JSON (output_format/response_format) validada
// e pedida de novo 1x se invalida; usage estimado (caracteres/4) para o Claude Code saber a hora de compactar.
function tokensEstimados(x) {
  return Math.ceil(JSON.stringify(x || "").length / 4);
}

function esquemaSaida(body) {
  const f = body.output_format || body.response_format;
  if (!f) return null;
  return f.schema || (f.json_schema && f.json_schema.schema) || (f.type && /json/.test(f.type) ? {} : null);
}

function limparJson(t) {
  return String(t || "").trim().replace(/^```(?:json)?\s*\n?/i, "").replace(/\n?```\s*$/, "").trim();
}

function erroJson(t) {
  try { JSON.parse(limparJson(t)); return null; } catch (e) { return e.message; }
}

async function forwardToArgonTools(req, res, body) {
  const requestModel = body.model;
  const isStream = !!body.stream;
  const nomes = new Set(body.tools.map((t) => t.name));
  const msgId = "msg_argon_" + Date.now();
  const t0 = Date.now();
  const entrada = tokensEstimados({ s: body.system, m: body.messages, t: body.tools });
  console.log(new Date().toISOString(), "[ARGON+tools]", requestModel, body.tools.length, "ferramentas, stream=" + isStream);
  let ping = null;
  if (isStream) {
    res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-cache", connection: "keep-alive" });
    enviarEvento(res, { type: "message_start", message: { id: msgId, type: "message", role: "assistant", model: requestModel,
      content: [], stop_reason: null, stop_sequence: null, usage: { input_tokens: entrada, output_tokens: 0 } } });
    ping = setInterval(() => enviarEvento(res, { type: "ping" }), 15000);
    res.on("close", () => clearInterval(ping));
  }
  const falhar = (msg) => {
    if (ping) clearInterval(ping);
    console.log(new Date().toISOString(), "[ARGON+tools] erro:", msg.slice(0, 300));
    registrarTurno(body, { ms: Date.now() - t0, erro: msg.slice(0, 300) });
    if (isStream) {
      enviarEvento(res, { type: "error", error: { type: "api_error", message: "Argon: " + msg.slice(0, 500) } });
      return res.end();
    }
    res.writeHead(502, { "content-type": "application/json" });
    res.end(JSON.stringify({ type: "error", error: { type: "api_error", message: "Argon: " + msg.slice(0, 500) } }));
  };
  try {
    const esquema = esquemaSaida(body);
    const ordemJson = esquema ? "Responda SOMENTE com um JSON valido (sem texto antes ou depois, sem bloco de codigo)" +
      (Object.keys(esquema).length ? " que siga este JSON Schema:\n" + JSON.stringify(esquema) : ".") : null;
    let texto = await argonTexto(body, ordemJson, false);
    let { texto: resto, chamadas } = extrairChamadas(texto, nomes);
    let refeito = null;
    const tc = body.tool_choice || {};
    if ((tc.type === "any" || tc.type === "tool") && !chamadas.length) {
      const alvo = tc.type === "tool" ? "a ferramenta " + tc.name : "uma das ferramentas";
      texto = await argonTexto(body, "Voce DEVE responder agora chamando " + alvo + " com um bloco ```tool_call. Nao escreva texto solto.", false);
      ({ texto: resto, chamadas } = extrairChamadas(texto, nomes));
      refeito = "tool_choice";
    }
    if (!chamadas.length && !esquema && NEGOU_ACESSO.test(resto) && !ultimoEhResultado(body)) {
      const novo = await argonTexto(body, "Sua resposta anterior foi:\n\"" + resto.slice(0, 800) + "\"\nVoce nao tentou " +
        "nenhuma ferramenta. Voce TEM acesso pelas ferramentas: chame agora a ferramenta adequada com um bloco ```tool_call.", false);
      const r2 = extrairChamadas(novo, nomes);
      if (r2.chamadas.length) { texto = novo; ({ texto: resto, chamadas } = r2); refeito = "negou_acesso"; }
    }
    if (!chamadas.length && !esquema && PROMETEU_ACAO.test(resto)) {
      const novo = await argonTexto(body, "Sua resposta anterior anunciou uma acao mas NAO chamou ferramenta:\n\"" +
        resto.slice(0, 1500) + "\"\nChame agora a(s) ferramenta(s) com bloco(s) ```tool_call. So responda em texto puro " +
        "se a tarefa ja estiver realmente terminada.", false);
      const r2 = extrairChamadas(novo, nomes);
      if (r2.chamadas.length) { texto = novo; ({ texto: resto, chamadas } = r2); refeito = "prometeu_acao"; }
    }
    if (esquema && !chamadas.length) {
      const erro = erroJson(resto);
      if (erro) {
        texto = await argonTexto(body, ordemJson + "\nSua resposta anterior NAO era JSON valido (" + erro + "). Responda so o JSON.", false);
        ({ texto: resto, chamadas } = extrairChamadas(texto, nomes));
        refeito = "formato";
      }
      resto = limparJson(resto);
    }
    const content = (resto ? [{ type: "text", text: resto }] : []).concat(chamadas);
    if (!content.length) content.push({ type: "text", text: "" });
    const stop = chamadas.length ? "tool_use" : "end_turn";
    console.log(new Date().toISOString(), "[ARGON+tools]", chamadas.length, "chamada(s):", chamadas.map((c) => c.name).join(",") || "-");
    registrarTurno(body, { ms: Date.now() - t0, chamadas: chamadas.map((c) => c.name), refeito,
      blocos_perdidos: (texto.match(/```tool_call/g) || []).length - chamadas.length, so_texto: !chamadas.length,
      chars_resposta: texto.length });
    return enviarResposta(res, isStream, ping, msgId, requestModel, content, stop,
      { input_tokens: entrada, output_tokens: tokensEstimados(texto) });
  } catch (e) {
    if (SEM_COTA.test(e.message || "")) {
      registrarTurno(body, { ms: Date.now() - t0, erro: "sem cota -> " + SUBSTITUTO });
      return sonnetNoLugar(req, res, body, e.message, ping, msgId);
    }
    // 2026-10-30: ponte do PC caída mesmo depois das repetições (argonTexto) -> o Sonnet responde no lugar
    if (QUEDA_CONEXAO.test(e.message || "") && !res.writableEnded && !sinalDoPedido()?.aborted) {
      registrarTurno(body, { ms: Date.now() - t0, erro: "ponte fora (" + e.message.slice(0, 60) + ") -> " + SUBSTITUTO });
      return sonnetNoLugar(req, res, body, e.message, ping, msgId);
    }
    return falhar(e.message);
  }
}

// Modelo hibrido: Argon pensa -> se nao gerar tool_call, o reserva executa as ferramentas.
// O Argon recebe o pedido inteiro (com instrucao de ferramentas) e responde. Se a resposta
// tiver tool_call, otimo — segue como forwardToArgonTools. Se nao, a resposta do Argon vai
// como "pensamento do especialista" para o reserva, que decide a ferramenta a chamar.
function forwardToHibrido(req, res, body, hibrido) {
  const requestModel = body.model;
  const isStream = !!body.stream;
  const nomes = new Set(body.tools.map((t) => t.name));
  const oaiBody = anthropicToOpenAI(body);
  oaiBody.stream = false;
  const payload = Buffer.from(JSON.stringify(oaiBody));
  const msgId = "msg_hib_" + Date.now();
  const t0 = Date.now();
  console.log(new Date().toISOString(), "[HIBRIDO]", requestModel, "->", hibrido.label, ",", body.tools.length, "ferramentas");
  let ping = null;
  if (isStream) {
    res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-cache", connection: "keep-alive" });
    enviarEvento(res, { type: "message_start", message: { id: msgId, type: "message", role: "assistant", model: requestModel,
      content: [], stop_reason: null, stop_sequence: null, usage: { input_tokens: 0, output_tokens: 0 } } });
    ping = setInterval(() => enviarEvento(res, { type: "ping" }), 15000);
  }
  const falhar = (msg) => {
    if (ping) clearInterval(ping);
    console.log(new Date().toISOString(), "[HIBRIDO] erro:", msg.slice(0, 300));
    registrarTurno(body, { ms: Date.now() - t0, erro: msg.slice(0, 300) });
    if (isStream) {
      enviarEvento(res, { type: "error", error: { type: "api_error", message: "Hibrido: " + msg.slice(0, 500) } });
      return res.end();
    }
    res.writeHead(502, { "content-type": "application/json" });
    res.end(JSON.stringify({ type: "error", error: { type: "api_error", message: "Hibrido: " + msg.slice(0, 500) } }));
  };

  // 1) Pede ao Argon
  const up = http.request({ host: "127.0.0.1", port: ARGON_PORT, method: "POST", path: "/v1/chat/completions",
    headers: { "content-type": "application/json", "content-length": String(payload.length) }, timeout: 600000,
    signal: sinalDoPedido() }, (ur) => {
    const parts = [];
    seCairNoMeio(ur, (e) => falhar(e.message));
    ur.on("data", (c) => parts.push(c));
    ur.on("end", () => {
      const corpo = Buffer.concat(parts).toString("utf8");
      if (ur.statusCode !== 200) return falhar("argon " + ur.statusCode + ": " + corpo);
      let textoArgon;
      try { textoArgon = (JSON.parse(corpo).choices || [])[0].message.content || ""; } catch (e) { return falhar("resposta argon ilegivel: " + e.message); }

      // 2) Tenta extrair tool_call do Argon
      const { texto: resto, chamadas } = extrairChamadas(textoArgon, nomes);
      registrarTurno(body, { ms: Date.now() - t0, chamadas: chamadas.map((c) => c.name), so_texto: !chamadas.length,
        blocos_perdidos: (textoArgon.match(/```tool_call/g) || []).length - chamadas.length, chars_resposta: textoArgon.length,
        reserva: chamadas.length ? null : hibrido.reserva });

      if (chamadas.length > 0) {
        // Argon conseguiu chamar ferramentas — usa diretamente
        const content = (resto ? [{ type: "text", text: resto }] : []).concat(chamadas);
        if (!content.length) content.push({ type: "text", text: "" });
        const stop = "tool_use";
        console.log(new Date().toISOString(), "[HIBRIDO] Argon chamou", chamadas.length, "ferramenta(s):", chamadas.map((c) => c.name).join(","));
        return enviarResposta(res, isStream, ping, msgId, requestModel, content, stop);
      }

      // 3) Argon respondeu so texto — passa pro reserva com a analise do Argon
      console.log(new Date().toISOString(), "[HIBRIDO] Argon nao chamou ferramenta, delegando ao", hibrido.label);
      delegarParaReserva(req, res, body, hibrido, textoArgon, isStream, ping, msgId, requestModel);
    });
  });
  up.on("error", (e) => falhar("argon inacessivel: " + e.message));
  up.setTimeout(600000, () => up.destroy(new Error("timeout")));
  res.on("close", () => { if (ping) clearInterval(ping); if (!res.writableFinished) up.destroy(); });
  up.end(payload);
}

// Envia resposta Anthropic (stream ou nao) — reutilizado por hibrido e tools
function enviarResposta(res, isStream, ping, msgId, requestModel, content, stop, uso) {
  uso = uso || { input_tokens: 0, output_tokens: 0 };
  if (!isStream) {
    if (ping) clearInterval(ping);
    const out = Buffer.from(JSON.stringify({ id: msgId, type: "message", role: "assistant", model: requestModel, content,
      stop_reason: stop, stop_sequence: null, usage: uso }));
    res.writeHead(200, { "content-type": "application/json", "content-length": String(out.length) });
    return res.end(out);
  }
  if (ping) clearInterval(ping);
  content.forEach((b, i) => {
    if (b.type === "text") {
      enviarEvento(res, { type: "content_block_start", index: i, content_block: { type: "text", text: "" } });
      if (b.text) enviarEvento(res, { type: "content_block_delta", index: i, delta: { type: "text_delta", text: b.text } });
    } else if (b.type === "thinking") {
      enviarEvento(res, { type: "content_block_start", index: i, content_block: { type: "thinking", thinking: "" } });
      if (b.thinking) enviarEvento(res, { type: "content_block_delta", index: i, delta: { type: "thinking_delta", thinking: b.thinking } });
      if (b.signature) enviarEvento(res, { type: "content_block_delta", index: i, delta: { type: "signature_delta", signature: b.signature } });
    } else if (b.type === "redacted_thinking") {
      enviarEvento(res, { type: "content_block_start", index: i, content_block: b });
    } else {
      enviarEvento(res, { type: "content_block_start", index: i, content_block: { type: "tool_use", id: b.id, name: b.name, input: {} } });
      enviarEvento(res, { type: "content_block_delta", index: i, delta: { type: "input_json_delta", partial_json: JSON.stringify(b.input) } });
    }
    enviarEvento(res, { type: "content_block_stop", index: i });
  });
  enviarEvento(res, { type: "message_delta", delta: { stop_reason: stop, stop_sequence: null }, usage: { output_tokens: uso.output_tokens } });
  enviarEvento(res, { type: "message_stop" });
  res.end();
}

// 29/10 (dona): Argon/Pro sem cota em TODAS as contas -> o Sonnet 5.5 web responde no lugar, com aviso na 1a linha
// do chat. Nunca o Flash-Lite calado (a ponte :20141 descarta a resposta dele e devolve 429 "Nenhuma conta com cota").
const SUBSTITUTO = "cw/claude-sonnet-5-5";
const SEM_COTA = /Nenhuma conta com cota/;

async function sonnetNoLugar(req, res, body, motivo, ping, msgId) {
  const isStream = !!body.stream;
  const volta = (/volta (\d\d:\d\d)/.exec(motivo) || [])[1];
  // 2026-10-30: também entra quando a ponte do PC não responde (20% dos turnos de 48 h: ECONNREFUSED/socket hang up)
  const porque = SEM_COTA.test(motivo || "") ? "sem cota em todas as contas" + (volta ? " (a 1a volta " + volta + ")" : "")
    : "fora do ar agora (a ponte do PC nao respondeu)";
  const aviso = "[AVISO: " + body.model + " " + porque + ". Quem responde abaixo e o Sonnet 5.5 web.]\n\n";
  console.log(new Date().toISOString(), SEM_COTA.test(motivo || "") ? "[SEM COTA]" : "[PONTE FORA]", body.model, "-> " + SUBSTITUTO);
  msgId = msgId || "msg_sub_" + Date.now();
  try {
    const r = await reservaJSON(req, { ...body, model: SUBSTITUTO, reasoning_effort: "max" });
    if (isStream && !res.headersSent) {
      res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-cache", connection: "keep-alive" });
      enviarEvento(res, { type: "message_start", message: { id: msgId, type: "message", role: "assistant", model: body.model,
        content: [], stop_reason: null, stop_sequence: null, usage: { input_tokens: 0, output_tokens: 0 } } });
    }
    // 30/10: o claude-web manda "(empty response)" como texto quando só chama ferramenta: fora
    const content = [{ type: "text", text: aviso }].concat((r.content || []).filter((b) => b.type === "tool_use" ||
      (b.type === "text" && b.text && b.text.trim() && b.text.trim() !== "(empty response)")));
    return enviarResposta(res, isStream, ping, msgId, body.model, content, r.stop_reason || "end_turn", r.usage);
  } catch (e) {
    if (ping) clearInterval(ping);
    const msg = body.model + " " + porque + " e o Sonnet 5.5 web tambem falhou: " + e.message.slice(0, 300);
    if (isStream && res.headersSent) {
      enviarEvento(res, { type: "error", error: { type: "api_error", message: msg } });
      return res.end();
    }
    res.writeHead(429, { "content-type": "application/json" });
    return res.end(JSON.stringify({ type: "error", error: { type: "rate_limit_error", message: msg } }));
  }
}

// Manda a resposta do Argon pro modelo reserva via OmniRoute, que gera o tool_use real.
// O reserva recebe o pedido original (system + tools + msgs) + a resposta do Argon como contexto.
// Sempre sem stream: a resposta volta inteira e sai pelo enviarResposta (stream ou nao, conforme o pedido).
// Se o reserva so devolver texto (ou falhar), vale o texto do Argon: ele e o cerebro.
function delegarParaReserva(req, res, body, hibrido, textoArgon, isStream, ping, msgId, requestModel) {
  const doArgon = () => enviarResposta(res, isStream, ping, msgId, requestModel, [{ type: "text", text: textoArgon || "" }], "end_turn");
  const reservaBody = JSON.parse(JSON.stringify(body));
  reservaBody.model = hibrido.reserva;
  reservaBody.stream = false;
  if (!Array.isArray(reservaBody.messages)) reservaBody.messages = [];
  reservaBody.messages.push({ role: "assistant", content: [{ type: "text", text: textoArgon || "(sem resposta)" }] });
  reservaBody.messages.push({ role: "user", content: [{ type: "text",
    text: "A mensagem acima foi escrita pelo Gemini 4 Argon (especialista de raciocinio), que nao consegue chamar ferramentas. " +
    "Execute agora a proxima acao que ele decidiu, chamando a(s) ferramenta(s) adequada(s). Se ele ja terminou a tarefa e " +
    "nao ha ferramenta a chamar, responda so OK." }] });
  const removed = transform(reservaBody);
  const payload = Buffer.from(JSON.stringify(reservaBody));
  console.log(new Date().toISOString(), "[HIBRIDO] reserva", hibrido.reserva, (payload.length / 1024).toFixed(0) + "KB",
    removed ? "(limpou " + removed + " assinatura(s))" : "");
  const headers = { ...req.headers, host: UP_HOST + ":" + UP_PORT, "content-length": String(payload.length) };
  delete headers["transfer-encoding"];
  delete headers["accept-encoding"];
  const up = http.request({ host: UP_HOST, port: UP_PORT, method: "POST", path: "/v1/messages", headers,
    signal: sinalDoPedido() }, (ur) => {
    const parts = [];
    seCairNoMeio(ur, () => doArgon());
    ur.on("data", (c) => parts.push(c));
    ur.on("end", () => {
      const corpo = Buffer.concat(parts).toString("utf8");
      if (ur.statusCode !== 200) {
        console.log(new Date().toISOString(), "[HIBRIDO] reserva", ur.statusCode + ":", corpo.slice(0, 300));
        return doArgon();
      }
      let resp;
      try { resp = JSON.parse(corpo); } catch { return doArgon(); }
      const blocos = (resp.content || []).filter((b) => b.type === "tool_use");
      if (!blocos.length) {
        console.log(new Date().toISOString(), "[HIBRIDO] reserva nao chamou ferramenta -> texto do Argon");
        return doArgon();
      }
      console.log(new Date().toISOString(), "[HIBRIDO] reserva chamou:", blocos.map((b) => b.name).join(","));
      const content = (textoArgon ? [{ type: "text", text: textoArgon }] : []).concat(blocos);
      enviarResposta(res, isStream, ping, msgId, requestModel, content, "tool_use");
    });
  });
  up.on("error", (e) => { console.log(new Date().toISOString(), "[HIBRIDO] reserva erro:", e.message); doArgon(); });
  up.setTimeout(600000, () => up.destroy(new Error("timeout")));
  up.end(payload);
}

// ===== 2026-10-27: banco de testes de divisao de trabalho Argon x reserva =====
// Modelo "hx-<modo>-<reserva>" (reserva: kiro | gemini | opus | sonnet). Modos: socorro, maos, plano, revisor, erro
// (descritos em D:\gemini-argo\captura\HIBRIDOS_PROGRESSO.md). "argon-pro" aponta para o vencedor (ARGON_PRO).
const RESERVAS = { kiro: "kr/claude-sonnet-4.5", gemini: "agy/gemini-3.8-flash-high", opus: "antigravity/claude-opus-4-6-thinking", sonnet: "cw/claude-sonnet-5-5" };
const MODOS = new Set(["socorro", "maos", "plano", "revisor", "erro"]);
const ARGON_PRO_ARQ = new URL("./argon_pro.txt", import.meta.url); // vencedor do teste, trocado sem reiniciar
const memoria = new Map(); // chave do pedido -> { plano, revisoes }

function hxConfig(model) {
  if (model === "argon-pro") {
    try { model = fs.readFileSync(ARGON_PRO_ARQ, "utf8").trim(); } catch { model = "hx-socorro-kiro"; }
  }
  const m = /^hx-([a-z]+)-([a-z]+)$/.exec(model || "");
  if (!m || !MODOS.has(m[1]) || !RESERVAS[m[2]]) return null;
  return { modo: m[1], reserva: RESERVAS[m[2]], label: m[2] };
}

function textoDe(c) {
  return typeof c === "string" ? c : Array.isArray(c) ? c.map(blocoTexto).filter(Boolean).join("\n") : "";
}

// Chave do pedido = ultima mensagem do usuario que nao e resultado de ferramenta (o pedido original desta tarefa)
function chavePedido(body) {
  const msgs = body.messages || [];
  for (let i = msgs.length - 1; i >= 0; i--) {
    const m = msgs[i];
    if (m.role !== "user") continue;
    const temResultado = Array.isArray(m.content) && m.content.some((b) => b.type === "tool_result");
    if (!temResultado) return i + ":" + textoDe(m.content).slice(0, 400);
  }
  return "0";
}

function ultimoEhResultado(body) {
  const m = (body.messages || []).at(-1);
  return m && m.role === "user" && Array.isArray(m.content) && m.content.some((b) => b.type === "tool_result");
}

function resultadoComErro(body) {
  const m = (body.messages || []).at(-1);
  if (!m || !Array.isArray(m.content)) return "";
  const erros = m.content.filter((b) => b.type === "tool_result" &&
    (b.is_error || /Traceback|Error\b|Exception|FAILED|AssertionError|exit code [1-9]|failed/i.test(textoDe(b.content))));
  return erros.map((b) => textoDe(b.content).slice(-4000)).join("\n---\n");
}

function lembrar(chave) {
  if (!memoria.has(chave)) {
    if (memoria.size > 200) memoria.delete(memoria.keys().next().value);
    memoria.set(chave, { plano: null, revisoes: 0 });
  }
  return memoria.get(chave);
}

// Pede texto ao Argon. extra = instrucao de sistema a mais; semFerramentas = nao ensina o protocolo tool_call.
// 29/10: 27% dos turnos do Argon puro caiam em "socket hang up"/ECONNRESET na ponte :20141; repete ate 2x so nesses.
const QUEDA_CONEXAO = /socket hang up|ECONNRESET|ECONNREFUSED|EPIPE/;
// 2026-10-30: sinal "o cliente desistiu" do pedido em andamento (posto no handler); chega aqui sem passar parâmetro
const PEDIDO = new AsyncLocalStorage();
const sinalDoPedido = () => PEDIDO.getStore()?.sinal;

// Resposta da ponte/reserva que caiu no meio (túnel caiu): o Node só marca "aborted" e nem "end" nem "error" chegam —
// a promessa ficava pendurada para sempre com o ping a cada 15 s. Agora vira erro (e casa com QUEDA_CONEXAO).
function seCairNoMeio(ur, falha) {
  ur.on("close", () => { if (!ur.complete) falha(new Error("socket hang up: resposta incompleta")); });
}

async function argonTexto(body, extra, semFerramentas) {
  const oai = anthropicToOpenAI(semFerramentas ? { ...body, tools: undefined } : body);
  if (extra) oai.messages.push({ role: "user", content: extra });
  oai.stream = false;
  const payload = Buffer.from(JSON.stringify(oai));
  for (let tentativa = 0; ; tentativa++) {
    try {
      return await argonUmaVez(payload);
    } catch (e) {
      if (sinalDoPedido()?.aborted) throw new Error("cliente desistiu do pedido");
      if (tentativa >= 2 || !QUEDA_CONEXAO.test(e.message || "")) throw e;
      console.log("argon: queda de conexao (" + e.message + "), repetindo " + (tentativa + 1) + "/2");
      await new Promise((r) => setTimeout(r, 3000 * (tentativa + 1)));
    }
  }
}

function argonUmaVez(payload) {
  return new Promise((ok, falha) => {
    const up = http.request({ host: "127.0.0.1", port: ARGON_PORT, method: "POST", path: "/v1/chat/completions",
      signal: sinalDoPedido(),
      headers: { "content-type": "application/json", "content-length": String(payload.length) } }, (ur) => {
      const parts = [];
      seCairNoMeio(ur, falha);
      ur.on("data", (c) => parts.push(c));
      ur.on("end", () => {
        const corpo = Buffer.concat(parts).toString("utf8");
        if (ur.statusCode !== 200) {
          // corpo inteiro no erro: o "Nenhuma conta com cota" pode vir depois do caractere 200 e o Sonnet não entrava
          const e = new Error("argon " + ur.statusCode + ": " + corpo.slice(0, 200));
          if (!SEM_COTA.test(e.message) && SEM_COTA.test(corpo)) e.message += " [" + (corpo.match(SEM_COTA) || [""])[0] + "]";
          return falha(e);
        }
        try { ok((JSON.parse(corpo).choices || [])[0].message.content || ""); } catch (e) { falha(e); }
      });
    });
    up.on("error", falha);
    up.setTimeout(600000, () => up.destroy(new Error("timeout argon")));
    up.end(payload);
  });
}

// Chama o reserva no OmniRoute sem stream e devolve o JSON Anthropic.
function reservaJSON(req, body) {
  const b = { ...body, stream: false };
  transform(b);
  const payload = Buffer.from(JSON.stringify(b));
  const headers = { ...req.headers, host: UP_HOST + ":" + UP_PORT, "content-length": String(payload.length) };
  delete headers["transfer-encoding"];
  delete headers["accept-encoding"];
  return new Promise((ok, falha) => {
    const up = http.request({ host: UP_HOST, port: UP_PORT, method: "POST", path: "/v1/messages", headers,
      signal: sinalDoPedido() }, (ur) => {
      const parts = [];
      seCairNoMeio(ur, falha);
      ur.on("data", (c) => parts.push(c));
      ur.on("end", () => {
        const corpo = Buffer.concat(parts).toString("utf8");
        if (ur.statusCode !== 200) return falha(new Error("reserva " + ur.statusCode + ": " + corpo.slice(0, 300)));
        try { ok(JSON.parse(corpo)); } catch (e) { falha(e); }
      });
    });
    up.on("error", falha);
    up.setTimeout(600000, () => up.destroy(new Error("timeout reserva")));
    up.end(payload);
  });
}

function comSistema(body, texto) {
  const b = JSON.parse(JSON.stringify(body));
  const bloco = { type: "text", text: texto };
  if (Array.isArray(b.system)) b.system.push(bloco);
  else if (typeof b.system === "string" && b.system) b.system = [{ type: "text", text: b.system }, bloco];
  else b.system = [bloco];
  return b;
}

// Repassa o pedido ao reserva com stream normal (modos em que o reserva e quem trabalha)
function repassarReserva(req, res, body, cfg) {
  const b = { ...body, model: cfg.reserva };
  transform(b);
  forward(req, res, Buffer.from(JSON.stringify(b)), true);
}

function abrirResposta(res, isStream, model) {
  const msgId = "msg_hx_" + Date.now();
  let ping = null;
  if (isStream) {
    res.writeHead(200, { "content-type": "text/event-stream", "cache-control": "no-cache", connection: "keep-alive" });
    enviarEvento(res, { type: "message_start", message: { id: msgId, type: "message", role: "assistant", model,
      content: [], stop_reason: null, stop_sequence: null, usage: { input_tokens: 0, output_tokens: 0 } } });
    ping = setInterval(() => enviarEvento(res, { type: "ping" }), 15000);
    res.on("close", () => clearInterval(ping));
  }
  return { msgId, ping };
}

function fecharComErro(res, isStream, ping, msg) {
  if (ping) clearInterval(ping);
  console.log(new Date().toISOString(), "[HX] erro:", msg.slice(0, 300));
  if (isStream) {
    enviarEvento(res, { type: "error", error: { type: "api_error", message: msg.slice(0, 500) } });
    return res.end();
  }
  res.writeHead(502, { "content-type": "application/json" });
  res.end(JSON.stringify({ type: "error", error: { type: "api_error", message: msg.slice(0, 500) } }));
}

const AVISO_ARGON = "Voce e o Gemini 4 Argon, o cerebro de uma dupla. Outro modelo (o executor) le e roda as ferramentas por voce.";

async function forwardHx(req, res, body, cfg) {
  const model = body.model;
  const isStream = !!body.stream;
  const log = (...a) => console.log(new Date().toISOString(), "[HX " + model + "]", ...a);

  if (cfg.modo === "socorro") return forwardToHibrido(req, res, body, cfg);

  if (cfg.modo === "plano" || cfg.modo === "erro") {
    const mem = lembrar(chavePedido(body));
    let extra = "";
    try {
      if (cfg.modo === "plano") {
        if (!mem.plano) {
          mem.plano = await argonTexto(body, AVISO_ARGON + " Escreva o PLANO para cumprir o ultimo pedido do usuario: " +
            "passos curtos e concretos (o que ler, o que mudar, como conferir) e as armadilhas. Nao escreva o codigo inteiro.", true);
          log("plano do Argon:", mem.plano.length, "caracteres");
        }
        extra = "PLANO do Gemini 4 Argon (especialista) para esta tarefa — siga, ajustando ao que encontrar:\n" + mem.plano;
      } else {
        const erro = resultadoComErro(body);
        if (erro) {
          const diag = await argonTexto(body, AVISO_ARGON + " A ultima ferramenta deu erro. Diagnostique a CAUSA e diga " +
            "exatamente o que corrigir (arquivo, trecho, mudanca). Seja curto.", true);
          log("diagnostico do Argon:", diag.length, "caracteres");
          extra = "DIAGNOSTICO do Gemini 4 Argon (especialista) para o erro da ultima ferramenta — considere antes de agir:\n" + diag;
        }
      }
    } catch (e) { log("Argon falhou, segue so o reserva:", e.message); }
    return repassarReserva(req, res, extra ? comSistema(body, extra) : body, cfg);
  }

  const { msgId, ping } = abrirResposta(res, isStream, model);
  const enviar = (content, stop) => enviarResposta(res, isStream, ping, msgId, model,
    content.filter((b) => ["text", "tool_use", "thinking", "redacted_thinking"].includes(b.type)), stop);
  try {
    if (cfg.modo === "maos") {
      let ordem;
      try {
        ordem = await argonTexto(body, AVISO_ARGON + " Decida a PROXIMA ACAO: qual ferramenta, com quais parametros " +
          "exatos (caminhos absolutos, texto exato a trocar). Se a tarefa ja terminou, escreva a resposta final ao usuario.", true);
      } catch (e) {
        // 28/10: Argon sem cota/fora -> o reserva faz este passo sozinho (antes o pedido inteiro dava erro)
        log("Argon falhou, reserva sozinho neste passo:", e.message);
        const r0 = await reservaJSON(req, { ...body, model: cfg.reserva });
        return enviar(r0.content || [], r0.stop_reason || "end_turn");
      }
      const pedido = comSistema(body, "Voce e o EXECUTOR de uma dupla. O cerebro (Gemini 4 Argon) decidiu a proxima acao abaixo. " +
        "Execute-a com as ferramentas, fielmente. Se ele escreveu a resposta final e nao ha acao, repita a resposta dele.\n\n" + ordem);
      const r = await reservaJSON(req, { ...pedido, model: cfg.reserva });
      log("reserva:", (r.content || []).map((b) => b.type === "tool_use" ? b.name : b.type).join(","));
      return enviar(r.content || [], r.stop_reason || "end_turn");
    }

    // revisor: o reserva trabalha; quando termina, o Argon revisa (no maximo 2 vezes por pedido)
    let r = await reservaJSON(req, { ...body, model: cfg.reserva });
    const terminou = !(r.content || []).some((b) => b.type === "tool_use");
    const mem = lembrar(chavePedido(body));
    if (terminou && mem.revisoes < 2) {
      mem.revisoes++;
      const final = (r.content || []).filter((b) => b.type === "text").map((b) => b.text).join("\n");
      const hist = { ...body, messages: [...(body.messages || []), { role: "assistant", content: final }] };
      const parecer = await argonTexto(hist, "Voce e o Gemini 4 Argon, REVISOR. O executor acima diz que terminou. Confira pelo " +
        "historico (resultados das ferramentas) se o pedido do usuario foi cumprido por inteiro e se foi verificado. Se sim, " +
        "responda so APROVADO. Se nao, liste curto o que falta ou esta errado.", true);
      log("revisao", mem.revisoes + ":", parecer.slice(0, 80).replace(/\s+/g, " "));
      if (!/^\W*APROVADO/i.test(parecer.trim())) {
        r = await reservaJSON(req, { ...body, model: cfg.reserva, messages: [...(body.messages || []),
          { role: "assistant", content: final || "Terminei." },
          { role: "user", content: "O revisor (Gemini 4 Argon) NAO aprovou:\n" + parecer + "\nCorrija/complete com as ferramentas." }] });
      }
    }
    return enviar(r.content || [], r.stop_reason || "end_turn");
  } catch (e) {
    return fecharComErro(res, isStream, ping, "hx: " + e.message);
  }
}

function anthropicToOpenAI(body) {
  const messages = [];
  if (body.system) {
    const sysText = typeof body.system === "string"
      ? body.system
      : Array.isArray(body.system)
        ? body.system.map(b => b.text || "").join("\n")
        : "";
    // 31/10 (Genspark): sem as linhas de assinatura do Claude Code, que só confundem o modelo do chat web
    const limpo = sysText.split("\n").filter((l) => !STRIP.some((re) => re.test(l.trim()))).join("\n");
    if (limpo.trim()) messages.push({ role: "system", content: limpo });
  }
  if (Array.isArray(body.tools) && body.tools.length) {
    messages.push({ role: "system", content: instrucaoFerramentas(body.tools) });
  }
  if (Array.isArray(body.messages)) {
    for (const m of body.messages) {
      const role = m.role === "assistant" ? "assistant" : "user";
      let content;
      if (typeof m.content === "string") {
        content = m.content;
      } else if (Array.isArray(m.content)) {
        content = m.content.map(blocoTexto).filter(Boolean).join("\n");
      } else {
        content = String(m.content || "");
      }
      messages.push({ role, content });
    }
  }
  // 31/10 (Genspark): as instruções de ferramenta ficam enterradas no meio de ~37 mil caracteres e o modelo do chat
  // às vezes respondia "não foi possível ler o arquivo" sem tentar. Um lembrete curto no FIM do pedido.
  if (Array.isArray(body.tools) && body.tools.length) {
    messages.push({ role: "user", content: LEMBRETE_FERRAMENTAS });
  }
  return {
    model: body.model,
    messages,
    stream: !!body.stream,
  };
}

function openAIToAnthropic(oai, requestModel) {
  const choice = (oai.choices || [])[0] || {};
  const msg = choice.message || {};
  const text = msg.content || "";
  return {
    id: "msg_" + (oai.id || "argon").replace("chatcmpl-", ""),
    type: "message",
    role: "assistant",
    model: requestModel || "gemini-4-argon",
    content: [{ type: "text", text }],
    stop_reason: "end_turn",
    stop_sequence: null,
    usage: {
      input_tokens: (oai.usage || {}).prompt_tokens || 0,
      output_tokens: (oai.usage || {}).completion_tokens || 0,
    },
  };
}

function openAIChunkToAnthropicEvents(chunk, requestModel, index) {
  const events = [];
  if (index === 0) {
    events.push({
      type: "message_start",
      message: {
        id: "msg_argon_" + Date.now(),
        type: "message",
        role: "assistant",
        model: requestModel || "gemini-4-argon",
        content: [],
        stop_reason: null,
        stop_sequence: null,
        usage: { input_tokens: 0, output_tokens: 0 },
      },
    });
    events.push({
      type: "content_block_start",
      index: 0,
      content_block: { type: "text", text: "" },
    });
  }
  const choice = (chunk.choices || [])[0] || {};
  const delta = choice.delta || {};
  if (delta.content) {
    events.push({
      type: "content_block_delta",
      index: 0,
      delta: { type: "text_delta", text: delta.content },
    });
  }
  if (choice.finish_reason) {
    events.push({ type: "content_block_stop", index: 0 });
    events.push({
      type: "message_delta",
      delta: { stop_reason: "end_turn", stop_sequence: null },
      usage: { output_tokens: 0 },
    });
    events.push({ type: "message_stop" });
  }
  return events;
}

function forwardToArgon(req, res, body) {
  const requestModel = body.model;
  const isStream = !!body.stream;
  const oaiBody = anthropicToOpenAI(body);
  const payload = Buffer.from(JSON.stringify(oaiBody));

  console.log(new Date().toISOString(), "[ARGON]", requestModel, "-> localhost:" + ARGON_PORT, "stream=" + isStream);

  const up = http.request({
    host: "127.0.0.1",
    port: ARGON_PORT,
    method: "POST",
    path: "/v1/chat/completions",
    headers: {
      "content-type": "application/json",
      "content-length": String(payload.length),
    },
    timeout: 600000,
  }, (ur) => {
    if (ur.statusCode !== 200) {
      const parts = [];
      ur.on("data", c => parts.push(c));
      ur.on("end", () => {
        const errBody = Buffer.concat(parts).toString("utf8");
        console.log(new Date().toISOString(), "[ARGON] upstream", ur.statusCode + ":", errBody.slice(0, 300));
        if (ur.statusCode === 429 && SEM_COTA.test(errBody)) return sonnetNoLugar(req, res, body, errBody);
        res.writeHead(ur.statusCode || 500, { "content-type": "application/json" });
        res.end(JSON.stringify({
          type: "error",
          error: { type: "api_error", message: "Argon proxy error: " + errBody.slice(0, 500) },
        }));
      });
      return;
    }

    if (isStream) {
      res.writeHead(200, {
        "content-type": "text/event-stream",
        "cache-control": "no-cache",
        connection: "keep-alive",
      });
      let chunkIndex = 0;
      let buffer = "";
      let fechado = false; // 2026-10-30: message_stop já foi (ou o erro já foi mandado)
      const fechar = () => {
        if (fechado) return;
        fechado = true;
        const evs = openAIChunkToAnthropicEvents({ choices: [{ delta: { content: "" }, finish_reason: "stop" }] }, requestModel, chunkIndex);
        for (const ev of evs) res.write("event: " + ev.type + "\ndata: " + JSON.stringify(ev) + "\n\n");
      };
      // 2026-10-30: decodificador de texto do próprio stream. Antes era data.toString("utf8") por pedaço: "ç"/"ã"
      // partido entre dois pedaços TCP virava "��" nas respostas em português
      ur.setEncoding("utf8");
      ur.on("data", (data) => {
        buffer += data;
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data: ") || fechado) continue;
          const pl = line.slice(6).trim();
          if (pl === "[DONE]") {
            fechar();
            return;
          }
          try {
            const chunk = JSON.parse(pl);
            if (chunk.error) {
              // 2026-10-30: a ponte caiu no meio da resposta (finish_reason "error"); antes virava end_turn e o
              // Claude Code tomava a resposta cortada como completa
              fechado = true;
              console.log(new Date().toISOString(), "[ARGON] erro no meio do stream:", String(chunk.error.message || "").slice(0, 200));
              res.write("event: error\ndata: " + JSON.stringify({ type: "error", error: { type: "api_error", message: chunk.error.message || "Argon: erro no meio da resposta" } }) + "\n\n");
              return;
            }
            const events = openAIChunkToAnthropicEvents(chunk, requestModel, chunkIndex);
            for (const ev of events) {
              res.write("event: " + ev.type + "\ndata: " + JSON.stringify(ev) + "\n\n");
              if (ev.type === "message_stop") fechado = true;
            }
            chunkIndex++;
          } catch {}
        }
      });
      // a ponte terminou sem finish_reason/[DONE] (ou a conexão caiu: "close" sem "end"): fecha o stream direito
      ur.on("end", () => { fechar(); res.end(); });
      ur.on("close", () => { if (!res.writableEnded) { fechar(); res.end(); } });
    } else {
      const parts = [];
      ur.on("data", c => parts.push(c));
      ur.on("end", () => {
        try {
          const oaiResp = JSON.parse(Buffer.concat(parts).toString("utf8"));
          const antResp = openAIToAnthropic(oaiResp, requestModel);
          const out = Buffer.from(JSON.stringify(antResp));
          res.writeHead(200, {
            "content-type": "application/json",
            "content-length": String(out.length),
          });
          res.end(out);
        } catch (e) {
          res.writeHead(500, { "content-type": "application/json" });
          res.end(JSON.stringify({ type: "error", error: { type: "api_error", message: "Argon response parse error: " + e.message } }));
        }
      });
    }
  });
  up.on("error", (e) => {
    console.log(new Date().toISOString(), "[ARGON] error:", e.message);
    if (res.writableEnded) return;
    // 2026-10-30: ponte do PC fora antes de qualquer resposta -> o Sonnet responde no lugar (com aviso)
    // (res.destroyed = o próprio cliente foi embora e o up.destroy() virou "socket hang up": aí ninguém espera resposta)
    if (!res.headersSent && !res.destroyed && QUEDA_CONEXAO.test(e.message || "") && !sinalDoPedido()?.aborted) {
      return sonnetNoLugar(req, res, body, e.message);
    }
    const erro = { type: "error", error: { type: "api_error", message: "Argon proxy unreachable: " + e.message } };
    // 2026-10-30: com o stream já aberto o erro vai como evento SSE (antes saía JSON cru no meio dos eventos)
    if (res.headersSent) return res.end("event: error\ndata: " + JSON.stringify(erro) + "\n\n");
    res.writeHead(502, { "content-type": "application/json" });
    res.end(JSON.stringify(erro));
  });
  up.setTimeout(600000, () => { up.destroy(new Error("timeout")); });
  res.on("close", () => { if (!res.writableFinished) up.destroy(); });
  up.end(payload);
}

const GATEWAY_GRANDE = /Input exceeds (?:maximum input tokens|context window) for ([^:"]+): estimated (\d+) input tokens, (?:max input|limit) (\d+)\. Reduce the prompt or route to a model with a larger (?:input limit|context window)\./;
const KIRO_GRANDE = /Input content length exceeds threshold\./;
const KIRO_LIMITE = 150000;

function cleanText(text) {
  return text.split("\n").filter((l) => !STRIP.some((r) => r.test(l.trim()))).join("\n");
}

function cleanBlocks(blocks) {
  let removed = 0;
  const out = [];
  for (const b of blocks) {
    if (b && typeof b.text === "string") {
      const t = cleanText(b.text);
      if (t !== b.text) removed++;
      if (t.trim() === "") continue;
      out.push({ ...b, text: t });
    } else out.push(b);
  }
  return { out, removed };
}

function transform(body) {
  if (!body || typeof body.model !== "string" || !body.model.startsWith("antigravity/")) return 0;
  let removed = 0;
  if (Array.isArray(body.system)) {
    const r = cleanBlocks(body.system);
    removed += r.removed;
    if (r.out.length) body.system = r.out; else delete body.system;
  } else if (typeof body.system === "string") {
    const t = cleanText(body.system);
    if (t !== body.system) { removed++; body.system = t; }
  }
  if (Array.isArray(body.messages)) {
    for (const m of body.messages) {
      if (!m || m.role !== "system") continue;
      if (typeof m.content === "string") {
        const t = cleanText(m.content);
        if (t !== m.content) { removed++; m.content = t; }
      } else if (Array.isArray(m.content)) {
        const r = cleanBlocks(m.content);
        removed += r.removed;
        m.content = r.out;
      }
    }
  }
  return removed;
}

function traduzirGrande(texto, tamPedido) {
  const g = texto.match(GATEWAY_GRANDE);
  if (g) {
    const limite = g[1].startsWith("kiro/") ? Math.min(+g[3], KIRO_LIMITE) : +g[3];
    return texto.replace(GATEWAY_GRANDE, "prompt is too long: " + g[2] + " tokens > " + limite + " maximum");
  }
  if (KIRO_GRANDE.test(texto)) {
    const estimado = Math.max(Math.ceil(tamPedido / 4), KIRO_LIMITE + 20000);
    return texto.replace(KIRO_GRANDE, "prompt is too long: " + estimado + " tokens > " + KIRO_LIMITE + " maximum");
  }
  return null;
}

function responderTraduzido(ur, res, tamPedido) {
  const partes = [];
  ur.on("data", (c) => partes.push(c));
  ur.on("end", () => {
    let corpo = Buffer.concat(partes);
    const headers = { ...ur.headers };
    try {
      const enc = String(headers["content-encoding"] || "").toLowerCase();
      const aberto = enc === "gzip" ? zlib.gunzipSync(corpo)
        : enc === "br" ? zlib.brotliDecompressSync(corpo)
        : enc === "deflate" ? zlib.inflateSync(corpo) : corpo;
      const novo = traduzirGrande(aberto.toString("utf8"), tamPedido);
      if (novo !== null) {
        corpo = Buffer.from(novo);
        delete headers["content-encoding"];
        console.log(new Date().toISOString(), "recusa por tamanho traduzida:", novo.slice(0, 200));
      }
    } catch {}
    delete headers["transfer-encoding"];
    headers["content-length"] = String(corpo.length);
    res.writeHead(ur.statusCode, headers);
    res.end(corpo);
  });
}

function forward(req, res, buf, mensagens) {
  const headers = { ...req.headers, host: UP_HOST + ":" + UP_PORT };
  if (buf) { headers["content-length"] = String(buf.length); delete headers["transfer-encoding"]; }
  const up = http.request({ host: UP_HOST, port: UP_PORT, method: req.method, path: req.url, headers }, (ur) => {
    if (mensagens && ur.statusCode === 400) return responderTraduzido(ur, res, buf ? buf.length : 0);
    res.writeHead(ur.statusCode || 502, ur.headers);
    ur.pipe(res);
  });
  up.on("error", (e) => {
    if (!res.headersSent) res.writeHead(502, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: { message: "antigravity-cc-proxy: upstream error: " + e.message } }));
  });
  res.on("close", () => { if (!res.writableFinished) up.destroy(); });
  if (buf) up.end(buf); else req.pipe(up);
}

// 2026-10-29: modelos "cline-..." (ex.: cline-opus-5-5) vao para a cline-ponte do PC da dona pelo tunel ssh -R
// (127.0.0.1:20160). A ponte usa o login que ja esta no Cline do PC e chama api.cline.bot. Ver D:\\cline-ponte.
const CLINE_PORT = 20160;
function isCline(model) { return typeof model === "string" && /^cline[-/]/.test(model); }
function forwardToCline(req, res, buf) {
  const headers = { ...req.headers, host: "127.0.0.1:" + CLINE_PORT, "content-length": String(buf.length) };
  delete headers["transfer-encoding"];
  const up = http.request({ host: "127.0.0.1", port: CLINE_PORT, method: req.method, path: req.url, headers }, (ur) => {
    res.writeHead(ur.statusCode || 502, ur.headers);
    ur.pipe(res);
  });
  up.on("error", (e) => {
    if (!res.headersSent) res.writeHead(529, { "content-type": "application/json" });
    res.end(JSON.stringify({ type: "error", error: { type: "overloaded_error",
      message: "cline-ponte fora do ar (PC desligado ou tunel caido): " + e.message } }));
  });
  res.on("close", () => { if (!res.writableFinished) up.destroy(); });
  up.end(buf);
}

// 2026-10-30: CHAVE nos pedidos de chat. Argon/hx/híbridos iam direto à ponte do PC sem conferir nada, e no teste o
// OmniRoute também respondeu /v1/messages sem chave vindo da internet: qualquer um que alcançasse a :20133 gastava
// as cotas. Agora o pedido do Argon precisa da MESMA chave do OmniRoute que os clientes já
// mandam (conferida no próprio OmniRoute, com cache). Local (a VPS) e Tailscale (100.64.0.0/10) passam sem chave.
// MODO_CHAVE=observar (padrão): não bloqueia, só registra "[CHAVE]" no journal; =exigir: responde 401.
const MODO_CHAVE = process.env.MODO_CHAVE || "observar";
const chavesVistas = new Map(); // chave -> { ok, ate }

function chaveDoPedido(req) {
  const a = String(req.headers["authorization"] || "");
  return (/^Bearer\s+/i.test(a) ? a.replace(/^Bearer\s+/i, "") : a) || String(req.headers["x-api-key"] || "");
}

function origemConfiavel(req) {
  const ip = (req.socket.remoteAddress || "").replace(/^::ffff:/, "");
  if (ip === "127.0.0.1" || ip === "::1") return true;
  const m = /^100\.(\d+)\./.exec(ip);
  return !!m && +m[1] >= 64 && +m[1] <= 127; // Tailscale
}

function chaveValida(chave) {
  const c = chavesVistas.get(chave);
  if (c && c.ate > Date.now()) return Promise.resolve(c.ok);
  return new Promise((ok) => {
    const guardar = (v, ms) => { chavesVistas.set(chave, { ok: v, ate: Date.now() + ms }); ok(v); };
    const up = http.request({ host: UP_HOST, port: UP_PORT, method: "GET", path: "/v1/models",
      headers: { authorization: "Bearer " + chave, "x-api-key": chave } }, (ur) => {
      ur.resume();
      if (ur.statusCode === 200) return guardar(true, 10 * 60000);
      if (ur.statusCode === 401 || ur.statusCode === 403) return guardar(false, 60000);
      ok(true); // OmniRoute com outro problema: não barrar por isso (não pode quebrar)
    });
    up.on("error", () => ok(true));
    up.setTimeout(8000, () => up.destroy(new Error("timeout")));
    up.end();
  });
}

async function liberadoArgon(req, modelo) {
  if (origemConfiavel(req)) return true;
  const chave = chaveDoPedido(req);
  const valida = chave ? await chaveValida(chave) : false;
  if (valida) return true;
  console.log(new Date().toISOString(), "[CHAVE]", MODO_CHAVE === "exigir" ? "BARRADO" : "seria barrado",
    "ip=" + (req.socket.remoteAddress || "?"), "modelo=" + modelo, chave ? "chave invalida" : "sem chave",
    "ua=" + String(req.headers["user-agent"] || "").slice(0, 60));
  return MODO_CHAVE !== "exigir";
}

const server = http.createServer((req, res) => {
  const isChat = req.method === "POST" && /\/(messages|chat\/completions)(\?|$)/.test(req.url || "");
  if (!isChat && req.method === "POST" && /\/messages\/count_tokens/.test(req.url || "")) {
    const cs = [];
    req.on("data", (c) => cs.push(c));
    req.on("end", () => {
      const b = Buffer.concat(cs);
      let m = "";
      try { m = JSON.parse(b.toString("utf8")).model; } catch {}
      if (isCline(m)) return forwardToCline(req, res, b);
      forward(req, res, b, false);
    });
    return;
  }
  if (!isChat) return forward(req, res, null, false);
  const chunks = [];
  req.on("data", (c) => chunks.push(c));
  req.on("end", async () => {
    let buf = Buffer.concat(chunks);
    // 2026-10-30: cliente fechou antes da resposta (Esc no Claude Code) = cancela as chamadas à ponte/reserva deste pedido
    const ac = new AbortController();
    res.on("close", () => { if (!res.writableFinished) ac.abort(); });
    PEDIDO.enterWith({ sinal: ac.signal });
    try {
      const j = JSON.parse(buf.toString("utf8"));
      // 2026-10-29: Sonnet web (cw/ e sonnet-fila) e Argon nao recebem imagem -> o Gemini descreve (visao.mjs)
      if (precisaOlhos(j.model) && temImagem(j)) {
        try {
          await descreverImagens(j, req.headers, (m) => console.log(new Date().toISOString(), j.model + ": " + m));
          buf = Buffer.from(JSON.stringify(j));
        } catch (e) { console.log(new Date().toISOString(), "visao falhou: " + e.message); }
      }

      // 2026-10-30: "return await": sem o await a rejeição dos handlers async escapava do try e derrubava o node
      // inteiro (unhandled rejection) — todos os modelos caíam juntos
      if (isCline(j.model)) return await forwardToCline(req, res, buf);

      // teste 30/10: o OmniRoute também aceitou /v1/messages SEM chave vindo da internet -> a conferência vale p/ todos
      if (!(await liberadoArgon(req, j.model))) {
        res.writeHead(401, { "content-type": "application/json" });
        return res.end(JSON.stringify({ type: "error", error: { type: "authentication_error",
          message: "mande a chave do OmniRoute (x-api-key ou Authorization: Bearer)" } }));
      }

      if (isArgonModel(j.model)) {
        if (Array.isArray(j.tools) && j.tools.length) return await forwardToArgonTools(req, res, j);
        return await forwardToArgon(req, res, j);
      }

      const hx = hxConfig(j.model);
      if (hx) {
        if (Array.isArray(j.tools) && j.tools.length) return await forwardHx(req, res, j, hx);
        return await forwardToArgon(req, res, j);
      }

      // Modelos hibridos: argon-kiro, argon-gemini, argon-opus
      const hib = isHibrido(j.model);
      if (hib) {
        if (Array.isArray(j.tools) && j.tools.length) return await forwardToHibrido(req, res, j, hib);
        // Sem ferramentas: so o Argon puro
        return await forwardToArgon(req, res, j);
      }

      if (argonFlash(j)) {
        buf = Buffer.from(JSON.stringify(j));
        console.log(new Date().toISOString(), "argon-flash ->", FLASH_MODELO);
      }

      const removed = transform(j);
      if (removed) {
        buf = Buffer.from(JSON.stringify(j));
        console.log(new Date().toISOString(), j.model + ": removidas " + removed + " linha(s) de assinatura");
      }

      // 2026-10-29: Sonnet web (claude-web) sempre no esforço máximo
      const m = (j.model || "").toLowerCase();
      if (m.startsWith("cw/") || m === "claude-sonnet-5-5" || m === "claude/claude-sonnet-5-5" || m === "cc/claude-sonnet-5-5") {
        if (!j.reasoning_effort) {
          j.reasoning_effort = "max";
          buf = Buffer.from(JSON.stringify(j));
        }
      }
    } catch (e) {
      // 2026-10-30: handler que já respondeu (cabeçalho enviado) e depois falhou: mandar de novo ao forward dava
      // ERR_HTTP_HEADERS_SENT e derrubava o processo
      if (res.headersSent || res.writableEnded) {
        console.log(new Date().toISOString(), "erro depois de responder:", e && e.message);
        if (!res.writableEnded) res.end();
        return;
      }
    }
    forward(req, res, buf, /\/messages(\?|$)/.test(req.url || ""));
  });
});
// 2026-10-30: última rede de proteção — um erro solto de um pedido não pode derrubar o proxy de todos os modelos
process.on("unhandledRejection", (e) => console.log(new Date().toISOString(), "unhandledRejection:", e && (e.stack || e.message || e)));
process.on("uncaughtException", (e) => console.log(new Date().toISOString(), "uncaughtException:", e && (e.stack || e.message || e)));
server.requestTimeout = 0;
server.timeout = 0;
server.keepAliveTimeout = 65000;
server.listen(LISTEN, "127.0.0.1", () => console.log("antigravity-cc-proxy " + LISTEN + " -> " + UP_HOST + ":" + UP_PORT + " (argon -> :" + ARGON_PORT + ")"));
