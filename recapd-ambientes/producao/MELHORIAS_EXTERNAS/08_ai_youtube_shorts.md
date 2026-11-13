# 08 — AI-Youtube-Shorts-Generator (⭐155) → pipeline mais simples que o nosso

Clone: `D:\outros projetos para extrair melhorias\AI-Youtube-Shorts-Generator`
Veredito: ⚪ **BAIXO.** Fábrica faceless end-to-end, mas mais simples que o nosso. 1 ideia pontual
aproveitável no `composer.py`.

## O que faz (modules/)
- `brain.py`: gera roteiro via LLM (Groq/Llama). `audio.py`: TTS. `asset_manager.py`: busca
  stock/avatar. `composer.py`: monta cenas + concatena com xfade.
- Foco em short de tópico com B-roll/avatar — NÃO é recap de manhwa. Sem split de painel,
  sem leitura de balão, sem ensemble. Nosso pipeline é mais avançado nessas frentes.

## A única peça interessante: `modules/composer.py`
- `concatenate_with_transitions` (linha ~143): xfade entre cenas com offset calculado a partir
  da duração acumulada + acrossfade no áudio. É essencialmente o que nosso `_render_xfade_segment`
  já faz. Confirma que nossa abordagem está correta.
- FIXES de Windows úteis de notar (linhas ~199-200): `pix_fmt='yuv420p'` + `movflags='faststart'`
  pra evitar erro 0x80004005 e corrupção de playback. NÓS já usamos faststart+yuv420p
  (ver burn_subtitles em effects_engine), então estamos cobertos. Bom como checklist.
- `process_scene`: crop pra remover logo do avatar — irrelevante (não usamos avatar).

## PLANO
- Nenhuma ação. Serve de validação de que nosso concat/transição está no caminho certo.
- Se algum dia der erro 0x80004005 / playback corrompido no Windows, conferir faststart+yuv420p
  (este repo é a referência do fix).

## O que NÃO copiar
- A arquitetura inteira (mais simples), o uso de avatar, a busca de stock footage.
