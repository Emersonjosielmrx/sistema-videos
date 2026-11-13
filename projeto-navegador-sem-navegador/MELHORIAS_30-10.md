# Melhorias de 30/10 (revisão profunda) — registro de andamento

Backup do código antes das mudanças: `D:\projeto-navegador-sem-navegador_backup_20261030` (sem cookies/capturas/logs).

## Feito
- `core/arquivo.py` (novo): `gravar_json`/`gravar_texto` atômicos (tmp + replace, repete se o Windows prender o arquivo).
- `core/cofre_cookies.py`: gravação atômica + trava entre processos (`cofre_<perfil>.lock`); `salvar()` relê o arquivo
  dentro da trava e só grava os cookies que o servidor MUDOU nesta sessão (antes regravava todos e desfazia a rotação
  feita por outro processo); `ler()` repete se pegar o arquivo no meio de uma troca.
- `core/cdp_aba.py`: erro claro quando não há aba; `fechar()` não estoura se o Chrome já fechou; `with Aba(...)`.
- `core/maquinas.py`: `--maquina` sem nome dá mensagem em vez de IndexError.
- `tools/empacotar_worker.py`: inclui `core/arquivo.py`; confere antes de montar se todo import do projeto feito pelos
  arquivos do pacote está no pacote (antes só quebrava lá na máquina com ModuleNotFoundError).
- `services/youtube/upload_http.py`:
  - recusa ANTES de enviar o arquivo quando não há horário ou o horário já passou (< 5 min); confere de novo antes de
    agendar (envio longo podia passar do horário e o vídeo abriria na hora);
  - arquivo enviado em partes (antes lia o vídeo inteiro na RAM);
  - etapa final que dá timeout/5xx: relê o vídeo; se o Studio já mostra agendado, devolve o id (antes o postador caía
    no Chrome e subia um 2º vídeo no mesmo horário);
  - depois de agendar relê o vídeo (até 3x): público sem agenda volta para privado e falha; agenda que não pegou falha;
  - erro depois do vídeo criado leva o id do rascunho privado que sobrou na mensagem (vai para o youtube_http.log);
  - `LimiteDiario` (subclasse de RuntimeError) para o limite diário de envios;
  - `sincronizar` do youtube_http trocado só durante a construção do Studio (antes ficava trocado no processo todo);
  - cookies/token gravados atômicos; caminhos de outros projetos no FIM do sys.path; colher_sessao sem aba = erro
    claro, set copiado antes de iterar, corpo não-JSON do ars/grst não derruba.

- `services/instagram/postar.py` (Reel da produção):
  - etapa final (`configure_to_clips`): queda de rede não sai mais direto (o postador caía no Chrome e podia postar o
    Reel 2x) — repete com o mesmo upload_id; recusa de verdade (feedback_required/spam/login/checkpoint) para na hora
    em vez de insistir 30x por 4 min numa conta já marcada; o código do Reel só conta se vier dentro de `media`
    (formato real conferido em capturas/ig_reel.jsonl: `for (;;);{"payload":{"media":{"code":...}}}` e
    `payload.statusCode 202` = processando);
  - ffprobe que não lê o vídeo dá erro claro; capa temporária apagada mesmo com erro; carrossel valida sem `assert`;
    story sem `media` não estoura KeyError; CLI sem argumentos mostra o uso.
- `services/instagram/web.py`: uma linha cortada numa captura `ig_*.jsonl` derrubava todo post por HTTP (agora pula
  a linha); resposta HTML no lugar do JSON vira erro claro.
- `tests/test_offline.py` (novo, 24 testes sem rede): `python -m unittest tests.test_offline -v`.

