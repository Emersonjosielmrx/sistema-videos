# LONGOS — decisões (mais nova em cima)

- 13/11 00:12 [melhorador código ag-opus-5-5] mascote_overlay.py: Descarte automático de overlays na transição de cena e filtro de memes externos (46 linhas). Desfazer: copiar mascote_overlay.py.bak_20261113_001251_melhorador

- 12/11 23:40 [melhorador código ag-opus-5-5] fx_clips.py: Movimento de câmera dinâmico obrigatório nos primeiros 6s do gancho (26 linhas). Desfazer: copiar fx_clips.py.bak_20261112_234032_melhorador

- 10/11 23:35 [melhorador agy/gemini-3.8-flash-high] EXPERIMENTO aberto 'mascote_voz_thalita': A={} x B={'mascote.voz': 'pt-BR-ThalitaMultilingualNeural'} — Testar a voz pt-BR-ThalitaMultilingualNeural na mascote para obter entonação mais jovem, expressiva e compatível com anime/waifu nos momentos de CTA e reação, sem aumentar o tempo de render em relação à FranciscaNeural.

- 06/11 17:01 [melhorador] EXPERIMENTO 'cta_inicio_frase_7' fechado: vence A (B deixou o render 1.4x mais lento)

- 29/10 22:28 [melhorador código agy/gemini-3.8-flash-high] mascote_overlay.py: Remover desfoque gaussiano pesado no fundo durante overlay da mascote e limitar quadros estáticos a 3.5s (9 linhas). Desfazer: copiar mascote_overlay.py.bak_20261029_222802_melhorador

- 29/10 21:53 [melhorador código agy/gemini-3.8-flash-high] fx_clips.py: Priorizar topo/rostos no crop vertical 16:9 para evitar decapitação de personagens (34 linhas). Desfazer: copiar fx_clips.py.bak_20261029_215327_melhorador

- 29/10 19:22 [melhorador código agy/gemini-3.8-flash-high] anime_tts.py: Corrigir truncamento da última palavra/frase e congelamento de ~7s no final do vídeo (59 linhas). Desfazer: copiar anime_tts.py.bak_20261029_192226_melhorador

- 29/10 18:51 [melhorador gemini-4-argon] EXPERIMENTO aberto 'cta_inicio_frase_7': A={} x B={'cta.depois_da_frase': 7} — Atrasar o CTA inicial da frase 4 para a frase 7 reduz a quebra do gancho nos primeiros segundos de história e aproxima a retenção inicial do patamar de 72.3% assistido observado em 3KMWDC4AQl8.

## 28/10 (claude-36) — melhorador v2: views reais + teste A/B; resumo de abertura; mascote fala
- Melhorador lê o DESEMPENHO REAL (painel :8790 /api/ranking: views, tempo médio, views/h por longo postado) e
  isso entra no decisor acima do júri (PROMPT_MELHORADOR v2).
- TESTE A/B: o decisor abre 1 experimento por vez (linhas\LONGOS\experimento.json, só chaves de alavanca); o
  cliente.enviar alterna A/B por pedido (pedido.json variante/longo_override) -> kaggle_trabalhador põe
  ANIME_LONGO_OVERRIDE -> anime-pipeline._cfg_longo aplica; pronto.json/render.json registram a variante e os
  segundos de render. julgar_experimento: 2 vídeos por lado; B vence por views/h (x1,3) ou júri (+0,3) sem ficar
  1,4x mais lento; vencedor vira alavanca global (vigiada). Histórico: experimentos.jsonl. Testado isolado
  (bench\teste_melhorador.py).
- Alavancas novas: resumo.ligado/max, mascote.fala/tom/voz.
- [GRANDE] Resumo de abertura (anime-pipeline._resumo_longo) e mascote falando os CTAs — ver EFEITOS_ANDAMENTO.md.
  Desfazer: config/longo.json resumo.ligado=false / mascote.fala=false.

