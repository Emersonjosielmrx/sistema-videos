# Bots novos do Telegram (dono, 22/10/2026)

## FEITO 23/10 ~10h (itens 1–8, testados com estado temporário e envio falso)
- 1/2 disco: avisos.py INCIDENTES — 2º aviso do mesmo problema (qualquer robô) = "mesmo problema" no log, não sai;
  texto com CONSERTEI/voltou ao normal fecha; `fechar_incidentes()` (chamado no despachar_resumo, ~28 min) manda
  "✅ Disco voltou ao normal" quando o D: tem >= 8 GB. Disco do C:/PC2 fica fora (sem checagem automática).
- 2 contas com problema: notificar_telegram.checar_logs guarda `contas_abertas`; `_conta_voltou` olha TikTok/Insta
  postados e o ledger do YouTube -> "✅ Contas que voltaram a postar". Veo deslogada/sem crédito: some em 7 dias sem aviso.
- 2/3 monitor do anime: janela 3 h, linha sem data herda a data de cima, WARNING/INFO não conta, mesmo erro (sem os
  números) só 1 vez (`erros_avisados` no estado), "✅ Vídeos de anime voltaram ao normal" quando o tipo some.
- 4/6 avisos._silencioso: 0h–6h59 e origem "no ar" saem com disable_notification (texto e arquivo).
- 5 postagens: 1 lista por resumo (avisos.resumo_devido() no notificar_telegram, antes do despachar_resumo), YouTube
  canal+título+link, TikTok/Insta/MS Energy contagem por conta. Saiu de avisos_projetos.
- 7 Short repetido: 1 msg por canal; já avisados em postador config\avisos_studio_duplicados.json (semeado com 23).
- 8 ROTA: "vigia mútuo"->producao, "tiktok notebooks"->pendencias_humanas; origem fora da ROTA e de
  GERAL_DE_PROPOSITO vira 1 item "Aviso novo sem bot próprio" no resumo do geral.
23/10 ~11h também FEITO: 10 (avisos.TECNICO refaz com o 2º modelo), 13 (resumo que falha volta pra fila),
16 (os 2 leitores antigos do bot geral saem na hora), 14 verificado (trava existe). Comentários do Inovare Manga ind
(403) agora lidos pelo Studio (postador config\comentarios_pelo_studio.json). Falta: 9 (comentários num bot só),
11 (código do TikTok no notebook automático), 12 (int_produto — dono), 15 (botões).

## Análise de melhorias (23/10 ~10h, log estado\avisos.jsonl 24 h)
Volume 24 h: postagem 49 (no ar 43), bloqueios 23 (+18 segurados), producao 23 (monitor do anime 13 + 57 segurados),
metricas 11, aprendizado 10, opus 9, resumos 8, pendencias 4, geral 4. ~40 notificações entre 0h e 7h.
1. Mesmo problema por vários robôs: disco cheio = 6 msgs (hipercool 4 + monitor do anime 2). Agrupar por incidente.
2. Falta "voltou ao normal" (prioridade do dono: quebrou/consertou): disco, monitor do anime, contas com problema.
3. monitor do anime re-avisa linha velha de log (disco cheio já resolvido; WARNING de legenda 429 nem é erro).
   Guardar a última linha vista por arquivo; ignorar WARNING.
4. Madrugada: mandar com disable_notification (sem tocar) 0h–7h, exceto urgente; aprendizado (9 msgs+vídeos à 1h) de manhã.
5. Resumo de postagens: guarda só os 8 últimos blocos de 30 min ("... e mais N") e fica enorme. Trocar por contagem por
   canal/rede + links só do YouTube.
6. "No ar" 43/dia tocando: silencioso ou em bloco.
7. Short repetido: 1 msg por vídeo (CartuchoReact 3 em 2 min) -> 1 por canal por rodada.
8. Origens novas caem no geral sem ninguém saber: "tiktok notebooks" (-> pendencias_humanas), "vigia mútuo" (-> producao).
   Regra: origem fora da ROTA aparece no resumo como "sem bot".
9. Comentários divididos: API -> bot geral (enviar direto), Studio -> bot comentarios. Juntar (1 leitor por bot!
   bots_conversa já lê o comentarios).
10. Texto simplificado ainda vaza jargão ("O que fazer: REVISAR", "parceiro_postar.log: KeyError") e às vezes inventa ação.
    Conferir a saída (palavra técnica -> refaz/usa glossário).