- `services/veo_flow/flow_gerar.py` + `flow_http.py` (Veo/gera_imagem da produção):
  - resposta do StreamChat decodificada de uma vez (antes, byte a byte: acento/emoji partido virava "�" e o stream
    era lido de 1 em 1 byte); linha cortada no fim do stream não derruba mais um pedido já aceito (créditos gastos);
  - espera do download aguenta queda de rede até o prazo (antes 1 erro de conexão jogava fora um vídeo já pago);
  - download grava `.parcial` e só depois o nome final (o Veo nunca vê meio mp4); download vazio = erro;
  - conversa que o Flow não criou = recusa clara; erro ao fechar o Chrome não deixa a trava da porta presa;
  - `rpc()` com resposta ilegível vira recusa (ultimo_erro) em vez de traceback; cookies da saúde gravados atômicos.
  - Conferido ao vivo (só leitura): `saude_flow` responde igual ao código antigo (o 401 do GetCredits da
    fabricadeautomacoesia acontece também no backup — é da conta, não da mudança).
- `services/google_photos/fotos_http.py`: página meio carregada não dá AttributeError; item de formato estranho na busca
  é pulado (antes perdia a busca inteira); download atômico; resposta ilegível vira recusa.
- `services/youtube/studio_analytics.py` (metricas_rede da produção): coluna de métrica ausente (canal sem Shorts etc.)
  não dá mais KeyError. Conferido ao vivo na fiodameada (Shorts 13.199 impressões, tráfego, termos de busca).
- `tools/manter_cookies.py`: a rotação relê o arquivo na hora de gravar e só troca os cookies girados (antes podia
  gravar por cima de cookies que o postador acabou de renovar); gravação atômica. Rodado às 13:35: 17 vivos, 6 girados
  (igual às rodadas anteriores), nenhum .tmp sobrando.
- `tools/capturar_passivo.py`, `tools/capturar_rotacao.py`: cookies e token gravados atômicos.
- `tools/quero.py`: o id do comentário agora é comparado como texto (pk numérico nunca batia com a chave do JSON e a
  pessoa podia ser atendida de novo a cada rodada); 1 DM por pessoa por dia; `--maximo` (10) por rodada; para na hora
  se o Instagram bloquear (feedback_required/spam); sem link nenhum não manda DM vazia; estado gravado atômico.
- `legado/`: os `client.py` antigos, `core/auth.py`, `core/session.py` e os testes antigos (endpoints inventados,
  "SUCESSO TOTAL" falso) saíram do caminho e do pacote dos notebooks — nada da produção os importava (conferido com
  busca em postador, Veo, gera_imagem, maquina_remota). Ver `legado/LEIA.md`.

- `services/tiktok/studio.py`: lista de vídeos com `has_more` sem itens (ou cursor parado) entrava em laço infinito
  (a tarefa NSN_Inteligencia travava); página de bloqueio em HTML vira erro legível.
- `relatorios/inteligencia.py`: `contas_tiktok.json` (lido pelo painel :8790), o JSON do dia e o INTELIGENCIA.md
  gravados atômicos.
- `tools/empacotar_worker.py`: mensagem clara quando a pasta dist está presa por outro programa.
- `README.md` reescrito: o que está em produção (quem chama o quê), uso rápido, regras e testes (o antigo ensinava a
  usar os módulos inventados que foram para `legado/`).

### 2ª rodada (30/10 tarde)
- `tests/test_offline.py` relança sozinho com o python do `D:\veo\venv` (o `python` padrão do PC não tem websocket/
  curl_cffi) e `testar.cmd` roda de qualquer pasta/dois cliques.
- `services/instagram/seguir.py`: resposta 200 "ok" não é mais varrida por palavras — um @usuario com "spam" ou
  "challenge" no nome, numa lista de sugestões, pausava a conta 48 h à toa; HTML de login vira erro, não "bloqueio";
  estado gravado atômico.
- `services/google_photos/catalogo_visao.py`: miniatura que não veio (403/HTML) não vai mais para a IA de visão;
  conexões do SQLite fechadas (`por_tag` abria uma nova a cada chamada).
- `tools/colher_notebooks.py`: erro numa conta não pula as outras da máquina; a vez da máquina é renovada a cada conta
  (com muitas contas a reserva de 15 min vencia no meio e o Veo abria outro Chrome junto) e, se outro pegou a vez,
  para naquela máquina.
