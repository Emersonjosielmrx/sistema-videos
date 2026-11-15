# Lista da dona (colada em 15/11 00h) — situação de cada item

Legenda: ✅ feito · 🟡 parcial · ⏳ pendente (com o porquê)

| # | Pedido | Situação | Onde / o que foi feito |
|---|---|---|---|
| 1 | Pose nova de capa (youtu.be/iI52YYpcQAU — ex x namorada na cama) | ✅ 15/11 | `recapd bin/capa_ia_anime.POSES_SENSUAIS["ex_x_namorada_cama"]` (rodízio da capa B dos longos). Adaptada à regra das capas (sem foco no bumbum/nudez parcial). Teste: `D:\tmp\teste_pose\ex_namorada.jpg` — saiu certa pelo Gemini em 20 s. |
| 2 | Vozes do narrador por papel (sistema, monstro) + palavras como "montanhas" (seios), molecagem | 🟡 | Monstro já existe (`config/longo.json vozes_monstro`, `anime-pipeline.py` papel "monstro"). Falta a voz do SISTEMA e o vocabulário de molecagem — ⏳ testes de voz estão PAUSADOS pela dona (memória project_voz_clonada). |
| 3 | Parceiro novo @nexhwaoficial | ✅ 15/11 | `config/parceiro.json` fontes (manhwa). |
| 4 | Ver se vale a pena github robonuggets/gauntlet-loop | ⏳ | Não avaliado ainda — vai pra caixa do pesquisador (avaliação com fonte). |
| 5 | Transição "a tela dentro do celular/carro/da própria imagem" (Short 6sapq_ovKVw) | ⏳ | Não feito: precisa de efeito novo de render (moldura de celular + zoom); entra no melhorador como proposta. |
| 6 | Obra youtu.be/CgyXHx6h2a8 ("Reencarnou como VILÃO e tem uma ESPOSA MAID") | ✅ 15/11 | Partes 1, 2 e 4 do Luke Manhwa no TOPO da fila (`config/fontes_prioridade.json`, série "vilao_maid", 3 não apareceu no canal). Dono fixo da série = InventoReact (`colab/postar_longos.SERIE_DONO`), playlist própria "REENCARNOU como VILÃO com a ESPOSA MAID 🥵 saga em ordem". Próximas partes: ⏳ procurar em canal de FORA do Brasil. |
| 7 | Banimento das chaves Groq e por quê | ✅ (antes) | `hipercool-videos/bin/groq_api.py _marcar_invalida` (401/400 org. restrita); memória feedback_groq_proxy (Groq só pelo Webshare). |
| 8 | Priorizar a trilha do Short DPcqU-UwecY pra anime e Shorts | ✅ 15/11 | NÃO estava na biblioteca (comparei com as 330: maior semelhança 0,096). Música separada da voz (demucs, `recapd bin/separar_trilha.py`) -> `assets/trilhas/prioritarias/mihawk_anime_ref_demucs_DPcqU-UwecY.mp3`, priority=true, moods tense_dramatic e sad_emotional. |
| 9 | Painel de tokens unido ao melhorador e ao continue (gastar/poupar) | ✅ (antes) + 15/11 | `vps157/modo_tokens.py`, combo cc-sobra. 15/11: melhorador dos longos também usa cc-sobra -> ag-opus-5-5 (com Opus 4.6) -> Gemini. |
| 10 | Avisos unificados num bot; pendências humanas só o que a IA não resolve | ✅ (antes) | `video-fila/avisos.py` ROTA + UNIFICADO + HUMANO_ORIGENS. |
| 11 | Erro "32000 output token maximum" | ✅ (antes) | CLAUDE_CODE_MAX_OUTPUT_TOKENS=64000 no settings do VS Code/Antigravity. |
| 12 | "🔴 Recap longo com ERRO ... rc=1" (sem motivo) | ⏳ | O aviso vem de `colab/vps_central.py:1013` e só repete o erro.json do Kaggle ("rc=1"). Melhorar exige mudar o worker do Kaggle — não mexi hoje (5 contas acabaram de ser banidas). Hoje não há nenhum erro.json na fila. |
| 13 | Aviso da Binance "transferência universal" | ✅ (antes) | `lucrativa_patch/investidor_spot.py` (avisa 1x/7 dias; nada desligado). É só desmarcar na Binance. |
| 14 | Shorts repetidos ("YouTube achou 1 Short parecido") | ✅ (antes) | `postador bin/avisos_studio.py` detecta e não repete o aviso. |
| 15 | Metas de inscritos + metas inteligentes auto-ajustáveis | ✅ (antes) | `postador bin/notificar_telegram.py _piso_auto` / metas de inscritos por degrau. |
| 16 | Documento com todos os tipos de aviso e exemplo | ✅ (antes) | `D:\video-fila\AVISOS_TELEGRAM_CATALOGO.md`. |
| 17 | Parceiros @neithkpop @exploramundofc @segurancaexplicada @sabiaquex | ✅ 15/11 | Os 3 primeiros já estavam; @sabiaquex (fatos) cadastrado 15/11. |
| 18 | Capas de exemplo do @ansaketv pra Shorts | 🟡 15/11 | 12 miniaturas em `D:\hipercool-videos\config\capas_referencia\ansaketv_shorts`. Padrão: 2 quadros da cena empilhados (antes / quase beijo) + pergunta provocativa no meio ("SHIROGANE NÃO PERDOOU?!"). ⏳ Aplicar como estilo no capar_shorts. |
| 19 | Parceiro @odaniels00 (estilo de narração e trilha mais emocionante) | ✅ 15/11 | `config/parceiro.json` (anime, marcado como referência de estilo). |
