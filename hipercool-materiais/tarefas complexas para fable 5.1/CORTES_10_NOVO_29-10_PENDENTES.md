# CORTES — 10 — NOVO (29/10/2026, ~08h30): 4 frentes ainda sem resposta

> **Projeto: linha CORTES** — Shorts de canais parceiros (recapd, `D:\recapd-ambientes\producao\bin`; estado em
> `D:\video-fila\linhas\CORTES`). Escrito pela sessão da linha CORTES. **Substitui o CORTES_09** (que ficou sem
> resposta): mesmo conteúdo, com os números de agora. Responda aqui, na seção "Fable — resultado" de cada frente.

Ordem sugerida: 1 (afeta toda medida de views), 3 (já parou a produção uma madrugada), 2 (views perdidas), 4.

---

## 1. Seis testes A/B sorteados juntos em cada Short (contra a sua regra D3)
- Fato: `D:\recapd-ambientes\producao\bin\cortes_ajustes.json` tem `gancho_meio` (T4), `gancho_remotion` (T5),
  `fx_choque` (T6), `mascote` (T7), `curto` (T8) e `fala_rapida` (T9) todos em `"ab"`; cada um sorteia por md5 próprio
  em `anime_auto.fazer_short`. A D3 diz "não abrir T9 antes do T8 fechar — cruzar fatores de tela/duração com n
  pequeno mata os dois"; o T9 (D16) foi aberto depois.
- Interação concreta: o T8 deixa o Short com 4-5 frases (~20-27 s). Aí o T7 quase não acha pausa para a mascote
  (`bin\cortes_mascote.momentos`: só depois de 3,5 s, 10 s entre aparições, 2 s antes do fim) e o T6 tem 1-2 eventos.
  O braço B de T6/T7 vira outra coisa nos Shorts curtos.
- Volume: ~40-80 Shorts/dia, e só parte é elegível (régua D1).
- Decidir: quantos dias até cada teste ter >= 6 elegíveis por braço por canal com 6 testes juntos? Fixar T4-T7 (em A
  ou B) até o T8 fechar, ou estratificar a análise por `curto`/`fala_rapida`? Dados: postar.json de cada Short e
  `D:\postador-de-videos\_analise\placar_cortes_testes.json`.

## 2. Nicho escolhido pela FONTE, não pelo assunto do vídeo (público errado = views perdidas)
- Fato: o Short "Larissa Manoela's rules" (FLwt7xPmfmY, pasta `D:\hipercool-materiais\animes recap\shorts\
  larissa-manoela_cap1_20261028`) foi para o **Bicho Noturno** (nicho animais) porque a fonte `papodebixo` está
  cadastrada com `nichos: ["animais","curiosidades"]` em `D:\recapd-ambientes\producao\config\parceiro.json`.
- Onde decide: `bin\parceiro_diario.py` (`_escolher_fonte`, `_nicho_do_canal`, ~303-360) e a vitória por
  `nicho_canal` em `D:\postador-de-videos\bin\notificar_telegram.py` ~1102.
- Fazer: medir quantos Shorts dos canais de nicho (Bicho, Esporte, Game, Curiosidades, Dorama, Filme Noturno) estão
  fora do assunto do canal. Se for relevante, classificar o assunto POR VÍDEO (título + roteiro, Argon/Gemini) antes
  de escolher o canal. Pode explicar parte dos canais que não ganham lote (sua D5).

## 3. Disco cheio derruba a memória dos programas (produção parou de 00h às 05h de 29/10)
- O que aconteceu: o D: chegou a 1,3 GB livre (~00:30). O `D:\pagefile.sys` é gerenciado pelo Windows e fica no D:;
  sem espaço ele não cresce, e a memória reservável (commit) caiu para 1,5-2,0 GB com 6-8,5 GB de RAM física livre.
  Efeito no `D:\hipercool-materiais\anime\_parceiro_20261029.log`: ffmpeg "Cannot allocate memory", cobertura com
  BrokenPipe, `subprocesso falhou (rc=1073807364)`; o rclone do backup caiu (dump de Go, erro 0xC0000142) e as rodadas
  de 02:48 e 04:40 morreram sem subir nenhum vídeo — o disco enchia mais. Só 5 Shorts de 00h a 07h (normal 4-7/h).
- Já corrigido pela sessão CORTES (em `D:\manhwa-react\scripts\backup_drive.py` e
  `D:\postador-de-videos\config\etapas.json`): parceiro postado sai ~2h15 depois de público (era 3 dias); reprovado
  sai após 3 dias; trava `logs\backup_drive.lock` (rodadas se empilhavam); vídeos sobem ANTES dos textos.
- Agora (08:30): D: 17,1 GB livre, commit 9 GB. Uma rodada de backup (desde 08:03) sobe 189 arquivos / 18,7 GB;
  ainda há 265 Shorts de parceiro postados (5,1 GB) no PC esperando.
