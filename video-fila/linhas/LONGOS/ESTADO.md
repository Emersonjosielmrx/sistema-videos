# LONGOS — estado (atualizar a cada ciclo; mais novo em cima)

## 28/10 22h — feito à tarde/noite (tudo no pacote do Kaggle; nenhum longo saiu ainda: GPU sem cota)
- Efeitos: lista em EFEITOS_LISTA_DONA.md (17 feitos, ~+35% só CPU). Brilho e paralaxe 2.5D "5x menos" (só momentos-
  chave). Glitch corrigido (ia nos trechos normais). H.264 no download conferido (398 AV1 → 136 avc1).
- Mascote viva: mascote_producao.py + tarefa MascoteProducao (8:30/14:30/20:30, 2 falas/rodada). Dona: cabelo A
  (castanho dourado), estilo BIQUÍNI, nada sentada/deitada, vídeo 16:9 com ela ENTRANDO andando (veo_mascote --entra,
  imagens em mascote_waifu_v2\andando). Amigas (loira, indígena) aparecem menos, à direita, 1 a cada 3 falas.
  mascote_overlay: "_andando_" = tela cheia (ela anda no vídeo); antigos 9:16 = canto. Conferir 1º longo com isso.
- Melhores cortes (dona: "pros canais de cortes"): bin\melhores_cortes.py no fim do longo → cortes_longo\ (9:16) +
  cortes.json; trabalhador (VPS, backup .bak_) sobe junto. FALTA: a dona dizer os canais → postar (não liga sozinho).
  Teste num roteiro real: 5 trechos de ~90 s, notas 8–10, ganchos bons (bench\teste_cortes.py).
- Painel :8790: campo "Viu um vídeo bom?" (Telegram + estado\videos_referencia.jsonl) → tarefa EngenhariaReversaFila
  (2 em 2 h) → referencias\<id>\ANALISE.md + LINHA_DO_TEMPO.md.
- Porão (1TXD66c_ofg, 482 mil views): referencias\1TXD66c_ofg\ANALISE.md. CANDIDATOS a teste A/B do melhorador:
  abertura com ~50 cortes no 1º min; CTA de tribo nos 1os 20 s; mini-gancho a cada 15 min; "Completo" no título.
- OmniRoute 28/10: "antigravity/gemini-3.8-flash-tiered" travou (nem "ok" em 150 s); "gemini-fila" ok em 2 s. O
  pipeline usa o tiered no resumo/personagens — se seguir travado, trocar GEMINI_TEXTO_VIDEO.

## 28/10 ~10h — claude-36 assumiu (claude-fe parada desde 04h em 502/429)
- Kaggle: 0 GPU (4 contas sem cota semanal; 19 sem telefone verificado). 5 pedidos esperando na fila.
- Pedido da dona 04:05 (resumo/ambientação no início, mascote falando, efeitos tipo hipercool em camadas com
  custo medido): andamento em EFEITOS_ANDAMENTO.md; lista pra ela em EFEITOS_LISTA_DONA.md.
- FEITO no código (bin): resumo de abertura (_resumo_longo), mascote falando os CTAs (_marcar_falas_mascote,
  anime_segments._falas_mascote, mascote_overlay segura o quadro). Medição de efeitos em bench\.
- Próximo: conferir render curto no PC1 (bench\render_teste) → montar_pacote.py --codigo → 1º longo real no Kaggle
  quando a cota voltar → camada 1 de efeitos se a dona aprovar; testar NVENC no Kaggle.

## 26/10 18:50 — 1º ciclo
**Objetivo da dona:** máximo de views/viralização. Longos com voz clonada IGUAL aos Cortes + revezamento de vários
narradores (passagem criativa, jeito de cada um). 4 frentes de GPU em paralelo (3 pelas VPS + 1 direto do PC) testando
4 possibilidades ao mesmo tempo.

**Situação real (provado):**
- Voz clonada no Kaggle: só funcionou a partir de 26/10 ~17h (venv do Kaggle quebrado → fallback virtualenv). Sessões
  OK: emersonjosiel, aulacomia, e4487017 (vivo_<conta>.json applio:true, kokoro:true). emersongenc rodou sessão quebrada.
- NENHUM longo com voz clonada/revezamento pronto ainda. Em produção agora (18:47): 6d2a (e4487017, 92% acabamento),
  PFbu (emersonjosiel, 26%), 5FDt (aulacomia, 28%) — todos de revezamento (teste_narradores.json, 10 vozes).
