# Globo Solar | Energia Global (@globosolarenergiag, Concórdia do Pará)

Cliente desde 31/10/2026. Bio: Av. Deodoro da Fonseca 695, Pinheiro, Concórdia do Pará; "Financiamos e parcelamos";
WhatsApp (91) 99394-9409 (wa.me/5591993949409). Conta profissional, ~870 seguidores. Login à mão pela dona no cofre
`ig_globosolarenergiag` (porta 9803); cookies NSN `cofre_ig_globosolarenergiag.json`.

**Marca** (medida no avatar e nos Reels dela, não no palpite): ardósia #1A222D + laranja-avermelhado #EA3A21, logo
3D "GLOBO SOLAR" (no carrossel vai em texto: GLOBO branco / SOLAR laranja). O amarelo do Setembro Amarelo é campanha,
não marca. As artes antigas dela têm tabela de preço e "até 90%": NÃO reaproveitar sem a dona confirmar.

**Pasta do Drive**: https://drive.google.com/drive/folders/1dYM8scGjqmDwUe3MFW7or6v1qQhhdvWW (edição pública;
entrada / usados / fotos_base). Vigia: tarefa `EmpresasPastas_Vigia` (30 em 30 min, `bin\vigia_pasta_empresas.py`)
avisa no Telegram arquivo novo em entrada/ ou fotos_base/ (Globo e Advance).

## O que roda
| Tarefa | Horário | Script |
|---|---|---|
| GloboSolar_Carrossel | 10:50 / 17:40 | `bin\carrossel_globo.py` (visual do carrossel_advance com a marca da Globo; fotos da biblioteca geral aprovadas) |
| GloboSolar_Reel | 09:20 / 13:20 / 20:30 | `bin\reel_globo.py` (clone do dono, clone, foto real de obra) |
Travas iguais às da Advance, com arquivos próprios: 90 min entre posts (`cache\historico_carrosseis_globo.json` +
`videos\reels_globo`), pausa de 18 h no "spam" (`cache\globo_pausa.json`).

## Clone do dono
Fotos-base em `assets\globo\clone_bases`: a foto que a dona mandou (dono de camisa verde, cinturão) + 5 quadros dos
Reels dele, achados por `bin\coletar_rosto_globo.py` (YuNet+SFace contra a foto da dona, cosseno >= 0,50) e
conferidos a olho. Camisa preta no pedido do Flow. Clone que não passa no revisor de rosto não posta.

## Formatos dos Reels do clone (31/10, vale para Globo, Advance e MS)
- **Estilos** (`roteiro_ms.ESTILOS`): pergunta, criativo (lugar inusitado: rede na beira do rio, barquinho, barraca de
  açaí, campinho, praia de rio, feira, cozinha — citado na fala), dica, mito ou verdade, chamada direta. Escolha por
  conta no placar `insta_estilos` (Thompson: o que rende sai mais, o que não tem dado é testado; nunca 3x seguidas).
- **2-3 cenas** (`bin\cenas_veo.py`): a fala é dividida por frase e cada uma vira um clipe Veo do clone num ambiente
  (escritório, em cima dos painéis, garagem do cliente com o inversor, casa, comércio ou os inusitados); cada cena passa
  na trava; uma falhou = clipe único. 1 crédito do Veo por cena. `MS_MULTICENA=0` desliga.
- **Balão/gancho fora do rosto** (`montagem_ms.rosto_faixa`): acha o rosto e põe o texto onde ele não está.
- **Placar** (`bin\placar_estilos.py`, 1x/dia pelo vigia das pastas): cada Reel com 48 h contra a mediana da PRÓPRIA
  conta (views peso 2, curtidas 1, comentários 1) -> estilo, nº de cenas e formato. Segunda-feira: resumo no Telegram.
- **Legenda** (01/11, `montagem_ms._png_cinetica`): TODOS os Reels com legenda de ADESIVOS, como a abertura do longo
  (`hipercool-materiais\teste_legenda_abertura\abertura_v3_legenda_falada.mp4`): palavra por palavra, cada uma com
  fonte (Luckiest Guy/Bangers/Impact/Montserrat Black), cor em degradê, contorno grosso + brilho, giro e LUGAR
  diferente na tela; curtas pequenas em cima noutra cor; "pulo" ao entrar; nunca no rosto nem no topo ocupado pelo
  balão/faixa. `MS_LEGENDA=karaoke` volta à antiga. Remontar Reel pronto sem Veo: `_diag\remontar_reel.py <marca> <stem>`.
- **Layout** (01/11, `escolher_layout`): `normal` ou `aula` (faixa de título fixa na cor da marca + etiqueta
  1 O problema / 2 Como funciona / 3 O resultado, como o vídeo de produto da Inovare). Placar `<conta>:layout`.
  `MS_LAYOUT` força. Teste sem Veo: `_diag\teste_cinetica.py <stem> karaoke|cinetica`.
- **Animação Remotion** (01/11): as 3 solares entraram no `D:\claude-code-video` (mesmo motor dos vídeos de produto:
  telas/cartões flutuando, recorte do dono, só imagens, texto cinético). O pronto cai como `ccv_*.mp4` na pasta de
  Reels da empresa (`tipo_video: animacao`) e entra no placar de formato. Ver CLAUDE.md de lá.
- **Uma ensina a outra**: `roteiro_ms.escolher_estilo` soma o placar da conta (peso 1) com o das outras 2 solares
  (peso 0,5). Estilos (31/10): pergunta, criativo, dica, mito, chamada, mini-história, antes e depois, erro comum.
  Material de uma empresa NUNCA vai para a outra (só o aprendizado do que rende).

1º carrossel: https://www.instagram.com/p/DfKugP-GuL2/ (31/10 14:44, pauta financiamento).
