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

## Monetização (aba do Business Suite, 20/11)
- MS energy: qualificada em Monetização de conteúdo, Estrelas e Assinaturas — falta a dona aceitar os termos e
  cadastrar a conta de pagamento.
- Páginas novas: Estrelas = 500 seguidores por 30 dias; Assinaturas = 5.000 seguidores.
