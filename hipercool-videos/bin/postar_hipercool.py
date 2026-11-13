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

# O postador vai no FIM do path e o bin do hipercool no começo. Os dois têm 22 arquivos com o MESMO
# nome (censura_visual, gemini_llm, effects_engine, split-shorts...), e quem está primeiro ganha: com
# o postador na frente, um import feito antes das funções carregava a CÓPIA VELHA e ela ficava em
# sys.modules o resto do processo — foi assim que a censura antiga rodou escondida (dono, 16/10).
sys.path.append(str(POSTADOR_BIN))
sys.path.insert(0, str(BIN))
import politica  # noqa: E402  — só existe no postador, achado pelo fim do path

def _canal_pt():
    try:
        return json.loads((PROJECT / "config" / "fila.json").read_text(encoding="utf-8")).get("canal_pt") or "inovaremanhwabr"
    except (OSError, ValueError):
        return "inovaremanhwabr"


CANAL_PADRAO = _canal_pt()  # canal pt-BR = config/fila.json "canal_pt" (14/10: InovareManhwaVerse)
PROJETO = "hipercool"  # quem posta de verdade; quem pode postar em cada canal vem do cadastro (postador config/canais.json)
TIPO = {"longo": "compilado", "completo": "completo", "resumo": "short"}  # part_NN = short
# Os vídeos são em pt-BR. Os canais inovare de outra língua (hindi/ru/ind/ita/thai...) são do hipercool
# desde 2026-10-13, mas só podem receber vídeo NO IDIOMA deles (o campo "idioma" do rede_canais não é confiável).
CANAIS_PT = {"inovaremanhwabr", "InovareManhwaVerse", CANAL_PADRAO}
TAGS_BASE = ["manhwa", "recap", "webtoon", "romance", "drama", "recap manhwa",
             "manhwa romance", "shorts", "hipercool"]
MAX_CENSURA_SHORT = 0.5  # short com mais da metade do tempo censurado não sobe
# pt, vídeo com cena censurada: mede quantos querem a versão sem censura pelos comentários. SEM link/site:
# link pra conteúdo adulto na descrição/comentário fere a política do YouTube (risco de strike).
CHAMADA_SEM_CENSURA = ('🔥 Algumas cenas foram censuradas pro YouTube. Quer a versão SEM CENSURA? '
                       'Comenta "SEM CENSURA" aqui embaixo que a gente conta quantos querem 👀')
PARAR_EM = {"cota", "limite", "suspenso", "parado", "morto", "reservado", "timeout", "erro", "nao_aprovado", "nudez"}


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
    """Só gênero/busca: hashtag com o nome da obra é risco de direitos autorais (dono, 15/10)."""
    return "#Manhwa #ManhwaRecap #ResumoManhwa #Webtoon #Romance #Drama"


def _sem_obra(pacote, obra):
    """Tira o nome da obra de título/descrição/tags (seo._sem_obra) — vale pro modelo fixo e pro split-shorts."""
    try:
        sys.path.insert(0, str(BIN))
        import seo
        return seo._sem_obra(pacote, {"titulo": obra, "slug": re.sub(r"[^a-z0-9]+", "-", obra.lower()).strip("-")})
    except Exception:  # noqa: BLE001
        return pacote


PLAYLIST_GENERICA = {"recap": {"pt": "Manhwa Recap Narrado em Português", "_": "Manhwa Recap"},
                     "maratona": {"pt": "Maratona Manhwa Completo Narrado", "_": "Manhwa Recap Marathon"}}