- `tools/monitor_banimento.py`: se o `tetos.json` for mexido (à mão) durante a rodada, não grava por cima — a próxima
  rodada refaz. Testado com `--seco`.
- `tools/saude.py`: Flow sem créditos lidos aparece "logado (créditos não lidos)" em vez de "créditos None".
- 33 testes offline.

### 3ª rodada
- `core/cdp_aba.py` (usado pelo Flow, ouvinte passivo, colher_sessao, colher.py dos notebooks): a conexão com a aba
  tem prazo de 60 s no `recv`; 60 s sem evento (ex.: Flow gerando por HTTP) eram tratados como "aba fechada" e a
  thread de leitura morria — toda chamada seguinte (outro token, estender, corrigir) falhava "sem resposta". Agora o
  silêncio é ignorado; aba fechada de verdade dá "a aba fechou". Envio protegido por trava (ouvinte e principal
  mandavam juntos) e resposta que chega depois do prazo não fica acumulada.
- `services/instagram/web.py`: modelos das consultas em cache (`capturas/_modelos_ig_cache.json`), refeito só quando
  uma captura `ig_*.jsonl` muda (0,5 s → 0,01 s a cada abertura).
- `D:\gemini-argo\youtube_http.py` NÃO mexido: outra sessão já pôs gravação atômica nele hoje (12:39).
- 35 testes offline; worker reinstalado nas 3 máquinas.

### 4ª rodada (dona: "Sim, faça") — ritmo do Instagram, no postador da produção
`D:\postador-de-videos\bin\postar_insta_auto.py` (cópia antes da mudança: `postar_insta_auto.py.bak_20261030`):
- no máximo **1 Reel por conta em cada rodada** (`max_por_rodada_conta`, padrão 1) e **60 min entre dois Reels da
  mesma conta** (`intervalo_conta_min`, padrão 60) — os dois vão em `config\reuso_plataformas.json` → `instagram`
  se quiser mudar. Antes a rodada postava o teto do dia inteiro de uma vez, 60 s entre eles. O teto diário (tetos.json
  / max_dia) continua valendo; o total do dia agora também depende de quantas rodadas rodam.
- **pausa automática**: resposta "This user is inactive"/"cannot upload" = 7 dias; feedback_required, checkpoint,
  challenge, "Limitamos a frequência" = 48 h. Grava `config\instagram_pausas.json` e avisa no Telegram; a rodada pula
  a conta pausada. Para voltar antes: apagar a linha da conta nesse arquivo.
- nesses bloqueios **não tenta mais pelo Chrome** (antes: HTTP falhava → Chrome tentava de novo na mesma conta).
- **landingpageia.ia e jornalcomia pausadas até 06/11 14:44** (inativas desde 29–30/10).
- Testado sem postar (funções de bloqueio, pausa, último post e o desvio do Chrome); a próxima rodada da produção é a
  1ª prova real — no `logs\instagram_auto.log` aparecem "em pausa até ..." e "espera 60 min entre Reels".

### 5ª rodada (30/10 noite, no DESKTOP — cópia do pc1 trazida às ~18:50)
Conferência dos logs da produção do pc1 (só leitura, cópias em `%TEMP%\logs_pc1_nsn`):
- YouTube: `upload_http` novo sobe e agenda (ex.: 15:00–18:03, forjareact, cenareact, fiodameada, gamenoturno...).
  Nenhum "PÚBLICO sem agendamento" nem "já passou". Falhas que vão para o Chrome: `sem SAPISID` (manhwanoturno,
  inovaremanhwabr, inventoreact, filmenoturno: deslogados no cofre), inovare_hindi "Muitos avisos" (advertências da
  comunidade, 8x no dia — o postador continua tentando) e dois 403 no `metadata_update`.
- O 403 do forjareact às 15:53:02 foi um 2º processo do mesmo canal ao mesmo tempo (vídeo longo 9TclD-ENfSo subiu
  15:53:00; o short caiu no Chrome e subiu dSVU21_X5y8 às 15:56 — `uploads_ledger.jsonl`): não houve duplicata.
