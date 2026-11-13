# Painel de Clientes — como funciona (24/10/2026)

No ar em **https://clientes.opus-sem-limites.com.br**. Links de acesso (admin e de cada cliente):
`D:\painel-clientes\segredos\LINKS.txt` (não compartilhar o de administração).

## Para que serve
Painel só dos **clientes** (Açaí O Precioso, MS Energy, a outra empresa de energia solar quando entrar) e dos
**Instagram de produtos**: quantas pessoas entraram em contato, por onde, quem são, o que as campanhas de
impulsionamento trouxeram e os números do Instagram e do site — para a dona acompanhar e para mostrar ao cliente.

## Quem vê o quê
- **Administração** (link com a chave de admin): todos os clientes e produtos, visão geral, cria/edita campanhas,
  importa o CSV do Gerenciador de Anúncios, cria links rastreados, copia o link de cada cliente.
- **Cliente** (link próprio): só os números dele; pode marcar a situação de cada pessoa (novo, em atendimento,
  virou cliente, sem interesse) e escrever anotação. Não vê outros clientes nem cria campanha.
- A chave vai no `#k=` do link (não chega ao servidor no endereço nem fica em log) e sai da barra de endereço na hora;
  fica guardada no aparelho até clicar em "sair".
- 30/10: o cliente também entra com **usuário e senha** (`"login"` / `"senha"` em clientes_manuais.json; sem `"senha"`, a
  senha é o próprio usuário). Só o hash vai para o servidor. 20 chaves/senhas erradas do mesmo IP em 10 min → bloqueio
  de 10 min (HTTP 429).
- **Juntar pessoas** (admin e o próprio cliente): no diálogo "situação" de uma pessoa, "É a mesma pessoa que…" faz o @
  do Instagram e o telefone contarem 1 vez. A situação/anotação são somadas no registro principal; "separar" desfaz.
- **Quem entra no painel não conta como visita nem clique**: o servidor anota IP + navegador de quem usa uma chave
  (`dados/casa.json`, 60 dias); o coletor_vps.py tira esse par das visitas ao site, e o /r/ não conta o clique dele.
- A página se atualiza sozinha a cada 5 min (aba visível, sem diálogo aberto) — o modo TV não fica com número velho.

## De onde vem cada número
| Número | Fonte | Como é contado |
|---|---|---|
| Pessoas que entraram em contato | Direct e comentários do Instagram (API), WhatsApp da loja e pedidos do site (sistema acai-lojas) | cada pessoa 1 vez no período (`ig:<usuario>` ou `tel:<55...>`); contas da casa ficam fora (`ignorar` em clientes_manuais.json) |
| Toques no link da bio, visitas ao perfil, alcance, visualizações, seguidores | Instagram (API, insights da conta) | soma dos dias do período; dia do Instagram termina 04:00 de Brasília |
| Cliques nos links rastreados | links `/r/<código>` deste painel | cada clique antes de mandar pro WhatsApp/site; robôs (prévia do WhatsApp/Facebook) não contam |
| Visitas ao site | log do nginx (`/var/log/nginx/painel_visitas.log`) | pessoas diferentes por dia (IP + navegador), só a vitrine (sem /admin, /api, robôs) |
| Pedidos e vendido | sistema de pedidos da loja | sem cancelados e "aguardando" (igual ao fechamento da loja) |
| Campanhas | cadastro manual ou CSV do Gerenciador | "contatos durante" = pessoas em contato nos dias da campanha; "antes" = mesmo número de dias antes; custo por pessoa = investido ÷ contatos durante |
Fonte que não existe para o cliente não aparece; fonte que existe mas não está ligada aparece como **não conectado** com o motivo.
Cartão ligado mas sem número no período mostra **—** (não 0). Conta lida pela sessão (sem API, `instagram_http`) não
tem números por dia: só seguidores, posts e contatos; alcance/toques/visitas ao perfil ficam escondidos.
Seguidores = o último número de cada conta até o fim do período escolhido (período passado mostra o número daquela época).

## Peças
- `servidor/app.py` — API + página (Python só biblioteca padrão), contêiner `painel-clientes` na hermes-prod,
  127.0.0.1:8098, Traefik `/opt/traefik-config/dynamic/clientes.yml`. Dados em `/opt/painel-clientes/servidor/dados`
  (`painel.db`, `clientes.json`, `segredos.json`, `fontes/`, `casa.json`, `backups/`). `app.py` e `web/` são montados:
  trocar a página = copiar o arquivo; trocar o código = copiar + `docker restart painel-clientes`. **Backup do banco
  1x por dia** em `dados/backups/painel_AAAAMMDD.db` (14 dias) — campanhas, situações, anotações e cliques só existem
  ali. Respostas em gzip.
