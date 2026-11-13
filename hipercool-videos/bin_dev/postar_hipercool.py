#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""postar_hipercool.py — Posta a versão CENSURADA (completo + Shorts) do hipercool no YouTube.

A censurada vem do pipeline (`hiper-pipeline.py --censura`): mosaico só nas partes explícitas
dos painéis +18, legenda nítida por cima. Este script NÃO censura nada: se a censurada do
pipeline novo (meta com "censura") não existir, aborta — nunca posta o vídeo normal.

Sem --aprovado ele só prepara a revisão: gera a folha de quadros (.folha.jpg) e mostra o plano.
Retoma de onde parou: o que já subiu (workspace/postagens/ + ledger do postador) não sobe de novo;
se parar no limite diário do canal, é só rodar o mesmo comando no dia seguinte.

Uso:
  python bin/postar_hipercool.py --video workspace/videos/<..._NORMAL_ULTIMO.mp4>   # revisão
  python bin/postar_hipercool.py --video <...> --aprovado                           # posta
  python bin/postar_hipercool.py --video <...> --aprovado --no-shorts | --no-completo
  python bin/postar_hipercool.py --video <...> --ensaio                             # só mostra
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
BIN = PROJECT / "bin"
POSTADOR_BIN = Path(r"D:\postador-de-videos\bin")
ESTADO_DIR = PROJECT / "workspace" / "postagens"

sys.path.insert(0, str(POSTADOR_BIN))
import politica  # noqa: E402

def _canal_pt():
    try:
        return json.loads((PROJECT / "config" / "fila.json").read_text(encoding="utf-8")).get("canal_pt") or "inovaremanhwabr"
    except (OSError, ValueError):
        return "inovaremanhwabr"


CANAL_PADRAO = _canal_pt()  # canal pt-BR = config/fila.json "canal_pt" (14/10: InovareManhwaVerse)
PROJETO = "manhwa-react"  # dono padrão (rede); canais reservados ao hipercool usam o dono deles
# Os vídeos são em pt-BR. Os canais inovare de outra língua (hindi/ru/ind/ita/thai...) são do hipercool
# desde 2026-10-13, mas só podem receber vídeo NO IDIOMA deles (o campo "idioma" do rede_canais não é confiável).
CANAIS_PT = {"inovaremanhwabr", "InovareManhwaVerse", CANAL_PADRAO}
TAGS_BASE = ["manhwa", "recap", "webtoon", "romance", "drama", "recap manhwa",
             "manhwa romance", "shorts", "hipercool"]
MAX_CENSURA_SHORT = 0.5  # short com mais da metade do tempo censurado não sobe
PARAR_EM = {"cota", "limite", "suspenso", "parado", "morto", "reservado", "timeout", "erro", "nao_aprovado"}


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def achar_video_ultimo():
    cands = sorted((PROJECT / "workspace" / "videos").rglob("*_NORMAL_ULTIMO.mp4"),
                   key=lambda p: p.stat().st_mtime)
    return cands[-1] if cands else None


def achar_censurado(video):
    """Censurada da MESMA renderização (mesmo timestamp no nome)."""
    if "_CENSURADO" in video.stem:
        return video
    base = video.stem.replace("_ULTIMO", "")
    pastas = [video.parent]
    if video.parent.name == "normal":  # workspace/videos/<obra>/capNN/<idioma>/normal|censurado
        pastas.insert(0, video.parent.parent / "censurado")
    for pasta in pastas:
        for nome in (f"{base}_CENSURADO_ULTIMO.mp4", f"{base}_CENSURADO.mp4"):
            if (pasta / nome).exists():
                return pasta / nome
    return None


def ler_meta(video):
    p = video.with_suffix(".meta.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def obra_e_cap(meta, video):
    titulo = meta.get("titulo", "")
    obra = re.split(r"\s+[—–-]\s+", titulo)[0].strip()
    m = re.search(r"cap[ií]tulo\s*(\d+)", titulo, re.I) or \
        re.search(r"cap[- ]?[ií]?tulo[- ]?(\d+)", video.stem, re.I)
    if not obra:
        s = re.search(r"hipercool_(.+?)_\d{8}_\d{4}", video.stem)
        obra = re.split(r"-cap", s.group(1) if s else video.stem)[0].replace("-", " ").title()
    return obra, (int(m.group(1)) if m else 0)


def duracao(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
                       capture_output=True, text=True, timeout=30)
    return float(r.stdout.strip())


def gerar_folha(video, passo=5):
    """Folha de quadros a cada `passo` s pra revisar a censura antes de postar."""
    folha = video.with_suffix(".folha.jpg")
    linhas = math.ceil(duracao(video) / passo / 10)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video),
                    "-vf", f"fps=1/{passo},scale=144:-1,tile=10x{linhas}", "-frames:v", "1", str(folha)],
                   check=True, timeout=600)
    return folha