## 27/10 20h20 — recap longo SÓ nas GPUs
- O controlador mandava "anime longo" pra CPU do PC2 (ocioso.disparar_anime_longo -> anime_auto --engine worker):
  4 no dia, 3 falharam por disco cheio, o mesmo longo foi 3x. Cortado em controlador._cortes_pc2 (religa só com
  ANIME_LONGO_PC2=1). Longo = cliente.py (PC1 baixa e manda) -> VPS hermes-prod -> Kaggle. PC2 fica pros Shorts.
  _anime_longo_pc1 (kanban, só se a dona fixar no PC1) continua como estava.

## 27/10 20h — melhorador vira o substituto do chat (AINDA DESLIGADO)
- Modelos: sem Opus/Kiro (modelos_desligados); decisor = Argon (400 s) -> Gemini 3.8 x2 rotas; analista = Gemini 3.8.
- Lê PEDIDOS_DONA.md em toda decisão. Conserta código sozinho (codigo.modelo, caixa isolada, ≤ 60 linhas, válido ->
  real com backup -> pacote -> vigiado/desfeito). Testado num arquivo de brinquedo: aplicou e o teste passou.
- Alavanca/conserto agora SOBE O PACOTE (antes a mudança nunca chegava às GPUs do Kaggle).
- GPUs: central parada > 20 min = mata rclone preso na VPS; 0 GPU há 6 h = aviso 1x/dia. Testado.
- Conversa com a dona: atalho "Conversar com o Melhorador" na Área de Trabalho (CONVERSAR_MELHORADOR.bat ->
  conversar_melhorador.py): mostra onde ele está e abre o Claude Code numa conversa fixa (continua de onde parou).

## 27/10 16h — cota semanal de GPU do Kaggle
- aulacomia, e4487017 e emersonjosiel: kernel termina ("complete") logo depois de lançar, sem gravar vivo; a central
  relançava a cada 5 min. Provável cota semanal de GPU (30 h/conta) — rodaram ~3 sessões de 12 h desde 26/10.
  vps_central: "complete" sem sinal de vida desde o lançamento = conta descansa (ruins, TTL 12 h) e a vaga vai pra
  próxima. Só sobra emersongenc com GPU até a cota voltar ou a dona verificar telefone de mais contas.

## 27/10 15h — modelos do texto do vídeo + trilha alta
- [GRANDE] Passagem de vez (texto curto) = Argon puro (:20133, 90 s de limite) e, se demorar/falhar, Gemini 3.8 no
  resto do vídeo; jeito do narrador (texto longo) = Gemini 3.8 (antigravity/gemini-3.8-flash-tiered) direto. Medido
  no mesmo trecho (80 frases, 4 narradores): Gemini 3 sozinho 20 s com "caralho" e "mijada"; Argon em tudo 743 s
  (bloco de 1–5 min, caiu no limite); Argon curto + 3.8 = 205 s, sem palavrão. Desfazer: anime_tts._criativo
  (TEXTO_VIDEO_MODELO="" = só Gemini; GEMINI_TEXTO_VIDEO troca o 3.8).
- [GRANDE] Trilha alta com voz clonada: fx_music._ganho_voz leva a narração a -18,5 LUFS (edge, referência da
  trilha de -28) antes do mix, +limitador. Teste: voz -26,6 -> +8,1 dB, final -18,1. Vídeos já feitos: separar voz e
  trilha no PC1 leva 1,75 s por segundo de áudio (~2,2 h por longo de 75 min) ≈ metade de um render novo -> não
  compensa (regra da dona); vale só pros próximos.

## 27/10 09h — vídeos feitos 2x (dona brava: "não deixar mais isso acontecer")
- CAUSA: o alimentar recolhia o pronto (marca feito + apaga o pedido do Drive) e na MESMA volta abastecia com a lista de
  feitos lida no começo da volta e sem conseguir ler o pedido apagado → reenviava o vídeo que acabou de chegar.
  RA4H (Classmates) e PFbu (Stone Age) renderizaram 2x; as versões _SEM_NOMES limpas foram desperdiçadas.
