// 17/11: Carbon/Hydrogen/Argon completos dependem do User-Agent (CLI novo x IDE)? UMA conta (TK_ENC), de dentro do
// contêiner omniroute (mesmo IP de sempre da conta). Uso: docker exec -e TK_ENC=... -e PROJ=... omniroute node /tmp/teste_carbon.js
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
const PROJ = process.env.PROJ || "aicode-consumers";
const BASE = "https://daily-cloudcode-pa.googleapis.com/v1internal";
const UAS = {
  ide: "antigravity/ide/2.6.0 windows/amd64 google-api-nodejs-client/10.3.0",
  cli: "antigravity/cli/1.5.10 (os_type=windows; arch=amd64; aidev_client; auth_method=oauth)",
  hub: "antigravity/hub/2.32.2 (aidev_client; os_type=windows; arch=amd64)",
  omni_velho: "antigravity/cli/1.4.12 (aidev_client; os_type=darwin; arch=arm64; auth_method=consumer)",
  omni_novo: "antigravity/cli/1.5.10 (aidev_client; os_type=darwin; arch=arm64; auth_method=consumer)",
};

async function listar(nome) {
  const r = await fetch(`${BASE}:fetchAvailableModels`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${TOKEN}`, "User-Agent": UAS[nome] },
    body: JSON.stringify({ project: PROJ }),
  });
  const t = await r.text();
  let ids = [];
  try { ids = Object.entries(JSON.parse(t).models || {}).map(([k, v]) => k + (v.disabled ? "(OFF)" : "")); } catch {}
  console.log(`== lista UA ${nome}: HTTP ${r.status} | gemini-4: ${ids.filter(x => /gemini-4/.test(x)).join(", ") || "(nenhum)"}`);
  if (r.status !== 200) console.log("   ", t.slice(0, 300));
  return ids;
}

async function gerar(modelo, nome) {
  const corpo = {
    project: PROJ, model: modelo, userAgent: "antigravity", requestType: "agent",
    requestId: "agent-" + crypto.randomUUID(),
    request: { contents: [{ role: "user", parts: [{ text: process.env.PERGUNTA || "Quanto e 17*23? Responda so o numero." }] }],
               generationConfig: { maxOutputTokens: +(process.env.MAXOUT || 4000), thinkingConfig: { includeThoughts: true, thinkingLevel: process.env.NIVEL || "high" } }, sessionId: "-" + Math.floor(Math.random() * 1e15) },
  };
  const t0 = Date.now();
  const r = await fetch(`${BASE}:streamGenerateContent?alt=sse`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${TOKEN}`, "User-Agent": UAS[nome], Accept: "text/event-stream" },
    body: JSON.stringify(corpo),
  });
  const t = await r.text();
  let texto = "", pens = 0, uso = null, fim = null;
  for (const l of t.split("\n")) if (l.startsWith("data:")) {
    try {
      const j = JSON.parse(l.slice(5));
      uso = j.response?.usageMetadata || uso;
      fim = j.response?.candidates?.[0]?.finishReason || fim;
      for (const c of (j.response?.candidates || [])) for (const p of (c.content?.parts || [])) {
        if (p.thought) pens += (p.text || "").length; else if (p.text) texto += p.text;
      }
    } catch {}
  }
  console.log(`   gerar ${modelo} (UA ${nome}): HTTP ${r.status} ${((Date.now() - t0) / 1000).toFixed(1)}s ->`, JSON.stringify((texto.trim()||t.slice(0,200)).slice(0,80)), "texto", texto.length, "pensou", pens, "fim", fim, JSON.stringify(uso));
}

(async () => {
  for (const nome of ["omni_velho"]) {
    const ids = [];
    const alvo = [process.env.MODELO || "gemini-4-carbon-high"];
    for (const m of alvo) await gerar(m, nome);
  }
})().catch(e => console.log("erro", e.message));
