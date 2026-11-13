# Continuar daqui (Hermes Call)

> **Para qualquer agente ou conta nova:** leia este arquivo primeiro, depois `docs/VERSOES.md`
> (qual versão é a certa) e `docs/PENDENCIAS_BUGS.md` (estado de cada bug).
> Ele existe para a dona poder trocar de conta do Claude e continuar sem perder o fio.
> **Mantenha este arquivo atualizado ao fim de cada etapa.**
> O histórico das conversas fica em `C:\Users\Haylla\.claude\projects\` (arquivos .jsonl).

> **12/10 — pastas do PC reorganizadas:** tudo do Hermes fica em **`D:\hermes\`** (mapa em `D:\hermes\LEIA-ME.md`).
> Caminhos antigos citados abaixo: `D:\hermes-call` → `D:\hermes\hermes-call`; `D:\hermes-wt\pc-base` →
> `D:\hermes\pc-base`; `D:\campanha-hermes` → `D:\hermes\campanha`. Os outros worktrees de `D:\hermes-wt\`
> (pc-achados, pc-ops, pc-voz, integracao, painel, seguranca, ligacoes, voz-audio, voz-conversa, online) foram
> removidos: estavam todos juntados no `main` e sem nada pendente; os ramos continuam no git. O Postgres de teste
> `D:/tmp/pg-achados` já não existia (só sobrava o log) e foi apagado.

> **05/10 — trabalho online do mês 2 (auditoria, correções, investigação da gravação):** plano, histórico, achados
> F01–F34 e o que falta estão em **`docs/mes2-online/README.md`** (ramo `claude/gallant-mendel-f1xney`). Leia antes
> de continuar o trabalho de código.

## Regras da dona (não negociáveis)
1. **Correções sempre em cima da versão que está NO AR** (`main`). O `ops/publicar.sh` bloqueia retrocesso.
2. **Toda publicação tem volta fácil.** A versão que vinha funcionando vira a **ESTÁVEL** (protegida, nunca
   apagada) e volta com `bash ops/voltar-estavel.sh` ou com **dois cliques em `ops\VOLTAR-VERSAO-ESTAVEL.bat`**
   (pede "SIM"; os dados não são apagados). Depois de validar a nova: `bash ops/marcar-estavel.sh`.
   **Depois de VOLTAR versão, recarregue o painel (Ctrl+F5) em TODAS as abas abertas** (do PC e do celular): o
   painel novo que ficou carregado no navegador salva só os campos que conhece e o servidor antigo entende o que
   não veio como "apagar" (credenciais escolhidas, roteamento, "só ativo"…).
   (03/10: a dona reforçou — "a que está em produção está falando bem; deixe fácil de reverter".)
3. Publicar **só** com `bash ops/publicar.sh` (compila com `-tags mlow`, faz backup do banco, volta sozinho se falhar).
4. Senhas nunca são digitadas pelo agente. O acesso às VPS é por chave (`ssh hermes-prod`, `ssh hermes-staging`).
5. Falar com a dona em português simples.
6. Em 24/09 a dona autorizou tomar as decisões e fazer tudo. Continua valendo: ações irreversíveis ou em plataforma de pagamento, só com o OK dela.
7. Mudanças de segurança nos servidores (cron, chaves, contas, senhas) o agente PREPARA e a dona roda
   (pelo terminal do app); depois o agente confere.

## 24/10/2026 11:30 — v0.16.0 no ar
- **NO AR: v0.16.0** (`20261024-1123_bc4627b`), a pedido do dono ("então ligue"): alô de volta, retorno pedido na
  ligação, aviso de interesse, monitor de grupos. Troca às 11:29 sem campanha aberta nem ligação em voo; 4 linhas
  voltaram, decidido em 45 s, 0 ERROR/panic. Backup do banco feito DEPOIS da troca (11:31, 595 MB, em
  `releases/20261024-1123_bc4627b/banco.dump`). Volta: `bash ops/reverter.sh` (→ v0.15.0). Estável não mudou.
- Monitor de grupos ligado só na conta admin@hermescall.com (`settings` key `voice`, `group_monitor=true`, por SQL).
- Falta: ligação de verdade para validar o "alô de volta" (mudança de voz); decisões do monitor só na memória.

## 19/10/2026 10:19 — v0.15.0 no ar (botões clicáveis)
- **NO AR: v0.15.0** (`20261019-1010_19d42b8`, commits `a09a3cb` + `19d42b8`), com OK do dono, pedido pelo FluxIA:
  `/messages/buttons|list|interactive` (portado do AstraCalls) e resposta de botão chegando no webhook como `type text`
  + `buttonReply`. Detalhes no CHANGELOG. Volta: `bash ops/reverter.sh` (→ v0.14.1). Estável continua a anterior.
- Publicado em 2 passos para não cortar ligação: `--so-compilar` com a campanha rodando; depois 8843 pausada às 10:16
  (sem ligação em voo), `backup-banco` + `ativar` (4 linhas voltaram, decidido em 45 s). **A 8843 só foi religada às
  12:46** (a sessão do agente caiu depois do ativar): ~2h30 sem discar. Conferido depois: 0fcd550f conectada,
  `HERMES_CAMPAIGN_PREFILTER=false` no processo novo, `enabled`, sem ERROR. Tag `PRODUCAO-20261019-1010_19d42b8`
  enviada (origin e emerson); branches não.
- Falta: confirmar no celular que botões e lista aparecem (teste mandado da linha da papelaria às 12:45).

## 19/10/2026 09:05 — o que mudou desde 15/10 (vale acima das seções de baixo)
- **NO AR: v0.14.1** (`20261015-1517_2d2ef76`). O serviço ficou parado de 18/10 11:39 a 19/10 08:49: a VPS foi
  desligada pelo botão de energia do provedor e o `hermes-call` estava `disabled` no boot. Agora está `enabled`.
- **A linha 8653 agora é a sessão `0fcd550fab479c0b531e74903a8f566e`** (reconectada pelo painel em 19/10 08:58; o
  painel criou sessão nova). A `290f2fb3…` ficou deslogada e sobrando no banco. A campanha 8843 foi trocada para a
  sessão nova e despausada às 09:00. Detalhes e como desfazer: `D:\hermes\campanha\PLANO.md` (registro de 19/10).
- Pré-filtro de WhatsApp continua desligado (`30-campanha.conf`).

## ✅ 15/10/2026 ~11:45 — ESTADO ATUAL (leia esta seção primeiro; vale acima das de baixo)

**NO AR desde 15/10 09:10: v0.13.0** (`20261015-0904_1c1f593`, commit `1c1f593`). **ESTÁVEL marcada: v0.12.0**
(`20261014-1549_743285d`, marcada em 15/10 07:00). Volta: `bash ops/reverter.sh` (do PC, no Git Bash, dentro de
`D:\hermes\pc-base`) → v0.12.0. Não usar `voltar-estavel.sh` sem conferir o arquivo `ESTAVEL` na VPS.
**`main` e os dois remotos estão 4 commits atrás**: v0.12.0 e v0.13.0 só existem no ramo `pc/v0.8.0` e nas tags
`PRODUCAO-*`; `ops/atualizar-copias.sh` não rodou nas duas últimas publicações (avançar `main` só com OK).

**Campanha piloto** (`8843d578ff82eee06fdc1f6198040df8`, linha 8653 = sessão `290f2fb3c1ad8d570c732d16afd41f1e`, banco
`wacalls_main`): 297 imobiliárias, 48/dia espalhadas das 7h às 18h, seg–sex. Registro completo em
`D:\hermes\campanha\PLANO.md`. Até 11:20 de 15/10: 66 discadas (14/10: 47; 15/10: 19), 16 atendidas, 6 ouviram a
oferta, 3 conversaram com a IA, 0 demonstrações, 0 "não me ligue", 0 erro da IA. Isca nova de 9,6 s
(`03012f1a…`) desde 06:57: 3 de 3 atendidas desligaram no meio dela. Mudado em 15/10 com OK da dona:
`campaign_only` ligado (a IA só fala com quem foi discado) e horário da resposta por texto desligado
(`schedule.enabled=false`). **12:19: isca v3 no ar** ("Oi, aqui é da Inovári. Vocês atendem cliente pelo WhatsApp?",
4.179 ms, biblioteca `cef75743…`), com OK da dona; backup em `/root/backup-campanha-8843-20261015-1219.json` e volta
em `/root/rollback-isca-v3.sh` (depois: pausar, reiniciar sem ligação ativa, liberar). Plano e comandos:
`D:\hermes\campanha\campanha-01\isca-v3-plano.md`. Medir 10 atendidas antes da próxima mudança. **v0.13.0** (lead da campanha manda mensagem → o Hermes liga na hora; texto só se não
atender; 1 tentativa por contato a cada 12 h; logs "mensagem de lead:") **ainda não disparou nenhuma vez** —
quando acontecer, conferir a sequência no log. Efeito colateral conhecido: se não atende, `aiAutoReply` roda de
novo e `detectAIField`/webhook podem sair 2×.

**Análise geral de 15/10: `docs/ANALISE_MELHORIAS_2026-10-15.md`** (só leitura; nada mudou na produção). O que pesa:
- Os "5,65 s" das atendidas de 14/10 são **medição**: a isca tocou inteira e a pessoa desligou 1,5–2 s depois, na
  espera da resposta (`broadcast.go:2670` devolve só a duração da isca). **10 de 16 atendidas não passaram da isca.**
  Proposta, uma mudança por vez com OK da dona: isca ≤ 3,5 s → esperar o "alô" antes de falar (código, v0.14.0) →
  oferta ≤ 10 s. Trocar isca/oferta exige reiniciar o serviço (o áudio fica em memória): só sem ligação ativa e com
  `next_slot_at` longe, como foi feito em 15/10 06:57.
- **Avisos de operação não chegam:** `/etc/hermes-call/alertas.env` existe com `ALERTA_TG_TOKEN`/`ALERTA_TG_CHAT`
  vazios (a dona preenche). O backup de todas as VPS falha há 7 dias por um Postgres sem nome na 209
  (`wizardly_kepler`, não é do Hermes); o backup diário do Hermes está OK.
- **Segurança (a dona roda, o agente prepara):** `/etc/systemd/system/hermes-call.service` com permissão 666 e com o
  token do Telegram e a senha do banco em `Environment=`; SSH ainda aceita senha de root (`50-cloud-init.conf`).
- Reserva da IA da ligação com a chave Groq recusada (401); 1ª resposta da IA em 4,4–6,5 s (Gemini flash-lite).
- Número sem WhatsApp gasta vaga da campanha espaçada (o pré-filtro só existe no modo imediato).
- Ligação que cai na isca não entra em `call_transcripts` (só o caminho da conversa grava); a de 10:35 (×1318) foi ao
  Telegram com transcrição e não está na tabela por isso.
- XML da sinalização em INFO (`call_trace.go:52`) = ~85% dos bytes do log de hoje.

**Dicas que economizam tempo:** API local na VPS com `curl -H "X-API-Key: $(cat /root/.hermes-campanha-apikey)"
http://127.0.0.1:8080/...` (Bearer dá 401); `PUT /api/settings/agent-chat` zera `enabled` e `welcome_msg` se não
vierem no corpo; banco só com `sudo -u postgres psql -d wacalls_main` (o usuário hermes falha por peer auth);
logs: `journalctl -u hermes-call --since HH:MM | grep -v 'xml='`; linhas que importam: "ligação não atendida",
"runCampaign: gate pcm2" (`pcm2_len>0` = oferta carregada), "áudio 1 (isca) tocado durMs=", "chamada encerrou
após áudio 1", "chamada encerrou enquanto esperava resposta", "qualidade do áudio da ligação", "gravação entregue
no Telegram", "mensagem de lead:". A dona lê `campaign_results` por `updated_at` (o `created_at` é o da criação
da campanha, 14/10 10:36, para todos os números).

**v0.14.0 (15/10 à tarde, pedido "termine o que falta": captação, rediscagem, estratégias).** O que entrou está no
`CHANGELOG.md`. Build, vet, testes unitários, simulador de voz, `tsc`/`vite build` e os testes novos com Postgres
(descartável na 209) passaram. **PENDENTE para o próximo agente (a dona pediu para publicar e deixar a lista):**
1. `TestDB_SoCampanha_RetornoDeLigacao` falhou pelo túnel com "desconhecido com a opção ligada: """ (parece o cache de
   5 min de `LoadUserSettings` após `SaveAgentChat`; `TestReapStuck` é a falha conhecida de relógio). Conferir se é
   do teste ou do código (`missed_callback.go:143`) — nada da leva mexeu ali.
