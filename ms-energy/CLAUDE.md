# CLAUDE.md — MS Energy

Shorts de propaganda da **MS Energy**, empresa REAL de energia solar no Pará (Paragominas e região; Instagram
**@msenergycap**, link da bio = WhatsApp). Objetivo: pedidos de orçamento. Antes de mexer, ler
`docs\ANALISE_CAMPANHA.md` (análise de 22/10/2026, o que foi feito, testes e armadilhas).

## Ambiente
- Python da geração/trava/montagem: `D:\veo\venv\Scripts\python.exe`; do postador do Instagram:
  `D:\hipercool-videos\venv\Scripts\python.exe`. ffmpeg/ffprobe: `D:\hipercool-materiais\bin`. Sempre `PYTHONUTF8=1`.

## Fluxo (pipeline `ms_v2`, desde 22/10/2026)
1. **Geração** — `bin\gerar_short_veo.py` (via `bin\cron_gerar_ms_energy.bat 2`, disparado ~00:01 pelo controlador
   central `D:\video-fila\controlador.py`; ele tenta de novo até 3x/dia se não sair vídeo aprovado):
   - `bin\roteiro_ms.py` — pautas reais (dúvidas de quem quer instalar), regras de propaganda, revisor, histórico
     anti-repetição (`cache\historico_roteiros.json`), legendas prontas do Instagram/TikTok;
   - Veo 3.1 Fast pelo Flow (`D:\veo\beta\gera_auto.py`, contas em `D:\veo\beta\contas.py`): consultor(a) gerado(a)
     pelo Veo ou foto real de instalação como 1º quadro (`assets\fotos_instagram`, via `bin\baixar_fotos_insta.py`; + `google_fotos\` do Google Fotos
     das contas do dono via `bin\fotos_google_ms.py`, vídeos reais em `google_fotos\videos`);
   - `bin\qa_ms.py` — trava: começou/ficou na foto, faixa preta, juiz por visão (2 votos), Whisper confere a fala;
     reprovado: prova em `cache\veo_clips\reprovados`, no máx. 2 clipes por short;
   - `bin\montagem_ms.py` — 1080x1920, pergunta no topo, legenda sincronizada, cartão com logo/WhatsApp;
   - aprovado → `videos\shorts_veo` (+ `.json` com legendas); reprovado na trava final → `videos\_revisar`.
   **Formato `video_real`** (22/10, `bin\video_real_ms.py`, sem Veo): 2 trechos de vídeo REAL da empresa
   (`assets\videos_reais\clipes.json`, aprovados a olho) + narradora Thalita + trilha livre + a mesma montagem/trava.
   No `--tipo misto` é o 1º short dos dias pares; também cobre o dia quando o Veo fica sem conta.
2. **Postagem** — `D:\postador-de-videos\bin\postar_ms_energy.py`: Instagram Reel+Stories 10:17 e 19:37
   (`MSEnergy_PostarInsta` → `bin\cron_postar_insta.bat`, que renova o token antes), TikTok @energia.solar.da 12:10 e
   19:10 (`MSEnergy_PostarTikTok`). Vídeo novo (ms_v2) primeiro; antigo só de reserva e se a fala passar nas regras.
3. **Medição** — `bin\metricas_insta.py` toda segunda 09:07 (`MSEnergy_Metricas`) → `docs\METRICAS_INSTAGRAM.md`
   (Instagram pela API + TikTok Studio pelo navegador do cofre `msenergypara`; resumo no Telegram). Views de todas as
   contas do TikTok: `postador\bin\medir_tiktok.py` todo dia 07:23 (`TikTok_MedirViews`). As duas aparecem no painel
   :8790 → **Medições TikTok / Insta**, com botão "medir agora" que adianta a medição do dia.
4. **Cliente interessado** — `bin\vigia_clientes_insta.py` a cada 15 min (`MSEnergy_VigiaClientes`): Direct novo →
   resposta automática com o WhatsApp da bio (1x/pessoa/24 h; não responde se a empresa já respondeu); comentário novo
   → chamado no Direct + "Te mandamos uma mensagem no Direct 😉". Sempre avisa no Telegram na hora (com o resultado).
5. **Carrossel** — `bin\carrossel_ms.py` ter/qui/sáb 12:37 (`MSEnergy_Carrossel`): 6 imagens 1080x1350 (capa com foto
   real, 4 slides com ilustração Nano Banana 2.1 pelo Google Flow — `D:\flow-imagens` — com reserva Cloudflare, tudo
   conferido por visão, CTA), publicado pela API. Carrossel produzido antes com `--so-gerar` é o que a tarefa posta. Saída em
   `videos\carrosseis\<data>` (+ `meta.json`). Imagem de IA só ILUSTRA; nunca como "instalação da empresa".

## Regras
- Nunca prometer "zerar"/R$ 0, números/porcentagens/prazos, "garantir" resultado, nem citar concessionária
  (`roteiro_ms._PROIBIDO`). Texto sempre com acentuação correta.
- Nada dos efeitos de meme do Veo (`montar_final.py`, `agents.py`): o MS Energy tem módulos próprios.
- O dono do projeto não aparece (nem foto nem voz): a voz é a do próprio Veo.
- Foto com rosto de cliente não vira 1º quadro (não fazer cliente real "falar").
- Não religar o loop antigo `bin\run_loop_ms_energy.bat` (gastava crédito sem parar).
- Vídeo só vai pra fila aprovado pela trava; conferir quadros reais antes de dizer que está bom.
