# Acrescenta ao proxy 20133 (/opt/antigravity-cc-proxy/proxy.mjs) o desvio dos modelos "cline-..." para a
# cline-ponte do PC (tunel ssh -R em 127.0.0.1:20160). Idempotente. Uso na VPS: python3 patch_proxy.py
import shutil
import sys
import time

ARQ = "/opt/antigravity-cc-proxy/proxy.mjs"
src = open(ARQ, encoding="utf-8").read()
if "CLINE_PORT" in src:
    print("ja aplicado")
    sys.exit(0)

FUNC = '''
// 2026-10-29: modelos "cline-..." (ex.: cline-opus-5-5) vao para a cline-ponte do PC da dona pelo tunel ssh -R
// (127.0.0.1:20160). A ponte usa o login que ja esta no Cline do PC e chama api.cline.bot. Ver D:\\\\cline-ponte.
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

const server = http.createServer((req, res) => {'''

ANTES = "\nconst server = http.createServer((req, res) => {"
assert src.count(ANTES) == 1
src = src.replace(ANTES, FUNC, 1)

CONTAR_ANTES = '''  const isChat = req.method === "POST" && /\\/(messages|chat\\/completions)(\\?|$)/.test(req.url || "");
  if (!isChat) return forward(req, res, null, false);'''
CONTAR_DEPOIS = '''  const isChat = req.method === "POST" && /\\/(messages|chat\\/completions)(\\?|$)/.test(req.url || "");
  if (!isChat && req.method === "POST" && /\\/messages\\/count_tokens/.test(req.url || "")) {
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
  if (!isChat) return forward(req, res, null, false);'''
assert src.count(CONTAR_ANTES) == 1, "isChat nao achado"
src = src.replace(CONTAR_ANTES, CONTAR_DEPOIS, 1)

ROTA_ANTES = "      if (isArgonModel(j.model)) {"
ROTA_DEPOIS = "      if (isCline(j.model)) return forwardToCline(req, res, buf);\n\n" + ROTA_ANTES
assert src.count(ROTA_ANTES) == 1
src = src.replace(ROTA_ANTES, ROTA_DEPOIS, 1)

bak = ARQ + ".bak-cline-" + time.strftime("%Y%m%d%H%M")
shutil.copy2(ARQ, bak)
open(ARQ, "w", encoding="utf-8").write(src)
print("aplicado; backup", bak)
