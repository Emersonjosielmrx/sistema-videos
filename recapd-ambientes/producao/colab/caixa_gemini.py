"""caixa_gemini.py — a CAIXA de treino do melhorador (dona 27/10): o Gemini conserta numa CÓPIA dos arquivos (pasta
separada em D:\\hipercool-materiais\\_melhorador_caixa\\<data>_<nome>), só com Read/Edit/Write (sem Bash, sem acesso ao
original). Depois a sessão Claude faz o conserto real e compara os dois (diff) em linhas\\LONGOS\\COMPARACOES.md.

    python caixa_gemini.py <nome> <tarefa.txt> <arquivo1> [arquivo2 ...]
"""
import difflib
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import juri_longo  # noqa: E402

RAIZ = Path(r"D:\hipercool-materiais\_melhorador_caixa")
MODELOS = [("agy/gemini-3.8-flash-high", 40), ("antigravity/gemini-3.8-flash-tiered", 50)]


def caixa(nome, tarefa, arquivos, modelos=None, texto=False):
    """modelos = [(id, turnos)] (padrão: Gemini 3.8). texto=True (27/10, Argon puro sem ferramentas): manda o arquivo no
    prompt e aplica as trocas {"antes","depois"} que ele devolver — mesma caixa, mesmo diff."""
    modelos = modelos or MODELOS
    pasta = RAIZ / f"{datetime.now():%Y%m%d_%H%M%S}_{nome}"
    (pasta / "original").mkdir(parents=True)
    for a in arquivos:
        shutil.copy2(a, pasta / Path(a).name)
        shutil.copy2(a, pasta / "original" / Path(a).name)
    prompt = (f"{tarefa}\n\nOs arquivos estão NESTA pasta: {', '.join(Path(a).name for a in arquivos)}. Leia e edite "
              "SÓ o que está nesta pasta (não procure nem abra arquivos fora dela). Edite SÓ eles "
              "(Edit/Write). A pasta 'original' é só referência, não mexa. Faça a mudança mínima que resolve, sem "
              "quebrar o resto (quem chama a função continua funcionando igual), e escreva no fim, em 3–6 linhas: o que "
              "mudou, por quê e como testar.")
    resumo = None
    t0 = time.time()
    for m, turnos in modelos:
        try:
            if texto:
                resumo = _editar_por_texto(tarefa, pasta, arquivos, m)
            else:
                cmd_tools = ("Read,Edit,Write,Glob,Grep", "Bash,WebFetch,WebSearch,Agent")
                resumo = _chamar_editor(prompt, pasta, m, turnos, cmd_tools)
            break
        except Exception as e:  # noqa: BLE001
            print(f"[caixa] {m} falhou: {str(e)[:200]}", flush=True)
    (pasta / "tempo_s.txt").write_text(str(round(time.time() - t0)), encoding="utf-8")
    dif = []
    for a in arquivos:
        n = Path(a).name
        dif += difflib.unified_diff((pasta / "original" / n).read_text(encoding="utf-8").splitlines(),
                                    (pasta / n).read_text(encoding="utf-8").splitlines(),
                                    f"original/{n}", f"gemini/{n}", lineterm="")
    (pasta / "gemini.diff").write_text("\n".join(dif), encoding="utf-8")
    (pasta / "resumo_gemini.txt").write_text(resumo or "(sem resposta)", encoding="utf-8")
    print(f"[caixa] {pasta} — {len(dif)} linhas de diff", flush=True)
    return pasta


