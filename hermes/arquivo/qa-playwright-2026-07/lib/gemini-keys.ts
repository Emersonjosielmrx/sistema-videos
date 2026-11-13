// gemini-keys.ts — expoe as chaves Gemini que ja' existem nos projetos, pra quando
// uma funcao da UI exigir uma API key de LLM (ex: cadastrar credencial de IA num agente).
// Fonte: D:\credenciais-canais\todas_credenciais.json (bloco googlePalmApi).
// Muitas estao estouradas (429) no endpoint direto do Google; o caminho vivo e' o proxy
// OmniRoute (ver config.ts / README). Estas chaves servem so' pra PREENCHER campos da UI.
import { readFileSync } from "node:fs";

const CRED_PATH = process.env.HERMES_QA_CRED_PATH || "D:/credenciais-canais/todas_credenciais.json";

let cache: string[] | null = null;

export function geminiKeys(): string[] {
  if (cache) return cache;
  try {
    const j = JSON.parse(readFileSync(CRED_PATH, "utf8"));
    const arr: any[] = j.googlePalmApi || [];
    cache = [...new Set(arr.map((x) => x?.data?.apiKey).filter(Boolean))] as string[];
  } catch {
    cache = [];
  }
  return cache;
}

// Uma chave qualquer pra preencher formulario (nao garante que esteja com saldo).
export function anyGeminiKey(): string {
  const k = geminiKeys();
  return k.length ? k[0] : "";
}
