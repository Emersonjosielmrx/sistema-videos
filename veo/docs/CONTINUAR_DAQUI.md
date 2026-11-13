# Continuar daqui — Veo (parado em 16/10/2026, a pedido da dona)

## 0. CADEIA DE ALTERNATIVAS e CONTROLE DE CRÉDITOS (23/10/2026, ~23:00) — vale acima do resto

**Pedido da dona (23/10):** "pra ter uma ordem de fallbacks do Veo, justamente pra não ter como dar errado em todos,
algum vai fazer". Ordem das máquinas, nas palavras dela: "a ordem é primeiro os notebooks, depois o desktop se não
tiver rodando chamada, nem chamada, e depois o PC2 ou o 1, dependendo de qual está mais desocupado". Créditos: "se a
conta tiver sem crédito, é só trocar de conta e não de máquina; tem que ter um controle de créditos das contas, um
gerenciamento; se a conta está com menos de 20 créditos, já não faz mais naquele dia, passa pra outra". Telão: "o Veo
também não pode fazer se tiver exibindo um vídeo [...] a regra é limpar RAM e deletar processos desnecessários antes de
fazer qualquer ação, como vídeo Veo ou exibição".

**Por que:** de 18:52 a ~22:40 de 23/10 o Veo não gerou nada. O PC1 estava em pausa de carga (só notebooks), o x200ma
falhava ao abrir o Chrome ("não abriu a porta de controle", ~7 min por vez), o Acer estava com o login do TikTok, e a
cada ciclo o prompt voltava pra fila e o ciclo ABORTAVA. Contas paradas também: seebotsia/mundosolar/canalalucinaai
seguiam EXHAUSTED desde 00:05 de 23/10 porque o saldo "não dava pra reler" daqui e nunca eram liberadas.

**A cadeia, em ordem, a cada ciclo** (`beta\cadeia_veo.py`, montada antes de gastar LLM com prompt):

| # | Etapa | Entra se | Fica de fora se |
|---|---|---|---|
| 0 | (pausas) | pausa de **carga** = só tira o PC1 | pausa **manual** da dona ou de **bloqueio**: o ciclo para, nada é furado |
| 1 | **notebooks** (x200ma, acer) | Chrome livre (`maquina_remota.maquina_livre`) e o telão **não está tocando vídeo** lá | outro Chrome aberto (postagem/login do TikTok), exibindo vídeo (`vitrine/player.py`), sem resposta, ou de castigo |
| 2 | **desktop** | `D:\video-fila\maquinas.py medir("desktop")` diz ocioso: sem OBS, microfone/câmera livres, botão do painel ligado | em chamada/gravando, Chrome ocupado, sem resposta, castigo |
| 3 | **PC2 ou PC1**, o de **mais RAM livre** (mesma medição) | PC2: só com conta do Flow logada lá (hoje **nenhuma**). PC1: sem pausa de carga, com RAM p/ 1 Chrome (`recursos.slots_por_recurso`) e ocioso pela medição | PC1 em carga/sem RAM; PC2 sem conta, com render cheio ou castigo |
| 4 | **nenhuma serve** | — | prompt fica na fila; passou de **3 h** (`VEO_AVISO_H`) sem vídeo = **1 aviso** à dona (Telegram pelo `D:\video-fila\avisos.py`, origem `veo`, + pop-up) com o motivo exato; zera no próximo vídeo (`logs\veo_sem_alternativa.json`) |

**Dentro de cada etapa** (troca de CONTA, não de máquina): contas que rodam naquelas máquinas
(`cadeia_veo.maquinas_da_conta`), a de **mais crédito** primeiro, empate = a que renova antes, saldo ainda desconhecido
depois. Sem crédito → marca e vai pra próxima conta da MESMA etapa. Só muda de etapa quando nenhuma conta da etapa serve
ou as máquinas falharam na hora de abrir (nada pedido ao Flow = não conta tentativa nem castiga a conta).

