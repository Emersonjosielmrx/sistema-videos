"""Vigia do modelo da IA do FluxIA (cron na VPS 157, a cada 10 min; roda DENTRO do contêiner do FluxIA).

Pedido do dono (08/11): "tem que funcionar tudo com Gemini" e "crie crons para continuar funcionando".
Em 06-07/11 o Antigravity passou a responder 200 com "This version of Antigravity is no longer supported" e o bot
mandou isso aos clientes; depois o gemini-2.5-flash do AI Studio ficou sem cota. Este vigia:
  1. testa os modelos da lista ORDEM (só Gemini; o Sonnet fica só como reserva de emergência no agent.py),
     um pedido curto por modelo, com prazo curto, e descarta resposta que seja aviso de erro (agent.is_bad_reply);
  2. o primeiro que responder de verdade vira o modelo de todos os fluxos (config.model), com versão no histórico;
  3. não mexe se o modelo atual está bom; volta sozinho ao preferido (o 1º da ORDEM) quando ele voltar.
Uso:  python /app/vigia_modelo.py            -> testa e corrige
      python /app/vigia_modelo.py --simular  -> só mostra o que faria
Log: /data/vigia_modelo.log (uma linha por rodada)."""

import asyncio
import json
import sqlite3
import sys
import time

sys.path.insert(0, "/app")
from backend.agent import ask_agent, is_bad_reply  # noqa: E402

# Do mais desejado para o menos: Antigravity 3.8 (volta sozinho quando o Google aceitar de novo), AI Studio.
ORDEM = [
    "agy/gemini-3.8-flash-high",
    "gemini/gemini-3.5-flash-lite",
    "gemini/gemini-2.5-flash-lite",
    "gemini/gemini-3.8-flash",
    "gemini/gemini-3.6-flash",
    "gemini/gemini-3.5-flash",
    "gemini/gemini-2.5-flash",
]
PRAZO = 25  # segundos; o cliente não pode esperar mais que isso pela resposta
DB = "/data/fluxia.db"
LOG = "/data/vigia_modelo.log"


async def funciona(model: str) -> tuple[bool, str]:
    t0 = time.monotonic()
    try:
        text = await ask_agent("Responda em português, em uma frase curta.",
                               [{"role": "user", "content": "Diga só: oi, tudo bem?"}],
                               model=model, max_tokens=60, timeout=PRAZO)
    except Exception as e:
        return False, f"{type(e).__name__} {str(e)[:60]}"
    ms = int((time.monotonic() - t0) * 1000)
    if not text:
        return False, "vazia"
    if is_bad_reply(text):
        return False, f"aviso de erro: {text[:50]}"
    return True, f"{ms} ms"


async def main(simular: bool):
    db = sqlite3.connect(DB)
    flows = [(fid, json.loads(cfg or "{}")) for fid, cfg in db.execute("SELECT id, config FROM flows")]
    atual = {cfg.get("model") for _, cfg in flows}
    resultados = {}
    escolhido = None
    for m in ORDEM:
        ok, info = await funciona(m)
        resultados[m] = ("ok " if ok else "falhou ") + info
        if ok:
            escolhido = m
            break
    linha = time.strftime("%Y-%m-%d %H:%M:%S") + " | " + "; ".join(f"{m}: {r}" for m, r in resultados.items())
    if not escolhido:
        linha += " | NENHUM Gemini respondeu: modelo dos fluxos mantido (o agent.py ainda tenta as reservas)"
    elif atual == {escolhido}:
        linha += f" | mantém {escolhido}"
    else:
        linha += f" | troca {sorted(m or '' for m in atual)} -> {escolhido}"
        if not simular:
            for fid, cfg in flows:
                if cfg.get("model") == escolhido:
                    continue
                old = cfg.get("model")
                cfg["model"] = escolhido
                data = json.dumps(cfg, ensure_ascii=False)
                db.execute("UPDATE flows SET config = ? WHERE id = ?", (data, fid))
                db.execute("INSERT INTO flow_versions (flow_id, config, source, note) VALUES (?, ?, 'painel', ?)",
                           (fid, data, f"vigia do modelo: {old} -> {escolhido} ({resultados.get(old, 'fora da lista')})"))
                db.execute("INSERT INTO events (kind, detail, flow_id) VALUES ('ia', ?, ?)",
                           (f"vigia do modelo trocou {old} -> {escolhido}", fid))
            db.commit()
    print(linha)
    if not simular:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")


if __name__ == "__main__":
    asyncio.run(main("--simular" in sys.argv))