11. tiktok_notebooks pede ao dono copiar código do Gmail; o sistema já lê código no Gmail (tiktok_login_google) -> automatizar.
12. int_produto parado; msenergy-clientes no geral.
13. Resumo some se o envio falhar (itens apagados antes de mandar) -> apagar só depois do envio.
14. bots_conversa: 1 PermissionError no estado (22/10 23:31) — conferir trava contra 2 cópias (vigia relança a cada 20 min, roda 39).
15. Botões nos avisos (Ver no Studio / Já resolvi / Silenciar 24 h).
16. monitor_opus_telegram.py e ms-energy\bin\telegram_monitor.py leem o bot GERAL (token 8740…); hoje parados e sem
    agendamento — se alguém rodar, roubam mensagens do notificar_telegram. Tirar de uso.
O que os bots mostraram (problema de produção, não dos bots): limite diário em Dicas financeiras, ForjaReact,
Curiosidades Noturnas, Fio da Meada; rajadas de 3+ vídeos em <1 h de madrugada (Dorama, Filme, Game Noturno) e o
YouTube barrou o ManhwaReact 06:28 por excesso.

Status: **FEITO em 22/10 (~20h) para 4 bots** — `bloqueios`, `metricas`, `pendencias_humanas`, `producao`.
**Falta só `integracao_produto`:** desligado até o dono dizer para que é (proposta: MS Energy). Para ligar, pôr
`msenergy-clientes`/`msenergy-carrossel` (ou o que o dono disser) na `ROTA` do avisos.py e `em_uso: true` no JSON.

O que foi feito (22/10):
- `ROTA` (avisos.py) com todas as origens da tabela abaixo + `rampa de canais` → `postagem`.
- `despachar_resumo` manda **um resumo por bot** (origem fora da ROTA = bot geral); o log grava
  `resumo enviado|falhou "<bot>: N itens"` por bot.
- Inscritos com `chave` única nos dois lugares: notificar_telegram.py (`avisar(..., chave=)`, agora passa pelo
  portão) e **sem_token.py** — este já estava no portão sem chave e em 21/10 o portão escondeu 5 avisos de inscrito
  como "repetido" (Esporte Noturno 3×, Filme Noturno, Bicho Noturno).
- Testado: simulação isolada (rota, inscritos, resumo separado) + 1 mensagem real em cada bot (`_mandar`), todas
  entregues pelo bot certo, nenhuma caiu no geral.
- Respostas: o dono responder um alerta nos bots novos **não** chega ao vigia (só o bot geral é lido). Medido:
  0 respostas a alertas desde 18/10 (vigia_perguntas_feitas.jsonl), então nada em uso quebrou. Comandos soltos
  ("status", "opus") e respostas a comentários continuam no bot geral.
- Processo já aberto antes da mudança (painel :8790) segue com a rota antiga até reiniciar.

## Como funciona hoje

- Portão único: `D:\video-fila\avisos.py`. `enviar(texto, origem, importante)` escolhe o bot pela tabela
  `ROTA` (linha 45): origem → chave em `telegram_bots.json`. Origem fora da ROTA = bot geral (`telegram.json`).
- `importante=True` sai na hora; `importante=False` vai para o **resumo** das 9h/14h/21h.
- Bot sem "Iniciar" do dono cai no bot geral (`_SEM_CHAT`), então ligar um bot nunca perde aviso.

## Bots e o que cada um recebe

| Bot (chave no JSON) | @ | Origens (texto exato do 2º argumento de `enviar`) | Onde nasce |
|---|---|---|---|
| `bloqueios` | @bloqueios_emerson_bot | `studio` | postador-de-videos\bin\avisos_studio.py:119 |
| `metricas` | @metricas_emerson_bot | `inscritos` | postador-de-videos\bin\sem_token.py:66 **e** notificar_telegram.py:267 (ver armadilha 2) |
| | | `mil views` | postador-de-videos\bin\notificar_telegram.py:276 |
| | | `tiktok-views` | postador-de-videos\bin\medir_tiktok.py:132 |
| | | `msenergy-metricas` | ms-energy\bin\metricas_insta.py:226 |
| `pendencias_humanas` | @pend_humanas_emerson_bot | `contas com problema` | postador-de-videos\bin\notificar_telegram.py:681 |
| | | `checar_canais` | postador-de-videos\bin\checar_canais_diario.py:123 e 127 |
| | | `trechos_noite` | video-fila\trechos_noite.py:83 |
| `producao` | @producao_emerson_bot | `hipercool`, `manhwa-react`, `historias`, `recapd`, `veo`, `vídeos` | nome montado pela pasta em `notificar.py:30` (PREFIXO) e `_tg_safe.py:63` (ORIGEM) — cópias COMUM em hipercool-materiais\comum, hipercool-videos\bin, manhwa-react\mr, recapd-ambientes\producao\bin, historias-em-frames\bin, postador-de-videos\bin |
| | | `monitor do anime` | recapd-ambientes\producao\bin\anime_health_monitor.py:104 |
| | | `revisão do anime` | recapd-ambientes\producao\bin\anime_revisao.py:72 |
| | | `produção do parceiro` | recapd-ambientes\producao\bin\parceiro_diario.py:466 |
| | | `guarda de testes` | video-fila\guarda_testes.py:151 |
| | | `vigia de melhorias` | postador-de-videos\bin\vigia_melhorias.py:65 |
| | | `painel ia` | video-fila\painel_ia.py:658 |
| `integracao_produto` | @int_produto_emerson_bot | `msenergy-clientes`, `msenergy-carrossel` | ms-energy\bin\vigia_clientes_insta.py:153, carrossel_ms.py:372 |