- Instagram: a rodada das 15:48 já roda o código novo — "em pausa até 06/11 14:44" para jornalcomia e
  landingpageia.ia, 1 Reel por conta (nenhuma conta repetida). A rodada foi encerrada às 17:18 pelo limite de
  90 min do `etapa.py` (contas depois da inovaresites ficaram para a próxima).
- Flow pelos notebooks depois das 14:00: maioria ok. Erros vistos: reCAPTCHA não carregou (pc2: jornalcomia,
  inovaremanhwaversethai, gabriellyvitoriaisabelaaraujo), PUBLIC_ERROR_UNUSUAL_ACTIVITY, upload `[3]` de
  `*_parceiro_P-djtsSY2Co.jpg` (18:08–18:29, a mesma imagem em 5 contas) e `window.__nsnOrig is not a function` (pc2 15:27).

Correção:
- `services/youtube/upload_http.py`: quando dá erro depois do vídeo criado, o rastro "[rascunho privado X ficou no
  canal]" vai NA FRENTE da mensagem, e o corpo de erro do `_yt` fica numa linha só (300 caracteres). Antes o 403
  indentado ocupava os 300 caracteres que o `_subir_http` grava e o id do rascunho nunca chegava ao `youtube_http.log`.
  Teste `test_rascunho_aparece_no_log_cortado` (36 testes). Não vai no pacote dos notebooks.

### 6ª rodada (31/10, DESKTOP) — "Muitos avisos" vira espera de 24 h (produção no pc1)
Pendência do PROMPT_CONTINUAR ("Muitos avisos" fazia o HTTP cair no Chrome, que bate no mesmo bloqueio). Em
`D:\postador-de-videos\bin` (produção, mandado por scp ao pc1 com `.bak_20261031_muitos_avisos`):
- `politica.py`: `eh_advertencias(texto)` reconhece só o bloqueio de ENVIO por diretrizes da comunidade
  ("Muitos avisos" / "many warnings" + "não é possível enviar"/"community guidelines"); NÃO confunde com erro
  genérico nem com advertência de direitos autorais do conteúdo. `marcar_advertencias`/`em_advertencias` guardam
  espera de 24 h por canal em `config\advertencias_upload.json` (não renova o contador a cada checagem, igual ao
  conserto do limite_diario de 30/10). `checar_upload` e `postar_youtube` vetam ANTES de abrir qualquer poster;
  `classificar_erro` devolve `advertencias`; `tratar_erro` marca a espera.
- `youtube_web_poster.py`: o caminho HTTP (navegador sem navegador) para no aviso e NÃO cai no Chrome
  (levanta `Falha("advertencias")`); o caminho Chrome também reconhece o aviso no diálogo; STATUS mapeado.
- `youtube_poster.py` e `postar_tudo_multiplataforma.py`: status `advertencias` mapeado/encaminhado.
- Teste novo permanente `bin/test_advertencias.py` (11 testes OFFLINE: classificação, cooldown de 24 h sem renovar,
  veto antes do poster, mapas de STATUS, e o caminho HTTP parando no aviso com Enviador simulado — sem Chrome/rede).
  `python bin/test_advertencias.py` = 11 OK no pc1 (e no desktop). py_compile OK nos 4 arquivos.
- LIÇÃO: `D:\postador-de-videos\bin` é espelhado do pc1 (1 h); editar no desktop é revertido. O pc1 é a fonte:
  editar → scp pro pc1 → validar NO pc1.

### 7ª rodada (01/11, DESKTOP) — LimiteDiario do YouTube não cai mais no Chrome
Verificação da produção do pc1 (só leitura): o bloqueio "Muitos avisos" está segurando — `config\advertencias_upload.json`
tem inovare_hindi + 1 canal em espera; os logs mostram a virada em 31/10 09:11 ("HTTP recusado... não tenta pelo Chrome")
e hoje nenhuma nova tentativa desses canais. `test_advertencias` 11 OK e `test_offline` (nsn) 36 OK no pc1.
- `youtube_web_poster._subir_http`: quando o `upload_http` levanta `LimiteDiario` (canal sem telefone no limite do dia),
  para e devolve `Falha("limite")` em vez de cair no Chrome (que bate no MESMO limite da conta). O `postar_youtube` já
  marca a espera de 24 h nesse status. Direto da lista pendente do PROMPT_CONTINUAR; alinhado à regra da dona
  ("deu aviso de 24 h, esperar, não ficar tentando"). Teste `test_http_limite_diario_nao_cai_no_chrome` (12 OK no pc1).
  Mandado ao pc1 por scp com `.bak_20261101_limitediario`.

