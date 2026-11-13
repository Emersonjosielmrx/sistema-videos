# Variante "recap de ANIME" (dona, 02/11/2026)

> "Esses longos devem ser uma variante, porque o estilo de vídeo deles é diferente, até de capa, título, tags. Não são
> recaps de manhwa e sim de animes mesmo; têm vantagens e exigências diferentes. Tem mais potencial do que os que
> estamos fazendo, mas tem coisas pra estudar: a quantidade de views dos vídeos originais, e muitos vídeos são de
> capítulos/episódios, não de obras completas."

Parceiros de referência: @MattzRecaps, @NoteLeyZerandoAnimes, @DuduzivelAnimeRecap.
1º vídeo da variante: https://youtu.be/fQTiy7CVMxA

## O que já se sabe (conferido em 02/11)
fQTiy7CVMxA (Mattz - Animes Recap): "UM MLK SEM AMIGOS, FEIO, SEM DINHEIRO SEM QUERER SE TORNA NAMORADO DA + POPULAR
(1-12) Anime Recap" — 1h57 (7056 s), 24.117 views, 07/07/2026. Anime: comédia romântica (Maki Maehara / Umi Asanagi).
Temporada inteira (episódios 1 a 12), CAPÍTULOS POR EPISÓDIO na descrição (00:00 Ep 1, 09:12 Ep 2...).
Título: provocação em MAIÚSCULAS sobre o protagonista + "(1-12)" + "Anime Recap", SEM o nome do anime no título.
Descrição: 1 frase de sinopse com os nomes dos personagens, chamada pro canal, capítulos por episódio, bloco "TAG:" com
o nome do anime em várias formas + #anime. Sem legenda do YouTube (só automática).

## Configuração
- config\longo.json por_tipo["anime_recap"] (ANIME_VARIANTE=anime_recap; espelho ligado como o anime).

## Estudo dos 3 canais (CONFERIDO 02/11 ~12h: yt-dlp --flat-playlist, 60 vídeos de cada, D:\tmp_logs\anime_recap\canais.json)
| Canal | Mediana views | Mediana duração | Melhor |
|---|---|---|---|
| NoteLey - Zerando Animes | 42.000 | 68 min | 1,5 mi (88 min) "BULLIED BOY gains 300 LEVELS using a HACK..." |
| Mattz - Animes Recap | 10.500 | 48 min | 479 mil (112 min) "Ele Nasceu Amaldiçoado Com 100 Esposas (S2 - 12)" |
| DuduziVEL | 2.500 (só 3 vídeos) | 15 min | 3.700 (48 min) |

O QUE OS NÚMEROS MOSTRAM:
1. DURAÇÃO: os que mais vendem são temporada INTEIRA de 60-135 min; os piores de todos têm 9-26 min (episódio
   solto / parte). -> a variante faz SEMPRE temporada completa (1 cour = 12 eps) num vídeo só; nunca episódio solto.
2. TÍTULO: premissa do protagonista em 1 frase, com 3-6 PALAVRAS EM MAIÚSCULAS no meio (NoteLey: "Caçador FRAQUINHO
   recebe um sistema para ser o ÚNICO que pode subir de NÍVEL"), sem o nome do anime; no fim "- ANIME RECAP" e, no
   Mattz, a contagem de episódios "(12)" / "(S2 - 12)" / "(COMPLETO)". Mistura PT e EN (os em inglês também vão bem:
   canal recebe público de fora). Nossa tríade "humilhado -> virada" encaixa (BULLIED BOY / WEAKEST / Bebê ABANDONADO).
3. OBRA: isekai/sistema/subir de nível e comédia romântica escolar dominam o topo. Escolher pela fonte com mais views.
4. Descrição (fQTiy7CVMxA): sinopse de 1 frase com os NOMES dos personagens + capítulos POR EPISÓDIO (00:00 Ep 1...) +
   bloco de tags com o nome do anime em várias formas. (No título NÃO vai o nome; nas tags/descrição VAI.)
5. Content ID (inferência do nicho, não conferido): áudio original do anime mudo (só narração + trilha livre), nada da
   abertura/encerramento (OP/ED), cena contínua <= 3-5 s. O nosso pipeline já: muda o áudio da fonte, espelha (anime),
   corta por frase (~4-6 s) com zoom/movimento.

## Regras da variante (aplicadas no 1º vídeo, fQTiy7CVMxA)
- Fonte = temporada inteira do parceiro; o vídeo sai inteiro (sem cortar em partes).
- Título: premissa + MAIÚSCULAS + "(1-12) - ANIME RECAP" (ou "(COMPLETO)"); sem nome da obra.
- Capítulos POR EPISÓDIO quando a fonte tiver (os da descrição da fonte, reescalados pro nosso tempo).
- Tags/descrição: nome do anime em várias formas (é busca ativa no anime, diferente do manhwa).

## 02/11 noite — 1º vídeo (fQTiy7CVMxA) e ajuste de duração
- Feito no Kaggle em 3h47 (GPU: Whisper 266 s, legenda em 4 fatias 4543 s). Prévia aprovada; postado público no
  Manhwa Noturno (CartuchoReact sem cota; Animescomia pede "verificação única" pra capa personalizada).
- Saiu com **71 min de 118 (60%)** — manhwa fica 92-113% do original. Causa: a IA escreveu 873 frases pra alvo 1058
  e a frase de anime dura ~4,9 s (manhwa ~5,7 s).
- Conserto (só na variante, `pedido.json` tipo `anime_recap`): `anime_preparo_longo.py` usa 5,0 s/frase no alvo (em vez
  de 6,6) e `anime_script.rewrite_longo_com_tempo` pede "NO MÍNIMO N frases" e refaz 1x o bloco com menos de 80%.
  Meta: recap de anime com ~100-115 min para um original de 2 h.