- Conserto: cliente.alimentar relê _ja_feitos depois de recolher e tira os recolhidos do `ped`; pedido.json em cache.
  Versões antigas de RA4H/PFbu apagadas da pasta de revisão (pedido da dona).

## 27/10 07h
- Palavrão na passagem do revezamento (KwdN/Dragon: "caralho" na fala do Sirigueijo) apesar do prompt: anime_tts.revezar
  passa viralizador.anti_ban em todas as linhas e nas falas sai/entra. Desfazer: bloco "27/10" em revezar.
- Alimentador preso >2 h (cota do Drive: 1 rclone por pedido, até 10 min cada): cliente._pedidos = 1 lsf -R;
  pedido.json lido 1x (cache); batida no começo de cada volta.

## 27/10 04h
- [GRANDE] Gancho do longo deitado fora do rosto: fonte 46, 2 linhas, faixa translúcida no topo (anime_gancho.py; retrato igual). Prova: quadro antes/depois 5FDt. Desfazer: anime_gancho.py.bak_20261027_gancho_rosto.
- Nomes na legenda dos revezamentos feitos antes do conserto: colab\limpar_nomes.py (delogo) cria *_SEM_NOMES.mp4 sozinho.

## 26/10/2026 22h — 1º longo de revezamento (6d2a, 73,5 min) — júri 4,5 (base 4wuf 5,25)
PROVADO no log/vídeo: 10 vozes clonadas (misto Kokoro+Francisca), passagens da IA, marca d'água limpa (451 quadros),
completo (5 s/frase). Troca aos 7:19 confirmada por Whisper. Júri caiu na retenção (3,0) por causa do NOME do
narrador na legenda — a dona também reprovou.
- [GRANDE] Legenda normal no revezamento (sem nome/cor do narrador). Desfazer: anime_segments (bloco dono_rev).
- [GRANDE] Na troca, narrador PARCEIRO nunca é chamado pelo nome; só PERSONAGEM (personagem.json / tipo personagem).
  Reservas sem nome. anime_tts.eh_personagem/_passagem. Testado: parceiro→parceiro "meu chapa/colega"; Kratos→parceiro.
- Quem entra não reconta o fato da próxima frase (Whisper mostrou a frase repetida 2x).
- [GRANDE] Mascote (garota, canto inf. esquerdo) nos começos de capítulo + CTA no meio (falado). config\longo.json
  "mascote"/"cta.meio"; anime-pipeline._mascote_longo; mascote_overlay.overlay_mascote_deitado. Testado em trecho real.
- Júri por amostra: colab\juri_longo.py (claude-code-video v1.1: movimento medido + 4 verificadores entretenimento).

## 26/10/2026
- [GRANDE] Postagem dos longos só com voz clonada confirmada (render.json voz_clonada + applio_ok) — XNKC ia ao ar com
  Thalita + borrão antigo. Desfazer: tirar `_modelo_novo` de colab\postar_longos.py.
- [GRANDE] Revezamento de narradores contínuo (10 vozes/vídeo, cada bloco no jeito do narrador, passagem escrita pela
  IA, nome/cor na legenda; vídeos de avaliação, não vão pra canal) — anime_tts.revezar, teste_narradores.json.
  Desfazer: continuo=false.
- [GRANDE] Voz igual aos Cortes no Kaggle: base do rodízio (kokoro/francisca/misto), Kokoro na nuvem, venv→virtualenv.
- Trava: vídeo < 1 s por frase vira erro (kaggle_trabalhador + postar_longos).
- Marca d'água do scan removida no original (marca_site.py, inpaint TELEA; caixa grande = tarja INOVARE).
- Trilha: timeout do mix proporcional à duração (fx_music) — longo saía sem música.
- Proxy do edge no pacote do Kaggle; cache de voz (VPS + Drive); limite de pedido novo 6→8 h.
