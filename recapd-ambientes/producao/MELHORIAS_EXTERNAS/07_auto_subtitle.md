# 07 — auto-subtitle (⭐2.2k) → nada novo pra nós

Clone: `D:\outros projetos para extrair melhorias\auto-subtitle`
Veredito: ⚪ **BAIXO / IGNORAR.** Confirmação por análise, não por suposição.

## O que faz
`auto_subtitle/cli.py`: roda Whisper pra transcrever um vídeo qualquer e queima a legenda
(linha inteira) com ffmpeg. 4 arquivos, simples.

## Por que NÃO serve pra nós
1. É pra vídeo de ORIGEM DESCONHECIDA (não temos o texto). NÓS já temos o texto (narração nossa).
2. Só faz legenda de LINHA INTEIRA — sem word-level/karaokê (o próprio README confirma).
   Nós já fazemos melhor (1-2 palavras, highlight) em `render_subtitles_short`.
3. Transcrever com Whisper o áudio que nós mesmos geramos = reprocessar à toa. O doc 01
   (WordBoundary do edge-tts) dá o timing sem Whisper.

## Ação
Nenhuma. Mantido no índice só pra registrar que foi avaliado e descartado com motivo.
Se um dia precisarmos legendar um vídeo de terceiro (sem texto), aí Whisper entra — não é o caso.
