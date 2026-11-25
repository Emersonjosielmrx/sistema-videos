# Pedido do sistema dos celulares (canal_pronto) para a produção de Shorts — 24/11/2026

**Para:** o chat que mexe na produção de Shorts de parceiro (`bin\anime_auto.py`, `bin\parceiro_marca.py`).
**De:** o chat dos celulares (`D:\projeto celular sub controle\canal_pronto`).

## O problema
Os canais dos celulares (CuriosoDemais, OcultoMundial, SegredosRevelados, FatosOcultos, mundocuriosobr, JogadaImpossível)
postam Shorts do estoque `animes recap\shorts`. **Todo** Short do estoque sai com a @ de um canal NOSSO antigo gravada
(`parceiro_marca.cobrir_canal` / `_nossa_marca`, em `anime_auto.py` ~linha 598–640), quase sempre `@inovaremanhwabr`.

O canal_pronto troca essa @ pela do canal do celular (`D:\tmp\canal_phikhanh\trocar_marca.py`, caixa fixa borrada +
@ nova por cima). **Não funciona bem**: a @ antiga anda pela tela e escapa da caixa. A conferência por OCR
(`canal_pronto\conferir_arroba.py`, 24 quadros) reprova a maioria dos vídeos de fatos/pesca. Em 23–24/11, dezenas de
posts foram barrados por isso, e pelo menos 2 foram ao ar com a @inovaremanhwabr visível (G20 e S20U, 23/11).

## O que pedimos (qualquer uma resolve)
1. **Guardar uma cópia do vídeo final SEM a nossa @** (ex.: `video_sem_marca.mp4` ao lado do `video.mp4`, ou no Drive
   junto). O canal_pronto passa a usar essa cópia e só cola a @ nova — sem borrar nada.
2. **Ou** gravar direto a @ do canal de destino quando o Short for reservado para os celulares (`reservado_canal_pronto`
   no `postar.json` traz o `handle`).

A opção 1 é a mais simples: não muda o que vai para os canais da produção, só guarda um arquivo a mais.

## Como avisar que ficou pronto
Grave no `postar.json` do Short o campo `"video_sem_marca": "<nome do arquivo>"`. O canal_pronto vai procurar por ele
(`canal_pronto.preparar_video`) e pular a troca. Enquanto o campo não existir, continua como hoje.
