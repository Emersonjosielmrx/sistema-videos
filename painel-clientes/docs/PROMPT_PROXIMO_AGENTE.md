# Prompt para o próximo agente — Painel de Clientes (30/10/2026)

## Prompt

```
Você vai continuar o Painel de Clientes da dona: D:\painel-clientes (no ar em https://clientes.opus-sem-limites.com.br).
Responda sempre em português do Brasil, direto, sem perguntar o que dá para decidir sozinho.

LEIA PRIMEIRO, nesta ordem:
1. D:\painel-clientes\docs\ESPECIFICACAO.md — como funciona, de onde vem cada número, API, peças.
2. D:\painel-clientes\PENDENCIAS.md — o que falta, em ordem de prioridade.
3. D:\painel-clientes\docs\ANDAMENTO.md — o que já foi feito (inclui a revisão geral de 30/10).

O QUE É: painel dos clientes (Açaí O Precioso, MS Energy, Advance Energia Solar) e dos Instagram de produtos.
Mostra para o cliente, de um jeito que leigo entende: VISUALIZAÇÕES em destaque (o único número grande);
curtidas e "pessoas que entraram em contato" só em linhas pequenas; os 5 posts mais vistos com a miniatura do
próprio Instagram. Tudo que é complexo (tabelas, campanhas, links rastreados, gráficos) fica atrás do botão
"ver todos os detalhes". Tem "imagem para o status" (PNG 1080x1920, só visualizações em destaque) e
"conectar WhatsApp".

PEÇAS:
- servidor\app.py + servidor\web\index.html: contêiner Docker "painel-clientes" na hermes-prod (127.0.0.1:8098,
  Traefik). Só biblioteca padrão. Dados em /opt/painel-clientes/servidor/dados (painel.db, backup diário em backups/).
- Publicar: `python D:\painel-clientes\publicar.py` (tudo) ou `--config` (só clientes/chaves). Só a página:
  copiar servidor\web\index.html para /opt/painel-clientes/servidor/web/ por scp (é montada, não precisa reiniciar).
- coletor\coletar_instagram.py: tarefa PainelClientes_Coletar (30 min) — API do Instagram; renova sozinho, 1x/dia,
  os tokens que ainda funcionam (via D:\postador-de-videos\bin\renovar_token_insta.py).
- coletor\coletar_instagram_http.py: tarefa PainelClientes_ColetarHTTP (2 h, D:\veo\venv\Scripts\pythonw.exe) — contas
  sem API ("instagram_http": true; hoje só a Advance @advance_novoestrela) pela sessão do cofre (perfil ig_<conta>).
- servidor\coletor_vps.py: cron 5 min na VPS (pedidos da loja do Precioso + visitas dos sites pelo nginx).
- WhatsApp no status: o cliente conecta o WhatsApp dele no botão "conectar WhatsApp" (QR ou código pelo número);
  o painel cria 1 conta "Status · <cliente>" no Hermes Call (API https://hermescall.opus-sem-limites.com.br, chave
  hk_ do usuário Admin em segredos\hermes_chave.txt -> segredos.json como "hermes_chave"). O postador chama
  coletor\status_whatsapp.py (mandar_video) depois de postar no Instagram — hoje ligado só no
  D:\ms-energy\bin\reel_advance.py (Reels da Advance).
- Login do cliente: usuário/senha (Advance = luiz/luiz, pedido da dona) ou link com #k=chave (segredos\LINKS.txt).

COMO TESTAR ANTES DE PUBLICAR:
- Cópia do banco de produção em D:\painel-clientes\teste\dados_prod (renove com sqlite backup pela VPS, só leitura).
- Servidor local: PASTA_DADOS=D:/painel-clientes/teste/dados_prod PORTA=8199 HOST=127.0.0.1 python servidor/app.py
  (chaves de teste: admin "teste-admin-chave-local", cliente "chave-<id>"; para o Hermes use um Hermes FALSO com
  HERMES_URL apontando para ele — nunca teste contra o Hermes real com chave inventada).
- Página: extraia o <script> e rode `node --check`; confira no navegador do painel (localhost:8199) em tamanho de
  celular (375x812) sem rolagem lateral e sem erro no console.
- Antes de publicar: compare o sha256 do app.py da VPS com o que você leu (outra sessão pode ter publicado).

PRÓXIMOS PASSOS (ver PENDENCIAS.md):
1. Conferir se o Luiz conectou o WhatsApp (GET /api/whatsapp?cliente=advance com a chave de admin) e, depois do
   próximo Reel da Advance, se o status saiu (logs em D:\ms-energy\logs\reel_advance.log, linha "status WhatsApp").
2. Direct da Advance não entra: em coletar_instagram_http.py a leitura de direct_v2/inbox devolve algo que não é
   JSON (JSONDecodeError). Investigar com POUCAS leituras (o Instagram limitou essa conta em 30/10).
3. Levar o "mandar pro status" para os outros postadores que a dona quiser (MS Energy:
   D:\postador-de-videos\bin\postar_ms_energy.py), sempre sem deixar a falha do status desfazer o post do Instagram.
4. Instagram do Precioso sem acesso (pendência 1) e tokens vencidos dos produtos (pendência 2) dependem da dona
   logar no Instagram.
```

