"""anime_idiomas.py — versões do Short de PARCEIRO (@kaijinre) nos canais estrangeiros do hipercool.

Dono (16/10): "poste nos de língua estrangeira existentes". Adaptado de D:\\hipercool-videos\\bin\\idiomas.py (voz de
narrador, fonte e @ de cada canal). Para cada língua, a partir do vídeo ORIGINAL do parceiro:
  - cobre a legenda/marca dele com o @ DAQUELE canal (parceiro_marca, detecção reaproveitada do cache);
  - traduz o roteiro pt (1 chamada) e narra com a voz de narrador do canal;
  - legenda e gancho com fonte que tem o alfabeto — hindi/tailandês pelo libass (o Pillow daqui não tem raqm e
    desmontaria os sinais), vietnamita com Montserrat (a Impact não tem os acentos empilhados);
  - SEO na língua (seo_generator idioma_nome) e capa sem texto onde a fonte da capa não tem o alfabeto;
  - a análise de nudez é HERDADA da versão pt (mesma imagem, só muda o texto por cima).

  gerar(work, original, roteiro_pt, cand, nome_anime) -> {lingua: True/False}
  ANIME_IDIOMAS="hi,id,it,ru,th,vi,en" (padrão); vazio = só pt.
"""
import json
import logging
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

BIN = Path(__file__).resolve().parent
ANIMES_RECAP = Path(r"D:\hipercool-materiais\animes recap")

# voz de narrador = a mesma dos vídeos já publicados em cada canal (hipercool/bin/idiomas.py, "edge" F)
IDIOMAS = {
    "hi": {"nome": "hindi", "voz": "hi-IN-SwaraNeural", "handle": "@inovaremanhwaversehindi",
           "engine": "ass", "fonte_ass": "Nirmala UI"},
    "id": {"nome": "indonésio", "voz": "id-ID-GadisNeural", "handle": "@inovaremanhwaverseind"},
    "it": {"nome": "italiano", "voz": "it-IT-ElsaNeural", "handle": "@inovaremanhwaverseita"},
    "ru": {"nome": "russo", "voz": "ru-RU-SvetlanaNeural", "handle": "@inovaremanhwaru"},
    "th": {"nome": "tailandês", "voz": "th-TH-PremwadeeNeural", "handle": "@inovaremanhwaversethai",
           "engine": "ass", "fonte_ass": "Leelawadee UI"},
    "vi": {"nome": "vietnamita", "voz": "vi-VN-HoaiMyNeural", "handle": "@inovaremanhwaverseviet",
           "fonte_png": r"D:\hipercool-materiais\assets\fonts\Montserrat-ExtraBold.ttf",
           "fonte_ass": "Montserrat ExtraBold"},
    "en": {"nome": "inglês", "voz": "en-US-JennyNeural", "handle": "@inovaremanhwaverseeng"},
    "fr": {"nome": "francês", "voz": "fr-FR-VivienneMultilingualNeural", "handle": "@inovaremanhwafrench"},
}


CFG_PARCEIRO = BIN.parent / "config" / "parceiro.json"   # canais de destino (parceiro_diario)


def _cfg_idiomas():
    try:
        return json.loads(CFG_PARCEIRO.read_text(encoding="utf-8")).get("idiomas", {})
    except (OSError, ValueError):
        return {}


def linguas_ativas():
    """ANIME_IDIOMAS (o parceiro_diario passa só as línguas com fila curta); sem ela, as ativas no
    config/parceiro.json (en/fr: canal pausado no postador)."""
    padrao = [k for k, v in _cfg_idiomas().items() if v.get("ativo", True)] or [k for k in IDIOMAS if k != "en"]
    v = os.environ.get("ANIME_IDIOMAS", ",".join(padrao))
    return [x.strip() for x in v.split(",") if x.strip() in IDIOMAS]


def traduzir(linhas, lang):
    """Mesma quantidade de frases, mesma ordem — ou None."""
    import claude_client
    nome = IDIOMAS[lang]["nome"]
    prompt = (f"Traduza as {len(linhas)} frases abaixo (narração em português do Brasil de um resumo de manhwa) para "
              f"{nome}. Mantenha o tom de narração empolgante e falada, frases curtas, sem nome de obra. UMA tradução "
              f"por frase, mesma ordem e mesma quantidade ({len(linhas)}). Devolva SÓ um JSON: lista de strings.\n\n"
              + json.dumps(linhas, ensure_ascii=False))
    for _ in range(2):
        try:
            txt = claude_client.generate_text(prompt, max_tokens=4000, temperature=0.3, timeout=180) or ""
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[idiomas|{lang}] tradução falhou ({type(e).__name__})")
            continue
        m = re.search(r"\[.*\]", txt, re.S)
        try:
            lst = json.loads(m.group(0)) if m else None
        except ValueError:
            lst = None
        if isinstance(lst, list) and len(lst) == len(linhas) and all(isinstance(x, str) and x.strip() for x in lst):
            return [unicodedata.normalize("NFC", x.strip()) for x in lst]
    return None


