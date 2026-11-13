# Lições do melhorador (o que a sessão do Claude aprendeu melhorando este sistema em 26/10 — leia antes de propor)

1. Mude o que a EVIDÊNCIA mostra se repetindo em vários vídeos, nunca um caso isolado nem "melhoria qualquer".
2. Regra vaga não muda nada ("melhore o ritmo"). O que funcionou foi regra com número e componente pronto: o cartão
   final saiu parado em 4 vídeos (2,2–2,8% de movimento) até o manual dizer "desfoque <= 8 px, véu <= 60%, push-in
   1.0→1.18, tudo entra até 0,6 s" e dar o componente pronto (kit `src/lib/efeitos.tsx`) — aí deu 7,2%.
3. O editor "anota" no plano que fez movimento e não faz: confie na medida de movimento (< 4% = parada), não no que
   o editor diz que fez.
4. Nunca afrouxe limite: zona segura y 150–1580 e 60 px nas laterais, letra >= 32 px, só fatos do briefing. Um agente
   já tentou mudar para y 1680 e 24 px por conta própria.
5. O corretor estraga o que está certo se não recebe os fatos: inventou "24h", "30 min", "Entrega 99.4%". Regras de
   "não estrague" + trava de texto resolveram.
6. O editor copiava a edição do vídeo da pasta ao lado — por isso só a pasta dele fica visível. Não proponha regra
   que mande ler outros vídeos.
7. Muitas regras novas de uma vez = o editor esgota os 90 turnos (Follow-up 26/10). Mudança pequena, 1 por vez.
8. Diretor e movimento foram as notas mais baixas em todos os vídeos (5–6): layout repetido (pílula + título + card
   central em toda cena) e cenas paradas. As composições obrigatórias (plano.md) e o kit atacam isso — antes de
   inventar outra coisa, veja se o problema é o editor NÃO usar o que o manual já manda.
10. ESPERAR também é decisão. Se o manual mudou depois do último vídeo do tipo, a mudança ainda não foi medida:
    mexer de novo contamina o teste e ninguém sabe o que funcionou. (27/10: o Gemini quis reforçar a regra do
    cartão final que tinha acabado de entrar e nenhum vídeo tinha usado ainda.)
9. Anúncio: o DONO é o apresentador (foto dele na cena 1 e no cartão final). Entretenimento: verdade (lenda contada
   como lenda), gancho sem spoiler, virada no meio, pergunta no fim.