def _editar_por_texto(tarefa, pasta, arquivos, modelo):
    import json
    import re
    corpo = "\n\n".join(f"=== {Path(a).name} ===\n{(pasta / Path(a).name).read_text(encoding='utf-8')}" for a in arquivos)
    prompt = (f"{tarefa}\n\nArquivos:\n{corpo}\n\nFaça a mudança mínima que resolve, sem quebrar o resto. Responda SÓ o "
              'JSON {"trocas": [{"arquivo": "nome.py", "antes": "trecho EXATO que existe hoje (copie igual, com a '
              'indentação)", "depois": "como fica"}], "resumo": "3-6 linhas: o que mudou, por quê e como testar"}')
    import urllib.request
    cfg = json.loads(juri_longo.CCV_CONFIG.read_text("utf-8"))
    corpo_req = json.dumps({"model": modelo, "max_tokens": 8000,
                            "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    req = urllib.request.Request(cfg["gateway"].rstrip("/") + "/v1/messages", data=corpo_req,
                                 headers={"x-api-key": cfg["chave"], "Authorization": "Bearer " + cfg["chave"],
                                          "content-type": "application/json", "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=900) as r:
        resp = "".join(c.get("text", "") for c in json.load(r).get("content", []))
    (pasta / "resposta_texto.txt").write_text(resp, encoding="utf-8")
    d = json.loads(re.search(r"\{.*\}", resp, re.S).group(0))
    for t in d.get("trocas") or []:
        f = pasta / Path(t["arquivo"]).name
        s = f.read_text(encoding="utf-8")
        if t["antes"] not in s:
            raise RuntimeError(f"trecho 'antes' não existe em {f.name}: {t['antes'][:80]!r}")
        f.write_text(s.replace(t["antes"], t["depois"], 1), encoding="utf-8")
    return d.get("resumo", "")


def _chamar_editor(prompt, pasta, modelo, turnos, ferramentas):
    import json
    import os
    cfg = json.loads(juri_longo.CCV_CONFIG.read_text("utf-8"))
    env = dict(os.environ, ANTHROPIC_BASE_URL=cfg["gateway"], ANTHROPIC_AUTH_TOKEN=cfg["chave"],
               ANTHROPIC_MODEL=modelo, ANTHROPIC_DEFAULT_OPUS_MODEL=modelo, ANTHROPIC_DEFAULT_SONNET_MODEL=modelo,
               ANTHROPIC_DEFAULT_HAIKU_MODEL=modelo, ANTHROPIC_SMALL_FAST_MODEL=modelo,
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
    env.pop("ANTHROPIC_API_KEY", None)
    # 27/10: na 1ª rodada o Gemini LEU o arquivo real (editado pela sessão Claude) e copiou — caixa sem isolamento.
    # Agora: nega Read/Edit/Write/Grep/Glob nas pastas reais dos projetos (só a caixa fica visível).
    reais = ["recapd-ambientes", "hipercool-videos", "video-fila", "postador-de-videos", "manhwa-react", "veo",
             "claude-code-video", "hipercool-materiais/bin", "hipercool-materiais/comum"]
    nega = [f"{f}(//d/{r}/**)" for r in reais for f in ("Read", "Edit", "Write", "Grep", "Glob")]
    cfg_caixa = pasta / "_settings_caixa.json"
    cfg_caixa.write_text(json.dumps({"permissions": {"deny": nega}}), encoding="utf-8")
    cmd = [juri_longo._exe(), "-p", "--output-format", "json", "--max-turns", str(turnos), "--setting-sources", "project",
           "--settings", str(cfg_caixa),
           "--allowedTools", ferramentas[0], "--disallowedTools", ferramentas[1], "--add-dir", str(pasta)]
    _, saida = juri_longo.executar(cmd, pasta, 1800, env=env, entrada=prompt.encode("utf-8"))
    res = next((json.loads(l) for l in reversed(saida.strip().splitlines()) if l.startswith("{")), None)
    if not res:
        raise RuntimeError(saida[-300:])
    return (res.get("result") or "").strip()


if __name__ == "__main__":
    # CAIXA_MODELO=<id> troca o modelo; CAIXA_TEXTO=1 = sem ferramentas (arquivo no prompt)
    _m = os.environ.get("CAIXA_MODELO")
    caixa(sys.argv[1], Path(sys.argv[2]).read_text(encoding="utf-8"), sys.argv[3:],
          modelos=[(_m, 40)] if _m else None, texto=os.environ.get("CAIXA_TEXTO") == "1")
