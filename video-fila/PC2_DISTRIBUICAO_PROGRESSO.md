# PC2 apto + distribuição (dono 26/10/2026 ~05:30, foi dormir)

Pedido: "deixe o outro PC apto a rodar cortes, recap longo, hipercool atualizado, Veo com as contas que já conectei
(amanhã coloco mais) e todos os projetos conforme o sistema daqui precisar, pra balancear entre esse, ele e os 2
notebooks; esse aqui vive sobrecarregado; os 2 notebooks sempre rodando algo nas telas; o PC2 nas coisas mais pesadas
e também nas mesmas tarefas dos notebooks (postar, criar vídeos Veo, imagens etc.); este PC é a central que distribui."
Ordem de failback: NOTEBOOKS -> PC2 -> PC1 (último). + "faça tudo que tiver pendente e verifique os vídeos novos
conforme forem saindo e batem com o que queremos".

Regras: PC2 = mesmo IP da casa -> yt-dlp do PC2 NUNCA por conta própria (rajada 26/10 05:06-05:24 do autoloop do PC2
bloqueou o IP: pausa no PC1 05:17). Nada novo em C:\Users\Emerson-IA. Hipercool no PC2: dono pediu "atualizado".

## Frentes (marcar [x] com hora e o que foi conferido)
- [ ] A. Anime longo no PC2 pelo PC1 (ocioso.disparar_anime_longo); autoloop do PC2 DESLIGADO (fazia busca própria).
      Desmarcar do done do PC2 os que falharam sem baixar: msujs9l7Fpc, 0N12V4FLpj8 (já), EFXamkaZObI.
- [ ] B. Hipercool no PC2: venv aponta pro Python apagado (AppData) -> pyvenv.cfg home = C:\Python313; atualizar código.
      Também atlas (C:\Users\Emerson-IA\atlas\venv) e telão (C:\vitrine) usam o Python apagado.
- [ ] C. Cortes no PC2 (hoje recusado: "PC2 não tem voz clonada") — ver instalar_pc3.py e repetir pro PC2.
- [ ] D. Veo no PC2 com as contas já logadas lá (cadeia_veo / maquina_remota).
- [ ] E. Postagem (TikTok/Insta/YT) e imagens pelo PC2 também: ordem notebooks -> PC2 -> PC1.
- [ ] F. Conferir vídeos novos: dorama/filme 1ª pessoa sem "prota"; sem tarja quando não há legenda; narrador não
      lento (piso +5%); fim com folga; sincronia.
- [ ] G. TikTok paralelo (postar_tiktok_auto) — conferir rodada 14:05 (posts/rodada subiram?).
- [ ] H. Pendências antigas: anime_testes descarta tempos; chkdsk C: do PC2 (C:\_corrompido_recapd_apagar, pede
      reiniciar — perguntar ao dono).

## Andamento
- 18:15 [x] chkdsk no boot (dono reiniciou 18:07): C: NÃO está mais sujo; relatório Wininit 1001 = consertou vários
  registros (segmentos/atributos cruzados). C:\_corrompido_recapd_apagar APAGADA. 8771/8772 ok, venvs recap e
  hipercool importam, telão em execução, 29 GB livres. Job longo das 17:34 morreu no reinício (órfão no PC1 encerrado).
  Até 18:00: PC2 fez 3 Shorts sozinho (16:42, 17:12 trazidos) e logou TikTok em 5 contas.
- 16:05 [x] Controlador mandou Short pro PC2 sozinho (15:16, g1vpqeYMQYo, pronto 15:33; volta pro PC1 na rodada).
  [x] 1º login TikTok no PC2: inovaremultiatendimento (@plataforma.multia) 15:54. Hipercool fazendo línguas no PC2.
  Job longo das 13:24 (esperando o PC2 que reiniciou, timeout 4 h) encerrado — libera o próximo longo.
  PC3: passo assets cai no meio (ssh do PC3 "reset by peer"); InstalarPC3 segue tentando.
  "Atlas - vigia" está DESABILITADA no PC2 (alguém desligou; era Ready de manhã) — não religuei (projeto do dono).
