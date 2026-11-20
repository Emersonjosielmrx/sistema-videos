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

## Monetização (aba do Business Suite, 20/11)
- MS energy: qualificada em Monetização de conteúdo, Estrelas e Assinaturas — falta a dona aceitar os termos e
  cadastrar a conta de pagamento.
- Páginas novas: Estrelas = 500 seguidores por 30 dias; Assinaturas = 5.000 seguidores.