def _nome_playlist(obra, tipo, idioma=None):
    """Nome da playlist (tipo "recap" ou "maratona") da obra no canal da língua. NUNCA o nome da obra (dono, 15/10):
    padrão dos títulos, gerado uma vez pelo seo.nome_playlist e GRAVADO em config/fila.json (obras[].playlists[língua])
    — a playlist é achada pelo nome, então ele não pode mudar de um vídeo pro outro."""
    p = PROJECT / "config" / "fila.json"
    slug = re.sub(r"[^a-z0-9]+", "-", obra.lower()).strip("-")
    lang = idioma or "pt"
    c = json.loads(p.read_text(encoding="utf-8"))
    o = next((o for o in c.get("obras", []) if o["slug"] == slug or o["titulo"].lower() == obra.lower()), None)
    if o and ((o.get("playlists") or {}).get(lang) or {}).get(tipo):
        return o["playlists"][lang][tipo]
    nome = None
    try:
        sys.path.insert(0, str(BIN))
        import seo
        nome = seo.nome_playlist(o["slug"] if o else slug, tipo, idioma)
    except Exception as e:  # noqa: BLE001
        log(f"  [!] nome da playlist pelo SEO falhou ({str(e)[:100]})")
    if not nome:
        g = PLAYLIST_GENERICA[tipo]
        return g.get(lang, g["_"])  # genérico não é gravado: na próxima vez tenta o do SEO de novo
    if o:
        c = json.loads(p.read_text(encoding="utf-8"))  # relê: a fila pode ter mexido no arquivo nesse meio tempo
        alvo = next(x for x in c["obras"] if x["slug"] == o["slug"])
        alvo.setdefault("playlists", {}).setdefault(lang, {})[tipo] = nome
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, p)
        log(f"  playlist {tipo} ({lang}) da obra: '{nome}' (gravado em config/fila.json)")
    return nome


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


def _descricao_das_partes(lista, estado, idioma=None):
    """Põe "Parte X de Y" e o link do capítulo completo no topo da descrição de cada Short.

    O agente de SEO devolve UMA descrição e ela era copiada igual nas 10 partes, sem dizer que parte
    é nem apontar pro completo. Com o "vídeo relacionado" do Studio bloqueado pela verificação do
    canal, a descrição é o único caminho do Short pro vídeo completo."""
    import idiomas
    url_completo = ((estado.get("completo") or {}).get("url") or "").strip()
    total = len(lista)

    def rotulo(n):  # "Parte N" na língua do canal (a chave 'parte' já existe em idiomas.TEXTOS)
        try:
            return idiomas.texto(idioma, "parte", x=n)
        except Exception:  # noqa: BLE001
            return f"Parte {n}"

    for i, s in enumerate(lista, 1):
        linhas = [f"▶ {rotulo(i)}/{total}"]
        if url_completo:
            linhas.append(f"🎬 {url_completo}")
        anterior = (estado.get(f"part_{i - 1:02d}") or {}).get("url") if i > 1 else None
        if anterior:
            linhas.append(f"⏮ {rotulo(i - 1)}: {anterior}")
        s["description"] = "\n".join(linhas) + "\n\n" + (s.get("description") or "").strip()


def _titulo_seguro(titulo, idioma=None):
    """Título do roteiro passado pelo dicionário de segurança de anúncios (seo._sanitizar_seo, que só
    rodava dentro de seo.pacote). Devolve None se não sobrar título."""
    if not titulo:
        return None
    try:
        import seo
        novo = (seo._sanitizar_seo({"titulo": titulo, "descricao": "", "tags": []}, idioma) or {}).get("titulo")
    except Exception:  # noqa: BLE001 — sem o seo, melhor o título cru do que nenhum
        return titulo
    if not novo:
        return None
    # O dicionário troca a palavra em minúscula ("ESCRAVA" -> "serva") e o título fica com um buraco
    # no meio da CAIXA ALTA. Onde a palavra trocada estava em maiúsculas, a nova também fica.
    velhas, novas = titulo.split(), novo.split()
    if len(velhas) == len(novas):
        novo = " ".join(n.upper() if v != n and v.isupper() and len(v) > 2 else n
                        for v, n in zip(velhas, novas))
    return novo