**Castigo de máquina** (`logs\maquinas_veo.json`, lido da saída do worker): "FALHOU" 30 min, "não respondeu" 20 min,
"OCUPADO" 5 min. **Conta:** Flow "age-restricted" = fora 72 h; deslogada em todas as máquinas = fora 6 h (sem tentar
"relogar": nunca mexemos em login/senha); conta remota nunca cai pro Chrome do PC1 (`VEO_SO_NOTEBOOK=1`).

**Reserva:** no começo do ciclo os notebooks/desktop ficam reservados 12 min (`notebooks_reservados.json`, por "veo")
e, durante a geração, a máquina da etapa fica reservada pelo tempo todo (timeout + 5 min) e é solta no fim.

**Controle de créditos** (`beta\creditos_contas.py`, estado `logs\creditos_contas.json`): por conta `saldo`, `lido_em`,
`renova_em`, `gasto_hoje`, `videos_hoje`. O saldo vem do próprio worker (ele já lê o menu da conta ao abrir o Flow:
"saldo lido no menu de conta: N" — nada a mais é aberto); vídeo que saiu desconta `VEO_CUSTO_VIDEO` (20, marcado
"estimado"); **saldo < `VEO_CREDITO_MINIMO` (20) = fora até a renovação** (meia-noite + 5 min). O worker usa o mesmo
mínimo. Uma linha por dia vai pro resumo de avisos: "Créditos Veo: ... (N fora)". Conta EXHAUSTED cujo saldo não dá
pra reler daqui é liberada depois da renovação (o worker confere o saldo antes de gerar e sai sem gastar).

**Teste a seco:** `D:\veo\venv\Scripts\python.exe -X utf8 beta\teste_cadeia_a_seco.py` (10 cenários: PC1 em carga,
notebook ocupado/exibindo, desktop em chamada, sem crédito, deslogada, máquina falhando na hora de abrir, todas < 20,
nada por 4 h, pausa manual, pausa de bloqueio). Não gera, não gasta crédito, não usa ssh; estado em pasta temporária.
Backups: `cron_gerar_video_llm.py.bak_20261023_fallback`, `gera_auto.py.bak_20261023_fallback`.

**Falta (fora do Veo, outras sessões — não editei):**
1. `D:\video-fila\vitrine.py`: antes de mandar vídeo pro Acer/X200MA, pular a máquina com reserva viva por "veo" em
   `D:\postador-de-videos\config\notebooks_reservados.json` (`ate > time.time()`), como o `tiktok_notebooks._reservado`.
2. `D:\video-fila\vitrine\player.py` (nos notebooks): hoje, com `~/postador-worker/ocupado` sem login e RAM ≥ 700 MB,
   ele CONTINUA tocando vídeo — é o "Veo + vídeo no fundo" que a dona viu. Sugestão: se o `ocupado` for de Chrome com
   aba do Flow (ou o PC1 gravar `"por": "veo"` no ocupado), não tocar vídeo, só o painel.
3. Limpeza antes de cada ação: já existe e roda em TODA abertura de Chrome no notebook (`chrome_conta.abrir`: mata o
   Chrome órfão de job que acabou/passou de 50 min, fecha bandeja/atualização do Mint — lista `SUPERFLUOS` — limpa cache
   do perfil acima de 250 MB; o player fecha o painel quando vê o `ocupado`). Não fecha telão tocando, login aberto
   para a dona, `pythonw` nem sistema. O Veo não acrescentou outra limpeza: ele só não começa onde o telão está tocando.
4. `maquina_remota.FLOW_FORA_DAS_MAQUINAS = {"pc2"}` (postador): o Veo já pode usar o PC2 quando houver conta do Flow
   logada lá, mas o postador ainda diz que o Flow não roda no PC2 — alinhar quando a dona logar.

