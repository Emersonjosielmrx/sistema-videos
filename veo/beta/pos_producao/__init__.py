"""pos_producao: esteira modular de pos-producao dos videos Veo.

NAO-DESTRUTIVO: o mp4 original em videos/ fica intocado. Cada plugin produz
um mp4 ao lado (videos_pos/) ou metadados (videos_pos/_meta/).

Plugins sao modulos Python em pos_producao/plugins/ que expoem a funcao
    processar(input_mp4: str, output_mp4: str, meta: dict) -> bool

Para adicionar uma etapa nova, basta criar um .py nesse diretorio e listar
em pos_producao/config.yaml::pipeline.

Exemplos:
  - plugins.branding_watermark    (CTA + handle fixo)
  - plugins.ffmpeg_loudnorm       (mixar audio + normalizar)
  - plugins.tts_gemini_or_edge    (injeta fala PT-BR como faixa principal)
  - plugins.produto_rotativo      (overlay por categoria do video)

Tudo CPU-only (Intel 620); se um plugin precisar de GPU, levanta erro claro
e o pipeline segue sem ele (modo degradado).
"""

from .runner import run_pipeline, listar_plugins
from .config import CONFIG_PATH, VIDEO_SRC_DIR, VIDEO_OUT_DIR
__all__ = ["run_pipeline", "listar_plugins", "CONFIG_PATH", "VIDEO_SRC_DIR", "VIDEO_OUT_DIR"]
