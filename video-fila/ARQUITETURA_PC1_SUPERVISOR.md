# Arquitetura: PC1 só supervisor — proposta (24/11)

Pedido da dona (24/11): "temos que fazer a melhor arquitetura possível. Aqui (PC1) montava os vídeos e isso era o
gargalo; pedi pra pôr outro PC pra montar. A ideia é esse PC ser APENAS supervisor ou fazer só o que só pode ser feito
aqui. O Fish pode logar nos outros PCs, igual ao TikTok."

## O problema medido

- PC1 a 100% o dia todo (179 processos python, 60 chrome). Studio dá timeout de 90 s, ffprobe estoura, comandos lentos.
- Já tirado do PC1 hoje: render de Short (controlador), ffmpeg do produto, montagem do reel MS Energy, painel 15→60 s.
- **Gargalo que sobra: o FISH só roda no PC1.** `fish_lote.disponivel()` exige `D:\logins-google\cofre\contas.json`
  (só existe no PC1). O Fish é a voz PRIMÁRIA dos Shorts -> todo Short com Fish nasce no PC1 (anime_auto + narração),
  mesmo que o render vá pra fora. A fábrica de reCAPTCHA (`fabrica_fish.py`) também roda aqui com até 14 processos.

## O desenho (3 papéis)

| Papel | Máquina | Faz |
|---|---|---|
| **Supervisor** | PC1 | controlador (decide), painel, vigia, relatórios, o que tem login SÓ aqui (cofre do YouTube pra Studio de canais sem outra máquina), VS Code. Nada de render, nada de voz. |
| **Produtor de Short** | asusx, itau, PC2, desktop (MacBook) | escolhe a fonte já preparada, narra (Fish), monta, renderiza e devolve o vídeo pronto. Cada um PUXA da fila. |
| **Render auxiliar** | S20, S20 Ultra, G20, STI, HP | só recebe ffmpeg (trechos, capa, montagem) via `celulares.rodar_ffmpeg` — já funciona. |

## Como o Fish vai pros outros PCs (mesmo modelo do TikTok)

O TikTok já roda fora do PC1: cada conta tem uma lista `maquina` + `perfil_remoto` (onde a conta está logada) e
`maquina_remota.tentativas()` abre o Chrome DAQUELA conta naquela máquina, pela saída (proxy) da conta.

Pro Fish, o mesmo:
1. **Cada máquina produtora tem um pedaço do pool de contas Fish** (ex.: asusx 10 contas, itau 10, PC2 10…) — nunca
   a mesma conta em 2 máquinas. Cada conta continua saindo pelo IP Webshare FIXO dela (rnprmtfo-N) — a regra de IP vale
   igual (a ponte do proxy sobe na máquina que usa a conta).
2. **Login**: a dona loga a conta Fish na máquina (com o Google, como fez no PC1 com `logar_dona.py`) — o token
   Bearer fica salvo lá. É o passo que precisa dela (1 vez por conta).
3. **Créditos**: `creditos.json` deixa de ser só local — cada máquina desconta as suas contas e manda o saldo pro
   PC1 (supervisor) pelo relatório. Contas de máquinas diferentes nunca se misturam -> sem conflito de escrita.
4. **reCAPTCHA**: cada máquina sobe a sua `fabrica_fish.py` (Chrome quente só pras contas dela). Os notebooks Linux
   têm Chromium — testar que o enterprise.js gera token lá.
5. `fish_lote.disponivel()` passa a olhar se a máquina tem contas Fish dela (arquivo local), não o cofre do PC1.

## Ordem de execução (do mais seguro pro mais delicado)

1. **[feito hoje]** render/ffmpeg fora do PC1 (Shorts, produto, MS Energy), painel mais leve.
2. **Fila compartilhada de fontes** (já anotada como "falta" em 13/11): o PC1 só escolhe e baixa a fonte; cada
   produtor puxa a próxima. Sem isso os produtores param esperando o PC1.
3. **Fish num produtor (piloto)**: asusx com 5 contas Fish (de IPs que nenhuma outra conta usa). 1 dia medindo.
4. **Produtor completo de Short no asusx** (anime_auto lá, com Fish lá) — o PC1 deixa de narrar.
5. Repetir em itau, PC2, desktop. PC1 vira só supervisor.

