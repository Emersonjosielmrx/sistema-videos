# Cortes / recap de parceiros — o que melhorar, por prioridade (22/10/2026 ~10:50, claude-8a)

Base (medido hoje nos logs e no Studio):
- Produção: 54 Shorts prontos em 20/10, 61 em 21/10, 24 até 10h de 22/10. Mediana 13 min por Short (4 a 50).
- Falhas: 14 em 20/10, 4 em 21/10, 4 em 22/10 (todas 05:23-05:36, falta de memória do piloto).
- yt-dlp barrado: 467 linhas "yt-dlp em pausa" em 21/10; hoje sem Short pronto de 06:55 a 09:51.
- Capa IA: 17 Shorts sem capa em 21/10 (filtro do Cloudflare recusa + reserva sem saldo).
- ALCANCE: dos 34 Shorts de parceiro com views lidas, mediana = 1 view; 16 com 0; só 4 passaram de 1.000.
  Manhwa Noturno: 0 a 5 views por Short.
- Voz clonada: 72 Shorts; nenhum com 48 h ainda (41 agendados pro futuro), então ainda não há dado de narrador.

Marcação: [EU] = dá pra fazer sem o dono · [DONO] = precisa decisão/ação dele · [JUNTO] = eu preparo, ele aprova.

## P1 — Alcance (o maior problema: produzir 60/dia que dão 1 view não adianta)
1. FEITO 22/10 ~15:40 — `python D:\video-fila\diagnostico_alcance.py` (rodar de novo em 3-4 dias: o lote de views
   do M8 vai preencher muito mais). Hoje, 46 Shorts de parceiro com views de 48-96 h: mediana 1, 21 com zero, 8 com
   1.000+ (máx 1.827).
   - NICHO: filme_sem_voz (n 3, mediana 1.334, 2 com 1.000+), dorama (n 5, média 655, 2 com 1.000+) e fatos (n 6,
     média 430, 2 com 1.000+) rendem; manhwa (n 24, mediana 0, 50% zero) e anime (n 5, mediana 0) não — e são 63%.
   - PARCEIRO: kaijinre (a fonte de manhwa, n 20) mediana 0, 60% zero; d_UCSJ6_g (dorama) 2 de 2 com 1.000+;
     andreu_edit1 e xiuliamelo bons.
   - LÍNGUAS: ru/it/th/id 100% zero — já tinham sido cortadas em 21/10 (1/dia, estoque 2; a semana agendada que
     aparece é sobra de antes e esgota sozinha). Nada a mudar.
   - TÍTULO: provocação (mediana 7, 29% zero) > busca > curiosidade (61% zero); o placar de estilos (Thompson) já
     vai puxando pra provocação sozinho.
   - Palavrão em título/descrição: 0 nas 368 fichas de 7 dias (o "na porra" que apareceu era antigo).
   DECISÃO DO DONO sugerida: mais fonte de filme/dorama/fatos e menos kaijinre nos canais que aceitam qualquer nicho
   (os canais de manhwa continuam manhwa). Amostra ainda pequena: confirmar com a próxima rodada do diagnóstico.
2. [EU] Ler "continuaram assistindo" (% que não deslizou) dos Shorts de parceiro, não só views: mostra se o
   problema é o gancho dos 1ºs segundos (retenção) ou distribuição (o YouTube nem mostrou).
3. [JUNTO] Cortar produção pros canais/nichos que dão 0 view sistematicamente e dobrar nos que dão 1.000+
   (o controlador hoje produz por "fila vazia", não por resultado).
4. [EU] Agendamento muito à frente: Esporte Noturno já tem Short pra 28/10 (6 dias). Vídeo velho na fila perde a
   hora certa e a gente só mede uma semana depois. Proposta: no máximo 2-3 dias de fila por canal.
5. [EU] Testar o 1º segundo: hoje o Short abre com bordão/trecho original. Medir "continuaram" com e sem trecho
   (já há 6 hoje com trecho) e com gancho de pergunta x afirmação.
6. [JUNTO] Título/capa: os títulos são todos CAIXA ALTA provocativa iguais entre canais. Testar variação por
   canal (o Studio tem teste A/B de capa; teste_ab existe no youtube_studio_extras).
7. [DONO] Canais novos com 0-5 views (Manhwa Noturno, Noturnos): decidir se seguem com 3/dia ou se concentra.
8. FEITO 22/10 15:30 — achei 5 pares JÁ NO AR (mesma fonte em 2 canais pt; causa = disco cheio de 20/10 apagou o
   "já feito"); trava nova na postagem e na produção (registro durável _fontes_postadas.json). Dono decide os 5 pares.

## P2 — Gargalo de produção: yt-dlp barrado (para tudo por horas)
9. [EU] Medir quanto da baixa é legenda x vídeo: 21/10 tinha legenda YT em pt e es por vídeo = 3 pedidos por Short.
   Se a transcrição já vem do Whisper/Groq, a legenda do YT pode sair (1 pedido a menos por Short).
