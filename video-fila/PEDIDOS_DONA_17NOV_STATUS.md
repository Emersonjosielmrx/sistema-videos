# Pedidos da dona — conferência de 17/11 (feito / falta)

Conferido por busca no código, com prova (arquivo:linha) em `linhas\LONGOS\LONGOS_MELHORIAS.md`.
✅ feito · 🟡 parcial · ⏳ falta · 🙋 precisa da dona

## Feito hoje (17/11)
- ✅ **Agente de padrões e cruzamento de sucesso** — `analise_sinais_shorts.py` cruza capa, obra, fonte, voz, hora e outros sinais. Divide os Shorts em 2 metades por data: o que ganha nas duas é **RECEITA**, o que ganha só numa é **SORTE**, o que perde nas duas é **EVITAR**. Gera `RECEITAS_DO_SUCESSO.md` todo dia (tarefa FocoShorts).
- ✅ **"Oi" antes do continue** — `D:\sentinela_disparo.py` só manda o continue se o modelo responder ao "oi" pela mesma rota (`SENTINELA_SONDA=0` desliga).
- ✅ **Piadas ocultas** — moldes novos: "eu cairia / eu faria esse acordo", "ela é forte, respeito / prio de tudo", "montanhas" (sem nunca dizer "seios") e "não vai dar pra passar / vocês sabem o que acontece / o YouTube não gosta".
- ✅ **Diminutivos** (felizinha, bravinha…) no roteiro (`ROTEIRO_DIMINUTIVOS=0` desliga).
- ✅ **Chaves "Eu não quero"** — entrou no catálogo de memes com gatilhos ("se recusa", "não quer", "nem pensar"…), mas só toca nos longos.
- ✅ **Shorts repetidos** — 18 casos no histórico (14 em 15/11 04h). Agora tem trava: a mesma pasta não sobe 2x no mesmo canal, e duas rodadas juntas não mandam o mesmo vídeo (`POLITICA_TRAVA_REPETIDO=0` desliga).
- ✅ **Meta de inscritos com prazo** — semanal, ajusta sozinha (sobe se bateu, desce se não). Cartão no topo do painel. Hoje: 2.286 → 3.250 até 24/11.
- ✅ **Erro "32000 output token"** — limite em 64000 pra todos os processos.
- ✅ **"Recap longo com ERRO rc=1"** — o aviso agora diz o motivo de verdade e a conta.
- ✅ **Catálogo de avisos** regerado: `AVISOS_TELEGRAM_CATALOGO.md` (74 tipos, último exemplo de cada). Marque [x] no que quer cortar e me diga "aplica os avisos".
- ✅ **Banimento das chaves do Groq** — investigado e consertado (1 chave = 1 IP fixo).
- ✅ **@izabela.anholett** cadastrada, mas **pausada** até você escolher o canal (ver 🙋).

## Já estava feito
- ✅ @neithkpop, @exploramundofc, @segurancaexplicada, @sabiaquex — adicionados em 08/11 e 15/11.
- ✅ @odaniels00 (4 Shorts feitos) e @nexhwaoficial (7) produzindo.
- ✅ Pose nova de capa (iI52YYpcQAU) — só na capa B dos longos.
- ✅ gauntlet-loop avaliado e reprovado em 15/11 (só prompt).
- ✅ Narradores: os que vão mal saem do rodízio sozinhos; os bons aparecem mais.
- ✅ Trilha DPcqU-UwecY prioritária (peso 3x nos climas tenso e triste).
- ✅ Agente de efeitos e transições (tarefa EngenhariaReversaVisual) — 49 de 51 vídeos dos canais GOJO, Kuroroox, Noctryx e Dr1zzy analisados.

## Falta / parcial
- 🙋 **Trilha do Naruto** — está BLOQUEADA de propósito: foi reivindicada por direitos autorais no vídeo hTYlNKIR3-Y (21/10). Religar arrisca o canal. Decidir.
- ⏳ **Trilha khf9lUFizHE** como 2ª opção — falta separar a música do vídeo (como foi feito com o DPcqU).
- ⏳ **Capas da @ansaketv** — as 12 de exemplo estão baixadas, mas o estilo (2 quadros: antes e quase beijo, com pergunta no meio) ainda não foi aplicado nos Shorts.
- 🟡 **Beijo fake na capa** — as poses fake_* são usadas, mas o casal famoso da obra só sai em 4 obras; nas outras, o casal sai genérico.
- ⏳ **Tela dentro do celular / carro / própria imagem** — é um efeito novo de render; precisa de teste em outra máquina.
- 🟡 **Vídeos UauhQsJK7h4, LSUL0Vp-cLY, CbQG-QFpofA** — ainda não analisados (o yt-dlp está em pausa).
- 🟡 **Voz do sistema e do monstro** — a voz de monstro existe nos longos; a voz do sistema não. Nenhuma foi treinada com trechos específicos (os testes de voz estão pausados).
- ⏳ **Agente buscador de memes** (pesquisa memes virais, inclusive de duplo sentido, e põe em pasta pra você ver) — não existe. Os memes também só entram nos longos, não nos Shorts.
- 🟡 **Painel de tokens + melhorador + sentinela** — o modo gastar/poupar existe (`modo_tokens.py`), mas é regra fixa, não gerenciado pelo Sonnet web.
- 🟡 **Avisos do Telegram** — o bot é único e cada mensagem vira ficha, mas o "deslogado" não é confirmado com teste de login antes de avisar.
- 🟡 **Obra do CgyXHx6h2a8** — a série (vilao_maid) está cadastrada pro InventoReact, mas nenhuma parte foi postada, e falta achar as próximas em canais de fora do Brasil.
- 🟡 **Lista de conteúdos pra pedir autorização** — `FONTES_PARA_AUTORIZAR.md` (268), mas ainda entra coisa que não serve (g1, TNT, Enaldinho).
- ⏳ **Sistema único das máquinas** (o STI ou o desktop assumem como gerente se o PC1 cair) — não existe failover; hoje só avisa quem caiu.

## 🙋 Decisões que são da dona
1. **Prioridade por canal** — a regra de 12/11 ("o melhor faz o máximo, os fracos ficam com as sobras") e a de 16/11 ("30 dias pra todos") se chocam. Hoje vale a de 16/11, e o efeito é este: o **Tech Noturno, que rende 1 view de mediana, tem meta de 150 Shorts** e fica com quase toda a produção extra do Kaggle (8 de 9 Shorts nesta tarde). Proposta: piso de 7 dias pra todos; acima disso, quem rende mais produz primeiro, e canal com mediana < 10 fica só no piso.
2. **Canal de notícias de IA pra @izabela.anholett** — criar um novo ou usar o Tech Noturno (hoje é dorama e rende 1 view). Falta também medir o recorte "só o topo".
3. **Naruto** — religar ou não (risco de direitos autorais).
4. **Limite de 4 Shorts por canal por dia** — aumentar ou não.
5. **6 contas do Kaggle com chave recusada** (emersonjosiel2035, emersonjosiel2037, inovaremanhwaverse2, mundosolar1995, inovare, inovareee) — confirmar se estão banidas.