# ─── estado (o que já subiu) ─────────────────────────────────────────────────
SLUG_ATUAL = None  # canal desta execução (main)


def _arq_estado(censurado, slug=None):
    """Um estado por vídeo E canal (o mesmo capítulo pode subir no canal pt antigo e no novo).
    O inovaremanhwabr fica no nome antigo (sem sufixo) pra não perder o que já foi postado lá."""
    slug = slug or SLUG_ATUAL
    suf = "" if not slug or slug == "inovaremanhwabr" else f"__{re.sub(r'[^0-9A-Za-z_-]+', '', slug)}"
    return ESTADO_DIR / f"{censurado.stem}{suf}.json"


def ler_estado(censurado, slug=None):
    p = _arq_estado(censurado, slug)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def gravar_estado(censurado, estado, slug=None):
    ESTADO_DIR.mkdir(parents=True, exist_ok=True)
    _arq_estado(censurado, slug).write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def ja_postado(canal, arquivo, estado, chave):
    if (estado.get(chave) or {}).get("status") == "ok":
        return (estado[chave].get("url") or "já postado")
    ids = politica.creds_mesmo_canal(canal["id"])
    for r in politica._ler_ledger():
        if r.get("arquivo") == Path(arquivo).name and r.get("canal_id") in ids:
            return f"https://youtu.be/{r.get('video_id')}" if r.get("video_id") else "já postado (ledger)"
    return None


# ─── metadados ───────────────────────────────────────────────────────────────
def hashtags(obra):
    return f"#{re.sub(r'[^0-9A-Za-z]+', '', obra.title())} #Manhwa #Recap #Webtoon #Romance #Drama"


def _chave_fila(obra, cap):
    """Chave do capítulo na fila (ex.: the-inheritor-cap02) — pro agente de SEO achar o roteiro."""
    try:
        sys.path.insert(0, str(BIN))
        import fila
        for k, o, n, _p in fila.capitulos():
            if n == cap and (o["titulo"].lower() == obra.lower() or o["slug"] == re.sub(r"[^a-z0-9]+", "-", obra.lower()).strip("-")):
                return k
    except Exception:  # noqa: BLE001
        pass
    return None


def _juntar_tags(*listas):
    return list(dict.fromkeys(t for l in listas for t in (l or []) if t))[:30]


def _fim_sem_hashtag(desc, idioma=None):
    """Descrição que termina numa #hashtag deixa a lista de sugestões do Studio aberta por cima do título e
    o clique seguinte do poster expira (Short indonésio, 14/10). Termina com a frase de inscrição."""
    d = (desc or "").rstrip()
    if d and d.split()[-1].startswith("#"):
        import idiomas
        d += "\n\n" + idiomas.texto(idioma, "assine")
    return d


def _caber_tags(tags, limite=480):
    """O Studio conta 500 caracteres com aspas em volta de tag com espaço (+2) e vírgula entre elas;
    passou disso a caixa fica vermelha e o upload trava no passo Detalhes."""
    out, total = [], 0
    for t in (str(x).strip().replace(",", " ") for x in tags or []):
        custo = len(t) + (2 if " " in t else 0) + (1 if out else 0)
        if t and total + custo <= limite:
            out.append(t)
            total += custo
    return out


def meta_completo(meta, obra, cap, idioma=None, chave_fila=None):
    """Título/descrição/tags do completo: agente de SEO (seo.py); falhou -> modelo fixo."""
    import idiomas
    if chave_fila:
        try:
            import seo
            r = seo.pacote(chave_fila, idioma, "completo")
            if r:
                titulo = r["titulo"] if len(r["titulo"]) <= 100 else r["titulo"][:97] + "..."
                return titulo, r["descricao"].strip(), _juntar_tags(r["tags"], [obra.lower()], TAGS_BASE)
        except Exception as e:  # noqa: BLE001
            log(f"  [!] agente de SEO falhou ({str(e)[:100]}); usando o modelo fixo")
    ed = (meta.get("acabamento") or {}).get("editorial") or {}
    capitulo = idiomas.texto(idioma, "capitulo")
    titulo = meta.get("titulo_video") or f"{obra} — {capitulo} {cap} | Recap"
    if len(titulo) > 100:
        titulo = titulo[:97] + "..."
    desc = (f"📖 {obra} — {capitulo} {cap} | {idiomas.texto(idioma, 'recap')}\n\n"
            + (f"🔥 {ed['gancho']}\n\n" if ed.get("gancho") else "")
            + (f"❓ {ed['pergunta']}\n\n" if ed.get("pergunta") else "")
            + f"{hashtags(obra)}\n\n"
            + idiomas.texto(idioma, "assine"))
    tags = list(dict.fromkeys([*meta.get("tags", []), obra.lower(), *TAGS_BASE]))[:30]
    return titulo, desc, tags


