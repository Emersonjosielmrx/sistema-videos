# Formatos de vídeo longo — o que rende e o que testar

Pedido da dona (13/11 23h): "foca nos mais vistos do YouTube; analise outros conteúdos longos que possamos fazer, iguais ao
recap de anime/manhwa, mas que sejam ainda melhores, se existirem; liste e documente".

## 1. O que os NOSSOS dados dizem (views/dia por tema, 86 longos medidos, 14/11 00h)

| Tema | Vídeos | Média views/dia | Melhor | Leitura |
|---|---:|---:|---:|---|
| **Ex / dinheiro / vingança** (ex pediu volta, ganhou bilhões, gold digger) | 3 | **112** | 323 | **7x o Medieval** — amostra pequena, mas a diferença é enorme |
| Isekai de tecnologia (Medieval Age) | 9 | 15 | 85 | bom e estável, série dá recorrência |
| Fraco humilhado vira o mais forte | 30 | 9 | 100 | o "padrão" — rende pouco na média |
| Reencarnação / regressão | 14 | 3,5 | 31 | fraco |
| Outros | 30 | 1,8 | 21 | não vale |

**Conclusão:** o melhor "formato novo" já está dentro do nosso nicho: **manhwa/manhua de dinheiro + ex humilhada +
vingança**. É o que o InventoReact mostrou (HomhRlIE72I, 547 views em ~1,7 dia). A lista de prioridade
(`recapd-ambientes\producao\config\fontes_prioridade.json`) já está ordenada por views e os 10 primeiros são desse tema.

## 2. Formatos parecidos (mesma máquina: vídeo longo em inglês -> narração PT-BR + legenda + edição)

A pesquisa na web (Gemini Pro e Argon, 13/11) **recusou responder** — os números de audiência/RPM abaixo NÃO foram
verificados; a coluna "Nota" é avaliação minha pelo encaixe na nossa produção. Precisa de teste real (1 vídeo cada) antes
de virar linha.

| Formato | Encaixe na máquina | Risco de direitos / "conteúdo reaproveitado" | Nota | Por quê |
|---|---|---|---:|---|
| **Manhua / donghua chinês de dinheiro e vingança** (mesmo enredo, fonte chinesa) | igual ao que já fazemos | igual ao manhwa | 9 | é o tema campeão com fonte nova e muito volume |
| **Micro-drama chinês compilado** ("short drama": CEO, casamento por contrato, vingança da esposa) | precisa narrar por cima das falas reais | ALTO (Content ID das produtoras) | 6 | o tema é o mesmo do campeão, mas a fonte é filmada e as produtoras reivindicam |
| **Histórias de "Reddit" / vingança narradas** (AITA, ex traidora) | fácil: texto -> narração + imagens geradas | baixo (história própria) | 7 | mesmo gatilho de ex/vingança, sem depender de parceiro; precisa de imagem (Flow) |
| **Recap de dorama / k-drama** | igual | médio-alto (emissoras reivindicam clipes) | 5 | público BR grande, mas Content ID frequente |
| **Filme/série explicado** | igual | alto (Content ID de estúdio) | 4 | concorrência enorme e reivindicação |
| **Terror / creepypasta narrada** | fácil (texto + imagem) | baixo | 5 | público fiel, mas outro nicho e outra voz |
| **Lore de games / anime por temporada** | igual | médio | 4 | público menor no BR |

## 3. O que fazer agora (proposta)

1. **Foco total no tema campeão** (ex/dinheiro/vingança) — já está na frente da fila do Kaggle.
2. **Testar 1 manhua chinês do mesmo tema** (fonte nova, risco igual ao que já fazemos) — maior chance de repetir os 112 v/dia.
3. **Testar 1 "história de vingança narrada"** com imagens do Flow — se render, não depende de parceiro nem de Content ID.
4. Medir pelos views/dia na tabela "Longos que mais rendem" do relatório da ronda (ela já mostra views/dia).

Itens 2 e 3 esperam a dona dizer "pode testar".