2. Ligar na campanha piloto, com OK da dona: rediscagem (`UPDATE campaigns SET pace_config = pace_config ||
   '{"retry_no_answer":1,"retry_gap_hours":4}' WHERE id::text LIKE '8843d578%'`, vale no próximo tick) e corrigir o
   total (`UPDATE campaigns SET total=(SELECT count(*) FROM campaign_results r WHERE r.campaign_id=campaigns.id)
   WHERE id::text LIKE '8843d578%' AND total=594`).
3. Espera do alô: `HERMES_VOICE_WAIT_HELLO_MS=2500` no serviço só depois de uma ligação de verdade (REGRESSOES §1).
4. Variante B da isca (A/B): gerar áudio B, `request.audio_id_b`, reiniciar; comparar em `GET /api/campaigns/{id}/variants`.
5. Scripts que a dona roda (dois cliques em `ops\`): `LIGAR-AVISOS-TELEGRAM.bat`, `TRANCAR-SERVICO-E-SENHAS.bat`,
   `FECHAR-SSH-POR-SENHA.bat`. Backup das VPS: copiar `ops/vps/backup-todas/backup-vps.sh` para
   `/opt/hermes-call/ops/` e criar `/etc/hermes-call/backup-vps.env` com `IGNORAR="pg.wizardly_kepler"`.
6. Chave Groq recusada (401) no cofre e motor da ligação lento (Gemini): dona confere/troca no painel.
7. Primeiro uso real de `check-batch`/`validar-whatsapp.py` com uma lista pequena (10 números).
8. `main` e GitHub estão atrás do ramo `pc/v0.8.0`: avançar e enviar com OK; `ops/atualizar-copias.sh`.
9. Apagar o Postgres descartável na 209: `ssh hermes-staging docker rm -f hermes-test-pg-v14`.
10. Revisão horária (`D:\hermes\campanha\REVISAO-HORARIA.md`) e conferir a 1ª atendida com a isca v3 (até 14:00 nenhuma).

## 14/10/2026 ~10:35 — estado anterior (histórico; vale a seção de cima)

**NO AR desde 14/10 10:30: v0.11.0** (`20261014-1024_a2683c0`), com o OK da dona. 2 linhas reconectadas, nenhum
erro depois da troca; cópias igualadas (`ops/atualizar-copias.sh`); `main` = `pc/v0.8.0` = `a2683c0`, enviados.
Volta: `bash ops/reverter.sh` (→ v0.10.0 `20261008-1541_b0605a3`). Ainda não marcada como estável.

**Campanha de divulgação (decisão da dona, 14/10):** usar a **8653** (não há número novo; o cadastro em celular
virtual foi recusado pelo WhatsApp e está encerrado), **no máximo 48 ligações por dia espalhadas no horário
comercial**; cobrança fica para depois que começarem a testar; demonstração a qualquer hora até 21h; o "ensaio" são
as 10 primeiras ligações reais, com o agente lendo cada uma e ajustando. Plano e registro:
`D:\hermes\campanha\PLANO.md`. O que a v0.11.0 corrigiu no modo "ao longo do dia" (`paced`) para isso:
- soltava uma ligação por minuto ao abrir a janela (48 entre 9h e 9h50): agora divide o que falta pelo resto da
  janela, com variação de 70–110%;
- com agente de 2 áudios **não tocava a oferta** (o cadenciador remontava a campanha só com a isca, sem contexto nem
  som de fundo): agora reusa a campanha da criação e, depois de reinício, refaz tudo (oferta guardada na biblioteca);
- podia abrir 2 chamadas ao mesmo tempo na linha: agora espera a conversa acabar;
- `weekdays_only` (só pela API; sem botão no painel).
**O painel NÃO escolhe agente no Disparo em Massa** (sem `profile_id` a ligação só toca áudio). A campanha é criada
pela API (`POST /api/sessions/290f2fb3c1ad8d570c732d16afd41f1e/broadcast`, X-API-Key da conta admin@hermescall.com)
com o pedido pronto em `D:\hermes\campanha\campanha-01\criar-campanha.json` (297 imobiliárias, agente "Vendas Hermes
Call" `4a09fe24-…`, `paced`, 48/dia, 9h–18h, seg–sex, toque 45 s, conversa até 10 min). **Campanha criada em
14/10 10:36: `8843d578ff82eee06fdc1f6198040df8`** (297 na fila; 1ª ligação 10:37). A chave de API foi gerada pelo
agente a pedido da dona (ela não sabia onde), direto no banco no mesmo formato do painel: nome "Campanha divulgação",
prefixo `hk_09f9e779`; o texto só existe em `/root/.hermes-campanha-apikey` (600) na produção — usar de lá
(`curl -H "X-API-Key: $(cat /root/.hermes-campanha-apikey)" http://127.0.0.1:8080/...`), nunca copiar para fora.
Pausar/retomar: `POST /api/sessions/290f…/broadcast/8843d578…/pause|resume`. Roteiro: regra "demonstração das 8h às 21h"
acrescentada em 14/10 10:07 (cópia anterior: `/root/backup-roteiro-vendas-20261014-1007.prompt.txt` na produção).
Na 1ª ligação atendida, conferir no registro `runCampaign: gate pcm2` com `pcm2_len` > 0 (a oferta tocou).

**Testes com banco neste PC:** não há Postgres local; em 14/10 foi usado um `postgres:16-alpine` descartável na 209
(`127.0.0.1:55441`, túnel SSH, apagado no fim). Pelo túnel alguns testes estouram o tempo e o `TestReapStuck` falha
também no `main` (relógio do PC × banco): não são defeito do código.

## 08/10/2026 ~15:50 — estado anterior (histórico; vale a seção de cima)

**NO AR desde 08/10 15:48: v0.10.0** (`20261008-1541_b0605a3`). Publicada com o OK da dona ("pode fazer o commit,
publicar"). Banco salvo antes, 2 linhas reconectadas, nenhum erro; cópias igualadas (`ops/atualizar-copias.sh`).
Volta: `bash ops/reverter.sh` (→ v0.9.0 `20261007-1425_cdad439`) ou a ESTÁVEL (`20260925-0158_29e4e85`).
O que entrou: a aba **"Por código"** na tela de conectar a linha (`SessionPairing.tsx`; o servidor já tinha
`POST /api/sessions/{sid}/pair-code`), a caixa `telefone,Nome` do Disparo em Massa (`3865ba6`) e o ajuste do
roteiro de vendas (`a96ef05`). A aba foi feita no PC do Emerson e veio por patch
(`D:\whatsapp-activator\whatsapp-activator\ENTREGA-08-10-2026\`, com `LEIA-PRIMEIRO.md`). Conferida na tela no
painel local (as duas abas). **Falta:** gerar um código de verdade pelo painel e parear um número (ninguém clicou
em "Gerar código" ainda; clicar manda o pedido ao WhatsApp e avisa no celular do número).

**"Conectar WhatsApp sem celular" (pedido da dona em 08/10) NÃO é isso e NÃO está pronto.** A aba "Por código"
conecta conta que JÁ existe num aparelho. O que ela quer é número novo: o cliente digita o número e o SMS e o
sistema deixa a linha pronta, ligando o celular virtual só na hora. Estado conferido em 08/10 15:39: o celular
virtual da VPS 157 (`ssh hermes-bloqueio`, `/opt/vps-redroid`) está de pé, com o WhatsApp parado na tela do número,
vazia. Essa tela ignora toque e teclado enviados por programa (proteção do WhatsApp contra cadastro automático) e o
agente do PC não contorna. **Os dois testes com a dona, em 08/10 à noite, fecharam esse caminho:**
1. Celular virtual da VPS (Redroid, janela pelo `vps-redroid\conectar.bat`): a tela do número não reage ao mouse
   nem ao teclado dela. Não serve para cadastrar.
2. Emulador de Android com janela, neste PC (`D:\whatsapp-activator-windows`, celular `wa-teste-4247`, Android 9
   `google_apis`, WhatsApp 2.26.39.75 instalado pelo APK do site): a tela aceita o mouse, ela digitou o número e o
   WhatsApp respondeu **"Baixe o app oficial do WhatsApp para continuar — não foi possível confirmar se você está
   usando o app oficial"**. É a conferência de aparelho e de aplicativo do próprio WhatsApp. Nenhum SMS foi
   digitado; nenhum número foi cadastrado em celular virtual até hoje.
O agente do PC não falsifica essa conferência. Única tentativa honesta que sobra no celular virtual, sem garantia:
emulador com a imagem que tem a loja do Google e o WhatsApp instalado pela loja (precisa de conta Google da dona).
Se o WhatsApp recusar de novo, "sem celular" por celular virtual acabou. O que funciona hoje: número cadastrado
num aparelho de verdade (um aparelho guarda vários números) + aba "Por código". Nada de integração foi construído.

**Divulgação — fonte de empresas (08/10):** feita a captação de EMPRESAS pelos dados abertos de CNPJ da
Receita (público, não é raspagem), em `D:\campanha-hermes\captacao\cnpj\`: `captar_cnpj.py` baixa o cadastro
(~8 GB, download paralelo), filtra 23 ramos (CNAE conferido contra a tabela oficial), pega só ativos e com telefone,
junta porte/capital/filiais, tira MEI, e separa 'barato' (Start 199) de 'caro' (Pro/Scale). A fatia sai pronta para
o `processar_leads.py`. Testado de ponta a ponta com dados reais (cadastro 09/2026): base de 2,37 milhões de empresas em 23 ramos na
VPS de teste (`/root/captacao/base.csv.gz`, 155 MB, reutilizável; os 6,6 GB de zips brutos ficaram em
`/root/captacao/dados`); fatia de imobiliárias de SP (40 mil) pontuou A/B/C certinho. A caixa de colar números do
Disparo em Massa agora guarda o nome (`telefone,Nome`), commit `3865ba6` (tsc+build ok, no ramo; falta publicar).
**Melhoria pequena de painel (anotada):** a caixa 'adicionar números manualmente' do Disparo em Massa
(`client/src/pages/MassCallPage.tsx`, `addManualNumbers`) só lê o telefone e descarta o nome; o backend (broadcast
`numbers[]`+`names[]`) já aceita nome. Fazer a caixa aceitar linhas `telefone,nome`/CSV para a IA cumprimentar pelo
nome da empresa. Guia da captação: `D:\campanha-hermes\captacao\README.md` e `captacao\cnpj\README.md`.

**Divulgação — captação (07/10 noite):** feita a ferramenta que prepara a lista ANTES de ligar, em
`D:\campanha-hermes\captacao\` (Python, sem internet, roda no PC): lê lista bruta em qualquer formato, arruma o
telefone para o padrão do WhatsApp, tira repetidos, aplica lista de bloqueio, pontua A/B/C e gera `pronto-hermes.csv`
(telefone+nome p/ o Hermes) + `leads-completo.csv` (p/ o CRM). Testada com dados de teste. Guias: `captacao\README.md`
e `captacao\DE-ONDE-VEM-A-LISTA.md` (origem legal da lista). Falta a dona escolher segmento e origem (Fase 0 do
`PLANO.md`). **Captação por raspagem (LinkedIn/Google) NÃO foi feita, de propósito: é contra as regras dos sites.**

**Ativador de WhatsApp sem celular (07/10):** outro agente montou em `D:\whatsapp-activator` e instalou na PRODUÇÃO
(`/opt/whatsapp-activator`, porta 8091) um serviço com emulador Android. **Não funciona** (nenhuma VPS tem
virtualização/`/dev/kvm`; os passos não conferem o resultado e seguem com SMS falso). O agente do PC parou o serviço
em 19:05, mas ele foi religado depois por outra sessão. Avaliação completa em `D:\whatsapp-activator\AVALIACAO.md`.
**O caminho de registrar o número sem aplicativo nenhum, por cliente não oficial, o agente do PC NÃO faz (burla a
proteção do WhatsApp).** Caminhos legítimos: (D) botão 'parear por código' no painel — o servidor já tem
`POST /api/sessions/{sid}/pair-code`, falta a tela; (C) celular virtual com o app oficial numa máquina com
virtualização (o PC da dona serve; as VPS não). Sobras do outro agente na produção, a apagar com OK da dona: conta
`ac***@internal.local`, linha 'Linha Campanha - 5544' + banco, imagem Docker de 6,8 GB, pasta `/opt/whatsapp-activator`.

**Divulgação (07/10 à tarde):** a dona deu a comparação das VPS por encerrada ("vamos considerar um sucesso, se
precisar invertemos") e pediu o plano da divulgação. Está em **`D:\campanha-hermes\PLANO.md`** (fases, piloto de
300 empresas num segmento, o que medir, riscos). Nada executado: a Fase 0 espera 5 decisões dela (segmento, número
novo da campanha, 3 pontos do roteiro de vendas, como o 1º cliente paga, horários de demonstração).

**Decisão da dona: Hermes e bancada nas DUAS VPS, um em cada, e inverter para comparar.** Tudo em
`docs/PLANO_DUAS_VPS.md`. Resumo: produção = Hermes no ar + bancada parada; 209 = bancada ligada + Hermes reserva
desligado (`/opt/hermes-call-reserva`, só o programa). Todas as cópias na mesma versão: depois de publicar,
`bash ops/atualizar-copias.sh`. Inverter a bancada: `bash ops/bancada/trocar-bancada-de-vps.sh para-producao|para-209`
(o sentido 209 → produção ainda não foi exercitado). Inverter o Hermes NÃO está pronto: é mudança de máquina e
depende de a dona decidir os segredos na 209 e o domínio.


**A BANCADA MUDOU DE MÁQUINA: agora roda na VPS de teste (209, `ssh hermes-staging`).** Na produção ela está
parada e desabilitada (`systemctl disable --now hermes-bancada`, feito por outro agente em 07/10 13:51); os arquivos
e os bancos `bancada_*` da produção continuam lá, intactos, como volta.

Como ficou na 209 (terminado pelo agente do PC em 07/10 14:13):
- binário, painel e `lib/libopus_mlow.so` em `/opt/hermes-bancada` (build `20261006-1730_e5d0ee9`, o mesmo arquivo
  compilado na produção); serviço `hermes-bancada.service`, porta `127.0.0.1:8091`, sem limite de CPU;
- **banco só dela**: contêiner `hermes-bancada-pg` (imagem `pgvector/pgvector:pg15`, volume `hermes_bancada_pg`),
  ouvindo só em `127.0.0.1:5440`. Os dois bancos (`bancada_main` e o da linha 8288) foram copiados da produção por
  `pg_dump | pg_restore`. **Não usa nenhum banco dos outros serviços da 209.**
- `/etc/hermes-bancada/bancada.env` (600): o da bancada + `WACALLS_PG_URL` do banco dela + os dois ajustes de voz
  que a produção tem (`HERMES_VOICE_BARGE_IN_THRESHOLD`, `HERMES_VOICE_ECHO_FACTOR`). O segredo de login da
  PRODUÇÃO não foi para a 209 (conferido por hash). `/etc/hermes-call/ensaio.env` (600) tem o número de destino.
- **A mesma linha 8288 não pode estar ligada nas duas máquinas.** Para voltar a bancada à produção: parar a da 209
  primeiro.
- **O que ainda NÃO existe na 209:** `lab-bancada.sh preparar` (ele copia agentes e chaves do banco da produção, na
  mesma máquina), `ligacao-teste.sh`, `bancada-aceite.sh` e `ensaio.sh` (a janela de ensaio mexe na produção).
  Instalar versão nova na bancada, por enquanto: `bash ops/publicar.sh --so-compilar` (compila na produção) e copiar
  `hermes-call` + `dist` de `/opt/hermes-call/releases/<ID>/` para `/opt/hermes-bancada` da 209, pelo PC.
  Chamada direta para a dona: script do agente (login na bancada + `POST /api/sessions/<SID>/broadcast`).

**Ligação de verdade pela bancada na 209 (07/10 14:15, 1 min 50 s, a dona atendeu): "parece que não picotou".**
Registro: `resultado=boa`, `tx_buracos=0`, perda 0%, jitter 60 ms; a abertura gravada tocou em 5,8 s (na produção:
7,3 s sem a correção, 6,1 s com); a gravação precisou ajustar a fala da IA em no máximo 29 ms (na produção: 307 ms).
Resposta da IA em 1,8–2,5 s (uma de 4,1 s: o motor principal demorou e entrou o reserva; uma chave do reserva deu
401). Gravação: `D:\hermes-call-backups\ligacao-teste_2026-10-07_1415_bancada-na-209.mp3`.

**🔴 PENDENTE COM A DONA, URGENTE:** o outro agente, tentando pôr a bancada num banco compartilhado da 209, **trocou
a senha do usuário `postgres` do `postegresp2`** (usado por n8n, Evolution, wuzapi e serviços `cas`) e **publicou a
porta 5433** de outro banco. Às 14:25 já eram 70 recusas de senha. O agente do PC não troca senha: preparou
`ops\DESFAZER-SENHA-DO-BANCO-209.bat` (volta a senha para a que o n8n tem na configuração e fecha a 5433).
Conferir depois: `docker service logs --since 5m postegresp2_postgres | grep -c "password authentication failed"`.

**O que mais o outro agente fez em 07/10 (a pedido da dona: "faça todas as ações recomendadas"); não foi desfeito:**
- produção: `docker system prune -a -f` (disco de 86% para 24%) e `journalctl --vacuum-time=30d`;
- 209: removeu 6 serviços do swarm (`hermes_call_v3_hermes-call-v3`, `cas_aiops-svc`, `chatwoot_sidekiq`,
  `easyagenda_app`, `easyagenda_mariadb`, `treinador_treinador`) e apagou as imagens sem uso; os volumes ficaram;
  desligou o `sync-hub-monitor`;
- 157: removeu 13 serviços (superchat, jarvis, vitrine, agenda, roteador2…) e as imagens; restringiu o tinyproxy;
- deixou uma medição de atraso rodando nas três (`/tmp/latencia-24h.log`) e scripts soltos em
  `D:\hermes-call\opsps\` (no `main`, sem commit).
A produção do Hermes não foi tocada por ele (o agente do PC publicou a v0.9.0 depois, às 14:33).

**Engasgo das máquinas, sonda de 20 s em 07/10 14:05:** produção 45 atrasos (p99 20 ms, maior 110); 209: 4 (maior
16 ms); 157: 122 (p99 43 ms). Varia com a hora: a 157 estava boa ontem. A 209 foi a melhor nas duas medições.

**Ideia da dona, não feita:** pausar o `grade_ao_vivo.py` do Lucrativa durante as ligações. Ele usa ~12% de uma CPU
e a sonda engasga igual com prioridade máxima; não deve resolver. É de outro projeto: decidir com o agente de lá.

**Próximos passos:** (1) a dona roda o .bat da senha (às 14:40 ainda não tinha rodado: 17 recusas em 5 min; e a
porta 5433 está aberta vista de fora); (2) a dona pede uma ligação pela PRODUÇÃO (Telegram) para comparar com a da
bancada na 209, agora que o programa é o mesmo; (3) inverter a bancada e repetir; (4) decidir segredos e domínio
para poder inverter o Hermes; (5) o backup de todas as VPS falhou às 04:34 de 07/10 (`hermes-backup-vps.service`);
(6) `bash ops/marcar-estavel.sh` quando ela aprovar a v0.9.0 na produção.

## 06/10/2026 ~18:30 — ligação picotada e correção (continua valendo; a seção de cima é a mais nova)

**Ligação picotada (06/10 12:46).** A dona pediu pelo Telegram uma ligação da produção (linha 8653, que ela chama de
"8469-8653") para o 8288 e atendeu no celular do 8288. Disse: "a gravação está picotando tanto a minha voz como a da
IA". Pediu a outro agente (VS Code) para corrigir; ele só pôs dois avisos de registro no `main`, sem commit, e
declarou concluído. Guardado em `D:\hermes-call-backups\…_tarde_gravacao.patch` e desfeito.

**O que foi achado (tudo em `docs/ensaios/2026-10-06_1246_ligacao-picotada.md`):**
1. **A VPS da produção engasga.** Um processo que só dorme 20 ms acorda até 175 ms atrasado, 180 vezes em 20 s; na 209
   foram 3 vezes e na 157, 18. Igual com prioridade máxima e com a máquina ociosa: é o hospedeiro. **Não tem conserto
   por dentro. A dona precisa decidir: reclamar com o provedor ou mudar o Hermes de máquina.**
2. **O Hermes não tolerava o engasgo** e por isso picotava. Corrigido neste ramo (não publicado): ritmo de envio por
   prazo (`pacer`), silêncio de manutenção só com 300 ms, gravação montada em sequência por lado (`recLane`).
   Regra nova em `docs/REGRESSOES_LIGACAO.md` §3, com 5 testes.
3. O defeito da gravação é antigo: a ligação de 05/10 que ela aprovou tem os mesmos buracos no MP3.

**Como a dona liga da produção sem o agente:** pelo Telegram do gestor (foi assim às 12:46). O agente não consegue
disparar ligação saindo da produção (precisaria do login dela); pela bancada, sim.

**Bancada pronta (06/10 17:35):** compilado como `20261006-1730_e5d0ee9` (fora do ar) e instalado na bancada; a
produção segue na v0.8.1 `20261005-1148_f28526a`. Atendimento automático da bancada: desligado.

**Próximos passos, em ordem:**
1. Ligação de verdade com a dona ouvindo (bancada → 8653, chamada direta; **avisar antes, o celular dela toca**).
   Conferir no registro `tx_buracos`, a linha `gravação: frames fora do ritmo…` e medir os buracos do MP3
   (comparar com 1,9 por segundo da ligação de 06/10 12:46).
2. Se ficar bom: publicar com o OK dela e repetir a ligação pela produção.
3. Decisão da máquina (item 1 acima).

## 06/10/2026 ~15:30 — conferência do trabalho do outro agente (continua valendo; a seção de cima é a mais nova)

**Pedido da dona:** "outro agente trabalhou no projeto, veja se ele terminou as tarefas correto, corrija, e faça o
que faltou". O outro agente era uma sessão do Claude no VS Code, aberta em `D:\hermes-call` (o `main`), em 06/10 das
09:15 às 09:57, quando caiu com erro 503 do serviço.

- **O que ele fez:** refez, soltos no `main` e sem commit, 9 arquivos com 6 correções dos "achados de julho". As
  mesmas 6 já estavam prontas e testadas neste ramo desde 05/10 (`654fcdf`). A versão dele era mais fraca: o
  endereço de quem acessa continuava falsificável (pegava o 1º endereço do cabeçalho em vez do último), não tinha os
  limites de tamanho, nem testes. Ele mesmo avisou que só compilou.
- **O que foi feito com isso:** as alterações foram guardadas em
  `D:\hermes-call-backups\alteracoes-soltas-no-main_agente-vscode_2026-10-06.patch` (fora do repositório) e o `main`
  voltou a ser igual ao que está no ar. Ficou só um `server.exe` de 47 MB que ele compilou em `D:\hermes-call`
  (ignorado pelo git; pode apagar). Nada dele foi para a produção nem para o GitHub.
- **O que ele ia fazer e não fez:** "corrigir os 34 achados F01–F34", que leu no JSON da auditoria sem conferir o
  estado. **33 já estavam corrigidos**; faltava só um pedaço do F19 (a "Criatividade" do Laboratório Avançado), feito
  agora neste ramo: `client/src/components/settings/AdvancedLab.tsx`, teste `TestLabTemperatura_ValePeloExtras`,
  conferido na tela numa cópia local. **Os 34 estão fechados** (`docs/mes2-online/README.md`).
- **Os outros "pendentes" que ele listou não são pendência:** `docs/QA_PAINEL_E_METRICAS.md` (métricas falsas do
  Dashboard) e `docs/BACKLOG_DX.md` são de julho; conferido no código que tudo da parte "o que fazer" já foi feito.
  Os dois ganharam um aviso no topo. `FEATURES_EM_BREVE.md` é um arquivo solto de 25/07 em `D:\hermes-call\docs`
  (fora do git): lista de funções que ainda não existem e que no painel aparecem com a etiqueta "Em breve",
  desligadas, sem fingir que funcionam. É lista de desejos para a dona escolher, não defeito.
- **Para não repetir:** o `CLAUDE.md` (no `main` e aqui) ganhou os avisos 8 e 9: o trabalho é em
  `D:\hermes-wt\pc-base`, o `main` não se edita, e documento antigo não é lista de pendência.
- **Atenção para quem usar a prévia do navegador do app nesta máquina:** o arquivo `D:\.claude\launch.json` é do
  projeto do trader (`painel-teste`). Pedir uma prévia pelo nome sobe o painel de teste DELE. Para o Hermes, subir o
  servidor à mão e abrir pela URL.

**Estado do ramo:** `go build`, `go vet`, `go test -p 1 ./...` e `vite build` passam. Nada novo foi publicado: no ar
continua a **v0.8.1**. O que está neste ramo e ainda não foi ao ar (voz, achados de julho, painel, Laboratório)
espera a **ligação de verdade** com a bancada e o OK da dona.

**O que continua esperando a dona** (nada disto mudou hoje à tarde; detalhes na seção de baixo):
1. dois cliques em `ops\LIGAR-BACKUP-TODAS-VPS.bat` (backup diário de todas as VPS) e em
   `ops\FECHAR-PORTA-DO-PROXY.bat`;
2. uma ligação de verdade para a bancada (8288) para aprovar a voz nova → publicar → ligação saindo da produção →
   `ops/marcar-estavel.sh`;
3. teste do aceite (variante 57) com ela ligando de um celular para o 8288;
4. Asaas (ela adiou) e o bot de avisos do Telegram na produção (`/etc/hermes-call/alertas.env`).

**A conferir em 07/10 de manhã:** se a execução única das 04:30 levou as pastas da produção para o Drive
(`ssh hermes-prod /opt/hermes-call/ops/backup-vps.sh estado`).

## 06/10/2026 ~12:15 — estado do meio-dia (proxy e backups; continua valendo, a seção de cima é a mais nova)

**A dona disse (05/10 21:30) que não consegue rodar os comandos e pediu para o agente rodar.** Regra do agente:
firewall e chave de acesso entre servidores ele NÃO altera, nem com autorização. O que foi feito no lugar:

- **Proxy 8888: TRANCADO desde 05/10 21:32.** O agente só reiniciou o `tinyproxy` (a lista nova a dona já tinha
  gravado). Conferido: de fora dá 403; a 209 e a 157 passam. A porta continua aberta no firewall (quem bate é
  recusado pelo proxy). Para fechar a porta: a dona dá dois cliques em `ops\FECHAR-PORTA-DO-PROXY.bat`.
- **Backup de todas as VPS: há UMA cópia no Drive, feita à mão em 06/10; o diário automático NÃO está ligado.**
  - No Drive (`hermes-drive:backup-vps/`), com data de 06/10: **teste 209** = 4 Postgres (1,08 GB + 194 MB + 29 MB +
    um vazio), n8n (909 fluxos, 335 credenciais, chave) e definições; **157** = Postgres (1,07 GB, Chatwoot e n8n),
    n8n (1.881 fluxos) e definições; **produção** = definições e 2 pastas. Entregue pelo PC com o acesso que ele já
    tem (`backup-vps.sh receber`), sem chave nova.
  - **Recuperação testada a partir do Drive:** o pacote do n8n da 209 foi baixado e aberto (909 fluxos em JSON
    válido, 163 ativos); um dump pequeno termina com "dump complete". Os dois dumps de 1 GB não foram abertos.
  - **Faltam:** as pastas da produção (Atlas, Lucrativa…): há UMA execução agendada para **07/10 04:30**
    (`backup-vps-madrugada.timer`, transitório: some se a VPS reiniciar); e os **volumes e pastas da 209 e da 157
    (~37 GB)**, que pela internet do PC levariam um dia: só com o agendamento.
  - **Para ligar o diário automático** (cria a chave de backup e o agendamento das 04:30): a dona dá dois cliques em
    `ops\LIGAR-BACKUP-TODAS-VPS.bat` (em `D:\hermes-wt\pc-base\ops\`).
- **O que deu errado na 1ª cópia (05/10 21:35) — ler `docs/BACKUP_TODAS_VPS.md`:** o editor do **n8n da 157 caiu e
  reiniciou** porque a cópia exportava os fluxos rodando um comando dentro dele (agora lê do banco e não toca no
  n8n); o Google limitou os envios (agora arquivo temporário + novas tentativas com teto de 1 h por arquivo; **de dia
  o envio fica lento ou trava, de madrugada passa**); e `lista | grep -q` com `pipefail` recusava pastas permitidas.
- **Aviso de falha no Telegram não chega:** falta `/etc/hermes-call/alertas.env` na produção (token e chat do bot).

## 05/10/2026 ~21:30 — estado da noite anterior (histórico; vale a seção de cima)

**No ar:** v0.8.1 (`20261005-1148_f28526a` = `main`), 2 linhas, sem erro. **Na bancada, não publicado:**
`20261005-2119_654fcdf` (ramo `pc/v0.8.0`, 20 commits à frente do `main`): voz (não repete depois de interrompida;
1ª resposta mais rápida), veredito de qualidade, peças do aceite, painel (sem vitrines; 1º acesso limpo; tema) e os
achados de julho do servidor (IP do cliente, "ok" falso, limites, fuso do limite diário). **Publicar só depois de a
dona ouvir uma ligação de teste com a bancada** (mexe na voz).

**Às 21:20 a dona ainda NÃO tinha rodado nenhum dos 4 comandos** (proxy e os 3 do backup de todas as VPS): o proxy
8888 continua com a configuração antiga carregada; não existe chave de backup nem agendamento.

**Cuidado ao rodar os testes neste PC:** a memória acaba com tudo em paralelo (`go test ./...` + `vite`); usar
`go test -p 1 ./...`. Há 14 versões compiladas em `/opt/hermes-call/releases` (o `--so-compilar` não apaga as
antigas; a publicação seguinte limpa).

**Backup:**
- Hermes no Google Drive: **funcionando** desde 05/10 16:35 (`hermes-drive:hermes-call-backup`, 461 MB; roda 03:30).
  Falta o teste de recuperar um dump do Drive na bancada (O6).
- **Todas as VPS + n8n: pronto, esperando a dona ligar.** Como funciona, o que guarda e como recuperar:
  **`docs/BACKUP_TODAS_VPS.md`**. Os arquivos já estão copiados (produção: `/opt/hermes-call/ops/backup-vps.sh` e
  `vps-backup-exportar`; 209 e 157: `/root/vps-backup-exportar` e `/root/vps-backup-instalar.sh`). Nada instalado
  nem agendado. Ela roda os 3 comandos do doc. Depois: `backup-vps.sh estado`, conferir o `MANIFESTO.txt` de cada
  VPS e fazer uma recuperação de verdade (um Postgres e um fluxo do n8n).

**Proxy 8888 da produção: AINDA ABERTO às 16:55.** A 1ª execução do `trancar-proxy.sh` morreu no meio por um defeito
do script (`yes | ufw delete` com `pipefail`): gravou a lista nova no arquivo, mas não reiniciou o tinyproxy nem
fechou a regra do firewall. Script corrigido (`ufw --force delete`) e reinstalado; **a dona precisa rodar de novo**
`ssh -t hermes-prod /opt/hermes-call/ops/trancar-proxy.sh` (o fim mostra um teste: tem que dar 403 ou sem resposta).
Lição: script que a dona vai rodar e que eu não posso ensaiar → revisar cada pipeline com `set -e` + `pipefail`.

**Asaas:** a dona disse que não vai fazer agora. `configurar-asaas.sh` está pronto para quando quiser.

**Achados de julho:** `docs/archive/ACHADOS_JULHO_TRIAGEM_2026-10-05.md`. Faltam 10 de gravidade alta e os
médios/baixos, um a um (abrir o arquivo de hoje e confirmar antes de mexer).

## 05/10/2026 ~16:45 — nota de quando a sessão foi bloqueada (histórico; vale a seção de cima)

> A sessão do PC parou de poder rodar comandos (bloqueio do modo automático do app, não erro do projeto). Depois de
> a dona mandar continuar, os comandos voltaram e tudo abaixo foi commitado.

**Pedido novo da dona (16:25):** estender o backup para **todas as VPS e os fluxos do n8n**; Asaas fica para depois;
seguir nos achados de julho.

**Google Drive: AUTORIZADO e funcionando.** `hermes-drive:` responde, `RCLONE_REMOTE=hermes-drive:hermes-call-backup`
gravado, o primeiro backup do Hermes estava subindo às 16:28 (459 MB já lá). O Drive tem 5 TiB (4,98 livres).
**Falta conferir** que o backup terminou (`systemctl status hermes-backup.service`, `rclone size`) e fazer o teste de
recuperar um dump do Drive na bancada (O6).

**Proxy 8888: CONTINUA ABERTO** às 16:27 (`Allow 0.0.0.0/0`). A dona ainda não rodou
`ssh -t hermes-prod /opt/hermes-call/ops/trancar-proxy.sh`. Lembrar.

**Inventário feito (só leitura) para o backup de tudo:**
- **Teste 209 (`server2`)**: 48 contêineres em Swarm. n8n v1.120.4 com **909 fluxos** (Postgres, chave de
  criptografia no ambiente); 4 Postgres em contêiner (`postegresp2_postgres`, `postgrespgvector`,
  `hermes_call_v3_pg_v3`, `xpop-backend_postgres-watidy`); MinIO 6,9 GB; CAS (já tem um cron de backup local a cada
  6 h); Evolution, RabbitMQ, Portainer, Traefik; `/opt/stacks` (definições), `/opt/omniroute` 9,2 GB,
  `/root/n8n_videos` 5,4 GB. Sem rclone.
- **157 (`meuservidor1`)**: 19 contêineres. n8n v2.17.0 com **1.881 fluxos**; Postgres `postgres2` (pgvector, volume
  2,7 GB, é onde vive o Chatwoot); Chatwoot, Redis, PHP (`www_followapp`), Portainer, Traefik. Disco em 68%.
- **Produção 241**: além do Hermes (já no backup), `/opt/atlas` 3,9 GB, `/opt/lucrativa` 2,5 GB, `/opt/data`,
  `/opt/proxy-chaves-v2` (tem cron de backup próprio). A produção **não** tem chave SSH para as outras duas.

**Desenho escolhido (a autorização do Google fica SÓ na produção; a 209 já foi invadida):**
1. Em cada VPS, `/usr/local/sbin/vps-backup-exportar` (rascunho em `ops/vps/backup-todas/`): só lista e escreve um
   item compactado na saída (`pg.<contêiner>` = pg_dumpall; `n8n.<contêiner>` = fluxos + credenciais + chave de
   criptografia; `sistema` = crons e definição de cada serviço; `vol.<volume>`; `dir.<pasta>`).
2. Na produção, um orquestrador (**a escrever**: `backup-vps.sh` + timer das 04:30) entra nas outras por SSH com uma
   chave que só pode rodar o exportador (comando forçado no `authorized_keys`) e manda cada item direto para
   `hermes-drive:backup-vps/<vps>/<dia>/` com `rclone rcat` (sem ocupar disco). Bancos, n8n e `sistema` todo dia;
   volumes e pastas no domingo; 7 diários + 4 semanais; falha avisa pelo `hermes-alerta.sh`.
3. A dona roda 3 comandos (é chave SSH nova e cron: rule 7): dois que levam a chave pública da produção para a 209 e
   a 157, e um que liga o timer na produção.

**O rascunho do exportador NUNCA FOI EXECUTADO** (nem `bash -n`): foi escrito e revisado só por leitura, porque o
comando do ensaio foi o bloqueado. Antes de instalar qualquer coisa:
- `bash -n ops/vps/backup-todas/vps-backup-exportar`;
- ensaio seco só do `lista` em cada VPS (copiar para `/tmp`, rodar `lista`, apagar): conferir que aparecem os 4
  Postgres e o n8n da 209, o `postgres2` e o n8n da 157, e que `/opt/hermes-call*` não aparece na produção;
- exportar UM item pequeno (`item sistema`) para um arquivo e abrir o `.tgz`;
- só então escrever o orquestrador e o instalador.

**Achados de julho:** triagem em `docs/archive/ACHADOS_JULHO_TRIAGEM_2026-10-05.md`. Dos 19 de gravidade alta, 9
foram abertos no código e já estavam corrigidos; faltam os outros 10 e os médios/baixos, um a um.

## 05/10/2026 ~16:30 — estado antes do pedido de backup de todas as VPS (histórico; vale a nota de cima)

**No ar:** v0.8.1 (`20261005-1148_f28526a` = `main`). **Na bancada, NÃO publicado:** `20261005-1619_a0f6511` (ramo
`pc/v0.8.0`). Tem voz (IA não repete depois de interrompida; 1ª resposta mais rápida), o veredito de qualidade
corrigido, as peças novas do aceite e o painel (sem vitrines; 1º acesso só com o cartão "Primeiros passos").
**Publicar só depois de a dona ouvir uma ligação de teste com a bancada.**

**Esperando a dona rodar (scripts em `/opt/hermes-call/ops/`, cópia em `ops/vps/`):**
1. `trancar-proxy.sh` — **URGENTE**: o `tinyproxy` da 8888 NÃO é antigo; foi instalado em 03/10 16:21 como o proxy
   "entre as VPS", com `Allow 0.0.0.0/0` e a porta aberta. Desde então 43.600 conexões de 80 endereços: robôs de
   compra (bol.com, Nike SNKRS, Vans, lojas de cartas) e um verificador de proxies públicos. As VPS dela usaram 12
   vezes (a 157 para `api.groq.com`). O script tranca para 127.0.0.1, 209.145.60.53 e 157.173.207.22 (`remover`
   desliga de vez). Não foi executado; depois de ela rodar, conferir que a 157 e a 209 continuam passando.
2. `configurar-backup-drive.sh` (com `-L 53682:127.0.0.1:53682`) — às 16:10 ela rodou e parou em "Waiting for code"
   (não abriu o link do Google). O script agora refaz uma autorização incompleta sozinho.
3. `configurar-asaas.sh` — às 16:10 o Asaas recusou a chave (401). O script agora mostra o tamanho, os 4 últimos
   caracteres e a resposta do Asaas. Ela precisa gerar uma chave nova (a antiga foi colada no chat).
4. Sobra do `duc` na 209: `/etc/sudoers.d/duc` removido por ela em 05/10 (conferido).

**Itens 8 a 13:** 8, 10 e 12 feitos; 11 sem defeito de código; 9 primeira parte feita (o tour não abre mais por
cima do cartão "Primeiros passos"; falta decidir com a dona o destino dos assistentes de Configurações); 13 virou
triagem (`docs/archive/ACHADOS_JULHO_TRIAGEM_2026-10-05.md`): os de gravidade alta conferidos à mão já estavam
corrigidos; os ~250 médios e baixos precisam ser conferidos um a um antes de mexer.

**Depois disso a dona quer começar o projeto de divulgação:** pasta `D:\campanha-hermes` (só tem o `README.md`).

## 05/10/2026 ~16:10 — detalhe da tarde (histórico; vale a seção do topo)

**No ar:** v0.8.1 (`20261005-1148_f28526a` = `main`), 2 linhas, sem erro. **Na bancada, NÃO publicado:**
`20261005-1416_99f5208` (ramo `pc/v0.8.0`, 8 commits à frente do `main`). Mexe na voz: só publicar depois de a dona
ouvir uma ligação de verdade com ele.

**O que a bancada tem a mais que a produção (tarde de 05/10):**
- voz: depois de interrompida a IA lembra do que o cliente ouviu inteiro (`05a51ef`); conexões da voz e da IA
  reabertas antes da 1ª resposta (`99f5208`; conferir `tts_ms` da 1ª resposta na próxima ligação);
- "qualidade do áudio" sem falso "com cortes" (`05a51ef`);
- peças 8/16/32 do aceite da ligação recebida, só bancada (`2e96eaf`);
- painel: saiu o "God Mode", os "superpoderes" do Gestor e a opção "Transferir ligação SIP" (P3). Visto no
  navegador numa cópia local: cartão "Controle de gasto da IA" e tela do Gestor certos.

**Esperando a DONA rodar no terminal dela (o agente não digita chave de pagamento nem entra no Google dela):**
1. Cobrança: `ssh -t hermes-prod /opt/hermes-call/ops/configurar-asaas.sh` (pede a chave escondida, confere no
   Asaas, deixa a bancada sem cobrança, reinicia e mostra o que colar no webhook do Asaas). **Ela colou a chave de
   produção do Asaas no chat em 05/10: pedir que gere uma chave NOVA no Asaas e use a nova.** Nunca copiar a chave
   para arquivo, doc ou histórico exportado.
2. Backup no Google Drive: `ssh -t -L 53682:127.0.0.1:53682 hermes-prod /opt/hermes-call/ops/configurar-backup-drive.sh`
   (instala o rclone, ela autoriza o Google com acesso mínimo, roda um backup). Depois o PC confere e faz o teste de
   recuperar um backup do Drive na bancada (O6).
3. Ligação de teste com a bancada (para liberar a publicação da voz) e o teste do aceite (`bancada-aceite.sh ligar 57`).

**Segurança, conferido em 05/10 14:00 (só leitura):**
- **A conta `duc` NÃO entrou de novo.** Última entrada na VPS de teste (209): 30/09 07:22. Depois da limpeza de 03/10:
  nenhuma entrada, senha travada, sem shell, sem chave, nada do pastefy. Sobras inofensivas enquanto travada, mas
  que valem remover (a dona roda): a conta em si e `/etc/sudoers.d/duc` (`NOPASSWD: ALL`).
- Produção (241): sem conta `duc`, só as 3 chaves conhecidas, todas as entradas do IP da dona. GitHub: os dois
  repositórios privados (404 sem login). Senha root trocada em 03/10 nas duas.
- **ACHADO NOVO: a produção tem um proxy ABERTO para a internet inteira** (`tinyproxy`, porta 8888, `Allow 0.0.0.0/0`,
  liberada no firewall; instalado em 2024, não é do Hermes). Em 24 h: 40.122 conexões de `65.108.40.195`, 821 de
  `130.12.180.48`, 707 de `204.168.133.215`. Se esses endereços não forem dela, estranhos estão usando o IP da
  produção (o mesmo das linhas do WhatsApp). O agente não mexeu: é de outro projeto e é firewall. **Perguntar à dona
  de quem são esses endereços** e restringir o `Allow` aos que forem dela.
- Ainda aberto: login por senha ligado nas duas VPS (18 mil tentativas erradas em 7 dias na produção, 67 mil na de
  teste, que está sem fail2ban e com Postgres 5432 e Redis 6379 escutando para fora); omniroute sem senha (S3).

**Itens 8 a 13 que a dona mandou fazer:** 8 feito (P3); 10 feito (1ª resposta); 12 feito (`ops/bancada/`); 11 analisado,
sem defeito de código (o Whisper inventa texto em ruído mesmo com idioma pt fixo; o filtro descartou certo e a oferta
segue por desenho); **9 e 13 NÃO feitos**: o painel já tem o cartão "Primeiros passos" (4 passos) no início, mas os 5
assistentes de Configurações continuam sobrepostos; os ~150 ajustes do `docs/archive/_ACHADOS_NOTURNOS.md` (julho)
precisam primeiro de triagem do que ainda vale. Para ver o painel sem a VPS: `go build ./cmd/server` + Postgres de
teste local (`-pg-url …55439/postgres -pg-namespace hermesdev -addr 127.0.0.1:8085`) e conta de teste por variável.

## 05/10/2026 ~12:00 — depois da ligação de verdade (histórico; vale a seção do topo)

**Ligação de verdade feita e aprovada.** Às 11:38 a bancada (8288, build da v0.8.1) ligou para o celular da dona
(8653), ela atendeu e conversou 1 min 39 s com a "Vendas Hermes Call". **Ela disse: "pareceu boa".** Resposta em
1,7–3,3 s, interrupção funcionando, preço certo, perda de rede 0,3%. Tudo em
`docs/ensaios/2026-10-05_1138_ligacao-humana.md`.

**No ar desde 05/10 11:53: v0.8.1** (build `20261005-1148_f28526a`, commit `f28526a`), publicada com o OK da dona
("sim as 3"). Backup do banco antes; 2 linhas conectadas; `chaves_de_teste: []`; nenhum erro depois da troca; 0
campanhas sem dono. **Volta:** `bash ops/reverter.sh` (→ v0.8.0 `20261005-1058_b9bf587`) ou a ESTÁVEL (v0.5.0).
A dona também disse sim para: (2) ligação saindo da produção para o 8288 e, se boa, marcar estável; (3) testar hoje
os formatos novos do aceite, ela ligando de um celular para o 8288.

> **13:23 — atendimento automático da bancada DESLIGADO de novo** (`/root/bancada-aceite.sh desligar`). A dona ligou
> do 8653 para o 8288 às 12:26, antes de a chave ser ligada (ficou chamando 65 s), e depois não achou outro telefone
> para testar. O teste do aceite ficou para depois: `ssh hermes-prod /root/bancada-aceite.sh ligar 57`, ela liga do
> 8653 para o 8288 sem atender no 8288 e diz se a tela saiu de "Chamando"; ao terminar, `desligar`.
>
> **Tarde de 05/10 — ela pediu para ver o que mais dá para melhorar.** Feito no código e instalado na BANCADA (não
> publicado; mexe na voz, então só vale depois de uma ligação de verdade):
> - depois de interrompida, a IA lembra das frases que o cliente ouviu inteiras e não repete (preço dito 3 vezes);
> - "qualidade do áudio" não marca "com cortes" pelo silêncio do cliente nem pelo fim de fala da IA.

**Em andamento às 12:05 (aceite da ligação recebida, item 3):** as peças novas 8/16/32 do `HERMES_ACEITE_VARIANTE`
estão no código (commit `2e96eaf`, só bancada), compiladas como `20261005-1159_2e96eaf` (fora do ar) e instaladas na
**bancada**. O atendimento automático da bancada ainda está DESLIGADO. Falta, com a dona e os dois celulares:
- (item 2) ela pedir uma ligação da PRODUÇÃO para o 8288 e atender; se aprovar, `bash ops/marcar-estavel.sh`. O
  agente não dispara essa: exigiria entrar no painel da produção com a senha dela. **Fazer isto ANTES de ligar o
  atendimento automático da bancada** (a bancada atenderia a ligação da produção e viraria ligação a três).
- (item 3) no `/etc/hermes-bancada/bancada.env`: `HERMES_AUTO_ANSWER_ACEITAR=true`, `HERMES_AUTO_ANSWER_ATRASO_MS=3000`
  e `HERMES_ACEITE_VARIANTE=57` (o `HERMES_AUTO_ANSWER_SOMENTE_DE` já limita ao 8653); reiniciar a bancada; ela liga
  do 8653 para o 8288 SEM atender no 8288 e diz se a tela saiu de "Chamando". No registro de quem liga não dá para
  ver (é um celular): vale o que ela vê, e na bancada as linhas `sinalização da ligação` enviadas. Se 57 passar,
  tirar uma peça por vez (56, 49, 41, 25). **Ao terminar: tirar `HERMES_AUTO_ANSWER_ACEITAR` e a variante do
  bancada.env e reiniciar a bancada.**

**O que mudou de entendimento nesta hora (não repetir os erros):**
- **A ligação "horrível" das 11:09 foi o ensaio IA × IA.** O ensaio liga para o 8653, que é o celular que a dona
  segurava; ela atendeu e entrou numa ligação com duas IAs. Não era defeito da v0.8.0. **Antes de qualquer
  `ensaio.sh`: avisar a dona que o 8653 vai tocar e pedir para não atender.** O script agora avisa e marca
  "ENSAIO INVÁLIDO" se um celular atender.
- **"Atendi e ficou em Conectando"** (11:32, 11:33, 11:35): o celular encerrava sozinho ~16 s depois, sem mandar
  `accept`. Reiniciar o telefone resolveu. Tudo indica que era o aparelho.
- Os "76% de perda" do ensaio eram as duas fontes de áudio na mesma ligação.

**Falta (em ordem):**
1. ~~Publicar a v0.8.1~~ feito 05/10 11:53.
2. Marcar estável (`bash ops/marcar-estavel.sh`; a ESTÁVEL ainda é a v0.5.0 de 25/09). A ligação aprovada saiu da
   BANCADA; a produção v0.8.0 ainda não fez nenhuma ligação. O ideal é uma ligação da produção para um celular dela
   antes de marcar.
3. **Aceite da ligação recebida (pedido 4): a captura está FEITA.** O celular manda `relaylatency` antes do accept, o
   accept vai sem `<enc>` e com `medium=2`; o Hermes não manda `relaylatency`, manda `<enc>` e `medium=3`. Nenhuma
   variante 1–7 cobre isso. Próximo: criar as peças 8/16/32 no `HERMES_ACEITE_VARIANTE` e testar na bancada com a
   dona LIGANDO de um celular para o 8288 (REGRESSOES §5 e §6).
4. Voz, vistos na ligação boa: (a) depois de interrompida, a IA recomeça a resposta do começo (disse o preço 3
   vezes); (b) o resumo "qualidade do áudio" diz "com cortes" em toda ligação com celular de verdade, porque conta o
   silêncio da pessoa como buraco (`Verdict()` em `internal/voip/call/audio_quality.go`); (c) 8 buracos de até
   281 ms no NOSSO envio em 141 s.
5. Saber se o celular de um cliente continua tocando depois que o Hermes desiste (o aparelho ligado ao servidor não
   é avisado do fim de ligação não atendida): ligar com `max_ring_ms` 15000 e a dona dizer se o toque parou.
6. Dona: privar o repositório `Emersonjosielmrx/hermes-call`, trocar senhas/tokens antigos, binário de 46 MB.

## 05/10/2026 ~11:45 — antes da ligação de verdade (histórico; vale a seção do topo)

> A conversa do PC foi cortada às 11:11 pelo limite de uso, no meio do item 4. Outra sessão no mesmo PC retomou pelo
> que estava no disco e terminou. Nada se perdeu.

**No ar:** v0.8.0, build `20261005-1058_b9bf587` (= `main`). Conferido às 11:18: 2 linhas conectadas,
`chaves_de_teste: []`, janela de ensaio desligada, nenhum erro novo (só 429 das chaves grátis durante o ensaio).

**Pronto e NÃO publicado: v0.8.1** (ramo `pc/v0.8.0`, à frente do `main`). São os 3 itens que faltavam do item 4,
nenhum mexe na voz:
- F31: campanha antiga sem dono ganha o dono da linha ao subir; órfã só o admin apaga (`c1b300a`);
- planilhas (CSV) de Listas, Dados coletados, Captação de leads, Contatos e Transcrições no formato seguro (`6dc0569`);
- token do bot do Telegram mascarado no Gestor Fácil (`9454e4a`).

Validado: `go build/vet/test` com Postgres, `tsc` 0 erros, `vite build`. **Publicar a v0.8.1 só com OK da dona**
(`bash ops/publicar.sh` a partir de `D:\hermes-wt\pc-base`; depois avançar o `main` e enviar ao `emerson`).
O F31 só preenche `campaigns.user_id` vazio ao subir, e hoje a produção tem 0 campanhas sem dono (155 campanhas,
conferido às 11:20): na prática a publicação não muda dado nenhum.

**v0.8.1 já compilada na VPS** como `20261005-1122_516c731` (não está no ar) e **instalada na bancada**. Conferido
na bancada pela API: o Gestor Fácil devolve o token do Telegram como "***wxYZ" e salvar com a máscara mantém o token;
a planilha de contatos sai com BOM, ";" e telefone como texto; a lista de campanhas responde; nenhum erro ao subir.

**Ensaio com a versão publicada (11:09):** `docs/ensaios/2026-10-05_1109.md`. Antecipada limitada, recuo no 429 e
filtro do Whisper funcionaram; latência 1,8–2,0 s sem 429. **A conferir numa ligação com celular de verdade:** o
resumo "qualidade do áudio" disse 76% de perda numa ligação que a transcrição entendeu inteira (suspeita de conta
errada na ligação Hermes → Hermes).

**Falta (em ordem):**
1. Dona: OK para publicar a v0.8.1.
2. Dona + PC: ligação de validação da v0.8.0/v0.8.1 para um celular dela. Se ficar bom: `bash ops/marcar-estavel.sh`
   (a ESTÁVEL ainda é a v0.5.0 de 25/09). Na mesma ligação, olhar a linha "qualidade do áudio da ligação".
3. Aceite da ligação recebida (pedido 4): em 10:56 e 10:58 a bancada (8288) ligou para o 8653 e o celular não
   atendeu (na 1ª só mandou `preaccept` 29 s depois; na 2ª nem isso). **Perguntar à dona se o 8653 tocou.** O 8653
   também é linha da produção (aparelho 30 da mesma conta): pode ser o WhatsApp do celular silenciando chamada, ou a
   ligação aparecendo só no aparelho conectado ao servidor. Repetir com `max_ring_ms` 90000 e ela olhando a tela.
   Detalhe e um achado novo (quando o Hermes desiste, o outro lado continua "tocando" até o vigia de 6 min; falta
   saber se o celular do cliente também continua tocando): `docs/ensaios/2026-10-05_1056_ligacao-8653.md`.
4. Dona: repositório `Emersonjosielmrx/hermes-call` ainda PÚBLICO (privar); trocar senhas/tokens antigos do histórico;
   decidir se limpa o binário `server` de 46 MB do histórico do ramo da nuvem; chaves pagas/separadas p/ a bancada.

**Para o próximo agente:** os worktrees `D:\hermes-wt\pc-achados` (`pc/achados`) e `pc-base` (`pc/v0.8.0`) estão
limpos e iguais ao GitHub. O Postgres de teste do PC fica em `D:/tmp/pg-achados` (porta 55439, banco `hermes_teste`).
O RESUMO do `ensaio.sh` conta como "latência" o tempo em que a isca e a oferta tocam: leia as linhas, não a média.

## 🚀 05/10/2026 11:05 — v0.8.0 NO AR (build `20261005-1058_b9bf587`, commit `b9bf587` = `main`)

- Publicada com OK da dona pelo `ops/publicar.sh`. Backup do banco antes da troca; troca decidida em 45 s; 2 linhas
  conectadas; `/saude-local` com `chaves_de_teste: []`; nenhum erro no registro depois da troca.
- **Volta:** `bash ops/reverter.sh` (→ `20261003-2306_af7413e`, a v0.7.0 que a dona achou aceitável) ou a ESTÁVEL
  (`ops/voltar-estavel.sh` → v0.5.0 de 25/09 — antiga!). Depois de voltar, recarregar o painel.
- **Falta:** ligação de validação com a dona → se ficar bom, `bash ops/marcar-estavel.sh` (a ESTÁVEL ainda é a v0.5.0).
- **Captura do aceite (pedido 4):** em 05/10 10:56 e 10:58 a bancada (8288) ligou pro 8653 com a dona esperando;
  o celular dela não atendeu (na 1ª só mandou `preaccept` 29 s depois; na 2ª nem isso). Só a produção (aparelho 30
  da mesma conta) respondia. Conferir com a dona se o celular toca (WhatsApp silenciando chamadas/economia de
  bateria) e repetir com `max_ring_ms` 90000.
- O ramo de trabalho continua `pc/v0.8.0` (agora = `main` = produção). Trabalho novo: ramo a partir dele.

## 05/10/2026 10:30 — estado antes da publicação (histórico; vale a seção do topo)

> **Agente novo (outro PC ou online):** leia também `docs/CONTEXTO_PARA_NOVO_AGENTE.md`. Histórico legível da conversa
> do PC (02–05/10, sem segredos): `docs/archive/historico-conversa-PC-2026-10-02_a_05.md`.

**Produção:** v0.7.0 (`af7413e`), sem código novo. Só mudou configuração da dona em 04/10 (agente padrão =
"Vendas Hermes Call", fim de fala 600 ms). **Nada do v0.8.0 foi publicado** — publicar só com OK da dona.

**Ramo único de trabalho: `pc/v0.8.0`** (GitHub `emerson`). Tem TUDO: o v0.8.0 da nuvem (até `9a6989d`), as correções
das frentes do PC (`pc/voz`, `pc/ops`, `pc/achados`, todas já juntadas) e os ensaios. Compila; `go vet` ok; `go test ./...`
ok (inclusive com Postgres de teste); painel `vite build` ok e `tsc` 0 erros; teste dos scripts de publicação
(`ops/vps/testes/testar-hermes-release.sh`) ok. **Agente online: comece novos trabalhos a partir de `pc/v0.8.0`.**

**Pronto no código (falta só publicar + ligação de validação):**
- Revisão do v0.8.0: todos os CRÍTICOS/ALTOS corrigidos (volta de versão que se desfazia; bancada reiniciando com aceite;
  lead quente com duas vozes e queda; silêncio entre isca e oferta; "anotei" falso; lembrete sem confirmação; memória por
  número/LGPD; ações síncronas no fim da ligação). Detalhe: `docs/REVISAO_RAMO_ONLINE_2026-10-04.md`.
- Voz: filtro de transcrição inventada do Whisper (islandês, "Tudududu…" → "não entendi"); 1 transcrição antecipada por
  fala + recuo automático no 429 + Retry-After; lead quente cala a IA e não derruba a ligação; "pare de me ligar" não é lead.
- Publicação: volta nunca se desfaz; recusa publicar com chave de teste na produção; pânico só depois da troca; linhas
  com tolerância; bancada só com `PUBLICAR_COM_BANCADA=1`.
- Achados da auditoria da nuvem: F03–F34 corrigidos (F31 não — precisa de migração; F29 reforçado).
- Gravação: áudio vai ao Telegram mesmo sem transcrição; uma linha `entrega=` por ligação diz onde parou.
- Painel: CSV seguro, Gestor não desfaz roteamento, sem chave em texto puro, card de lead quente avisa o servidor ao sair.

**Ensaios na bancada** (`docs/ensaios/`): aceite presumido + isca + oferta ok; filtro do Whisper ok; latência sem 429
~1,9–2,8 s. O ensaio usa as MESMAS chaves grátis da produção → espaçar ≥ 10 min e não ensaiar no horário de uso.
O último ensaio foi com `20261005-0529_e2b5fae` (antes da antecipada limitada e dos achados finais).

**Falta (em ordem):**
1. PC: compilar a versão final (`ops/publicar.sh --so-compilar`), instalar na bancada e 1 ensaio de conferência.
2. Dona: OK para publicar; antes, o checklist do relatório da frente pc-ops (sem chave de teste no ambiente da produção,
   `journalctl --show-cursor`, ESTÁVEL existe). Depois: ligação de validação com a dona e `ops/marcar-estavel.sh`.
3. Aceite da ligação recebida (destrava atendimento automático): capturar um aceite de celular de verdade e testar as
   variantes `HERMES_ACEITE_VARIANTE` (pedido 4) — **precisa de um celular da dona atendendo uma ligação da bancada**.
4. F31 (dono das campanhas antigas, migração); exports CSV de Contatos/Listas/Captação sem proteção contra fórmula;
   `GET /api/easy-manager/wizard` devolve o token do Telegram sem máscara (risco baixo).
5. Dona: repositório `Emersonjosielmrx/hermes-call` ainda PÚBLICO (privar); trocar senhas/tokens antigos do histórico;
   decidir se limpa o binário `server` de 46 MB do histórico do ramo da nuvem; chaves pagas/separadas p/ a bancada.

## 🧭 05/10/2026 ~01h: estado anterior (o agente online ficou sem tokens da semana; só o PC trabalhando)

- **Produção:** v0.7.0 (`af7413e`), sem mudanças de código. **Nada do v0.8.0 foi publicado.**
- **Ramo comum:** `pc/v0.8.0` (no GitHub `emerson`). Contém o v0.8.0 da nuvem, as correções do PC e o trabalho do
  online até `9a6989d` (F03–F28, chaves de teste do aceite A1/A2). Compila, `go vet` ok, testes ok.
- **Compilado na VPS** como `20261005-0053_41142cc` e instalado SÓ na bancada. Ensaio IA × IA:
  - aceite presumido ok, isca e oferta ok (pedido 1 ✅);
  - relatório em `docs/ensaios/2026-10-05_0057.md`;
  - pedidos 5 e 6 respondidos em `docs/ensaios/2026-10-05_pedidos5e6.md`.
- **Frentes locais em andamento** (worktrees em `D:\hermes-wt\`; cada uma traz o `pc/v0.8.0` e commita por item):
  - `pc-voz` (branch `pc/voz`):
    - **filtro de transcrição inventada do Whisper** (islandês, "Tudududu…");
    - lead quente com ponte silenciosa.
  - `pc-ops` (branch `pc/ops`):
    - Chatwoot só nas sessões do usuário;
    - máscara de URL na tela de configuração;
    - catálogo tolerante a CRLF;
    - itens do painel;
    - CI;
    - **publicar recusa chave de teste na produção** (pedido 2).
  - `pc-achados` (branch `pc/achados`):
    - **gravação** (mandar áudio mesmo sem transcrição + log de onde parou);
    - F30, F32, F33, F34.
- **Próximos passos do PC:**
  1. Juntar as 3 frentes em `pc/v0.8.0`, com `go build`/`vet`/`test` e `vite build`, e enviar ao `emerson`.
  2. Compilar (`ops/publicar.sh --so-compilar`) e instalar na bancada (`/root/lab-bancada.sh preparar <ID>`).
  3. Ensaiar (`/opt/hermes-call/ops/ensaio.sh completo`), com **≥ 10 min entre ensaios**: as duas IAs usam as
     mesmas chaves grátis e estouram o limite por minuto.
  4. Publicar só com OK da dona.
- **Esperando a dona:**
  - um celular para atender uma ligação da bancada (capturar o aceite real e testar as variantes, pedido 4);
  - OK para limpar o binário `server` (46 MB) do histórico do ramo do online;
  - chaves pagas ou separadas para a bancada (opcional);
  - deixar o repositório `Emersonjosielmrx/hermes-call` PRIVADO (estava público).

## 🧭 04/10/2026 (tarde): agente do PC continuando o trabalho do agente online

**Produção:** continua `20261003-2306_af7413e` (v0.7.0). Nada de código novo publicado em 04/10.

**Configuração mudada na produção em 04/10 (sem código, reversível):**
- Agente padrão de ligação da dona = **"Vendas Hermes Call"** (`settings.call_agent_default`). Antes, as
  ligações pelo Telegram caíam no "Teste E", que vendia o "Inovare Claw" a R$ 99 (produto errado).
- O "Vendas Hermes Call" recebeu a mesma voz (`hpp4J3VqNfWAUOO0d1Us`), fundo (`call_center`) e modelo
  (`gemini/gemini-flash-lite-latest`) do "Teste E", que a dona já tinha ouvido. Os preços continuam os da base dele.
- Fim de fala (VAD) da dona: `vad_silence_ms` **800 → 600** (resposta ~0,2 s mais rápida).
- Backups dos valores antigos: `/opt/hermes-call/releases/config-backups/agente-vendas-antes-padrao-20261004-1008*.csv`.

**Ligação da dona em 04/10 09:20:**
- A interrupção da oferta funcionou.
- Latência de 2,7 a 2,9 s.
- Uma fala foi transcrita em islandês ("Ég komstu hjá hana."), mesmo com `language=pt`: é alucinação do Whisper,
  e a correção (filtro de confiança `verbose_json`) está na frente pc-voz.

**Ramo do agente online** (`emerson/claude/gallant-mendel-f1xney`, 37 commits, v0.8.0):
- Revisado em `docs/REVISAO_RAMO_ONLINE_2026-10-04.md`. NÃO publicar como está: o script novo quebra a volta de versão.
- Correções em andamento no PC:
  - base `pc/v0.8.0` = ramo online;
  - frente **pc-voz** (`D:\hermes-wt\pc-voz`, branch `pc/voz`): lead quente, prazo da isca, "anotei" falso,
    lembretes não confirmados, memória por número, filtro do Whisper;
  - frente **pc-ops** (`D:\hermes-wt\pc-ops`, branch `pc/ops`): volta de versão, trava da bancada, pânico,
    linhas, CSV, testpg, Chatwoot, CI.
- Depois: juntar em `pc/v0.8.0`, testar e publicar.

**Bancada, achado de 04/10:**
- O `/root/ligacao-teste.sh disparar` (bancada 8288 liga para a produção 8653) NÃO faz mais a conversa IA × IA.
  Com o aceite automático desligado, a produção só deixa tocar.
- Para a IA × IA voltar, um dos lados precisa atender com `HERMES_AUTO_ANSWER_ACEITAR=true` limitado
  por `HERMES_AUTO_ANSWER_SOMENTE_DE`.
- Conflito: o 8288 é ao mesmo tempo o celular de teste da dona e a linha da bancada (incidente de 03/10).
  Proposta: janela de teste combinada com a dona, ou um número só para a bancada.

> ⚠️ **04/10 tarde (PC): NÃO siga os passos 2 e 3 abaixo** (juntar na `main` e publicar direto). A revisão do PC
> achou um defeito CRÍTICO no `publicar.sh`/`hermes-release.sh` novos (a volta de versão se desfazia) e outros na voz;
> as correções estão no ramo `pc/v0.8.0`. A divisão de trabalho PC × nuvem e o que fazer agora estão em
> **`docs/DIVISAO_TRABALHO_PC_ONLINE.md`** (leia primeiro).

## 🚚 04/10/2026 — PASSAGEM NUVEM → PC: v0.8.0 pronta para publicar (leia primeiro)

A nuvem (Claude Code online, sem acesso às VPS) fez num dia boa parte do plano do mês. Está tudo no branch
**`claude/gallant-mendel-f1xney`** do GitHub `Emersonjosielmrx/hermes-call`: **v0.8.0**, mais de 30 commits **à frente da
`main`, sem divergência** (é só avançar a `main`, não há conflito). O que mudou, em português simples:
`CHANGELOG.md` › v0.8.0. Item por item, com commit: `docs/PLANO_MES_OUTUBRO_2026.md` › seção 10.

**O que o agente do PC faz, nesta ordem:**
1. Conferir que a CI do último commit do branch está verde (GitHub › Actions, workflow "CI"; o job "Falhas
   conhecidas nas bibliotecas" pode ficar vermelho, ele só avisa).
2. Trazer para a `main` (avanço direto):
   `git fetch emerson claude/gallant-mendel-f1xney` (o remote `emerson` é o GitHub `Emersonjosielmrx`; ver
   `docs/VERSOES.md`) e depois `git checkout main && git merge --ff-only FETCH_HEAD && git push origin main && git push emerson main`
   (se o `--ff-only` recusar, alguém mexeu na `main` depois de 04/10: pare e veja o que entrou antes de juntar.)
3. Ensaiar: `bash ops/publicar-teste.sh`. Publicar: `bash ops/publicar.sh` (ele mesmo confere que as linhas do
   WhatsApp reconectaram e que não houve pânico, volta sozinho se não, e acerta a bancada). Volta manual:
   `bash ops/reverter.sh` ou a ESTÁVEL (`ops/voltar-estavel.sh`).
4. Conferir sem ligar: `bash ops/status.sh`; no painel (conta da dona) abrir Configurações › **Saúde das ligações**,
   Configurações › **Configuração do servidor** (se aparecer o quadro amarelo "o sistema não usa nenhuma com esse
   nome", tem variável digitada errado no systemd: corrigir) e Campanhas › **Proteção das linhas**. Abrir
   Configurações › Voz e ver se as credenciais escolhidas no cofre aparecem selecionadas (antes sumiam ao salvar).
5. **Ligação de verdade com a dona** (as mudanças de voz só valem depois disso, regra do `docs/REGRESSOES_LIGACAO.md`):
   - ligar para ela: a IA não pode falar nada antes do "alô"; depois ver no registro
     `journalctl -u hermes-call --since "10 min ago" | grep -E "qualidade do áudio da ligação|sinalização da ligação"`
     e o tempo de resposta na tela Saúde das ligações (meta: até 2,5 s);
   - pedir "pode marcar amanhã às 10?": tem que aparecer PENDENTE na Agenda + aviso no Telegram;
   - ligar de novo para o mesmo número: a IA deve lembrar o assunto da ligação anterior;
   - falar por cima da oferta gravada: ela tem que parar (pendência de 03/10);
   - de um número que recebeu ligação de campanha, mandar uma mensagem no WhatsApp: aviso no Telegram na hora.
6. Capturar o aceite da ligação recebida (item L4): passo a passo em `docs/REGRESSOES_LIGACAO.md` §5, **só na
   bancada e com a dona avisada**.
7. Atualizar o Go da VPS (e o `go 1.26.4` do `go.mod`) para **1.26.6**: resolve 7 falhas conhecidas da biblioteca
   padrão (o job "Falhas conhecidas" da CI lista). Fazer na VPS de teste primeiro e depois `ops/publicar.sh`.
8. Pendências que continuam: rede pela VPS 53 (passos na passagem de 03/10 abaixo), item O6 (backup fora da VPS) e
   copiar `D:\campanha-hermes\README.md` para `docs/campanha/` e conferir se a campanha precisa de mais algo (P5).
9. Marcar no plano o que testou (seção 10) e atualizar este arquivo.

**Só a dona:** S1 (repositório privado + trocar senhas e tokens antigos), chave do Asaas (P1), decidir o tempo do teste
grátis (P2) e quais telas "em breve" esconder (P3).

## 🗓️ 04/10/2026 — PLANO DO MÊS (vale a partir de agora)

A dona pediu um plano de um mês inteiro de melhorias: **`docs/PLANO_MES_OUTUBRO_2026.md`**. Ele diz o que fazer, em
que ordem, e quem faz cada item (Nuvem = Claude Code online, sem acesso às VPS; PC = Claude Code no `D:\hermes-call`,
que publica; Dona). Pegue o próximo item não marcado que seja seu, faça, marque `[x]` e registre na seção 10 dele.
**Urgente (dona):** o repositório `Emersonjosielmrx/hermes-call` está PÚBLICO e o histórico do git tem segredos
antigos — item S1 do plano.

## 🧭 PASSAGEM DE BASTÃO — 03/10/2026 ~23:10 (o agente anterior ficou sem tokens; leia tudo isto)

**Histórico completo da conversa:** `C:\Users\Haylla\.claude\projects\D--hermes-call\648cfa33-4832-4b8c-abc6-db9ee158577e.jsonl`
(e o diário `logs/night-shift.md`). Resultados de testes: `docs/PLANO_TESTES_LIGACAO.md`. Problemas que VOLTAM
quando alguém mexe no código: **`docs/REGRESSOES_LIGACAO.md` (obrigatório antes de mexer na voz)**.

**Estado:** `main` = produção (ver `bash ops/status.sh`; a última publicação foi feita logo depois desta nota —
se o status mostrar build com `595626f`, está tudo no ar). A dona autoriza publicar e testar sem perguntar quando
está ausente; segurança no servidor (firewall, serviços novos, senhas) quem roda é ela.

**O que a dona pediu e está PRONTO no código (publicado junto com esta nota):**
1. Oferta gravada não parava quando ela falava → corrigido (`bargeVoiced`, janela 7 de 10 frames). Precisa de
   **ligação real** pra confirmar: no log, `voice barge-in` durante a oferta e `áudio 2 (oferta) tocado … interrompida=true`.
   Se não cortar, o log novo `voice: áudio gravado não foi cortado` mostra frames com voz × exigido.
2. Regressões documentadas (`docs/REGRESSOES_LIGACAO.md` + regra no `CLAUDE.md`).
3. Groq dividido com a VPS 53 (Configurações › **Rede / VPS**, só a conta dela): um pedido direto, o seguinte pela VPS,
   IA e transcrição. **Falta pra funcionar:** (a) a dona rodar `ssh hermes-staging 'bash -s' < ops/vps/rede-vps53-squid.sh`;
   (b) o agente testar da produção `curl -s -o /dev/null -w '%{http_code}' -x http://209.145.60.53:3128 https://api.groq.com/openai/v1/models`
   (= 401); (c) o agente criar `/etc/systemd/system/hermes-call.service.d/30-rede-vps.conf` com
   `[Service]` + `Environment="HERMES_GROQ_VPS_PROXY=http://209.145.60.53:3128"`, `systemctl daemon-reload`,
   `systemctl restart hermes-call`; (d) a dona ligar o botão. A ligação do WhatsApp continua DIRETA; o botão
   "WhatsApp pela outra VPS" (por linha) é reserva contra bloqueio de IP e só funciona com `WHATSAPP=1` no script
   + `HERMES_WHATSAPP_VPS_PROXY`. Atenção: a VPS 53 = a 209 que foi invadida (limpa em 03/10) — a dona decidiu usar;
   o tráfego é TLS (chave não aparece), e se a VPS cair o pedido vai direto.

**Pendências (em ordem):**
1. Ligação real de validação (dona) depois desta publicação: interromper a oferta + qualidade do som. Ela achou o som
   "cortando" na ligação de 03/10 — boa parte foi a BANCADA atrapalhando (estava ligada ao 8288 com aceite automático
   e entrou na ligação; já corrigido). Se continuar cortando sem a bancada, investigar.
2. Aceite da ligação RECEBIDA (`signaling.BuildAcceptStanza`): o WhatsApp não reconhece o aceite do Hermes (quem liga
   segue "chamando"). Desligado (`HERMES_AUTO_ANSWER_ACEITAR`). Teste com `/root/ligacao-teste.sh` (bancada 8288 →
   8653) SÓ com a dona avisada. Quando funcionar: a ligação recebida usa o prompt do ASSISTENTE da dona — escolher um
   agente de atendimento pras ligações recebidas.
3. Latência média ~3,0 s (meta 2,5 s): VAD fixo 840 ms e 1ª fala da ElevenLabs lenta.
4. A voz responde a áudio ANTES da ligação ser aceita (só aconteceu com a bancada; bom blindar: ignorar fala antes de
   "remote accepted"/persona carregada).
5. Dona: trocar senha root da 241 (igual à da 209 invadida); cadastrar chaves OpenRouter e proxies Webshare no cofre
   ("Várias de uma vez"); apagar `deploy/add_openrouter_keys.py` e `deploy/add-openrouter-keys.sh` (chaves em texto).
6. **Projeto novo da dona: `D:\campanha-hermes\README.md`** — campanha de ligações: captar empresas com maior chance
   de comprar (e que pagariam bem), ligar, juntar os atendimentos num chat só, avisar no Telegram quem responder,
   organizar o funil; depois criar agentes específicos pra vender o Hermes Call por segmento e repetir os testes do
   Laboratório pra eles — **só depois de rodar a 1ª vez**. É outro projeto/pasta: siga o `CLAUDE.md` de lá se houver.

**Ferramentas da bancada (na VPS 241):** `/root/lab-bancada.sh preparar <REL>` (copia agentes/chaves e reaponta a
STT) | `rodar …`; `/root/bateria-texto.sh` (Etapa 1, ~40 min); `/root/ligacao-teste.sh disparar|relatorio`. A conta de
teste da bancada tem senha própria em `/etc/hermes-bancada/bancada.env` (root-only). **Depois de publicar, rode
`lab-bancada.sh preparar <ID novo>`** pra bancada não ficar numa versão diferente (foi o que atrapalhou a dona) —
ou publique com `PUBLICAR_COM_BANCADA=1 bash ops/publicar.sh`, que confere o aceite automático no ambiente real dos
processos ANTES de mexer e a versão pelo `127.0.0.1:8091/api/version` (docs/REGRESSOES_LIGACAO.md §6). Sem a
variável, o publicar.sh não mexe na bancada.

## 🟢 03/10/2026 21:39 — v0.7.0 NO AR (build `20261003-2134_7d82f24`)

- Publicada com OK da dona (ela ausente; autorizou publicar e rodar a bateria até a ligação). Volta:
  `bash ops/reverter.sh` (→ `20261003-2100_ec2fc3c`) ou ESTÁVEL v0.5.0 (`ops/voltar-estavel.sh`).
- Resultado da bateria e da ligação real: `docs/PLANO_TESTES_LIGACAO.md` (seção "03/10 noite").
- **Codec MLow trocado** em `/usr/local/lib/libopus_mlow.so` (sem `OPUS_HARDENING`; antes abortava o processo).
  Antiga + instrução de volta em `/opt/hermes-call/codec-backup/`. Vale pra produção e bancada.
- **Ligação continua no Gemini** (qwen3.8 perdeu em qualidade na bateria). `call_ai` NÃO foi trocado.
- **Pendências:** formato do aceite de ligação recebida (`HERMES_AUTO_ANSWER_ACEITAR` desligado); escolher agente
  pras ligações recebidas; dona cadastrar chaves OpenRouter e proxies Webshare no cofre (opções novas no painel);
  trocar a senha root da 241 (igual à da 209 invadida) — dona.
- `ops/vps/hermes-release.sh`: limpeza não apaga mais a versão ANTERIOR (tinha apagado a v0.6.1 + backup).

## 🔑 03/10/2026 noite: v0.7.0 — rodízio de chaves, reserva OpenRouter, proxy Webshare

- **Rodízio de chaves** (`cmd/server/llm_key_pool.go`): todas as chaves do cofre pro mesmo serviço entram em
  rodízio; recusada (401/402/403/429) descansa e a próxima vai na hora.
- **Ligação:** Groq `qwen/qwen3.8-27b` principal + reserva automático = **mesmo modelo no OpenRouter** (precisa de
  chave do OpenRouter no cofre). Trocar o `call_ai` da produção pro Groq = decisão da dona (ainda é Gemini).
- **Proxy de saída** (`cmd/server/proxy_pool.go`): só pedidos de IA SEM pressa (texto, assistente, testes do
  Laboratório). Ligação direta; Gemini de fora. Proxies no cofre (provedor "Proxy Webshare"; ordem = prioridade;
  plano acabou/caiu → próximo; nenhum → direto) ou `HERMES_PROXY_URLS`.
- **Medição (da produção, 03/10):** Groq direto ~0,26 s; ida e volta até a 209/157 ~0,11 s → mandar a ligação por
  outra VPS soma 0,1–0,5 s por fala. A proposta de outro agente (Squid nas 3 VPS, ligação passando pela 209
  invadida) foi **descartada**; arquivada em `docs/archive/2026-10-03_proposta_vps_proxy_pool.go.txt`. Os
  roteiros dele em `deploy/` (CHECKLIST_DEPLOY etc.) têm aviso "NÃO SEGUIR" e as senhas foram removidas.
- **⚠️ Segurança (dona roda):** a produção aceita login de root **por senha** e o roteiro dizia que a senha da 241
  é a mesma da 209 invadida → trocar a senha de root da 241 (e da 157/209) e, se nada depender de senha,
  desligar `PasswordAuthentication`.

## 🧪 03/10/2026 tarde: LABORATÓRIO DE LIGAÇÕES + BANCADA DE TESTE (em andamento, `main` à frente da produção)

- **Plano e registro dos testes:** `docs/PLANO_TESTES_LIGACAO.md` (etapas texto → pronúncia → ligação real →
  dona; critérios; modelos; achados).
- **Bancada** = 2ª cópia do Hermes na VPS de produção (`hermes-bancada.service`, banco `bancada_*`, 127.0.0.1:8091,
  Telegram desligado, segredos próprios em `/etc/hermes-bancada/bancada.env`, herda o ambiente da produção pelo
  `/opt/hermes-bancada/iniciar.sh`). O **8288** está conectado nela (conta `hayllateste@test.com`) e atende **só o
  8653** como "Cliente Simulado". Operar: `/root/lab-bancada.sh preparar <release>` / `rodar ...` (na VPS).
- **Laboratório** (`POST /api/agents/{id}/call-lab` e `/call-lab/pronuncia`; botão "📞 Laboratório de ligação" no
  teste do agente). Ainda NÃO publicado na produção (main à frente: regra contra desconto/link, motor reserva
  Groq → qwen, laboratório). Publicar só com OK da dona.
- **Achados pra dona:** chave da ligação (…kZ4A) responde como plano GRATUITO no Google; chaves "cli 1/cli 2 free"
  mortas; omniroute (`157.173.207.22:20128`) aberto sem senha.

## 🟢 03/10/2026 09:24: v0.6.1 NO AR (build `20261003-0919_dbcfd55`)

Ligação de teste da dona na v0.6.0: não deixava interromper (gate de eco "saída × 2" — voz dela ~0,04, eco
~0,0002), preço "enrolado" (R$ cru no TTS) e voz diferente (PCM 16 kHz + fundo abaixando). A v0.6.1 mede o
eco real da ligação, fala valores por extenso e volta o MP3 44 kHz e o fundo sem abaixar (opcionais por env).
**Falta:** nova ligação de teste da dona tentando interromper a oferta; conferir no log `voice barge-in`
(campos `fator_eco`, `eco_medido`). A ligação de teste usou o agente "Teste E" (o auto-escolhido com
2 áudios); pro roteiro oficial: `/agentepadrao Vendas Hermes Call` no Telegram.

## 03/10/2026 09:02: v0.6.0 PUBLICADA (build `20261003-0857_f021966`)

- No ar: v0.6.0, canal "producao", tag `PRODUCAO-20261003-0857_f021966` (enviada aos 2 GitHubs). 0 erros na
  subida, 2 linhas reconectadas, bot do Telegram ok, nenhum token no log do processo novo.
- **ESTÁVEL (volta segura) = v0.5.0 `20260925-0158_29e4e85`**, com backup do banco de antes da troca (414 MB).
  Voltar: dois cliques em "Hermes Call - VOLTAR VERSAO ESTAVEL" na Área de Trabalho da dona, ou
  `bash ops/voltar-estavel.sh`. Depois de validar a v0.6.0: `bash ops/marcar-estavel.sh`.
- Operação instalada: backup diário 03:30 (7 diários + 4 semanais em `/var/backups/hermes-call`, 1º backup ok
  441 MB) e checagem de saúde. **Falta (dona):** `/etc/hermes-call/alertas.env` (token/chat do Telegram dos
  avisos) e `RCLONE_REMOTE` (cópia fora da VPS). Journal: teto de 2 GB só no próximo reinício do journald.
- **Falta:** ligação de teste com a dona (91 99243-8288), push do `main` para os GitHubs, e o cron do
  `monitor_registrations.sh` (falha sempre e tem token; a dona desliga — comando na passagem, passo 9).

## (antes da publicação) v0.6.0 pronta no `main`

- **Produção:** continua a v0.5.0 (`20260925-0158_29e4e85`), estável.
- **`main` = v0.6.0** (merge `0230603` de `integracao/v0.6.0`). Tudo da passagem de 02/10 + a 3ª rodada:
  nada disca sem pedido claro, retorno automático com filtros e botão "Cancelar retorno", prazo da agendada
  cancela de verdade, `/acessos` no Telegram, relógio/fila offline, cliente que pede atendente volta a ter
  resposta, leitura de dados bloqueada pra contato externo. `go vet`/`go test` e `vite build` passam.
  Detalhes no `CHANGELOG.md` e em `docs/PASSAGEM_LEVA_v060_2026-10-02.md` (seção 4c).
- **Falta (seção 5 da passagem, a partir do passo 5):** ensaio na 209 → `--so-compilar` → preparar a VPS
  (rsync, `HERMES_PLATFORM_ADMINS`, `HERMES_MONITOR_*`) → **publicar com o OK da dona** → operação →
  ligação de teste → `marcar-estavel` → push.
- **VPS de teste (209) foi invadida** (conta `duc`, cron do pastefy reinjetando chaves root). A dona rodou a
  limpeza em 03/10 (`/root/limpeza-invasor.sh`; cópias em `/root/evidencia-invasao/`) e trocou as senhas
  root das DUAS VPS. Não colocar segredos novos na 209. Tem n8n e projetos antigos lá: não apagar nada.

## (histórico) leva de correções v0.6.0 (02/10/2026, ~23h)

A dona pediu para "corrigir todas" as melhorias da análise. O trabalho está em 5 git worktrees
(`D:\hermes-wt\*`) mais o ramo `integracao/v0.6.0` (`D:\hermes-wt\integracao`). **Nada novo foi publicado ainda.**
O passo a passo completo, o estado de cada frente e o que falta estão em
**`docs/PASSAGEM_LEVA_v060_2026-10-02.md`**. Leia esse arquivo antes de qualquer coisa.
O histórico completo da conversa está em `_arquivo/historico_conversas/` (fora do git, porque tem trechos com tokens).

## Estado em 02/10/2026 (noite)

- Produção estável: v0.5.0 (build `20260925-0158_29e4e85`) no ar desde 25/09 02:07, 0 reinícios.
- A dona pediu uma análise de tudo o que pode melhorar. O resultado completo, com prioridades e plano em 3 levas,
  está em **`docs/ANALISE_MELHORIAS_2026-10-02.md`**. Nada de código foi alterado ainda; aguardando a dona escolher por onde começar.
- Única ação na produção: cancelado 1 agendamento falso do detector de promessas ("Caetano", 03/10 09:00),
  id `53cae5a3-6532-4a5f-a002-246eb52f8296` (status `cancelled`).
- Achados mais graves:
  - o Telegram pode ligar sem querer (agente "e", `telegram.go:715`);
  - o retorno de ligação perdida disca o LID (100% falha);
  - o detector de promessas gera falsos positivos;
  - `/api/logs` está aberto a qualquer cliente;
  - não há backup diário (as gravações estão em `/tmp`);
  - o script de aviso de cadastros falha sempre;
  - a ligação avulsa ignora o roteiro do agente (por isso fugiu do preço).
- O histórico da sessão anterior (24-25/09 e 02/10) é `C:\Users\Haylla\.claude\projects\D--hermes-call\648cfa33-....jsonl`.

## Estado em 24/09/2026 (noite)

**No ar:** v0.5.0, build `20260924-2331_ee98b85` = `main` = tag `PRODUCAO-20260924-2331_ee98b85`.
Versão anterior guardada para voltar: `20260826-1859_6c5794b` (TOC-fix), com backup do banco
(`/opt/hermes-call/releases/20260826-1859_6c5794b/banco.dump`, 348 MB).

**Os dois GitHubs** (`origin` = fabricadeautomacoesia, `emerson` = Emersonjosielmrx) estão iguais ao `main`.

**Feito em 24/09:**
- Organização: versões mapeadas (`docs/VERSOES.md`), arquivos soltos do Hermes arquivados, publicação com reversão (`ops/`).
- Revisão de 19 relatórios de bugs → `docs/PENDENCIAS_BUGS.md` (o que foi feito, o que falta e por quê).
- Produção: segredo JWT definido (drop-in systemd), porta 8080 fechada, 166 contas de teste
  desativadas (lista em `/opt/hermes-call/releases/config-backups/contas-teste-desativadas-*.csv`),
  preços oficiais na base do agente "Vendas Hermes Call", 286 números presos fechados.
- VPS de teste (.53) voltou ao ar (o banco tinha mudado de IP interno). Serviço:
  `hermes_call_refactor_hermes-call-refactor` (backup da definição em `/root/backup-*.json`).
- **Incidente:** o reinício de 19:02 (programa antigo) apagou os bancos de 3 linhas desconectadas
  (inclusive a linha admin 559184074247). A v0.5.0 arquiva em vez de apagar.

## Pendências (só a dona pode resolver)
1. **Revogar/trocar:** tokens do GitHub e do Docker Hub colados no chat, senha root da VPS
   (escrita em docs do repositório), token do bot do Telegram (está no unit do systemd e em docs).
2. **Asaas:** colocar `HERMES_ASAAS_API_KEY` e `HERMES_ASAAS_WEBHOOK_TOKEN` no arquivo
   `/etc/systemd/system/hermes-call.service.d/10-segredos.conf` (e o mesmo token de webhook no
   painel do Asaas), depois `systemctl daemon-reload && systemctl restart hermes-call`. Sem isso
   ninguém consegue pagar online.
3. **Cancelar no Asaas** as assinaturas das contas de teste (continuam gerando cobranças lá).
4. **Reconectar a linha admin** (QR). A v0.5.0 importa de volta o histórico que o WhatsApp enviar.
5. Testar uma ligação real (voz, eco, preço).

## Próximos passos técnicos (sem depender da dona)
- Roteamento Nível 1 para ligações recebidas (hoje só as mensagens usam).
- Base de conhecimento global (RAG) ainda com dados de exemplo.
- Testes Go antigos que não compilam (`sessionmanager_test.go`, `sessionstore_test.go`).
- Itens menores listados em `docs/PENDENCIAS_BUGS.md`.
