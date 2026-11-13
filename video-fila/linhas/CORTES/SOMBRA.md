
# 27/10 06:28 — agy/gemini-3.8-flash-high (lote sem-obra-5f43a1_cap1_20261026, sem-obra-324029_cap1_20261026_vi, sem-obra-c853c4_cap1_20261026, sem-obra-110e14_cap1_20261027)
- diagnóstico: O lote apresentou fala truncada e inacabada no encerramento em todos os 4 Shorts avaliados (q18 em sem-obra-5f43a1, sem-obra-324029_vi, sem-obra-c853c4 e sem-obra-110e14). Além disso, identificou-se inserção indevida de tarja branca opaca no centro da tela sobre rostos e ações sem legenda da fonte subjacente (sem-obra-c853c4 q04/q08/q16 e sem-obra-110e14 q08/q14). Por fim, títulos entregando spoiler do desfecho no primeiro quadro anularam a retenção em 2 Shorts (sem-obra-c853c4 q01 e sem-obra-110e14 q01).

## 27/10 06:28 [agy/gemini-3.8-flash-high] APLICARIA regras_titulo: [] -> ['Nunca dê spoiler do clímax ou do desfecho no título; crie curiosidade e tensão provocativa sem antecipar o resultado da narrativa.']
- porque: Spoilers prematuros do clímax e do final ocorreram no título inicial em sem-obra-c853c4 (q01.jpg) e sem-obra-110e14 (q01.jpg), prejudicando a retenção.
- veredito da sessão Claude: (preencher: concordo / discordo e por quê)

## 27/10 06:28 PROPOSTA [CERTEZA] Corrigir truncamento de áudio e fala cortada no final do Short (agy/gemini-3.8-flash-high)
- prova: Ocorrência grave repetida em 100% do lote no q18.jpg: sem-obra-5f43a1 ('porque...'), sem-obra-324029_vi ('vào lúc...'), sem-obra-c853c4 ('como...') e sem-obra-110e14 ('fera pra').
- onde: anime_montar.py / anime_auto.py (renderização final de áudio e vídeo com ffmpeg)
- como testar: Renderizar Short de teste e verificar via ffprobe se a duração do vídeo estende-se por 0.2s a 0.5s após o encerramento do último fonema da locução.

## 27/10 06:28 PROPOSTA [CERTEZA] Impedir tarja branca no centro da tela sobre a ação sem legenda da fonte (agy/gemini-3.8-flash-high)
- prova: sem-obra-c853c4 (q04, q08, q16) e sem-obra-110e14 (q08, q14) aplicaram tarja opaca no centro cobrindo atletas, rostos e tela de status sem haver legenda original.
- onde: parceiro_marca.py (_posicionar_tarja / _caixa_justa) e anime_hardsub_detect.py
- como testar: Processar os vídeos do lote confirmando que tarjas e delogo só são gerados sob detecção positiva de texto queimado e confinados à área de legenda.

