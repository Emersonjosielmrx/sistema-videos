#!/usr/bin/env python3
# 06/11/2026 (dona): "Opus Automatico (gratis)" (genspark-opus-5-5) tenta PRIMEIRO o Opus 5.5 do Antigravity
# (combo ag-opus-5-5). Se ele nao der 200 (sem cota/erro), segue o caminho de antes (Genspark -> substitutos).
# Tambem troca o Opus 4.6 (morto: "no longer available") por ag-opus-5-5 nos substitutos.
p = '/opt/antigravity-cc-proxy/proxy.mjs'
s = open(p).read()

old46 = 'substitutos: ["antigravity/claude-opus-4-6-thinking", "cc/claude-opus-5-5", "cc/claude-opus-4-8"],'
assert s.count(old46) == 2, 'substitutos mudaram'
s = s.replace(old46, 'substitutos: ["ag-opus-5-5", "cc/claude-opus-5-5", "cc/claude-opus-4-8"],')
s = s.replace('nomeSubstituto: "Opus gratis (4.6) / pago (5.5)", tentativas: 5 },\n  // 03/11',
              'nomeSubstituto: "Opus 5.5 Antigravity / pago (5.5)", tentativas: 5, primeiro: "ag-opus-5-5" },\n  // 03/11', 1)
assert 'primeiro: "ag-opus-5-5"' in s, 'nao marcou primeiro'

FUNC = r'''
// 2026-11-06: tenta um modelo do OmniRoute ANTES da ponte (ex.: ag-opus-5-5 no "Opus Automatico gratis").
// 200 -> entrega ao cliente (com os thinking juntados) e devolve true. Outro status -> descarta e devolve false.
// Sem cota (429) -> pula esse modelo por 10 min para nao atrasar os proximos pedidos.
const primeiroForaAte = new Map();
function tentarPrimeiro(req, res, j, modelo) {
  if ((primeiroForaAte.get(modelo) || 0) > Date.now()) return Promise.resolve(false);
  const b = { ...j, model: modelo };
  limparThinkingVazio(b);
  const payload = Buffer.from(JSON.stringify(b));
  const headers = { ...req.headers, host: UP_HOST + ":" + UP_PORT, "content-length": String(payload.length) };
  delete headers["transfer-encoding"]; delete headers["accept-encoding"];
  return new Promise((ok) => {
    const up = http.request({ host: UP_HOST, port: UP_PORT, method: "POST", path: req.url, headers }, (ur) => {
      if (ur.statusCode !== 200) {
        if (ur.statusCode === 429) primeiroForaAte.set(modelo, Date.now() + 10 * 60000);
        console.log(new Date().toISOString(), "[PRIMEIRO]", modelo, "deu", ur.statusCode, "-> segue o caminho normal");
        ur.resume(); return ok(false);
      }
      console.log(new Date().toISOString(), "[PRIMEIRO]", j.model, "-> respondido por", modelo);
      const h = { ...ur.headers }; delete h["content-length"];
      res.writeHead(200, h);
      if (/event-stream/.test(String(ur.headers["content-type"] || ""))) juntarThinkingSSE(ur, res);
      else ur.pipe(res);
      ok(true);
    });
    up.on("error", () => ok(false));
    res.on("close", () => { if (!res.writableFinished) up.destroy(); });
    up.end(payload);
  });
}

function forward(req, res, buf, mensagens, tentativa = 0) {'''
old_sig = '\nfunction forward(req, res, buf, mensagens, tentativa = 0) {'
assert s.count(old_sig) == 1
s = s.replace(old_sig, FUNC, 1)

old_h = '''      if (ponte) {
        PEDIDO.enterWith({ sinal: ac.signal, ...ponte });'''
new_h = '''      if (ponte) {
        if (ponte.primeiro && (await tentarPrimeiro(req, res, j, ponte.primeiro))) return;
        PEDIDO.enterWith({ sinal: ac.signal, ...ponte });'''
assert s.count(old_h) == 1, 'handler da ponte mudou'
s = s.replace(old_h, new_h, 1)
open(p, 'w').write(s)
print('ok')
