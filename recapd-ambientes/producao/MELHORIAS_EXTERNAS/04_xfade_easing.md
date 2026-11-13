# 04 — xfade-easing (⭐117) → easing nas transições xfade

Clone: `D:\outros projetos para extrair melhorias\xfade-easing`
Veredito: 🟡 **MÉDIO.** Deixa as transições xfade mais suaves/profissionais. NÃO confundir com
as transições elementais (essas são overlays alpha por cima; isto é a curva de progresso do xfade).

## O que nós temos hoje
- `effects_engine._pick_xfade` (linha ~1827): escolhe transição xfade + duração por mood
  (impact/tension/normal), com pools grandes (coverleft, hrwind, dissolve, circleopen...).
- `_render_xfade_segment` (~1887): aplica `xfade=transition=X:duration=d:offset=...` + acrossfade.
- LIMITAÇÃO: o xfade do ffmpeg roda com progresso LINEAR. A transição começa e termina seca,
  sem aceleração/desaceleração. Fica "mecânica".

## O que o xfade-easing oferece
Duas variantes (ver README do clone):
1. **Custom ffmpeg build** com opções `easing=` e `reverse=` no filtro xfade — exige PATCH no
   ffmpeg (recompilar). ❌ NÃO fazer: nosso ffmpeg é o do venv, recompilar é frágil no Windows.
2. **Custom expressions** (`transition=custom:expr='...'`) — funcionam no ffmpeg PADRÃO, sem patch.
   ✅ ESTE é o caminho. O repo tem expressões PRÉ-GERADAS na pasta `expr/` que dá pra copiar
   verbatim e colar no nosso filter_complex. Ex: easing quartic-out + transição radial.

## PLANO DE IMPLEMENTAÇÃO
1. Abrir a pasta `expr/` do clone e pegar 3-4 expressões prontas que combinem com nossos moods
   (ex: easing suave pro "normal/calmo", easing rápido pro "impact").
2. Em `_pick_xfade`/`_render_xfade_segment`, quando a transição escolhida tiver expressão de easing
   disponível, trocar `transition=X` por `transition=custom:expr='<expr colada>'`.
3. Manter fallback: se a expressão falhar no nosso build, cair no `transition=X` linear de hoje.
4. Testar PERFORMANCE: o README avisa que custom expression é mais lento que built-in
   ("clunky"/"performance"). Medir o tempo extra de render num cap; se pesar muito, usar só nos
   cortes-chave (impact), não em todos.

## ⚠️ ARMADILHAS
- NÃO recompilar ffmpeg. Só a variante de expressão.
- Validar que cada `expr` colada roda no NOSSO build (`ffmpeg -h filter=xfade` já é cacheado em
  `_xfade_supported`). Algumas expressões podem usar funções não suportadas.
- Não tocar no áudio: easing é só vídeo; o acrossfade continua igual.

## O que NÃO copiar
- O CLI em shell deles, os patches em C (`patches/`, `src/vf_xfade-diff`).