def meta_completo(meta, obra, cap, idioma=None, chave_fila=None):
    """(título, descrição, tags, estilo do título) do completo: agente de SEO (seo.py); falhou -> modelo fixo.
    Nunca o nome da obra (dono, 15/10)."""
    import idiomas
    if chave_fila:
        try:
            import seo
            r = seo.pacote(chave_fila, idioma, "completo")
            if r:
                titulo = r["titulo"] if len(r["titulo"]) <= 100 else r["titulo"][:97] + "..."
                return titulo, r["descricao"].strip(), _juntar_tags(r["tags"], TAGS_BASE), r.get("estilo")
        except Exception as e:  # noqa: BLE001
            log(f"  [!] agente de SEO falhou ({str(e)[:100]}); usando o modelo fixo")
    ed = (meta.get("acabamento") or {}).get("editorial") or {}
    capitulo = idiomas.texto(idioma, "capitulo")
    # O modelo fixo entra quando o agente de SEO cai (15/10 à noite: 429 em todas as chaves). O
    # meta.titulo_video vem do roteiro, que é escrito SEM as regras de título: no cap 10 era "ELA
    # ACEITOU SER A ESCRAVA DELE?! - THE INHERITOR CAP 10" — nome da obra e palavra que derruba
    # anúncio. Aqui ele só entra depois de passar pelo dicionário seguro (_sem_obra vem depois).
    titulo = _titulo_seguro(meta.get("titulo_video"), idioma) or f"{ed.get('gancho') or 'O que ele herdou?!'} | {capitulo} {cap}"
    desc = (f"📖 {capitulo} {cap} | {idiomas.texto(idioma, 'recap')}\n\n"
            + (f"🔥 {ed['gancho']}\n\n" if ed.get("gancho") else "")
            + (f"❓ {ed['pergunta']}\n\n" if ed.get("pergunta") else "")
            + f"{hashtags(obra)}\n\n"
            + idiomas.texto(idioma, "assine"))
    tags = list(dict.fromkeys([*meta.get("tags", []), *TAGS_BASE]))[:30]
    r = _sem_obra({"titulo": titulo, "descricao": desc, "tags": tags}, obra)
    titulo = r["titulo"] if len(r["titulo"]) <= 100 else r["titulo"][:97] + "..."
    return titulo, r["descricao"], r["tags"], "fixo"


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
    # Short de RESUMO (pedido do dono, 16/10): subproduto do mesmo vídeo, pra medir se a história
    # condensada rende mais que o trecho "Parte 3 de 5". Por enquanto só GERA o arquivo — a
    # postagem fica pro dono liberar depois de ver. Falhar aqui não pode derrubar os Shorts.
    try:
        import short_resumo
        if not (out_dir / "meta_resumo.json").exists():
            arq = short_resumo.montar(censurado, out_dir, obra, cap)
            if arq:
                m = short_resumo._meta(censurado)
                (out_dir / "meta_resumo.json").write_text(
                    json.dumps({**short_resumo.metadados(m, obra, cap, idioma), "arquivo": arq.name},
                               ensure_ascii=False, indent=2), encoding="utf-8")
                log(f"  Short de resumo gerado (não postado): {arq.name}")
    except Exception as e:  # noqa: BLE001
        log(f"  [!] Short de resumo não saiu: {str(e)[:120]}")

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


