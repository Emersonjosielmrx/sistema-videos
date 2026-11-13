#!/usr/bin/env python3
# 06/11/2026: no proxy 20133, quando a Anthropic recusa com 400 "Invalid signature in thinking block"
# (raciocinio de outro modelo no historico), tira os blocos thinking e repete o pedido (ate 2 vezes).
p = '/opt/antigravity-cc-proxy/proxy.mjs'
s = open(p).read()

FUNCS = r'''
// 2026-11-06: 400 "Invalid `signature` in `thinking` block" = raciocinio de OUTRO modelo (reserva) no historico.
// Tira os blocos thinking e repete: 1a tentativa = de todas as mensagens menos a ultima do assistente;
// 2a = de todas, e desliga o raciocinio so neste pedido (sem thinking a ultima mensagem nao precisa comecar com um).
function erroAssinatura(txt) {
  return /Invalid `?signature`? in `?thinking`? block|must start with a thinking block|Expected `?thinking`?/i.test(txt || "");
}
function semThinking(buf, tentativa) {
  let j;
  try { j = JSON.parse(buf.toString("utf8")); } catch { return null; }
  if (!j || !Array.isArray(j.messages)) return null;
  let ultimo = -1;
  j.messages.forEach((m, i) => { if (m && m.role === "assistant") ultimo = i; });
  let n = 0;
  j.messages.forEach((m, i) => {
    if (!m || m.role !== "assistant" || !Array.isArray(m.content)) return;
    if (tentativa === 1 && i === ultimo) return;
    const antes = m.content.length;
    m.content = m.content.filter((b) => !(b && (b.type === "thinking" || b.type === "redacted_thinking")));
    n += antes - m.content.length;
    if (!m.content.length) m.content = [{ type: "text", text: "(...)" }];
  });
  if (tentativa >= 2) {
    if (j.thinking) { delete j.thinking; n++; }
    delete j.context_management;
  }
  return n ? { buf: Buffer.from(JSON.stringify(j)), n } : null;
}
function tentarSemThinking(req, res, buf, ur, tentativa) {
  const partes = [];
  ur.on("data", (c) => partes.push(c));
  ur.on("end", () => {
    let corpo = Buffer.concat(partes);
    const headers = { ...ur.headers };
    let texto = "";
    try {
      const enc = String(headers["content-encoding"] || "").toLowerCase();
      const aberto = enc === "gzip" ? zlib.gunzipSync(corpo)
        : enc === "br" ? zlib.brotliDecompressSync(corpo)
        : enc === "deflate" ? zlib.inflateSync(corpo) : corpo;
      texto = aberto.toString("utf8");
    } catch {}
    if (erroAssinatura(texto)) {
      const novo = semThinking(buf, tentativa + 1);
      if (novo) {
        console.log(new Date().toISOString(), "assinatura invalida: tirados " + novo.n + " bloco(s) thinking, repetindo (tentativa " + (tentativa + 1) + ")");
        return forward(req, res, novo.buf, true, tentativa + 1);
      }
    }
    const trad = texto ? traduzirGrande(texto, buf ? buf.length : 0) : null;
    if (trad !== null) { corpo = Buffer.from(trad); delete headers["content-encoding"]; }
    delete headers["transfer-encoding"];
    headers["content-length"] = String(corpo.length);
    res.writeHead(ur.statusCode, headers);
    res.end(corpo);
  });
}

function forward(req, res, buf, mensagens, tentativa = 0) {'''

old_sig = 'function forward(req, res, buf, mensagens) {'
assert s.count(old_sig) == 1, 'assinatura do forward mudou'
s = s.replace('\n' + old_sig, FUNCS, 1)

old_400 = '    if (mensagens && ur.statusCode === 400) return responderTraduzido(ur, res, buf ? buf.length : 0);'
new_400 = ('    if (mensagens && ur.statusCode === 400 && buf && tentativa < 2) return tentarSemThinking(req, res, buf, ur, tentativa);\n'
           + old_400)
assert s.count(old_400) == 1, 'linha do 400 mudou'
s = s.replace(old_400, new_400, 1)
open(p, 'w').write(s)
print('ok')