## 27/10 06:28 PROPOSTA [CERTEZA] Ajustar posição da marca d'água e @ do canal para não cobrir rostos ou legendas (agy/gemini-3.8-flash-high)
- prova: sem-obra-5f43a1 (q03: @ centralizado sobre os olhos/rosto), sem-obra-324029_vi (q01: @ sobre a legenda da fonte) e sem-obra-110e14 (q18: colisão de @ com legenda da narração).
- onde: parceiro_marca.py (função de estampagem da marca d'água / @)
- como testar: Renderizar amostras verificando se o @ é fixado em zona segura fora da área de legendas (y=1350-1580) e sem colidir com caixas de rostos detectadas.

### AVALIAÇÃO DA SESSÃO CLAUDE (27/10 07:10) — volta 1 do Gemini 3.8 high
- regras_titulo "nunca spoiler do clímax/desfecho": CONCORDO (o júri do claude-code-video achou o mesmo; regra segura).
- PROPOSTA "fala truncada no fim em 100%": DISCORDO — é o LOOP do Short ("quer saber...", "porque..."); estava nas
  LIÇÕES e no PROMPT e ele repetiu o falso positivo. -> reforçar no prompt: "NÃO proponha nada sobre o fim em gancho".
- PROPOSTA "tarja sem legenda": METADE CERTA — o Short dos ovos (oi9Rg, 19:00) teve visão "sem legenda" e os pixels
  criaram tarja (falso positivo REAL, corrigido 07:05: veredito da visão manda). Nos de esporte/brinquedos a visão leu
  legenda de verdade (o júri não vê o que está debaixo da tarja) — ali era falso positivo do júri.
- PROPOSTA "@ do canal em cima de rosto": CONCORDO (já estava no ESTADO, frente 5).
- Placar: 2 certas, 1 meio certa, 1 errada (repetiu erro avisado). Útil como ACHADOR de defeitos; NÃO confiável para
  aplicar sozinho ainda (ignorou lição explícita).

# 27/10 10:20 — BANCADA (mesmo pedido, lote c853c4/110e14/8a49d5/777e60; nada aplicado) — notas da sessão Claude 0-10
Gabarito: código = botão INSCREVA-SE em cima de rostos (8a49d5), texto do topo colidindo com o da fonte, tela final
parada 2 s; alavanca = no máx. 1 regra de título (ortografia/sem spoiler). Errado: "fim cortado" (lição), @ no rosto e
tarja sem legenda (já corrigidos hoje 07:10/07:30). Defeito de TODOS: regra de layout ("não sobrepor") no regras_titulo,
que só vai pro prompt do título — não muda posição de nada; só a parte "ortografia" serve.
| modelo | s | nota | por quê |
| gemini-4-argon (puro) | 122 | 7,0 | INSCREVA-SE nos rostos (certo, preciso) + typo SOCOMANDO; não leu código |
| argon-flash | 356 | 6,5 | igual ao Gemini 3.8 + nomes de arquivo reais; repetiu @ (já feito) |
| agy/gemini-3.8-flash-high | 327 | 6,5 | idem argon-flash (o Argon quase não mudou nada) |
| argon-pro | 31 | 5,5 | tarja sem legenda (real, já feito) + typo; regra de título na alavanca de roteiro |
| argon-opus | 115 | 5,0 | só tarja/rosto (já feito); caminho inventado pipeline/renderer.py |
| argon-kiro | 36 | 4,5 | idem + caminho inventado pipeline/composicao.py |
| argon-gemini | 509 | — | falhou: Argon "Todas as contas estão bloqueadas" (7 em paralelo esgotaram) |

# 27/10 11:00 — BANCADA DE CRIAÇÃO (roteiro com tempo + título do mesmo Short: zapc2YyZp0Y lobos, filme 1ª pessoa)
Notas da sessão Claude 0-10 (roteiro: fiel à legenda, 1ª pessoa, fluido; título: regra sem spoiler do final + palavras buscadas)
| modelo | roteiro s/nota | título s/nota | vídeo (60/40) |
| gemini-4-argon | 195/8,0 | 156/5,0 (entrega o final: LOBOS enfrentam a BATALHA) | 6,8 |
| argon-opus | 97/8,0 | 96/5,5 ("descobriu proteção" truncado) | 7,0 |
| argon-pro (Kiro) | 48/8,0 | 23/5,0 (entrega o final: encara TIGRE com matilha) | 6,8 |
| argon-kiro (Kiro) | 17/7,5 | 151/7,0 | 7,3 |
| agy/gemini-3.8-flash-high | 6/7,0 ("sem vergonha", "pai biológico" inventado) | 8/7,5 | 7,2 |
| argon-flash | 6/6,5 (= Flash; "Olha isso." solto) | 8/7,5 | 6,9 |
| argon-gemini | 162/6,0 ("bicho desviver meu pai" errado) | 191/4,0 ("VINGANÇA do tigre" falso) | 5,2 |
Kiro acabou 27/10 ~10:50: argon-kiro/argon-pro sem nova rodada. Arquivos: bancada\criacao_20261027\.

# 29/10 14:35 — gemini-4-argon (lote sem-obra-907307_cap1_20261028, sem-obra-f4a685_cap1_20261028, sem-obra-16de72_cap1_20261028, sem-obra-d9bb92_cap1_20261029)
- diagnóstico: Dois problemas se repetem em >= 2 Shorts do lote: (1) a legenda dinâmica (karaokê) ultrapassa o limite inferior da zona segura y=1580, sendo coberta pela interface do Reels/TikTok em sem-obra-907307_cap1_20261028 (q01 a q18, faixa y=1630–1730) e sem-obra-d9bb92_cap1_20261029 (q01 em y=1620–1640 e q13 com quebra de linha chegando a y=1670–1680); (2) inserção de trechos excessivamente escuros/subexpostos e com queda drástica de ritmo na subida para o clímax em 3 dos 4 Shorts: sem-obra-907307_cap1_20261028 (q16, fenda escura em 28.08s), sem-obra-f4a685_cap1_20261028 (q16, estádio escuro sob tempestade sem ação) e sem-obra-16de72_cap1_20261028 (q13 e q17, quadros em breu/sombras quase sem contraste). Além disso, o título de topo e elementos superiores invadem a zona acima de y=150 ou colidem com marca d'água/rosto em sem-obra-907307 (q01, y=80–140), sem-obra-f4a685 (q01/q02) e sem-obra-d9bb92 (q01, y=40).

## 29/10 14:35 PROPOSTA [CERTEZA] Subir âncora vertical da legenda karaokê e limitar quebra de linha para respeitar zona segura (y <= 1500) (gemini-4-argon)
- prova: sem-obra-907307_cap1_20261028 (q01 a q18 com legenda entre y=1630 e y=1730) e sem-obra-d9bb92_cap1_20261029 (q01 em y=1620–1640 e q13 com 2ª linha em y=1670–1680), invadindo a interface inferior do Reels/Shorts.
- onde: Módulo de renderização de legendas ASS/Remotion (posicionamento vertical marginV / y-anchor da legenda karaokê)
- como testar: Renderizar novamente sem-obra-d9bb92_cap1_20261029 e sem-obra-907307_cap1_20261028 e extrair folha de quadros verificando que a base da última linha de legenda permanece entre y=1250 e y=1500 (nunca abaixo de y=1580).

## 29/10 14:35 PROPOSTA [CERTEZA] Filtrar tomadas subexpostas (luma médio baixo) na seleção de cenas e travar topo do título em y >= 160 (gemini-4-argon)
- prova: Trechos escuros/quase pretos quebrando a retenção em 3 Shorts: sem-obra-907307_cap1_20261028 (q16), sem-obra-f4a685_cap1_20261028 (q16) e sem-obra-16de72_cap1_20261028 (q13, q17); e invasão da faixa superior (y < 150) em sem-obra-907307 (q01, y=80–140) e sem-obra-d9bb92 (q01, y=40).
- onde: Seletor de cenas/cortes de vídeo (filtro de brilho/luma mínimo por tomada) e layout do gancho superior (y_min=160)
- como testar: Medir luma médio (Y) dos segmentos candidatos descartando ou clareando trechos com Y < 35 antes da montagem, e validar no frame de 1,5s (folha_topo.py) que nenhum texto de gancho inicia acima de y=160.

# 29/10 15:45 — gemini-4-argon (lote sem-obra-907307_cap1_20261028, sem-obra-f4a685_cap1_20261028, sem-obra-16de72_cap1_20261028, sem-obra-d9bb92_cap1_20261029)
- diagnóstico: Padrão 1 (legibilidade/zona segura inferior e superior): nos Shorts sem-obra-907307_cap1_20261028 (q01–q18, y=1630–1730; topo em y=80–140), sem-obra-f4a685_cap1_20261028 (q18, y~1800 e q02 título sobre o rosto) e sem-obra-d9bb92_cap1_20261029 (q01 e q13, legenda atingindo y=1620–1680 e card do topo em y=40), elementos de legenda e sobreposições invadem as áreas da interface nativa (abaixo de y=1580 e acima de y=150). Padrão 2 (movimento/exposição e sincronia visual): nos Shorts sem-obra-907307_cap1_20261028 (q10/q11 estático com 15.7% de movimento e q16 escuro), sem-obra-f4a685_cap1_20261028 (q09 contradição visual e q16 escuro/sem ação) e sem-obra-16de72_cap1_20261028 (q01 desfocado, q13 e q17 quase em breu), há seleção de takes subexpostos, estáticos ou em contradição com a locução.

## 29/10 15:45 [gemini-4-argon] APLICARIA regras_roteiro: [] -> ['Proibido usar bordões de personagens, saudações de abertura ou frases desconexas do tema; inicie a primeira frase direto na ação ou conflito central da cena.']
- porque: Em sem-obra-f4a685_cap1_20261028 (q01.jpg, história 3.5), o roteiro iniciou com o bordão 'Pelos poderes de Bright Moon, meus rebeldes' em um vídeo sobre futebol.
- veredito da sessão Claude: (preencher: concordo / discordo e por quê)

## 29/10 15:45 PROPOSTA [CERTEZA] Travar posicionamento vertical da legenda karaokê e do gancho superior dentro da zona segura (y=150 a y=1580) (gemini-4-argon)
- prova: Em sem-obra-907307_cap1_20261028 (q01 a q18: legenda em y=1630-1730 e título em y=80-140) e sem-obra-d9bb92_cap1_20261029 (q01 e q13: legenda descendo até y=1620-1680 na segunda linha), o texto invade a interface inferior e superior do Shorts/Reels.
- onde: Módulo de renderização de legenda/ASS ou template Remotion (cálculo de marginV / y-anchor da legenda e do título de topo)
- como testar: Renderizar sem-obra-907307_cap1_20261028 e sem-obra-d9bb92_cap1_20261029 com duas linhas de legenda e medir o bounding box em q01 e q13 garantindo topo >= 150px e base <= 1580px.

## 29/10 15:45 PROPOSTA [CERTEZA] Filtro de luminância mínima e movimento na seleção de cortes (rejeitar takes escuros/subexpostos e estáticos) (gemini-4-argon)
- prova: Takes quase em breu ou estáticos quebraram a retenção em 3 Shorts do lote: sem-obra-907307_cap1_20261028 (q11 com 15.7% de movimento e q16 escuro), sem-obra-f4a685_cap1_20261028 (q16 escuro/tempestade sem ação) e sem-obra-16de72_cap1_20261028 (q01 desfocado/escuro, q13 e q17 em breu).
- onde: Seletor de cenas / extração de cortes de vídeo (validação de brilho médio Y e fluxo óptico por tomada)
- como testar: Rodar o seletor nos vídeos-fonte de sem-obra-16de72_cap1_20261028 e sem-obra-907307_cap1_20261028 exigindo luminância média mínima e movimento > 20% em tomadas > 2s, verificando a substituição dos trechos q13/q17 e q11/q16.

# 29/10 16:54 — gemini-4-argon (lote sem-obra-907307_cap1_20261028, sem-obra-f4a685_cap1_20261028, sem-obra-16de72_cap1_20261028, sem-obra-d9bb92_cap1_20261029)
- diagnóstico: Dois defeitos de posicionamento na zona segura se repetem em 2 ou mais Shorts do lote: (1) a legenda dinâmica (karaokê) cai abaixo do limite de y=1580, sendo encoberta pela interface do Reels/Shorts em sem-obra-907307_cap1_20261028 (q01 a q18, entre y=1630 e y=1730) e sem-obra-d9bb92_cap1_20261029 (q01 e q13, atingindo y=1620 a y=1680); (2) elementos de topo e títulos de gancho invadem a zona acima de y=150 ou colidem com a marca d'água (@) e rostos em sem-obra-907307_cap1_20261028 (q01/q02, y=80 a y=140), sem-obra-d9bb92_cap1_20261029 (q01, y=40) e sem-obra-f4a685_cap1_20261028 (q01/q02 sobre o @assistiainvestimentos e o rosto do Rivaldo). Além disso, trechos escuros/subexpostos sem ação quebram o ritmo e a retenção em 3 Shorts: sem-obra-907307_cap1_20261028 (q16), sem-obra-f4a685_cap1_20261028 (q16) e sem-obra-16de72_cap1_20261028 (q01, q13, q17).

## 29/10 16:54 PROPOSTA [CERTEZA] Travar âncora vertical da legenda dinâmica (karaokê) e do título/card superior dentro da zona segura (y=160 a y=1500) (gemini-4-argon)
- prova: Legenda invadindo a interface inferior (abaixo de y=1580) em sem-obra-907307_cap1_20261028 (q01-q18, y=1630-1730) e sem-obra-d9bb92_cap1_20261029 (q01/q13, y=1620-1680); elementos e títulos no topo invadindo y<150 ou colidindo com @/rostos em sem-obra-907307_cap1_20261028 (q01/q02, y=80-140), sem-obra-d9bb92_cap1_20261029 (q01, y=40) e sem-obra-f4a685_cap1_20261028 (q01/q02).
- onde: Renderizador de legendas/ASS ou componente Remotion de overlay de texto e gancho superior na pipeline da linha CORTES
- como testar: Renderizar novamente sem-obra-907307_cap1_20261028 e sem-obra-d9bb92_cap1_20261029 e verificar nos quadros extraídos se o baseline da segunda linha da legenda fica estritamente <= y=1500 e o topo do gancho/card >= y=160 sem sobrepor o @.

## 29/10 16:54 PROPOSTA [CERTEZA] Filtro de luminância mínima e movimento na seleção de cortes para descartar takes subexpostos ou em breu (gemini-4-argon)
- prova: Quedas severas de iluminação e takes quase pretos apontados como defeito grave/médio em 3 Shorts do lote: sem-obra-907307_cap1_20261028 (q16), sem-obra-f4a685_cap1_20261028 (q16) e sem-obra-16de72_cap1_20261028 (q01, q13, q17).
- onde: Seletor de cenas / extrator de tomadas de vídeo da linha CORTES
- como testar: Medir luminância média (Y) dos segmentos candidatos e rejeitar ou aplicar correção de gamma em trechos com Y médio abaixo do limiar antes de montar o corte; validar nos quadros q13 e q17 de sem-obra-16de72_cap1_20261028.
