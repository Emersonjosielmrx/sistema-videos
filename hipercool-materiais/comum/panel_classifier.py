# COMUM — fonte única: D:\hipercool-materiais\comum\panel_classifier.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir panel_classifier.py --de <projeto>
"""panel_classifier.py — classifica o TIPO de painel pra decidir se vale efeito caro (parallax/depth).

Motivação (pedido da usuária): painéis que são só TEXTO/onomatopeia/impacto-sem-personagem
não ganham nada com parallax 2.5D ou movimento — e gerar depth (off, ~20s) ou processar (on)
neles só ATRASA o vídeo à toa. Este módulo dá um sinal BARATO (PIL+numpy, ZERO rede, ZERO depth)
usado nos DOIS lugares:
  - prefetch de depth (off): pular painéis que não valem → não gera depth à toa.
  - pipeline (on): se não vale, cai direto no Ken Burns sem nem tentar parallax.

⚠️ REGRA CRÍTICA (decisão da usuária): este sinal SÓ pode cortar EFEITOS PESADOS / MOVIMENTO
(parallax, depth, e movimento/efeitos caros que não fazem sentido num quadro só de texto).
NUNCA cortar as TRANSIÇÕES NO CORTE — elas continuam entre TODOS os quadros, porque o quadro
SEGUINTE pode ser uma cena boa. Pular transição quebraria a continuidade. Use vale_parallax()
só pra gate de parallax/movimento, jamais pra gate de transição.

Cache por md5. Fallback: se algo falhar, retorna 'cena' (assume que vale — não perde efeito).
"""
import os
import json
import hashlib
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = PROJECT_DIR / "workspace" / "panel_class_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# limiares calibráveis por env (calibragem AGRESSIVA — decisão da usuária 2026-06-30)
FLAT_STD_TH = float(os.environ.get("PANEL_FLAT_STD", "38"))      # std de luminância abaixo disso = fundo plano
DOMINANT_TH = float(os.environ.get("PANEL_DOMINANT", "0.82"))    # 1 tom ocupa >82% = chapado/texto/onomatopeia


def classify(img_path):
    """Retorna 'cena' (vale parallax) | 'texto_plano' (NÃO vale) | 'erro'.
    'texto_plano' = fundo liso, chapado ou só texto: parallax 3D não agrega, só atrasa.
    Sinal: std baixo (pouca variação tonal) OU 1 tom domina (chapado/texto sobre cor)."""
    try:
        b = Path(img_path).read_bytes()
    except Exception:
        return "cena"
    h = hashlib.md5(b).hexdigest()
    cf = CACHE_DIR / f"{h}.json"
    if cf.exists():
        try:
            return json.loads(cf.read_text(encoding="utf-8")).get("tipo", "cena")
        except Exception:
            pass
    try:
        from PIL import Image
        import numpy as np
        im = Image.open(img_path).convert("L").resize((128, 192))
        a = np.asarray(im, dtype="float32")
        std = float(a.std())
        hist = np.bincount(a.astype("uint8").ravel(), minlength=256)
        dominant = float(hist.max() / hist.sum())
        tipo = "texto_plano" if (std < FLAT_STD_TH or dominant > DOMINANT_TH) else "cena"
        info = {"tipo": tipo, "std": round(std, 1), "dominant": round(dominant, 3)}
    except Exception:
        return "cena"
    try:
        cf.write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return tipo


def vale_parallax(img_path):
    """True se o painel vale o custo de parallax/depth. Atalho booleano."""
    return classify(img_path) != "texto_plano"
