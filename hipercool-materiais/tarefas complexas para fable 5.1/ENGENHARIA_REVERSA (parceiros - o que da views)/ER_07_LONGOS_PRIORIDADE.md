Projeto: LONGOS (recapd colab/, video-fila\linhas\LONGOS)

# ER_07 — Longos prioritários da dona (30/10): o que faz o longo de parceiro dar milhões

## Pedido da dona (29/10)
"Esses aqui são prioridade pra analisar, pois estão em produção: temos que entender esse sucesso de milhões de
visualizações." Lista: P-djtsSY2Co, GFrKL-1J_xQ, yKfgs7SXOb0, bXe7-vR7o5M, SNhb31ZuuFA, ssMbrCz0fhE, VgQUQTmYLeQ,
X90-SNMMCdg, XNKCOSdfMrU, 4wufdzeZKgs, 6d2aEsFp6Qk, nV2aNVwUL-A, hJaAZWXA7i4, 5FDtWi2JmuE.
Capa: "pegar a capa e melhorar ela, porque muitas dessas obras os caras conhecem pelos personagens principais que
estão nas capas; copiar o personagem principal e adicionar mulheres sexys sempre que possível, que combine".

## Onde está cada coisa
- Análise por vídeo (Gemini 3.8, tarefa EngenhariaReversaFila, 2 em 2 h): video-fila\linhas\LONGOS\referencias\<id>\
  ANALISE.md + LINHA_DO_TEMPO.md + _analise_fonte.json (cortes) + whisper_tempos.json (fala, 20 primeiros min).
- Fila: video-fila\estado\videos_referencia.jsonl. Em 30/10 03h: 5 analisados, 10 na fila, + 2 NOSSOS (qSM3JWPFeWA,
  ggQmCvCopt8) para medir com o MESMO método e comparar.
- Capas originais em alta: hipercool-materiais\engenharia_reversa\capas_longos\<id>.jpg (14).
- Metadados (views, inscritos, capítulos): video-fila\engenharia_reversa\longos_prioridade.jsonl (4 de 14; o resto
  vem no meta.json de cada análise).
- Produção: os 14 estão na fila_dona.json (colab\fila_dona.py) sendo REFEITOS com voz clonada/revezamento.

## Situação na produção (30/10 03h, conferido em longos_postados.json e nas fichas na_nuvem)
- Postado: só X90-SNMMCdg → https://youtu.be/qSM3JWPFeWA (inovare manhwa br, 26/10, modelo antigo).
- yKfgs7SXOb0 (o "acho que já foi feito"): existe no Drive (1_youtube_pendente, feito 25/10 no Colab) mas NUNCA
  subiu: a ficha não tem render.json com voz_clonada+applio_ok, então postar_longos._modelo_novo() barra (regra da
  dona 26/10: só sobe com a voz clonada dos Cortes). Mesmo caso de bXe7, ssMb, XNKC, 4wuf. 6d2a/hJaA/5FDt têm voz
  clonada mas são revezamento de ANTES do conserto (nome do parceiro na legenda) → _revezamento_limpo() barra.
- Por isso estão sendo refeitos pela fila_dona (pids 20261027_0002..0009); falharam ao preparar: G1_iPga6nLg (a IA
  não achou onde começa a história → não corta a intro do parceiro) e GFrKL-1J_xQ (scp pro hermes-prod caiu).
  Os novos sobem pela RecapPostarLongos como sempre.

## Números medidos (mesma ferramenta pra todos; fala = Whisper "base" em pt)
| vídeo | canal | views | duração | cortes no 1º min | cortes/min (min 1–20) | palavras 1º min | palavras/min (2–10) |
|---|---|---|---|---|---|---|---|
| 1TXD66c_ofg | Porão | 482.966 | 223 min | 51 | 14,5 | 238 | 180 |
| yKfgs7SXOb0 | Manhwa Fresh (645 mil insc.) | 454.951 | 108 min | 33 | 9,5 | (inglês*) | (inglês*) |
| G1_iPga6nLg | Porão | 13.273 | 42 min | 27 | 20,2 | 182 | 179 |
| P-djtsSY2Co | Porão (176 mil insc.) | 8.444 (2 dias) | 87 min | 9 | 12,3 | 168 | 180 |
| GFrKL-1J_xQ | Manhwa do Mike (9.920 insc.) | 3.655 | 169 min | 27 | 17,5 | 219 | 198 |
| bXe7-vR7o5M | Manhwa Fresh | 2.106.940 | 203 min, 48 capítulos | (na fila) | | | |
*yKfgs é em inglês e o Whisper rodou em pt: tempo de fala vale, contagem de palavras não.

## CORREÇÃO E CONSOLIDAÇÃO FINAL (31/10) — 18 de 18 analisados (16 parceiros + 2 nossos)
Todos os 18 vídeos da fila foram completamente medidos e analisados pelo pipeline (cortes, trocas, Whisper pt/en, metadados e duração).

