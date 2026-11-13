# Acompanhamento de hora em hora — TODA produção e postagem de vídeo (dona, 02/11/2026)

Escopo: as 3 solares, todas as contas de Instagram e TikTok, Veo/Flow, Comédia Noturna, meta de reserva (7 dias),
**Cortes, cortes dos recaps longos e todos os vídeos que forem feitos** (dona 02/11: "na verdade todos os vídeos").
Gerente do Kaggle (GPU/contas/Shorts no Kaggle): `D:\hipercool-materiais\comum\kaggle_gerente\PROGRESSO.md`.
Registro de cada rodada: `D:\video-fila\ACOMPANHAMENTO_LOG.md` (hora, números, o que falhou, o que corrigiu).

Ler antes (memória C:\Users\Haylla\.claude-vscode\projects\d--\memory\): MEMORY.md, project_solares_criativos,
project_advance_solar, project_ms_energy, feedback_solares_tentar_ate_conseguir, feedback_legenda_cinetica_padrao,
project_catalogo_videos, project_tiktok_logins, project_instagram_senha, project_veo_limpo, project_flow_creditos_reais,
project_videos_comentarios, feedback_reserva_1_semana, feedback_fechar_o_que_abrir, feedback_kaggle_saida_fixa.

## REGRAS QUE NÃO SE QUEBRAM
- **NUNCA 2 contas pelo mesmo IP, nem em teste** (02/11: 14 contas Kaggle banidas por isso). Nada de laço sobre contas.
  Ler D:\hipercool-materiais\comum\kaggle_gerente\INCIDENTE_BANIMENTO_02NOV.md antes de tocar em qualquer conta.
- Nunca rajada: mínimo 90 min entre posts da mesma conta; Instagram/TikTok limitou (feedback_required, spam, checkpoint,
  suspended) = pausa, nunca insistir.
- Post de empresa solar nunca é pulado (tenta até sair, com intervalo).
- Tudo oculto (wscript D:\rodar_oculto.vbs ...), nada abre janela na tela da dona. Nada no disco C.
- Nunca matar pythonw no PC2. RAM < 1 GB (dona 03/11): postador-de-videos\bin\netbooks chrome_conta._liberar_ram + fechar Chrome de
  automação esquecido há mais de 2 h.
- Contar post de verdade, não linha parecida: TikTok = linhas "OK #N (conta)" em postador-de-videos\logs\tiktok_AAAAMMDD.log;
  Instagram = SOMA dos "RESUMO Instagram: postados N" do logs\instagram_AAAAMMDD.log (06/11: contar linhas
  "OK navegador|OK publicado|..." conta o MESMO post 2x — deu 148 quando o real era 66; o painel :8790 está certo);
  solares = "PUBLICADO:".
  ("postado" casa com o caminho "postador-de-videos" — já deu contagem errada.)
- Conserte a CAUSA, sem atalho destrutivo; nunca mexa em hipercool/histórias nem no PC2. PC2 com disco baixo: só avisar.
- Feche o que abrir (Chrome do cofre: Browser.close pelo CDP).
- Laço que fica no ar (ex.: parceiro_diario.py producao) roda o código de quando abriu: mudou o código → reiniciar o laço.

## 1) EMPRESAS SOLARES (clientes reais, Pará) — cada uma a cada 2 h, alternando reel e carrossel
- Advance @advance_novoestrela: reel 08/12/16/20h (AdvanceSolar_Reel), carrossel 10/14/18/22h (AdvanceSolar_Carrossel).
  O LUIZ é o RESPONSÁVEL pela Advance, NUNCA "dono" em vídeo/legenda/card.
- Globo @globosolarenergiag: reel 09:20/13:20/17:20/21:20, carrossel 11:20/15:20/19:20/23:20.
- MS @msenergycap: reel 08:40/12:40/16:40/20:40 (MSEnergy_PostarInsta -> postador-de-videos\bin\postar_ms_energy.py),
  carrossel 10:40/14:40/18:40 (falta 22:40 — perguntar à dona).
- Logs: D:\ms-energy\logs\reel_advance.log, reel_globo.log, carrossel_advance.log, carrossel_globo.log, carrossel.log (MS),
  D:\ms-energy\videos\cron_postar_insta.log (reel MS). Estoque: estoque_reels.py (Solares_Estoque) deixa reels e 1
  carrossel por empresa prontos; reels em ms-energy\videos\reels_advance, reels_globo, shorts_veo.