def _postar_pt(nome_anime, source_url=""):
    """Reserva (o anime_auto já passa o caminho): postar.json da versão pt deste Short — o mais novo com esse slug
    (ou slug-2, -3...), sem sufixo de língua e, se der, da mesma fonte."""
    import anime_publish
    slug = anime_publish.slugify(nome_anime)
    cands = [p for p in (ANIMES_RECAP / "shorts").glob(f"{slug}*_cap1_*/postar.json")
             if re.match(re.escape(slug) + r"(-\d+)?_cap1_\d{8}$", p.parent.name)]

    def _fonte(p):
        try:
            return json.loads((p.parent / "metadata.json").read_text(encoding="utf-8"))["video"]["source_url"]
        except (OSError, ValueError, KeyError, TypeError):
            return None
    if source_url:
        cands = [p for p in cands if _fonte(p) == source_url] or cands
    return max(cands, key=lambda p: p.stat().st_mtime) if cands else None


def gerar_uma(lang, work, original, linhas_pt, cand, nome_anime, pt_postar):
    import parceiro_marca
    cfg = IDIOMAS[lang]
    d = Path(work) / f"lang_{lang}"   # pasta própria: o anime-pipeline guarda o TTS em <pasta>/audio_cache
    d.mkdir(parents=True, exist_ok=True)
    # 13/11: o narrador é conferido ANTES da tradução e da cobertura (~2 min de PC) — o Short pt sem narrador clonado
    # (formato de teste "transmissao") gastava a cobertura inteira e só depois desistia.
    try:
        narr = json.loads(Path(pt_postar).read_text(encoding="utf-8")).get("narrador") if pt_postar else None
    except (OSError, ValueError):
        narr = None
    narr = narr or os.environ.get("VOZ_CLONADA")
    if not narr and os.environ.get("PERMITIR_EDGE_PURO") != "1":
        logging.error(f"[idiomas|{lang}] sem narrador clonado — versão não sai (Edge pura proibida, dona 28/10)")
        return False
    linhas = traduzir(linhas_pt, lang)
    if not linhas:
        logging.error(f"[idiomas|{lang}] sem tradução — pulando")
        return False
    roteiro = d / "roteiro.txt"
    roteiro.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    src = d / "source.mp4"
    if not parceiro_marca.cobrir(original, src, cfg["handle"]):
        logging.error(f"[idiomas|{lang}] cobertura falhou — pulando")
        return False
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", ANIME_TTS_VOICE=cfg["voz"],
               ANIME_LANG_NOME=cfg["nome"], ANIME_DESCARACT_FLIP="0", ANIME_OUTRA_LINGUA="1")
    # 28/10 (dona: Edge PURO nunca, só como base com clone em cima): a versão na outra língua usa o MESMO narrador
    # clonado do pt por cima da voz Edge da língua (todas femininas, como a Francisca = mesmo tom de base). Sem
    # narrador no pt = não sai.
    if narr:
        env.update(VOZ_CLONADA=narr, VOZ_CLONADA_BASE="francisca", VOZ_CLONADA_VERSAO="2")
    for chave, var in (("fonte_png", "ANIME_SUB_FONT_PNG"), ("fonte_ass", "ANIME_SUB_FONT_ASS")):
        if cfg.get(chave):
            env[var] = cfg[chave]
    if cfg.get("engine"):
        env["ANIME_SUB_ENGINE"] = cfg["engine"]
    try:  # curva de narração: os mesmos impactos da versão pt (mesma ordem de frases)
        imp = json.loads((Path(work) / "_impactos.json").read_text(encoding="utf-8"))["impactos"]
        env["ANIME_IMPACTOS"] = ",".join(str(int(i)) for i in imp)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    r = subprocess.run([sys.executable, str(BIN / "anime-pipeline.py"), "--video-source", str(src),
                        "--script", str(roteiro), "--titulo", cand["title"], "--formato", "short",
                        "--short-source-kind", "native"], env=env)
    vf = d / "final_anime_short.mp4"
    if r.returncode != 0 or not vf.exists():
        logging.error(f"[idiomas|{lang}] pipeline falhou (rc={r.returncode})")
        return False
    pub = [sys.executable, str(BIN / "anime_publish.py"), "--video", str(vf), "--anime", nome_anime, "--cap", "1",
           "--formato", "short", "--source-url", cand.get("url", ""), "--titulo-original", cand.get("title", ""),
           "--roteiro", str(roteiro), "--midia", "manhwa", "--idioma", lang]
    canal = (_cfg_idiomas().get(lang) or {}).get("canal")
    if canal:
        pub += ["--canal", canal]
    if pt_postar:
        pub += ["--revisao-de", str(pt_postar)]
    rp = subprocess.run(pub, env=dict(os.environ, PYTHONUTF8="1"), timeout=1800)
    logging.info(f"[idiomas|{lang}] {'OK' if rp.returncode == 0 else 'publish falhou'}")
    return rp.returncode == 0


def gerar(work, original, roteiro_pt, cand, nome_anime, pt_postar=None):
    linhas_pt = [l.strip() for l in Path(roteiro_pt).read_text(encoding="utf-8").splitlines() if l.strip()]
    if not pt_postar or not Path(pt_postar).is_file():
        pt_postar = _postar_pt(nome_anime, cand.get("url", ""))
    if not pt_postar:
        logging.warning("[idiomas] postar.json da versão pt não achado — as versões ficam sem análise herdada")
    res = {}
    for lang in linguas_ativas():
        try:
            res[lang] = gerar_uma(lang, work, original, linhas_pt, cand, nome_anime, pt_postar)
        except Exception as e:  # noqa: BLE001
            logging.error(f"[idiomas|{lang}] erro: {type(e).__name__}: {e}")
            res[lang] = False
    logging.info(f"[idiomas] {sum(res.values())}/{len(res)} línguas: {res}")
    return res