10. [EU] Baixar a fonte 1 vez só (hoje: tentativa "width<=720" e depois "height<=720" = 2 downloads quando a 1ª
    falha). Usar um formato só, que sempre existe.
11. [EU] Fila de fontes já baixadas (estoque de 10-20 vídeos baixados de madrugada, devagar): de dia o Cortes
    trabalha do estoque e não depende do IP. Hoje ele baixa na hora de produzir.
12. [JUNTO] Desktop/PC3 como 2º IP? Ele está na mesma internet (não ajuda). Só um IP de outra casa/4G resolveria;
    Webshare não serve (testado: proxy fixo barrado, rotativo trava no download).
13. [EU] Painel: tempo parado por bloqueio por dia (minutos de pausa) como número na Visão geral.

## P3 — Qualidade do vídeo
14. [EU] Capa: 17 sem capa em 21/10. Quando a IA recusa, usar quadro do próprio vídeo com o título por cima
    (gerador local, sem filtro), em vez de sair sem capa.
15. [EU] Conferir a sincronia narração x imagem e o fim sem imagem parada em 5 Shorts de hoje (freezedetect +
    "cortes pelos tempos"), já que o roteiro com tempo roda em todos agora.
16. [EU] "Short curto, sem contexto" (X): medir duração final x original nos de hoje; abaixo de 60% = refazer roteiro.
17. [EU] Gancho de retorno: conferir nos logs quantos foram recusados 2x e saíram com CTA (o fallback).
18. [JUNTO] Trechos originais: tarefa TrechosNoite 03:20 baixa 10 personagens; ouvir os "trechos_revisar".
19. [EU] Marca d'água/tarja: o conserto de 06:33 só vale pro @kaijinre; conferir outros parceiros com tarja.
20. [EU] Legenda queimada falhou 4x em 20/10 ("burn_subtitles falhou"): achar a causa (sai sem legenda).
21. [JUNTO] Fidelidade da voz clonada (plano próprio em clone2\MELHORIAS_FIDELIDADE): A/B pra ouvir.
22. [DONO] Vozes muito usadas x pouco usadas: quando houver views (a partir de 24/10), cortar narrador que não rende.

## P4 — Escolha da fonte (o que entra na fila)
23. [EU] Conferir o assunto do vídeo do parceiro contra o nicho do canal antes de baixar (caso @papodebixo:
    "pastores ricos" no Bicho Noturno). Precisa OK do dono (item 6 do PENDE DO DONO).
24. [EU] Priorizar fonte pelas views do original x idade (o log já tem "(N views)" da origem): fonte que viralizou
    no parceiro tende a render; hoje o rodízio é por nicho.
25. [EU] Evitar fonte já usada por outro canal da casa (mesmo vídeo de origem 2x).
26. [EU] Fonte em inglês x pt: medir se Short traduzido rende diferente.

## P5 — Postagem
27. [EU] Horário: medir views por hora de publicação (o ledger tem publish_at) e ajustar os horários por canal.
28. [DONO] Verificação única (telefone) no ForjaReact, Filme Noturno e Dicas: hoje travam no limite diário.
29. [DONO] Apagar os privados duplicados do ForjaReact.
30. [EU] Ritmo: o controlador produz 54-61/dia; os tetos somados dos canais BR são ~3/dia cada. Conferir se
    sobra Short pronto que nunca posta (fila crescendo = render desperdiçado).
31. [EU] Reaproveitar no TikTok/Insta os Shorts de parceiro que deram 1.000+ (o catálogo já faz reuso, conferir).

## P6 — Custo e estabilidade
32. [EU] FEITO hoje: vigia sem chamar o agente pra ruído (Kiro: 48 -> 11 rodadas no replay). Conferir amanhã.
33. [EU] FEITO hoje: reserva do Kiro no vigia e no painel. Conferir quando o Kiro zerar (~23/10).
34. [EU] Memória: o clone travou com o piloto rodando junto (05:31). Regra no controlador: não roda coisa pesada
    (separação/treino) no PC1 enquanto o Cortes converte voz.
35. [JUNTO] GPU do Kaggle na conversão da voz (plano pronto, claude-c2): só pra vídeo longo; Short em lote.
36. [DONO] Limpeza do source.mp4 (3,8 GB no D:, hoje 9% livre): regra nova precisa do OK.
37. [EU] Disco do PC2 com 4,3 GB: medir o que ocupa (sem mexer nos arquivos do hipercool).

## P7 — Painel / acompanhamento
38. [EU] Aba "Alcance": views 48 h por canal/nicho/narrador com filtro (sai do item 1).
39. [EU] Na aba Voz, ranking de narrador por views mediana quando houver dado (a partir de 24/10).
40. FEITO 13:15 (dono decidiu): sem resposta em 24 h o achado vira candidato e entra em
    aprendizado\PARA_IMPLEMENTAR.md; a sessão que mexer na produção é obrigada a ler e decidir (memória atualizada).

## Ordem sugerida pra fazer agora (sem esperar o dono)
1 -> 2 -> 9/10 -> 4 -> 14 -> 15/16/17 -> 20 -> 24/25 -> 27 -> 30 -> 34 -> 38.
