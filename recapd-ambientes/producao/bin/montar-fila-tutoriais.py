#!/usr/bin/env python3
"""montar-fila-tutoriais.py — Fila de postagem dos vídeos-tutorial de IA (OpenClaw).

Pega os 107 vídeos b-roll (videos-produzidos-v2) já baixados, tira TÍTULO/DESCRIÇÃO
do roteiro .md de cada um, distribui em round-robin pelos canais de IA/automação,
respeitando a cota diária, e agenda (privado + publishAt) espalhado ao longo dos dias.

Gera fila compatível com postar-fila.py. Config no topo (edite se precisar).

Uso: python bin/montar-fila-tutoriais.py
"""
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent

BRT = timezone(timedelta(hours=-3))

# ---------------- CONFIG ----------------
VIDEOS_DIR = Path(r"D:/openclaw-videos/videos-produzidos-v2")
ROTEIROS_DIR = Path(r"D:/openclaw-videos/roteiros")
SAIDA = PROJECT / "_LEIA_POSTAR_VIDEOS" / "fila_tutoriais_ia.json"
QUOTA_DIA = 8            # conservador (limite real varia 9-21/canal)
# DIA_INICIO: None = amanhã | "HOJE" = hoje | "YYYY-MM-DD" = data fixa
DIA_INICIO = "HOJE"
# slots de HOJE à noite (postando ~15:30). Se DIA_INICIO for outro dia, use os do dia todo.
SLOTS = ["16:00", "16:45", "17:30", "18:15", "19:00", "19:45", "20:30", "21:15"]

# Canais de IA/automação (por ID — robusto a nomes com espaço/caractere especial)
CANAIS_IA = [
    ("n6w2HCpYQI6i63cu", "inovarecap(inovare ia"),
    ("nmitE1d50lEJ9j7I", "seebotstia (inovare com ia"),
    ("Pbvr1t6upxkBLYBi", "raiz fabricadeautomacoes0(ia pro"),
    ("1A2FbLAQ1XswAhly", "raiz 5 aulasrevolution (aula com ia"),
    ("rnejQCTSYYBQQhNb", "emersongenc( cerebro digital"),
    ("qVbHRTFgTxilpshH", "raiz 2 emersonjosiel649(emerson ia"),
    ("nYfShqgOuc7VLGUo", "raiz 6 emersongencshin(ia brasileira"),
    ("ikcbItItaj2bNPqh", "raiz 4 solarmundo195 (fala com ia"),
    ("ifBvEBgDU9B1ttax", "en1653964(sintetize a"),
    ("oD2B8wL3p4oyd0UZ", "repost 1 inovarecap(inovare 2 ia"),
    ("eFybCEfRjwxkBwCS", "repost 2 emersongenc"),
    ("oqeQ184UqMDyqt59", "repost fabiovideoseducativos(fabio ia"),
]

TAGS = ["IA", "automação", "n8n", "inteligência artificial", "tutorial", "dev",
        "programação", "chatbot", "agente ia", "automacao", "tecnologia",
        "openai", "no code", "devbr", "workflow"]