## Restrições (o que eu NÃO faço — vale para você também)

```
- Não digito senha nem token em site nenhum e não faço login por ninguém (nem no Instagram, nem no Hermes, nem no
  painel em produção). Login com senha é sempre a dona quem faz. Em servidor local de teste pode.
- Nunca mostro, imprimo, logo nem coloco em comando a chave do Hermes, as chaves do painel, tokens do Instagram ou
  senhas. Leio de arquivo dentro do script e pronto. Nada disso vai para o GitHub.
- Na hermes-prod (VPS COMPARTILHADA com o Hermes Call, Atlas e Lucrativa): só mexo no que é do painel
  (/opt/painel-clientes, contêiner painel-clientes, /etc/cron.d/painel-clientes, /opt/traefik-config/dynamic/clientes.yml
  e o log de visitas do nginx pelo ligar_visitas_nginx.py, que roda `nginx -t` antes e desfaz se falhar).
  Não reinicio nem altero o Hermes Call, o acai-lojas, o nginx de outros sites, o Atlas nem o Lucrativa.
- Não mudo o CÓDIGO do Hermes Call (D:\hermes). O painel só usa a API dele. Publicar o Hermes exige OK da dona.
  O banco do Hermes só foi tocado 1 vez, com autorização dela, para criar a chave do painel; não mexer mais.
- Ao banco da loja (acai-lojas) só leitura (node:sqlite com readOnly dentro do contêiner).
- Acesso às VPS só por chave (ssh hermes-prod); nunca tento senha (fail2ban bane o IP).
- Não mando mensagem em nome da dona nem do cliente (WhatsApp, Telegram, e-mail, Direct) sem ela pedir. O "status
  do WhatsApp" só sai para quem o próprio cliente conectou.
- Não leio o Instagram em rajada: a conta da Advance foi limitada em 30/10. O coletor HTTP roda a cada 2 h com
  poucas leituras; não rode ele várias vezes seguidas para testar.
- Não apago dado (banco, backups, logs, cache\coletor_estado*.json, segredos\). Não mato processo de outra sessão
  (pythonw de produção, Chrome do cofre nas portas 97xx, ffmpeg ativo) — confira antes.
- Downloads e arquivos temporários só no disco D (nunca no C).
- Número que não tem fonte aparece "não conectado"/"—", nunca inventado. Na tela do cliente a comparação com o
  período anterior só aparece quando cresceu (queda fica nos detalhes) — decisão da dona.
- Publicar o painel pode (é o fluxo normal), mas só depois de testar local; conferir o sha256 da VPS antes.
- Não digo "pronto" sem prova: teste rodado, print/leitura da tela, ou resposta da API em produção.
```
