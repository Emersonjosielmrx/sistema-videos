# Estado do Facebook — atualizado 20/11/2026

## Postador ATUAL: `bin\fb_reel_bs.py` (Meta Business Suite)
O antigo `facebook_cdp_poster.py` (botão "Criar reel" na página) PAROU em 2026: o layout novo não tem o botão.
Agora tudo posta pela tela "Criar reel" do Business Suite:
`https://business.facebook.com/latest/reels_composer?asset_id=<asset_id>`

Fluxo: entrar como a Página (`fb_entrar_como.py`) → composer → "Postar em" fica SÓ a Página (Instagram desmarcado) →
"Adicionar vídeo" (file chooser) → texto → Avançar (botão do rodapé; a setinha das miniaturas também se chama
"Avançar") → Avançar → Compartilhar → "Reel em processamento".

## Quem posta
| Página | Conta / saída | Script | Tarefa |
|---|---|---|---|
| MS energy (cliente) | msenergypara, casa, porta 9401 | `postar_ms_energy.py --so fb` | MSEnergy_PostarFB 11:05/20:05 |
| Anime Noturno, Assist-IA Investimentos, Curiosidades Noturnas, Dorama Noturno, Filme Noturno | emersonjosiel02, Webshare rnprmtfo-58, porta 9798 | `postar_facebook_paginas.py` | FacebookPaginas 12:20/18:20/21:10 |

Config: `config\facebook_paginas.json` (asset_id, tags do tema, canais de origem, por_dia). Filtro de tema: a 1ª
hashtag da legenda tem que estar nas `tags` da Página. Registro:
`logs\facebook_paginas.json`. Log: `logs\facebook_paginas.log`, `D:\ms-energy\videos\cron_postar_fb.log`.

## Ferramentas
- `fb_contas.py` abre o Chrome da conta e RECUSA se o proxy não bate com a saída da conta.
- `fb_page_id.py` acha o asset_id (`delegate_page_id`); `fb_criar_pagina.py` cria Página; `fb_montar_pagina.py` põe
  foto/capa; `fb_arte_pagina.py` gera a arte; `fb_conferir_reels.py` confere a aba Reels; `fb_monetizacao.py` lê a aba
  Monetização.

## Inteligência (20/11, igual às outras redes)
- **Catálogo**: `catalogo.py` lê `logs\facebook_paginas.json` → o vídeo passa a ter postagem "facebook" (resumo mostra a
  coluna facebook; o backup do Drive sabe o que já foi pro FB).
- **Escada** `fb_escada.py` (estado `config\fb_escada.json`, log `logs\fb_escada.log`): base = `por_dia` (3), sobe +1 a
  cada 3 dias se encheu o teto em 2 dos últimos 3 dias, sem bloqueio e views não caindo; teto 8/dia. Erro com
  bloqueio/restrição/limite no postador = desce 1 e segura 24 h sem postar. `python fb_escada.py ver`.
- **Medidor** `fb_medir.py`: views de cada reel + seguidores por Página (pela saída fixa) → `logs\fb_views.jsonl` e
  `FACEBOOK_VISUALIZACOES.md`.
- Tarefa `FacebookInteligencia` 08:30 (medir + escada).

## Criação automática de Páginas (20/11: 1 por TikTok, 53 na fila)
- Fila `config\fb_fila_paginas.json` (53 = TikToks sem Página; 27 na msenergypara/perfil 10+ anos, 26 na
  emersonjosiel02). Página de TikTok sem canal = `temas_veo` (Veo do tema que já saiu no YouTube, só versão limpa).
- `fb_criar_fila.py`: arte → cria (nome/categoria/bio) → id + asset_id → foto → capa → entra no
  `facebook_paginas.json` → 1º Reel. Etapa que falhou continua na próxima rodada. 1 Chrome aberto o procedimento todo.
- Ritmo: revezam as contas, 3 h entre criações da mesma conta, máx. 3/dia (msenergypara) e 2/dia (emersonjosiel02);
  aviso de "rápido demais"/restrição/checkpoint = conta parada 48 h + Telegram. Estado `logs\fb_fila_estado.json`.
- Tarefa `FacebookCriarPaginas` 09:40 13:40 16:40 19:40 22:40 (pula se uma rodada de postagem está rodando).
  `python fb_criar_fila.py --ver` mostra a fila.

## Rodada de hora em hora + correções (20/11 tarde)
- `FacebookPaginas` 08:20→23:20 de hora em hora; as 2 contas em PARALELO (`--horario --conta X`, cada uma no Chrome e
  saída dela). `deve_postar_agora`: o teto da escada espalhado 08-21 h e 1 post guardado pro nobre 21-22 h.
  Sem post devido = sai em ~1 s sem abrir nada. Catálogo: usa o `catalogo_videos.json` salvo (< 2 h); o
  `sincronizar()` lia o Drive e travou a rodada das 12:20 por 10+ min.
- Entrar como a Página = cookie `i_user=<id>` no Chrome (`fb_entrar_como.entrar_como_cookie`); menu só de reserva.
- `fb_contas.abrir`: sem porta = mata os Chromes restantes DESTE perfil e tenta 2x (ECONNREFUSED 9401 da MS Energy 11:05
  era Chrome do perfil morrendo); `fechar` espera o processo sair.
