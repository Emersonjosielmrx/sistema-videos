# Pendências — Painel de Clientes (MVP no ar em 24/10/2026; revisão geral em 30/10/2026)

Em ordem de prioridade. O que foi feito em 30/10 está em `docs\ANDAMENTO.md`.

0. **WhatsApp no status — falta só o Luiz conectar.** Ligado em 30/10: chave de API do Hermes criada para o usuário
   "Admin" (nome "Painel de Clientes (status do WhatsApp)", em `segredos\hermes_chave.txt`; revogar = Configurações ›
   API do Sistema › API Keys no Hermes). A conta "Status · Advance Energia Solar" já existe no Hermes e o QR real foi
   testado. Quando o Luiz conectar pelo botão "conectar WhatsApp", cada Reel novo da Advance
   (`D:\ms-energy\bin\reel_advance.py`) vai também para o status dele. Carrosséis não vão. MS Energy e outros
   clientes: chamar `coletor\status_whatsapp.py` no postador deles.

1. **Instagram do Açaí O Precioso (@accai_oprecioso) sem acesso à API.** Sem isso não entram Direct, comentários,
   alcance nem seguidores do Precioso (hoje só pedidos do site e visitas). Precisa conectar a conta ao app da Meta
   (login do Instagram dela) e pôr o token em `D:\credenciais-canais\instagram_contas.json`. Alternativa sem API: pôr
   `"instagram_http": true` no Precioso em `config\clientes_manuais.json` (lê pela sessão do cofre, como a Advance) —
   precisa da conta logada no perfil `ig_accai_oprecioso` do cofre.
2. **Tokens vencidos das contas de produto.** `inovarecom.ia` (Hermes Call) e `futebolcom.ia2` (Cardápio Digital)
   venceram em 24/10; `sintetizerisada` (Agenda IA) em 08/05; várias contas de grupo nunca tiveram token. Token vencido
   não se renova: precisa entrar de novo pelo login do Instagram no app. **Desde 30/10 o coletor renova sozinho (1x por
   dia) o token das contas que ainda respondem** (msenergycap, inovaresites, inovareclone, inovareagenda, inovarecrm),
   então essas não vencem mais; quem for reconectado entra na renovação automaticamente.
3. **Advance (@advance_novoestrela, conta pessoal)**: lida pela sessão do cofre a cada 2 h desde 30/10 (tarefa
   `PainelClientes_ColetarHTTP`). Conta pessoal não dá alcance/toques/visitas ao perfil — só seguidores, posts,
   comentários e Direct. Para ter tudo: virar conta profissional e ligar à API.
4. **WhatsApp da loja do Precioso não está conectado** no sistema acai-lojas (`dados/whatsapp/precioso` vazio): as
   conversas do WhatsApp da loja ainda não contam como contato.
5. **Pedido de teste na loja** (nº 3, 11/10, "Eduardo Almeida", R$ 45,00) aparece como pedido real no painel.
   Se for teste, cancelar no painel da loja.
6. **MS Energy sem contato novo pela API desde 23/11/2025** (o vigia_clientes da MS Energy vê o mesmo): os clientes
   dela devem estar indo direto pro WhatsApp. Para medir, usar o link rastreado na bio/anúncios (item 7).
7. **Link da bio da MS Energy**: hoje é o `wa.me` direto (o Instagram já conta os toques). Para separar por
   campanha/lugar, trocar pela versão rastreada (criar em "Links rastreados") — decisão da dona.
8. **API de anúncios da Meta** (ads_read): hoje o investido/alcance/resultados do anúncio entram à mão ou pelo CSV do
   Gerenciador (CSV por conjunto de anúncios agora soma numa campanha só). Com a conta de anúncios autorizada, puxar sozinho.
9. **Segunda empresa de energia solar**: se não for a Advance, preencher um cliente novo em
   `config\clientes_manuais.json` e rodar `python publicar.py --config`.
10. **TikTok** dos clientes (MS Energy tem @energia.solar.da) ainda não entra no painel.
11. **Resumo para o cliente** (semanal no WhatsApp/Telegram com o link do painel) — não feito (manda mensagem em nome
    da dona: precisa do OK dela e do texto).
12. **Histórico do Instagram**: a API só dá 30 dias de números por dia; o painel guarda dali em diante. Comparações
    com períodos antes de 27/09/2026 ficam sem números do Instagram (aparecem como "—", não 0).
13. **Senha do login da Advance** é o próprio nome (luiz/luiz), por pedido da dona. Se quiser mais segura, pôr
    `"senha": "..."` no cliente em `clientes_manuais.json` e rodar `python publicar.py --config`.
