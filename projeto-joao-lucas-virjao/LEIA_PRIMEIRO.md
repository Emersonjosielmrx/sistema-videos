# Projeto João Lucas Virjão

Criado em 04/11/2026 a pedido da dona.

## O que é
Faz o mesmo que o **recap**, mas **mantendo a voz da narração original** (narrador parceiro autorizado; o @KkVirjao
autorizou em 15/10, ver hipercool-videos\CLAUDE.md "Canais autorizados"). Não troca a voz nem reescreve roteiro:
só **melhora o vídeo ao máximo**:
- legenda cinética **MIX** no vídeo inteiro (cada palavra com desenho/efeito diferente)
- efeitos visuais nas palavras fortes (fx_visual: zoom, tremor, flash) + cor/nitidez
- **memes**: interrupção em tela cheia com som (~1/min) + meme de imagem rápido com som de impacto
- **trilha** por clima com ducking sob a voz original
- borrão só se a fonte tem legenda queimada (detecção automática)
- 1080p60

## Como funciona (feito 04/11)
1. `bin\enviar_kaggle.py <source.mp4> "<titulo>" <id_youtube> [urgente]` manda o pedido para a central da
   hermes-prod (o PC NÃO fala com o Kaggle; cada conta sai pela saída dela). `urgente` = pid `20261027_0001xx`,
   pego antes dos outros.
2. Na GPU do Kaggle o pedido traz `longo_override {"voz_original": true}` e o `anime-pipeline.py` desvia para
   `D:\recapd-ambientes\producao\bin\voz_original.py`, que faz: Whisper large-v3 na GPU com o tempo de cada palavra,
   depois memes, depois a base (trechos + memes, juntados com o concat demuxer), depois `fx_subtitles.burn_subtitles_ass`
   (legenda MIX + efeitos + 1080p60), depois `add_dynamic_music` (trilha), e no fim `final_anime_deitado.mp4`.
3. `bin\recolher_e_postar.py <pid> <id> "<titulo>"` (oculto, pythonw) espera o pronto, põe a ficha no Drive
   (`animes recap\na_nuvem`), guarda uma cópia em `prontos\` e chama o `postar_quando_pronto.py` (postagem
   **agendada**, com ele na frente, respeitando o limite de cada canal). Log: `recolher.log`.
4. Código novo vai para o Kaggle com `colab\montar_pacote.py --codigo` (o trabalhador baixa a cada pedido).

## Pasta pública do parceiro (04/11)
Drive `manhwa-drive:joao-lucas-virjao` — https://drive.google.com/open?id=10cenaur7rDEuwSThSzDo20vP0M0-u5HF
(qualquer pessoa com o link = EDITOR, dado por `bin\liberar_edicao_pasta.py`).
Entradas (vigia_drive.ENTRADAS -> longo_override):
- `1_VIDEO CRU...` → cru=True (voz_original.tirar_pausas: silêncio > 0,6 s sai) + edição + até 8 cortes
- `2_VIDEO JA EDITADO - so melhorar...` → edição, sem cortes
- `3_VIDEO JA EDITADO - melhorar + cortes...` → edição + cortes
- `4_SO CORTES...` → so_cortes (pula a legenda do longo; o completo não volta)
Saídas: `5_SAIDA - VIDEOS COMPLETOS` (`<nome> - EDITADO.mp4`) e `6_SAIDA - SHORTS` (`<nome>/corte_NN.mp4` +
`LEIA - titulos sugeridos.txt`).
- `7_SEUS MEMES com prioridade...` / `8_SUAS TRILHAS com prioridade...` → o Kaggle baixa a cada vídeo; memes dele
  entram primeiro (vídeo até 12 s com som ou imagem); trilhas dele substituem as nossas.
Ordem no voz_original: (pausas) → Whisper → memes → base → trilha → cortes (já com trilha) → legenda MIX do longo.
- `_ja recebidos` (original dele depois de enviado), `_interno` (cópia que a central move pra fila)
Vigia: `bin\vigia_drive.py`, tarefa do Windows **JoaoLucasVirjaoDrive** (5/5 min, pythonw). Log `vigia_drive.log`.
Pedidos com pid `20261027_000200_jlv...` = passam na frente dos longos normais.

## Pedidos
`pedidos.json`. Primeiro: UJmG_sJ1NX0 "Park Hanju foi Humilhado e Intimidado, Mas Se Tornou o MONSTRO da Escola"
(27 min), pid `20261027_000100_UJmG_sJ1NX0`, pego pela GPU aulasrevolution em 04/11 15:33.

## Teste local (04/11)
2 min do 1º vídeo em `trabalho\teste\final_anime_deitado.mp4`: legenda MIX ok, memes ok, trilha ok, 1080p, -13 LUFS.
A transcrição do teste usou o Whisper small (CPU) e errou palavras; no Kaggle vai o large-v3.

## Pendente / melhorar
- [ ] A última palavra antes do meme fica até 0,5 s em cima dele (o `legenda_mix.blocos` segura o cartão até o próximo).
- [ ] Cortar a abertura do parceiro ("se inscreve no canal...") — o `cliente._cortar_intro` do recap faz isso.
- [ ] Gancho na tela nos 3 primeiros segundos + barra de progresso (o `extra` do burn_subtitles_ass, anime_gancho).
- [ ] Título próprio (hoje vai o título original) e crédito ao narrador na descrição.
- [ ] Alimentador automático (lista de vídeos do canal do parceiro, um por vez).

## Regras que valem aqui
- yt-dlp sem rajada (um vídeo por vez). Nada de Kaggle direto do PC.
- Tudo oculto (sem janela na tela da dona). Postagem sempre agendada.
