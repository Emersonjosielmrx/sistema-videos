"""produto_rotativo: adiciona overlay do produto IA certo para a categoria do video.

CPU-only (ffmpeg drawtext + opcional PNG do produto).

Configuracao em pos_producao/assets/produtos.json:
[
  {
    "id": "hipercube",
    "nome": "HiperCube",
    "tag": "hipercube",
    "url": "https://hipercube.app",
    "cta": "Teste gr\u00e1tis em hipercube.app",
    "tema_alvo": ["tecnologia", "ia", "superacao"],  # casou se tema do canal contiver algum
    "peso": 1,                                        # para sorteio ponderado
    "cor": "#FF6B00",
    "logo_png": "logos/hipercube.png"                 # opcional
  },
  ...
]

Comportamento:
  - Para cada video, escolhe 1 produto cujo tema_alvo bate com o canal/tema
  - Se nenhum bate: usa produto_padrao (configuravel)
  - Rotacao por hash do nome do video (estavel - mesmo video sempre mesmo produto)
"""

import hashlib
import json
import subprocess
from pathlib import Path

SUFFIX = "produto"
_BASE = Path(__file__).resolve().parent.parent.parent
_ASSETS = _BASE / "pos_producao" / "assets"
_LOGOS = _BASE / "pos_producao" / "logos"
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_PRODUTOS = _ASSETS / "produtos.json"

# produto padrao se nenhum casar com o tema
_DEFAULT_PRODUTO = {
    "id": "geral",
    "nome": "Inovare Stories",
    "tag": "inovare",
    "url": "https://inovarestories.com",
    "cta": "Mais conteudo em inovarestories.com",
    "tema_alvo": [],
    "peso": 1,
    "cor": "#FFFFFF",
    "logo_png": None,
}


def _carregar_produtos():
    if not _PRODUTOS.exists():
        return [_DEFAULT_PRODUTO]
    try:
        with open(_PRODUTOS, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    return [_DEFAULT_PRODUTO]


def _escolher_produto(stem: str, produtos: list) -> dict:
    """Escolhe 1 produto. Criterio:
       1) hash do stem % soma_pesos = alvo
       2) se tema bater (via meta['tema']), aumenta peso do candidato
       3) caso nenhum tema bata, retorna o produto com maior peso
    """
    pool = []
    for p in produtos:
        # peso base + bonus se stem contiver tema alvo
        peso = p.get("peso", 1)
        tema = p.get("tema_alvo") or []
        for t in tema:
            if t.lower() in stem.lower():
                peso *= 5
                break
        pool.extend([p] * max(1, peso))
    h = int(hashlib.md5(stem.encode("utf-8")).hexdigest(), 16)
    return pool[h % len(pool)]


def _gerar_card_produto(produto: dict, saida: Path, w=1080, h=1920, duracao=2.0):
    """Gera um mp4 2s com card colorido + texto do produto. CPU-only."""
    cor = produto.get("cor", "#FFFFFF")
    # cor pode ter # - sanitizar pra lavfi
    cor_safe = cor.replace("#", "0x")
    nome = produto.get("nome", "")
    cta = produto.get("cta", "")
    fs_nome = int(h * 0.07)
    fs_cta = int(h * 0.04)
    safe_nome = nome.replace(":", "\\:").replace("'", "\\'")
    safe_cta = cta.replace(":", "\\:").replace("'", "\\'")
    vf = (
        f"color=c={cor_safe}:s={w}x{h}:d={duracao}:r=30,"
        f"drawtext=text='{safe_nome}':fontcolor=white:fontsize={fs_nome}:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-60,"
        f"drawtext=text='{safe_cta}':fontcolor=white:fontsize={fs_cta}:"
        f"x=(w-text_w)/2:y=(h-text_h)/2+80"
    )
    cmd = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", vf,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(saida),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return r.returncode == 0 and saida.exists()


def _concat(lista_mp4, saida: Path) -> bool:
    lista = saida.parent / f"_lista_{saida.stem}.txt"
    linhas = []
    for p in lista_mp4:
        pp = Path(p).resolve()
        linhas.append(f"file '{pp}'")
    lista.write_text("\n".join(linhas), encoding="utf-8")
    cmd = [
        _FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(lista),
        "-c", "copy",
        "-movflags", "+faststart",
        str(saida),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    try:
        lista.unlink()
    except Exception:
        pass
    return r.returncode == 0 and saida.exists()


def processar(input_mp4: str, output_mp4: str, meta: dict) -> bool:
    if not Path(_FFMPEG).exists() or not Path(input_mp4).exists():
        return False
    produtos = _carregar_produtos()
    produto = _escolher_produto(meta.get("stem", ""), produtos)

    tmp_card = Path(output_mp4).with_suffix(".card.mp4")
    if not _gerar_card_produto(produto, tmp_card):
        return False
    return _concat([input_mp4, tmp_card], Path(output_mp4))


# gera produtos.json padrao se nao existir
def _ensure_produtos_json():
    if not _PRODUTOS.exists():
        _PRODUTOS.parent.mkdir(parents=True, exist_ok=True)
        with open(_PRODUTOS, "w", encoding="utf-8") as f:
            json.dump([_DEFAULT_PRODUTO], f, ensure_ascii=False, indent=2)