- 14:50 Anime longo do jeito novo FUNCIONOU até o PC2: 14:14 "Whisper fica pro PC2", 14:18 fonte enviada (373 MB) —
  mas o dono reiniciou o PC2 ~14:40 e o job morreu (o próximo disparo do controlador refaz com outro vídeo).
  Pausa dos Shorts no PC2 (pc2_parceiro_falhou.json, 3 falhas dos meus testes) apagada às 14:05.
  Reinício 14:42: C: continuou sujo (autochk não rodou). Agendado de verdade: chkntfs /D + /C C: + "chkdsk C: /f"
  -> BootExecute = "autocheck autochk /p \??\C:" => roda no PRÓXIMO boot. Depois apagar C:\_corrompido_recapd_apagar.
  Pós-reinício: 8771 e 8772 respondem, telão rodando; atlas ainda não (conferir).
- 13:10 ACHADOS: (1) AnimeOcioso está DESLIGADA desde 20/10 — quem manda é o controlador.py (_cortes_pc2); ele tinha
  "PC2 não tem o clone" e NUNCA mandava Short pro PC2 -> trava tirada. (2) Anime longo nunca chegava ao PC2: o PC1
  fazia o Whisper do vídeo inteiro (estourava 47 min) e o payload usava `lang` inexistente (NameError, deitado e short
  worker) -> agora sem legenda do YT o PC2 faz Whisper+roteiro (_prepara_candidato sem_whisper; daemon já sabe), lang
  vai em cand["_lang"], target_lines no payload. (3) "Nenhum candidato deitado" com 819 na busca: top=125 cortava
  antes de tirar os 735 feitos -> filtra a lista toda. Job das 12:02 (Whisper no PC1 há 35 min) encerrado.
  CONFERIR na próxima rodada do controlador: anime longo no PC2 (Whisper lá) e Short no PC2.
- 13:05 PC3: tarefa automática andando (codigo, segredos, voz, vozes, modelos feitos; assets em curso).
- 13:05 E: logins TikTok no PC2: 4 tentativas, Chrome fechou ~1 min depois (dono usando o PC2? fechou as janelas) — o
  vigia repete. Teste de imagem no PC2 adiado (abriria Chrome na tela do dono).
- 10:20 chkdsk: dono está usando o PC2 — reinício CANCELADO. chkdsk /scan online falhou (sem cópias de sombra). Sobra
  de 19 KB em C:\_corrompido_recapd_apagar; C: segue marcado sujo = conserta no próximo reinício que o dono fizer.
  Disco BS3S20/120G status OK.
- 10:10 Dono autorizou apagar o corrompido: `fsutil dirty set C:` no PC2 (chkdsk no próximo boot); em 2º plano espera
  o PC2 sem Chrome/render, reserva a vez ("reinicio chkdsk") e reinicia. DEPOIS: apagar C:\_corrompido_recapd_apagar e
  conferir se hipercool 8771, daemon 8772, telão e atlas voltaram.
- 10:10 Imagens (Flow) no PC2: maquina_remota.FLOW_FORA_DAS_MAQUINAS = set() (era {"pc2"}) e gera_imagem considera o
  PC2 livre. TESTAR depois do reinício: gera_imagem.gerar_imagem(..., maquinas=["pc2"]).
- 10:05 F: filme 09:01 (forever-my-girl) 1ª pessoa ok; manhwa 09:26 com "o prota" = certo (regra só dorama/filme).
- 09:45 PC3: a instalação do Cortes NUNCA terminou (estado/instalar_pc3.json só tem "pastas" desde 24/10). O shell do
  ssh do PC3 alterna cmd/PowerShell e a conexão cai ("reset by peer"). instalar_pc3.mandar sem aspas aninhadas (vale
  nos 2 shells), passo_voz com a junção certa, passo_codigo leva _whisper_sub.py. A tarefa InstalarPC3 (--auto, 15 min)
  faz os passos que faltam quando o ssh deixar — conferir estado/instalar_pc3.json.