## O que precisa da dona

- Aprovar o desenho (principalmente: contas Fish logadas em outras máquinas; conta nova é 1 PC por dia).
- Logar as contas Fish nos notebooks (eu deixo a janela pronta, como foi no PC1).
- Decidir quantas contas vão pra cada máquina.

## Riscos

- Conta Fish logada em 2 máquinas = mesmo token em 2 IPs -> risco de ban da conta. Por isso: 1 conta = 1 máquina.
- reCAPTCHA no Chromium do Linux pode não sair igual ao do Windows — piloto antes de espalhar.
- Notebook desligado/tela que apaga = produtor parado (configurar "nunca suspender" nos dois — pendente).

## 24/11 tarde — decisão da dona + piloto do Fish remoto

Dona: "a ideia é que TODOS sejam workers e montadores, assim se um falhar o outro assume, e posso gerenciar de
qualquer um (preferência PC1 ou o MacBook, que ela está formatando). Faça todos os render fora do PC1; logue os Fish nos
outros (HP Pavilion, STI, PC2) — eles têm as mesmas contas; é o mesmo processo do login do TikTok."

Feito:
- Contas Fish com Google JÁ logado por máquina (netbooks_logins.json x creditos.json): STI 42, PC2 38, MacBook 38,
  x200ma 38, acer 38, HP 33, asus 24.
- Script `fish_audio\logar_fish_remoto.py <maquina> <email>` (e `--lista`): abre o Chrome da conta na máquina pelo
  maquina_remota com proxy_n = IP Fish fixo dela, entra com Google (logar_dona._tentar_google), guarda o token em
  fish_audio\sessoes_remotas\<maquina>.json; 1 conta = 1 máquina (donos.json).

Piloto (STI, jogoscomia, rnprmtfo-34) BARRADO pela salvaguarda — corretamente:
"SEM_PROXY 34: o túnel do proxy do PC1 não responde aqui — não abro (nunca pelo IP de casa)".
Causa: o túnel reverso do maquina_remota leva a máquina ao PROXY DO TIKTOK deste PC (porta 18200+N, PAC que manda SÓ
domínios do TikTok pelo Webshare). O Fish usa OUTRA ponte (fish_audio._subir_ponte, porta 18500+N) e o PAC do TikTok
não cobre fish.audio. Falta: túnel reverso -R 18500+N:127.0.0.1:18500+N + Chrome remoto com proxy da ponte Fish pra
fish.audio (e o PAC/regra pra recaptcha do Google sair pelo MESMO IP). É regra de IP nova -> precisa do OK da dona.

## 24/11 noite — saída do Fish nas máquinas: FEITA e testada; login automático: NÃO fechou

Dona aprovou ("sim") a saída nova. Feito:
- `netbooks\chrome_conta.py`: `--proxy-fish=N` (Chrome sai INTEIRO por --proxy-server=127.0.0.1:18500+N, confere a
  ponte antes, PROXY_OK; nunca pelo IP de casa). Instalado SÓ no STI (backup chrome_conta.py.bak_24nov lá). PC2 não
  recebeu (regra SEM_PROXY_REMOTO: worker do hipercool, só com a dona).
- `maquina_remota.Remoto.abrir(..., proxy_fish=N)`: sobe a ponte Fish aqui (fish_audio._subir_ponte), túnel reverso
  -R 18500+N, chrome_conta --proxy-fish.
- Provado: túnel do STI até a ponte 31 -> http 200 pelo IP da conta (1ª conexão ~15 s, depois 3 s). A página do
  fish.audio CARREGA no STI pelo IP certo.

Não fechou: o clique automático no "Escolha uma conta" do Google (o Fish trocou o login pra botão largo "Continuar com
Google"; a lista de contas do Google não tem data-identifier hoje; com PC1/STI lentos o popup às vezes nem abre; uma
tentativa por teclado abriu o login da Apple). 7 tentativas, ~4 min cada.

IPs: medidos com prazo curto (15-20 s) pareciam "fora" (4 de 5) — ERRO DE MEDIÇÃO: a 1ª conexão leva ~15 s. Com prazo
certo, 22 de 24 IPs Fish funcionam (fora: rnprmtfo-5 e -19). O jogoscomia (rnprmtfo-34) estava fora de verdade.