> **ATUALIZAÇÃO 22/10 (conferida no código/git — NÃO refazer o que está aqui):** a nota "falta (código)" abaixo
> envelheceu: **IM-02/05, VO-02/03/06, BX-05 (md5) e os 4 itens da seção 3.3 JÁ FORAM FEITOS** (commits no main
> do beta de 16/10 à noite em diante: `9725521`, `156b0ca`, `2e215ae`, `4181959`, `e8c1d4c`, `8f525cb` — ver a
> tabela "Registro" do PLANO). O `PAUSE_SYSTEM` não existe mais e quem governa o veo é o **controlador geral**
> (`D:\video-fila\controlador.py`, ver o bloco "Estado em 22/10" do `D:\veo\CLAUDE.md`). O dedupe AB-08 roda em
> produção (`logs\hashes_videos.json`). Pendências reais de 22/10: VEO-03 (recortar a marca Grok das 292 fotos),
> VEO-04 (sonda avisar crédito/EXHAUSTED — o MS Energy esgota as contas de madrugada), VEO-05 (painel),
> VEO-06 (botão Veo_DESLIGAR valer no controlador), VEO-07 (contagem do Drive congela se o rclone falhar) —
> detalhes em `D:\video-fila\ACHADOS_LEVANTAMENTO_2026-10-22.txt`.

