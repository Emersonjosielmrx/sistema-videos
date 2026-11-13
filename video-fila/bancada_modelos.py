# -*- coding: utf-8 -*-
r"""bancada_modelos.py — BANCADA: qual Argon chega mais perto do Opus 5.5? (dona 29/10: "fizemos vários modelos Argon/
Gemini e tem as notas deles; quero comparar com o Opus 5.5 e o Gemini, ver qual versão do Argon chega mais perto do
Opus e se tiver ideia de melhorar um, bom também").

O que faz (nada é aplicado — ambiente separado, só arquivos em estado\central\bancada\<data>\):
  1. Pega a MESMA tarefa real que o melhorador dos Cortes manda ao decisor (cortes_melhorador._prompt: júris do
     lote, alavancas permitidas, lições, brief do central) e manda em paralelo para cada candidato (cortes_juri.chamar_json,
     mesmo caminho da produção). Guarda resposta, tempo, erro e se as alavancas passam na trava.
  2. O Opus 5.5 (cc/claude-opus-5-5) responde a mesma tarefa = REFERÊNCIA.
  3. O Opus julga cada resposta (sem saber de quem é): nota 0–10 em diagnóstico (bate com o dado?), alavancas (úteis,
     na faixa, seguem D1 — curto/loop/elegibilidade), risco (algo que piora o vídeo ou fere regra), e "distância da
     minha resposta"; mais uma IDEIA de como melhorar cada Argon (prompt/dupla).
  4. Grava BANCADA.md (tabela) + resultado.json e acrescenta o resumo em D:\gemini-argo\COMPARACAO_MODELOS.md.

    D:\recapd-ambientes\producao\venv\Scripts\python.exe bancada_modelos.py   # (esse Python tem psutil, que o cortes_juri usa)
    python bancada_modelos.py                       # candidatos padrão (os que responderem ao teste de 5 tokens)
    python bancada_modelos.py --modelos a,b,c       # só esses
    python bancada_modelos.py --sem-juiz            # sem a nota do Opus (só tempo/trava)
Custo: 1 chamada por candidato (Argon ~1–5 min) + 2 do Opus (referência + juiz). Sem Kiro.
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — regra da dona: nenhum processo filho abre janela na tela
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
PASTA = BASE / "estado" / "central" / "bancada"
COMPARACAO = Path(r"D:\gemini-argo\COMPARACAO_MODELOS.md")
CANDIDATOS = ["gemini-4-argon", "argon-pro", "argon-gemini", "argon-flash", "agy/gemini-3.8-flash-high",
              "antigravity/gemini-3-flash", "antigravity/claude-opus-4-6-thinking"]
REFERENCIA = "cc/claude-opus-5-5"
SEM_JANELA = 0x08000000


def log(m):
    print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def _responde(modelo, timeout=150):
    """Teste de 5 tokens pelo MESMO gateway que o chamar_json usa (:20133 — o Argon só vive lá; pela :20128 ele estoura)."""
    import urllib.request
    try:
        cfg = json.loads(Path(r"D:\claude-code-video\config.json").read_text("utf-8"))
        body = json.dumps({"model": modelo, "max_tokens": 5, "stream": False,
                           "messages": [{"role": "user", "content": "responda só: ok"}]}).encode()
        req = urllib.request.Request(cfg["gateway"].rstrip("/") + "/v1/messages", data=body,
                                     headers={"content-type": "application/json", "x-api-key": cfg["chave"],
                                              "anthropic-version": "2023-06-01"})
        urllib.request.urlopen(req, timeout=timeout).read()
        return True
    except Exception:  # noqa: BLE001
        return False


def _tarefa():
    """Prompt real do decisor dos Cortes (+ brief do central, se existir)."""
    import cortes_melhorador as cmel
    c = cmel._ler(cmel.CFG, {})
    est = cmel._ler(cmel.ESTADO, {"mudancas": [], "decisoes": [], "uso": {}})
    prompt, ultimos, _ = cmel._prompt(est, c)
    brief = BASE / "estado" / "central" / "brief_cortes.md"
    if brief.is_file():
        prompt += "\n\n## BRIEF DO MELHORADOR CENTRAL (dados reais)\n" + brief.read_text(encoding="utf-8")[:6000]
    return prompt, ultimos, c


def _rodar(modelo, prompt, c, pasta):
    import cortes_juri as cj
    import cortes_melhorador as cmel
    t = time.time()
    try:
        prazo = 420 if "argon" in modelo else 900
        r, erro = cj.chamar_json(prompt, cmel.LINHA, modelo, timeout=prazo, max_turnos=30), None
    except Exception as e:  # noqa: BLE001
        r, erro = {}, f"{type(e).__name__}: {str(e)[:200]}"
    aj = cmel._ler(cmel.AJUSTES, {})
    val = []
    for a in (r or {}).get("alavancas") or []:
        spec = c["alavancas"].get(str(a.get("chave")))
        campo = str(a.get("chave")).split(":", 1)[-1]
        ok = bool(spec) and cmel._validar(spec, a.get("op", "set"), a.get("valor"), aj.get(campo)) not in (None, aj.get(campo))
        val.append({"chave": a.get("chave"), "op": a.get("op"), "valor": a.get("valor"), "passa_trava": ok})
    out = {"modelo": modelo, "segundos": round(time.time() - t), "erro": erro, "alavancas": val, "resposta": r}
    (pasta / (modelo.replace("/", "_") + ".json")).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"{modelo}: {out['segundos']} s, erro={erro}, alavancas={[(v['chave'], v['passa_trava']) for v in val]}")
    return out


def _julgar(resultados, ref, pasta):
    """Opus 5.5 dá nota a cada resposta (anônimas) comparando com a dele; devolve {rotulo: {notas, ideia}}."""
    import claude_client as cc
    rot = {}
    anon = []
    for i, r in enumerate(resultados):
        rot[f"R{i + 1}"] = r["modelo"]
        anon.append(f"### R{i + 1}\n" + json.dumps(r["resposta"], ensure_ascii=False)[:5000])
    prompt = (
        "Você é o juiz de uma bancada de modelos que decidem MELHORIAS para Shorts (alavancas num json de ajustes). "
        "Abaixo está a SUA resposta de referência para a mesma tarefa e as respostas anônimas R1..Rn. Regras que valem "
        "mais que gosto: (D1) 60% dos Shorts não entram no lote do feed; quem entra para em ~1.200 views; sai quem é "
        "assistido inteiro (15–25 s, loop); nunca promover por nota de júri; comparar só vídeos elegíveis. "
        "Para CADA Rk dê, em JSON: {\"Rk\": {\"diagnostico\": 0-10 (bate com os dados?), \"alavancas\": 0-10 (úteis, "
        "na faixa, seguem D1), \"risco\": 0-10 (10 = sem risco de piorar/ferir regra), \"distancia\": 0-10 (10 = igual "
        "à sua referência), \"nota\": média, \"ideia\": \"1 frase: o que mudar no prompt/dupla desse modelo para chegar "
        "mais perto\"}}. Responda SÓ o JSON.\n\n### REFERÊNCIA (sua)\n" + json.dumps(ref.get("resposta"), ensure_ascii=False)[:6000]
        + "\n\n" + "\n\n".join(anon))
    texto = cc.generate_text(prompt, max_tokens=2500, temperature=0.2, model=REFERENCIA, timeout=600) or ""
    (pasta / "juiz_resposta.txt").write_text(texto, encoding="utf-8")
    m = re.search(r"\{.*\}", texto, re.S)
    try:
        notas = json.loads(m.group(0)) if m else {}
    except ValueError:
        notas = {}
    return {rot.get(k, k): v for k, v in notas.items() if isinstance(v, dict)}


def main(a):
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    modelos = a[a.index("--modelos") + 1].split(",") if "--modelos" in a else CANDIDATOS
    sem_juiz = "--sem-juiz" in a
    pasta = PASTA / datetime.now().strftime("%Y%m%d_%H%M")
    pasta.mkdir(parents=True, exist_ok=True)
    prompt, lote, c = _tarefa()
    (pasta / "tarefa.md").write_text(prompt, encoding="utf-8")
    vivos = []
    for m in modelos:
        ok = _responde(m)
        log(f"teste {m}: {'responde' if ok else 'NÃO responde (fora da bancada)'}")
        if ok:
            vivos.append(m)
    log(f"lote {lote} | candidatos vivos: {vivos}")
    with ThreadPoolExecutor(max(1, len(vivos))) as ex:
        res = list(ex.map(lambda m: _rodar(m, prompt, c, pasta), vivos))
    ref = None
    if not sem_juiz:
        if _responde(REFERENCIA):
            ref = _rodar(REFERENCIA, prompt, c, pasta)
        else:
            log(f"{REFERENCIA} sem cota agora: bancada sem juiz")
    notas = _julgar(res, ref, pasta) if ref and ref.get("resposta") else {}
    linhas = ["# Bancada de modelos — " + datetime.now().strftime("%d/%m %H:%M") + f" (lote {', '.join(lote)})", "",
              "| modelo | s | erro | alavancas (passam trava) | diagnóstico | alavancas | risco | distância do Opus | NOTA | ideia |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    tabela = []
    for r in res + ([ref] if ref else []):
        n = notas.get(r["modelo"], {})
        al = f"{sum(1 for v in r['alavancas'] if v['passa_trava'])}/{len(r['alavancas'])}"
        linhas.append(f"| {r['modelo']} | {r['segundos']} | {(r['erro'] or '')[:40]} | {al} | {n.get('diagnostico', '—')} | "
                      f"{n.get('alavancas', '—')} | {n.get('risco', '—')} | {n.get('distancia', '—')} | **{n.get('nota', '—')}** | "
                      f"{str(n.get('ideia', '')).replace('|', '/')[:160]} |")
        tabela.append({"modelo": r["modelo"], "segundos": r["segundos"], "erro": r["erro"], "alavancas": al, **n})
    resumo = "\n".join(linhas) + "\n"
    (pasta / "BANCADA.md").write_text(resumo, encoding="utf-8")
    (pasta / "resultado.json").write_text(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), "lote": lote,
                                                       "tabela": tabela}, ensure_ascii=False, indent=1), encoding="utf-8")
    (PASTA / "ultima.json").write_text((pasta / "resultado.json").read_text(encoding="utf-8"), encoding="utf-8")
    try:  # documento comum de todos os chats (regra: só acrescentar)
        with COMPARACAO.open("a", encoding="utf-8") as f:
            f.write(f"\n\n### {datetime.now():%d/%m %H:%M} — CENTRAL — bancada do decisor dos Cortes (juiz: Opus 5.5)\n"
                    f"Pasta: `{pasta}`. Mesma tarefa real para todos; nada aplicado.\n\n" + "\n".join(linhas[2:]) + "\n")
    except OSError:
        pass
    print(resumo)
    log(f"bancada gravada em {pasta}")


if __name__ == "__main__":
    main(sys.argv[1:])