- 09:40 E: TikTok no PC2 ainda sem login: às 09:34 havia uma janela de LOGIN da conta inovaremanhwaverseesp aberta no
  PC2 (dono/outra rotina conectando conta?) — não mexi; o vigia loga as 5 quando o PC2 ficar livre.
- 09:20 [x] C FEITO: 1º Short inteiro no PC2 (under-the-grip-of-fear_cap1_20261026, 1m53, 23 frases voz clonada,
  1ª pessoa pela protagonista, sem "prota") trazido pro PC1 pelo ocioso. O ocioso já manda Short pro PC2 sempre que ele
  está livre; o kanban agora aceita Cortes no PC2.
- 08:50 C: 2º Short do PC2 (xjFSFa-rqI4) passou do SEM_YTDLP (cand.json + Whisper ok) e parou no RVC: "No module named
  'rvc.lib'" — BUG do instalar_pc3: junção ia em applio\rvc INTEIRO (é o código); o certo é só applio\rvc\models ->
  models\rvc. Corrigido no instalar_pc3.passo_voz (vale PC3 também) e reinstalado no PC2. Rerodando o mesmo id.
  PENDENTE PC3: rodar instalar_pc3.py voz + codigo quando o ssh voltar (mesmo bug + _whisper_sub.py).
  OBS dono: o rodízio mandou filme de terror (filme_sem_voz) pro Esporte Noturno — não mexi.
- 08:45 [x] G: rodada TikTok 06:41 com paralelo: 44 posts em 1h35 (~2,2 min/post; 25/10 manhã inteira = 22),
  sem post repetido (conferido por caminho), erros normais (4 deslogadas, 1 timeout).
- 08:45 F: filme 07:56 (ly4ra-0_x7M) em 1ª pessoa, sem bordão — v11 ok na produção real.
- 08:40 C: 1º Short no PC2 (JnxqtL2WwzM, Filme Noturno) FALHOU: o PC2 listava o canal e pedia legenda no YouTube
  (yt-dlp = IP da casa, "not a bot"/429) e faltava _whisper_sub.py (sync pula "_"). Consertado: PC1 manda fonte +
  legenda + cand.json (ocioso._extras_pc1, PC2 e PC3); anime_auto com SEM_YTDLP=1 + --id usa o cand.json; fetch_captions
  respeita SEM_YTDLP; pc2_parceiro.ps1 liga SEM_YTDLP=1; pc2_recapd leva _whisper_sub.py. 2º teste disparado.
  PENDENTE PC3: não tem sync automático de código — mandar _whisper_sub.py/anime_auto/anime_fetch quando o ssh voltar
  (instalar_pc3.py codigo também pula "_").
- 08:30 E: o Chrome que minha 1ª chamada cortada abriu no PC2 (05:44) ficou aberto e travava o PC2 pra TODO navegador
  (TikTok login, Veo, postagem) — fechado (chrome_conta fechar). Login TikTok das 5 contas fica pro vigia.
- 06:19 C: instalação dos Cortes no PC2 OK (pipeline importa, D: ok, ffmpeg, 26 vozes, venv_vozes torch 2.11,
  35,6 GB livres). transferencias.TAREFAS["cortes"] agora inclui pc2 (marca "anime_auto.py --modo short",
  disparo = ocioso._disparar_parceiro_pc2). 06:25 teste real disparado (D:\veo\venv python; o venv do recap não
  tem tzdata). CONFERIR: Short do PC2 chegou com voz clonada e passou na revisão.