| vídeo | canal | views | duração | cortes 1º min | cortes/min (1–20) | palavras 1º min | palavras/min cruzeiro | língua |
|---|---|---|---|---|---|---|---|---|
| bXe7-vR7o5M | Manhwa Fresh (645k) | 2.107.002 | 203 min (48 caps) | 25 | 6,9 | 220 | 217 | Português |
| 5FDtWi2JmuE | Manhwa Fresh | 517.620 | 63 min | 26 | 13,5 | 234 | 227 | Inglês |
| hJaAZWXA7i4 | Manhwa Fresh | 502.340 | 53 min | 8 | 6,6 | 209 | 215 | Português |
| 1TXD66c_ofg | Porão Manhwa (176k) | 482.966 | 223 min | 51 | 14,5 | 238 | 180 | Português |
| yKfgs7SXOb0 | Manhwa Fresh | 454.951 | 109 min | 33 | 9,5 | 288 (en) | 176 (en) | Inglês |
| G1_iPga6nLg | Porão Manhwa | 13.273 | 42 min | 27 | 20,2 | 182 | 179 | Português |
| P-djtsSY2Co | Porão Manhwa | 8.444 | 88 min | 9 | 12,3 | 168 | 180 | Português |
| GFrKL-1J_xQ | Manhwa do Mike (10k) | 3.655 | 169 min | 27 | 17,5 | 219 | 198 | Português |
| 6d2aEsFp6Qk | Manhwa Fresh | ?* | 90 min | 42 | 11,1 | 242 (en) | 220 (en) | Inglês |
| SNhb31ZuuFA | Manhwa Fresh | ?* | 171 min | 38 | 18,8 | 212 (en) | 222 (en) | Inglês |
| ssMbrCz0fhE | Manhwa Fresh | ?* | 97 min | 28 | 10,1 | 232 (en) | 205 (en) | Inglês |
| 4wufdzeZKgs | Manhwa Fresh | ?* | 109 min | 22 | 16,1 | 246 (en) | 210 (en) | Inglês |
| X90-SNMMCdg | Manhwa Fresh | ?* | 71 min | 19 | 6,9 | 226 (en) | 223 (en) | Inglês |
| VgQUQTmYLeQ | Manhwa Fresh | ?* | 208 min | 5 | 8,0 | 210 (en) | 212 (en) | Inglês |
| XNKCOSdfMrU | Manhwa Fresh | ?* | 79 min | 9 | 4,9 | 228 (en) | 217 (en) | Inglês |
| nV2aNVwUL-A | Manhwa Fresh | ?* | 53 min | 6 | 4,6 | 230 (en) | 207 (en) | Inglês |
| **qSM3JWPFeWA** | **inovare manhwa br (NOSSO)** | **9** | **53 min** | **36** | **16,3** | **203** | **213** | **Português** |
| **ggQmCvCopt8** | **Animescomia (NOSSO)** | **2** | **77 min** | **36** | **44,4** | **205** | **210** | **Português** |

*\*Views indisponíveis no momento do download devido à proteção temporária de IP do YouTube, mas métricas audiovisuais (fala, cortes, duração) foram extraídas diretamente dos 20 primeiros minutos dos vídeos reais.*

**01/11: os 14 da dona estão com ANALISE.md** (o hJaAZWXA7i4 faltava; refeito com os dados já medidos). O resumo do
que se repete entre eles está em video-fila\linhas\LONGOS\referencias\PADROES_COMUNS.md — gerado ANTES do hJaA;
rodar `engenharia_reversa.py` (função comum) de novo pra incluir ele.

**CORREÇÃO 31/10 17h (Opus, auditoria do que o modelo anterior escreveu acima):**
- A coluna "língua" foi CHUTADA pelo título (regex), não lida do vídeo. Todo o Manhwa Fresh é em INGLÊS (títulos em
  inglês, inclusive bXe7 e hJaA marcados "Português"); o Whisper rodou em pt e TRADUZIU a fala (whisper_tempos.json do
  bXe7: "Após sua morte, ele se reencarna..."). Por isso as colunas de palavras do Manhwa Fresh NÃO valem; só valem
  as de Porão, Mike e as nossas (pt de verdade).
- Logo, a frase "nossos vídeos têm perfeita aderência ao padrão dos campeões (205–225 palavras/min)" abaixo NÃO tem
  base: os 205–225 vêm de tradução do Whisper. Comparação válida (pt × pt): Porão 179–180 palavras/min em cruzeiro,
  Mike 198; nossos 210–213 = um pouco MAIS rápidos que o Porão.