- Vídeos antigos (25/10 e manhã de 26/10): Thalita do edge + borrão fixo. X90 foi ao ar no inovare manhwa br
  (https://youtu.be/qSM3JWPFeWA). Postagem agora só com render.json voz_clonada+applio_ok.
- Problemas de infra resolvidos hoje: edge bloqueia IP do Kaggle (proxies no pacote), venv, central travando em rclone
  (teto _rcl), duplicata de pedido, alimentador travando (vigia reinicia), janelas (sem_janela/rodar_oculto).
- Bloqueio das VPS ao IP de casa por excesso de SSH seguidos (~10 min): juntar comandos numa conexão só.

## Achados da linha de base (4wuf, 26/10 07h, modelo antigo — folha de contato do juri_longo.py)
- OK: gancho escrito no topo na abertura; legenda karaokê legível; fundo desfocado nas laterais; movimento 17–62%
  (nenhum trecho parado).
- [CERTEZA] Balões do manhwa em INGLÊS ("STUDENT NUMBER 35", "CALM DOWN"...) — fonte gringa. Pensar: tradução dos
  balões (pesado) ou zoom que evita balão; pelo menos não destacar.
- [CERTEZA] Muito sangue/gore em vários trechos — risco de desmonetização (avaliar filtro/menos tempo nesses painéis).
- [CERTEZA] Sem mascote e sem CTA no meio em nenhum quadro da amostra (base item 2 do prompt).
- [CERTEZA] Final repete a mesma imagem nos 3 quadros (termina parado).
- Ferramenta: colab\juri_longo.py (júri Gemini por amostra + movimento) — claude-code-video v1.1.

## 27/10 00:35 — pedidos novos da dona
- DELOGO aprovado ("extremamente boa") pra esconder texto/marca — memória feedback_delogo_esconder + MURAL.
  Nomes apagados com delogo nos revezamentos antigos: *_SEM_NOMES.mp4 em recap-longos-prontos (6d2a e 5FDt prontos;
  PFbu/hJaA rodando). Atenção: neles o NOME do parceiro ainda é FALADO nas trocas (oferecer silenciar a palavra).
- TESTE tarja branca x delogo na legenda queimada da fonte: quando vier fonte com legenda queimada (anime_legenda_fonte
  acha), fazer trecho curto com as 2 versões pra dona; sem resposta, gerar os 2 longos.
- MELHORADOR do longo (colab\melhorador_longo.py, desligado no controle.json até a dona ligar): camadas de modelo
  como o melhorador de hoje — Gemini 3.8 (ilimitado) nas tarefas que de fato aliviem os de cima; Kiro Sonnet só a
  partir de 01/11; Opus 4.6 (antigravity, cota por tempo) e Opus 5.5 (cc, nem sempre há) no decisor; o sistema
  funciona com ou sem o 5.5. Argon: só quando a dona disser que está pronto. HOJE: testar só com o Gemini 3.8 e
  medir se ele é útil (comparar o que ele decide com o que a sessão Claude decidiria).

## 27/10 01:10 — 1º teste do melhorador com o Gemini 3.8 (analista + decisor)
- Analisou o 5FDt sozinho (nota 4,38; 6d2a 4,5). Decisor: diagnóstico com prova, NENHUMA alavanca (certo: nada
  ali se resolve por alavanca) e 4 propostas CERTEZA corretas em PROPOSTAS.md: gancho cobre o rosto; plano parado
  > 9 s e final parado; caixas/balões em inglês (sugeriu delogo); karaokê grudando palavras ("atingiro") — esta a
  sessão Claude não tinha visto. VEREDITO: Gemini 3.8 serve como analista e como escritor de propostas; ainda NÃO
  testado aplicando alavanca de verdade. LUFS corrigido (5FDt: -13,8 LUFS, 0 silêncios = trilha ok).
- Próximo pra sessão forte: atacar as 4 propostas (gancho fora do rosto, plano parado, balão em inglês, karaokê).

## Lista (CERTEZA / GOSTO)
1. [CERTEZA] Conferir o 1º longo de revezamento quando sair: vozes_lista no render.json, Kokoro, passagens, legenda com
   nome, trilha, marca d'água, sincronia, duração vs frases. Folha de contato + áudio.
2. [CERTEZA] Base da seção 3 do prompt no vídeo real: tarja só com legenda queimada, CTA meio + mascote, gancho 0–2 s.
3. [GOSTO] 4 frentes de teste em paralelo (uma por GPU): definir fatores (ex.: narrador único x revezamento; com/sem
   mascote; trilha; ritmo).
4. [PEDIDO DONA 26/10] Inserir cortes curtos dos produtos de IA (Veo limpo, 15–25 s, 1 a cada 40–60 min, sem
   WhatsApp/telefone/link na tela) — começar com 1 vídeo teste. Risco: banimentos anteriores por propaganda.
5. [PEDIDO DONA 26/10] Ampliar longos para outros nichos (como os Cortes): candidatos = compilados dos Cortes por
   nicho (30–60 min), temporada resumida, filme explicado, mistério/true crime, histórias pra dormir. Aguardando
   escolha da dona.

## Próximos (dona 26/10 19h: "trabalhe sozinho, não espere minhas respostas")
1. Validar o 1º longo de revezamento (6d2a/PFbu/5FDt) — folha de contato, áudio, render.json.
2. Frente DORAMA LONGO: achar 2–3 canais em inglês de C/K-drama recap longo (1–3 h) e mandar 1 vídeo teste pelo
   mesmo caminho (Kaggle + voz clonada + revezamento) pro Dorama Noturno. yt-dlp sem rajada (ytdlp_vez).
3. Frente FILME EXPLICADO (compilados de movie recap) pro Filme Noturno.
4. Depois: série completa, donghua; inserção de produto (1 vídeo teste, regras de segurança acima).

## PRECISA DO DONO
- (não bloqueia) opiniões sobre frente nova; a ordem acima é decisão minha.
- X90 já no ar com o modelo antigo: manter ou tirar.
