# CORTES — 02 — Formato do Short: duração, gancho, ritmo, final

> **Projeto: linha CORTES** — Shorts de canais parceiros (recapd, `D:\recapd-ambientes\producao\bin`; estado em
> `D:\video-fila\linhas\CORTES`). Escrito pela sessão da linha CORTES em 28/10/2026.

## Fatos
- Referência que mais estourou entre os parceiros (13,98 mi): análise quadro a quadro em
  `D:\claude-code-video\referencias\cortes_nerdcf_anya_13mi\` e comparação em
  `D:\video-fila\linhas\CORTES\REFERENCIA_NERDCF.md`. Deles: 28,8 s, 5,6 cortes/10 s, título FIXO no topo o vídeo
  todo, SEM narração (voz original + música), 2 atos que rimam, final com ação pendente.
- Os nossos: 50-75 s, narração clonada do início ao fim, legenda palavra por palavra, gancho só nos 3,2 s iniciais.
  O tamanho sai da fonte: log "Duração do original: 64.8s -> Alvo: 11 linhas" (`anime_auto.py`, procure "Alvo:").
- Roteiro: `bin\anime_script.py` (prompt v12, 1ª pessoa no dorama/filme). Gancho: `bin\anime_gancho.py`.
  Cortes de cena e fuga do escuro: `bin\anime_segments.py` (`_analise_fonte`, `_encostar_na_troca`).

## Onde esta sessão chegou no limite
- Não há retenção por segundo (ver 01), então não sei ONDE as pessoas deslizam nos nossos Shorts. Toda decisão de
  formato foi por gosto da dona + referência, não por curva de retenção.
- Não sei se "narrar tudo" ajuda ou atrapalha em cena cômica/de reação (a referência não narra nada).
- Duração: nunca testei Short curto (~30 s) contra o atual. O alvo de linhas segue a duração da fonte.

## Perguntas para o Fable
1. Qual política de duração por nicho (anime cômico, dorama, filme sem voz, fatos)? Desenhe o teste.
2. Título fixo no topo (como a referência) x gancho que some — candidato a T8. Onde: `anime_gancho.queimar`.
3. Narração parcial: deixar trechos com a voz/som original e narrar só a ponte. O que muda no `anime_script`/
   `anime_segments`/mixagem? (Já existe abertura com trecho real só em pt: `anime_tts._abrir_com_trecho`.)
4. Final: hoje o roteiro termina numa frase; a referência termina na resolução visual. Como forçar isso no roteiro e
   no corte?
5. Use `metricas_studio.json` + `aprendizado_global.json` (top/piores) para achar o padrão dos nossos Shorts que
   mais renderam — esta sessão não fez essa análise.

## Fable — resultado
**29/10 03:25 (Fable 5.1).** Base: `ENGENHARIA_REVERSA\ER_01` (279 Shorts com views de 48 h × tabela do Studio) e
`engenharia_reversa\medidas_nossos.jsonl` (60 dos nossos medidos pelo ffmpeg; só 18 receberam o lote — pouco ainda).
5. **Padrão dos que mais renderam** (feito primeiro, responde o resto): os 5 únicos que passaram do 1º lote (2.071 a
   6.674 views) têm **13–24 s, 64–89% assistido** (o de 6.674 passa de 100% = o público repete), nichos fatos/
   esportes, "continuaram" 57% (igual aos que pararam em 1.200). Os do platô de 1.000–1.500: 50–75 s, 44%
   assistido. Entre os 18 medidos pelo ffmpeg que receberam lote, duração × % assistido = −0,43 e silêncio inicial ×
   % assistido = −0,48 (n pequeno, só direção). Cortes/s e 1º corte não separam nada.
1. **Duração por nicho:** o dado não pede política por nicho, pede uma só — **15–25 s**, porque a porta do 2º lote é
   assistir inteiro. Teste aberto: **T8** (`curto: "ab"` no `cortes_ajustes.json`; B = 4–5 frases; `anime_auto.py`
   ao calcular `target_lines`; postar.json `curto`; placar já conta). Decisão por `pct_media` ≥ 65% e ≥500 views,
   ≥ 6 por braço por canal; detalhes em TESTES.md. Manhwa/dorama: antes de testar formato, resolver a
   elegibilidade (ER_01/ER_04) — nesses canais o feed nem mostra.
2. **Título fixo no topo × gancho que some:** sem dado nosso (título de parceiro não separa alto de baixo, 35 mil
   Shorts). Candidato a T9 só depois do T8 fechar, para não cruzar dois fatores de duração/tela com n pequeno.
3. **Narração parcial:** a referência não narra; os nossos 5 melhores narram do início ao fim e mesmo assim passaram.
   Então narrar não é o que barra — o tamanho é. Deixar para depois do T8; se o curto vencer, o passo natural é
   "voz original nos 2 s do gancho + narração" (já existe `anime_tts._abrir_com_trecho` em pt).
4. **Final:** o loop já existe (`PARCEIRO_LOOP=1`, `anime_script.fechar_loop` troca a última frase pelo gancho de
   retorno) e é sempre ligado — não é teste, então não dá para medir. Proposta: virar T9 "loop × CTA" só quando o
   T8 fechar; com Short de 20 s o loop é o que faz o % assistido passar de 100%.
