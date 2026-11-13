# O que a pesquisa de notebooks (04/11/2026) ensinou sobre a OLX

A pesquisa listou 9.870 anúncios de notebook com entrega até R$ 1.000 e abriu ~1.000 deles.

| # | Achado | Número | O que mudou no sistema |
|---|---|---|---|
| 1 | O filtro de RAM que o vendedor marca erra | 12 de 49 (25%) divergem da descrição. "32 GB/64 GB" muitas vezes é o disco | A RAM só vale pela descrição, pelo título ou pelas **fotos**. O filtro serve só de pista para escolher a ordem de abrir |
| 2 | A maioria nem diz a RAM | 475 de 711 (67%) não dizem em lugar nenhum do texto | **Leitura das fotos** (tela do sistema, BIOS, etiqueta) por Gemini. Se as fotos também não mostram, o robô pergunta ao vendedor |
| 3 | O carregador quase nunca é citado | 58% não informam; 25% dizem que vem SEM | "sem carregador" = descarta. Não informado = pergunta ao vendedor. Carregador visível na foto conta como "tem" |
| 4 | "Funciona?" muitas vezes fica sem resposta | 43% incerto, 34% não funciona, só 23% dizem que funciona | O incerto avisa com ⚠️ e vai para a pergunta ao vendedor |
| 5 | A condição "Com defeito ou avarias" não serve para cortar | 61 dos marcados assim funcionam (tela quebrada, tecla, bateria) | Não usar o filtro de condição da OLX para excluir. A IA lê o defeito |
| 6 | **Preço isca** | O 1º do ranking (R$ 100) era um anúncio de mudança: o MacBook custava R$ 2.000 e os R$ 100 eram da cama | A IA extrai o `preco_real` da descrição. As fotos marcam "fotos de outros itens". Preço real acima do teto = descarta |
| 7 | Até R$ 300, quase tudo é peça | Títulos "p/ peças", "retirar peças", "para reparo" e "carcaça" dominam a faixa barata | Corte por título (regex) antes da IA, e depois triagem da IA |
| 8 | A triagem em lote falhava | 71 lotes falharam porque a resposta da IA vinha cortada (max_tokens 800) | Triagem com max_tokens 4000 e lotes de 60. Falhou = mantém o lote e tenta 2× |
| 9 | A OLX devolve 502 às vezes | 1 em ~100 páginas | `_get` tenta 3× com espera |
| 10 | A OLX tem filtros de atributo | RAM `nme` (7=1GB, 2=2GB, 4=4GB, 6=8GB, 1=16GB, 3=32GB, 5=64GB); processador `nmo`; entrega `opst=2`; menor preço `sp=1` | Para ir direto nos fortes, use a URL com `nme=6` ou `nme=1` e deixe a IA conferir |
| 11 | A listagem para em 100 páginas (5.000 anúncios) | — | Passou disso, recomeçar com `ps=<último preço>` |
| 12 | Na pesquisa, contar achados duvidosos encerra cedo | A 1ª rodada parou em R$ 250 achando que já tinha 16 GB (eram falsos) | Contar só os **confirmados** (funciona + RAM no texto ou nas fotos) |

## Pesquisa de consoles e acessórios (04/11/2026, `pesquisa_mercado.py` e `pesquisa_acessorios.py`)
| # | Achado | O que fazer |
|---|---|---|
| 13 | PS3 "destravado" custa o mesmo que o travado (mediana R$ 750 nos dois). E destravar é grátis (HEN/CFW até o 4.93) | Não pagar a mais por "destravado". Com HEN, leitor quebrado não importa. Bluetooth/Wi-Fi queimado = não comprar |
| 14 | PS5: só 9 de 405 anúncios dizem o firmware, e as fotos quase nunca mostram (1 em 60, e era 14.00) | **Perguntar ao vendedor** a versão (Informações do Console) antes de comprar. Desbloqueável até 13.60 |
| 15 | PS5 barato com **foto de propaganda / print de outro anúncio** | Sinal de golpe: a verificação de fotos marca isso em `obs` |
| 16 | O Mercado Livre bloqueia o curl (challenge) e a API pública dá 403 | Usar o Chrome da OLX (`olx_chat.navegador`). O ML já mostra o frete para Paragominas (CEP do perfil) |
| 17 | Chrome fora da tela "dorme": screenshot e render travavam | Flags `--disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-background-timer-throttling` |
| 18 | Categorias OLX | consoles: `/games/consoles-de-video-game`; acessórios: `/games/acessorios-de-video-game`; HD/SSD: `/informatica`. Filtros de console: `gcbd` (marca), `cdvgm` (modelo), `gcfs` (características) |

## Frete (dona 04/11: "todos têm frete, até o frete grátis")
| # | Achado | O que fazer |
|---|---|---|
| 19 | API de frete da OLX: `POST apigw.olx.com.br/delivery/quote` com `{"zipCode","listId","searchCategoryLevelZero/One/Two","weight"}`. Funciona com curl_cffi, sem login. O peso está em `ad.olxDelivery.weight` | `olx_buscas.frete()` cota todo anúncio aberto para o CEP da dona (68625016, Paragominas-PA) |
| 20 | **"Frete grátis" sai pago no Norte**: 19 anúncios assim deram R$ 41,83 de frete em média (R$ 28–77). Os sem frete grátis deram R$ 37,40 | Teto e ranking sempre pelo **TOTAL = preço (ou preço real) + frete real**. O aviso mostra "preço + frete = total" |
| 21 | Os rankings da pesquisa de notebooks (04/11) usaram só o preço do anúncio | Daqui para frente, `*_ranking_frete.json` e o alerta usam o total |

## IA (dona 04/11)
- Texto (triagem, julgamento, assistente, chat): **`sonnet-fila` (Sonnet 5.5 web) → `gemini/gemini-4-argon` (reserva) → `gemini-fila`**. Fica em `modelos_texto` no config.json.
- Fotos: `gemini-fila`, porque o Sonnet web não enxerga imagem direto. Lotes de 12 imagens derrubavam o OmniRoute; usar até 4–6 por pedido.

## Robô / infra
- A tarefa agendada ignora o início se sobrou um `wscript` da execução anterior. A trava `rodando.pid` agora confere se o PID é mesmo um python, porque o Windows reaproveita PIDs.
- Para reiniciar: matar o PID de `estado\rodando.pid` e rodar `Start-ScheduledTask BuscasOLX`. Se não subir, conferir `wscript` órfão.
