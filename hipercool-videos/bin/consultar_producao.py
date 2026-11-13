#!/usr/bin/env python3
"""Ferramentas de consulta para o vigia/agente responder perguntas do dono.

O agente (Sonnet 4.5 headless) chama este script por CLI para obter dados
que não estão nos logs nem nos arquivos do hipercool.

    python bin/consultar_producao.py views                   # views de todos os canais (2 dias)
    python bin/consultar_producao.py views --dias 7           # views dos últimos 7 dias
    python bin/consultar_producao.py views --canal "Manhwa Noturno"
    python bin/consultar_producao.py ranking                  # top vídeos por views (48h)
    python bin/consultar_producao.py comentarios              # comentários recentes não respondidos
    python bin/consultar_producao.py comentarios --canal "Manhwa Noturno"
    python bin/consultar_producao.py uploads                  # últimos uploads (todos os projetos)
    python bin/consultar_producao.py uploads --n 20
    python bin/consultar_producao.py canais                   # lista de canais com subs e views
    python bin/consultar_producao.py filas                    # estado das filas de postagem
    python bin/consultar_producao.py resumo                   # resumo geral (mesmo do Telegram diário)
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

POST = Path(r"D:\postador-de-videos")
sys.path.insert(0, str(POST / "bin"))


def _n(x):
    return f"{x:,}".replace(",", ".")


def cmd_views(args):
    import youtube_poster as yp
    import stats_views
    canais = yp._load_canais()
    if args.canal:
        c = yp._find_canal(canais, args.canal)
        canais = [c] if c else []
        if not canais:
            print(f"Canal '{args.canal}' não encontrado")
            return
    corte = (datetime.now(stats_views.BRT) - timedelta(days=args.dias)).date()
    for c in canais:
        try:
            tok = yp.refresh_access_token(c)
            pl, _ = stats_views.uploads_playlist(tok)
            if not pl:
                continue
            vids = stats_views.listar_videos(tok, pl, max_itens=50)
            sts = stats_views.stats_videos(tok, vids)
        except Exception as e:
            print(f"[{c['nome']}] erro: {str(e)[:80]}")
            continue
        filt = []
        for s in sts:
            dt = datetime.fromisoformat(s["publicado"].replace("Z", "+00:00")).astimezone(stats_views.BRT).date()
            if dt >= corte:
                s["_data"] = str(dt)
                filt.append(s)
        if not filt:
            continue
        filt.sort(key=lambda x: -x["views"])
        total_views = sum(s["views"] for s in filt)
        print(f"\n[{c['nome']}] {len(filt)} vídeos desde {corte} — total: {_n(total_views)} views")
        for s in filt:
            print(f"  {_n(s['views']):>8} views  {_n(s['likes']):>5} likes  {s.get('_data', '')}  {s['titulo'][:70]}")


def cmd_ranking(args):
    arq = POST / "_analise" / "aprendizado_global.json"
    if not arq.exists():
        print("Arquivo de ranking não encontrado (aprendizado_global.json). Rode notificar_telegram primeiro.")
        return
    d = json.loads(arq.read_text("utf-8"))
    print(f"Ranking de views em 48h — atualizado: {d.get('atualizado', '?')}, janela: {d.get('janela_dias', '?')} dias\n")
    print("TOP 15:")
    for i, v in enumerate(d.get("top", []), 1):
        print(f"  {i:>2}. {_n(v['views']):>8} views  {v.get('canal', '')[:22]:22}  {v['titulo'][:55]}")
    print("\nPor canal (mediana de views em 48h):")
    for canal, r in sorted(d.get("por_canal", {}).items(), key=lambda x: -x[1].get("mediana", 0)):
        print(f"  {canal[:25]:25} mediana={_n(r['mediana']):>7}  n={r['n']:>3}  pct>1k={r.get('pct_1000', 0)}%")
    print("\nPor origem (projeto):")
    for orig, r in sorted(d.get("por_origem", {}).items(), key=lambda x: -x[1].get("mediana", 0)):
        print(f"  {orig[:25]:25} mediana={_n(r['mediana']):>7}  n={r['n']:>3}")


def cmd_comentarios(args):
    import youtube_poster as yp
    canais = yp._load_canais()
    if args.canal:
        c = yp._find_canal(canais, args.canal)
        canais = [c] if c else []
    total = 0
    for c in canais:
        try:
            tok = yp.refresh_access_token(c)
        except Exception:
            continue
        try:
            url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&allThreadsRelatedToChannelId={c.get('yt_id', '')}&maxResults=20&order=time&moderationStatus=published"
            req = __import__("urllib.request", fromlist=["urlopen"]).Request(url, headers={"Authorization": f"Bearer {tok}"})
            with __import__("urllib.request", fromlist=["urlopen"]).urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
        except Exception as e:
            print(f"[{c['nome']}] erro comentários: {str(e)[:80]}")
            continue
        items = data.get("items", [])
        if not items:
            continue
        print(f"\n[{c['nome']}] últimos comentários:")
        for t in items[:args.n]:
            sn = t["snippet"]["topLevelComment"]["snippet"]
            autor = sn.get("authorDisplayName", "?")
            texto = sn.get("textDisplay", "")[:120].replace("\n", " ")
            pub = sn.get("publishedAt", "")[:16]
            replies = t["snippet"].get("totalReplyCount", 0)
            print(f"  {pub}  {autor[:20]:20}  {'✓' if replies else '○'}  {texto}")
            total += 1
    print(f"\n{total} comentários listados")


def cmd_uploads(args):
    import politica
    ups = politica._ler_ledger()
    ups = [r for r in ups if r.get("video_id")][-args.n:]
    print(f"Últimos {len(ups)} uploads (todos os projetos):\n")
    for r in reversed(ups):
        ts = str(r.get("ts", ""))[5:16].replace("T", " ")
        canal = r.get("canal", "")[:25]
        arq = r.get("arquivo", "")[:40]
        vid = r.get("video_id", "")
        print(f"  {ts}  {canal:25}  {arq:40}  https://youtu.be/{vid}")


def cmd_canais(args):
    import youtube_poster as yp
    canais = yp._load_canais()
    print(f"{'Canal':30} {'Subs':>8} {'Status':10}")
    print("-" * 55)
    for c in canais:
        try:
            tok = yp.refresh_access_token(c)
            url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true"
            req = __import__("urllib.request", fromlist=["urlopen"]).Request(url, headers={"Authorization": f"Bearer {tok}"})
            with __import__("urllib.request", fromlist=["urlopen"]).urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            st = data["items"][0]["statistics"]
            print(f"  {c['nome'][:28]:28} {_n(int(st.get('subscriberCount', 0))):>8} {'ok':10}")
        except Exception as e:
            print(f"  {c['nome'][:28]:28} {'?':>8} {str(e)[:30]}")


def cmd_filas(args):
    sys.path.insert(0, str(POST / "bin"))
    import notificar_telegram as nt
    estado = nt.carregar_estado()
    fi = nt.filas_atuais()
    print("Filas de postagem:\n")
    for nome, info in sorted(fi.items()):
        nivel = info.get("nivel", "?")
        n = info.get("n", "?")
        marca = "⚠️" if nivel != "ok" else "✅"
        print(f"  {marca} {nome[:35]:35} n={n:>3}  {nivel}")


def cmd_resumo(args):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import vigia_telegram
    print(vigia_telegram.status())


def main():
    p = argparse.ArgumentParser(description="Consultar dados da produção de vídeos")
    sub = p.add_subparsers(dest="cmd")
    v = sub.add_parser("views", help="views dos vídeos por canal")
    v.add_argument("--dias", type=int, default=2)
    v.add_argument("--canal", default="")
    r = sub.add_parser("ranking", help="top vídeos por views em 48h")
    c = sub.add_parser("comentarios", help="comentários recentes")
    c.add_argument("--canal", default="")
    c.add_argument("--n", type=int, default=10)
    u = sub.add_parser("uploads", help="últimos uploads")
    u.add_argument("--n", type=int, default=10)
    sub.add_parser("canais", help="lista de canais com inscritos")
    sub.add_parser("filas", help="estado das filas de postagem")
    sub.add_parser("resumo", help="resumo geral da produção")
    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return
    {"views": cmd_views, "ranking": cmd_ranking, "comentarios": cmd_comentarios,
     "uploads": cmd_uploads, "canais": cmd_canais, "filas": cmd_filas, "resumo": cmd_resumo}[args.cmd](args)


if __name__ == "__main__":
    main()
