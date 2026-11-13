"""propagandas_pre_geradas: usa pool de mp4 curtos ja gerados antes.

Diferenca do propagandas_pool.py (que gera card dinamico por video):
  - aqui voce gera N propagandas fixas UMA vez (pode usar Veo, ou ja tem no disco)
  - salva em pos_producao/propagandas_pool/*.mp4
  - a cada video novo, sorteia 1 do pool e concatena no final

CPU-only. NAO-destrutivo.

Vantagens:
  - Propaganda com audio/imagem de alta qualidade (Veo)
  - Sem gastar API a cada video (so na geracao do pool)
  - Mensagem consistente entre videos

Geracao (exemplo, manual):
  cd D:\veo\beta
  for i in 1 2 3 4 5; do
    python gera_auto.py "propaganda animada do produto Hermes Call com whatsapp {whatsapp}, vertical, 5s" \
      pos_producao/propagandas_pool/hermes_${i}.mp4 --image logo.png
  done
"""

import hashlib
import subprocess
from pathlib import Path

SUFFIX = "adpool"
_BASE = Path(__file__).resolve().parent.parent.parent
_POOL_DIR = _BASE / "pos_producao" / "propagandas_pool"
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"


def _listar_pool() -> list[Path]:
    if not _POOL_DIR.exists():
        return []
    out = []
    for pat in ("*.mp4", "*.mov"):
        out.extend(_POOL_DIR.glob(pat))
    return sorted(out)


def _escolher(stem: str, pool: list[Path]) -> Path | None:
    if not pool:
        return None
    h = int(hashlib.md5(stem.encode("utf-8")).hexdigest(), 16)
    return pool[h % len(pool)]


def _concat(lista_mp4, saida: Path) -> bool:
    lista = saida.parent / f"_lista_{saida.stem}.txt"
    linhas = [f"file '{Path(p).resolve()}'" for p in lista_mp4]
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
    pool = _listar_pool()
    if not pool:
        # pool vazio: pula silenciosamente (nao falha o pipeline)
        # log informativo sera mostrado pelo runner quando pool dir nao existir
        return False
    if not Path(_FFMPEG).exists() or not Path(input_mp4).exists():
        return False
    stem = meta.get("stem", "")
    escolhido = _escolher(stem, pool)
    if not escolhido:
        return False
    ok = _concat([input_mp4, str(escolhido)], Path(output_mp4))
    import sys as _sys
    print(f"      [DEBUG pool] input={input_mp4} prop={escolhido} saida={output_mp4} ok={ok}", file=_sys.stderr, flush=True)
    return ok