> **ESTADO MAIS NOVO: 16/10 ~22:55 (claude-40).** Cada item feito tem linha na tabela "Registro" de
> `PLANO_MELHORIAS_VEO.md` (com a validação). Fila geral e respostas do dono: seção "Respostas do dono" de
> `C:\Users\Haylla\.claude-vscode\plans\jazzy-conjuring-umbrella.md`. Regra do dono: no Opus, trabalho DIRETO, sem
> subagentes/workflow (memória project_trocador_subagentes). Depois de mexer: `python D:\veo\beta\validate.py`.
>
> **Feito em 16/10 (noite), além do que já estava:** piso da política (4/canal/dia, 1 h; total coletivo sem teto por
> ordem do dono) e Veo com 2/canal; caminho antigo do Veo desarmado; telefone fora de todo o histórico do git (backup
> `D:\veo\_backup_git_beta_20261016.bundle`; push exige `--force`); fotos só sem marca e por persona; extras do Studio
> na rede; leitor de métricas do Studio (`postador\bin\metricas_rede.py`: "continuaram assistindo" → gancho, CTR →
> título) e laço do gerador (AT-03); rampa por dado; SEO por autocompletar; legendas TikTok/Insta sem #fyp; sonda das
> contas Google; crítico com modelo próprio; prompt sem texto na tela; validate.py com comportamentos; docs; folhas de
> quadros no `rede --aprovar`; **comercial 1 em 3 no TikTok/Insta** (`postador\bin\comercial_veo.py`, card v6 sem
> contato + checagem por visão; ligado em `reuso_plataformas.json` → `veo_comercial`); pool de propaganda só na
> orientação certa; `postador\bin\workers.py` (worker comum; ida e volta testada no desktop). **23:20:** 3.3 fechado
> (conferência de fala dentro da trava de render), `supervisor.py` (raiz) sem janela, `validar_video` morta removida do
> cron, `experimental\` mantida (é ambiente do painel; depende do BX-08). Seções 3.2/3.3: o que sobra depende do dono
> (AT-12: estado de sessão separado do MS Energy) ou foi avaliado e descartado (ver "avaliados, não feitos").
>
> **Cuidado — desktop:** depois de CADA job do `workers.py` o OpenSSH 7.7 de lá recusa TODA conexão por ~10 min
> (3 vezes em 16/10; não é o nº de conexões). `workers.descansar` dá 12 min de folga após o job. Sugestão ao dono:
> atualizar o OpenSSH Server do desktop.
> **Cuidado — rascunhos:** `youtube_studio_extras --limpar-rascunhos` apaga TODOS os rascunhos presos do canal; em
> 16/10 um teste apagou junto um rascunho antigo ("Aulas IA - Micro-aulas e Tutoriais #shorts"). Agora ele só LISTA;
> apagar exige `--apagar-mesmo` — confira a lista antes. Conferir no Studio do historiasemframes se o vídeo de teste
> `DwzlNTVpHEM` ("teste rascunho apagar", privado) sumiu mesmo (o script confirmou o clique; às 23:10 o oEmbed ainda
> dava 403 "indisponível").
>
> **Falta (código):** AT-11 (capa A/B/C: Short não aceita capa pelo Studio web — só vale para vídeo longo), IM-02/04/05
> (card animado, cache de clipe parado, variar card), VO-02/03/06, BX-05 resto (ffmpeg pela constante central: 24
> caminhos), BX-08 (promover a beta para prod), AT-07 opcional (nota pós-render), AT-08 b/c (Ingredients/Extend:
> gasta crédito), Onda 4.2 (historias animada: é da claude-20 + crédito), Kwai (precisa conta).
> **Esperando o dono:** (1) verificar InventoReact por telefone (vídeo >15 min removido; "relacionado" bloqueado) e
> dizer se ManhwaReact é verificado (completo de 31 min pendente); (2) fotos novas: fotos reais dele ou recortar a
> faixa da marca do Grok (o gateway não mantém o rosto); (3) push do veo com `--force`; (4) conta do Kwai; (5) canal
> novo do anime (ligar com espaçamento quando existir).

> **ATUALIZAÇÃO 16/10, ~19:45 (sessão claude-40):** a seção 3.2/3.3 foi quase toda feita — ver as linhas de 16/10 no
> fim da tabela "Registro" de `PLANO_MELHORIAS_VEO.md` (cada uma com como foi validada). Feito: teto de uploads do Veo
> por canal/dia (o Veo tinha gastado a cota do ManhwaReact e o react do dono não subiu), fluxo do Veo novo até a rede
> (`limpar_veo` lê `beta\videos\cron_shorts` e roda antes da rede na tarefa de hora em hora), legenda pelo áudio,
> vozes, telefone fora dos arquivos versionados, filtro de contato (com testes), BX-02, BX-03, AB-08, AB-10, AT-12
> (parcial), 3.3. **Falta:** BX-04/06 (ffmpeg central, `validate.py`, docs), AB-09 folhas de quadros, extras do Studio
> na rede/anime (2.3 do plano geral). **Esperando a dona:** (1) manter o `limpar_veo` na tarefa `ManhwaReact-Rede`
> (mexido sem aviso — ela pediu aviso antes) e pôr os extras do Studio nela; (2) fotos novas sem marca — 298 das 305
> de `D:\veo\fotos` têm marca do Grok, então quase todo Veo novo sai barrado; (3) limpar o telefone do HISTÓRICO do
> git antes de qualquer push. Seção 3.1 (AB-01, AB-02 política) segue precisando de aviso a ela.

> Para o próximo agente. Leia nesta ordem:
> 1. `D:\veo\CLAUDE.md` — regras do projeto, onde fica cada coisa, como ligar e pausar;
> 2. **este arquivo** — o estado real e o que falta;
> 3. `docs\PLANO_MELHORIAS_VEO.md` — as 50 melhorias com evidência em arquivo:linha, a ordem em ondas,
>    as decisões da dona e a tabela "Registro" com tudo o que já foi feito e validado.
>
> **Regra que vale acima de tudo: nada do veo volta ao YouTube, e a geração não é religada, sem a dona mandar.**

---

## 1. O que está funcionando agora (conferido em 16/10, 11:30)

| Parte | Estado |
|---|---|
| Rede do manhwa-react com as mudanças desta auditoria | **No ar.** A rodada automática das 11:17 já usou o código novo |
| Os 27 vídeos quebrados fora da fila de postagem | **No ar.** Aparecem como "esperando aprovação", não mais como prontos |
| Card sem WhatsApp, sem marca, com voz aprovada | **No código.** Vale no próximo vídeo que for montado |
| Porteiro de qualidade e conferência de fala | **No código, nunca rodou.** Depende da geração, que está pausada |
| Dedupe de fala | **No código, nunca rodou.** Mesma razão |

**Geração do veo: PAUSADA** desde 12/10 (`beta\logs\PAUSE_SYSTEM`, motivo "manual"). Nenhum vídeo gerado em 16/10.
A pasta `beta\videos\rejeitados\` nem existe ainda, porque o porteiro nunca reprovou nada de verdade.

**Commits** (nada foi enviado ao GitHub): `a1cee7e` Onda 0, `8ad167a` Onda 1, ambos no `main` de `D:\veo\beta`.
As mudanças em `D:\manhwa-react\mr\rede.py` **não têm commit** (aquele projeto não usa git); a proteção é o backup
`mr\rede.py.bkp_20261016`.

---

## 2. Armadilhas que já custaram caro hoje

1. **Outra sessão do Claude edita `D:\manhwa-react\mr\rede.py`.** Em 16/10 às 11:27 o arquivo ficou quebrado
   (`NameError: _ocupados_veo`) por ~50 segundos entre dois salvamentos dela. A tarefa `ManhwaReact-Rede` roda no
   minuto 17 de cada hora: se calhasse ali, a rodada falhava. **Antes de abrir esse arquivo, olhe a data de
   modificação e pergunte à dona se outra sessão está nele.**
2. **O teto de veo desta auditoria não vale mais.** Essa outra sessão implementou, a pedido da dona, o `veo_rampa`:
   vagas próprias para o Veo, **3 por canal por dia desde 16/10, 4 desde 23/10, 5 desde 30/10** (em 2 canais: 6/dia
   indo a 10). O código diz, certo, que `veo_max_dia` e `veo_pelo_diretor` só valem com `veo_rampa` vazia.
   Isso contraria a recomendação AB-11 do plano (1 a 2 por dia até haver 10 medições de 48 h) e volume é o que o
   YouTube pune. É decisão da dona, está registrada. Para voltar ao teto menor: `"veo_rampa": []` no `config.json`.
3. **Não confie no que um teste parece dizer.** Na 1ª simulação eu li "o veo entrou pelo diretor" e estava errado:
   ele entrou por uma regra de reserva minha, e o diretor tinha escolhido outro canal. Um revisor pegou. Confira a
   causa, não só o resultado.
4. **`--simular` não é leitura pura:** grava `work\rede_notas.json` e `work\rede_meta\*`, inclusive o veredito do
   revisor. Para re-testar um item barrado, apague o json dele em `work\rede_meta` antes.

---

## 3. O que falta — e é isto que a dona mandou fazer ("faça todas as melhorias pendentes")

Das 50 melhorias do plano, **9 estão feitas** (ver a tabela "Registro"). O trabalho foi interrompido antes de começar
esta lista. Ordem sugerida: do mais perigoso para o menos.

### 3.1 Precisa de aviso/decisão da dona antes (ela pediu: "me avisa antes de mexer em tarefa agendada ou política")

| Item | O que fazer | Onde |
|---|---|---|
| **AB-01** | Desarmar o caminho antigo: tirar as etapas 1 e 2 do `.bat`, desabilitar a tarefa `AgendadorVO3`, mover os 3 scripts para `bin\_legado\`. **Conferir antes** se alguma fonte que não é veo (recaps, "materiais") depende deles | `D:\postador-de-videos\bin\postar_tudo_auto.bat`, `postar_tudo_hoje.py`, `postar_pos_final.py`, `agendar_vo3.py` |
| **AB-02** | Piso de segurança no código da política (≤ 4 por canal/dia, ≥ 1 h, ≤ 20/dia), que o json não consiga afrouxar, e limites por projeto. Hoje está em 10/50/0 h | `D:\postador-de-videos\bin\politica.py` função `politica()` |
| **AB-04** | `veo_so_limpo: true` no TikTok e Instagram + legenda pela fala do vídeo, sem `#fyp/#viral`. Hoje os dois ainda publicam a versão COM o número na tela | `config\reuso_plataformas.json`, `bin\tiktok_cdp_poster.py`, `bin\postar_insta_auto.py` |
| Religar a geração | Só depois da Onda 0 fechada. Apagar `beta\logs\PAUSE_SYSTEM` e usar o botão `Veo_LIGAR_*.bat` | `D:\veo\beta` |

