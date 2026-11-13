"""ManhwaReact - RPA de pos-producao para shorts de react.

Uso:
  python manhwareact.py analyze  <video.mp4>
  python manhwareact.py process  <video.mp4> [--no-llm] [--keep-all] [--force] [--dry-run] [--out DIR]
  python manhwareact.py batch    [PASTA]     (padrao: inbox/)  processa todos os mp4 ainda nao processados
  python manhwareact.py watch    [PASTA]     fica vigiando a pasta e processa o que chegar
  python manhwareact.py aprovar  [--tudo]    revisa os videos prontos antes de postar
  python manhwareact.py publicar [--simular|--situacao]  agenda no YouTube os aprovados (via postador-de-videos)
  python manhwareact.py rede     [--simular|--aprovar|--comentarios]  distribui e agenda 1 video/dia em cada canal da rede
  python manhwareact.py camera   <video|pasta> [--so-detectar] [--area X:Y:L:A]  so a webcam da gravacao, em 1920x1080
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
# 22/10 (vigia 5a71ce): a env acima só vale pros FILHOS — o stdout DESTE processo, quando a tarefa agendada
# roda em cp1252, estourava UnicodeEncodeError num print com emoji e o exit saía != 0 com o trabalho feito.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mr.common import load_config, log, save_json, load_json  # noqa: E402

VIDEO_EXT = {".mp4", ".mkv", ".mov", ".webm"}


def cmd_analyze(cfg, args):
    from mr import probe as P
    info = P.probe(cfg, args.video)
    loud = P.measure_loudness(cfg, args.video)
    layout = P.detect_layout(cfg, args.video)
    plan = P.plan_output_layout(cfg, layout)
    print(json.dumps({"info": info, "loudness": loud, "layout": layout, "plan": plan}, indent=1, ensure_ascii=False))


def _apply_overrides(cfg, args):
    if getattr(args, "whisper", None):
        cfg["transcribe"]["model"] = args.whisper
    if getattr(args, "preset", None):
        cfg["output"]["preset"] = args.preset
    if getattr(args, "no_cuts", False):
        cfg["cuts"]["enabled"] = False
    if getattr(args, "music", False):
        cfg["music"]["enabled"] = True


def cmd_process(cfg, args):
    from mr.pipeline import process
    _apply_overrides(cfg, args)
    so = [int(x) for x in args.partes.split(",")] if args.partes else None
    s = process(cfg, args.video, use_llm=(False if args.no_llm else None), keep_all=args.keep_all, force=args.force, dry_run=args.dry_run, out_dir=args.out, only_parts=so, forcar_repetido=args.forcar_repetido)
    print(json.dumps({"status": s.get("status"), "outputs": [o["file"] for o in s["outputs"]]}, indent=1, ensure_ascii=False))


def cmd_canais(cfg, args):
    from mr.channels import generate_kits
    idx = generate_kits(cfg)
    print(json.dumps(idx, indent=1, ensure_ascii=False))


def cmd_memes(cfg, args):
    from mr.memes import build_catalog
    cat = build_catalog(cfg, limit=args.limit, tier=args.tier)
    print(f"{len(cat)} memes no catalogo")


def cmd_ideias(cfg, args):
    """Roda o vigia de formatos sobre videos ja processados (usa transcript/layout/editorial do work/)."""
    from mr import ideias as ID
    from mr.pipeline import slugify
    from pathlib import Path as _P
    src = _P(args.folder)
    n = 0
    for v in sorted(src.glob("*.mp4")):
        w = _P(cfg["paths"]["work"]) / slugify(v.stem)
        if not (w / "transcript.json").exists() or not (w / "layout.json").exists():
            continue
        if (w / "ideia.json").exists() and not args.force:
            continue
        tx = load_json(w / "transcript.json"); layout = load_json(w / "layout.json")
        ed = load_json(w / "editorial.json") if (w / "editorial.json").exists() else None
        segs = tx["segments"]
        if ed and ed.get("speakers"):
            for k, val in ed["speakers"].items():
                if int(k) < len(segs): segs[int(k)]["speaker"] = val
        for s in segs:
            s.setdefault("speaker", "creator")
        idea = ID.analyze_idea(cfg, v, layout, segs, ed)
        if idea:
            save_json(idea, w / "ideia.json"); ID.save_idea(cfg, idea); n += 1
    log(f"ideias: {n} analisado(s)")


def cmd_musica(cfg, args):
    from mr.musicgen import generate_pool
    n = generate_pool(cfg, per_mood=args.por_mood, duration=args.dur, moods=args.moods.split(",") if args.moods else None)
    print(f"{n} faixa(s) gerada(s)")


def cmd_publicar(cfg, args):
    from mr import publish as PB
    if args.situacao:
        PB.situacao(cfg)
        return
    PB.publicar(cfg, dry_run=args.simular, limite=args.limite, so_comentarios=args.so_comentarios)


def cmd_rede(cfg, args):
    from mr import rede as RD
    if args.desligar:
        RD.desligar(cfg)
    elif args.ligar:
        RD.ligar(cfg)
    elif args.aprovar:
        RD.aprovar(cfg, tudo=args.tudo, abrir=not args.sem_abrir)
    elif args.comentarios:
        RD.comentarios(cfg)
    else:
        RD.agendar(cfg, simular=args.simular, dias=args.dias, limite=args.limite,
                   janela_h=(0 if args.sem_janela else args.janela))


def cmd_memoria(cfg, args):
    from mr import memoria as MEM
    mem = MEM.preencher_com_o_que_ja_existe(cfg) if args.preencher else MEM.carregar(cfg)
    for s, e in sorted(mem.items()):
        print(f"{s} | {e.get('status'):9} | {str(e.get('canal')):14} | {str(e.get('assunto'))[:60]}")
    print(f"{len(mem)} gravacao(oes) na memoria")


def cmd_capas(cfg, args):
    from mr.capa import refazer_capas
    refazer_capas(cfg, so=args.so)


def cmd_grande(cfg, args):
    from mr.grande import empacotar
    print(json.dumps(empacotar(cfg, args.video, use_llm=not args.no_llm, force=args.force), indent=1, ensure_ascii=False))
    if not args.sem_cortes:
        from mr.pipeline import process
        process(cfg, args.video, use_llm=(False if args.no_llm else None))


def cmd_temas(cfg, args):
    from mr import temas as TEMAS
    for n, t in enumerate(TEMAS.temas(cfg, args.video, force=args.force), 1):
        print(f"tema {n}: {t['inicio'] / 60:6.1f} - {t['fim'] / 60:6.1f} min | {t.get('tipo', 'react')}: {t['tema']} ({t['canal'] or '?'})")


def cmd_camera(cfg, args):
    from mr.camera import cortar_tudo
    res = cortar_tudo(cfg, args.video, saida_dir=args.saida, area=args.area, so_detectar=args.so_detectar,
                      forcar=args.forcar)
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))
    if any("erro" in r for r in res):
        sys.exit(1)


def cmd_base(cfg, args):
    from mr.base import preparar
    print(json.dumps(preparar(cfg, args.fonte, refazer=args.refazer), indent=1, ensure_ascii=False))


def cmd_aprovar(cfg, args):
    from mr import publish as PB
    PB.aprovar(cfg, tudo=args.tudo, abrir=not args.sem_abrir)


def _state_path(cfg):
    return Path(cfg["paths"]["work"]) / "state.json"


def _pending(cfg, folder):
    st = load_json(_state_path(cfg)) if _state_path(cfg).exists() else {}
    out = []
    for f in sorted(Path(folder).iterdir()):
        if f.suffix.lower() not in VIDEO_EXT or not f.is_file():
            continue
        key = f.name
        rec = st.get(key)
        mtime = int(f.stat().st_mtime)
        if rec and rec.get("mtime") == mtime and rec.get("status") in ("done", "rejected", "ja_feito", "repetido"):
            continue
        # arquivo ainda sendo gravado/copiado? espera estabilizar
        if time.time() - f.stat().st_mtime < 20:
            continue
        out.append(f)
    return out


def _run_batch(cfg, folder, args):
    from mr.pipeline import process
    from mr import memoria as MEM
    st = load_json(_state_path(cfg)) if _state_path(cfg).exists() else {}
    files = _pending(cfg, folder)
    if not files:
        return 0
    mem = MEM.carregar(cfg)
    novos = []
    for f in files:
        feito = None if args.forcar_repetido else MEM.ja_feito(cfg, f, mem)
        if feito:
            log(f"JA FEITO (memoria): {f.name} = {feito.get('arquivo')} [{feito.get('status')}, {feito.get('canal')}] - pulando")
            st[f.name] = {"mtime": int(f.stat().st_mtime), "status": "ja_feito", "igual_a": feito.get("slug"), "when": time.strftime("%Y-%m-%d %H:%M")}
        else:
            novos.append(f)
    save_json(st, _state_path(cfg))
    files = novos[:args.max] if getattr(args, "max", None) else novos
    log(f"batch: {len(files)} video(s) novo(s) nesta rodada em {folder} ({len(novos)} no total)")
    for f in files:
        try:
            from mr import probe as P, grande as GR
            info = P.probe(cfg, f)
            cfg_f = cfg
            if GR.eh_grande(cfg, info):  # react grande (deitado): video inteiro (grandes/) + cortes (cortes/)
                from mr import temas as TEMAS
                partes = [(f, {})] if args.no_llm else TEMAS.dividir(cfg, f)
                if len(partes) > 1:  # varios assuntos: cada tema vira um video completo + cortes
                    outs = []
                    for parte, tema in partes:
                        cfg_t = TEMAS.cfg_do_tema(cfg, tema)  # aula -> canal de aulas fixo
                        GR.empacotar(cfg_t, parte)
                        sp = process(cfg_t, parte, keep_all=args.keep_all, force=args.force, forcar_repetido=args.forcar_repetido)
                        outs += [o["file"] for o in sp["outputs"]]
                    from mr.pipeline import slugify
                    MEM.registrar(cfg, slugify(f.stem), f, info["duration"], "done", saidas=[p.name for p, _ in partes],
                                  assunto=f"dividida em {len(partes)} temas (work/<slug>/temas.json)")
                    st[f.name] = {"mtime": int(f.stat().st_mtime), "status": "done", "temas": [p.name for p, _ in partes],
                                  "outputs": outs, "when": time.strftime("%Y-%m-%d %H:%M")}
                    save_json(st, _state_path(cfg))
                    continue
                cfg_f = TEMAS.cfg_do_tema(cfg, partes[0][1])
                GR.empacotar(cfg_f, f, use_llm=not args.no_llm)
            s = process(cfg_f, f, use_llm=(False if args.no_llm else None), keep_all=args.keep_all, force=args.force, forcar_repetido=args.forcar_repetido)
            st[f.name] = {"mtime": int(f.stat().st_mtime), "status": s.get("status"), "outputs": [o["file"] for o in s["outputs"]], "when": time.strftime("%Y-%m-%d %H:%M")}
        except Exception as e:  # noqa: BLE001
            log(f"ERRO em {f.name}: {e}")
            st[f.name] = {"mtime": int(f.stat().st_mtime), "status": "error", "error": str(e)[:500], "when": time.strftime("%Y-%m-%d %H:%M")}
        save_json(st, _state_path(cfg))
    prontos = [f.name for f in files if st.get(f.name, {}).get("status") == "done"]
    erros = [f.name for f in files if st.get(f.name, {}).get("status") == "error"]
    if prontos or erros:
        from mr import notificar
        partes = sum(len(st[n].get("outputs") or []) for n in prontos)
        notificar.aviso("Lote processado", f"{len(prontos)} video(s) pronto(s), {partes} parte(s)"
                        + (f"; {len(erros)} com ERRO: {', '.join(erros)[:150]}" if erros else ""),
                        nivel="erro" if erros else "ok")
    return len(files)


def cmd_batch(cfg, args):
    try:  # liga/desliga único dos projetos (D:\video-fila\controle.py); sem ele = ligado
        sys.path.insert(0, r"D:\video-fila")
        import controle
        ok, motivo = controle.ligado("manhwa-react", "producao")
    except Exception:  # noqa: BLE001
        ok, motivo = True, ""
    if not ok:
        log(f"batch: {motivo}")
        return
    _apply_overrides(cfg, args)
    folder = args.folder or cfg["paths"]["inbox"]
    n = _run_batch(cfg, folder, args)
    log(f"batch: {n} processado(s)")


def cmd_watch(cfg, args):
    _apply_overrides(cfg, args)
    folder = args.folder or cfg["paths"]["inbox"]
    log(f"watch: vigiando {folder} (Ctrl+C para parar)")
    while True:
        try:
            if _run_batch(cfg, folder, args):
                from mr.limpeza import limpar
                limpar(cfg)
        except KeyboardInterrupt:
            break
        except Exception as e:  # noqa: BLE001
            log(f"watch: erro {e}")
        time.sleep(args.interval)


def main():
    ap = argparse.ArgumentParser(description="ManhwaReact - pos-producao automatica de shorts de react")
    ap.add_argument("--config", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze"); a.add_argument("video")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--no-llm", action="store_true", help="nao usar Claude (gancho/titulo por heuristica)")
    common.add_argument("--keep-all", action="store_true", help="renderiza mesmo se o editorial reprovar")
    common.add_argument("--force", action="store_true", help="ignora cache do work/")
    common.add_argument("--whisper", default=None, help="modelo whisper: tiny|base|small|medium|large-v3-turbo")
    common.add_argument("--preset", default=None, help="preset x264 (ultrafast..veryslow)")
    common.add_argument("--no-cuts", action="store_true")
    common.add_argument("--music", action="store_true", help="liga trilha de fundo")
    common.add_argument("--forcar-repetido", action="store_true", help="processa mesmo se a memoria disser que ja foi feito/repetido")
    p = sub.add_parser("process", parents=[common]); p.add_argument("video"); p.add_argument("--dry-run", action="store_true"); p.add_argument("--out", default=None)
    p.add_argument("--partes", default=None, help="so estas partes (ex.: 6 ou 2,3), sem apagar as outras")
    b = sub.add_parser("batch", parents=[common]); b.add_argument("folder", nargs="?")
    b.add_argument("--max", type=int, default=None, help="no maximo N videos nesta rodada")
    w = sub.add_parser("watch", parents=[common]); w.add_argument("folder", nargs="?"); w.add_argument("--interval", type=int, default=30)
    sub.add_parser("canais", help="gera perfil, banner e descricao de cada canal em canais/")
    ii = sub.add_parser("ideias", help="vigia de formatos: analisa os videos reagidos e alimenta o quadro de ideias")
    ii.add_argument("folder"); ii.add_argument("--force", action="store_true")
    mu = sub.add_parser("musica", help="gera trilhas originais com MusicGen local (sem copyright) em assets/music_generated")
    mu.add_argument("--por-mood", type=int, default=3); mu.add_argument("--dur", type=int, default=30); mu.add_argument("--moods", default=None)
    mm = sub.add_parser("memes", help="descreve os memes do acervo (visao) e monta assets/memes_catalogo.json")
    mm.add_argument("--limit", type=int, default=None); mm.add_argument("--tier", default="haiku")
    pu = sub.add_parser("publicar", help="agenda no YouTube os videos aprovados (shorts/ e cortes/, via postador-de-videos)")
    pu.add_argument("--simular", action="store_true", help="so mostra o que subiria e quando")
    pu.add_argument("--situacao", action="store_true", help="resumo por canal: token, fila, aprovados, postados")
    pu.add_argument("--limite", type=int, default=None, help="maximo de videos nesta rodada")
    pu.add_argument("--so-comentarios", action="store_true", help="so posta os comentarios pendentes")
    rd = sub.add_parser("rede", help="distribui os videos prontos (react + historias) e agenda 1 por dia em cada canal da rede")
    rd.add_argument("--simular", action="store_true", help="mostra o plano (canal, horario, titulo) sem subir")
    rd.add_argument("--dias", type=int, default=1, help="quantos dias a frente preencher (hoje incluso)")
    rd.add_argument("--janela", type=float, default=None, help="so sobe o que publica nas proximas N horas (padrao 3)")
    rd.add_argument("--sem-janela", action="store_true", help="sobe agora tudo que planejou (gera rajada - evite)")
    rd.add_argument("--limite", type=int, default=None, help="maximo de uploads nesta rodada")
    rd.add_argument("--aprovar", action="store_true", help="revisao humana de tudo que a rede pode postar")
    rd.add_argument("--tudo", action="store_true", help="com --aprovar: aprova todos sem abrir")
    rd.add_argument("--sem-abrir", action="store_true")
    rd.add_argument("--comentarios", action="store_true", help="so posta o 1o comentario do canal nos videos que ja abriram")
    rd.add_argument("--desligar", action="store_true", help="botao DESLIGAR: para a postagem automatica (nada sobe nem abre navegador)")
    rd.add_argument("--ligar", action="store_true", help="botao LIGAR: volta a postagem automatica e ja faz as pendentes de hoje")
    me = sub.add_parser("memoria", help="lista os videos ja feitos (memoria para nao repetir)")
    me.add_argument("--preencher", action="store_true", help="registra o que ja foi processado e ainda nao esta na memoria")
    cp = sub.add_parser("capas", help="refaz as capas dos videos prontos no estilo novo (sem re-renderizar)")
    cp.add_argument("--so", nargs="*", default=None, help="so videos cujo nome contem estes textos")
    gr = sub.add_parser("grande", parents=[common], help="react grande deitado: video INTEIRO para postar (grandes/) + cortes (cortes/)")
    gr.add_argument("video"); gr.add_argument("--sem-cortes", action="store_true")
    tm = sub.add_parser("temas", help="mostra como uma gravacao deitada e longa sera dividida por assunto (cada tema = video completo + cortes)")
    tm.add_argument("video"); tm.add_argument("--force", action="store_true")
    cm = sub.add_parser("camera", help="tira so a webcam da gravacao do OBS (sem o video/desenho de baixo) em 1920x1080")
    cm.add_argument("video", help="arquivo ou pasta"); cm.add_argument("--saida", default=None)
    cm.add_argument("--area", default=None, help="X:Y:L:A manual, se a deteccao errar")
    cm.add_argument("--so-detectar", action="store_true", help="so mostra a area achada (gera a previa), sem cortar")
    cm.add_argument("--forcar", action="store_true", help="refaz mesmo se a saida ja existe")
    ba = sub.add_parser("base", help="prepara o video base de um react (link do YouTube ou arquivo): baixa, transcreve a narracao, acha as cenas")
    ba.add_argument("fonte"); ba.add_argument("--refazer", action="store_true")
    av = sub.add_parser("aprovar", help="revisa os videos prontos (abre no player) antes de postar")
    av.add_argument("--tudo", action="store_true", help="aprova todos os pendentes sem abrir")
    av.add_argument("--sem-abrir", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    if args.cmd in ("process", "batch", "watch", "grande", "temas", "base", "rede", "publicar"):
        try:
            from mr.limpeza import limpar
            limpar(cfg)
        except Exception as e:  # noqa: BLE001
            log(f"limpeza: falhou ({e}), seguindo")
    {"analyze": cmd_analyze, "process": cmd_process, "batch": cmd_batch, "watch": cmd_watch, "canais": cmd_canais, "memes": cmd_memes, "ideias": cmd_ideias, "musica": cmd_musica,
     "publicar": cmd_publicar, "aprovar": cmd_aprovar, "base": cmd_base, "grande": cmd_grande, "capas": cmd_capas, "memoria": cmd_memoria,
     "rede": cmd_rede, "camera": cmd_camera, "temas": cmd_temas}[args.cmd](cfg, args)


if __name__ == "__main__":
    main()
