#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aprovar.py — revisão humana dos vídeos antes de irem pro YouTube.

Com "exigir_aprovacao_humana": true em config/politica.json, NENHUM postador
sobe um vídeo que não foi aprovado aqui (o youtube_poster.py recusa).

Junta os vídeos pendentes de todas as fontes que os postadores usam:
  - D:\\hipercool-materiais\\**\\postar.json (recap / animes / historias)
  - (16/10: cache vo3, pos_final e agendar_vo3 sairam - caminho antigo do veo desarmado, scripts em bin\\_legado\\)
  - D:\\hipercool-materiais\\manhwa-react\\{shorts,cortes}\\<canal>\\*.postar.json (rede de react)

Uso:
  python bin/aprovar.py                 # revisa um por um (abre o vídeo no player)
  python bin/aprovar.py --listar        # só lista o que está pendente
  python bin/aprovar.py --sem-abrir     # revisa sem abrir o player
  python bin/aprovar.py --aprovar ARQ   # aprova um arquivo direto
  python bin/aprovar.py --rejeitar ARQ  # rejeita (nunca será postado)
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import politica  # noqa: E402

MANHWA_REACT_PRONTOS = [Path(r"D:\hipercool-materiais\manhwa-react\shorts"), Path(r"D:\hipercool-materiais\manhwa-react\cortes")]


def coletar_pendentes():
    """[{arquivo, titulo, origem, texto}] de todas as fontes, sem duplicar arquivo."""
    import postar_tudo_hoje

    # 16/10 (dono; item AB-01 de D:\veo\docs\PLANO_MELHORIAS_VEO.md): o caminho antigo do veo (cache vo3, pos_final COM
    # o slide de WhatsApp, agendar_vo3) saiu - postar_pos_final.py e agendar_vo3.py estao em bin\_legado\. O Veo vai
    # ao ar so limpo, pela rede (manhwareact.py rede --aprovar).
    itens = []
    for cat in ("recap", "animes", "historias"):
        for it in postar_tudo_hoje.coletar_materiais(cat, [], so_aprovados=False):
            itens.append({"arquivo": it["arquivo"], "origem": f"materiais/{cat}",
                          "titulo": it["titulo"], "texto": it["descricao"]})
    for pj in sorted(p for pasta in MANHWA_REACT_PRONTOS for p in pasta.glob("*/*.postar.json")):
        try:
            d = json.loads(pj.read_text(encoding="utf-8"))
        except Exception:
            continue
        mp4 = pj.parent / d.get("arquivo", "")
        if d.get("pronto") is not False and mp4.is_file():
            itens.append({"arquivo": str(mp4), "origem": f"manhwa-react/{pj.parent.name}",
                          "titulo": d.get("titulo", ""), "texto": d.get("descricao", "")})

    vistos, uniq = set(), []
    for it in itens:
        k = str(Path(it["arquivo"]).resolve()).casefold()
        if k not in vistos:
            vistos.add(k)
            uniq.append(it)
    return uniq


def _mb(arq):
    try:
        return Path(arq).stat().st_size / 1e6
    except OSError:
        return 0


def revisar(pendentes, abrir=True):
    print("Para cada vídeo: [a]provar  [r]ejeitar  [p]ular  [s]air\n")
    feitos = {"aprovado": 0, "rejeitado": 0}
    for n, it in enumerate(pendentes, 1):
        print(f"── {n}/{len(pendentes)} ─ {it['origem']} ─ {_mb(it['arquivo']):.0f} MB")
        print(f"   arquivo: {it['arquivo']}")
        print(f"   título:  {it['titulo'][:100]}")
        if it["texto"]:
            print(f"   texto:   {it['texto'][:300].replace(chr(10), ' ')}")
        if abrir:
            try:
                os.startfile(it["arquivo"])  # abre no player padrão do Windows
            except Exception as e:
                print(f"   (não consegui abrir o player: {e})")
        while True:
            r = input("   > ").strip().lower()[:1]
            if r in ("a", "r", "p", "s"):
                break
        if r == "s":
            break
        if r == "p":
            continue
        status = "aprovado" if r == "a" else "rejeitado"
        nota = input("   nota (opcional): ").strip() if status == "rejeitado" else ""
        politica.marcar_aprovacao(it["arquivo"], status, nota)
        feitos[status] += 1
    print(f"\nAprovados: {feitos['aprovado']} | Rejeitados: {feitos['rejeitado']}")


def main():
    ap = argparse.ArgumentParser(description="Revisão humana antes de postar")
    ap.add_argument("--listar", action="store_true", help="só lista os pendentes")
    ap.add_argument("--sem-abrir", action="store_true", help="não abre o player")
    ap.add_argument("--aprovar", nargs="+", metavar="ARQ", help="aprova arquivo(s)")
    ap.add_argument("--rejeitar", nargs="+", metavar="ARQ", help="rejeita arquivo(s)")
    args = ap.parse_args()

    for status, arqs in (("aprovado", args.aprovar), ("rejeitado", args.rejeitar)):
        for arq in arqs or []:
            if not Path(arq).is_file():
                print(f"não existe: {arq}")
                continue
            politica.marcar_aprovacao(arq, status)
            print(f"{status}: {arq}")
    if args.aprovar or args.rejeitar:
        return

    if not politica.politica().get("exigir_aprovacao_humana"):
        print("Aviso: exigir_aprovacao_humana está DESLIGADO em config/politica.json —"
              " os postadores não estão checando aprovação.\n")

    aprov = politica.ler_json(politica.APROV_FILE, {})
    pendentes = [it for it in coletar_pendentes()
                 if politica.status_aprovacao(it["arquivo"], aprov) is None]
    print(f"{len(pendentes)} vídeo(s) aguardando revisão.\n")
    if args.listar:
        for it in pendentes:
            print(f"  [{it['origem']:22}] {_mb(it['arquivo']):6.0f} MB  {it['arquivo']}")
        return
    if pendentes:
        revisar(pendentes, abrir=not args.sem_abrir)


if __name__ == "__main__":
    main()
