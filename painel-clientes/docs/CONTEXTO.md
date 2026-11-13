# Painel de Clientes — levantamento (24/10/2026, noite)

## Pedido da dona (palavra por palavra)

> projete um painel baseado nesse mais so para os clienets que vamso ter como vamso ter acai o rpecisoso que e
> https://precioso.opus-sem-limites.com.br/, e ms energy e ooutro de enrgia solar qeu vamops adicionar, e agroa dops
> prudotos esse vai ser excluviso para os isntragm de clienets e produtos e pessosa que etreram em contatoe varios
> dados que vamos ultimalizar que vamos fazer campanhas impulsionamento e qeuro metircas rpa mostrar rpa clienets
> comoq auntas epsasaos entraram em contato etc

Leitura: um painel **só de clientes e produtos** (não de canais de vídeo), "baseado nesse" = no estilo dos painéis
que já existem (painel :8790 `D:\video-fila\painel_web\index.html` e telão `D:\video-fila\vitrine\painel.html`).
Clientes: **Açaí O Precioso**, **MS Energy**, **outra empresa de energia solar (ainda vai entrar)**. Também os
**Instagram de produtos**. Foco: **pessoas que entraram em contato**, dados para **campanhas/impulsionamento** e
**métricas para mostrar ao cliente** ("quantas pessoas entraram em contato" etc.).

## Clientes e fontes de dados

### Açaí O Precioso
- Site/cardápio com pedido online: https://precioso.opus-sem-limites.com.br (título "Açaí O Precioso - Faça seu
  pedido!", Paragominas-PA, cor #5e1d8f, Instagram **@accai_oprecioso**).
- Sistema `acai-lojas` (Node 22, contêiner Docker `acai-lojas` na **hermes-prod**, `/opt/acai-lojas/servidor`,
  porta 127.0.0.1:8095; nginx 127.0.0.1:8086 serve `/var/www/precioso` e manda `/api/` com `X-Loja: precioso`).
  Multi-loja: `precioso` e `nelson` (outra loja já prevista; `/var/www/nelson`).
- Banco SQLite `/opt/acai-lojas/servidor/dados/acai.db` (WAL; backup diário em `dados/backups`). Tabelas: `pedidos`
  (loja, criado_em ISO UTC, telefone, nome, itens JSON, total, status, origem, forma_pagamento, cupom, desconto,
  avaliacao...), `clientes` (loja, telefone, nome, bairro, origem, criado_em, optout...), `conversas`/`mensagens`
  (WhatsApp da loja), `contatos_wa`, `envios` (campanhas de WhatsApp: tipo, status, respondeu_em, variante),
  `followups`, `cupons` (usos), `resgates`, `atividades`. `src/relatorio.js` já calcula fechamento do dia (pedidos,
  ticket médio, itens, clientes novos, avaliação).
- **Hoje: 1 pedido de teste (11/10), 1 cliente, 0 conversas** — o WhatsApp da loja não está conectado
  (`dados/whatsapp/precioso` vazio). O painel tem que funcionar com zero e crescer.
- Ler o banco: `docker exec -i acai-lojas node --disable-warning=ExperimentalWarning -` com `node:sqlite`
  `DatabaseSync(path, {readOnly: true})` funciona (testado). Não mexer no sistema da loja.
- Visitas do site: nginx global `/var/log/nginx/access.log` (formato combined, SEM host, remote_addr 127.0.0.1 por
  causa do Traefik) — dá pra separar pelo referer, mas o certo é um `access_log` próprio por site com
  `$http_x_forwarded_for` e `$host` (mexer no nginx da produção só com `nginx -t` antes do reload).

### MS Energy (energia solar, Paragominas-PA)
- Instagram **@msenergycap** (BUSINESS, 2.076 seguidores, 166 posts em 24/10). **Token da API vivo** em
  `D:\credenciais-canais\instagram_contas.json` (formato n8n: `name`, `data.accessToken`), API
  `https://graph.instagram.com/v21.0` (Instagram Login). Renovação: `D:\postador-de-videos\bin\renovar_token_insta.py`.
- Métricas prontas: `D:\ms-energy\bin\metricas_insta.py` (perfil + insights por Reel/carrossel: views, reach, likes,
  comments, shares, saved, ig_reels_avg_watch_time; histórico em `D:\ms-energy\cache\metricas\<data>.json`; TikTok
  @energia.solar.da lido pelo navegador do cofre `msenergypara`).
