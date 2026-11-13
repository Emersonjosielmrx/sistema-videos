# Vídeos longos: quanto cada melhoria acrescenta no TEMPO DE GERAÇÃO (atualizada 28/10 17h)

**Como ler:** o tempo é o de **gerar** o vídeo, não a duração do vídeo. Conta feita para o **pior caso: só processador
(CPU), sem GPU**, numa máquina de 4 núcleos (Kaggle sem GPU, VPS ou PC). Base: hoje um longo de **75 min leva ~4,4 h**
pra gerar (medido nos últimos 15 longos: ~210 s de geração por minuto de vídeo). A % é sobre essas 4,4 h.
Os efeitos de imagem foram medidos em trechos reais (tempo de processador do ffmpeg; `bench\bench_efeitos.py`).

## Feitos (código pronto e já no pacote do Kaggle desde 28/10 17h)
| # | O quê | + horas (longo de 75 min) | + % |
|---|---|---|---|
| 1 | Resumo de abertura (frases + imagem de cada momento, sem contar o final) | +0,04 h | +1% |
| 2 | Mascote falando os pedidos de inscrição (voz CLONADA por cima, nunca edge puro) | ~0 | ~0% |
| 3 | Câmera forte (zoom e sobe/desce dentro da imagem) | ~0 | ~0% |
| 4 | Sons de ação (espada, golpe, quebra, corrida, tiro...): frases com som 16% → 40% | ~0 | ~0% |
| 5 | Falas reais de séries (Chaves, Chris, Faustão, Bob Esponja) numa brecha | +0,01 h | ~0% |
| 6 | Falas de personagem com voz clonada (como o Mike), ~1 a cada 2 min | ~+0,5 h só CPU | ~+11% |
| 7 | Memes abrindo brecha no resumo | ~0 | ~0% |
| 8 | Glitch de cor só nas frases de golpe | +0,03 h | +0,7% |
| 9 | Balanço da câmera nas lutas, **com leve rotação** | +0,17 h | +3,8% |
| 10 | Partículas (faísca, velocidade, chuva, pétalas) nas cenas que combinam | +0,13 h | +3% |
| 11 | Transições de fogo, água, raio, rasgar (1 a cada ~8 cortes) | +0,14 h | +3,2% |
| 12 | Tremida leve em todo trecho | +0,06 h | +1,3% |
| 13 | Corte na troca de cena (Hypit) | +0,19 h | +4,3% |
| 14 | Narradores: os mais atrativos primeiro, 1ª troca cedo e depois cada vez mais espaçadas; Patrick Estrela fora | ~0 | ~0% |
| 15 | Legenda agrupada por sentido (Hypit) | ~0 | ~0% |
| 16 | Brilho (bloom) **5x menos**: só nos trechos de luz/fogo/magia/golpe, no máx. 1 a cada 5 | ~+0,2 h | ~+4% |
| 17 | Paralaxe 2.5D de verdade **só nos momentos-chave** (resumo de abertura + 1 em 5 golpes, ~20 trechos; medido 23 s/trecho) | ~+0,13 h | ~+3% |
| | **Total dos feitos** | **~+1,6 h** (4,4 h → ~6 h só CPU) | **~+35%** |

28/10 17h: o glitch de cor estava entrando nos trechos normais em vez dos golpes (erro meu) — corrigido.

Ainda **não saiu nenhum longo com tudo isso**: as 4 GPUs do Kaggle estão sem cota da semana. O primeiro longo
completo sai quando a cota voltar, e aí confiro o vídeo de verdade.

## Pendentes
| O quê | Situação |
|---|---|
| Baixar do YouTube em H.264 (−0,19 h, −4%) | você aprovou; falta mexer na opção do yt-dlp |
| Campo no painel :8790 pra você mandar vídeo bom que viu (avisa no Telegram e entra na fila de análise) | a fazer |
| Engenharia reversa de um vídeo do Porão que estourou (análise + linha do tempo) | a fazer |
| Falas de séries: 16 cortadas de 21 | faltam 5 |
| Mascote: opções de cabelo/olhos (8) | saíram A, B, D; gerando C, E, F, G, H |
| Mascote: 10 cosplays sensuais (estilo capa, sem homem) | saiu a dama medieval; as outras 9 vêm depois das cores |
| Mascote falando no Veo 3 (fundo branco → recorte nas laterais) | 1ª tentativa baixou vídeo de outro robô (separado em `_errados`); gerando de novo |
| "Virar anime" (interpolar quadros) | só abertura/clímax; ainda não feito |
| Melhorador automático | pronto, mas DESLIGADO até você dar o sinal |

## Você ainda escolhe (todo trecho = caro)
| O quê | O que é | + horas | + % |
|---|---|---|---|
| Cor de cinema + vinheta + grão | deixa a imagem com "cara de filme": cores mais quentes/contrastadas, bordas escurecidas e um chuvisco leve | +0,63 h | +14% |


Dá pra fazer igual ao brilho e à paralaxe: só em 1 a cada 5 trechos, ~1/5 do custo (~+3%).

## Não compensa (medido)
- Converter o vídeo de AV1 pra H.264 depois de baixar: custa mais do que economiza.
- Bloom/paralaxe/rotação em todo trecho somados: +18% a +40% cada.
- As transições do jeito que o hipercool aplica hoje (recodifica o vídeo inteiro ~17 vezes num longo).
