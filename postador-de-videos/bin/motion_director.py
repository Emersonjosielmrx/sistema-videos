"""motion_director.py — Agente Diretor de Movimento (TAREFA 16).

Decide PREVIAMENTE (adiantado ao render, de preferência no 2º PC) o efeito/params ideal de cada
painel, cacheado por md5 em workspace/motion_direction_cache/. Arquitetura em camadas p/ economia:

  PASSO 0 — PRÉ-FILTRO EM CÓDIGO (barato, ZERO IA): resolve >60% dos painéis sem chamar Haiku/Gemini.
  PASSO 1 — TRIAGEM Haiku (_ask_image_json): só nos painéis "ricos" que sobraram → categoria.
  PASSO 2 — REFINO Gemini: só quando vale → efeito EXATO do catálogo + params.

Fallback total: qualquer falha → decisão do pré-filtro ou None (caller cai no keyword da T15).
Flag MOTION_DIRECTOR=1. panel_effects consome o cache; se há decisão, usa; senão, pick_effect keyword.
NUNCA trava o render esperando IA. Persiste tudo (md5). Não reanalisa painel já decidido.
"""
import os
import json
import hashlib
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "workspace" / "motion_direction_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# duração abaixo disso → efeito fixo simples, não analisa
MIN_DUR_ANALISE = float(os.environ.get("MD_MIN_DUR", "1.2"))


def _md5(img_path):
    try:
        return hashlib.md5(Path(img_path).read_bytes()).hexdigest()
    except Exception:
        return None


def _load(md5):
    if not md5:
        return None
    f = CACHE_DIR / f"{md5}.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _save(md5, decisao):
    if not md5:
        return
    try:
        (CACHE_DIR / f"{md5}.json").write_text(json.dumps(decisao, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


# ─── PASSO 0: pré-filtro 100% código (zero IA) ───────────────────────────────
def pre_filtro(img_path, texto="", dur=None, is_sensual=False, tem_balao=False,
               troca_cena=False, prev_md5=None, this_md5=None):
    """Resolve por regra barata. Retorna decisão dict (com 'fonte':'prefiltro') ou None
    (=painel 'rico', segue pra IA). Decisão dict: {efeito, categoria, motivo, fonte}."""
    # +18 → sem efeito (censura cuida)
    if is_sensual:
        return {"efeito": None, "categoria": "censura", "motivo": "+18 pula efeito", "fonte": "prefiltro"}
    # texto/plano → sem efeito de movimento
    try:
        import panel_classifier as _pcl
        if not _pcl.vale_parallax(img_path):
            return {"efeito": None, "categoria": "texto_plano", "motivo": "so texto/plano", "fonte": "prefiltro"}
    except Exception:
        pass
    # capa/crédito → sem efeito
    try:
        import haiku_helpers as _hh
        # heurística barata primeiro seria ideal; usa cache do classifier já feito acima
    except Exception:
        pass
    # clip curto → efeito fixo simples
    if dur is not None and dur < MIN_DUR_ANALISE:
        return {"efeito": "breathing", "categoria": "zoom", "motivo": "clip curto, kenburns padrao", "fonte": "prefiltro"}
    # painel quase idêntico ao anterior → herda decisão
    if prev_md5 and this_md5 and prev_md5 == this_md5:
        prev = _load(prev_md5)
        if prev:
            return {**prev, "motivo": "herdou do painel anterior (identico)", "fonte": "prefiltro"}
    # troca de cena → transição padrão por regra
    if troca_cena:
        return {"efeito": "mangaslide", "categoria": "transicao", "motivo": "troca de cena", "fonte": "prefiltro"}
    # balão/muito texto → zoom suave padrão (não corta leitura; evita famílias fortes)
    if tem_balao:
        return {"efeito": "dollypush", "categoria": "zoom", "motivo": "tem balao, zoom suave", "fonte": "prefiltro"}
    return None  # painel rico → IA


# ─── PASSO 1+2: IA (Haiku triagem → Gemini refino) ───────────────────────────
def _analisa_ia(img_path, texto=""):
    """Painel rico → Haiku decide categoria; efeito exato via keyword da categoria. Gemini
    fica p/ refino opcional (caro). Retorna decisão dict ou None."""
    try:
        import haiku_helpers as _hh
        img = Path(img_path).read_bytes()
        d = _hh._ask_image_json(
            img,
            "Painel de manhwa. Que MOVIMENTO de câmera combina? Responda JSON: "
            '{"categoria":"zoom|tempo|transicao|atmosfera","close":true|false,"acao":true|false}')
        if not d:
            return None
        cat = d.get("categoria", "zoom")
        # mapa categoria → efeito representativo do panel_effects (roteamento fino via keyword no render)
        rep = {"zoom": "facezoom" if d.get("close") else "dollypush",
               "tempo": "freezeimpact" if d.get("acao") else "slowmoin",
               "transicao": "mangaslide", "atmosfera": "breathing"}
        return {"efeito": rep.get(cat, "dollypush"), "categoria": cat,
                "motivo": f"IA haiku: {d}", "fonte": "haiku"}
    except Exception:
        return None


def decidir_efeito(img_path, texto="", dur=None, is_sensual=False, tem_balao=False,
                   troca_cena=False, prev_md5=None, use_ia=True):
    """Decisão completa por painel, CACHEADA. Retorna dict {efeito, categoria, motivo, fonte}.
    efeito=None significa 'sem efeito' (decisão explícita, também cacheada)."""
    md5 = _md5(img_path)
    cached = _load(md5)
    if cached is not None:
        return cached
    dec = pre_filtro(img_path, texto, dur, is_sensual, tem_balao, troca_cena, prev_md5, md5)
    if dec is None and use_ia and os.environ.get("MOTION_DIRECTOR", "0") == "1":
        dec = _analisa_ia(img_path, texto)
    if dec is None:
        dec = {"efeito": None, "categoria": "nenhum", "motivo": "sem decisao (fallback keyword)", "fonte": "none"}
    _save(md5, dec)
    return dec
