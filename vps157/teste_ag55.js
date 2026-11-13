// Teste direto no Google (cloudcode-pa) com UMA conta (alxservicesia), de dentro do conteiner omniroute (mesmo IP).
// Uso: docker exec -e TK_ENC=... omniroute node /tmp/teste_ag55.js
const fs = require("fs");
const crypto = require("crypto");

function chave() {
  const env = fs.readFileSync("/app/data/server.env", "utf8");
  const linha = env.split("\n").find(l => l.trim().startsWith("STORAGE_ENCRYPTION_KEY="));
  const v = linha.split("=").slice(1).join("=").trim().replace(/^["'](.*)["']$/, "$1");
  return crypto.scryptSync(v, "omniroute-field-encryption-v1", 32);
}
function decifra(enc) {
  const [iv, dado, tag] = enc.slice("enc:v1:".length).split(":");
  const d = crypto.createDecipheriv("aes-256-gcm", chave(), Buffer.from(iv, "hex"), { authTagLength: 16 });
  d.setAuthTag(Buffer.from(tag, "hex"));
  return d.update(dado, "hex", "utf8") + d.final("utf8");
}

const TOKEN = decifra(process.env.TK_ENC);
const PROJ = "aicode-consumers";
const BASE = `https://${process.argv[3] || "cloudcode-pa.googleapis.com"}/v1internal`;

function ua(ver) { return `antigravity/${ver} windows/amd64 google-api-nodejs-client/10.3.0`; }

async function quota(ver) {
  const r = await fetch(`${BASE}:fetchAvailableModels`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${TOKEN}`, "User-Agent": ua(ver) },
    body: JSON.stringify({ project: PROJ }),
  });
  const t = await r.text();
  console.log(`\n== fetchAvailableModels (UA ${ver}) HTTP ${r.status}`);
  try {
    const j = JSON.parse(t);
    for (const [k, v] of Object.entries(j.models || {}))
      if (/claude|argon|gpt/i.test(k)) console.log("  ", k, JSON.stringify(v.quotaInfo || {}), v.modelProvider || "");
  } catch { console.log(t.slice(0, 600)); }
}

async function gerar(modelo, ver, creditos) {
  const corpo = {
    project: PROJ, model: modelo, userAgent: "antigravity", requestType: "agent",
    requestId: "agent-" + crypto.randomUUID(),
    request: {
      contents: [{ role: "user", parts: [{ text: "Quanto e 17*23? Responda so o numero." }] }],
      generationConfig: { maxOutputTokens: 2000 },
      sessionId: "-" + Math.floor(Math.random() * 1e15),
    },
  };
  if (creditos) corpo.enabledCreditTypes = ["GOOGLE_ONE_AI"];
  const t0 = Date.now();
  const r = await fetch(`${BASE}:streamGenerateContent?alt=sse`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${TOKEN}`, "User-Agent": ua(ver), Accept: "text/event-stream" },
    body: JSON.stringify(corpo),
  });
  const t = await r.text();
  let texto = "";
  for (const l of t.split("\n")) if (l.startsWith("data:")) {
    try { const j = JSON.parse(l.slice(5)); for (const c of (j.response?.candidates || [])) for (const p of (c.content?.parts || [])) if (p.text && !p.thought) texto += p.text; } catch {}
  }
  console.log(`-- ${modelo} | UA ${ver} | creditos=${creditos ? "sim" : "nao"} -> HTTP ${r.status} ${Date.now() - t0}ms | ${r.ok ? "RESPOSTA: " + texto.trim().slice(0, 80) : t.replace(/\s+/g, " ").slice(0, 400)}`);
  return r.status;
}

(async () => {
  const modo = process.argv[2] || "tudo";
  await quota("2.27.0");
  if (modo === "quota") return;
  if (modo === "semsufixo") { await gerar("claude-opus-5-5", "2.27.0", false); await gerar("claude-opus-5-5-high", "2.1.1", false); return; }
  if (modo === "um") { await gerar("claude-opus-5-5-high", "2.27.0", false); await gerar("claude-sonnet-5-5-high", "2.27.0", false); return; }
  // 1 variavel por vez, comecando pelo que o OmniRoute faz hoje
  await gerar("claude-opus-5-5-high", "2.1.1", false);
  await gerar("claude-opus-5-5-high", "2.27.0", false);
  await gerar("claude-opus-5-5", "2.27.0", false);
  await gerar("claude-opus-5-5-high", "2.27.0", true);
})();
