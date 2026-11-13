#!/usr/bin/env python3
# 06/11/2026: Opus/Sonnet 5.5 do Antigravity (ag-opus-5-5 / ag-sonnet-5-5) mandam o raciocinio partido em varios blocos
# "thinking" pequenos e SEM assinatura. O Claude Code mostra cada um como "Thought for 0s" (parece loop/erro) e, quando
# a conversa volta pra conta paga, a Anthropic recusa esses blocos (assinatura invalida).
# Conserto no proxy 20133: para modelos ag-*, junta os blocos thinking seguidos num so e renumera os indices.
p = '/opt/antigravity-cc-proxy/proxy.mjs'
s = open(p).read()

FUNCS = r'''
// 2026-11-06: modelos "ag-*" (Opus/Sonnet 5.5 do Antigravity) partem o raciocinio em varios blocos thinking pequenos
// e sem assinatura -> no Claude Code aparecem varias linhas "Thought for 0s". Este filtro de SSE junta os blocos
// thinking seguidos num so (renumerando os indices) antes de entregar ao cliente.
function juntarThinkingSSE(ur, res) {
  let resto = "";
  let idxCliente = -1;        // ultimo indice entregue ao cliente
  const mapa = new Map();     // indice do upstream -> indice do cliente
  let thinkingAberto = false; // ha um bloco thinking aberto no cliente
  let fecharPendente = false; // o upstream fechou o thinking; so fecha no cliente se vier outro tipo
  const sai = (ev) => res.write("event: " + ev.type + "\ndata: " + JSON.stringify(ev) + "\n\n");
  const fecharThinking = () => {
    if (thinkingAberto) { sai({ type: "content_block_stop", index: idxCliente }); thinkingAberto = false; }
    fecharPendente = false;
  };
  const tratar = (bloco) => {
    const linha = bloco.split("\n").find((l) => l.startsWith("data:"));
    if (!linha) { if (bloco.trim()) res.write(bloco + "\n\n"); return; }
    let ev;
    try { ev = JSON.parse(linha.slice(5).trim()); } catch { res.write(bloco + "\n\n"); return; }
    if (ev.type === "content_block_start") {
      const tipo = ev.content_block && ev.content_block.type;
      if (tipo === "thinking" && thinkingAberto) { mapa.set(ev.index, idxCliente); fecharPendente = false; return; }
      fecharThinking();
      idxCliente++;
      mapa.set(ev.index, idxCliente);
      if (tipo === "thinking") thinkingAberto = true;
      return sai({ ...ev, index: idxCliente });
    }
    if (ev.type === "content_block_delta") {
      const i = mapa.has(ev.index) ? mapa.get(ev.index) : idxCliente;
      if (thinkingAberto && i === idxCliente) fecharPendente = false;
      return sai({ ...ev, index: i });
    }
    if (ev.type === "content_block_stop") {
      const i = mapa.has(ev.index) ? mapa.get(ev.index) : idxCliente;
      if (thinkingAberto && i === idxCliente) { fecharPendente = true; return; }
      return sai({ ...ev, index: i });
    }
    if (ev.type === "message_delta" || ev.type === "message_stop") fecharThinking();
    res.write(bloco + "\n\n");
  };
  ur.setEncoding("utf8");
  ur.on("data", (c) => {
    resto += c.replace(/\r\n/g, "\n");
    let k;
    while ((k = resto.indexOf("\n\n")) >= 0) { const b = resto.slice(0, k); resto = resto.slice(k + 2); tratar(b); }
  });
  ur.on("end", () => { if (resto.trim()) tratar(resto); fecharThinking(); res.end(); });
  ur.on("error", () => res.end());
}

function forward(req, res, buf, mensagens, tentativa = 0) {'''

old_sig = '\nfunction forward(req, res, buf, mensagens, tentativa = 0) {'
assert s.count(old_sig) == 1, 'forward mudou'
s = s.replace(old_sig, FUNCS, 1)

# dentro do forward: para ag-* em stream com 200, passa pelo filtro
old_pipe = '''    if (mensagens && ur.statusCode === 400 && buf && tentativa < 2) return tentarSemThinking(req, res, buf, ur, tentativa);
    if (mensagens && ur.statusCode === 400) return responderTraduzido(ur, res, buf ? buf.length : 0);
    res.writeHead(ur.statusCode || 502, ur.headers);
    ur.pipe(res);'''
new_pipe = '''    if (mensagens && ur.statusCode === 400 && buf && tentativa < 2) return tentarSemThinking(req, res, buf, ur, tentativa);
    if (mensagens && ur.statusCode === 400) return responderTraduzido(ur, res, buf ? buf.length : 0);
    if (mensagens && ur.statusCode === 200 && agModelo(buf) && /event-stream/.test(String(ur.headers["content-type"] || ""))
        && !String(ur.headers["content-encoding"] || "")) {
      const h = { ...ur.headers }; delete h["content-length"];
      res.writeHead(200, h);
      return juntarThinkingSSE(ur, res);
    }
    res.writeHead(ur.statusCode || 502, ur.headers);
    ur.pipe(res);'''
assert s.count(old_pipe) == 1, 'trecho do pipe mudou'
s = s.replace(old_pipe, new_pipe, 1)

AG = r'''
function agModelo(buf) {
  if (!buf) return false;
  const m = /"model"\s*:\s*"([^"]+)"/.exec(buf.toString("utf8", 0, Math.min(buf.length, 4000)));
  return !!(m && /^(ag-|antigravity\/claude-(opus|sonnet)-5)/.test(m[1]));
}
'''
s = s.replace('\nfunction juntarThinkingSSE(', AG + '\nfunction juntarThinkingSSE(', 1)
open(p, 'w').write(s)
print('ok')