### 8ª rodada (01/11, DESKTOP) — token do ouvinte passivo no canal certo
Verificação da produção (pc1, só leitura): bloqueio "Muitos avisos" holding (advertencias_upload.json inalterado,
sem re-marcar); nenhuma recusa/limite nova hoje; uploads HTTP normais. `test_advertencias` 12 OK, `test_offline` 36 OK.
- `tools/capturar_passivo.py`: o token (`sessionInfo.token`) era atribuído ao canal pela URL da ABA
  (`self.alvo["url"]`), que o laço só atualiza a cada ~2 s. Se a mesma aba do Studio trocava de canal e o token novo
  chegava antes dessa atualização, ele ia pro `cookies\yt_sessao_<slug>.json` do canal ERRADO (suspeita do
  PROMPT_CONTINUAR, agora confirmada no código). Correção: usar o `documentURL` do PRÓPRIO evento
  `Network.requestWillBeSent` (a URL do frame que emitiu o token), com fallback pra url da aba. Impacto limitado
  (token errado só faria o upload_http renovar), mas evita gravar sobre o token bom de outro canal.
  Teste `TestCapturaTokenCanalCerto.test_token_usa_documenturl_do_pedido` (37 OK no pc1). `.bak_20261101_documenturl`.

## Achado para a dona (não é código)
- **Instagram em rajada (29/10):** pelo `logs/instagram_postagens.jsonl`, 11 contas postaram 5 a 8 Reels em menos de
  30 min no dia 29 (landingpageia.ia: 10 no dia, 8 em 30 min; gestaodegrupos.ia 8; mentoriasia.ia 7; agentesdeia,
  crmchatwoot, disparoemmassa, fabricademarketing, followupia, superchatia, vpsblindada: 5 cada). Em 30/10 a
  landingpageia.ia e a jornalcomia respondem "This user is inactive so they cannot upload" e a produção continua
  tentando (HTTP e depois Chrome) a cada rodada. Não mexi no ritmo de postagem (é regra da produção/tetos, decisão
  da dona); sugestão: intervalo mínimo entre Reels da mesma conta no `postar_insta_auto` e pausar as contas inativas.
- **YouTube limite diário:** historiasemframes e inovare_ind deram "limite diário de envios" (telefone não
  verificado) no HTTP e caíram no Chrome, que bate no mesmo limite. O `upload_http` agora levanta `LimiteDiario`;
  o `_subir_http` do postador poderia pular o Chrome nesse caso (não mexi no postador).
- 13 canais do YouTube com cookie HTTP morto em 30/10 13:35 (assistiainvestimentos, cenareact, curiosidadesnoturnas,
  historiasemframes, inovare_ind, inovare_ita, inovare_ru, inovare_thai, inovaremanhwabr, inventoreact,
  manhwanoturno, manhwareact, mundoquenaoexiste): esses sobem pelo Chrome (ou o upload_http colhe na hora).

## Instalação nas máquinas
- PC1: a produção já usa o código novo direto desta pasta.
- x200ma, acer, pc2: instalados ~14h com `maquina_remota.py instalar-nsn <maq>` — "x200ma: nsn ok 56 cookies",
  "acer: nsn ok 52 cookies", "pc2: nsn ok 57 cookies" (o "nsn ok" é o import do postar.py e do flow_gerar.py lá;
  os cookies de cada máquina foram preservados).
- desktop: NÃO instalado — o ssh dele derruba as conexões (IMPLANTAR_MAQUINA.md §7); insistir piora.