Já ligados (não mexer): `postagem` (postagens, filas de postagem, ritmo de postagem, postador, no ar),
`comentarios`, `aprendizado`, `opus`. **Acrescentar `rampa de canais` → `postagem`** (rampa_canais.py:137).

`vigia_trader` (@vigia_emerson_bot) é do robô de investimentos (trader_binance\vigia\vigia_externo.py:157).
Não pôr origem de vídeo nele.

**A confirmar com o dono antes de ligar:** `integracao_produto` — o nome "int_produto" é ambíguo; a proposta
é MS Energy (produto real, clientes no Insta). Se o dono não responder, ligar os outros 4 e deixar este parado.
`origem "postador"` vem de duas fontes (rotina do notificar_telegram e o PREFIXO do notificar.py dentro de
postador-de-videos); as duas continuam no bot `postagem`, está certo.

Volume no dia 22/10 (log `estado\avisos.jsonl`, 24 h): no ar 44, studio 38 enviados + 14 repetidos,
hipercool 6 na hora + 39 no resumo, postagens 38 no resumo, monitor do anime 7 + 16 repetidos, inscritos 4.

## Passos

1. **ROTA** (avisos.py:45): acrescentar cada origem da tabela com a chave do bot. Só isso já leva para o bot
   certo tudo o que é `importante=True`.
2. **Resumo por bot** (`despachar_resumo`, avisos.py:222): hoje junta tudo e manda no bot geral
   (`_mandar("\n".join(partes))` sem origem). Separar os itens por `ROTA.get(origem)` e mandar **um resumo por
   bot**. Sem isso `mil views`, `tiktok-views`, `msenergy-metricas`, `hipercool` (rotina) etc. continuam
   caindo no bot geral. `_mandar` escolhe o bot pela origem: passar uma origem do grupo ou mudar para receber
   a chave do bot. Manter "uma vez por horário" (`ultimo_resumo`).
3. **Inscritos** do notificar_telegram.py:267 saem por `enviar()` direto (bot geral), fora do portão.
   Trocar por `avisar(..., "inscritos", importante=True)` **com `chave` única** (ex.: `f"inscritos:{slug}:{total}"`).
   Sem chave única o portão tira os números do texto e trata "+1 inscrito em X (agora 16)" e "(agora 17)" como
   repetidos por 12 h — o dono perde inscrito, que é prioridade dele.
4. Testar (seção abaixo). Trocar `em_uso` para `true` no JSON.

## Armadilhas

1. **Comentários do notificar_telegram.py:239 ficam no bot geral.** O dono responde o comentário dando
   "responder" no Telegram, e `responder()` (notificar_telegram.py:390) só lê o `getUpdates` do bot geral.
   Mover para outro bot quebra a resposta ao YouTube. Só mover se também ler o `getUpdates` do bot novo,
   como `_responder_aprendizado` (linha 369) já faz, com offset próprio no estado.
2. Mesmo cuidado com qualquer aviso que espera resposta do dono (SIM/NÃO, reply).
3. `notificar.py` e `_tg_safe.py` são **COMUM** (cópia "# COMUM"): não precisa mexer neles, a rota é toda no
   avisos.py. Se mexer, editar em hipercool-materiais\comum e rodar `recursos.py subir`.
4. Não mandar direto pela API fora do portão: perde o filtro de repetidos e o registro.
5. Memória `feedback_telegram_avisos.md`: na hora só inscritos/comentários/vigia/erro; rotina vai pro resumo.
   Separar por bot **não** muda o que é importante ou rotina.

## Como provar que funcionou

- `python D:\video-fila\avisos.py` antes e 24 h depois: contagem por origem e situação.
- Para cada bot novo, um aviso de teste pelo portão com `importante=True` e `chave` de teste
  (ex.: `avisos.enviar("teste de rota: bloqueios", "studio", importante=True, chave="<SEGREDO_REMOVIDO>")`)
  e conferir que chegou no bot certo (`message_id` devolvido + o dono ver). Avisar o dono antes: são 5 mensagens.
- `python avisos.py resumo` força o resumo: devem sair resumos separados, um em cada bot que tiver item.
- Depois de 24 h, no bot geral só pode sobrar o que não está na tabela.