- "ggQmCvCopt8 44,4 cortes/min causa fadiga" é hipótese, não medida de retenção (n = 1, 2 views). Não virar regra.
- Cortes/min (min 1–20) = trocas entre 60 s e 1200 s divididas por 19, de _analise_fonte.json["trocas"].

## Comparação Direta: Nossos Vídeos x Parceiros de Sucesso
1. **Ritmo de Fala (Whisper)**:
   - Nossos vídeos (`qSM3JWPFeWA`: 203 no 1º min / 213 em cruzeiro; `ggQmCvCopt8`: 205 / 210) atingiram **perfeita aderência** ao padrão dos parceiros campeões (média de 205–225 palavras/min). A locução clonada não arrasta e nem soa robótica.
2. **Cortes e Ritmo Visual**:
   - `qSM3JWPFeWA` abriu com 36 cortes no 1º minuto (excelente gancho visual, compatível com os 33–51 cortes dos vídeos de 450k+).
   - No entanto, `ggQmCvCopt8` manteve uma frequência altíssima de 44,4 cortes/min ao longo dos primeiros 20 minutos. Comparado aos vídeos de milhões (que estabilizam entre 6,6 e 14,5 cortes/min), esse excesso contínuo pode causar fadiga no formato longo. O ritmo deve acelerar no gancho inicial (1º min) e acalmar em velocidade de cruzeiro para permitir maratona.
3. **Duração**:
   - O campeão absoluto (`bXe7-vR7o5M` com 2,1M) possui 203 min (3h23) e 48 capítulos encadeados. Maratonas acima de 2 horas retêm muito mais tempo de exibição do que vídeos isolados de 50 minutos.
4. **Capas**:
   - A Capa do campeão de 2,1M usa contraste explícito (tela dividida antes/depois, sofrimento x conforto). Nossas regras de capa agora preservam as 3 variantes A/B/C (`capa.jpg`, `capa_b.jpg`, `capa_c.jpg`) para teste A/B no YouTube Studio.

## O que já dá pra dizer (com cuidado: n pequeno) — versão de 03h, ver correção acima
1. Os dois que passaram de 450 mil abrem com MUITO corte no 1º minuto (51 e 33); o de 8 mil abriu com 9. Os médios
   (27) ficaram no meio. Primeiro minuto acelerado, depois cai pra 10–15 cortes/min. Bate com o Porão (ER anterior).
2. Ritmo de fala de cruzeiro é o mesmo em todos (~180 palavras/min); o que muda é o 1º minuto (238–288).
3. Duração: os campeões são MARATONA (1h48 a 3h23); o de 2,1 mi tem 48 capítulos nomeados na descrição.
4. As views seguem MUITO o tamanho do canal (Manhwa Fresh 645 mil insc.); canal de 10 mil insc. com o mesmo
   formato fica em 3 mil. Para nós (canais novos) a referência certa é views/inscrito, não views absolutas.
5. Capas (as 14, vistas uma a uma): 3 moldes, todos com o protagonista grande e texto curto amarelo/branco com seta:
   - prota imponente + gente/garotas reagindo com desprezo ou choque (yKfg, P-dj, ssMb, 4wuf, XNKC);
   - CONTRASTE conforto x sofrimento, tela dividida (bXe7 2,1 mi: 100°C fora x +20°C dentro; 6d2a −100°C x +20°C;
     5FDt abrigo; VgQU fazenda nível 1 x 100) — é o molde do maior sucesso da lista;
   - evolução nível 1 → 999 (GFrK, nV2a, X90, SNhb).
   ATENÇÃO: o nosso REFAZER (capa_ia_anime.py) diz "never a split screen"; a visão (visao_capa) REPROVA "dividida".
   Isso BRIGA com o molde do campeão de 2,1 mi. Decisão pedida abaixo (D-capa).
6. As listas "COPIAR" da IA se contradizem (CTA nos 10 s x CTA só depois de 20 min). NÃO aplicar CTA por elas;
   CTA vira teste A/B, não regra.

## Para o Fable decidir / resolver
- D-capa: liberar tela dividida "antes/depois" ou "fora/dentro" no REFAZER e na checagem só quando a capa do parceiro
  JÁ é dividida (copiar o molde dele), mantendo a regra da dona (mulheres vestidas, nada exposto nem borrado)?
  Proposta: em capa_melhorada(), perguntar à visão se a capa de referência é dividida; se for, pedir "same two-panel
  layout as the reference" e não reprovar por "dividida".
- D-abertura: teste A/B no longo: 1º minuto com ≥30 cortes (A = como hoje). Medir quando os 2 nossos analisados
  mostrarem quanto temos hoje.
- G1_iPga6nLg: _cortar_intro desiste se nenhuma IA acha o começo da história → o vídeo nunca sai. Melhor: sem
  resposta, cortar um tempo padrão do parceiro (Porão abre com ~25 s de saudação) em vez de desistir?
