"""supervisor_melhorador.py — confere se o melhorador central ligado está fazendo o trabalho da sessão Claude
(dona 29/10: "veja se o melhorador ligado está mesmo fazendo o seu trabalho e supervisione ele").

A cada volta (tarefa SupervisorMelhorador, 1 h) olha as últimas 2 h e grava em logs\\supervisor_melhorador.md:
- PARADO: nenhuma rodada de linha há mais de 3 h (só "RAM baixa"/"nada com pressão").
- PRESO NA RAM: >= 4 voltas seguidas puladas por RAM.
- FALHA: rc != 0 ou "nenhum decisor respondeu".
- MUDOU DE NOVO: a mesma alavanca dos Cortes mudou 2x antes de >= 3 Shorts julgados (vigia não teve tempo).
- PROVA FRACA: alavanca aplicada sem citar Short/quadro no porquê.
- REGRA DE TÍTULO/ROTEIRO SOBRE LAYOUT (erro clássico do Gemini: alavanca de texto não muda posição).
Avisa no Telegram (avisos.enviar, resumo) só PARADO, FALHA repetida e MUDOU DE NOVO.
"""
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
LOG_CENTRAL = AQUI / "logs" / "melhorador_central.log"
SAIDA = AQUI / "logs" / "supervisor_melhorador.md"
ESTADO_CORTES = AQUI / "linhas" / "CORTES" / "melhorador_estado.json"
EVOL_CORTES = AQUI / "linhas" / "CORTES" / "evolucao.jsonl"
LAYOUT = re.compile(r"\b(y\s*=|zona segura|margem|posi[cç]|pixel|px\b|canto|topo da tela|sobrep)", re.I)
PROVA = re.compile(r"(sem-obra-\w+|_cap\d+_\d{8}|q\d{2})")


def _linhas_log(desde):
    out = []
    for l in LOG_CENTRAL.read_text("utf-8", errors="replace").splitlines():
        m = re.match(r"\[(\d\d)/(\d\d) (\d\d):(\d\d)(?::\d\d)?\]", l)
        if not m:
            continue
        t = datetime(datetime.now().year, int(m[2]), int(m[1]), int(m[3]), int(m[4]))
        if t >= desde:
            out.append((t, l))
    return out


def _julgados_depois(em):
    n = 0
    if EVOL_CORTES.exists():
        for l in EVOL_CORTES.read_text("utf-8").splitlines():
            try:
                d = json.loads(l)
            except ValueError:
                continue
            n += d.get("nota") is not None and str(d.get("data", "")) > em
    return n


def conferir(horas=2):
    agora = datetime.now()
    achados, alertas = [], []
    rec = _linhas_log(agora - timedelta(hours=max(horas, 3)))
    rodou = [t for t, l in rec if re.search(r"\]\s+\w+: (APLICAR|sombra) ->", l)]
    if not rodou:
        achados.append("PARADO: nenhuma linha rodou nas últimas 3 h")
        alertas.append(achados[-1])
    ram = 0
    for _t, l in reversed(rec):
        if "pressão:" in l:
            continue
        if "RAM livre" in l:
            ram += 1
        elif re.search(r"(APLICAR|sombra) ->|nada com pressão", l):
            break
    if ram >= 4:
        achados.append(f"PRESO NA RAM: {ram} voltas seguidas puladas por RAM baixa")
    falhas = [l for t, l in rec if t >= agora - timedelta(hours=horas)
              and (re.search(r"rc=(?!0 )\d+", l) or "nenhum decisor respondeu" in l)]
    for l in falhas:
        achados.append("FALHA: " + l[:250])
    if len(falhas) >= 2:
        alertas.append(f"{len(falhas)} falhas do melhorador em {horas} h")
    try:
        est = json.loads(ESTADO_CORTES.read_text("utf-8"))
    except (OSError, ValueError):
        est = {"mudancas": []}
    mud = est.get("mudancas", [])
    for a, b in zip(mud, mud[1:]):
        if a["campo"] == b["campo"] and _julgados_depois(a["em"]) - _julgados_depois(b["em"]) < 3 \
                and datetime.fromisoformat(b["em"]) >= agora - timedelta(hours=horas):
            achados.append(f"MUDOU DE NOVO: cortes {b['campo']} em {a['em'][11:16]} e {b['em'][11:16]} sem 3 Shorts julgados")
            alertas.append(achados[-1])
    for m in mud:
        if datetime.fromisoformat(m["em"]) < agora - timedelta(hours=horas):
            continue
        if not PROVA.search(str(m.get("porque", ""))):
            achados.append(f"PROVA FRACA: cortes {m['campo']} ({m['em'][11:16]}) sem Short/quadro no porquê")
        novo = m["depois"][-1] if isinstance(m["depois"], list) and m["depois"] else m["depois"]
        if m["campo"] in ("regras_titulo", "regras_roteiro") and LAYOUT.search(str(novo)):
            achados.append(f"REGRA DE TEXTO SOBRE LAYOUT: cortes {m['campo']} = {str(novo)[:160]}")
    linha = f"\n## {agora:%d/%m %H:%M} — {'OK' if not achados else str(len(achados)) + ' achado(s)'}\n" + \
            "".join(f"- {a}\n" for a in achados) + \
            f"- rodadas de linha em 3 h: {len(rodou)}; mudanças dos Cortes vigiando: " \
            f"{sum(m['estado'] == 'vigiando' for m in mud)}\n"
    with open(SAIDA, "a", encoding="utf-8") as f:
        f.write(linha)
    if alertas and "--sem-aviso" not in sys.argv:
        try:
            import avisos
            avisos.enviar("Supervisor do melhorador: " + " | ".join(alertas), "supervisor_melhorador",
                          chave="<SEGREDO_REMOVIDO>")
        except Exception as e:  # noqa: BLE001
            with open(SAIDA, "a", encoding="utf-8") as f:
                f.write(f"- aviso Telegram falhou: {e}\n")
    print(linha)
    return achados


if __name__ == "__main__":
    conferir()
