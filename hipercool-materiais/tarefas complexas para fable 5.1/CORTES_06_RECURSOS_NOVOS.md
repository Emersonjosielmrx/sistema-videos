# CORTES — 06 — Recursos visuais: o que ampliar

> **Projeto: linha CORTES** — Shorts de canais parceiros (recapd, `D:\recapd-ambientes\producao\bin`; estado em
> `D:\video-fila\linhas\CORTES`). Escrito pela sessão da linha CORTES em 28/10/2026.

## O que já está ligado como teste (28/10, TESTES.md)
- T5 gancho no Remotion (camada transparente sobre o ffmpeg): `D:\claude-code-video\remotion\src\_cortes\gancho\`,
  chamado por `bin\anime_gancho._camada_remotion` (~60-90 s de render, Chrome ~1 GB, só no PC1).
- T6 choque/fogo (porte do `D:\manhwa-react\mr\divider.py`): quadros prontos em
  `D:\hipercool-materiais\assets\cortes_fx\` (gerados por `src\_cortes\fx`), sobrepostos em `bin\fx_subtitles._fx_choque`.
  O estilo glitch travou o render do Remotion e ficou fora.
- T7 mascote (waifu v2) num canto nas pausas da fala: `bin\cortes_mascote.py`, fotos recortadas em
  `D:\hipercool-materiais\mascote_waifu_v2\cosplay_recorte\` + gravações vivas `workspace\assets\mascote_viva\`.

## O que existe e não está sendo usado nos Cortes
- `D:\claude-code-video\remotion\src\lib\` : `vivo.tsx` (personagem recortado se mexendo), `tres.tsx` (3D/2.5D),
  `karaoke.tsx`, `efeitos.tsx`. Telinha de WhatsApp/print animado (citado pela dona como ponto forte do Remotion).
- Ideias levantadas e não feitas: título fixo no topo (02), trechos com voz original (02).

## Para o Fable
1. Dos recursos acima, quais têm maior chance de mover retenção nos primeiros 3 s e no meio do Short? Ordene por
   retorno/custo (o PC1 é o gargalo de CPU — ver 08).
2. A mascote hoje escolhe o canto por "menos gradiente" num quadro. Existe forma barata de saber se ela cobre algo
   IMPORTANTE (rosto, balão, ação)? Detecção de rosto/saliência no lugar do gradiente?
3. Por que o render do glitch trava no Remotion (`src\lib\transicoes.tsx`, estilo 'glitch')?

## Fable — resultado
**29/10 (Fable).** 1. **Ordem por retorno/custo, com o dado do ER_01/CORTES_02:** o que separa os Shorts que saem do
platô não é o que acontece nos 3 primeiros segundos ("continuaram" é igual, 54–57%, nos dois grupos), é assistir o
vídeo INTEIRO (% assistido 72% × 44%) — e isso depende do tamanho (13–24 s) mais do que de efeito. Então: (a) **T8
curto** (já aberto, custo zero de CPU — menos frases = menos render); (b) **loop no final** (já existe, `fechar_loop`;
custo zero) — com Short de 20 s é o que passa de 100% assistido; (c) **título fixo no topo** (a referência de 14 mi
faz; custo baixo: 1 camada ASS, sem Remotion) — T9 depois do T8; (d) T5 gancho Remotion, T6 choque, T7 mascote:
custo alto (Chrome 1 GB, 60–90 s de render no PC1 que é o gargalo) e sem evidência de que movem o 2º lote — manter
os testes abertos só até terem n ≥ 12 elegíveis por braço e decidir pelo placar; não ampliar antes disso. `vivo.tsx`/
`tres.tsx`/telinha de WhatsApp: valem para PRODUTOS (prova de produto) mais do que para Cortes de parceiro, onde a
imagem já é o vídeo da fonte.
2. **Mascote cobrindo algo importante:** sim, barato — o YuNet (OpenCV `FaceDetectorYN`, já usado pela linha
PRODUTOS para "cabeça livre de cartão") roda em ms por quadro: nos 3 quadros do trecho onde a mascote entra, achar
rostos e escolher o canto SEM rosto; empate = menor gradiente como hoje. Balões/texto: `fx_detect` já tem detecção de
texto na fonte (hardsub) — reaproveitar a caixa para excluir o canto. Onde: `bin\cortes_mascote.py` (escolha do
canto). Não implementei: a mascote é T7 e o placar dela ainda não disse se vale a pena existir.
3. **Glitch travando o Remotion:** não medi (precisa reproduzir o render com log do Chrome; o T5 já mostrou que o
Chrome do Remotion cai com RAM < 3 GB — rc 0xC0000409 é falha de memória/stack). Suspeita de graça: o estilo
'glitch' em `transicoes.tsx` desenha por quadro com filtros CSS/canvas que estouram a memória da aba no PC1; testar
com `--concurrency 1` e 720p antes de culpar o código. Fica como pendência de quem mexer no Remotion.