### 3.2 Código, sem risco de postar — pode fazer direto

| Item | O que fazer | Onde |
|---|---|---|
| **Vozes proibidas** | Ainda em uso em 3 arquivos do postador (a Onda 0 limpou só o veo). Trocar pelas edge Multilingual aprovadas, copiando de `D:\hipercool-videos\bin\elenco.py` (PROIBIDAS, EDGE_F/EDGE_M, VARIACOES, `falar_edge`). **Não copiar** `edge_tts_engine.py`, que é o legado com o problema | `D:\postador-de-videos\bin\edge_tts_engine.py`, `curadoria.py`, `test_all_voices.py` |
| **Telefone no git** | O número da dona está em 10 lugares de `produtos.json`, que já entrou no commit `a1cee7e`, num repositório com remoto no GitHub. Nada foi enviado. Tirar do arquivo versionado e ler de um arquivo fora do git (ex.: `beta\secrets\contato.json`, que já é ignorado). Hoje **nada no código põe esse número na tela ou na fala**, então é só higiene | `D:\veo\beta\pos_producao\assets\produtos.json` |
| **Filtro de contato** | O `PROIBIDO_CONTATO` que escrevi barra número que não é telefone (ano, capítulo, placar, "24/7") e deixa passar vários convites escritos de outro jeito. Um revisor listou os casos. Corrigir com testes sobre títulos reais de `_postados\react\publicados.json` | `D:\manhwa-react\mr\rede.py` (perto de `PROIBIDO_TITULO`) — **cuidado com a outra sessão** |
| **AB-08** | Dedupe de **vídeo** (o de fala está pronto): comparar quadros do vídeo novo com os já postados e com os 730 antigos, para não sair quase o mesmo clipe duas vezes. Copiar de `D:\manhwa-react\mr\memoria.py` (`hashes_quadros`, `_parecido`, limiar 0,35). Indexar uma vez os 241 limpos + 21 completos | novo módulo em `D:\veo\beta`, chamado no porteiro e/ou no inventário da rede |
| **AB-10** | Alertas no Telegram: canal que passou de 3 uploads no dia, 2 uploads do mesmo canal com menos de 1 h, política fora do piso, 2 canais com erro no mesmo dia (então criar `PARADO.json`). Teria pego o afrouxamento de 14/10 | `D:\postador-de-videos\bin\notificar_telegram.py` |
| **BX-02** | `sem_janela.py` (copiar de `D:\hipercool-videos\bin`) importado no topo de `loop_cron.py`, `cron_gerar_video_llm.py`, `worker_noite.py`, `supervisor.py`; pausa manual deve **dormir** em vez de abortar a cada 30 s; `SKIP_RESOURCE_CHECK` não pode ignorar a pausa | `D:\veo\beta` |
| **BX-03** | Trava de um render por vez (copiar a classe `Trava` de `mr\rede.py`) em `montar_final.montar`, `limpar_veo.processar` e no `worker_noite` | `D:\veo\beta\pos_producao` |
| **AB-09** | Folhas de quadros (5 quadros × 3 vídeos) para aprovar lote olhando, em vez de no escuro; e ampliar o detector de marca para qualquer logo fixo, não só a do TikTok (há brutos com marca do **Grok** na pasta) | `D:\manhwa-react\testes\folhas_quadros.py`, `D:\postador-de-videos\bin\limpar_veo.py` |
| **AT-12** | Conta pro só reabre quando o saldo for lido de novo; timeout do cron = deadline do worker + 60 s; gravar o log do worker em `logs\worker_<sessao>_<ts>.log` (hoje o stdout é descartado) | `D:\veo\beta\cron_gerar_video_llm.py` |
| **BX-04/05/06** | `validate.py` cobrindo os módulos vivos; remover código morto; md5 no lugar de `hash()` em `plugins\propaganda_inteligente.py`; caminho do ffmpeg só pela constante central; corrigir `README.md`, `TUTORIAL_AGENTE.md` e `ARQUITETURA.md`, que citam venv e pastas que não existem | `D:\veo\beta` |

