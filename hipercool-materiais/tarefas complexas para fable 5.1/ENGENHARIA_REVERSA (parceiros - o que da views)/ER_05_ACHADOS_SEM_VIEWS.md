# ER_05 — O aprendizado gera sugestões que ninguém liga a views

## Fato (29/10)
`D:\video-fila\aprendizado.py` (roda a cada 30 min pelo VigiaVideos) pega o source.mp4 que o Cortes já baixou e
pergunta a 2 modelos o que o parceiro faz que nós não fazemos. Placar:
- claude-sonnet: 307 candidatos, 160 pendentes, 10 aplicados, 154 descartados
- gemini: 257 candidatos, 58 pendentes, 13 aplicados, 247 descartados
`aprendizado\PARA_IMPLEMENTAR.md`: 564 grupos candidatos, quase todos "visto em 1 vídeo", nota 9–10 dada pelo
próprio modelo. Exemplos do topo: corte 3D de lareira, texto derretendo com tracking, legenda verde neon trackeada.
Nenhum tem as views do vídeo do parceiro de onde saiu, nem do canal dele.

## O problema
A nota é "parece bom", não "dá views". Um achado de um vídeo de 300 views vale o mesmo que de um de 3 milhões.
E muitos são de edição manual (tracking 3D) que o pipeline automático não faz.

## O que esta sessão vai fazer (mecânico)
Montar `D:\video-fila\engenharia_reversa\` com: lista leve (`--flat-playlist` pela ytdlp_vez) dos Shorts de cada
parceiro com views públicas; medidas por vídeo do que o Cortes já baixou (duração, cortes/s, gancho 2 s, legenda,
voz, texto na tela); e a comparação 10% de cima x 10% de baixo do MESMO canal.

## Tarefa para o Fable (o que é difícil)
1. Desenhar como pesar cada achado pelas views do vídeo de origem relativas à mediana do canal dele, e cortar o
   que só aparece em vídeo fraco.
2. Separar o que o pipeline automático consegue fazer do que é edição manual — e o que virou código em qual
   projeto (`D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md`, só Edit).
3. Mudar o prompt do estudo para pedir comparação ENTRE um vídeo alto e um baixo do mesmo parceiro (em vez de
   "o que ele faz que nós não"), sem Opus nos pipelines.

## Fable — resultado
**29/10 04:10 — desenho (sem mexer no `aprendizado.py` ainda: é a sessão de ER que o roda; aplicar quando ela quiser).**
1. **Peso de cada achado = evidência de que ele acompanha views no MESMO canal do parceiro.** Para o vídeo de origem
   `v` do parceiro `p`: `r = log2(views_v / mediana_p)` (mediana dos Shorts de `p` na lista guardada do Cortes,
   `titulos_parceiros.json` já tem). Um achado visto em `n` vídeos recebe `peso = Σ r` (não a média): visto em 1
   vídeo de 300 views num canal de mediana 50 mil → r ≈ −7 → peso negativo → cai; visto em 3 vídeos top do canal →
   r ≈ +3 cada → +9. Corte: descartar `peso < 0` ou `n = 1 e r < 1`; "candidato" só com `peso ≥ 2` e `n ≥ 2`. A nota
   9–10 do próprio modelo entra só como desempate. Isso elimina a maioria dos 564 sem ninguém ler.
2. **Separar "o pipeline faz" de "edição manual":** marcar cada achado com uma de 3 classes no próprio JSON do
   estudo: `pipeline` (ritmo de corte, duração, legenda, título fixo, som, zoom/pan, cor — tudo que ffmpeg/ASS/
   Remotion-kit fazem), `kit` (precisa de um efeito novo mas genérico: rasgo, glitch, tracking simples), `manual`
   (3D, tracking de rosto, motion design feito à mão). Só `pipeline` e `kit` entram no PARA_IMPLEMENTAR; `manual`
   vai para uma lista "referência" que não gera tarefa. Pedir a classe ao modelo no mesmo prompt custa 0.
   O que virou código fica no `MELHORIAS_PARA_TODOS_OS_PROJETOS.md` (só Edit) — a marcação `aplicado` do
   `aprendizado.py marcar` já existe; ligar o id do achado ao item do doc.
3. **Prompt do estudo: comparar ALTO × BAIXO do mesmo parceiro**, nunca "o que ele faz que nós não". Entrada: 2
   vídeos do mesmo canal (1 do top 10%, 1 do fundo 10% — `amostra.py` já baixa assim), mesmas medidas do `medir.py`
   (cortes/s, 1º corte, silêncio inicial, volume). Pergunta: "o que o alto tem que o baixo não tem, e vice-versa; só
   diferenças que um pipeline automático reproduz; responda com a medida (ex.: 1º corte em 0,8 s × 3,1 s)". Modelo:
   Argon → Gemini 3.8 (regra da casa; sem Opus). Importante pelo ER_01: filtrar os vídeos do parceiro que NÃO
   receberam lote (views < 5% da mediana do canal) antes de escolher o "baixo" — senão compara-se com vídeo que
   ninguém viu, e a "diferença" é ruído.
4. **O que já se sabe que dá views nos nossos (ER_01/02):** 15–25 s e assistir inteiro. Qualquer achado que
   alongue o Short (narrar tudo, mais frases, mais cenas) deve receber peso negativo por padrão.
