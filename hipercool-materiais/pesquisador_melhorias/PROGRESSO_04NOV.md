# Progresso da madrugada 04/11 (retomável — ler isto primeiro se o chat parar)

Pedido da dona (04/11 ~02:20, foi dormir, trabalhar até 08:00):
1. Analisar se o desenho do pesquisador (motor com botão, Argon contínuo, sem repetir, só verifica no código e documenta) faz sentido.
2. Procurar o máximo de SKILLS (Claude Code / agentes) que ajudem nos projetos de vídeo.
3. Comparar Argon x Opus 5.5 na pesquisa: o Opus 5.5 (chat principal) faz a MESMA pesquisa `area_voz_rapida` e compara.
4. Crons 05:40 e de hora em hora até 08:00 para continuar se os tokens acabarem.
5. Não guardar só na memória: gravar tudo em disco a cada passo.
6. No fim: mandar para os chats abertos (o dos VÍDEOS LONGOS e o que COORDENA OS CURTOS) as melhorias que valem a pena implementar.

## Fatos conferidos
- Modelos deste chat (transcript): claude-opus-5-5 182 msgs (começo), gemini-4-argon 141 msgs (meio), opus-auto agora.
- Os arquivos de resposta da rodada 2026-11-03_1205 foram reescritos/resumidos pelo Argon, NÃO são as respostas brutas.
  As brutas existem só na conversa (notificações a9266…=Sonnet, ad98b…=Argon, a8d61…=Opus 4.6). Os .output em Temp estão vazios.
- Placar antigo NÃO é confiável: `novos` contava errado e o fallback HTML deu ★0; `importar JUNTO.md` não acha nada (sem "github.com/").
- 404 reais citados: luoyily/RVC-ONNX-Infer, OpenBMB/nanovllm-voxcpm, Seatop/nanovllm-voxcpm (o certo é a710128/nanovllm-voxcpm), ConfigureNode/RVC-C.
- gh CLI não instalado; sem GITHUB_TOKEN -> API REST 60/h.

## Passos
- [x] 1 regravar respostas brutas (sonnet, argon, opus46) + consertar pesquisador.py (estrelas, importar JUNTO, nomes com número)
- [x] 2 pesquisa do Opus 5.5 (eu) -> respostas/area_voz_rapida__opus55.md (+ opus55_busca_github.txt)
- [x] 3 comparar 5 respostas -> COMPARACAO_MODELOS.md (Sonnet 9,5 > Opus55 9,0 > Argon 7,5 > Gemini 7,0 > Opus4.6 6,5)
- [x] 4 skills: SKILLS_VIDEO.md escrito (03:40); Argon 49 links, Gemini 42, todos existem. (antes: Gemini Pro PRONTO (rodadas/2026-11-04_skills/respostas/skills_video__gemini.md, 42 links conferidos, 0 inexistentes);
      Argon ainda rodando -> salvar em skills_video__argon.md, rodar `pesquisador.py comparar rodadas\2026-11-04_skills`, escrever SKILLS_VIDEO.md
- [x] 5 análise do motor -> MOTOR_DESENHO.md
- [x] 6 CURTOS = claude-dc -> ENVIADO 03:45. claude-78 = contas/logins (não mandar). LONGOS = claude-38 (presumido, não respondeu) -> ENVIADO 03:47 com "ignore se não for".
Resposta CURTOS (claude-dc, ~04:00): nenhuma skill instalada (código de terceiros espera a dona). Aproveitou a ideia do qc-skill
sem baixar nada: medidor med_qa_shorts em video-fila\vigilancia.py lê o qa.json dos Shorts das últimas 2 h (0 de 394 com problema).
Deixados 6: decomposer, câmera/tipografia, termos em alta, Remotion -> esperam OK da dona. LONGOS (claude-38): CONFIRMOU que é o dos longos; recebeu a lista e vai implantar o que valer depois de fechar os 2 longos por sessão no Kaggle.
  Fechamento dele: "Aprendizado: 0 aplicados, 0 reprovados, todos deixados" (madrugada usada na redução de tempo: 2 longos/sessão,
  master na junção, Edge em paralelo em anime_tts.preparar_clone, legenda leve). Próximo passo dele: medir custo fixo por frase do RVC (blocos de ~30 s).
LONGOS ~09:20: 1 aplicado (QA dos longos no Kaggle: qa_video.py após o render, GPU; qa.json em na_nuvem\<nome>\qa.json),
  1 reprovado (RVC em blocos: 2 longos por sessão escondem o tempo da voz; cortar nos silêncios arrisca a legenda), 3 deixados.
  Sugestão dele: med_qa_longos na vigilancia.py lendo D:\hipercool-materiais\animes recap\na_nuvem\*\qa.json.
CURTOS ~09:40: V-18 tipografia cinética na legenda MIX (legenda_mix.py, ANIME_LEGENDA_ENTRADAS=0 desliga) + med_qa_longos na vigilancia.py.
  Deixados: câmera sincronizada com a fala (fx_clips._movimento já move tudo; falta tempo por palavra no clipe), gancho 3 s, termos, Remotion.
Manhã 04/11 (dona pediu): reenviados os pendentes ao claude-dc (curtos: 5 itens) e ao claude-38 (longos: 5 itens). Instalar skill de terceiros = só com OK explícito da dona.
TUDO FEITO. Retornos agendados: nada a fazer, a não ser responder se claude-38/claude-dc perguntarem algo. (03:42 perguntei o assunto a claude-38, claude-dc, claude-78; esperando resposta. Mandar a parte "LONGOS" ou "CURTOS" de SKILLS_VIDEO.md ao certo) mandar melhorias aos chats: LONGOS = sessão "continue sessão vídeos longos" (transcript a7522fd2). Coordenador dos CURTOS: não achado
      pelo transcript; perguntar com ListAgents/SendMessage curto. Mensagem = só o que vale a pena (ver SKILLS_VIDEO.md e voz).
## Conferido no código (04/11 03:05) — NÃO recomendar como novo
- RVC na nuvem JÁ usa Applio + FCPE (recapd-ambientes\producao\bin\voz_clonada_nuvem.py:105) e base Kokoro ONNX pt-br com tempo por palavra (:65-78).
- O que é INÉDITO e vale: (a) chamada run_infer_script é 1 POR FRASE (:93-109) -> juntar frases em blocos de ~30 s com silêncio e cortar depois (medir antes no log "[i/n] ... (x s)");
  (b) roteiro anotado {speaker,text,instruct} + voz fixa por personagem (padrão alexandria-audiobook); (c) teste A/B MeanVC (zero-shot, Apache) x RVC — testes de voz estão PAUSADOS: só com OK da dona.
- [x] 7 importar: +54 repos (total 123) e +19 subáreas no config.json (03:00): `pesquisador.py importar rodadas\2026-11-03_1205\JUNTO.md` e o JUNTO das skills; areas_novas do opus55