# ─── shorts ──────────────────────────────────────────────────────────────────
def cortar_shorts(censurado, obra, cap, idioma=None):
    slug = re.sub(r"[^a-z0-9]+", "-", obra.lower()).strip("-")
    out_dir = PROJECT / "workspace" / "shorts" / (f"{slug}-cap{cap}" + (f"-{idioma}" if idioma else ""))
    meta_path = out_dir / "meta_shorts.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    if meta.get("_fonte") != censurado.name:
        log(f"Cortando Shorts de {censurado.name} (leva ~10 min)...")
        env = dict(os.environ, PYTHONUTF8="1",
                   PATH=r"D:\hipercool-materiais\bin" + os.pathsep + os.environ.get("PATH", ""))
        r = subprocess.run([sys.executable, str(BIN / "split-shorts.py"), "--video", str(censurado),
                            "--obra", obra, "--capitulo", str(cap), "--out-dir", str(out_dir),
                            *(["--idioma", idioma] if idioma else [])],
                           env=env, capture_output=True, text=True, timeout=3600,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0 or not meta_path.exists():
            log(f"ERRO split-shorts: {(r.stderr or r.stdout)[-600:]}")
            return []
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        log(f"Shorts já cortados desta versão em {out_dir}")
    shorts = []
    for chave in sorted(k for k in meta if k.startswith("part_")):
        info = meta[chave]
        mp4 = out_dir / info["arquivo"]
        if mp4.exists():
            pt = info.get("pt", {})
            shorts.append({"chave": chave, "file": mp4, "inicio": info["inicio"], "fim": info["fim"],
                           "title": pt.get("title"), "description": pt.get("description", ""),
                           "tags": pt.get("tags", TAGS_BASE)})
    return shorts


def fracao_censurada(ini, fim, janelas):
    coberto = sum(max(0.0, min(fim, b) - max(ini, a)) for a, b in janelas)
    return coberto / max(0.01, fim - ini)


# ─── postagem ────────────────────────────────────────────────────────────────
def postar(canal, chave, arquivo, titulo, desc, tags, estado, censurado, args, thumbnail=None, playlist=None):
    url = ja_postado(canal, arquivo, estado, chave)
    if url:
        log(f"  {chave}: já postado — {url}")
        return "ja"
    if args.ensaio:
        log(f"  [ENSAIO] {chave}: {Path(arquivo).name} | {titulo}")
        return "ensaio"
    if politica.cota_restante(canal) <= 0:
        log(f"  {chave}: limite diário do canal atingido — rode de novo amanhã")
        return "cota"
    politica.marcar_aprovacao(arquivo, "aprovado", "postar_hipercool --aprovado (folha revisada)")
    tags = _caber_tags(tags)
    desc = _fim_sem_hashtag(desc, getattr(args, "idioma", None))
    log(f"  {chave}: subindo {Path(arquivo).name}...")
    status, info = politica.postar_youtube(canal["id"], str(arquivo), titulo, desc, tags, privacy="public",
                                           projeto=politica.reservado_para(canal) or PROJETO, sintetico=True,
                                           thumbnail=thumbnail, playlist=playlist)
    estado[chave] = {"status": status, "url": info if status == "ok" else None, "info": info,
                     "arquivo": Path(arquivo).name, "em": datetime.now().isoformat(timespec="seconds")}
    gravar_estado(censurado, estado)
    log(f"  {chave}: {status} — {info}")
    return status


def postar_longo(args):
    """Compilação 16:9 mais nova da obra (bin/hiper-longo.py) no canal: título/descrição/tags pelo agente de
    SEO (com a lista de capítulos e minutos), capa da compilação, playlist "<obra> — Maratona"."""
    global SLUG_ATUAL
    pasta = PROJECT / "workspace" / "videos" / "longo" / args.longo / (args.idioma or "")
    comps = sorted(pasta.glob(f"{args.longo}_caps*.mp4"), key=lambda p: p.stat().st_mtime)
    if not comps:
        log(f"ERRO: nenhuma compilação 16:9 em {pasta}")
        sys.exit(1)
    comp = comps[-1]
    meta = json.loads(comp.with_suffix(".json").read_text(encoding="utf-8"))
    canal, err = politica.achar_canal(args.canal)
    if not canal:
        log(f"ERRO canal: {err}")
        sys.exit(1)
    SLUG_ATUAL = (politica.rede_do_cred(canal["id"]) or {}).get("slug", canal["nome"])
    if args.idioma:
        cfg_fila = json.loads((PROJECT / "config" / "fila.json").read_text(encoding="utf-8"))
        if canal["id"] not in politica.creds_mesmo_canal((cfg_fila["idiomas"].get(args.idioma) or {}).get("canal", "")):
            log(f"ERRO: '{SLUG_ATUAL}' não é o canal de '{args.idioma}'. Nada foi postado.")
            sys.exit(2)
    elif SLUG_ATUAL not in CANAIS_PT:
        log(f"ERRO: '{SLUG_ATUAL}' é canal de outro idioma e a compilação é em pt-BR. Nada foi postado.")
        sys.exit(2)
    import fila
    chaves = [k for k, o, n, _p in fila.capitulos() if o["slug"] == args.longo and n in meta.get("caps", [])]
    titulo, desc = meta.get("titulo", comp.stem), meta.get("capitulos_descricao", "")
    tags = [args.longo.replace("-", " "), "manhwa recap", "resumo manhwa", *TAGS_BASE]
    try:
        import seo
        r = seo.pacote_longo(chaves, args.idioma, meta.get("capitulos_descricao", ""))
        if r:
            titulo, desc, tags = r["titulo"][:100], r["descricao"].strip(), _juntar_tags(r["tags"], tags)
            if meta.get("capitulos_descricao", "")[:5] not in desc:
                desc += "\n\n" + meta.get("capitulos_descricao", "")
    except Exception as e:  # noqa: BLE001
        log(f"  [!] agente de SEO (longo) falhou ({str(e)[:100]})")
    estado = ler_estado(comp)
    capa = meta.get("capa") if meta.get("capa") and Path(meta["capa"]).exists() else None
    obra_nome = next((o["titulo"] for _k, o, _n, _p in fila.capitulos() if o["slug"] == args.longo), args.longo)
    st = postar(canal, "longo", comp, titulo, desc, tags, estado, comp, args, thumbnail=capa,
                playlist=f"{obra_nome} — Maratona")
    if st == "ok":
        meta.setdefault("postado", {})[SLUG_ATUAL] = (estado.get("longo") or {}).get("url")
        comp.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"RESUMO: longo={st}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--video", help="_NORMAL_ULTIMO.mp4 (ou a própria _CENSURADO); padrão: o mais recente")
    ap.add_argument("--canal", default=CANAL_PADRAO, help=f"canal (padrão: {CANAL_PADRAO})")
    ap.add_argument("--aprovado", action="store_true", help="confirma que a folha foi revisada e posta")
    ap.add_argument("--no-shorts", action="store_true", help="não posta Shorts")
    ap.add_argument("--no-completo", action="store_true", help="não posta o vídeo completo")
    ap.add_argument("--ensaio", action="store_true", help="só mostra o que faria")
    ap.add_argument("--idioma", help="versão em outra língua (hi/id/it/ru/th) — exige o canal daquela língua")
    ap.add_argument("--longo", metavar="OBRA", help="posta a compilação 16:9 mais nova da obra (slug)")
    ap.add_argument("--max-novos", type=int, help="sobe no máximo N vídeos novos agora (completo primeiro, depois "
                    "os Shorts); se sobrar, o RESUMO traz faltam=... e a próxima rodada continua dali")
    args = ap.parse_args()
    if args.longo:
        if not args.aprovado and not args.ensaio:
            log("Compilação 16:9 usa só painéis já censurados pelo vertical; rode com --aprovado para postar.")
            sys.exit(3)
        postar_longo(args)
        return

    video = Path(args.video) if args.video else achar_video_ultimo()
    if not video or not video.exists():
        log(f"ERRO: vídeo não encontrado: {args.video or 'nenhum _NORMAL_ULTIMO.mp4'}")
        sys.exit(1)
    censurado = achar_censurado(video)
    meta = ler_meta(censurado) if censurado else {}
    if not censurado or "censura" not in meta:
        log("ERRO: não há versão censurada do pipeline novo para este vídeo "
            "(arquivo _CENSURADO com meta 'censura'). Renderize de novo com --censura. Nada foi postado.")
        sys.exit(2)
    val = (meta.get("acabamento") or {}).get("validacao") or {}
    if not val.get("ok"):
        log(f"ERRO: a censurada não passou na validação: {val.get('problemas')}. Nada foi postado.")
        sys.exit(2)
    canal, err = politica.achar_canal(args.canal)
    if not canal:
        log(f"ERRO canal: {err}")
        sys.exit(1)
    slug = (politica.rede_do_cred(canal["id"]) or {}).get("slug", canal["nome"])
    global SLUG_ATUAL
    SLUG_ATUAL = slug
    idioma_video = meta.get("idioma", "pt")
    if (args.idioma or "pt") != idioma_video:
        log(f"ERRO: o vídeo é em '{idioma_video}' e foi pedido --idioma {args.idioma or 'pt'}. Nada foi postado.")
        sys.exit(2)
    if args.idioma:
        cfg_fila = json.loads((PROJECT / "config" / "fila.json").read_text(encoding="utf-8"))
        alvo = (cfg_fila["idiomas"].get(args.idioma) or {}).get("canal", "")
        if canal["id"] not in politica.creds_mesmo_canal(alvo):
            log(f"ERRO: '{slug}' não é o canal de '{args.idioma}' (config/fila.json). Nada foi postado.")
            sys.exit(2)
    elif slug not in CANAIS_PT:
        log(f"ERRO: '{slug}' é canal de outro idioma e o vídeo é em pt-BR. Nada foi postado.")
        sys.exit(2)

    obra, cap = obra_e_cap(meta, censurado)
    cens = meta["censura"]
    log(f"Censurada: {censurado.name} | {obra} cap {cap} | {len(cens['paineis'])} painéis censurados "
        f"({', '.join(sorted({p['nivel'] for p in cens['paineis']})) or 'nenhum'}) | detector {cens.get('detector')}")

    if not args.aprovado and not args.ensaio:
        folha = gerar_folha(censurado)
        log(f"REVISÃO: confira a censura em {folha}")
        log("Se estiver certo, rode o mesmo comando com --aprovado para postar.")
        sys.exit(3)

    estado = ler_estado(censurado)
    resultados = []

    playlist = f"{obra} — Recap"
    chave_fila = _chave_fila(obra, cap)
    novos = 0
    if not args.no_completo:
        titulo, desc, tags = meta_completo(meta, obra, cap, args.idioma, chave_fila)
        capa = (meta.get("acabamento") or {}).get("capa")
        capa = capa if capa and Path(capa).exists() else None
        st = postar(canal, "completo", censurado, titulo, desc, tags, estado, censurado, args,
                    thumbnail=capa, playlist=playlist)
        resultados.append(("completo", st))
        novos += st == "ok"
        if st in PARAR_EM:
            args.no_shorts = True
    if not args.no_shorts and args.max_novos is not None and novos >= args.max_novos:
        resultados.append(("faltam", "shorts"))
        args.no_shorts = True

    if not args.no_shorts:
        lista = cortar_shorts(censurado, obra, cap, args.idioma)
        if lista and chave_fila:  # títulos/tags dos Shorts pelo agente de SEO (1 chamada pra todas as partes)
            try:
                import seo
                pk = seo.pacote(chave_fila, args.idioma, "shorts", n=len(lista))
                if pk:
                    for s, t in zip(lista, pk["titulos"]):
                        s["title"], s["description"] = t[:100], pk["descricao"].strip()
                        s["tags"] = _juntar_tags(pk["tags"], ["shorts", obra.lower()], TAGS_BASE)
            except Exception as e:  # noqa: BLE001
                log(f"  [!] agente de SEO (Shorts) falhou ({str(e)[:100]}); títulos do split-shorts")
        for i, s in enumerate(lista):
            frac = fracao_censurada(s["inicio"], s["fim"], cens.get("janelas", []))
            if frac > MAX_CENSURA_SHORT:
                log(f"  {s['chave']}: pulado ({frac:.0%} do trecho é censura)")
                resultados.append((s["chave"], "pulado"))
                continue
            if (args.max_novos is not None and novos >= args.max_novos
                    and not ja_postado(canal, s["file"], estado, s["chave"])):
                resultados.append(("faltam", str(len(lista) - i)))
                break
            st = postar(canal, s["chave"], s["file"], s["title"], s["description"], s["tags"],
                        estado, censurado, args)
            resultados.append((s["chave"], st))
            novos += st == "ok"
            if st in PARAR_EM:
                break
            time.sleep(3)

    log("RESUMO: " + ", ".join(f"{k}={v}" for k, v in resultados))
    if any(v == "cota" for _, v in resultados):
        log("Parou no limite diário. Rode o mesmo comando amanhã — o que já subiu não sobe de novo.")


if __name__ == "__main__":
    main()