- Antes de reel NOVO sair: 4-5 quadros com D:\hipercool-materiais\bin\ffmpeg.exe e olhar: marca certa no cartão final
  (já saiu cartão da MS num reel da Advance), texto fora do rosto, rosto certo, sem preço/"zerar"/garantia, fala que
  combine com o cenário. Defeito = mover para ms-energy\videos\_revisar e avisar. Placar: ms-energy\bin\placar_estilos.py
  (estilo, layout, legenda, legenda_mix inteligente x livre); afunilar (docs\GLOBO.md).

## 2) INSTAGRAM — postador-de-videos\bin\postar_insta_auto.py, config\reuso_plataformas.json "instagram"
- ~33 contas; quem postou hoje e por que as outras não (pausa do Instagram, sem vídeo, máquina). Contas novas: tarefa
  InstagramCriarContas (bin\instagram_criar.py); em 01/11 falhou 4x no campo de usuário — print em
  logs\instagram_tela\*_erro_sem_campo_usuario.png: olhar e consertar.

## 3) TIKTOK — bin\postar_tiktok_auto.py (rodadas 06:40, 14:05, 19:35), reserva em bin\reserva_veo.py
- 01/11 só 12 de ~50 contas postaram: 22 contas "Veo de reserva" sem vídeo desde 25-26/10 (reserva acaba em 2-9 por
  rodada). Feito: reserva vai primeiro pra quem está há mais tempo sem postar; desktop voltou (1080p medido no caminho
  remoto). PENDENTE dona: liberar vídeos que já saíram no YouTube de canais sem TikTok próprio. "DESLOGADO" com todas as
  máquinas ocupadas costuma ser o PC1 (conta nunca logada nele). fabricadeautomacoesia: Gmail cheio, não recebe código.

## 4) VEO / FLOW — D:\veo\beta (gera_auto.py, cron_gerar_video_llm.py, cadeia_veo.py, flow_saldo_real.py)
- Gargalo: máquinas (x200ma, acer, pc2, desktop) ocupadas. Reel de cliente fura a reserva do Veo; "máquina ocupada"
  espera até 45 min sem gastar tentativa; pausa de "carga" gera só fora do PC1; "age-restricted" tira a máquina 6 h.
- DESKTOP fora do Veo: Flow pede verificação de idade (dona confirma).
- Rajada de capas de anime (D:\flow-imagens\gera_imagem.py, 8+ juntas) com referências recusadas nas MESMAS contas do
  Veo: risco de bloqueio — dona decide parar ou limitar a 1.
- Fila central/Chromes dinâmicos/Flow de imagens por HTTP: veo\docs\CREDITOS_E_FILA_CENTRAL.md + tarefa do Fable
  VEO_01_fila_central_e_creditos.md.

## 5) VÍDEOS FEITOS — acompanhar CADA um (quadros reais, não só log) e melhorar
- Legenda MIX é o padrão em TODOS; efeitos de som só nos estilos leves (criativo/historia/comparacao/chamada).
- Remotion: D:\claude-code-video (solares em gerar.py SOLAR_REGRAS + produto\kit.py SOLARES; ~3 h por vídeo).
- Processo travado (CPU parada e log parado vários minutos): taskkill /F /T e rodar a tarefa de novo.
- Cortes / parceiros (recapd parceiro_diario + anime_auto; log D:\hipercool-materiais\anime\_parceiro_AAAAMMDD.log e
  D:\recapd-ambientes\producao\logs\parceiro_producao.log) e cortes dos recaps longos (anime-pipeline "[cortes]",
  pasta cortes_longo): 1080p (ffprobe), legenda MIX, voz certa, sem texto cortado. Kaggle: "[kaggle-lote]"/"renderizado
  no KAGGLE"; erro no Kaggle volta pro PC sozinho.

## 6) META DE RESERVA (1 semana por canal; fora: hipercool, histórias; exceções: Veo e longos)
- `python D:\video-fila\reserva_status.py` (agendados + prontos ÷ consumo real 3 dias, piso 3/dia). Os mais vazios sobem?
- Onde trava: `python D:\video-fila\status_videos.py`, controlador_AAAAMMDD.log ("PC3:", "DISPAROU"),
  recapd logs\parceiro_producao.log, RAM/CPU, desktop (`ssh desktop`, poucas conexões).