- `servidor/coletor_vps.py` — cron 5 min na VPS (`/etc/cron.d/painel-clientes`): banco da loja por
  `docker exec acai-lojas node` (somente leitura) + log de visitas → `dados/fontes/*.json`. Log:
  `/opt/painel-clientes/coletor_vps.log`.
- `servidor/ligar_visitas_nginx.py` — liga o log de visitas (cópia em `/opt/painel-clientes/backup_nginx`,
  `nginx -t` antes, desfaz se falhar).
- `coletor/coletar_instagram.py` — PC1, tarefa do Windows `PainelClientes_Coletar` (30 min, prioridade 6). LÊ a API
  do Instagram (tokens de `D:\credenciais-canais\instagram_contas.json`) e, 1x por dia, renova o token das contas que
  responderam (`D:\postador-de-videos\bin\renovar_token_insta.py`: só renova com 7+ dias, copia o arquivo antes) — sem
  isso o token vence em 60 dias. Pula as contas `instagram_http`. Log `logs\coletor.log`, estado
  `cache\coletor_estado.json`.
- `coletor/coletar_instagram_http.py` — PC1, tarefa `PainelClientes_ColetarHTTP` (2 h, `D:\veo\venv\Scripts\pythonw.exe`):
  contas sem API (`"instagram_http": true`, ex.: Advance) pela sessão do cofre (perfil `ig_<conta>`), pouca leitura.
  Falhando há 6 h+, o painel mostra o motivo. Log `logs\coletor_http.log`.
- `gerar_config.py` — `config\clientes.json` = `config\clientes_manuais.json` + produtos das landings
  (`D:\landings-produtos\conteudo.json`) com o Instagram de `marcas_instagram.json`.
- `publicar.py` — publica tudo; `python publicar.py --config` só manda clientes/chaves (cliente novo).

## Cliente novo (ex.: a outra empresa de energia solar)
1. Em `config\clientes_manuais.json`, preencher o modelo `solar2` (nome, cor, cidade, instagram, whatsapp, site) e
   `"ativo": true`.
2. Token do Instagram dele em `D:\credenciais-canais\instagram_contas.json` (nome "Instagram <usuario>").
3. `python D:\painel-clientes\publicar.py --config` → o link do cliente aparece em `segredos\LINKS.txt`.

## API (cabeçalho `X-Chave`)
- `GET /api/eu` → `{papel, clientes:[{id,nome,tipo,cor,cidade,instagram,site,whatsapp,link_cliente?}]}`
- `GET /api/painel?cliente=&de=AAAA-MM-DD&ate=` → `{cliente, periodo, cards[{id,titulo,valor,anterior,fonte,conectado,sub,fmt,motivo}], por_canal, serie_contatos, serie_dia, pessoas[], campanhas[], links[], pedidos[], posts[], fontes[], status_opcoes}`
- `GET /api/geral?de=&ate=` (admin) → uma linha por cliente/produto com os números principais e o que falta conectar
- `POST /api/entrar {usuario, senha}` → `{chave}` (público; 429 depois de 20 erros do IP em 10 min)
- `POST /api/pessoa {cliente, pessoa, status?, nota?}` (admin ou o próprio cliente)
- `POST /api/pessoa/juntar {cliente, pessoa, com}` ou `{cliente, pessoa, separar: true}` (admin ou o próprio cliente);
  `pessoas[]` traz `juntadas: [ids]`
- `POST /api/campanha {id?, cliente, nome, plataforma, objetivo, inicio, fim, orcamento, gasto, alcance, impressoes, cliques, resultados, resultado_tipo, obs, destino?}` (admin; cria o link rastreado da campanha)
- `POST /api/campanha/apagar {id}`, `POST /api/link {cliente, nome, destino, codigo?}`, `POST /api/link/apagar {codigo}` (admin)
- `POST /api/campanhas/importar {cliente, csv}` (admin; cabeçalhos do Gerenciador em português ou inglês)
- `POST /api/coleta` (admin; coletor do PC1) · `GET /r/<código>` (público, conta e redireciona) · `GET /api/saude`