### 3.3 Achados de gravidade média dos revisores, ainda abertos

- O teto de veo é por **rodada**, não por dia: com mais canais permitidos que o teto, fura. Somar o que já foi
  agendado hoje (`publicados.json`) em `distribuir()`.
- A conferência de fala pode rodar o whisper local junto com um render (regra "um render pesado por vez").
- Não há chave para desligar a validação de arquivo separadamente (só `VEO_VALIDAR=0`, que desliga tudo).
- `fala_repetida` pode colidir com a própria fala re-enfileirada e descartar um prompt já pago.

---

## 4. Decisões que só a dona pode tomar

As 14 da seção 6 do plano. As que travam o resto:

1. **Quais canais recebem o veo.** Há dado novo: o diretor avaliou 40 vídeos e nenhum tira nota ≥ 7 nos 2 canais de
   hoje; 35 tirariam em canais bloqueados — **mundoquenaoexiste (21)**, assistiainvestimentos (14),
   dicasfinanceirasdaia (14). Para liberar, basta no `config.json` do manhwa-react:
   `"rede": {"canais_veo_limpo": ["inventoreact", "manhwareact", "mundoquenaoexiste"]}`
2. COMPLETO (com WhatsApp) sai ou não do TikTok/Instagram.
3. Limites da política: voltar a 3/12/2 h para todos, ou por projeto.
4. Quando religar a geração e com quantas contas.
5. Se pode transcrever o áudio com o Groq pelo proxy (hoje funciona; custa ~1 MB por vídeo).