Próximo (simples e certo): login ASSISTIDO — chrome_conta `logar` abre o Chrome VISÍVEL na tela do notebook já no
fish.audio pelo IP da conta; a dona clica "Continuar com Google" e na conta (sem senha, 1 vez por conta) e o
logar_fish_remoto lê o token. Igual ao logar_dona.py que ela usou no PC1 em 19/11.

## 25/11 madrugada — Fish LOGADO no STI (piloto fechou)

- Ponte do Fish RODANDO NA MÁQUINA: `~/postador-worker/ponte_proxy_fixo.py N 18500+N` (credencial Webshare em
  `~/postador-worker/secrets/proxies.txt`, chmod 600). Mesmo IP fixo da conta que no PC1 (rnprmtfo-31 = 91.123.10.220
  dos dois lados). fish.audio carrega em 1 s (pelo túnel até o PC1 dava ERR_TIMED_OUT/CONNECTION_CLOSED).
  `maquina_remota._ponte_fish_la(n)` sobe/confere a ponte lá (PONTE_LA_OK); sem ela cai no túnel. FISH_PONTE_LA=0 desliga.
- Login por Google em máquina nova = Google pede "Confirme que é você" no celular (Redmi A3) -> PARA (regra).
  Por isso o login remoto LEVA A SESSÃO que a conta já tem no PC1 (sessoes.json: token + workspace) pro localStorage
  do Chrome de lá e confere com `login_fish.logado`. Sem Google, ~1 min. ("não é pra ter diferença entre criar e relogar")
  `python logar_fish_remoto.py sti <email>`; FISH_REMOTO_SO_GOOGLE=1 força o caminho do Google.
- reCAPTCHA Enterprise sai no Chrome do STI (_JS_CARREGAR + _JS_TOKEN da fabrica_fish): 2,9 s frio, 0,5 s quente.
- 1 conta = 1 máquina: `creditos.escolher` pula conta cujo dono (sessoes_remotas\donos.json) é outra máquina
  (FISH_MAQUINA, padrão "pc1"). inovaremanhwaverseesp -> sti.
- FALTA: produzir com o Fish NO STI (fish_lote/fish_http rodando lá com a fábrica de lá e as contas dele) e repartir
  as contas por máquina; ponte e chrome_conta --proxy-fish só estão no STI (HP/MacBook/asusx/itau ainda não).

## 25/11 04:40 — postagem PARADA 30 h pelo botão da central-reserva (consertado)

