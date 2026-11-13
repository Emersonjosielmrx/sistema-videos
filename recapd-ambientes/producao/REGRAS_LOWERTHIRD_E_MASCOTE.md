# 📋 REGRAS DE USO — Lower-third e Mascote (aprovados c/ ressalvas) — 2026-06-30

> Usuária aprovou lower-third (#1) e mascote (#4) das categorias novas, MAS com ressalvas
> CRÍTICAS que precisam estar implementadas antes de ligar no pipeline. Documentado aqui pra não perder.

## ✅ LOWER-THIRD (faixa de nome/cargo do personagem) — fx_lowerthird.mov
Aprovado. É o que "aponta"/apresenta o personagem. Regras OBRIGATÓRIAS:

### Regra 1 — VERIFICAR o nome (não inventar)
- O nome exibido TEM que ser o nome real do personagem, vindo do `persona` da locução
  (narration_cache → locucoes[].persona). NUNCA usar "Personagem" genérico nem chutar.
- Se a persona for "Narrador"/"Narradora" → NÃO mostrar lower-third (narrador não é personagem em cena).
- Conferência: só disparar quando persona é um nome próprio real (não narrador, não vazio).

### Regra 2 — NÃO REPETIR (uma apresentação por personagem por vídeo)
- Cada personagem só recebe lower-third UMA vez no vídeo — na PRIMEIRA vez que ele aparece/fala.
- Manter um set `personagens_ja_apresentados` durante a geração. Se já está no set, NÃO repete.
- Por quê: apresentar o mesmo personagem 3x no mesmo vídeo é amador e poluído.
- IMPLEMENTAÇÃO: no loop de clips do hiper-pipeline, na 1ª locução de cada persona nova,
  marcar pra disparar lower-third com {nome: persona, papel: opcional}. Demais ocorrências: pular.

## ✅ MASCOTE — precisa SER UMA GAROTA (garota-propaganda do canal), NÃO um emoji
A amostra fx_mascot.mov usa um emoji 🐱 — REPROVADO esse formato. O que a usuária quer:
- Uma **GAROTA mascote**, estilo a **mascote da Crunchyroll (Hime)** — a "garota-propaganda"
  do canal, que aparece de vez em quando fazendo algum movimento/reação.
- NÃO é comentário real, NÃO é texto de comentário. É a personagem-mascote fazendo uma
  pose/gesto/reação no canto da tela.

### Como fazer (honestidade técnica)
- Desenhar uma garota anime convincente em CSS puro NÃO fica bom (vira boneco tosco).
- O CAMINHO CERTO: precisa de um **ASSET de imagem** da mascote — idealmente um PNG com fundo
  transparente da garota-propaganda do canal (ou um sprite-sheet com 2-3 poses).
  - Opção A: usuária/designer fornece o PNG da mascote do canal.
  - Opção B: gerar a mascote por IA de imagem (ex: Pollinations/SD) — uma garota anime fixa,
    mesma identidade visual sempre, fundo transparente, 3-4 poses (acenando, surpresa, apontando, joinha).
  - Depois o efeito HyperFrames anima esse PNG (entra deslizando, faz um balanço, sai) — igual
    fx_mascot mas com a imagem da garota no lugar do emoji.
- DEFINIR COM A USUÁRIA: ela tem um PNG da mascote do canal? Ou quer que eu gere uma identidade
  de mascote por IA? Sem o asset da garota, o efeito fica só como placeholder (emoji).

### Regra de uso da mascote (quando existir)
- Aparece com PARCIMÔNIA: 1-2x por vídeo no máximo (é tempero, não enche). Por cadência, não por cena.
- Poses variadas pra não repetir a mesma animação.

## Status
- fx_lowerthird.mov: pronto, mas as Regras 1 e 2 são de INTEGRAÇÃO no hiper-pipeline (ainda não feito).
  Hoje está registrado no elemental_transitions como efeito manual. NÃO ligar em auto sem as 2 regras.
- fx_mascot.mov: placeholder com emoji. AGUARDA decisão da usuária sobre o asset da garota-mascote.
- As outras 3 categorias novas (frame, bignumber, timeskip): aguardando avaliação da usuária.