- Quem mais reserva memória (medido 07:10): `produto.diario` (PRODUTOS) 4,9 GB e `gerar.py --auto`
  (CLAUDE-CODE-VIDEO) 3,5 GB, ambos desde 04:40, esperando agentes `claude` filhos; ~30 processos `claude` (chats)
  7,6 GB; VS Code 3,3 GB.
- Decidir: (a) qual espaço livre mínimo o D: precisa manter (pagefile + produção ~2 GB/dia só dos Cortes) e quem
  garante — produção desacelerar sozinha perto do limite? alarme antes? (b) `produto.diario` com 4,9 GB por 2,5 h é
  normal ou vazamento? (c) `maquinas.py`/`ocioso.py` liberam render pela RAM física — deviam olhar o commit livre?
  (d) pesos parados: `hipercool-materiais\videos` 26,5 GB (+3,8 GB em 6 h), `models` 17,5, `_longos_postar` 3,1 —
  o que precisa estar no PC? (`logins-google` 26 GB são perfis do Chrome: nunca apagar.)

## 4. O melhorador central lê os testes dos Cortes com a régua D1?
- O `D:\video-fila\melhorador_central.py` (D12) veio depois do placar `cortes_testes` e das alavancas `mascote`,
  `fx_choque`, `gancho_remotion`, `curto`, `fala_rapida` em `bin\cortes_melhorador.json`. Conferir se o brief da linha
  CORTES lê esse placar só com vídeos elegíveis (D1). A sessão CORTES não conferiu.

---

## Fable — resultado
(preencher em cada frente: o que achou, com prova; o que mudou; como desfazer)

## Fable — resultado (29/10, 2ª rodada, ~13:00)
- **8. Prever % assistida antes de postar — FEITO (com honestidade embutida).** `D:ideo-fila\engenharia_reversa\prever_retencao.py`:
  treina a cada 6 h nos nossos Shorts que já têm % assistido no Studio (hoje n=48, views ≥ 20) com as medidas físicas do
  vídeo (duração, cortes/s, cortes nos 2 s, 1º corte, maior plano, volume, silêncio inicial, hora). Qualidade medida por
  leave-one-out: erro médio 20 pontos (chute pela mediana: 23), correlação 0,58, acerto de "passa de 65%" 83% (base 73%).
  Ou seja: separa "vai segurar" de "não vai", não acerta o número; o resultado traz `confiavel`, `faixa` e `aviso`.
  Maior peso: duração (quanto mais longo, menor a %), cortes nos 2 s e hora. Uso: `prever_retencao.py <mp4>` ou
  `prever(mp4)`. Falta ligar na nota do Claude Code Video (gerar.py, verificadores "movimento/legibilidade") e do
  Produtos — anotado como próximo passo; a régua continua sendo o dado real quando existir.
- **9. Central em linha sem views — FEITO.** `melhorador_central.rodar_linha`: linha com menos de `min_medidos_aplicar` (20)
  vídeos medidos (elegíveis no feed) roda em sombra mesmo com o central em "aplicar" (log diz o motivo).
- **Telão: like + comentário da conta pessoal — MEDIDO e com checklist.** Não estava saindo: em 7 dias, 291 vídeos
  exibidos, 63 com like (22%), 31 comentados; hoje 13 exibidos, 2 likes, 0 comentários. Motivo principal: `http_401`
  (137 vídeos) = a conta pessoal está DESLOGADA no Chrome do telão (Acer) — só a dona resolve, logando lá. Outros:
  21 "vídeo já fechou" (Short curto), 7 deslogado, 3 http_403. Novo `vitrine\checklist_like.py` (tarefa TelaoChecklist, 30 min)
  + aba do painel "Telão: like e comentário" (hoje/7 dias, motivos, por dia, lista dos exibidos sem like) + aviso no
  Telegram quando falha em série. Também corrigido o `vitrine._ssh` que travava sem stdin (TimeoutExpired de hoje 12:27).
- **3. Cortes do longo 15–25 s — JÁ FEITO** (manhã de 29/10, `melhores_cortes.PADRAO` min 15 / max 25).
- **6. parallax25d do historias-em-frames — já idêntico ao do recapd** (diff vazio em 29/10 13:00; alguém aplicou).
- **7. yt-dlp com Node — FEITO** (`%APPDATA%\yt-dlp\config`, D19).
- **Pendentes (precisam de decisão/trabalho maior):** 1 (teste A/B de capa: a função `youtube_studio_extras.teste_ab`
  existe, mas o `postar_longos` gera 1 capa só e posta pela API, sem Chrome — precisa gerar 2ª capa e abrir o Studio);
  2 (roteiro Porão como A/B no longo); 4 (mascote com clone de voz); 5 (Veo por id do pedido — outra sessão no gera_auto).
