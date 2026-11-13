# 06 — moviepy (⭐14.7k) → referência de efeitos (NÃO adotar como dep)

Clone: `D:\outros projetos para extrair melhorias\moviepy`
Veredito: ⚪ **BAIXO.** Biblioteca madura de edição em Python (numpy). Nós usamos ffmpeg direto
(mais rápido e sem carregar frames na RAM). Adotar moviepy seria REGREDIR em performance.
Serve só como catálogo de ideias de efeito — reimplementar via ffmpeg, não importar.

## Efeitos do moviepy que valem como IDEIA (pasta `moviepy/video/fx/`)
Cada um já tem equivalente em ffmpeg que devemos usar no lugar:
- `Resize` / `Crop` → já fazemos Ken Burns via `zoompan`/`scale`/`crop` no effects_engine.
- `FadeIn`/`FadeOut`/`CrossFadeIn` → temos `fade`/xfade.
- `Scroll` → pan vertical (útil pra painel comprido de manhwa). HOJE: conferir se já cobrimos
  painel alto com pan; se não, ffmpeg `crop` animado faz isso sem moviepy.
- `Painting` (efeito pintura), `GammaCorrection`, `LumContrast` → filtros `eq`/`curves` do ffmpeg.
  ⚠️ Nossa regra fixa #4 PROÍBE colorbalance/curves/rgbashift. Então NÃO usar esses.
- `Freeze` (congela frame) → pode ser útil pra "impacto"; ffmpeg via `tpad`/loop de frame.

## PLANO
- Nenhuma ação direta. Se faltar um efeito específico, consultar a implementação numpy do moviepy
  pra entender a matemática e reproduzir com filtro ffmpeg. Não adicionar moviepy ao requirements.

## O que NÃO fazer
- NÃO `pip install moviepy` no venv do projeto. NÃO trocar nosso pipeline ffmpeg por moviepy.
- Respeitar a regra fixa #4 (sem curves/colorbalance/rgbashift/screen blend).