---

## 5. Ferramentas novas que você já tem

| Arquivo | Para quê |
|---|---|
| `D:\veo\beta\validar_video.py` | O vídeo presta? 9:16, duração, áudio, **decodifica**, sem quadro preto/congelado. `python validar_video.py <mp4>` |
| `D:\veo\beta\conferir_fala.py` | O Veo falou o que foi pedido, em português? Transcreve e compara por semelhança **e** cobertura. `python conferir_fala.py <mp4> "fala pedida"` |
| `D:\veo\beta\logs\falas_historicas.json` | 132 falas já usadas, só para o dedupe. Não é fila de postagem |
| `D:\veo\docs\videos_corrompidos_20261016.txt` | Os 27 vídeos quebrados, com diagnóstico. Já marcados como rejeitado |

Infra destravada hoje: **Groq** voltou (proxies novos da dona; transcrição em ~6 s) e a **voz** voltou
(`edge-tts` subiu de 7.2.8 para 7.3.1 no venv do veo — o 403 era versão, não proxy).

---

## 6. Como validar qualquer coisa que você mexer

- Vídeo: `python validar_video.py <mp4>` e **extrair quadros e olhar** (`ffmpeg -ss N -i x.mp4 -vframes 1 q.png`).
- Fala: `python conferir_fala.py <mp4> "o que foi pedido"`.
- Rede: `python manhwareact.py rede --simular` (não posta) e conferir o log em `D:\manhwa-react\logs\rede_AAAAMMDD.log`.
- Projeto: `python validate.py` no `D:\veo\beta` (com `PYTHONUTF8=1` e o venv `D:\veo\venv`).
- Nunca dizer "pronto" sem uma dessas provas. A dona pede resultado conferido, não código que importa sem erro.

## 7. Registro

Ao terminar um item, escreva uma linha na tabela "Registro" do fim de `docs\PLANO_MELHORIAS_VEO.md` com a data, o que
foi feito e **como foi validado** — é assim que o próximo agente sabe no que pode confiar.
