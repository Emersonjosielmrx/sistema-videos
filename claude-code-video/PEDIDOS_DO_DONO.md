# Pedidos da dona para o melhorador

O melhorador lê este arquivo em TODA rodada, com prioridade acima dos defeitos do júri. Ele também roda quando há
pedido aberto, mesmo sem vídeo novo.
- Pedido aberto = linha começando com `- [ ] `. Escreva com as suas palavras, um por linha.
- Quando ele atende, a linha vira `- [x] ... → data, o que fez`.
- O que só se resolve mudando CÓDIGO: ele muda numa cópia, testa (compila/importa + renderiza 2 quadros), o crítico
  revisa e só então aplica (com backup; desfaz na hora se a produção der erro, ou se a nota cair em 2 vídeos).
  Se falhar no teste ou no crítico, vira ideia em `IDEIAS_CODIGO.md` para você ver.
- O chat do melhorador (CONVERSAR_MELHORADOR.bat) escreve aqui o que você pedir na conversa.

## Pedidos
<!-- 11/11 dona: "faça as que faltam" — o que o historias-em-frames tinha e este projeto ainda não tem. O código de
     referência continua em D:\historias-em-frames\bin\ (e cópia no Drive em
     manhwa-drive:videos-backup/historias-em-frames/arquivo_20261111/). Um por vez, na ordem (maior impacto em views
     primeiro). Detalhes de cada um: D:\video-fila\linhas\CLAUDE-CODE-VIDEO\ESTADO.md, seção "Ainda falta trazer". -->
- [ ] Efeitos sonoros curtos nas palavras de impacto da narração (dinheiro, choque, clique, virada), sincronizados com o tempo da palavra. Referência: historias-em-frames\bin\fx_audio_final.py, fx_foley.py e config\gatilhos_palavras.json. Volume baixo, no máximo 1 a cada 3 s.
- [ ] Capa (thumbnail) gerada para cada Reel, com pose escolhida de um catálogo e texto grande legível, e conferida por visão antes de usar. Referência: capa_ia_historias.py, config\POSES_HISTORIAS.py, visao_capa.py.
- [ ] Narração que acelera um pouco rumo ao clímax e corta pausas mortas maiores que 0,07 s. Referência: narracao_curva.py.
- [ ] Trilha que sobe de intensidade no gancho e no clímax e desce na resolução, em vez do ducking fixo. Referência: music_escalation.py.
- [ ] Memes visuais de 1 s ligados à emoção da cena (só no modo entretenimento, nunca em anúncio de cliente). Catálogo pronto em D:\hipercool-videos\config\memes_catalogo.json; lógica em historias memes_catalogo.py.
- [ ] Transições por palavra-chave do roteiro (fogo, água, raio, impacto, glitch) além do rasgo que já existe. Referência: elemental_transitions.py e os overlays.
- [ ] Pergunta de engajamento no meio do vídeo e um comentário para fixar, ligados ao tema. Referência: community_hooks.py.
- [ ] Mesmo rosto do protagonista em todas as cenas do modo entretenimento (banco de personagens). Referência: character_bank.py.