def short_resumo_postavel(obra, cap):
    """O Short de resumo que o cortar_shorts gerou (meta_resumo.json), no formato da lista de Shorts, chave "resumo".
    A análise do vídeo pronto olha o próprio arquivo (_revisao_ok: chave fora de part_ = o arquivo)."""
    slug = re.sub(r"[^a-z0-9]+", "-", obra.lower()).strip("-")
    out_dir = PROJECT / "workspace" / "shorts" / f"{slug}-cap{cap}"
    try:
        m = json.loads((out_dir / "meta_resumo.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    mp4 = out_dir / (m.get("arquivo") or "")
    if not m.get("arquivo") or not mp4.exists():
        return []
    pt = m.get("pt") or {}
    r = _sem_obra({"titulo": pt.get("title") or "", "descricao": pt.get("description") or "",
                   "tags": pt.get("tags") or TAGS_BASE}, obra)
    return [{"chave": "<SEGREDO_REMOVIDO>", "file": mp4, "inicio": 0.0, "fim": 0.0, "title": r["titulo"],
             "description": r["descricao"], "tags": r["tags"]}]


def capas_short(lista, obra, cap, idioma=None, ensaio=False):
    """Capa 9:16 de cada Short (bin/capa_ia.capas_short: mesmas poses/falas do capítulo, selo "CAP. N • i/total").
    Põe s["capa"] em cada item; já feitas na pasta dos Shorts são reaproveitadas. Falhou -> Short sobe sem capa."""
    if not lista:
        return
    pasta = Path(lista[0]["file"]).parent
    base = pasta / "capa"
    feitas = [Path(f"{base}_p{i + 1:02d}.jpg") for i in range(len(lista))]
    if not all(p.exists() for p in feitas) and not ensaio:
        try:
            sys.path.insert(0, str(BIN))
            import capa_ia
            import idiomas
            slug = re.sub(r"[^a-z0-9]+", "-", obra.lower()).strip("-")
            selo = idiomas.texto(idioma, "cap", n=cap) if cap else ""
            fonte = {"ru": "Montserrat-ExtraBold.ttf"}.get(idioma) or \
                idiomas.IDIOMAS.get(idioma, {}).get("fonte_png") or "LuckiestGuy-Regular.ttf"
            capa_ia.capas_short(slug, [f"{selo} • {i + 1}/{len(lista)}".strip(" •") for i in range(len(lista))],
                                base, f"cap{cap:02d}", fonte=fonte, idioma=idioma or "pt")
        except Exception as e:  # noqa: BLE001
            log(f"  [!] capas dos Shorts falharam ({str(e)[:120]}); sobem sem capa")
    for s, p in zip(lista, feitas):
        s["capa"] = p if p.exists() else None


def fracao_censurada(ini, fim, janelas):
    coberto = sum(max(0.0, min(fim, b) - max(ini, a)) for a, b in janelas)
    return coberto / max(0.01, fim - ini)


# ─── análise do vídeo pronto (16/10) ─────────────────────────────────────────
def _vertical_aprovado(slug, n, idioma=None):
    """O capítulo vertical de onde o 16:9 tira os painéis já censurados tem veredito ok (da análise ou liberado pelo
    dono)? Então o capNN.mp4 do compilado não precisa de análise própria (dono 19/10)."""
    import fila
    import revisao_video
    e = fila.ler_estado().get(f"{slug}-cap{n:02d}") or {}
    rel = (((e.get("idiomas") or {}).get(idioma) or {}).get("video") if idioma else e.get("video"))
    cens = achar_censurado(fila.video_do_estado(rel)) if rel else None
    if not (bool(cens) and revisao_video.aprovado(cens)[0]):
        return False
    # 23/10: o capNN.mp4 feito ANTES do vertical aprovado (ex.: 16:9 de 15/10, censura antiga) não herda o veredito
    seg = PROJECT / "workspace" / "videos" / "longo" / slug / (idioma or "") / f"cap{n:02d}.mp4"
    return not seg.exists() or seg.stat().st_mtime >= Path(cens).stat().st_mtime


def _revisao_ok(chave, arquivo, censurado, args=None):
    """Nada sobe sem veredito "ok" da análise do vídeo pronto (bin/revisao_video.py) — criada depois que o
    canal pt levou advertência por nudez no compilado caps 1-11 (16/10). Completo: o próprio arquivo. Short: o
    completo censurado de onde ele foi cortado. Longo 16:9: cada capNN.mp4 da compilação cujo capítulo vertical
    ainda não foi aprovado (e a compilação não pode ser mais velha que eles). Sem veredito, analisa agora (alguns
    minutos). (ok, motivo, nudez): nudez = veredito "reprovado" deste mesmo arquivo (achou nudez sem censura) — o
    único motivo que segura a postagem (dono 19/10)."""
    import revisao_video
    arquivo = Path(arquivo)
    if chave == "longo":
        caps = json.loads(arquivo.with_suffix(".json").read_text(encoding="utf-8")).get("caps", [])
        alvos = [arquivo.parent / f"cap{n:02d}.mp4" for n in caps]
        velhos = [a.name for a in alvos if a.exists() and a.stat().st_mtime > arquivo.stat().st_mtime]
        if velhos:
            return False, f"a compilação é mais velha que {', '.join(velhos)} (refeitos): compile de novo", False
        if args is not None and getattr(args, "longo", None):
            alvos = [a for a, n in zip(alvos, caps) if not _vertical_aprovado(args.longo, n, args.idioma)]
    elif str(chave).startswith("part_"):
        alvos = [Path(censurado)]
    else:
        alvos = [arquivo]
    for a in alvos:
        if not a.exists():
            return False, f"{a.name} não existe pra analisar", False
        ok, motivo = revisao_video.aprovado(a)
        if not ok and not motivo.startswith("análise reprovado"):  # reprovado do mesmo arquivo: não reanalisa
            log(f"  {chave}: analisando {a.name} antes de postar ({motivo})...")
            revisao_video.revisar(a)
            ok, motivo = revisao_video.aprovado(a)
        if not ok:
            return False, f"{a.name}: {motivo}", motivo.startswith("análise reprovado")
    return True, "", False


# ─── postagem ────────────────────────────────────────────────────────────────
def postar(canal, chave, arquivo, titulo, desc, tags, estado, censurado, args, thumbnail=None, playlist=None,
           anotar=None):
    """anotar: campos extras gravados no estado se subir (ex. estilo do título, pra medir)."""
    url = ja_postado(canal, arquivo, estado, chave)
    if url:
        log(f"  {chave}: já postado — {url}")
        return "ja"
    if args.ensaio:
        log(f"  [ENSAIO] {chave}: {Path(arquivo).name} | {titulo}")
        return "ensaio"
    if politica.cota_restante(canal, PROJETO) <= 0:
        log(f"  {chave}: limite diário do canal atingido — rode de novo amanhã")
        return "cota"
    ok_rev, motivo, nudez = _revisao_ok(chave, arquivo, censurado, args)
    if nudez:  # dono 19/10: nudez achada segura este vídeo; a fila passa pro próximo (canal não fica vazio)
        log(f"  {chave}: NÃO sobe — a análise do vídeo pronto achou nudez ({motivo}). Se for engano: "
            f"python bin/revisao_video.py --liberar <vídeo>")
        return "nudez"
    if not ok_rev:  # regra do dono (18/10): fora nudez achada, a análise avisa e não segura
        log(f"  {chave}: análise do vídeo pronto: {motivo} — sobe mesmo assim (regra do dono 18/10)")
    politica.marcar_aprovacao(arquivo, "aprovado", "postar_hipercool --aprovado (folha revisada)")
    tags = _caber_tags(tags)
    if not getattr(args, "idioma", None) and (chave == "longo" or (ler_meta(censurado).get("censura") or {}).get("janelas")):
        blocos = desc.split("\n\n", 1)  # 2º parágrafo: aparece antes do "mais" sem tirar a 1ª linha do SEO
        desc = "\n\n".join([blocos[0], CHAMADA_SEM_CENSURA, *blocos[1:]])
    desc = _fim_sem_hashtag(desc, getattr(args, "idioma", None))
    log(f"  {chave}: subindo {Path(arquivo).name}...")
    status, info = politica.postar_youtube(canal["id"], str(arquivo), titulo, desc, tags, privacy="public",
                                           projeto=PROJETO, sintetico=True,
                                           tipo=TIPO.get(chave, "short" if chave.startswith("part_") else chave),
                                           thumbnail=thumbnail, playlist=playlist)
    estado[chave] = {"status": status, "url": info if status == "ok" else None, "info": info,
                     "arquivo": Path(arquivo).name, "em": datetime.now().isoformat(timespec="seconds")}
    if status == "ok":  # acabamento no Studio: roda em rodar_extras (fila, a cada rodada de postagem)
        estado[chave].update(titulo=titulo, canal=canal["id"], capa=str(thumbnail or ""), **(anotar or {}),
                             extras=_extras_de(chave, args, censurado, playlist, thumbnail, estado))
    gravar_estado(censurado, estado)
    log(f"  {chave}: {status} — {info}")
    return status


# ─── acabamento no Studio (D:\postador-de-videos\bin\youtube_studio_extras.py) ──────────────────
EXTRAS_INTERVALO_H = 3  # pendente (canal em verificação, vídeo agendado/processando) tenta de novo depois disso
EXTRAS_MAX_AVISOS = 3   # "aviso" (tela mudou, deu erro) desiste depois de tantas tentativas


def _vid(url):
    m = re.search(r"(?:youtu\.be/|v=|/shorts/|/video/)([\w-]{11})", url or "")
    return m.group(1) if m else None


def _extras_de(chave, args, censurado, playlist, capa, estado):
    """O que fazer no Studio depois que `chave` subiu: tela final (vídeo + playlist) e teste A/B das capas no
    completo/longo; "vídeo relacionado" = o completo nos Shorts; comentário fixado com a chamada SEM CENSURA
    (pt, vídeo com censura — a mesma regra da descrição)."""
    ex, short = {}, chave.startswith("part_")
    # "curtir" pelo próprio canal DESLIGADO em 23/10 (dona: "o like é numa conta só, a minha pessoal, no Acer"):
    # o like agora é o do telão do Acer (D:\video-fila\vitrine.py curtir_no_telao), 1 por vídeo
    if not short and playlist:
        ex["tela_final"] = {"playlist": playlist}
    if not getattr(args, "idioma", None) and (chave == "longo" or (ler_meta(censurado).get("censura") or {}).get("janelas")):
        ex["comentario"] = {"texto": CHAMADA_SEM_CENSURA}
    cj = Path(capa).with_suffix(".json") if capa else None
    if not short and cj and cj.exists():
        arqs = [str(cj.parent / v["arquivo"]) for v in json.loads(cj.read_text(encoding="utf-8")).get("variantes", [])
                if (cj.parent / v["arquivo"]).exists()]
        if len(arqs) >= 2:
            ex["teste_ab"] = {"capas": arqs[:3], "capa_json": str(cj)}
    completo = estado.get("completo") or {}
    if short and _vid(completo.get("url")):
        ex["relacionado"] = {"video": _vid(completo["url"]), "titulo": completo.get("titulo", "")}
    return ex


def _extra_pendente(p, agora):
    st = p.get("status") or ""
    if st in ("ok", "ja") or (st.startswith("aviso") and p.get("tentativas", 0) >= EXTRAS_MAX_AVISOS):
        return False
    if st.startswith("bloqueado"):  # conta do YouTube barrou o recurso: só tenta de novo depois da data que ele deu
        m = re.search(r"até (\d{4}-\d{2}-\d{2})", st)
        return bool(m) and agora.date().isoformat() >= m.group(1)
    em = p.get("em")
    return not em or (agora - datetime.fromisoformat(em)).total_seconds() >= EXTRAS_INTERVALO_H * 3600


def rodar_extras(max_videos=3):
    """Faz/repete o acabamento no Studio de tudo que subiu (todos os canais) e ainda está pendente. Cada vídeo
    abre o Chrome do canal uma vez (todas as ações juntas). Devolve quantos vídeos mexeu."""
    import youtube_studio_extras as yx
    sys.path.insert(0, str(BIN))
    import capa_ia
    agora, feitos = datetime.now(), 0
    for arq in sorted(ESTADO_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            estado = json.loads(arq.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for chave, item in estado.items():
            if feitos >= max_videos:
                return feitos
            ex = item.get("extras") if isinstance(item, dict) else None
            vid = _vid(item.get("url")) if ex else None
            # "curtir" já agendado antes de 23/10 não roda mais (o like é só o da conta pessoal da dona, no Acer)
            fazer = {a: p for a, p in (ex or {}).items() if a != "curtir" and _extra_pendente(p, agora)}
            if not fazer or not vid or not item.get("canal"):
                continue
            kw = {}
            if "tela_final" in fazer:
                kw["tela_final"] = fazer["tela_final"]["playlist"]
            if "relacionado" in fazer:
                kw.update(relacionado=fazer["relacionado"]["video"], titulo_relacionado=fazer["relacionado"]["titulo"])
            if "teste_ab" in fazer:
                kw["ab"] = fazer["teste_ab"]["capas"]
            if "comentario" in fazer:
                kw["comentario"] = fazer["comentario"]["texto"]
            if "curtir" in fazer:
                kw["curtir"] = True
            res = yx.rodar(item["canal"], vid, **kw)
            feitos += 1
            for a, p in fazer.items():
                p["status"] = res.get(a) or "aviso: " + str(res.get("erro") or "sem resposta")[:150]
                p["em"], p["tentativas"] = agora.isoformat(timespec="seconds"), p.get("tentativas", 0) + 1
                if a == "teste_ab" and p["status"] == "ok":
                    capa_ia.registrar_teste(p["capa_json"])
            log(f"  extras {arq.stem[:40]} {chave} ({vid}): " + ", ".join(f"{a}={p['status']}" for a, p in fazer.items()))
            arq.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    return feitos


def postar_longo(args):
    """Compilação 16:9 mais nova da obra (bin/hiper-longo.py) no canal: título/descrição/tags pelo agente de
    SEO (com a lista de capítulos e minutos), capa da compilação, playlist "<obra> — Maratona"."""
    global SLUG_ATUAL
    pasta = PROJECT / "workspace" / "videos" / "longo" / args.longo / (args.idioma or "")
    comps = sorted(pasta.glob(f"{args.longo}_caps*.mp4"), key=lambda p: p.stat().st_mtime)
    if getattr(args, "longo_caps", None):  # 23/10: arquivo certo (16:9 avulso NN-NN ou compilado 1-N), não o mais novo
        a, _, b = args.longo_caps.partition("-")
        comps = [p for p in [pasta / f"{args.longo}_caps{int(a):02d}-{int(b or a):02d}.mp4"] if p.exists()]
    if not comps:
        log(f"ERRO: nenhuma compilação 16:9 em {pasta}")
        log("RESUMO: longo=faltando")
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
    obra_titulo = next((o["titulo"] for _k, o, _n, _p in fila.capitulos() if o["slug"] == args.longo), args.longo)
    r = _sem_obra({"titulo": titulo, "descricao": desc, "tags": tags}, obra_titulo)  # nunca o nome da obra
    titulo, desc, tags = r["titulo"], r["descricao"], r["tags"]
    estado = ler_estado(comp)
    capa = meta.get("capa") if meta.get("capa") and Path(meta["capa"]).exists() else None
    obra_nome = next((o["titulo"] for _k, o, _n, _p in fila.capitulos() if o["slug"] == args.longo), args.longo)
    falas = {k: (meta.get(k) or {}).get("id") for k in ("intro_voz", "intro_meio") if (meta.get(k) or {}).get("id")}
    st = postar(canal, "longo", comp, titulo, desc, tags, estado, comp, args, thumbnail=capa,
                playlist=_nome_playlist(obra_nome, "maratona", args.idioma), anotar=falas or None)
    if st == "ok":
        meta.setdefault("postado", {})[SLUG_ATUAL] = (estado.get("longo") or {}).get("url")
        comp.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        if falas:  # o rodízio só anda quando o compilado sobe (bin/intros_voz.py)
            import intros_voz
            for id_ in falas.values():
                intros_voz.registrar_uso(id_, args.longo, (estado.get("longo") or {}).get("url"))
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
    ap.add_argument("--longo-caps", metavar="A-B", help="com --longo: posta <obra>_capsAA-BB.mp4 (ex.: 5-5 = 16:9 do "
                    "cap 5; 1-5 = compilado) em vez da mais nova")
    ap.add_argument("--max-novos", type=int, help="sobe no máximo N vídeos novos agora (completo primeiro, depois "
                    "os Shorts); se sobrar, o RESUMO traz faltam=... e a próxima rodada continua dali")
    ap.add_argument("--extras", action="store_true", help="só o acabamento no Studio do que já subiu (tela final, "
                    "comentário fixado, teste A/B, vídeo relacionado dos Shorts) — repete os pendentes")
    args = ap.parse_args()
    if args.extras:
        log(f"RESUMO: extras={rodar_extras(max_videos=args.max_novos or 3)} vídeo(s)")
        return
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

    playlist = _nome_playlist(obra, "recap", args.idioma)
    chave_fila = _chave_fila(obra, cap)
    novos = 0
    if not args.no_completo:
        titulo, desc, tags, estilo = meta_completo(meta, obra, cap, args.idioma, chave_fila)
        capa = (meta.get("acabamento") or {}).get("capa")
        capa = capa if capa and Path(capa).exists() else None
        st = postar(canal, "completo", censurado, titulo, desc, tags, estado, censurado, args,
                    thumbnail=capa, playlist=playlist, anotar={"estilo_titulo": estilo})
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
        for s in lista:  # título do split-shorts pode trazer o nome da obra
            r = _sem_obra({"titulo": s["title"] or "", "descricao": s["description"] or "", "tags": s["tags"]}, obra)
            s["title"], s["description"], s["tags"] = r["titulo"], r["descricao"], r["tags"]
        _descricao_das_partes(lista, estado, args.idioma)
        capas_short(lista, obra, cap, args.idioma, args.ensaio)
        if not args.idioma:  # 23/10 (ordem da dona): o Short de RESUMO sobe por último, depois dos cortados (só pt:
            lista += short_resumo_postavel(obra, cap)  # a descrição do short_resumo.metadados é fixa em português)
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
                        estado, censurado, args, thumbnail=s.get("capa"))
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