- Ordem dos Cortes: parceiro_diario `_prioridade`; `config\parceiro.json` fila_alvo pt = 21. MS Energy RESERVA_DIAS.
- Resposta: X/21 canais na meta, 3 mais vazios, o que mudou, o que corrigiu. Todos >= 7 dias (ou 3 rodadas subindo
  sozinhos) = avisar a dona.

## 7) COMÉDIA NOTURNA (@comedianoturna, conta emersonjosiel02, projeto "comentarios")
- `D:\videos-comentarios\bin\producao.py` (ciclo/produzir/postar/status), `comentarios_video.py`. Tarefas
  ComentariosProducao (2/2 h), ComentariosPostagem (30/30 min). Log logs\producao.log. Status: `producao.py status`.
- Kaggle: fila `manhwa-drive:colab_recap/fila_comentarios/<id>` (pronto.json/erro.json); central da casa
  `D:\recap_central_casa\central.log`. Marca > 2 h é solta sozinha.
- 3 posts/dia ("cota do dia esgotada" = normal). Reuso: TikTok mundosolar1995 e Insta sintetizerisada.
- Alarmes: pedido parado > 3 h sem pronto; "FALHOU" repetido; reserva < 1 dia.
- Cada vídeo novo (D:\hipercool-materiais\videos-comentarios\<data>_<id>\ video.mp4 + postar.json), antes de postar:
  falas no postar.json; volume (ebur128 ~ -14 LUFS); 6 quadros (select+tile): lê o comentário literal, reação/bordão
  DELE, print certo na hora certa, MIX não cobre o print nem o cartão, figurinha só na reação, nome certo no cartão,
  nada cortado, 1080x1920. Anotar em D:\videos-comentarios\MELHORIAS.md. Defeito em 2+ vídeos = consertar a causa e
  testar (`producao.py produzir <id>` com COMENTARIOS_MODO=local). Defeito grave não postado: postar.json "postado":
  "segurado" + "revisao". 1x/dia: views dos postados → o que os melhores têm em comum.
- Antes de mexer em visual/narração: `python D:\video-fila\aprendizado.py aprovados` + PARA_IMPLEMENTAR.md.

## Pendente com a dona
Métrica de views no painel (semana/mês, média/dia, antes x depois, por conta, gráfico — D:\painel-clientes ou :8790);
Kaggle em lote com revolutionemerson2, emersonjosiel0, revolutionemerson3, emersonjosiel02 pelo Webshare (dona digita
as senhas); desktop/idade no Flow; capas (rajada); carrossel MS 22:40; liberar vídeos do YT pras contas TikTok de reserva.

## Resposta à dona (formato da dona 10/11)
Rode `python D:\video-fila\resumo_rodada.py` (grava a marca da rodada; desde a ÚLTIMA rodada) e responda NESTA ordem:
1. **Pendente** (PENDENTES_DONA.md — apague a linha quando resolver, acrescente o que surgir pra dona decidir);
2. **Postados desde a última rodada** (TikTok, Instagram, solares, YouTube) e **feitos** (Cortes, Comédia, Veo, reels, longos);
3. **Balanço**: reserva (X/21, 3 mais vazios), Kaggle (curto/longo ativos, treino), contas IG ativas/pausadas/novas,
   **melhorador** (última volta/aplicação, PARADO?) e **pesquisas recebidas** (quantas, pendentes por linha, implantadas);
4. o que falhou e o que corrigiu nesta rodada. Curto, em português.
5. (dona 10/11) A CADA rodada também: **máquinas** (todos os PCs/celulares/Kaggle 100% usados? livre/parado = dar
   trabalho ou anotar), **erros do painel** (/api/problemas) e **avisos do Telegram** desde a última rodada — os que
   têm conserto em código, consertar; **pedidos ainda não executados**; **pendências só da dona**; relatório de
   melhorias (melhorador, pesquisador: achado/implantado, aprendizado, rede de aprendizado, engenharia reversa —
   implantação andando?); canais/projetos parados (por que não postam); qualidade das contas (foto, bio, nome —
   contas sem perfil postam com a mesma dedicação das solares). Tudo isso sai do `resumo_rodada.py`.