- `fb_escada`: segura Página com Reel decolando (como o YouTube) e +1 vaga no dia em que estagna.
- Medição por HTTP (`D:\projeto-navegador-sem-navegador\services\facebook\medir.py`, chat "navegador sem navegador"),
  fallback `fb_medir.py`; 08:30 14:30 20:00. Postagem por HTTP: em andamento lá (`docs\FACEBOOK_SEM_NAVEGADOR.md`).
- Vigilância: `video-fila\vigilancia.med_facebook` (Página sem Reel até 22 h; mesmo erro 3x em 6 h); painel confere as
  4 tarefas.

## Decisões da dona 20/11 tarde
- **MS Energy é comercial**: o perfil msenergypara só posta na Página MS energy, os MESMOS vídeos do Instagram
  (`postar_ms_energy.py`). Nada de entretenimento lá: Cena React e Histórias em Frames (criadas lá) PAUSADAS; a fila
  inteira (51) vai pro emersonjosiel02.
- **msenergypara fora do Fish** (era rnprmtfo-37 desde 19/11, e o Facebook/TikTok dela saem de casa = 2 IPs): cofre
  `fish_proxy_removido` + `fish_removida`; `pool_fish.candidatas` pula `fish_removida`/`so_casa`.
- **1 perfil = 1 saída**: proxy por Página não adianta (o mesmo perfil gerencia todas). O que se mede é até quantas
  Páginas VALEM a pena: `fb_saturacao.py` (depois do medidor) compara a mediana de views dos Reels dos últimos 3 dias
  com a 1ª semana do perfil; < 40% com >= 15 Reels = perfil saturando -> `fb_criar_fila` para de criar + Telegram.
  Relatório `FACEBOOK_SATURACAO.md` (views por lote de 5 Páginas, na ordem de criação).

## Monetização (aba do Business Suite, 20/11)
- MS energy: qualificada em Monetização de conteúdo, Estrelas e Assinaturas — falta a dona aceitar os termos e
  cadastrar a conta de pagamento.
- Páginas novas: Estrelas = 500 seguidores por 30 dias; Assinaturas = 5.000 seguidores.

## 22/11/2026 (tarde/noite) — registro para auditoria
- **Estado de postagem às 19:21:** 14 páginas no config, 12 ativas (Cena React e Histórias em Frames pausadas). Reels hoje: Assist-IA 2; Anime, Curiosidades, Dorama, Esporte, Cartucho React, Fio da Meada e Mistérios 1 cada; Filme, Bicho, Invento React, Comédia e MS Energy 0. Fonte: `bin\fb_status.py`.
- **Causas das falhas (não corrigidas na raiz):** upload `FileChooser.set_files` estourando 90 s 3x (Dorama, Filme, Bicho, Invento React, Comédia); `Page.goto` do compositor do Filme Noturno estourando 120 s; PC1 muito carregado (comandos simples levando minutos). O vigia (`bin\fb_vigia.py`) matou rodadas com mais de 45 min às 13:32, 15:42, 17:21 e 18:09.
- **Rodadas manuais de hoje:** uma conta por vez, trava `logs\fb_postando_<conta>.lock`. A da emersonjosiel02 das 16:27 (pid 37812) foi morta pelo vigia às 17:21. A da mundosolar1995 das 18:36 terminou sem erro até ~19:21. A da emersonjosiel02 foi disparada de novo ~19:25 (task byory29eb); resultado ainda não conferido.
- **Alteração em `bin\fb_reel_bs.py` (`_botao`):** `bounding_box(timeout=8000)` dentro de try, para o PC1 pesado não derrubar a página (o erro `Locator.bounding_box: Timeout 30000ms` derrubou a Anime Noturno 4x). O arquivo compila; NÃO foi testado no navegador.
- **Novo `bin\fb_api_checar.py`:** confere o acesso pela Graph API só por leitura, sem postar. Sai pela saída fixa da conta (fish_audio._subir_ponte, rnprmtfo-58 para a emersonjosiel02). O JSON de `/me/accounts` vem por stdin e o app id/segredo por FB_APP_ID/FB_APP_SECRET; nada é gravado em disco nem impresso.
- **Resultado da checagem da API:** 5 tokens de página válidos (Cartucho React, Esporte Noturno, Filme Noturno, Dorama Noturno, Curiosidades Noturnas), tipo PAGE, com pages_manage_posts, pages_read_engagement e pages_show_list; leitura de dados e de Reels funcionou; os ids batem com os asset_id do config. Mas `expires_at` = 22/11 16:00 -03 (checado às 16:19), então são tokens de curta duração, já vencidos. Anime Noturno e Assist-IA não vieram por causa da paginação (usar `/me/accounts?limit=100`).
- **Pendente com a dona (API):** gerar token de usuário novo e trocar por um de longa duração (`fb_exchange_token`), chamar `/me/accounts?limit=100` e mandar o resultado, que a checagem roda de novo e deve mostrar `expires_at` = 0. Redefinir o segredo do app (Configurações > Básico), exposto no chat. Os tokens da mundosolar1995 têm de ser chamados pelo IP -69. Nenhum token ou segredo foi guardado em arquivo ou memória.
- **Anime Noturno:** 5 vídeos "não baixou" do Drive (rclone copyto); motivo NÃO investigado.
- **MS Energy:** 0 post hoje. A tarefa `MSEnergy_PostarFB` roda às 20:05; se continuar em 0, rodar na mão (`python postar_ms_energy.py --um --so fb`) antes da trava das 23h dela.