def _brt_to_utc_iso(dia_str, hhmm):
    h, m = map(int, hhmm.split(":"))
    y, mo, d = map(int, dia_str.split("-"))
    return (datetime(y, mo, d, h, m, tzinfo=BRT)
            .astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"))


def _pick_slots(n, pool):
    if n <= 1:
        return [pool[0]]
    if n >= len(pool):
        return (pool * ((n // len(pool)) + 1))[:n]
    return [pool[round(i * (len(pool) - 1) / (n - 1))] for i in range(n)]


def _titulo_desc(roteiro_path, fallback_nome):
    """Extrai título (linha '# ...') e descrição (cold open) do roteiro."""
    titulo, cold = None, ""
    if roteiro_path.exists():
        txt = roteiro_path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^#\s+(.+)$", txt, re.MULTILINE)
        if m:
            titulo = re.sub(r"^(Long|Short)\s*:\s*", "", m.group(1)).strip()
        mc = re.search(r'Locução:\s*"([^"]+)"', txt)
        if mc:
            cold = mc.group(1).strip()
    if not titulo:
        titulo = fallback_nome.replace("_", " ").replace("-", " ").strip().title()
    titulo = titulo[:100]
    desc = (f"{titulo}\n\n"
            f"{cold}\n\n" if cold else f"{titulo}\n\n")
    desc += ("🔔 Inscreva-se pra mais conteúdo de IA, automação e programação!\n"
             "💬 Comenta o que achou!\n\n"
             "#IA #automação #n8n #devbr #inteligenciaartificial #tutorial #tecnologia")
    return titulo, desc[:5000]


def main():
    videos = sorted(VIDEOS_DIR.glob("*.mp4"))
    if not videos:
        print(f"ERRO: nenhum vídeo em {VIDEOS_DIR}", file=sys.stderr)
        sys.exit(1)

    if DIA_INICIO == "HOJE":
        dia0 = datetime.now(BRT).strftime("%Y-%m-%d")
    elif DIA_INICIO:
        dia0 = DIA_INICIO
    else:
        dia0 = (datetime.now(BRT) + timedelta(days=1)).strftime("%Y-%m-%d")

    # 1. monta itens (título/descrição do roteiro) — SÓ os que têm roteiro real.
    #    Vídeos sem roteiro na pasta são conteúdo misto (manhwa, sub-workflows) e
    #    NÃO entram na fila dos canais de IA — ficam listados em excluidos.
    itens = []
    excluidos = []
    for v in videos:
        base = v.stem[:-6] if v.stem.endswith("_broll") else v.stem  # tira _broll
        roteiro = ROTEIROS_DIR / f"{base}.md"
        if not roteiro.exists():
            titulo, _ = _titulo_desc(roteiro, base)
            excluidos.append({"arquivo": str(v), "titulo_inferido": titulo})
            continue
        titulo, desc = _titulo_desc(roteiro, base)
        itens.append({"arquivo": str(v), "titulo": titulo, "descricao": desc,
                      "tags": TAGS, "roteiro": str(roteiro)})

    # 2. round-robin pelos canais
    for i, it in enumerate(itens):
        cid, cnome = CANAIS_IA[i % len(CANAIS_IA)]
        it["canal"] = cid
        it["canal_nome"] = cnome

    # 3. por canal: agrupa em dias (cota) + horários espalhados
    fila = []
    por_canal = {}
    for it in itens:
        por_canal.setdefault(it["canal"], []).append(it)
    for cid, lst in por_canal.items():
        por_dia = {}
        for idx, it in enumerate(lst):
            off = idx // QUOTA_DIA
            dia = (datetime.strptime(dia0, "%Y-%m-%d") + timedelta(days=off)).strftime("%Y-%m-%d")
            it["upload_dia"] = dia
            por_dia.setdefault(dia, []).append(it)
        for dia, grupo in por_dia.items():
            for it, hhmm in zip(grupo, _pick_slots(len(grupo), SLOTS)):
                it["publish_at"] = _brt_to_utc_iso(dia, hhmm)
                it["publish_brt"] = f"{dia} {hhmm}"
                it["status"] = "pendente"
                fila.append(it)

    fila.sort(key=lambda it: (it["upload_dia"], it["publish_at"]))
    saida_obj = {"tipo": "tutoriais-ia", "gerado_em": datetime.now(BRT).isoformat(),
                 "quota_por_canal_dia": QUOTA_DIA, "total_itens": len(fila),
                 "excluidos_sem_roteiro": excluidos, "itens": fila}
    SAIDA.write_text(json.dumps(saida_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    # resumo
    print(f"\n✅ Fila gerada: {SAIDA}\n   {len(fila)} vídeos, {len(CANAIS_IA)} canais\n")
    dias = sorted({it["upload_dia"] for it in fila})
    for dia in dias:
        do_dia = [it for it in fila if it["upload_dia"] == dia]
        print(f"── DIA {dia} — {len(do_dia)} uploads ──")
        for cid, cnome in CANAIS_IA:
            chit = [it for it in do_dia if it["canal"] == cid]
            if chit:
                print(f"   [{cnome[:30]:30}] {len(chit)}: "
                      + ", ".join(it["publish_brt"].split()[1] for it in chit))
    print("\n(amostra de títulos)")
    for it in fila[:6]:
        print(f"   {it['publish_brt']}  [{it['canal_nome'][:18]:18}] {it['titulo'][:50]}")
    print(f"\n⚠️ EXCLUÍDOS (sem roteiro, NÃO vão pra fila): {len(excluidos)}")
    for e in excluidos:
        print(f"   - {e['titulo_inferido'][:55]}  ({Path(e['arquivo']).name[:40]})")


if __name__ == "__main__":
    main()