- 06:20 H: anime_testes.alinhar_tempos (formato várias vozes herda os tempos do solo) — testado com exemplo.
- 05:55 [x] hipercool atualizado: pc2.sincronizar_bin() = "90 conferidos, 0 copiados" (fila.py é só do PC1, de
  propósito; worker_daemon.py só existe no PC2).
- 05:52 C: 1ª tentativa falhou (o ssh do PC2 cai no cmd; o "cmd /c" do instalar_pc3 com aspas aninhadas quebrava o
  tar) -> instalar_pc2_cortes.mandar próprio. Segredos ok; resto rodando.
- 05:50 A: anime_auto.fazer_deitado agora MANDA a fonte (já baixada no PC1) pro PC2 em
  C:/recapd-e-animes/workspace/anime/<id>/source.mp4 e o daemon pula o download. Caminho certo = ocioso.disparar_anime_longo.
- 05:50 D: Veo no PC2 JÁ FUNCIONA (cadeia: notebooks -> desktop -> pc2 -> pc1; 05:23 gerou recenas_ia em
  inovaremanhwaverserussian pelo PC2). 38 perfis cadastrados no PC2, só 5 com Google logado.
- 05:50 E: TikTok no PC2: as 5 contas com Google estão na fila do tiktok_notebooks (login automático "Continuar com
  Google"); notebooks já com todos logados. O vigia chama a cada 20 min; ele sai MUDO quando não tem máquina livre.
  Minha 1ª chamada (timeout 200 s) cortou no meio e deixou a vez do PC2 até ~05:57.
- 05:50 C: instalar_pc2_cortes.py (reusa instalar_pc3) rodando em 2º plano: codigo segredos voz vozes modelos assets
  venv testar (log logs\instalar_pc2_cortes.log). Junção C:\recapd-ambientes\producao -> C:\recapd-e-animes criada.
  Depois: tirar o "nao pc2" de transferencias.TAREFAS["cortes"] e conferir 1º Short do PC2 com voz.
- 06:00 [x] B feito: PC2 reiniciou 05:32 (sozinho) e o hipercool 8771 voltou pelo venv novo. Junção
  C:\Users\Emerson-IA\AppData\Local\Programs\Python\Python313 -> C:\Python313 (a pasta lá era sobra do instalador que
  falhou, 94 MB, apagada) => telão e atlas voltaram. AnimeDaemon (tarefa) DESLIGADA: o watchdog já abre o daemon e
  ficavam 2 na porta 8772.
- 06:00 F: filme 03:16 (Chiquinha) saiu 1ª pessoa mas com 4 bordões + invenção -> v11: dorama/filme sem bordão,
  abertura (trecho), tirada, interjeição do narrador; anime_tts não abre com o trecho. Testado com chiquinha: limpo.
  GTA-v/GTA-rp: tarja na legenda (tinham legenda), clone +5% base ok. "Sem legenda = sem tarja" ainda sem caso real.
- 05:45 B parcial: pyvenv.cfg do hipercool e do atlas -> C:\Python313 (backup .bak_20261026), testados ok. Telão:
  tarefa PC2_Telao roda o caminho antigo; schtasks /Change /TR TRAVA (pede senha) — NÃO usar. Plano: junção
  C:\Users\Emerson-IA\AppData\Local\Programs\Python\Python313 -> C:\Python313 (mklink /J disse "já existe"; conferir).
  Watchdog (C:\inovare-workers\watchdog.vbs) reabre recap e hipercool pelos venvs = ok. Hipercool venv sem torch/whisper.
  05:47 PC2 caiu da rede (Tailscale offline) — esperar voltar.
- 05:35 A: autoloop do PC2 desligado (rajada yt-dlp). Daemon 8772 no ar.
- 05:30 PC2 recap reinstalado (C:\Python313 NuGet, venv, tools, .pth PATH+subst D:), daemon 8772 ok (/health 0,25 s).
