#!/usr/bin/env python3
"""curadoria.py — Funil de curadoria de materiais (trilhas, SFX, overlays, transições).

REGRA DE OURO: os vídeos que o usuário manda são de OUTROS criadores que já usaram o
som/efeito. O que baixamos/cortamos desses vídeos serve SÓ como PISTA para identificar
e depois pesquisar a versão ORIGINAL e LIMPA. O pedaço cortado NUNCA vai pro projeto
final. O destino do material aprovado é só a pasta _aprovados\\ — integração no pipeline
(trilhas/prioritarias, sfx_prioridade) é uma fase futura, sob comando do usuário.

Fluxo:
  baixar <url>            → _pistas\\<slug>\\ (áudio/vídeo + metadata.json)
  cortar <slug> ini fim   → recorte-pista em _pistas\\<slug>\\recortes\\
  frames <slug> ini fim   → frames em _pistas\\<slug>\\frames\\ (inspecionar overlay/transição)
  identificar <slug>      → Gemini opina nome/artista/uso (2ª opinião; você confirma)
  registrar ...           → cria/atualiza entrada no catálogo (status a_aprovar/pista)
  original <id> <url>     → baixa a versão LIMPA pra _a_aprovar\\<tipo>\\
  aprovar <id>            → move _a_aprovar → _aprovados + grava classificação
  classificar <id> ...    → grava melhor_uso/mood/genero/prioridade/notas
  listar [--status][--tipo]  / catalogo  → mostra o estado

Materiais ficam em D:\\hipercool-materiais\\_curadoria\\ (compartilhado entre projetos).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

# Console Windows é cp1252; forçamos UTF-8 pra não quebrar com →/✓/✗ e acentos.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ─── Caminhos ────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent
MATERIAIS = Path(os.environ.get("HIPERCOOL_MATERIAIS", r"D:\hipercool-materiais"))
CURADORIA = MATERIAIS / "_curadoria"
PISTAS = CURADORIA / "_pistas"
A_APROVAR = CURADORIA / "_a_aprovar"
APROVADOS = CURADORIA / "_aprovados"
CATALOGO = CURADORIA / "catalogo.json"

TIPOS = ("trilha", "sfx", "overlay", "transicao")
TIPO_DIR = {"trilha": "trilhas", "sfx": "sfx", "overlay": "overlays", "transicao": "transicoes"}

# Reusa o pool de chaves Gemini do projeto (gemini_llm) — import preguiçoso (só quando precisa)
sys.path.insert(0, str(PROJECT_DIR / "bin"))


# ─── Util ────────────────────────────────────────────────────────────────────
def _venv_python():
    """Python do venv compartilhado (onde yt_dlp está instalado)."""
    cand = Path(r"D:\hipercool-videos\venv\Scripts\python.exe")
    return str(cand) if cand.exists() else sys.executable


def slugify(text, maxlen=60):
    s = re.sub(r"[^\w\s-]", "", (text or "").lower(), flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s[:maxlen] or "sem-titulo"


def ensure_dirs():
    for d in (PISTAS, A_APROVAR, APROVADOS):
        for t in TIPO_DIR.values():
            (A_APROVAR / t).mkdir(parents=True, exist_ok=True)
            (APROVADOS / t).mkdir(parents=True, exist_ok=True)
        PISTAS.mkdir(parents=True, exist_ok=True)


def load_catalogo():
    if CATALOGO.exists():
        try:
            return json.loads(CATALOGO.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ! catalogo.json ilegível ({e}); começando vazio")
    return []


def save_catalogo(items):
    CATALOGO.parent.mkdir(parents=True, exist_ok=True)
    CATALOGO.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def find_item(items, item_id):
    for it in items:
        if it["id"] == item_id or it["id"].startswith(item_id):
            return it
    return None


def new_id():
    return uuid.uuid4().hex[:8]


def run(cmd, **kw):
    """Executa um comando, devolvendo (returncode, stdout, stderr)."""
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", **kw)
    return p.returncode, p.stdout, p.stderr


def ffprobe_duration(path):
    rc, out, _ = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", str(path)])
    try:
        return round(float(out.strip()), 2)
    except Exception:
        return None


# AcoustID: chave de aplicação pública de teste do projeto pyacoustid (uso leve).
# Troque por uma própria (grátis em https://acoustid.org/new-application) se bater limite.
ACOUSTID_KEY = os.environ.get("ACOUSTID_API_KEY", "cSpUJKpD")


def anunciar(texto):
    """Fala um texto curto pela voz edge (Francisca) e toca — só pra ANUNCIAR qual é o
    som antes de processar. NÃO é o TTS de narração do chat (esse fica na outra sessão).
    Silencioso/no-op se CURADORIA_VOZ=0 ou se o edge falhar."""
    if os.environ.get("CURADORIA_VOZ", "1") == "0":
        return
    try:
        import edge_tts_engine
        tmp = CURADORIA / "_voz_tmp.mp3"
        ok = edge_tts_engine.speak(texto, voice="pt-BR-FranciscaNeural", out_wav=str(tmp))
        if ok and tmp.exists():
            # toca sem travar muito; ffplay sai sozinho com -autoexit -nodisp
            run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(tmp)])
    except Exception as e:
        print(f"  (voz indisponível: {e})")


# ─── baixar ──────────────────────────────────────────────────────────────────
def cmd_baixar(args):
    ensure_dirs()
    url = args.url
    # 1) pega metadados primeiro (pro slug e pro catálogo)
    rc, out, err = run([_venv_python(), "-m", "yt_dlp", "-J", "--no-warnings",
                        "--skip-download", url])
    if rc != 0:
        print(f"  ✗ falha ao ler metadados: {err.strip()[:300]}")
        return 1
    try:
        meta = json.loads(out)
    except Exception:
        print("  ✗ metadados não-JSON")
        return 1

    titulo = meta.get("title", "sem-titulo")
    slug = slugify(titulo)
    dest = PISTAS / slug
    dest.mkdir(parents=True, exist_ok=True)

    metadata = {
        "url": url,
        "titulo": titulo,
        "uploader": meta.get("uploader"),
        "duracao": meta.get("duration"),
        "descricao": (meta.get("description") or "")[:4000],
        "tags": meta.get("tags") or [],
        "categorias": meta.get("categories") or [],
        "capitulos": [{"titulo": c.get("title"), "inicio": c.get("start_time"),
                       "fim": c.get("end_time")} for c in (meta.get("chapters") or [])],
        "baixado_em": datetime.now().isoformat(timespec="seconds"),
    }
    (dest / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
    print(f"  ✓ metadata.json → {dest}")

    modo = args.modo
    if modo in ("audio", "ambos"):
        rc, _, err = run([_venv_python(), "-m", "yt_dlp", "-x", "--audio-format", "mp3",
                          "--audio-quality", "0", "--no-warnings",
                          "-o", str(dest / "audio_full.%(ext)s"), url])
        if rc == 0:
            print(f"  ✓ áudio → {dest / 'audio_full.mp3'}")
        else:
            print(f"  ✗ áudio falhou: {err.strip()[:300]}")
    if modo in ("video", "ambos"):
        rc, _, err = run([_venv_python(), "-m", "yt_dlp", "-f",
                          "bv*+ba/b", "--no-warnings",
                          "-o", str(dest / "video_full.%(ext)s"), url])
        if rc == 0:
            print(f"  ✓ vídeo → {dest}\\video_full.*")
        else:
            print(f"  ✗ vídeo falhou: {err.strip()[:300]}")

    # registra a pista no catálogo
    items = load_catalogo()
    iid = new_id()
    items.append({
        "id": iid,
        "tipo": None,
        "status": "pista",
        "slug": slug,
        "origem_url": url,
        "origem_titulo": titulo,
        "recorte": None,
        "identificacao": {},
        "original_url": None,
        "arquivo_limpo": None,
        "classificacao": {},
        "criado_em": datetime.now().isoformat(timespec="seconds"),
    })
    save_catalogo(items)
    print(f"  ✓ pista registrada no catálogo: id={iid} slug={slug}")
    print(f"\n  Próximo: cortar/identificar; depois ache o ORIGINAL limpo e use 'original {iid} <url>'.")
    return 0


# ─── cortar ──────────────────────────────────────────────────────────────────
def _find_slug_dir(slug):
    d = PISTAS / slug
    if d.exists():
        return d
    # busca por prefixo
    for cand in PISTAS.glob(f"{slug}*"):
        if cand.is_dir():
            return cand
    return None


def cmd_cortar(args):
    d = _find_slug_dir(args.slug)
    if not d:
        print(f"  ✗ pista '{args.slug}' não encontrada em {PISTAS}")
        return 1
    src = None
    if args.tipo == "video":
        src = next(iter(d.glob("video_full.*")), None)
    else:
        src = next(iter(d.glob("audio_full.*")), None) or next(iter(d.glob("video_full.*")), None)
    if not src:
        print(f"  ✗ nenhum arquivo full em {d} (rode 'baixar' antes)")
        return 1

    rec_dir = d / "recortes"
    rec_dir.mkdir(exist_ok=True)
    ext = "mp4" if args.tipo == "video" else "mp3"
    nome = f"pista_{args.inicio.replace(':','')}-{args.fim.replace(':','')}.{ext}"
    out = rec_dir / nome

    cmd = ["ffmpeg", "-y", "-ss", args.inicio, "-to", args.fim, "-i", str(src)]
    if args.tipo == "video":
        cmd += ["-c", "copy"]
    else:
        cmd += ["-vn", "-acodec", "libmp3lame", "-q:a", "2"]
    cmd += [str(out)]
    rc, _, err = run(cmd)
    if rc != 0:
        print(f"  ✗ ffmpeg falhou: {err.strip()[-400:]}")
        return 1
    print(f"  ✓ recorte-PISTA → {out}  (dur={ffprobe_duration(out)}s)")
    print("  Lembre: isto é só PISTA pra identificar. NÃO vai pro projeto.")
    return 0


# ─── frames ──────────────────────────────────────────────────────────────────
def cmd_frames(args):
    d = _find_slug_dir(args.slug)
    if not d:
        print(f"  ✗ pista '{args.slug}' não encontrada")
        return 1
    src = next(iter(d.glob("video_full.*")), None)
    if not src:
        print(f"  ✗ sem video_full em {d} (baixe com --video ou --ambos)")
        return 1
    fr_dir = d / "frames"
    fr_dir.mkdir(exist_ok=True)
    cmd = ["ffmpeg", "-y", "-ss", args.inicio, "-to", args.fim, "-i", str(src),
           "-vf", f"fps={args.fps}", str(fr_dir / "frame_%04d.png")]
    rc, _, err = run(cmd)
    if rc != 0:
        print(f"  ✗ ffmpeg falhou: {err.strip()[-400:]}")
        return 1
    n = len(list(fr_dir.glob("frame_*.png")))
    print(f"  ✓ {n} frames → {fr_dir}")
    return 0


# ─── identificar (Gemini = 2ª opinião sobre o TEXTO) ──────────────────────────
def cmd_identificar(args):
    d = _find_slug_dir(args.slug)
    if not d or not (d / "metadata.json").exists():
        print(f"  ✗ metadata.json não encontrado pra '{args.slug}'")
        return 1
    meta = json.loads((d / "metadata.json").read_text(encoding="utf-8"))
    try:
        import gemini_llm
    except Exception as e:
        print(f"  ✗ não consegui importar gemini_llm: {e}")
        return 1

    prompt = (
        "Você é um especialista em trilhas sonoras, efeitos e overlays usados em vídeos de "
        "anime/manhwa recap. Com base nos metadados de um vídeo de OUTRO criador (que usou "
        "esses materiais), sugira o que provavelmente são os sons/músicas/efeitos usados, "
        "para que eu possa procurar a versão ORIGINAL e LIMPA depois.\n\n"
        f"TÍTULO: {meta.get('titulo')}\n"
        f"CANAL: {meta.get('uploader')}\n"
        f"DURAÇÃO: {meta.get('duracao')}s\n"
        f"TAGS: {', '.join(meta.get('tags') or [])[:500]}\n"
        f"CAPÍTULOS: {json.dumps(meta.get('capitulos') or [], ensure_ascii=False)[:800]}\n"
        f"DESCRIÇÃO (trecho): {(meta.get('descricao') or '')[:1500]}\n\n"
        "Responda em JSON com esta forma:\n"
        '{"musicas_provaveis":[{"nome":"","artista":"","onde_achar_original":""}],'
        '"sfx_provaveis":[""],"overlays_ou_transicoes":[""],'
        '"melhor_uso_sugerido":"trilha|emocao|acao|ambiente","mood":"","confianca":"baixa|media|alta",'
        '"observacoes":""}'
    )
    print("  … consultando Gemini (pode rotacionar chaves)…")
    resp = gemini_llm.generate_text(prompt, temperature=0.4, max_tokens=1024)
    if not resp:
        print("  ✗ Gemini não respondeu (sem chave/quota?). Identificação manual então.")
        return 1
    print("\n──── SUGESTÃO DO GEMINI (2ª opinião — você confirma) ────")
    print(resp.strip())
    print("─────────────────────────────────────────────────────────")

    # guarda no metadata da pista pra referência
    meta["identificacao_gemini"] = resp.strip()
    (d / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    print(f"  ✓ salvo em {d / 'metadata.json'} (campo identificacao_gemini)")
    if args.voz:
        # tenta extrair um nome de música da resposta pra anunciar
        m = re.search(r'"nome"\s*:\s*"([^"]+)"', resp)
        nome = m.group(1) if m else "esse material"
        anunciar(f"Pela análise, parece ser {nome}. Confirme se é esse o som antes de eu continuar.")
    return 0


# ─── original (baixa a versão LIMPA pra _a_aprovar) ───────────────────────────
def cmd_original(args):
    ensure_dirs()
    items = load_catalogo()
    it = find_item(items, args.id)
    if not it:
        print(f"  ✗ id '{args.id}' não está no catálogo")
        return 1
    tipo = args.tipo or it.get("tipo")
    if tipo not in TIPOS:
        print(f"  ✗ informe --tipo ({'/'.join(TIPOS)})")
        return 1
    destdir = A_APROVAR / TIPO_DIR[tipo]
    destdir.mkdir(parents=True, exist_ok=True)
    base = slugify(it.get("origem_titulo") or it["slug"])
    out_tmpl = str(destdir / f"{base}_{it['id']}.%(ext)s")

    if tipo in ("overlay", "transicao"):
        fmt = ["-f", "bv*+ba/b"]
    else:
        fmt = ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
    rc, _, err = run([_venv_python(), "-m", "yt_dlp", *fmt, "--no-warnings",
                      "-o", out_tmpl, args.url])
    if rc != 0:
        print(f"  ✗ download do original falhou: {err.strip()[:300]}")
        return 1
    # acha o arquivo gerado
    gerado = next(iter(destdir.glob(f"{base}_{it['id']}.*")), None)
    if not gerado:
        print("  ✗ baixou mas não achei o arquivo gerado")
        return 1
    print(f"  ✓ ORIGINAL limpo → {gerado}  (dur={ffprobe_duration(gerado)}s)")

    if args.normalizar and tipo in ("trilha", "sfx"):
        norm = gerado.with_name(gerado.stem + "_norm.mp3")
        rc, _, err = run(["ffmpeg", "-y", "-i", str(gerado),
                          "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB",
                          "-acodec", "libmp3lame", "-q:a", "2", str(norm)])
        if rc == 0:
            print(f"  ✓ normalizado (original cru guardado) → {norm}")
            it["arquivo_limpo"] = str(norm)
        else:
            print(f"  ! normalização falhou, fica o cru: {err.strip()[-200:]}")
            it["arquivo_limpo"] = str(gerado)
    else:
        it["arquivo_limpo"] = str(gerado)

    it["tipo"] = tipo
    it["original_url"] = args.url
    it["status"] = "a_aprovar"
    save_catalogo(items)
    print(f"  ✓ status → a_aprovar. Ouça/veja e depois: aprovar {it['id']}")
    return 0


# ─── classificar ──────────────────────────────────────────────────────────────
def cmd_classificar(args):
    items = load_catalogo()
    it = find_item(items, args.id)
    if not it:
        print(f"  ✗ id '{args.id}' não encontrado")
        return 1
    c = it.get("classificacao") or {}
    if args.melhor_uso:
        c["melhor_uso"] = args.melhor_uso
    if args.mood:
        c["mood"] = args.mood
    if args.genero:
        c["genero"] = args.genero
    if args.prioridade:
        c["prioridade_sugerida"] = args.prioridade
    if args.notas:
        c["notas"] = args.notas
    it["classificacao"] = c
    if args.tipo:
        it["tipo"] = args.tipo
    save_catalogo(items)
    print(f"  ✓ classificação de {it['id']}: {json.dumps(c, ensure_ascii=False)}")
    return 0


# ─── aprovar ──────────────────────────────────────────────────────────────────
def cmd_aprovar(args):
    ensure_dirs()
    items = load_catalogo()
    it = find_item(items, args.id)
    if not it:
        print(f"  ✗ id '{args.id}' não encontrado")
        return 1
    if not it.get("arquivo_limpo"):
        print("  ✗ esse item não tem arquivo_limpo (rode 'original' primeiro)")
        return 1
    tipo = it.get("tipo")
    if tipo not in TIPOS:
        print(f"  ✗ tipo do item indefinido; use classificar --tipo")
        return 1
    src = Path(it["arquivo_limpo"])
    if not src.exists():
        print(f"  ✗ arquivo_limpo não existe no disco: {src}")
        return 1
    destdir = APROVADOS / TIPO_DIR[tipo]
    destdir.mkdir(parents=True, exist_ok=True)
    dest = destdir / src.name
    src.replace(dest)
    it["status"] = "aprovado"
    it["caminho_aprovado"] = str(dest)
    it["aprovado_em"] = datetime.now().isoformat(timespec="seconds")
    save_catalogo(items)
    print(f"  ✓ APROVADO → {dest}")
    print("  (destino final por enquanto; NÃO integrei no pipeline/prioridades)")
    return 0


# ─── listar / catalogo ────────────────────────────────────────────────────────
def cmd_listar(args):
    items = load_catalogo()
    if args.status:
        items = [i for i in items if i.get("status") == args.status]
    if args.tipo:
        items = [i for i in items if i.get("tipo") == args.tipo]
    if not items:
        print("  (catálogo sem itens com esse filtro)")
        return 0
    for it in items:
        c = it.get("classificacao") or {}
        print(f"  [{it['id']}] {it.get('status'):9} tipo={it.get('tipo') or '?':9} "
              f"uso={c.get('melhor_uso') or '-':8} mood={c.get('mood') or '-':10} "
              f"| {it.get('origem_titulo') or it.get('slug')}")
    print(f"\n  total: {len(items)}")
    return 0


# ─── impressao (fingerprint AcoustID — ajuda a achar o original) ──────────────
def cmd_impressao(args):
    """Gera a impressão digital (fpcalc) de uma pista/recorte e consulta o AcoustID
    pra sugerir título/artista REAIS — ajuda a caçar a versão original limpa."""
    d = _find_slug_dir(args.slug)
    if not d:
        print(f"  ✗ pista '{args.slug}' não encontrada")
        return 1
    # prioriza recorte (trecho isolado da música), senão o áudio full
    alvo = None
    if args.recorte:
        alvo = d / "recortes" / args.recorte
    if not alvo or not alvo.exists():
        alvo = next(iter((d / "recortes").glob("*.mp3")), None) if (d / "recortes").exists() else None
    if not alvo or not alvo.exists():
        alvo = next(iter(d.glob("audio_full.*")), None)
    if not alvo or not alvo.exists():
        print(f"  ✗ sem áudio pra impressão em {d}")
        return 1

    try:
        import acoustid
    except Exception as e:
        print(f"  ✗ pyacoustid indisponível: {e}")
        return 1

    print(f"  … gerando impressão de {alvo.name} e consultando AcoustID…")
    try:
        results = list(acoustid.match(ACOUSTID_KEY, str(alvo)))
    except acoustid.NoBackendError:
        print("  ✗ fpcalc não encontrado no PATH (Chromaprint).")
        return 1
    except acoustid.WebServiceError as e:
        print(f"  ✗ AcoustID web error: {e}")
        return 1
    except Exception as e:
        print(f"  ✗ falha na impressão: {e}")
        return 1

    if not results:
        print("  (nenhuma correspondência no AcoustID — banco cobre música comercial; "
              "trilhas de jogo/anime podem não estar lá. Use 'identificar' (Gemini).)")
        return 0
    print("\n──── CORRESPONDÊNCIAS AcoustID (caçar o original limpo) ────")
    for score, rid, title, artist in results[:5]:
        print(f"  {score*100:5.1f}%  {artist or '?'} — {title or '?'}")
    print("───────────────────────────────────────────────────────────")
    top = results[0]
    if args.voz:
        anunciar(f"A música provável é {top[2] or 'desconhecida'}, de {top[3] or 'artista desconhecido'}. "
                 f"Confirme se é essa antes de eu continuar.")
    return 0


# ─── CLI ──────────────────────────────────────────────────────────────────────
def build_parser():
    p = argparse.ArgumentParser(description="Curadoria de materiais (trilhas/SFX/overlays/transições)")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("baixar", help="baixa um vídeo de criador pra _pistas/")
    b.add_argument("url")
    b.add_argument("--audio", dest="modo", action="store_const", const="audio", default="audio")
    b.add_argument("--video", dest="modo", action="store_const", const="video")
    b.add_argument("--ambos", dest="modo", action="store_const", const="ambos")
    b.set_defaults(func=cmd_baixar)

    c = sub.add_parser("cortar", help="recorta um trecho-PISTA (só pra identificar)")
    c.add_argument("slug")
    c.add_argument("inicio", help="HH:MM:SS ou MM:SS")
    c.add_argument("fim")
    c.add_argument("--tipo", choices=["audio", "video"], default="audio")
    c.set_defaults(func=cmd_cortar)

    f = sub.add_parser("frames", help="extrai frames de um trecho (overlay/transição)")
    f.add_argument("slug")
    f.add_argument("inicio")
    f.add_argument("fim")
    f.add_argument("--fps", default="2")
    f.set_defaults(func=cmd_frames)

    i = sub.add_parser("identificar", help="Gemini opina sobre o material (2ª opinião)")
    i.add_argument("slug")
    i.add_argument("--voz", action="store_true", help="anuncia a sugestão pela voz edge")
    i.set_defaults(func=cmd_identificar)

    fp = sub.add_parser("impressao", help="fingerprint AcoustID (acha título/artista real)")
    fp.add_argument("slug")
    fp.add_argument("--recorte", help="nome do arquivo em recortes/ (senão usa audio_full)")
    fp.add_argument("--voz", action="store_true", help="anuncia o resultado pela voz edge")
    fp.set_defaults(func=cmd_impressao)

    o = sub.add_parser("original", help="baixa a versão LIMPA pra _a_aprovar/")
    o.add_argument("id")
    o.add_argument("url")
    o.add_argument("--tipo", choices=list(TIPOS))
    o.add_argument("--normalizar", action="store_true")
    o.set_defaults(func=cmd_original)

    cl = sub.add_parser("classificar", help="grava classificação no catálogo")
    cl.add_argument("id")
    cl.add_argument("--tipo", choices=list(TIPOS))
    cl.add_argument("--melhor-uso", dest="melhor_uso",
                    choices=["trilha", "emocao", "acao", "ambiente"])
    cl.add_argument("--mood")
    cl.add_argument("--genero")
    cl.add_argument("--prioridade", choices=["baixa", "media", "alta"])
    cl.add_argument("--notas")
    cl.set_defaults(func=cmd_classificar)

    a = sub.add_parser("aprovar", help="move _a_aprovar → _aprovados")
    a.add_argument("id")
    a.set_defaults(func=cmd_aprovar)

    ls = sub.add_parser("listar", help="lista o catálogo")
    ls.add_argument("--status", choices=["pista", "a_aprovar", "aprovado", "descartado"])
    ls.add_argument("--tipo", choices=list(TIPOS))
    ls.set_defaults(func=cmd_listar)

    sub.add_parser("catalogo", help="alias de listar").set_defaults(
        func=cmd_listar, status=None, tipo=None)
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    ensure_dirs()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
