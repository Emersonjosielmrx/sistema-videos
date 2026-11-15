# Instagram — estratégia (14/11/2026)

Pedido da dona: "Instagram: veja qual a melhor estratégia e faça".

## Diagnóstico (números de 14/11)
- 35 contas postando até 5-8 Reels/dia cada, por automação e proxy, com o mesmo vídeo dos Shorts e a mesma legenda.
- Resultado: sintetizerisada 844 posts = 12 seguidores; fakenews.ia4 782 = 10; _lucrocomia_ 134 = 7; iapro.mentoria 788 = 6;
  futebolcom.ia2 683 = 5; as outras 0. Ou seja: o volume não traz nada — alcance cortado (filtro anti-spam).
- Pesquisa (Gemini Pro, com fontes de 2026): conta nova postando em volume sem interação humana cai no filtro de
  automação e de "conteúdo não original"; o ponto ótimo é 1 Reel/dia (no máximo 2) e é melhor concentrar em 3-5 contas.
  Fontes: viral.app (estudo com 32 mil contas), proxies.sx (guia antiautomação 2026), tubefilter (penalidade de
  conteúdo reaproveitado, 30/04/2026), Buffer (melhores horários, 12/11/2026).

## O que foi feito
- `config/instagram_foco.json`: só as 5 contas com seguidores postam, no máximo 2 Reels/dia e com pelo menos 4 h entre
  eles. As outras 30 ficam PARADAS (nada foi apagado). Desligar: env `INSTA_FOCO=0` ou apagar o arquivo.
- Código: `bin/postar_insta_auto.py` (bloco "14/11 ... foco").

## Próximos passos (a fazer)
1. Hashtags: no máximo 5, específicas do nicho (o Instagram limitou a 5 em 2026).
2. Gancho no 1º quadro: texto na tela já no início (a capa de IA dos Shorts entra como 1º quadro — `capar_shorts.py`).
3. Variar o horário (+/- 30 min) e postar entre 18 h e 23 h.
4. Contas com mais de 700 posts e 0 seguidores: a pesquisa recomenda abandonar ou recomeçar com conta nova aquecida
   (5-7 dias só navegando antes do 1º Reel). Decisão da dona.
5. Medir em 7 dias (InstagramMedirSeguidores, 07:40): se as 5 não crescerem, recomeçar 3 contas novas com aquecimento.