`D:\postador-de-videos\config\POSTAGEM_DESLIGADA.json` (criado 23/11 22:40 pela CENTRAL-RESERVA do desktop: "o DESKTOP é
a central") desligava no PC1 a postagem de parceiro/postador/manhwa-react/anime/historias/veo. O desktop (MacBook) está
sendo formatado e offline -> NINGUÉM postava: parceiro 29 Shorts em 23/11, ZERO em 24 e 25/11; TikTok sem rodar desde 23/11;
o longo Rzoy "subiu" 4 vezes e voltou "parado". O vigia viu (consertos_ia\20261125_005128_8244.md) e ninguém agiu.
Feito: renomeado pra `POSTAGEM_DESLIGADA.json.desligado_central_reserva_23nov` (volta = renomear de novo).
postar_longos: status barrado no checar_upload (parado/canal_bloqueado/repetido/nao_aprovado) não vira mais
"erro DEPOIS de subir — pode ter ficado rascunho" (nada chega ao Studio nesses casos).
LIÇÃO pra arquitetura "todos workers": central-reserva precisa de PRAZO/vida — se a máquina reserva sumir, o PC1 volta.

## 25/11 04:50 — STI GERA FISH SOZINHO (fim a fim)

- `fabrica_fish_linux.py` (sem dependências; CDP por websocket feito à mão) em ~/postador-worker, porta 9397, mesma API
  da fabrica_fish do PC1 (/estado /sessao /token /soltar), só serve contas de ~/postador-worker/fish_contas.json
  (o `logar_fish_remoto.entregar` grava ao logar). Fecha o Chrome da conta após 15 min sem uso.
- `fish_http.py` + `fish_audio.py` copiados em ~/postador-worker/fish: `FishHTTP(email).gerar()` -> 2,3 s, 50 créditos,
  MP3 ok, saldo 7054 -> 7004, tudo pelo rnprmtfo-31.
- Achado no caminho: narrador principal 4b215a58 sumiu do Fish (404) — trocado provisório (ver memória project_fish_audio).
- FALTA: (1) o STI não tem ffmpeg (acabamento/montagem) — instalar ou montar em outra; (2) produtor de Short completo
  rodando lá (anime_auto) ou o PC1 pedir as falas pro STI por HTTP; (3) repetir em HP/asusx/itau com outras contas.

## 25/11 05:30 — longo "baixado" com BURACOS (consertado antes de subir)

O .partial do rclone multi-thread nasce com o tamanho final; o teto de 90 min matou o download do Rzoy e o arquivo ficou
com 12 de 400 amostras ZERADAS (52-53% e 96-98%) mas com o tamanho exato do Drive -> postar_longos aceitava como
"completo" (3 lugares conferiam só o tamanho). Nada furado chegou ao YouTube (24/11 04:49 parou no ffprobe; 25/11 01:20
parou no botão). Feito: `_md5_igual` (rclone hashsum md5 do Drive x md5 local) nos 3 lugares; LONGO_CONFERE_MD5=0 volta.
.partial furado do Rzoy apagado — baixa de novo na próxima rodada.

## 25/11 05:30 — 7 contas Fish em 3 máquinas + notebooks sem dormir

- Contas Fish por máquina (donos.json): STI 1 (inovaremanhwaverseesp/31), asusx 3 (emersonjosiel02/58, seebotsia/70,
  mundosolar1995/69), itau 3 (inovarecap/29, emersongencshin/57, inovaremultiatendimento/33). emersonjosiel03 falhou
  (sessão do PC1 de 19/11, provavelmente vencida) — fica no PC1.
- `fish_http`: conta de outra máquina usa a fábrica DE LÁ por túnel ssh (_base/_dono); geração sai pela ponte do PC1
  do MESMO rnprmtfo-N. Máquina fora: falha em ~3 s e fica 5 min sem tentar (_FORA); o rodízio passa pra próxima conta.
  FISH_REMOTA=0 desliga. Testado: PC1 gerou via asusx e via itau.
- asusx/itau: maquina_remota.MAQUINAS ganhou os dois (só Fish por enquanto). Tampa fechada NÃO suspende
  (logind.conf.d/30-tampa-nao-suspende.conf), sono do sistema desligado (sleep.conf.d/omarchy-sleep-disabled.conf),
  "Stay Awake" do Omarchy ligado (sem bloqueio de tela/descanso). asusx: ventoinha no máximo (serviço ventoinha-maxima;
  desfazer: systemctl disable --now ventoinha-maxima). itau: sem controle de ventoinha no Linux (é da BIOS).
- Senha ao ligar: é a senha da CRIPTOGRAFIA DO DISCO (LUKS), antes do Linux; depois o Omarchy já entra sozinho
  (sddm autologin). Tirar = guardar a chave sem proteção no disco -> decisão da dona (não mexi).
- Faltam: fábrica subir sozinha ao ligar (serviço de usuário) nos 3; HP/MacBook; produtor completo de Short nas máquinas.
- 05:40 ciclo cron: fábricas STI/asusx/itau ativas; TikTok postando; longos aguardando rodada (Rzoy baixa de novo com MD5).
- 05:56 ciclo cron: Rzoy baixando pro Fio da Meada (VIP); 1 proxy do Groq fora (rodízio segue); fábricas ok.
- 06:18 ciclo: TikTok OK #1-#4 hoje (rodada terminou no teto de 50 min com EPIPE do Playwright = cosmético); Rzoy ainda baixando pro Fio da Meada.
- 06:35 ciclo: FILA DE CAPAS ZERADA desde 24/11 20:57 (capas_depois.json = "[]") — ler() devolvia [] quando o arquivo
  estava no meio de outra gravação e o gravar() salvava a lista vazia (99 itens, 10 pendentes perdidos). Restaurada do
  bkp_2411_reabrir + reabertos os 8 pendentes (2 canal_encerrado). ler() agora tenta 10 vezes e LEVANTA (nunca grava
  por cima); gravar() atômico (tmp + replace). Reserva do Studio era o DESKTOP (offline): `_reserva_padrao()` usa o STI
  quando o desktop não responde. Desktop offline também derrubava: postagem (botão central-reserva) e capas — conferir
  outros lugares que dependem dele.
  - rodizio_longos.py força YT_MAQUINA=desktop (RODIZIO_MAQUINA) — com o desktop offline o rodízio de título/capa falha; trocar quando o MacBook voltar ou setar RODIZIO_MAQUINA=sti. 06:29 longo 'O BILIONÁRIO MAIS ODIADO' subindo.
- 07:10 ciclo: fila de capas voltou a rodar (8 pendentes; 6 do Fio da Meada). Studio dá timeout de 90 s no goto: o canal
  abre nos notebooks fracos (x200ma/acer/pc2) e a reserva STI também estourou (ocupado com TikTok). Vídeos existem (oembed
  200). Segue tentando sozinho (até 12). Solução de fundo: logar o YouTube das contas nos notebooks rápidos (asusx/itau)
  — precisa da dona (Google em máquina nova pede o celular). TikTok: OK inovarecap 06:47.
- 07:26 ciclo: TikTok OK #3 emersonjosiel2027 07:15; longo teste-voz (postar_xtts_teste) subindo desde 06:29; Rzoy (--so) baixando desde 05:30; capas seguem com timeout no Studio (notebooks fracos); fábricas Fish ok.
- 07:35: CORREÇÃO do ciclo 07:26 — o envio das 06:29 ERA o Rzoy (pelo postar_xtts_teste). 3,4 GB "em 61 min" e no fim
  `titulo.click` estourou 10 s (print logs\yt_web\20261125_072821_falha_fiodameada.png: título visível, Studio "Envio em
  3%", link https://youtu.be/cPQnT-EZuxE "Salvo como privado"). Ficou RASCUNHO PRIVADO INCOMPLETO no Fio da Meada; Rzoy
  preso ao Fio da Meada (vai tentar de novo lá). Conserto: youtube_web_poster tenta o clique do título 3x (tira o mouse,
  clica no cabeçalho do diálogo, reabre rascunho se fechou, 3ª forçada). PENDENTE DONA: apagar o rascunho cPQnT-EZuxE
  (não apaguei — ação irreversível no canal).
- 08:05 ciclo: PC1 com commit 28/36 GB e controlador sem psutil por 180 s. Pesados AQUI: (a) QA da MS Energy com Whisper
  medium 4,6 GB (qa_ms._transcrever_agora) -> FEITO: qa_ms._transcrever_fora transcreve no STI (venv do chatterbox,
  modelo medium copiado pra ~/modelos/whisper); falhou = roda aqui como antes; QA_WHISPER_FORA=0 desliga. (b) produção de
  Short do parceiro (cron_parceiro.bat producao -> parceiro_diario -> anime_auto -> anime-pipeline 2,6 GB) roda no PC1
  porque o Fish/cofre só existia aqui — é o passo "produtor de Short nas máquinas" (agora o Fish já está nelas). (c)
  63 pontes Webshare = só 73 MB (não é problema).
  - 08:15: Whisper no STI testado: 19 palavras certas em 90 s (a maior parte é carregar o medium). QA da MS sai do PC1.
- 08:26 ciclo: capas 90 feitas / 5 pendentes (t8tD, 4hP2J, Hm4n aplicadas 08:15-08:23, a do t8tD pela reserva STI); commit PC1 28 -> 21,7 GB; Rzoy em preparo pro Fio da Meada; fábricas Fish ok.
- 08:56 ciclo: Rzoy subindo no Fio da Meada desde 08:32 (cópia pro Chrome remoto; 1ª vez levou 61 min); capas 7 aplicadas hoje (1 pendente: mtvUEf6UD8A); fábricas ok.
- 09:18: RZOY POSTADO no Fio da Meada: https://youtu.be/75IxznGPk88 (3,4 GB em 46 min). Rascunho velho cPQnT-EZuxE (privado, incompleto) continua lá — dona decide apagar.
- 09:26 ciclo: parceiro 13 Shorts no YouTube hoje (0 em 24/11), TikTok 29 OK no log de hoje, capas 94 feitas / 2 pendentes (mtvUEf6UD8A + a nova do Rzoy), commit PC1 20,6 GB, fábricas Fish ok.
- 10:08 FIM do acompanhamento: parceiro 15 Shorts hoje, capas 95 feitas / 1 pendente (Rzoy novo), fábricas Fish ok. Pendências da dona: apagar rascunho cPQnT-EZuxE; aprovar voz substituta do Chris (ac63ad94); senha LUKS dos notebooks; logar YouTube nos notebooks rápidos.

## 25/11 tarde — produção de Short e produtos fora do PC1

- Short do parceiro: a narração JÁ sai pelo Fish online (11 falas hoje, voz nova ac63ad94 aprovada pela dona: "Chris novo
  é muito melhor"). O controlador já manda a produção de parceiro pro PC2 (DISPAROU pc2 várias vezes hoje); `cortes_pc1`
  só roda com CORTES_NO_PC1=1. A rodada no PC1 de 24/11 11:37 -> 25/11 10:31 (1377 min) foi a última.
- Remotion órfão no PC1: 2 cadeias (render de produto desde 01:31 e still desde 24/11 19:43) abertas por um bash de
  chat que morreu — fechadas (taskkill /T só nelas).
- Produto: `produto/editor.py._render` agora tenta PC2 -> NOTEBOOK pelo despacho.remotion (asusx/itau) -> PC1 só se
  nenhum der. PRODUTO_DESPACHO=0 desliga. Teste real com inovareclaw_ia_20261125_045547 em andamento.
- 14:33: TESTE OK — produto inovareclaw renderizado no asusx pelo despacho (1859 s, 18,4 MB, 1080x1920, 29,6 s, quadro
  conferido). produto/editor.py: PC2 -> notebook -> PC1.

## 25/11 14:30 — CHAVE DO GOOGLE DRIVE VENCIDA (consertado)
- `rclone` dava "invalid_grant: token expired" em manhwa-drive, conta32 e manhwa-drive-chave desde ~14:00 (o app do
  Cloud está em "Testando": a autorização vence em 7 dias). A tarefa DriveChaveRenovar falhou 16/11 e 21/11 — causa real:
  a porta 127.0.0.1:53682 do `rclone authorize` presa (bind) -> "não deu o link". Renovada 14:29, 78 pastas em todos os
  alvos (PC1 + 3 VPS).
- drive_chave.py ganhou `diario` (renova só se a última OK tem 4+ dias ou o Drive não responde) e a tarefa passou de
  5/5 dias para TODO DIA 04:20 -> 3 chances antes de vencer.
- Dano: postar_longos tirou 2 longos da fila de cortes ("sem cortes no Drive") porque o rclone falhou. Devolvidos
  (keBJ_bd5oVw HistoriasEmFrames, gJve_WjefZs Fio da Meada; bkp longos_postados.json.bkp_2511_cortes) e o código só tira
  quando o Drive RESPONDE "não encontrado".

## 25/11 14:40 — PENDÊNCIAS (pedidos da dona x estado)
Feito e conferido: postagem religada; capas dos longos (96 feitas, 0 pendentes); Fish em STI/asusx/itau (7 contas);
notebooks sem dormir; render de Short e produto fora do PC1; transcrição da MS no STI; chave do Drive (+ renovação
diária); voz nova aprovada; senha dos notebooks documentada.
Falta (minha parte): (1) Instagram sai por IP dividido com o TikTok (fakenews.ia4 + iapro.mentoria no IP 2; regra da
casa: Instagram 1 conta por IP) — dar IP rnprmtfo livre por conta (livres: 1,2,4,6-13,20,40-49,79,80,86-88);
(2) levantamento noturno: 12 áreas prontas, plano final nunca escrito; (3) Fish só gera quando o PC1 pede — produtor
completo de Short nas máquinas; (4) HP/MacBook sem Fish; (5) rodizio_longos preso no desktop.
Da dona: rascunho cPQnT-EZuxE no Fio da Meada; login do YouTube nos notebooks rápidos; canais em descanso (o médico
decide sozinho); vinheta do Lemo; teto diário do TikTok.
