# 06 — Mascote viva (a "dona do canal")
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

**Objetivo da dona:** parecer uma mulher real dona do canal — a morena brasileira (cabelo castanho dourado), estilo
biquíni/cosplay sensual sem nudez, que ENTRA andando na tela em paisagem, anda por vários pontos e faz poses enquanto
fala os pedidos de inscrição/comentário; amigas (loira, indígena) aparecem menos e interagem.

**Onde olhar**
- Produção contínua: `D:\video-fila\linhas\LONGOS\mascote_producao.py` (tarefa MascoteProducao 8:30/14:30/20:30),
  imagens `bench\gerar_waifu2.py` (Flow, ref `mascote_waifu_opcoes\05_morena_brasileira_4.png`), vídeo
  `bench\veo_mascote.py --entra` (1º quadro 16:9 com ela na borda), recorte `bench\mascote_recorte.py`.
- Arsenal: `D:\hipercool-materiais\assets\mascote_viva\` (+ `producao.json`). Fotos: `mascote_waifu_v2\andando` (definitivas).
- No longo: `D:\recapd-ambientes\producao\bin\mascote_overlay.py` (`gravacao_viva`, `amiga_viva`, `_paisagem` = tela
  cheia) chamado por `anime-pipeline._mascote_longo`.

**Problemas abertos (meu limite):**
1. **Voz × boca:** o Veo grava a fala com a voz DELE e boca sincronizada; no longo usamos a voz CLONADA da narração e
   o som do Veo é descartado → a boca mexe com outras palavras. Ideia: passar o áudio do Veo pelo RVC (clone) mantendo
   o tempo (a sincronia fica), ou gerar a fala do Veo a partir do nosso texto exato de CTA.
2. **Recorte:** sem IA (o rembg estourou a RAM do PC1): apaga só o branco ligado à borda → sobram pontinhos brancos
   presos entre mechas do cabelo. Melhor: matting de verdade (BiRefNet/RMBG) rodando no Kaggle com GPU.
3. **Veo:** recusa/erros de automação (ver frente 08); biquíni passou na política no 1º teste.
4. A mascote de tela cheia pode cobrir a legenda/tarja do longo — falta regra de posição.

**Como medir:** retenção no segundo em que ela aparece (frente 01); comentários/inscritos depois do CTA dela.

## Fable — resultado
**29/10 (Fable).** 1. **Voz × boca:** a saída que mantém a sincronia é a que você mesmo apontou — passar o ÁUDIO do
Veo pelo RVC (`voz_clonada.py` converte wav mantendo duração/quadros; é o que ele faz com a base Edge), não a
narração clonada por cima. Para a boca falar o CTA certo, o texto do pedido ao Veo tem de ser o CTA exato (a fala do
Veo vira a base; o clone só troca o timbre). Custo: 1 RVC por gravação (segundos, no PC2 onde o clone já roda).
2. **Recorte:** no Kaggle com GPU (BiRefNet/RMBG-2) é o certo e já há sessão de Kaggle para o longo; no PC1, o
`rembg` com `u2netp` (modelo pequeno) a 512 px nos ~10 quadros-chave e máscara propagada por fluxo ótico cabe na RAM
— mas é trabalho de bancada, não medi. Os pontinhos brancos entre mechas somem com 1 passada de `morphologyEx`
(abertura 3 px) + feather na máscara atual — correção de 5 linhas em `mascote_recorte.py`, sem IA.
3. **Posição × legenda:** regra simples — a mascote de tela cheia só nos trechos em que `roteiro_tempos` não tem
fala (pausas) ou com a legenda deslocada para o lado oposto (`SUB_Y_*` já é variável); o `qa_video` (D10) pode
acusar sobreposição quando a mascote gravar sua caixa num json.
4. **Prioridade pela régua da dona (views):** nenhum dado ainda diz que a mascote segura audiência (T7 nos Cortes
sem n; longos sem curva). Antes de refinar recorte e amigas, medir 10 longos com × sem mascote por `pct_media`/
`dur_media` (lote do Studio) — se não mover, a energia vai para o T8/elegibilidade, que mexe em 60% dos vídeos.

**29/10 tarde (sessão LONGOS):** voz — feito de outro jeito: o CTA virou PAUSA com a voz do próprio Veo (cena em loop borrada atrás, legenda = texto do sidecar), `anime_segments._falas_mascote` + `mascote_overlay.montar_pausa`; RVC no áudio do Veo NÃO feito. Recorte — pontinhos entre mechas resolvidos sem IA em `mascote_recorte.py` (mancha branca fechada 150–4000 px com anel < 80 de cinza = fundo; medido: mechas 56–69, dentes 91). Medir com × sem mascote: NÃO feito.
