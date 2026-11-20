# Facebook sem navegador (começado 20/11/2026)

Pedido da dona (20/11): "vamos tentar fazer o navegador sem navegador no Facebook, que hoje fazemos pelo navegador".
Mesmo padrão do Gemini/Flow/Fish: o Chrome da conta só COLHE os cookies; o resto é HTTP pela saída fixa da conta.

## Feito e testado (20/11)

| Peça | Arquivo | Resultado |
|---|---|---|
| Sessão HTTP | `services\facebook\sessao.py` | home logada em 2,8 s; `fb_dtsg` + `lsd` no HTML; pela saída da conta (`rnprmtfo-58` / casa) |
| "Entrar como" a Página | `Sessao.como(page_id)` | troca o cookie `i_user`; a home passa a dizer USER_ID/NAME da Página. Substitui `fb_entrar_como.py` |
| Ler Página | `services\facebook\paginas.py` | seguidores + reels + views (`play_count_reduced`) + asset_id só com GET (~5 s) |
| Conferir config | `python -m services.facebook.paginas conferir <conta>` | age como cada Página e confere o asset_id (5 Páginas em 27 s). Substitui `fb_page_id`/`fb_ativos` |
| Medir todas | `services\facebook\medir.py` | 6 Páginas / 2 contas em 10,7 s, mesmo `fb_views.jsonl` + relatório do `fb_medir.py` (Chrome levava ~2 min) |

- **Ligado na produção:** `cron_facebook_inteligencia.bat` (tarefa FacebookInteligencia 08:30) mede por HTTP; só se
  não medir nenhuma Página cai no `fb_medir.py` com Chrome. Voltar ao antigo: `.bak_antes_http_20nov`.
- Cookies colhidos: `c_user` + `xs` (login), `i_user` (ator), `datr`, `fr`, `sb`, `ps_l/ps_n`, `wd`, `dbln`. Ficam em
  `cookies\fb_<conta>.json` (cada máquina colhe os seus; nunca copiar). O `i_user` do arquivo não é sobrescrito pelas
  trocas de Página da sessão HTTP.
- Números batem com o Chrome: Anime Noturno 220/204 views por HTTP x 220/203 no Chrome às 09:53.
- Monetização: `business.facebook.com/latest/monetization?asset_id=` abre por HTTP (200, 1 MB) e traz alguns sinais
  (`is_page_onboarded_to_unified_payout_program`...); os requisitos detalhados vêm por GraphQL depois — `fb_monetizacao`
  é consulta manual, ficou como está.

## Falta

### 1. POSTAR o Reel por HTTP (prioridade)
- Regra: nada de post de teste em Página real. Captura passiva (só ouve, não clica) das postagens REAIS de hoje:
  - `NSN_CapturaFB_1515` (15:15, 40 min): Cena React posta ~15:20 (msenergypara).
  - `NSN_CapturaFB_2055` (20:55, 105 min): as 5 Páginas da emersonjosiel02 no horário nobre (21–22 h).
  - Saída: `capturas\passivo_facebook_20261120.jsonl`.
- Às 12:20 NENHUMA Página postava (`--horario`: 2 de 3 feitos de madrugada, o 3º guardado para o nobre).
- Esperado (confirmar na captura, NADA inventado): upload do arquivo (rupload/vupload) + GraphQL de publicar o Reel no
  Business Suite (`business.facebook.com/api/graphql/` com `doc_id`), com `av`=<Página> e `fb_dtsg`.

### 2. Criar Página (deixado por último, de propósito)
- Captura passiva das criações reais: `NSN_CapturaFB_criar_1337`, `_1637`, `_1937` (45 min cada).
- Risco: criar Página é a ação que o Facebook mais vigia; perfil novo já está no limite (2–3/dia). Só converter depois
  que a postagem por HTTP rodar alguns dias sem aviso. Foto e capa da Página vêm junto (upload de imagem).

### 3. Listar Páginas da conta
- A lista do menu "Ver todos os perfis" carrega por GraphQL (não vem na home). Hoje a config já tem os ids, e o
  `conferir` confere cada um — basta para a produção. Capturar o doc_id se precisar listar páginas desconhecidas.

## Achados no caminho (20/11)
- 11:05 `postar_ms_energy.py --so fb` (MS Energy, cliente) falhou 2x: clique com tempo esgotado e depois
  `connect_over_cdp ECONNREFUSED 127.0.0.1:9401` — o Chrome do perfil msenergypara não abriu a porta. Intermitente: às
  12:18 a colheita pelo mesmo Chrome funcionou (48 s). Postar por HTTP elimina esse Chrome.
- Outro chat (Claude Code, 12:11) rodou `services.facebook.medir cenareact` — o módulo já está em uso fora deste chat.
  Avisos por SendMessage aos chats ocupados ficaram retidos (outro modo de permissão).

## Tarefas temporárias a apagar depois
`NSN_CapturaFB_1515`, `NSN_CapturaFB_2055`, `NSN_CapturaFB_criar_1337`, `NSN_CapturaFB_criar_1637`,
`NSN_CapturaFB_criar_1937` (todas "Once"; depois de rodar ficam paradas — apagar com Unregister-ScheduledTask).