- Contatos: `D:\ms-energy\bin\vigia_clientes_insta.py` (a cada 15 min): comentário novo e Direct novo → aviso no
  Telegram + resposta automática com o WhatsApp `https://wa.me/message/RTCI5IGNUZVIF1`. Estado em
  `D:\ms-energy\cache\vigia_clientes.json` (ids + horários de comentários/mensagens, `respondidos`). Texto dos avisos
  em `D:\video-fila\estado\avisos.jsonl` (origem `msenergy-clientes`). API: `me/conversations?platform=instagram`
  e `me/media` + `{id}/comments` dão as pessoas (username, texto, horário).
- WhatsApp da MS Energy é o celular da empresa: não temos acesso às conversas → medir **cliques** no link.
- `D:\postador-de-videos\config\marcas_instagram.json` também tem a conta `msenergysolar.pa` (marca MS Energy).

### Outra empresa de energia solar
- Ainda não tem nome/Instagram. Cliente novo tem que entrar por configuração (uma entrada num JSON), sem código.

### Instagram de produtos
- `marcas_instagram.json` (com campo `produto`): inovarecom.ia = Hermes Call, futebolcom.ia2 = Cardápio Digital,
  sintetizerisada = Agenda IA; mais contas de grupo em `D:\postador-de-videos\config\instagram_produtos.json`
  (disparoemmassa, followupia, vpsblindada, ...) ainda sendo criadas (5/dia).
- Página de venda de cada produto: `<slug>.opus-sem-limites.com.br` (nginx 127.0.0.1:8087, `/var/www/landings` na
  hermes-prod; textos em `D:\landings-produtos\conteudo.json`, que tem o WhatsApp de venda).
- **Tokens da API de quase todas as contas de produto estão mortos (HTTP 400 em 24/10)**; só `msenergycap` e
  `_lucrocomia_` respondem. As contas estão logadas no navegador do PC1 (`D:\postador-de-videos\bin\instagram_local.py`,
  senha só pela variável `IG_SENHA`). Atendimento por IA de comentário/DM: fluxo n8n "instagram multi atendimento
  geral" na VPS 209 (ver memória reference-n8n-console-instagram).

### Campanhas / impulsionamento
- **Não existe nada de Meta Ads no sistema** (sem token de anúncios, sem conta de anúncio cadastrada). O que dá para
  medir sem a API: link rastreado por campanha (redirecionador próprio que conta clique e manda pro WhatsApp/site),
  contatos que chegam no período, e o número que a dona digita/importa do Gerenciador de Anúncios (CSV).

## Onde hospedar
- **hermes-prod** (`ssh hermes-prod`, 62.171.128.241) — é a PRODUÇÃO do Hermes Call: não derrubar nada.
  DNS coringa `*.opus-sem-limites.com.br` aponta pra ela; Traefik v2.10 lê `/opt/traefik-config/dynamic/*.yml`
  (modelo: `precioso.yml`, `certResolver: le`, serviço `http://127.0.0.1:<porta>/`). Portas já usadas no 127.0.0.1:
  8080, 8085, 8086, 8087, 8090, 8095, 8777. Docker disponível (compose do acai-lojas como modelo), Python 3.11 no host,
  ~5 GB de RAM livre, 99 GB de disco.
- O PC1 (Windows, este) tem os tokens do Instagram, o cofre de navegador e os scripts da MS Energy: coleta do Instagram
  roda aqui e manda pra VPS (como o vitrine.py faz com o telão).

## Regras da dona que valem aqui (memória)
- Tabelas: ordenar clicando na coluna, filtro por coluna, busca geral, exportar CSV; sempre título + link; aba por
  cliente/projeto; botão de verdade (POST), nunca "rode este comando"; visual com os efeitos do Hermes Call
  (vidro/blur, cards que sobem no hover, ícone com glow, faixa hero em degradê, entrada fade/slide).
- Conferir telas com print real (desktop e celular) e testar os cliques.
- MVP no ar primeiro, depois `PENDENCIAS.md` com o que faltou.
- Telegram só pelo portão `D:\video-fila\avisos.py` (poucas mensagens). Google só pelo navegador (nada de chave de API
  do Google Cloud). Senha/token nunca em código, log ou print.
- Português do Brasil em tudo que a dona e o cliente veem.
