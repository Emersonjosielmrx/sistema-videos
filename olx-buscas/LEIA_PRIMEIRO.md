# Buscas na OLX com aviso no Telegram (criado 04/11/2026)

## Regras da dona (fixas no código)
1. Só anúncio **com Entrega**, Brasil inteiro. Usa o filtro `opst=2` na URL e confere `olxDelivery` dentro do anúncio.
2. Ordem **do menor preço** (`sp=1`) até o **teto** (`max`) de cada busca. Passou do teto, para de ler.
3. Abre cada anúncio novo e lê a descrição. A IA (`gemini-fila` no OmniRoute 157, chave em recapd secrets\omniroute.json) julga:
   - se é o produto mesmo, e não capa, caixa, cabo, troca ou outro modelo;
   - o estado: funciona, defeito, sucata ou incerto;
   - se atende os requisitos da busca (`precisa`), como carregador ou GB;
   - o que vem junto e as pegadinhas.
   Avisa só se é o produto, funciona e atende os requisitos. "incerto" também avisa, com ⚠️. Defeito só avisa se a busca tiver `defeito`.
4. Anúncio já julgado não passa de novo pela IA. Se um anúncio aprovado baixar de preço, avisa de novo com "BAIXOU de R$ X".

## Peças
- Bot próprio: @olx_agent_emerson_bot (config.json). Só aceita comandos do chat_id da dona. Mensagem de outro chat fica registrada no log.
- Tarefa `BuscasOLX`: roda no logon e a cada 10 min, oculta (rodar_oculto.vbs → iniciar.bat → pythonw). O PID fica em `estado\rodando.pid`, e se já estiver rodando ela sai.
- A OLX bloqueia o curl comum (Cloudflare 403). Tem que usar curl_cffi `impersonate="chrome"`.
  - A **lista** de anúncios vem do stream RSC (`self.__next_f.push`), no bloco `{"ads":[...]}`.
  - O **anúncio** vem de `<script id="initial-data" data-json=...>`, no campo `ad.body`.
- `buscas.json` guarda as buscas. `estado\vistos.json` guarda o veredito por listId. `estado\olx.log` é o log.

## Comandos (Telegram ou `python olx_buscas.py comando "..."`)
- `/add iphone 8 | max 350 | precisa 64GB ou mais | sem plus` (opções: max obrigatório, min, precisa, sem, defeito, nome)
- `/add <link OLX com categoria> | max 150`
- `/lista`, `/del N`, `/pausar N`, `/ligar N`, `/agora`
- Teste sem avisar: `python olx_buscas.py testar "iphone 8" 350 "64GB ou mais"`

## Triagem e velocidade
- Antes de abrir os anúncios, uma chamada à IA julga os títulos da página inteira (`triagem`). Corta jogo, controle avulso, caixa, aluguel etc.
- Depois abre e julga 3 anúncios por vez.
- Medido no PS4 até R$ 450: 187 cortados pelo título, 13 abertos, 11 eram o produto de verdade.

## Assistente no Telegram (Sonnet web, `cw/claude-sonnet-5-5`)
- Texto livre no bot, sem "/", vai para `assistente()`. Ele devolve ações e aplica: regra_add/del, teto, minimo, sem_add, nova_busca, pausar/ligar/apagar, rodar_agora.
- Se a dona **responder um aviso**, a busca é a daquele aviso (`estado\avisos.json` liga message_id → busca/anúncio).
- As regras são uma lista por busca e podem **afrouxar** o padrão. Exemplo: "aceita controle quebrado se o console funcionar".
- "sem" corta pelo título sem ler o anúncio. O prompt proíbe inventar palavras como controle/carregador/tela. Erro visto em 04/11: o Sonnet tinha posto "controle" na busca de PS4.
- O histórico da conversa fica em `estado\conversa.json`.

## Chat com vendedores (`olx_chat.py`). A dona autorizou em 04/11: o robô manda sozinho, sem confirmação.
- Usa o Chrome perfil `D:\hipercool-materiais\perfis_chrome\olx`, porta CDP 9788, com a conta da dona logada.
  - Se o Chrome não está aberto, abre fora da tela e fecha no fim. Fecha com `Browser.close`; o `b.close()` só desconecta.
  - O login sobrevive ao fechar (testado). Os cookies também estão copiados em `estado\cookies_olx.json`.
- Anúncio aprovado entra em `estado\fila_chat.json`. A cada 10 min o `ciclo()` faz duas coisas:
  1. Lê as conversas abertas pelo robô. Se o vendedor respondeu, o Sonnet resume e dá um veredito (comprar/negociando/descartar). Responde ou faz contraproposta e manda tudo para o Telegram.
  2. Manda as 1ªs mensagens da fila, no estilo da dona (ex.: "Ate quanto faz ?").
- Abre a conversa direto por `chat.olx.com.br/?list-id=<id>`. O campo de texto tem placeholder "Responder <nome>".
- Para ler as bolhas: `div[class*='group/bubble']`. Avô com `items-end` = a dona; `items-start` = o vendedor. O DOM vem do mais novo para o mais velho.
- Limites (config.json): `chat_max_dia` 20, `chat_max_por_conversa` 4, `chat_intervalo_s` 180. Conversa sem resposta há 3 dias = "sem resposta".
- **Conversa que a dona já tinha com aquele anúncio NÃO é tocada** (status "da dona").
- Nunca fecha compra. Nunca passa telefone, Pix ou endereço (`_limpa` apaga números). Nunca negocia fora da OLX.
- Desligar o chat: `"chat_ligado": false` em config.json.

## Pesquisa de mercado (pesquisa_notebooks.py) e aprendizados
- `python pesquisa_notebooks.py lista|abrir N|verificar|relatorio`. O resultado sai em `pesquisa\RESULTADO_NOTEBOOKS.md`. Feita em 04/11.
- **Ler `APRENDIZADOS.md`** antes de mexer. Trata do filtro de RAM errado, do preço isca, da leitura de fotos e dos códigos de filtro da OLX (`nme`, `nmo`).
- O alerta normal agora:
  - lê as fotos quando sobra dúvida (`ler_fotos`);
  - extrai o `preco_real` e descarta preço isca;
  - tenta de novo quando a OLX dá 502.

## Pendente
- Anunciar de volta (revenda): a dona pediu, ainda não foi feito.
- Usar o botão oficial "Fazer oferta" do anúncio. Hoje o desconto é pedido por mensagem.
