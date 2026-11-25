r"""tendencias_30dias.py — 24/11 dona ("analise como esses projetos podem melhorar nossos vídeos... pensando em melhorar o
pesquisador que não acha nada"; "instale os que você recomendou e implemente"). O pesquisador antigo só buscava
REPOSITÓRIOS no GitHub (1.844 achados, 9 implantados) e nada no sistema olhava o que está em alta AGORA (anime_discover
ordena por views totais; buscar_fontes_campeas só olha nossos canais).

Usa o last30days-skill (github.com/mvanhorn/last30days-skill, MIT) instalado no notebook asusx
(~/ferramentas/last30days-skill, yt-dlp novo no venv) — roda LÁ, não no PC1 (regra: PC1 livre). Fontes só sem conta
nossa: YouTube (transcrição pelo yt-dlp, 1 por vez) e Reddit. Nada fala como conta.

Faz as perguntas de PERGUNTAS (nicho dos nossos canais), traz os .md e grava:
  D:\video-fila\tendencias\AAAA-MM-DD\<pergunta>.md  (relatório bruto: vídeos dos últimos 30 dias, views, trechos)
  D:\video-fila\tendencias\TENDENCIAS.md             (resumo do dia: títulos campeões + ganchos das transcrições)
    python tendencias_30dias.py            # todas as perguntas
    python tendencias_30dias.py --uma "x"  # só uma
Tarefa Tendencias30Dias (1x por dia, 06:40). Desliga: estado\tendencias.off.
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(r"D:\video-fila")
SAIDA = BASE / "tendencias"
DESLIGA = BASE / "estado" / "tendencias.off"
HOST = "asusx"
REMOTO = "~/ferramentas/last30days-skill"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe" if Path(r"C:\Program Files\Git\usr\bin\ssh.exe").exists() else "ssh"
# perguntas no idioma do público (pt) e no formato dos títulos que viralizam — não "como fazer recap" (só traz tutorial)
PERGUNTAS = [
    "manhwa recap viral ele renasceu sistema",
    "manhwa recap ele despertou poder humilhado",
    "anime recap viral shorts português",
    "curiosidades shorts viral o que acontece",
    "manhwa recap romance ex arrependida",
]


def log(m):
    print(f"[{datetime.now():%H:%M}] {m}", flush=True)


def rodar(pergunta):
    """Roda 1 pergunta no notebook e devolve o markdown (ou '' se falhar)."""
    q = pergunta.replace('"', "")
    cmd = (f"cd {REMOTO} && export PATH=$PWD/.venv/bin:$PATH && timeout 600 python "
           f"skills/last30days/scripts/last30days.py \"{q}\" --search youtube,reddit --emit md --research-only "
           f"2>/dev/null")
    try:
        r = subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOST, cmd], capture_output=True,
                           timeout=700, creationflags=0x08000000)
    except subprocess.TimeoutExpired:
        return ""
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else ""


def resumir(md):
    """Do markdown do last30days: [(titulo, data, canal, views, url, [trechos])] dos vídeos."""
    itens = []
    for bloco in re.split(r"\n### \d+\. ", md)[1:]:
        tit = bloco.split(" (score", 1)[0].strip()
        m = re.search(r"- (\d{4}-\d{2}-\d{2})[^|]*\| ([^|]+) \| \[([\d,]+)views", bloco)
        url = re.search(r"URL: \[(https://www\.youtube\.com/watch\?v=[\w-]+)\]", bloco)
        trechos = re.findall(r'^\s+- "(.+?)"$', bloco, re.M)
        if m:
            itens.append({"titulo": tit, "data": m.group(1), "canal": m.group(2).strip(),
                          "views": int(m.group(3).replace(",", "")), "url": url.group(1) if url else "",
                          "trechos": trechos[:5]})
    return itens


def main():
    if DESLIGA.exists():
        return
    perguntas = [sys.argv[sys.argv.index("--uma") + 1]] if "--uma" in sys.argv else PERGUNTAS
    hoje = datetime.now().strftime("%Y-%m-%d")
    pasta = SAIDA / hoje
    pasta.mkdir(parents=True, exist_ok=True)
    todos = []
    for q in perguntas:
        log(f"pergunta: {q}")
        md = rodar(q)
        if not md:
            log("  sem resposta (notebook fora ou erro)")
            continue
        (pasta / (re.sub(r"[^\w]+", "_", q)[:60] + ".md")).write_text(md, "utf-8")
        its = resumir(md)
        log(f"  {len(its)} vídeos")
        for it in its:
            it["pergunta"] = q
        todos += its
    vistos, unicos = set(), []
    for it in sorted(todos, key=lambda x: -x["views"]):
        if it["url"] and it["url"] in vistos:
            continue
        vistos.add(it["url"])
        unicos.append(it)
    # o last30days traz o mais RELEVANTE (às vezes de 2024/25); os dos últimos 45 dias vêm primeiro, os antigos depois
    from datetime import timedelta
    corte = (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d")
    recentes = [x for x in unicos if x["data"] >= corte] + [x for x in unicos if x["data"] < corte]
    for x in recentes:
        x["recente"] = x["data"] >= corte
    (pasta / "tendencias.json").write_text(json.dumps(recentes, ensure_ascii=False, indent=1), "utf-8")
    linhas = [f"# 🔥 O que está em alta no nosso nicho — {datetime.now():%d/%m %H:%M}", "",
              "Fonte: last30days (YouTube + Reddit, últimos 30 dias), rodado no notebook asusx. Use os TÍTULOS como "
              "modelo de fórmula e os TRECHOS como modelo de gancho de abertura (não copiar texto).", "",
              "| Views | Data | Canal | Título |", "|---:|---|---|---|"]
    for x in recentes[:25]:
        selo = "🆕 " if x.get("recente") else ""
        linhas.append(f"| {x['views']:,} | {selo}{x['data']} | {x['canal'][:25]} | [{x['titulo'][:80]}]({x['url']}) |"
                      .replace(",", "."))
    linhas += ["", "## Ganchos das transcrições (como os vídeos que viralizaram ABREM)", ""]
    for x in recentes[:10]:
        if x["trechos"]:
            linhas.append(f"**{x['titulo'][:70]}** ({x['views']:,} views)".replace(",", "."))
            linhas += [f"- \"{t}\"" for t in x["trechos"][:3]]
            linhas.append("")
    (SAIDA / "TENDENCIAS.md").write_text("\n".join(linhas) + "\n", "utf-8")
    log(f"TENDENCIAS.md: {len(recentes)} vídeos")


if __name__ == "__main__":
    main()
