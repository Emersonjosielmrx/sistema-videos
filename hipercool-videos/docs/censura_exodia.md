# A censura "Exodia" — o que é, e por que o borrão não é opcional

> **16/10, fim do dia — o que vale hoje está em `config/censuras.json`.** O Exodia foi aposentado:
> `censurar_fosco` agora é mosaico colorido do painel inteiro (blocos 55, borrão 45), nível único.
> São dois caminhos, não três: mosaico localizado sempre que há caixas; fosco do painel só quando
> não há localização utilizável. Um terceiro nível mais forte (blocos 90 / borrão 95) foi mostrado
> ao dono e recusado: *"o N3 certeza é quase blur total, não dá pra manter só no anterior?"*.
> Este documento continua valendo como a história do Exodia e das medições.

> Anotado em 16/10/2026, a pedido do dono: *"há um tipo de censura que tinha antes que também era
> muito eficaz, que era a de mudança de cores, espectro, sei lá, era como se fosse um negativo mas
> não era, acho que chamamos de Zeus ou coisa assim, era uma combinação de censuras e era melhor que
> o mosaico. Procure ela mas ainda não aplique, só deixe como uma opção documentada."*

## Achada: chama **Exodia**, não Zeus — e já é o `fosco` de hoje

Está em `bin/censura_visual.censurar_fosco`, com a nota *"Exodia fosco da V8 (aprovado pela
usuária)"*. É mesmo uma **combinação**, e é a que o dono lembra:

| Passo | Filtro | O que faz |
|---|---|---|
| 1 | `negate` | inverte as cores (o "negativo") |
| 2 | `scale=iw/25` + `scale=iw*25:flags=neighbor` | encolhe e amplia sem suavizar: pixelão grosso |
| 3 | `hue=s=0` | tira a cor, vira cinza |
| 4 | `noise=alls=60` | granulado por cima |
| 5 | `drawbox color=white@0.7` | véu branco cobrindo tudo |
| 6 | `GaussianBlur(251)` | **o borrão forte** |
| 7 | `lumakey` + recolagem | traz de volta, NÍTIDOS, os balões e o branco da página |

Ou seja: o "fosco" que parece só um borrão é, por dentro, a tal combinação. O que o olho vê como
borrão é o passo 6 em cima dos cinco anteriores.

## Medido em 16/10 (2ª rodada, com o fluxo COMPLETO)

> A 1ª rodada deste documento concluiu errado, porque eu rodei só o filtro do ffmpeg e pulei a
> etapa em OpenCV. Refiz chamando o caminho inteiro, no painel 100 do cap 3 (o mais explícito da
> obra). O que vale é a tabela abaixo.

| Versão | Resultado |
|---|---|
| Como está hoje (com negativo, borrão 251) | ilegível |
| **SEM o negativo**, borrão 251 | **ilegível também — igual ao de cima** |
| Sem negativo, borrão 81 | a cena já aparece: dá pra ver as pernas |
| Sem negativo, borrão 41 + pixelão grosso | a cena fica bem visível |

**Duas conclusões:**

1. **O negativo não muda o resultado final.** O dono dizia lembrar da combinação *sem* negativo, e a
   medição dá razão a ele: com ou sem, a imagem final é a mesma. Dá pra tirar o `negate` do filtro
   sem perder nada — um passo a menos.
2. **O borrão é quem esconde.** Dos sete passos, é o único que faz o trabalho; os outros mudam
   textura por baixo dele e quase não aparecem no resultado. Abaixo de 81 a cena volta.

**Sobre o `lumakey`:** ele não é o vilão que a 1ª rodada apontou. No filtro ele deixa passar o fundo
tratado onde a imagem é clara, e quem recoloca os balões nítidos é a etapa em OpenCV, depois do
borrão (máscara de balões + componente branco que encosta na borda do painel). No painel 100 essa
recolocação cobre **0%** — ou seja, ali o resultado é 100% fosco mesmo.

## Então o que dá pra fazer, se o borrão incomoda

Nada disso está aplicado — fica como opção, conforme o pedido:

1. **Mexer no lumakey antes do borrão.** Se o passo 7 recolocasse só caixas de texto de verdade (e
   não toda área clara), a combinação poderia viver com um borrão bem mais leve. Precisa de um
   detector de balão melhor que o limiar de luminância — o `fx_parallax.baloes()` já faz algo nessa
   linha e poderia entrar aqui.
2. **Borrão variável pelo score.** Painel de risco baixo com sigma menor, risco alto no sigma de
   hoje. Hoje é sigma fixo para todos.
3. **O enquadramento na parte limpa** (`CENSURA_RECORTE=1`, em `censura_visual`), que mostra arte de
   verdade em vez de cobrir. Está desligado por padrão porque foi testado em 16/10 e os recortes
   saíram COM nudez: a localização só marca a área que o modelo aponta, e o resto do corpo fica
   fora das caixas. Religar só depois que a detecção cobrir o corpo inteiro.

## O que NÃO fazer

Mostrar o conteúdo sem censura por pouco tempo, contando que o detector não pegue. O canal já levou
advertência por nudez em 16/10, e a segunda derruba o canal inteiro.
