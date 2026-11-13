# Caixa de entrada do pesquisador — linha LONGOS

O motor (MotorPesquisador) põe aqui TODO achado novo desta linha. O chat desta linha, ao abrir:
1. avalia cada bloco [ ] PENDENTE seguindo video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md;
2. troca [ ] PENDENTE por [x] AVALIADO <data> — X aplicados, Y reprovados, Z deixados;
3. cada reprovado: `python D:\hipercool-materiais\pesquisador_melhorias\motor_pesquisador.py reprovar dono/repo "motivo" <linha>` (vira aprendizado do motor).
Item com [USA em ...] já existe no nosso código: só olhe se trouxer versão/ideia nova.

## [x] AVALIADO 05/11 — 0 aplicados, 9 reprovados, 6 deixados — 2026-11-04 09:54 — Narração mais humana

> Retorno (chat dos LONGOS, 05/11): REPROVADOS (registrados no motor): rapido-tts, dia, Orpheus-TTS, bifonia, voice-tag-studio, prosodia, LEMAS-TTS, TrdHiggsV3, SynParaSpeech — motivos: só inglês/PT-PT/chinês, sem licença, ou não substituem o clone RVC dos narradores. DEIXADOS: Step-Audio-EditX (a dona pediu só uma AMOSTRA de risada de IA pra ouvir — ela prefere risada REAL; banco de risadas reais em andamento: colabalas_narradores.py na hermes-staging); DPDFNet, DeepFilterNet e resemble-enhance (TESTE de limpeza de voz pedido pela dona, antes da respiração — risco de comer o 'ar' que humaniza); f5-tts-pt-br (alternativa de clone pt-BR: testes de voz estão pausados pela dona); nova-bench (só serve se adotarmos tags de risada no TTS).
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_narracao_humana__sonnet_0937.md`
- [INÉDITO] github.com/stepfun-ai/Step-Audio-EditX — ★993, push 2026-04-09, Apache-2.0 — A powerful 3B-parameter, LLM-based Reinforcement Learning audio edit model excels at editing emotion, speaking style, and paralinguistics, a
- [INÉDITO] github.com/ira-rumik/nova-bench — ★4, push 2026-09-06, Apache-2.0 — NoVA: Non-Verbal Vocalization Alignment benchmark for tag-controlled laughter and sighs in TTS
- [INÉDITO] github.com/ceva-ip/DPDFNet — ★177, push 2026-10-20, Apache-2.0 — Clean up noisy speech in real time with DPDFNet - open-source streaming speech enhancement for research, audio apps, and edge devices. Inclu
- [INÉDITO] github.com/anurag12-webster/rapido-tts — ★15, push 2026-10-07, Apache-2.0 — Tiny, fast Brazilian Portuguese text-to-speech (21M params)
- [INÉDITO] github.com/nari-labs/dia — ★19408, push 2025-11-19, Apache-2.0 — A TTS model capable of generating ultra-realistic dialogue in one pass.
- [INÉDITO] github.com/canopyai/Orpheus-TTS — ★6392, push 2025-12-05, Apache-2.0 — Towards Human-Sounding Speech
- [INÉDITO] github.com/TigreGotico/bifonia — ★2, push 2026-11-02, Apache-2.0 — European-Portuguese heterophonic homograph disambiguation for TTS (rules + learned models, pure-Python)
- [INÉDITO] github.com/resemble-ai/resemble-enhance — ★2487, push 2024-12-03, MIT — AI powered speech denoising and enhancement
- [INÉDITO] github.com/Jarus77/voice-tag-studio — ★7, push 2026-08-10, MIT — Local annotation workbench for building emotion-tagged  STT or/and TTS datasets: diarize, overlap rescue, verbatim ASR, forced alignment, pl
- [INÉDITO (corrigido: era falso USA pela palavra 'prosódia')] github.com/jiangquewh/prosodia — ★7, push 2026-08-01, MIT — 情感/风格可控的表现力语音合成框架：LLM 文本规范化与韵律预测，含流式实时推理（纯 Python，离线优先）
- [INÉDITO] github.com/Rikorose/DeepFilterNet — ★4952, push 2024-10-17, NOASSERTION — Noise supression using deep filtering
- [INÉDITO] github.com/LEMAS-Project/LEMAS-TTS — ★104, push 2026-03-31, SEM LICENÇA — LEMAS‑TTS is a multilingual zero‑shot text‑to‑speech system, supporting 10 languages:  Chinese English Spanish Russian French German Italian
- [INÉDITO] github.com/Trindade7/TrdHiggsV3 — ★2, push 2026-07-16, MIT — Local TTS Voice Cloning for Non-English Languages — a Custom ComfyUI Node (with focus on European Portuguese / PT-PT & Angola)
- [INÉDITO] github.com/Cataldir/f5-tts-pt-br — ★1, push 2026-07-06, MIT — F5-TTS fine-tuned for Brazilian Portuguese (PT-BR) with voice cloning
- [INÉDITO] github.com/ShawnPi233/SynParaSpeech — ★72, push 2026-04-27, SEM LICENÇA — Official Repository of Paper: "SynParaSpeech: Automated Synthesis of Paralinguistic Datasets for Speech Generation and Understanding" (ICASS

## [x] AVALIADO 05/11 — 0 aplicados, 10 reprovados, 2 deixados — 2026-11-04 15:00 — Roteiro e storytelling

> Retorno (chat dos LONGOS, 05/11): o 'anti cara de IA' JÁ entrou em pt-BR por conta própria (04/11: anime_script._SEM_CLICHE no pedido do roteiro + continuidade das 3 últimas frases entre blocos, v17) — por isso sloptrim, humanizer-skill e antislop (em inglês) foram reprovados. REPROVADOS também: jarvis-write, LoreSpring, writers-room-story-engine (criam história original; o recap reconta o vídeo-fonte), content-skills, purffle-shorts, shortform-builder (Shorts/inglês), Awesome-Story-Generation (lista de papers). DEIXADOS: gepa e cap-evolve (otimização de prompt precisa de uma métrica de qualidade do roteiro que ainda não temos — a retenção dos longos ainda tem views demais poucas pra servir de nota).
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_roteiro__sonnet_1441.md`
- [INÉDITO] github.com/gepa-ai/gepa — ★7279, push 2026-11-04, MIT — Optimize prompts, code, and more with AI-powered Reflective Optimization
- [INÉDITO] github.com/ynnyh/jarvis-write — ★15, push 2026-10-30, Apache-2.0 — A controllable, revisable, consistency-first AI system for long-form novel writing — temporal story bible, foreshadowing scheduler, cascadin
- [INÉDITO] github.com/seyedehsanhadi/sloptrim — ★415, push 2026-10-22, Apache-2.0 — A local detector for AI-writing patterns. Scores every prose file your agent saves. Python standard library only, no network, no model.
- [INÉDITO] github.com/vyralcontent/content-skills — ★196, push 2026-06-22, MIT — A free Agent Skill for writing short-form hooks, scripts, and carousels for TikTok, Reels, and YouTube Shorts.
- [INÉDITO] github.com/Chamanrajragu/purffle-shorts — ★61, push 2026-11-02, MIT — Free open-source AI YouTube Shorts generator and faceless video maker in Python. Any LLM (GPT, Claude, Gemini, Ollama) writes scripts; text-
- [INÉDITO] github.com/skillberry-ai/cap-evolve — ★68, push 2026-11-04, Apache-2.0 — Optimize any AI agent’s skills, tools/MCP, and prompts against your own evals.
- [INÉDITO] github.com/Aboudjem/humanizer-skill — ★301, push 2026-09-06, MIT — Free, open-source AI writing humanizer and detector. 55 patterns, 5 voices, a 0-100 AI-tell score, and nothing leaves your machine.
- [INÉDITO] github.com/SalZaki/antislop — ★11, push 2026-06-27, MIT — Claude Code plugin with skills for removing AI-generated tells from writing. Humanize prose without losing your voice.
- [INÉDITO] github.com/yingpengma/Awesome-Story-Generation — ★672, push 2026-11-02, CC-BY-4.0 — This repository collects an extensive list of awesome papers about Story Generation / Storytelling, exclusively focusing on the era of Large
- [INÉDITO] github.com/jackterror/writers-room-story-engine — ★47, push 2026-07-07, MIT — A modular AI-ready story-development skill engine built on Pixar’s 22 Rules, Story Spine, Hero’s Journey, South Park causality, and characte
- [INÉDITO] github.com/dungnotnull/shortform-video-script-builder-agent-skill — ★5, push 2026-07-02, MIT — 📱 A data-driven short-form video script builder. Engineers hooks and retention curves for TikTok, Reels, and YouTube Shorts to maximize watc
- [INÉDITO] github.com/N1CK99925/LoreSpring — ★2, push 2026-10-09, MIT — Long-form story generation using collaborative AI agents. Maintains character consistency and plot coherence across chapters through vector 

## [x] AVALIADO 05/11 — 0 aplicados, 6 reprovados, 2 deixados — 2026-11-04 17:11 — Retenção e ganchos

> Retorno (chat dos LONGOS, 05/11): REPROVADOS: shortlint (os longos já têm QA no Kaggle — bin\qa_video.py com decodificação na GPU, 04/11), cut-video, mortemtrimmer, SilenceCutter (cortam silêncio de gravação humana; a narração é TTS e já existe a trava de duração que corta fim mudo — anime_segments._duracao_sa), keepwatching e hookline (Shorts). DEIXADOS: line/lighthouse e eruto-skills/analyze-video — servem pra escolher os MELHORES TRECHOS do longo pros cortes em pé e pra estudar a estrutura dos canais de recap que estouram; ficam pra quando a retenção dos longos tiver views suficientes pra comparar (hoje 2–22 views por longo, a maioria da própria dona). Achado real de retenção (Studio, 04/11): o problema é IMPRESSÃO (6–38 por longo), não abandono — feito: Short do corte liga ao longo pelo 'vídeo relacionado' (postar_longos.postar_cortes).
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_retencao__sonnet_1644.md`
- [INÉDITO] github.com/ghostfix-pm/shortlint — ★0, push 2026-08-17, MIT — Pre-publish quality gate for Shorts/Reels/TikTok - a Lighthouse-style linter for short-form video: duration, aspect, LUFS loudness, dead air
- [INÉDITO] github.com/line/lighthouse — ★272, push 2026-11-01, Apache-2.0 — [EMNLP2024 Demo], [ICASSP 2025], [ICASSP 2026] A user-friendly library for reproducible video moment retrieval and highlight detection. It a
- [INÉDITO] github.com/louisedesadeleer/cut-video — ★119, push 2026-07-09, MIT — Claude Code skill: tighten long recordings — remove silences, ums, dead air. Preserves laughs and comedic pauses. Fast on Apple Silicon.
- [INÉDITO] github.com/msertdev/keepwatching — ★2, push 2026-09-05, MIT — A retention database for short-form video formats. That renders. Named 9:16 formats with committed previews, measured retention and visible 
- [INÉDITO] github.com/eruto-skills/analyze-video — ★1, push 2026-10-04, MIT — Claude Code skill: Analyze a YouTube reference video's structure and rhetorical techniques (hooks, pacing, hedging, credibility, retention, 
- [INÉDITO] github.com/Thebentist/hookline — ★0, push 2026-09-23, MIT — Self-hosted short-form video research agent: niche agents, outlier detection, a calibrated relevance judge, hooks, reports, script briefs, R
- [INÉDITO] github.com/fadhiilahahmadzikri/mortemtrimmer — ★16, push 2026-06-11, MIT — AI-Powered Auto Silence Trimmer & Noise Reduction | DeepFilterNet3 + Silero VAD + Whisper | Remove silence, kill background noise from video
- [INÉDITO] github.com/Magerko/SilenceCutter — ★14, push 2026-07-20, MIT — Desktop app that automatically cuts silence out of videos. Trims dead air at the start and end, removes long pauses between words, and batch

## [x] AVALIADO 05/11 — 0 aplicados, 9 reprovados, 1 deixado — 2026-11-04 17:36 — Longos e compilados

> Retorno (chat dos LONGOS, 05/11): REPROVADOS: RapidVideoChapterGenerator, ABChapterize, podcast-chapter-tools, ffmpeg-metadata-chapter-generator (os longos já têm capítulos pelo SENTIDO do roteiro, na descrição — anime-pipeline._capitulos), stanza, LoopClip, claude-youtube-editor, apollo-agents, Music-Mashup (fora do recap). DEIXADO: linzzzzzz/openclip (extração de melhores momentos de vídeo longo — candidato pro melhores_cortes.py dos Shorts tirados do longo; fica pra depois do gargalo de postagem).
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_longos__sonnet_1716.md`
- [INÉDITO] github.com/dev-ansung/RapidVideoChapterGenerator — ★None, push ?, ver repo (fallback HTML) — Generate video chapters and thumbnail galleries for 4K movies in under 5 seconds using keyframe perceptual hashing — zero full-frame decodin
- [INÉDITO] github.com/Parkerlimps/stanza — ★None, push ?, ver repo (fallback HTML) — 给「看长视频总在拖进度条」的人用的本地播放器 · 自动切章节、配缩略图、用本地大模型起标题. Contribute to Parkerlimps/stanza development by creating an account on GitHub.
- [INÉDITO] github.com/linzzzzzz/openclip — ★None, push ?, ver repo (fallback HTML) — OpenClip - AI-powered highlight extraction for long videos (AI 驱动的长视频精彩时刻提取工具)
- [INÉDITO] github.com/quinnuk/LoopClip — ★None, push ?, ver repo (fallback HTML) — Windows app that downloads YouTube videos and auto-trims/re-encodes them into seamless looping 4K HEVC screensaver clips, with NVENC GPU acc
- [INÉDITO] github.com/hassancs91/claude-youtube-editor — ★None, push ?, ver repo (fallback HTML) — Record the talking head, Claude Code does the rest: the cut, the visuals, the voice, the sound effects, the thumbnail, and the YouTube uploa
- [INÉDITO] github.com/pabloformoso/apollo-agents — ★None, push ?, ver repo (fallback HTML) — Automated DJ mix generator — BPM-matched crossfades + 1080p video with spectral waveform visualizations and AI-generated artwork. Built for 
- [INÉDITO] github.com/Inguiotar/ABChapterize — ★None, push ?, ver repo (fallback HTML) — Correct chapter marks for your audiobooks - by actually listening to them. Whisper-based chapter detection for m4b/mp3/opus/mka.
- [INÉDITO] github.com/lofihippo/Music-Mashup — ★None, push ?, ver repo (fallback HTML) — Splice a series of songs into one mix. Web + CLI tool that auto-detects each track&#39;s loudest crescendo (&quot;Best Parts&quot;), applies
- [INÉDITO] github.com/hbmartin/podcast-chapter-tools — ★None, push ?, ver repo (fallback HTML) — Extract and transform podcast chapter information between PodCastIndex chapters, Podlove simple chapters, and description embeds.
- [INÉDITO] github.com/ravexina/ffmpeg-metadata-chapter-generator — ★None, push ?, ver repo (fallback HTML) — A Python script that generates an FFmpeg metadata file to add chapters to Video (MP4/Webm/...) files.

## [x] AVALIADO 05/11 — 0 implantados, 10 reprovados, 3 deixados — 2026-11-04 18:50 — Título, descrição, tags, SEO (`area_titulo_seo`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_titulo_seo__sonnet_1821.md`
- [INÉDITO] github.com/flack0x/trendspyg — ★None, push ?, ver repo (fallback HTML) — Free, maintained Python library + CLI for Google Trends: trending now, plus keyword interest over time, related queries &amp; interest by re
- [INÉDITO] github.com/cumabozkurt/advanced-free-keyword-research-tool — ★None, push ?, ver repo (fallback HTML) — Advanced Free Keyword Research Tool — bulk long-tail keyword ideas from 25 search engines&#39; autocomplete (Google, Bing, YouTube, Amazon, 
- [INÉDITO] github.com/sidharthnair7/truecopy — ★None, push ?, ver repo (fallback HTML) — Checks translated YouTube titles and descriptions against seven deterministic rules, then reads the metadata back from the YouTube Data API 
- [INÉDITO] github.com/ersum00/metaglot — ★None, push ?, ver repo (fallback HTML) — Multi-language SEO localization for video metadata. Translates titles and descriptions into 10+ languages via the YouTube Data API v3 — sear
- [INÉDITO] github.com/inmanjeffrey89-cell/keyword-ideas-cli — ★None, push ?, ver repo (fallback HTML) — Pull real keyword ideas from Google/YouTube/Amazon/Bing autocomplete, no API key.
- [INÉDITO] github.com/svx2027/yt-playlist-seo-pipeline — ★None, push ?, ver repo (fallback HTML) — Channel-agnostic YouTube playlist metadata pipeline: batch-updates titles, descriptions, tags, and chapter timestamps for an entire playlist
- [INÉDITO] github.com/0xelitesystem/youtube-title-ab-tester — ★None, push ?, ver repo (fallback HTML) — Compare 2 to 5 candidate video titles side by side. Length, word overlap, signal patterns, search-result preview.
- [INÉDITO] github.com/MelnixDev/codex-ymt — ★None, push ?, ver repo (fallback HTML) — Open-source Codex plugin and MCP server for translating YouTube video titles and descriptions, reviewing multilingual metadata, and safely p
- [INÉDITO] github.com/tamnd/tiktok-cli — ★None, push ?, ver repo (fallback HTML) — Read public TikTok videos, users, comments, hashtags, and trending feeds as structured records
- [INÉDITO] github.com/adewale/yaket — ★None, push ?, ver repo (fallback HTML) — TypeScript YAKE-compatible keyword extraction library for Node and Cloudflare Workers
- [INÉDITO] github.com/trendsapi-ai/tiktok-trends-api — ★None, push ?, ver repo (fallback HTML) — TikTok trends API: TikTok trending hashtags and hashtag volume over time as JSON. Spot rising TikTok hashtags from one REST endpoint, no scr
- [INÉDITO] github.com/Virlo-AI/Virlo-Agent-Plugin — ★None, push ?, ver repo (fallback HTML) — Give your AI agent a social media brain: TikTok, YouTube Shorts &amp; Instagram Reels trends, viral video analysis, creators, sounds &amp; h
- [INÉDITO] github.com/ymoslem/DesktopTranslator — ★None, push ?, ver repo (fallback HTML) — Local cross-platform machine translation GUI, based on CTranslate2
- Avaliação (chat LONGOS 05/11): SEO dos longos já é seo_generator (LLM + Thompson de estilo, palavras quentes do placar); regra da dona: nome da obra em lugar nenhum; ferramentas de tradução/API Data não se aplicam (sem Google Cloud)
  - DEIXADO flack0x/trendspyg: testar palavras em alta pro título dos longos (busca) — depois que a ponte Short->longo e a prioridade de canais (05/11) forem medidas
  - DEIXADO cumabozkurt/advanced-free-keyword-research-tool: idem: autocomplete do YouTube pras palavras do título; testar junto
  - DEIXADO inmanjeffrey89-cell/keyword-ideas-cli: idem: autocomplete sem chave; testar junto

## [x] AVALIADO 05/11 — 0 implantados, 4 reprovados, 0 deixados — 2026-11-04 22:25 — Localização e dublagem (`area_localizacao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_localizacao__sonnet_2201.md`
- [INÉDITO] github.com/Huanshere/VideoLingo — ★19075, push 2026-09-30, Apache-2.0 — Netflix-level subtitle cutting, translation, alignment, and even dubbing - one-click fully automated AI video subtitle team | Netflix级字幕切割、翻
- [INÉDITO] github.com/alexturkey/dubworld — ★56, push 2026-11-02, Apache-2.0 — Local-first AI video dubbing pipeline: transcription, translation, speech synthesis and timing alignment.
- [INÉDITO] github.com/bakrianoo/mazinger — ★472, push 2026-10-01, MIT — End-to-end video dubbing pipeline
- [INÉDITO] github.com/MasamiYui/translip — ★5, push 2026-07-29, Apache-2.0 — Speaker-aware multilingual video dubbing pipeline.
- Avaliação (chat LONGOS 05/11): longos só em pt; canais de outras línguas estão mortos/punidos (análise 05/11) — dublagem não entra agora

## [x] AVALIADO 05/11 — 0 implantados, 1 reprovados, 0 deixados — 2026-11-04 22:36 — Distribuição e algoritmos (`area_distribuicao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_distribuicao__sonnet_2231.md`
- [INÉDITO] github.com/inovector/mixpost — ★3905, push 2026-03-16, MIT — 📅 Schedule, 📢 publish, and ⚡ manage your social media content on your server. No subscriptions, no limits. (Buffer alternative)
- Avaliação (chat LONGOS 05/11): postagem já é própria (youtube_web_poster + agenda + rampa); agendador de redes não acrescenta

## [x] AVALIADO 05/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-04 22:44 — Engajamento e comunidade (`area_engajamento`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_engajamento__sonnet_2241.md`
- [INÉDITO] github.com/egbertbouman/youtube-comment-downloader — ★1274, push 2026-10-15, MIT — Simple script for downloading Youtube comments without using the Youtube API
- [INÉDITO] github.com/mattwright324/youtube-comment-suite — ★322, push 2026-08-30, MIT — Download YouTube comments from numerous videos, playlists, and channels for archiving, general search, and showing activity.
- Avaliação (chat LONGOS 05/11): comentários já lidos pelo Studio (youtube_studio_extras --ler-comentarios), sem API

## [x] AVALIADO 05/11 — 0 implantados, 10 reprovados, 0 deixados — 2026-11-04 23:03 — Controle de qualidade antes de postar (`area_qualidade_qc`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_qualidade_qc__sonnet_2251.md`
- [INÉDITO] github.com/DangTruong96/shorts-qc — ★0, push 2026-10-27, MIT — Quality gates for AI-generated short-form video — caption fit, TTS language leaks, dead air, loudness and panel edge checks, from a real dai
- [INÉDITO] github.com/ShakeJ/coolray-video-qc — ★0, push 2026-11-02, MIT — Local-first video and subtitle quality checks for Codex, Claude Code, and the command line. Python + FFmpeg. MIT.
- [USA em D:\recapd-ambientes\producao\bin\qa_video.py:35] github.com/kajisho5/qc-skill — ★None, push ?, ver repo (fallback HTML) — Agent skill that deterministically checks video, audio, subtitle, and delivery artifacts against typed rules.
- [INÉDITO] github.com/ArchivalBoat50/video-qc-gate — ★0, push 2026-09-03, MIT — LLM-as-judge quality gate for AI-generated video: cheap objective checks, then a rubric-graded model verdict routing each clip to approved/r
- [INÉDITO] github.com/jasveerai88/faceless-qc-lite — ★1, push 2026-10-31, MIT — Free pre-upload checker for AI / faceless videos: loudness, dead air, black frames, caption speed, resolution. Local only, MIT.
- [INÉDITO] github.com/slhck/ffmpeg-quality-metrics — ★561, push 2026-10-25, MIT — Calculate quality metrics with FFmpeg (SSIM, PSNR, VMAF, VIF)
- [INÉDITO] github.com/madebysaira/AIVideoQualityGate — ★0, push 2026-09-10, MIT — Offline ffprobe and ffmpeg checks for AI video renders before client delivery
- [INÉDITO] github.com/Jakubczak/render-qa — ★2, push 2026-08-25, MIT — Deterministic quality checks for automated graphics and video rendering: reproducible HTML-to-video rendering plus geometry, layer-presence 
- [INÉDITO] github.com/KlausHammer/Verifyarr — ★0, push 2026-10-07, SEM LICENÇA — Self-hosted subtitle sync + verification for Plex/Bazarr libraries. Syncs subtitles with alass, Whisper-checks they actually match the audio
- [INÉDITO] github.com/backblaze-b2-samples/nudenet-video-moderation — ★0, push 2026-11-01, MIT — Self-hosted NSFW video moderation pipeline: NudeNet (local ONNX) classifies ffmpeg-sampled frames, flags unsafe content, and routes it to a 
- [INÉDITO] github.com/TusharTechs/audio-description-qa — ★0, push 2026-10-23, MIT — Quality checks for machine-written audio description. It catches silent stretches, dialogue collisions, camera language and invented charact
- Avaliação (chat LONGOS 05/11): QA já existe (bin/qa_video.py: loudness, silêncio, preto, resolução) + análise de nudez do vídeo pronto

## [x] AVALIADO 05/11 — 0 implantados, 8 reprovados, 0 deixados — 2026-11-04 23:13 — Coleta de métricas sem API Google Cloud (`area_metricas`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_metricas__sonnet_2306.md`
- [INÉDITO] github.com/duckdb/duckdb — ★42829, push 2026-11-04, MIT — DuckDB is a high-performance analytical database system
- [INÉDITO] github.com/pauling-ai/youtube-mcp-server — ★31, push 2026-10-23, MIT — Comprehensive MCP server for YouTube Data API v3, Analytics API, and Reporting API. 40 tools for channel analytics, video publishing, transc
- [INÉDITO] github.com/instaloader/instaloader — ★13783, push 2026-11-01, MIT — Download pictures (or videos) along with their captions and other metadata from Instagram.
- [INÉDITO] github.com/davidteather/TikTok-Api — ★6728, push 2026-08-24, MIT — The Unofficial TikTok API Wrapper In Python
- [INÉDITO] github.com/i1s-abhishek/youtube-studio-mcp — ★20, push 2026-04-20, MIT — Local MCP server for YouTube metadata, thumbnails, comments, and analytics.
- [INÉDITO] github.com/simonw/datasette — ★11543, push 2026-11-02, Apache-2.0 — An open source multi-tool for exploring and publishing data
- [INÉDITO] github.com/evidence-dev/evidence — ★7087, push 2026-11-04, MIT — Business intelligence as code: build fast, interactive data visualizations in SQL and markdown
- [INÉDITO] github.com/cadenburleson/social-dash — ★4, push 2026-03-19, MIT — Social media analytics dashboard for YouTube, TikTok, and Instagram
- Avaliação (chat LONGOS 05/11): métricas já vêm do Studio pelo navegador (metricas_rede.py -> _analise/metricas_studio.json) + analise_shorts_foco.py; sem API Google

## [x] AVALIADO 05/11 — 0 implantados, 5 reprovados, 0 deixados — 2026-11-04 23:20 — Melhorador que aprende (funil do que dá certo) (`area_melhorador_ia`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_melhorador_ia__sonnet_2316.md`
- [INÉDITO] github.com/algorithmicsuperintelligence/openevolve — ★None, push None, None — 
- [INÉDITO] github.com/SakanaAI/ShinkaEvolve — ★None, push ?, ver repo (fallback HTML) — ShinkaEvolve: Towards Open-Ended and Sample-Efficient Program Evolution 🧬
- [INÉDITO] github.com/shap/shap — ★None, push ?, ver repo (fallback HTML) — A game theoretic approach to explain the output of any machine learning model.
- [INÉDITO] github.com/optuna/optuna — ★None, push ?, ver repo (fallback HTML) — A hyperparameter optimization framework. Contribute to optuna/optuna development by creating an account on GitHub.
- [INÉDITO] github.com/st-tech/zr-obp — ★None, push ?, ver repo (fallback HTML) — Open Bandit Pipeline: a python library for bandit algorithms and off-policy evaluation
- Avaliação (chat LONGOS 05/11): motor de melhorias PARADO por ordem da dona (26/10); funil já usa Thompson (placar_titulos)

## [x] AVALIADO 05/11 — 0 implantados, 5 reprovados, 0 deixados — 2026-11-04 23:44 — Desempenho e GPU (`area_desempenho_gpu`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_desempenho_gpu__sonnet_2336.md`
- [INÉDITO] github.com/konecz/remotion-gpu — ★1, push 2026-10-31, MIT — A GPU rendering engine for Remotion: keep writing video in React, export on the NVIDIA GPU with the CPU free. Layered NVDEC/libplacebo/NVENC
- [INÉDITO] github.com/haasn/libplacebo — ★806, push 2026-11-05, LGPL-2.1 — Official mirror of libplacebo
- [INÉDITO] github.com/NVIDIA/Model-Optimizer — ★5524, push 2026-11-05, Apache-2.0 — A unified library of SOTA model optimization techniques like quantization, distillation, pruning, neural architecture search, speculative de
- [USA em D:\recapd-ambientes\producao\bin\marca_site.py:5] github.com/RapidAI/RapidOCR — ★8440, push 2026-11-04, Apache-2.0 — 📄 Awesome OCR multiple programing languages toolkits based on ONNX Runtime, OpenVINO, MNN, PaddlePaddle, TensorRT and PyTorch.
- [INÉDITO] github.com/Dominic485649/ffmpeg-qsv-lite — ★5, push 2026-11-03, MIT — A lightweight FFmpeg build focused on Intel QSV / oneVPL hardware HEVC and AV1 encoding.
- [INÉDITO] github.com/SpaceinvaderOne/transcoding-gpu-benchmark — ★34, push 2026-07-28, MIT — How many simultaneous 4K transcodes can your GPU sustain? Multi-vendor (Intel/AMD/NVIDIA/CPU) benchmark for Unraid with HDR tone-mapping, su
- Avaliação (chat LONGOS 05/11): render dos longos é no Kaggle (T4, NVENC pelo sitecustomize); Remotion/QSV/libplacebo não são o pipeline dos longos

## [x] AVALIADO 05/11 — 0 implantados, 10 reprovados, 0 deixados — 2026-11-05 00:00 — Orquestração e infraestrutura (`area_orquestracao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-04\respostas\area_orquestracao__sonnet_2346.md`
- [INÉDITO] github.com/Kaggle/kaggle-cli — ★None, push None, None — 
- [INÉDITO] github.com/coleifer/huey — ★6060, push 2026-11-01, MIT — a little task queue for python
- [INÉDITO] github.com/madebysaira/AIVideoBatchQueue — ★0, push 2026-09-06, MIT — Offline-first, crash-safe, resumable batch queue for AI video generation jobs. SQLite state machine, budget ceiling, provider-agnostic. 5th 
- [INÉDITO] github.com/The-Code-Labz/reelfactory — ★0, push 2026-10-06, MIT — Batch video generator daemon: TTS + images + ffmpeg subtitle burn, content-hash cached, single-binary CLI
- [INÉDITO] github.com/litements/litequeue — ★236, push 2026-07-31, MIT — Queue built on top of SQLite
- [INÉDITO] github.com/louislam/uptime-kuma — ★93269, push 2026-11-05, MIT — A fancy self-hosted monitoring tool
- [INÉDITO] github.com/dbos-inc/dbos-transact-py — ★1666, push 2026-11-04, MIT — Database-Backed Durable Python Workflows
- [INÉDITO] github.com/FrankS-IntelLab/agentic-kaggle-skill — ★191, push 2026-10-28, MIT — 🤖 AI Agent-driven Kaggle competition workflow. Battle-tested patterns for score stabilization, submission troubleshooting, kernel workflows,
- [INÉDITO] github.com/peter-wangxu/persist-queue — ★390, push 2026-01-08, BSD-3-Clause — A thread-safe disk based persistent queue in Python
- [INÉDITO] github.com/aryabagde/colab_resume — ★0, push 2026-08-03, MIT — python package that eliminates progress loss caused by GPU session disconnections in Google Colab and Kaggle by periodically checkpointing t
- Avaliação (chat LONGOS 05/11): fila própria pelo Drive + vps_central nas 4 centrais já é retomável; trocar de fila não ganha nada

## [x] AVALIADO 05/11 — 0 implantados, 4 reprovados, 0 deixados — 2026-11-05 00:24 — Direitos e políticas das plataformas (`area_direitos_politicas`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_direitos_politicas__sonnet_0001.md`
- [INÉDITO] github.com/contentauth/c2pa-rs — ★439, push 2026-11-05, NOASSERTION — Rust SDK for the core C2PA (Coalition for Content Provenance and Authenticity) specification
- [INÉDITO] github.com/contentauth/c2pa-python — ★109, push 2026-11-04, Apache-2.0 — Python binding for c2pa-rs library
- [INÉDITO] github.com/facebookresearch/audioseal — ★802, push 2026-11-03, MIT — Localized watermarking for AI-generated speech audios, with SOTA on robustness and very fast detector
- [INÉDITO] github.com/themankindproject/audiofp — ★12, push 2026-10-24, MIT — Audio fingerprinting SDK: Wang landmarks, Panako triplets, Haitsma–Kalker, streaming, file decoding, AudioSeal watermark detection.
- Avaliação (chat LONGOS 05/11): marca d'água/C2PA não reduz reivindicação nem strike; não é exigido para o nosso conteúdo

## [x] AVALIADO 05/11 — 0 implantados, 5 reprovados, 0 deixados — 2026-11-05 00:40 — Remotion (pacotes e técnicas novas) (`area_remotion`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_remotion__sonnet_0032.md`
- [INÉDITO] github.com/0xS4N4TG/kinetograph — ★None, push ?, ver repo (fallback HTML) — A blazingly fast programmatic video engine, made for agents.
- [INÉDITO] github.com/mromidev/claude-animated-shorts — ★1543, push 2026-11-01, MIT — Free Claude skill: viral animated story shorts (2D characters in a 3D world) with three.js + Remotion
- [INÉDITO] github.com/remotion-dev/template-tiktok — ★302, push 2026-11-02, SEM LICENÇA — Generate TikTok-style captions with Whisper.cpp
- [INÉDITO] github.com/remotion-dev/template-audiogram — ★275, push 2026-11-02, SEM LICENÇA — A template for making podcast video clips with Remotion.
- [INÉDITO] github.com/Vincentwei1021/video-shotcraft — ★None, push ?, ver repo (fallback HTML) — AI video skill for Claude Code &amp; Codex — cinematic, editable product promos with Remotion: 124 shot recipe cards, 150 motion previews, b
- Avaliação (chat LONGOS 05/11): Remotion é da linha Claude Code Video, não do pipeline dos longos (ffmpeg/Python)

## [x] AVALIADO 05/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-05 00:49 — FFmpeg (filtros e versões novas) (`area_ffmpeg`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_ffmpeg__sonnet_0041.md`
- [INÉDITO] github.com/AARomanov1985/CRT-TV-Emulator — ★29, push 2026-10-20, MIT — FFmpeg filter pipelines for batch simulating vintage CRT TV + VHS/DVD
- [INÉDITO] github.com/lucemia/typed-ffmpeg — ★1164, push 2026-11-05, MIT — Type-safe FFmpeg bindings for Python & TypeScript — filters, typing, and docs
- [INÉDITO] github.com/ayosec/ffmpeg-filters-docs — ★17, push 2026-08-30, Apache-2.0 — Improve the presentation of the FFmpeg filters documentation.
- Avaliação (chat LONGOS 05/11): efeitos/transições ficam como estão (dona 04/11: não mudar); bindings novos não acrescentam

## [x] AVALIADO 05/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-05 01:05 — Específico de anime/manhwa (`area_anime_manhwa`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_anime_manhwa__sonnet_0056.md`
- [INÉDITO] github.com/vikast908/ColorComic — ★21, push 2026-07-10, MIT — Colorize B&W manga/manhwa PDFs with deep learning — guided coloring gives each object its own color for a hand-colored look. Auto & referenc
- [INÉDITO] github.com/hummat/panelizer — ★6, push 2026-08-01, MIT — Panel-by-panel comic reader with automatic detection, human overrides, and cross-platform PWA viewer
- Avaliação (chat LONGOS 05/11): longos são recap de anime a partir de vídeo; colorir/painelizar manhwa não entra

## [x] AVALIADO 05/11 — 0 implantados, 2 reprovados, 1 deixados — 2026-11-05 01:29 — Concorrentes e tendências (`area_concorrentes_tendencias`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_concorrentes_tendencias__sonnet_0121.md`
- [INÉDITO] github.com/svx2027/yt-competitor-outlier-pipeline — ★0, push 2026-10-26, MIT — Single-competitor YouTube outlier analysis: yt-dlp channel-tab discovery, format-aware outlier detection, and a verification layer that inde
- [INÉDITO] github.com/RuochenLyu/google-trends-now — ★12, push 2026-07-16, MIT — Unofficial CLI and Node.js client for Google Trends Trending Now, with RSS fallback.
- [INÉDITO] github.com/ScrapeCreators/social-media-research-skills — ★5626, push 2026-08-26, MIT — AI agent skills for social media research. Outlier posts, comment mining, competitor teardowns, ad libraries & trends across TikTok, Instagr
- Avaliação (chat LONGOS 05/11): estudo dos concorrentes feito à mão (docs/VARIANTE_ANIME_RECAP.md); problema atual é impressão do canal, não tema
  - DEIXADO svx2027/yt-competitor-outlier-pipeline: pode achar os vídeos que estouram nos canais de referência (Mattz/NoteLey) — fazer quando a produção de longos voltar

## [x] AVALIADO 05/11 — 0 implantados, 4 reprovados, 0 deixados — 2026-11-05 01:47 — Concatenação de frases com silêncio-guia para inferência RVC em lote único (`area_rvc_batch_concat`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_rvc_batch_concat__sonnet_0141.md`
- [INÉDITO] github.com/AmnioticF72072/rvc-cpu-lite — ★0, push 2026-10-24, MIT — RVC inference on ONNX Runtime. CPU only, no PyTorch, no fairseq. Fixed-length generator export plus chunked inference.
- [INÉDITO] github.com/moyue23/rvc-web-runtime — ★1, push 2026-07-10, MIT — A 100% browser-based RVC inference engine for singing voice conversion, powered by ONNX Runtime (WASM).
- [INÉDITO] github.com/VoiceLala/rvc-cpp — ★0, push 2026-09-10, MIT — RVC.cpp — RVC-style voice conversion in C++ with ONNX Runtime. Offline and streaming inference, a C API, and no Python at runtime. By VoiceL
- [INÉDITO] github.com/Zundanen/Zundanen — ★2, push 2026-09-29, MIT — Local Finnish TTS and RVC voice generation app for Windows with batch generation, accent editing, and RVC v2 training.
- Avaliação (chat LONGOS 05/11): RVC roda no Kaggle e o gargalo do longo não é o RVC (medido 04/11: roteiro/montagem)

## [x] AVALIADO 05/11 — 0 implantados, 5 reprovados, 2 deixados — 2026-11-05 01:59 — Extratores de pitch F0 ultrarrápidos em FP16 e ONNX (FCPE, SwiftF0, RMVPE-TensorRT) (`area_pitch_extractors_fp16`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_pitch_extractors_fp16__sonnet_0151.md`
- [INÉDITO] github.com/lars76/swift-f0 — ★195, push 2026-09-25, MIT — Fast and accurate fundamental frequency (F0) detector using convolutional neural networks
- [INÉDITO] github.com/lars76/pitch-benchmark — ★85, push 2026-09-25, MIT — Comprehensive benchmark suite comparing pitch detection algorithms across multiple datasets.
- [INÉDITO] github.com/NewComer00/rmvpe-onnx — ★8, push 2026-04-11, NOASSERTION — Python package for RMVPE pitch estimator with pure ONNX Runtime inference
- [INÉDITO] github.com/CNChTu/FCPE — ★213, push 2025-10-14, MIT — 
- [INÉDITO] github.com/wbl-dev/rmvpe-onnx — ★0, push 2026-07-02, SEM LICENÇA — RMVPE F0 extraction without PyTorch — lightweight ONNX runtime, one-liner API.
- [INÉDITO] github.com/thewh1teagle/rmvpe-lite — ★1, push 2026-07-08, SEM LICENÇA — Re-usable package for pitch extraction
- [USA em D:\recapd-ambientes\producao\bin\climas_voz.py:8] github.com/yxlllc/RMVPE — ★84, push 2026-03-12, SEM LICENÇA — 
- [INÉDITO] github.com/Henley04/neural-resampler — ★1, push 2026-10-01, NOASSERTION — Rewritten HifiSampler in RUST. With improved FCPE F0 extract and ONNX deployment.
- Avaliação (chat LONGOS 05/11): RMVPE já em uso; ver deixados
  - DEIXADO lars76/swift-f0: F0 mais rápido que o RMVPE: testar no retreino de vozes (Kaggle), quando a dona liberar os testes de voz
  - DEIXADO CNChTu/FCPE: idem swift-f0 (torchfcpe): testar no retreino

## [x] AVALIADO 05/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-05 02:19 — Destilação das 73 vozes RVC v2 direto em embeddings/vozes nativas de Kokoro ou Qwen3-TTS (`area_destilacao_vozes_rvc_para_kokoro`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_destilacao_vozes_rvc_para_kokoro__sonnet_0211.md`
- [INÉDITO] github.com/RobViren/kvoicewalk — ★294, push 2026-04-06, Apache-2.0 — A random walk voice style cloning application for Kokoro text to speech
- [INÉDITO] github.com/Ashish-Patnaik/kokoclone — ★212, push 2026-04-19, Apache-2.0 — Voice Cloning, Now Inside Kokoro. Generate natural multilingual speech and clone any target voice with ease.
- Avaliação (chat LONGOS 05/11): testes de voz PAUSADOS pela dona; trocar o motor das 73 vozes é projeto grande sem pedido

## [x] AVALIADO 05/11 — 0 implantados, 1 reprovados, 0 deixados — 2026-11-05 02:34 — Extratores de pitch ultrarrápidos (FCPE, SwiftF0, RMVPE-ONNX) (`area_f0_extractors_fast`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_f0_extractors_fast__sonnet_0221.md`
- [INÉDITO] github.com/SonyCSLParis/pesto — ★305, push 2025-10-15, LGPL-3.0 — Self-supervised learning for real-time pitch estimation
- [USA em D:\recapd-ambientes\producao\bin\climas_voz.py:8] github.com/Dream-High/RMVPE — ★338, push 2024-01-25, Apache-2.0 — 
- [USA em D:\recapd-ambientes\producao\bin\climas_voz.py:8] github.com/xavriley/RMVPE — ★3, push 2025-11-18, Apache-2.0 — 
- Avaliação (chat LONGOS 05/11): RMVPE já em uso; ver deixados

## [x] AVALIADO 05/11 — 0 implantados, 9 reprovados, 0 deixados — 2026-11-05 02:59 — Cache fonético e de speaker embeddings pré-computados (`area_tts_kv_cache_frases`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_tts_kv_cache_frases__sonnet_0246.md`
- [INÉDITO] github.com/leisurely-potato/qwen3-tts-voice-clone-cache — ★0, push 2026-05-25, Apache-2.0 — Cached no-transcript voice cloning workflow for Qwen3-TTS 1.7B with reusable speaker prompts and GPU inference support.
- [INÉDITO] github.com/Holastor/Qwentts-SkyrimNet-Backend — ★4, push 2026-06-26, MIT — Local, high-performance TTS adapter server for SkyrimNet powered by qwentts.cpp (GGML). Supports instant voice cloning, dual-level caching, 
- [INÉDITO] github.com/omChauhanDev/pipecat-tts-cache — ★20, push 2026-07-21, BSD-2-Clause — Caching for any Pipecat TTS service: ~0.1 ms repeats, word timestamps kept. In Pipecat’s community integrations.
- [INÉDITO] github.com/PhyberApex/qwen3-tts-server — ★0, push 2026-11-04, MIT — OpenAI-compatible HTTP server for Qwen3-TTS: preset voices, voice design, voice cloning with a prompt cache, Prometheus metrics
- [CITADO em D:\video-fila\backup_pc2_recapd_20261026\requirements.txt:112] github.com/safetensors/safetensors — ★None, push None, None — 
- [INÉDITO] github.com/Cyan4973/xxHash — ★11408, push 2026-10-29, NOASSERTION — Extremely fast non-cryptographic hash algorithm
- [INÉDITO] github.com/joblib/joblib — ★4416, push 2026-11-02, BSD-3-Clause — Computing with Python functions.
- [INÉDITO] github.com/jnwatson/py-lmdb — ★755, push 2026-10-20, NOASSERTION — Universal Python binding for the LMDB 'Lightning' Database
- [INÉDITO] github.com/asg017/sqlite-vec — ★8237, push 2026-05-18, Apache-2.0 — A vector search SQLite extension that runs anywhere!
- [INÉDITO] github.com/facebookresearch/faiss — ★41256, push 2026-11-04, MIT — A library for efficient similarity search and clustering of dense vectors.
- Avaliação (chat LONGOS 05/11): voz é edge/Gemini (sem KV) + RVC; cache por frase não se repete entre longos

## [x] AVALIADO 05/11 — 0 implantados, 6 reprovados, 0 deixados — 2026-11-05 03:12 — Cache de embeddings de locutor e frases recorrentes (`area_tts_cache_semantico`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_tts_cache_semantico__sonnet_0301.md`
- [INÉDITO] github.com/jarohull-ai/Audioticon — ★0, push 2026-11-04, Apache-2.0 — Emoji-directed audiobook engine with sentence-level caching and DSP mastering (Rust)
- [INÉDITO] github.com/secondwindoss/diskcache-community — ★8, push 2026-11-04, Apache-2.0 — Disk and file backed persistent cache for Python, built on SQLite, with a Django backend. Community-maintained fork of python-diskcache.
- [INÉDITO] github.com/iamdgarcia/pipecat-echo-tts — ★0, push 2026-11-03, BSD-2-Clause — Your TTS bill, cached: a Pipecat TTS wrapper that caches phrase-level audio on live calls and replays it instantly on repetition. Open take 
- [INÉDITO] github.com/TigreGotico/tugaphone — ★5, push 2026-11-05, Apache-2.0 — TugaPhone is a Python library that phonemizes arbitrary Portuguese text across major Lusophone dialects (pt-PT, pt-BR, pt-AO, pt-MZ, pt-TL).
- [INÉDITO] github.com/SciQLop/Sciqlop-cache — ★6, push 2026-10-12, MIT — Fast, persistent, process-safe key-value cache for Python with a C++20 core
- [INÉDITO] github.com/avenet/elevenlabs-longform-reader — ★0, push 2026-09-16, MIT — Progressive long-form TTS reader with FastAPI, SQLite job state, and content-addressed ElevenLabs caching
- Avaliação (chat LONGOS 05/11): voz é edge/Gemini (sem KV) + RVC; cache por frase não se repete entre longos

## [x] AVALIADO 05/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-05 03:23 — Extratores de pitch ultrarrápidos para RVC v2 (torchfcpe e swift-f0) (`area_f0_pitch_fast_rvc`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_f0_pitch_fast_rvc__sonnet_0316.md`
- [INÉDITO] github.com/lars76/swift-f0-training — ★5, push 2026-09-25, MIT — Training code and ONNX export for the SwiftF0 pitch detector
- [INÉDITO] github.com/mairaksi/PiENet — ★51, push 2026-09-23, Apache-2.0 — Pitch estimation network (PiENet) for noise-robust neural F0 estimation of speech signals
- Avaliação (chat LONGOS 05/11): RMVPE já em uso; ver deixados

## [x] AVALIADO 05/11 — 0 implantados, 6 reprovados, 0 deixados — 2026-11-05 09:45 — Aceleração de TTS e RVC na iGPU Intel UHD 620 / Iris 640 via DirectML e Vulkan (`area_intel_uhd_directml_audio`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_intel_uhd_directml_audio__sonnet_0936.md`
- [INÉDITO] github.com/ayutaz/piper-plus — ★240, push 2026-11-05, MIT — Multilingual neural TTS (6 languages: JA/EN/ZH/ES/FR/PT, code supports SV) — C++, C#, Rust, Go, Python, npm (WASM). VITS + Prosody, streamin
- [INÉDITO] github.com/tterrasson/kokopop — ★11, push 2026-10-30, MIT — A standalone C++ library and toolkit for running neural text-to-speech models in GGUF format, with no Python dependencies.
- [INÉDITO] github.com/nyosegawa/speech.cpp — ★356, push 2026-11-01, MIT — Speech synthesis, speech recognition and voice activity detection for voice conversation, in C++ on ggml: Qwen3-TTS, Irodori-TTS, Qwen3-ASR,
- [INÉDITO] github.com/ServeurpersoCom/qwentts.cpp — ★207, push 2026-10-16, MIT — Local AI text-to-speech with voice cloning and voice design, powered by GGML. C++17 port of Qwen3-TTS (QwenLM/Qwen3-TTS). 10 languages, 24 k
- [INÉDITO] github.com/athrva98/polyinfer — ★11, push 2026-07-27, Apache-2.0 — Unified deployment pipeline
- [INÉDITO] github.com/ayutaz/vokra — ★13, push 2026-11-03, Apache-2.0 — Speech-first inference runtime in Rust — TTS / ASR / speech-to-speech / VC / speaker ID / VAD. An ONNX Runtime alternative that loads GGUF &
- Avaliação (chat LONGOS 05/11): TTS/RVC dos longos rodam no Kaggle (GPU T4), não no PC; iGPU Intel não entra

## [x] AVALIADO 05/11 — 0 implantados, 4 reprovados, 0 deixados — 2026-11-05 10:02 — Inferência de áudio e vídeo na Intel UHD 620 / Iris 640 via DirectML e OpenVINO (`area_onnx_directml_intel_uhd`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_onnx_directml_intel_uhd__sonnet_0946.md`
- [INÉDITO] github.com/openvinotoolkit/openvino.genai — ★614, push 2026-11-05, Apache-2.0 — Run Generative AI models with simple C++/Python API and using OpenVINO Runtime
- [INÉDITO] github.com/bdk38/kokoro-igpu — ★0, push 2026-08-08, MIT — Proof of concept for running Kokoro TTS on Intel iGPU hardware
- [INÉDITO] github.com/kaiyang223/whisper-openvino-arc — ★0, push 2026-09-24, MIT — 在 Intel Arc 独显上用 OpenVINO GenAI 跑 Whisper：55x 实时，内置 Silero VAD 抑制静音幻觉，输出合规的 SRT/VTT/LRC，附零依赖本地 Web 界面 | Run Whisper on Intel Arc GPUs via Op
- [INÉDITO] github.com/huggingface/optimum-intel — ★625, push 2026-11-05, Apache-2.0 — 🤗 Optimum Intel: Accelerate inference with Intel optimization tools
- Avaliação (chat LONGOS 05/11): TTS/RVC dos longos rodam no Kaggle (GPU T4), não no PC; iGPU Intel não entra

## [x] AVALIADO 05/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-05 10:23 — Destilação das 73 vozes RVC v2 em modelos TTS de passo único (`area_destilacao_rvc_para_tts`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_destilacao_rvc_para_tts__sonnet_1006.md`
- [INÉDITO] github.com/kyutai-labs/pocket-tts — ★10201, push 2026-11-05, MIT — A TTS that fits in your CPU (and pocket)
- [INÉDITO] github.com/MithrilMan/teacher-in-the-loop — ★11, push 2026-10-15, Apache-2.0 — Teacher in the Loop: reliable distillation of Kokoro-82M into 8M-parameter single-voice students (paper, training and inference code)
- Avaliação (chat LONGOS 05/11): testes de voz PAUSADOS pela dona; trocar o motor das 73 vozes é projeto grande sem pedido

## [x] AVALIADO 05/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-05 10:38 — Alinhamento de timestamps de palavras direto no TTS sem WhisperX (`area_alinhamento_forcado_tts`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_alinhamento_forcado_tts__sonnet_1026.md`
- [INÉDITO] github.com/remsky/Kokoro-FastAPI — ★5637, push 2026-11-04, Apache-2.0 — Dockerized OpenAI-compatible wrapper for Kokoro-82M text-to-speech w/multiplatform CPU, AMD, NVIDIA GPU PyTorch; multi-speaker, clone-tuning
- [INÉDITO] github.com/hexgrad/misaki — ★520, push 2025-08-11, Apache-2.0 — G2P
- [INÉDITO] github.com/Leochenlh001/tts-timestamp-estimator — ★0, push 2026-07-01, MIT — Estimate word or character timestamps for TTS subtitle highlighting from text and audio duration.
- Avaliação (chat LONGOS 05/11): legenda já sai do tempo das frases + Whisper na GPU (04/11); estimador não é melhor

## [x] AVALIADO 05/11 — 0 implantados, 4 reprovados, 0 deixados — 2026-11-05 10:52 — Pós-processamento de áudio e normalização LUFS em lote na GPU/CPU (`area_batch_mux_audio_ffmpeg`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_batch_mux_audio_ffmpeg__sonnet_1041.md`
- [USA em D:\recapd-ambientes\producao\bin\fx_music.py:123] github.com/sdroege/ebur128 — ★134, push 2026-10-27, MIT — Implementation of the EBU R128 loudness standard
- [INÉDITO] github.com/jiixyj/libebur128 — ★494, push 2023-06-25, MIT — A library implementing the EBU R128 loudness standard.
- [INÉDITO] github.com/vanjamodrinjak21/ebur128-stream — ★3, push 2026-09-22, Apache-2.0 — Streaming, zero-allocation EBU R128 / BS.1770-4 loudness measurement in pure Rust. M, S, I, true peak, LRA — chunk-deterministic, no_std cap
- [INÉDITO] github.com/CristianMoresi/DSPark — ★20, push 2026-11-03, MIT — Header-only C++20 audio DSP for real-time and offline processing. Filters, effects, analog circuit models, automatic dynamics, stereo tools,
- [INÉDITO] github.com/CristianMoresi/QuickMaster — ★6, push 2026-09-29, MIT — Intelligent offline audio mastering powered by DSPark. Whole-track analysis, interactive EQ, automatic dynamics, stereo generation, clipping
- Avaliação (chat LONGOS 05/11): loudnorm -14 LUFS já na junção das fatias (ANIME_MASTER_NA_JUNCAO, 04/11) e ebur128 no fx_music

## [x] AVALIADO 05/11 — 0 implantados, 1 reprovados, 0 deixados — 2026-11-05 11:07 — Cache de KV e embeddings de voz em TTS (`area_tts_prompt_cache`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_tts_prompt_cache__sonnet_1056.md`
- [INÉDITO] github.com/LMCache/LMCache — ★12285, push 2026-11-05, Apache-2.0 — LMCache: Supercharge Your LLM with the Fastest KV Cache Layer
- Avaliação (chat LONGOS 05/11): voz é edge/Gemini (sem KV) + RVC; cache por frase não se repete entre longos

## [x] AVALIADO 05/11 — 0 implantados, 6 reprovados, 0 deixados — 2026-11-05 11:22 — Aceleracao DirectML e OpenVINO para GPUs integradas Intel (`area_directml_intel_tts`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_directml_intel_tts__sonnet_1111.md`
- [INÉDITO] github.com/istupakov/onnx-asr — ★388, push 2026-11-04, MIT — A lightweight Python package for Automatic Speech Recognition using ONNX models
- [INÉDITO] github.com/ventura8/Whisper-Pro-ASR — ★14, push 2026-10-11, MIT — A high-performance Docker container that runs OpenAI's Whisper model. Optimized for CPU, Intel NPU, Intel Arc/iGPU, and NVIDIA CUDA GPUs.
- [INÉDITO] github.com/altunenes/parakeet-rs — ★421, push 2026-10-31, MIT — very fast speech-to-text, diarization, streaming (even in CPU) with NVIDIA Parakeet in Rust
- [INÉDITO] github.com/openvinotoolkit/openvino — ★11113, push 2026-11-05, Apache-2.0 — OpenVINO™ is an open source toolkit for optimizing and deploying AI inference
- [INÉDITO] github.com/openvinotoolkit/openvino_notebooks — ★3233, push 2026-11-05, Apache-2.0 — 📚 Jupyter notebook tutorials for OpenVINO™
- [INÉDITO] github.com/microsoft/ai-dev-gallery — ★1517, push 2026-10-17, MIT — An open-source project for Windows developers to learn how to add AI with local models and APIs to Windows apps.
- Avaliação (chat LONGOS 05/11): TTS/RVC dos longos rodam no Kaggle (GPU T4), não no PC; iGPU Intel não entra

## [x] AVALIADO 05/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-05 11:33 — Motores de alta vazao com continuous batching para audio (`area_vllm_sglang_audio`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_vllm_sglang_audio__sonnet_1126.md`
- [INÉDITO] github.com/andimarafioti/faster-qwen3-tts — ★1408, push 2026-10-09, MIT — Real-time text-to-speech with Qwen3-TTS
- [INÉDITO] github.com/malaiwah/qwen3-tts-server — ★9, push 2026-07-05, MIT — OpenAI-compatible HTTP server for Qwen3-TTS-CustomVoice — token-level PCM streaming, sentence chunking, emotion control, multilingual, CPU f
- [INÉDITO] github.com/wuxuedaifu/vllm-chatterbox-stream — ★8, push 2026-07-02, MIT — OpenAI-compatible multilingual TTS server — Chatterbox on vLLM with real-time PCM audio streaming, low time-to-first-byte (~0.7 s), voice cl
- Avaliação (chat LONGOS 05/11): voz do longo = edge/Gemini + RVC por frase; servidor de batching é escala que não temos

## [x] AVALIADO 05/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-05 11:52 — Conversao em lote e I/O binding de modelos RVC para TensorRT (`area_rvc_tensorrt_batch`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_rvc_tensorrt_batch__sonnet_1136.md`
- [INÉDITO] github.com/NVIDIA/TensorRT — ★13435, push 2026-10-09, Apache-2.0 — NVIDIA® TensorRT™ is an SDK for high-performance deep learning inference on NVIDIA GPUs. This repository contains the open source components
- [INÉDITO] github.com/NVIDIA/TensorRT-RTX — ★116, push 2026-10-15, Apache-2.0 — NVIDIA TensorRT-RTX is an SDK for high-performance AI inference on NVIDIA RTX GPUs. This repository contains Open-Source Software components
- [INÉDITO] github.com/MosRat/vocal-fast-rs — ★0, push 2026-10-11, MIT — Real-time Rust RVC voice conversion with CPU, DirectML, and TensorRT-RTX backends
- [USA em D:\recapd-ambientes\producao\bin\fx_clips.py:1651] github.com/microsoft/onnxruntime — ★22243, push 2026-11-05, MIT — ONNX Runtime: cross-platform, high performance ML inferencing and training accelerator
- Avaliação (chat LONGOS 05/11): RVC roda no Kaggle e o gargalo do longo não é o RVC (medido 04/11: roteiro/montagem)

## [x] AVALIADO 05/11 — 0 implantados, 1 reprovados, 0 deixados — 2026-11-05 12:06 — Injecao de emocao e alinhamento fonetico zero-shot (`area_expressividade_sincronia`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_expressividade_sincronia__sonnet_1156.md`
- [INÉDITO] github.com/wsssy/CoCoEmo — ★18, push 2026-07-01, MIT — CoCoEmo: Composable and Controllable Human-Like Emotional TTS via Activation Steering (ICML 2026). A training-free framework for mixed-emoti
- Avaliação (chat LONGOS 05/11): testes de voz PAUSADOS pela dona; emoção já vem do clima por cena (climas_voz.py)

## [x] AVALIADO 05/11 — 0 implantados, 5 reprovados, 0 deixados — 2026-11-05 12:18 — Conversão de voz zero-shot de 1 passo (mean flow, consistency) (`area_vc_mean_flow`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_vc_mean_flow__sonnet_1211.md`
- [INÉDITO] github.com/kiarina/meanvc2_onnx — ★0, push 2026-10-22, Apache-2.0 — Streaming MeanVC2 zero-shot voice conversion on ONNX Runtime for Flutter
- [INÉDITO] github.com/Jerrister/X-VC — ★86, push 2026-05-06, MIT — X-VC: Zero-shot Streaming Voice Conversion in Codec Space
- [INÉDITO] github.com/ShawnPi233/HQ-SVC — ★128, push 2026-06-17, SEM LICENÇA — Official Repository of Paper: "Towards High-Quality Zero-Shot Singing Voice Conversion in Low-Resource Scenarios"(AAAI 2026)
- [INÉDITO] github.com/LAION-AI/chatterbox-voice-conversion — ★7, push 2026-10-11, Apache-2.0 — High-level Python library for zero-shot voice conversion using Resemble AI's Chatterbox S3Gen model
- [INÉDITO] github.com/PlumBlossomMaid/Conan — ★0, push 2026-10-01, MIT — A chunkwise online network for zero-shot adaptive voice conversion with real-time streaming capability
- Avaliação (chat LONGOS 05/11): testes de voz PAUSADOS pela dona; RVC v2 em produção

## [x] AVALIADO 05/11 — 0 implantados, 4 reprovados, 0 deixados — 2026-11-05 12:49 — Roteiro anotado por LLM para narração (speaker/text/instruct) (`area_roteiro_anotado_voz`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_roteiro_anotado_voz__sonnet_1226.md`
- [INÉDITO] github.com/rubenwalther/dialogue-attribution — ★0, push 2026-11-01, MIT — Who says each quote in a novel, and how? LLM speaker & emotion attribution with validation, caching and evaluation.
- [INÉDITO] github.com/jazelly/castscript — ★0, push 2026-11-05, MIT — Plain-text multi-voice script format for audiobooks, rendered with local TTS engines
- [INÉDITO] github.com/Xerophayze/TTS-Story — ★351, push 2026-10-31, NOASSERTION — TTS-Story is a web-based multi‑voice TTS studio for turning tagged scripts into audiobooks—featuring full speaker management, chunk review/r
- [INÉDITO] github.com/dudarenok-maker/Castwright — ★27, push 2026-11-05, NOASSERTION — A local, multi-voice audiobook generator: an LLM casts every character in its own voice, kept consistent across a whole series — with voice 
- Avaliação (chat LONGOS 05/11): roteiro já marca clima/voz por cena (climas_voz + revezamento); formato novo não acrescenta


## [x] AVALIADO 05/11 — 0 implantados, 4 reprovados, 0 deixados — 2026-11-05 13:46 — RVC em ONNX Runtime CUDA no Linux do Kaggle (`area_rvc_onnx_kaggle_linux`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_rvc_onnx_kaggle_linux__sonnet_1336.md`
- [INÉDITO] github.com/Tps-F/rvc-onnx-test — ★5, push 2026-07-21, MIT — for onnx export test from rvc
- [INÉDITO] github.com/lona-cn/rvc_onnx_exporter — ★3, push 2026-03-29, NOASSERTION — web based RVC pth model转onnx工具
- [INÉDITO] github.com/PhamHuynhAnh16/contentvec_onnx_converter — ★2, push 2026-06-06, MIT — Một bộ chuyển đổi mô hình contentvec thành mô hình onnx giúp tăng tốc suy luận
- [INÉDITO] github.com/ImWuMie/vc-rs — ★0, push 2026-08-15, MIT — Real-time RVC voice changer in Rust: standalone GUI, CLI, and VST3 plugin running ONNX models on Windows ML or TensorRT
- Avaliação (chat LONGOS 05/11): RVC roda no Kaggle (T4) e o gargalo do longo não é o RVC (medido 04/11: roteiro/montagem); trocar o motor = risco sem ganho

## [x] AVALIADO 05/11 — 0 implantados, 6 reprovados, 0 deixados — 2026-11-05 13:59 — TTS de texto muito longo (1–4 h) (`area_longform_tts_blocos`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_longform_tts_blocos__sonnet_1351.md`
- [INÉDITO] github.com/romadinov/ebooker — ★0, push 2026-10-29, MIT — EPUB to Apple audiobook (M4B), locally. ASR-verified narration, explicit Russian stress, runs on Apple Silicon or NVIDIA.
- [INÉDITO] github.com/dqromney/tts-books — ★0, push 2026-08-13, Apache-2.0 — CPU-only text-to-speech audiobook generator built on Chatterbox Turbo TTS, with a tkinter desktop GUI, batch queue, resume support, garbled-
- [USA em D:\recapd-ambientes\producao\bin\anime_auto.py:511] github.com/pistelak/narrator — ★0, push 2026-09-30, MIT — Long-form TTS narration with per-chunk ASR verification: chunk, synthesize, verify, stitch, master
- [INÉDITO] github.com/xocialize/tts-orchestrator-kit — ★0, push 2026-07-24, MIT — Model-agnostic long-form TTS orchestration (chunk → synthesize → crossfade-assemble) for MLXEngine tts packages — VoxCPM2, Qwen3-TTS
- [INÉDITO] github.com/RobLe3/audiobook-harness — ★1, push 2026-08-03, Apache-2.0 — Local-first, evidence-based audiobook production harness for coding agents with Kokoro, dual ASR verification, and forced alignment.
- [INÉDITO] github.com/mukesh14149/pdf-to-audio — ★1, push 2026-08-23, MIT — Turn 500-1000+ page technical PDFs into audiobooks, entirely local: verbatim narration (no LLM rewriting), crash-resumable chunk pipeline, V
- [INÉDITO] github.com/Tanphong254/Vietnamese-Long-Audio-TTS — ★1, push 2026-10-15, MIT — A Vietnamese text-to-speech web app for long-form audiobooks, featuring Edge-TTS, resumable generation, audio chunking, and MP3 merging.
- Avaliação (chat LONGOS 05/11): TTS do longo já é por frase com conferência (narrator já USA em anime_auto) e continuidade entre blocos (04/11)

## [x] AVALIADO 05/11 — 0 implantados, 5 reprovados, 0 deixados — 2026-11-05 14:10 — Bancada de RTF na T4 (`area_tts_t4_bench`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_tts_t4_bench__sonnet_1401.md`
- [INÉDITO] github.com/YuvrajSinghBhadoria2/flash-attention-triton-cuda-benchmark — ★0, push 2026-09-27, MIT — Reproducible, roofline-grounded T4 benchmark of causal FP16 attention: Triton tl.attention vs per-row CUDA vs PyTorch fused SDPA (frozen v0.
- [INÉDITO] github.com/lyftium/vllm-serving-benchmark-t4 — ★0, push 2026-11-05, MIT — Measured vLLM serving study on 2×T4 (batching, AWQ, TP, prefix) — single-run Kaggle campaign; CSV + results.json
- [INÉDITO] github.com/dangkhoa2016/MOSS-TTS-v1.5-On-Kaggle-T4x2-GPU — ★0, push 2026-11-01, MIT — Reproducible deployment of OpenMOSS-Team/MOSS-TTS-v1.5 on Kaggle GPU T4 x2 using the original BF16 safetensors checkpoint—no GGUF, no quanti
- [INÉDITO] github.com/fishensw/VLLM-SM75 — ★38, push 2026-10-11, Apache-2.0 — 一个Turing专用vLLM分支，通过整合FlashInfer 0.6.18（PR #3526）与SM75后端门槛补丁（PR #47949），持续同步vLLM主线最新版本
- [INÉDITO] github.com/swdn133/nv-tensorrt-walkthrough-turing — ★2, push 2019-04-11, MIT — Walktrough for the setup of a Toolchain to use NVIDIA Turing GPUs to train a model that is optimized by TensorRT for inference on the Jetson
- Avaliação (chat LONGOS 05/11): bancada de terceiros na T4: não trocamos o motor de voz (testes de voz PAUSADOS pela dona)

## [x] AVALIADO 05/11 — 0 implantados, 8 reprovados, 0 deixados — 2026-11-05 14:28 — Conversão voz-a-voz zero-shot para trocar o RVC (`area_vc_zero_shot`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_vc_zero_shot__sonnet_1416.md`
- [INÉDITO] github.com/bshall/knn-vc — ★529, push 2026-01-16, NOASSERTION — Voice Conversion With Just Nearest Neighbors
- [INÉDITO] github.com/myshell-ai/OpenVoice — ★38140, push 2025-04-19, MIT — Instant voice cloning by MIT and MyShell. Audio foundation model.
- [INÉDITO] github.com/stremtec/astrape-vst — ★30, push 2026-07-03, MIT — Causal zero-shot voice conversion at 44.1kHz.
- [INÉDITO] github.com/caizexin/GenVC — ★60, push 2025-04-24, MIT — Self-supervised Generative LM-based Voice Conversion 
- [INÉDITO] github.com/Plachtaa/StreamVoiceAnon — ★102, push 2026-06-23, Apache-2.0 — [ICASSP'26] Real-time streaming voice anonymization & voice conversion
- [INÉDITO] github.com/yxlllc/DDSP-SVC — ★2711, push 2026-11-03, MIT — Real-time end-to-end singing voice conversion system based on DDSP (Differentiable Digital Signal Processing)
- [INÉDITO] github.com/freds0/free-svc — ★96, push 2025-07-23, MIT — [ICASSP 2025] FreeSVC: Towards Zero-shot Multilingual Singing Voice Conversion
- [INÉDITO] github.com/JeffC0628/awesome-voice-conversion — ★266, push 2026-10-11, Apache-2.0 — A curated list of awesome voice conversion, projects and communities.
- Avaliação (chat LONGOS 05/11): testes de voz PAUSADOS pela dona; RVC v2 com 73 vozes em produção

## [x] AVALIADO 05/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-05 14:44 — TTS pt-BR com licença comercial (`area_tts_ptbr`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_tts_ptbr__sonnet_1431.md`
- [INÉDITO] github.com/resemble-ai/Perth — ★541, push 2026-09-02, MIT — Open Audio Watermarking Tool
- [INÉDITO] github.com/devnen/Chatterbox-TTS-Server — ★1494, push 2026-05-26, MIT — Self-host the powerful Chatterbox TTS model. This server offers a user-friendly Web UI, flexible API endpoints (incl. OpenAI compatible), pr
- Avaliação (chat LONGOS 05/11): voz = edge/Gemini + RVC clonado (edge puro proibido; vozes aprovadas); TTS novo só com teste liberado

## [x] AVALIADO 05/11 — 0 implantados, 1 reprovados, 0 deixados — 2026-11-05 15:05 — Licença dos pesos e dos datasets de treino (`area_tts_licenca_pesos`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_tts_licenca_pesos__sonnet_1446.md`
- [INÉDITO] github.com/rishin-sharma/CorpusCustody — ★33, push 2026-09-04, MIT — Training-data license and provenance gate: resolve SPDX obligations, check compatibility against a declared purpose, and gate corpus ingesti
- Avaliação (chat LONGOS 05/11): não treinamos TTS próprio; vozes clonadas autorizadas pelos parceiros

## [x] AVALIADO 05/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-05 15:29 — TTS em CPU via GGUF/ggml/ONNX (`area_tts_cpu_gguf`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_tts_cpu_gguf__sonnet_1506.md`
- [INÉDITO] github.com/KittenML/kitten-tts-2-cpp — ★17, push 2026-10-30, MIT — Fast C++ inference for Kitten-TTS 2. Runs realtime on a CPU
- [INÉDITO] github.com/KittenML/KittenTTS — ★16805, push 2026-10-27, Apache-2.0 — Open-source State-of-the-art TTS model which runs on a CPU 😻 
- [INÉDITO] github.com/bailu-obj/gpt-sovits-onnx-rs — ★8, push 2026-10-04, MIT — A GPT-SoVITS Text-to-Speech (TTS) implementation in Rust, leveraging ONNX Runtime for near real-time performance on CPUs.
- Avaliação (chat LONGOS 05/11): voz do longo roda no Kaggle (GPU), não no PC

## [x] AVALIADO 05/11 — 0 implantados, 1 reprovados, 0 deixados — 2026-11-05 15:48 — Quantização int8 e fp16 de TTS (`area_tts_quantizacao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_tts_quantizacao__sonnet_1531.md`
- [INÉDITO] github.com/rahul1-bot/VOCODE-Efficient-Neural-Vocoders — ★1, push 2026-07-31, MIT — Twelve neural vocoders trained from scratch and measured under one protocol, with executed deployment interventions judged against same-hard
- Avaliação (chat LONGOS 05/11): voz do longo roda no Kaggle (GPU), sem gargalo de memória

## [x] AVALIADO 05/11 — 0 implantados, 1 reprovados, 0 deixados — 2026-11-05 16:01 — Controle de velocidade/tom/volume por instrução no próprio TTS (`area_tts_edicao_acustica`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_tts_edicao_acustica__sonnet_1556.md`
- [INÉDITO] github.com/music-and-arts/pocket-tts-enhanced — ★1, push 2026-07-24, MIT — Enhancements for Kyutai's Pocket TTS: inline tags for speed, pause and temperature control, plus scripts to automatically detect and re-gene
- Avaliação (chat LONGOS 05/11): velocidade/tom/clima já controlados (climas_voz.py, narracao_curva)

## [x] AVALIADO 05/11 — 0 implantados, 3 reprovados, 2 deixados — 2026-11-05 16:18 — Avaliação automática da voz gerada (`area_tts_avaliacao_auto`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_tts_avaliacao_auto__sonnet_1606.md`
- [INÉDITO] github.com/sarulab-speech/UTMOSv2 — ★377, push 2026-04-02, MIT — UTokyo-SaruLab MOS Prediction System
- [INÉDITO] github.com/wenet-e2e/wespeaker — ★1456, push 2026-09-22, Apache-2.0 — Research and Production Oriented Speaker Verification, Recognition and Diarization Toolkit
- [INÉDITO] github.com/inworld-ai/open-tts-eval — ★42, push 2026-09-09, MIT — Open, reproducible TTS/STT evaluation toolkit: WER/CER via Whisper ASR, NISQAv2, audio health, and prosody metrics with offline black-and-wh
- [INÉDITO] github.com/owenawsong/RareSpeech — ★0, push 2026-10-13, MIT — Rare-term TTS evaluation beside WER: anchored target retention, original audio evidence and reproducible comparisons.
- [INÉDITO] github.com/OpenBMB/UltraEval-Audio — ★328, push 2026-11-03, Apache-2.0 — Your faithful, impartial partner for audio evaluation — know yourself, know your rivals. 真实评测，知己知彼。A unified benchmark framework for ASR/TTS
- Avaliação (chat LONGOS 05/11): QA do longo já mede áudio (qa_video); nota automática de voz só com o retreino
  - DEIXADO sarulab-speech/UTMOSv2: nota automática de naturalidade: usar no retreino de vozes quando a dona liberar
  - DEIXADO wenet-e2e/wespeaker: comparar a voz clonada com o narrador real (banco de falas 05/11): junto com o retreino

## [x] AVALIADO 05/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-05 16:29 — Cache de frases e montagem de lotes (`area_tts_cache_lote`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_tts_cache_lote__sonnet_1621.md`
- [INÉDITO] github.com/dinosaurav/Rubedo — ★6, push 2026-09-14, MIT — Content-addressed caching and run history for Python batch pipelines — built for steps you can't afford to re-run
- [INÉDITO] github.com/oconnor663/blake3-py — ★207, push 2026-11-01, NOASSERTION — Python bindings for the BLAKE3 cryptographic hash function
- Avaliação (chat LONGOS 05/11): frases não se repetem entre longos; o RVC já roda em lote por narrador


## [x] AVALIADO 06/11 — 1 implantado (ideia), 3 reprovados, 0 deixados — 2026-11-05 18:30 — Sessão de visualização e vídeo sugerido (`area_dist_sessao_visualizacao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-05\respostas\area_dist_sessao_visualizacao__sonnet_1816.md`
- [INÉDITO] github.com/chongminggao/KuaiRand — ★176, push 2026-01-06, CC-BY-SA-4.0 — An Unbiased Sequential Recommendation Dataset with Randomly Exposed Videos
- [INÉDITO] github.com/chongminggao/KuaiRec — ★250, push 2026-01-06, CC-BY-SA-4.0 — KwaiRec: A Fully-observed Dataset for Recommender Systems.
- [INÉDITO] github.com/slimykat/longstoryshort-yt-audit — ★0, push 2026-05-18, Apache-2.0 — Tool for auditing YouTube recommendations on long-form and short-form videos.  This tool supported the paper: "Long Story Short: Auditing U.
- Avaliação (chat LONGOS 06/11): os 3 repos não servem (datasets do Kuaishou; robô no YouTube com 0 estrelas). IMPLANTADA a ideia da resposta (playlist + tela final apontando pro próximo): tela final '1 vídeo + 1 playlist' em todo LONGO apontando pra playlist 'Histórias COMPLETAS 🔥 (recap)' — postador-de-videosin\extras_ledger.py (LONGO_TELA_FINAL="" desliga); a playlist entra no envio (colab\postar_longos.py, LONGO_PLAYLIST="" desliga). Recurso padrão: vale também nos canais sem recursos avançados.


## [x] AVALIADO 06/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-06 09:57 — Ponte Short -> longo (link relacionado, fixado, cards) (`area_dist_ponte_short_longo`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_dist_ponte_short_longo__sonnet_0941.md`
- [INÉDITO] github.com/AgriciDaniel/claude-youtube — ★685, push 2026-04-10, MIT — Claude Code skill for YouTube creators — channel audits, video SEO, retention scripts, thumbnails, content strategy, Shorts optimization, an
- [INÉDITO] github.com/adityaarsharma/youtube-marketing-skills — ★None, push ?, ver repo (fallback HTML) — Open-source agent-agnostic YouTube growth toolkit — 21 AI commands + live channel MCP. Works with Claude Code, Cursor, Codex, Windsurf, Gemi
- [INÉDITO] github.com/mlvps/shortsmith — ★15, push 2026-05-06, MIT — Open-source pipeline for stitching viral shorts and auto-posting to YouTube. Generate 500 hook+CTA variations from one end-clip, stitch with
- Avaliação (chat LONGOS 06/11): ponte Short->longo já feita (postar_longos.ligar_pontes, liga só com o longo público); skills genéricas de YouTube/gerador de Shorts não acrescentam; o bloqueio real é o YouTube negar recursos avançados em 9 canais

## [x] AVALIADO 06/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-06 10:14 — Playlists e séries para longos (`area_dist_playlists_series`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_dist_playlists_series__sonnet_1001.md`
- [INÉDITO] github.com/guessit-io/guessit — ★948, push 2026-10-21, LGPL-3.0 — GuessIt is a python library that extracts as much information as possible from a video filename.
- [INÉDITO] github.com/erengy/anitomy — ★327, push 2026-07-27, MPL-2.0 — Anime video filename parser
- [INÉDITO] github.com/lijunzh/hunch — ★7, push 2026-11-05, MIT — Fast, offline media filename parser for Rust — extract title, year, season, episode, codec, and 40+ properties from messy filenames
- Avaliação (chat LONGOS 06/11): parsers de nome de arquivo (guessit LGPL, anitomy MPL): não precisamos — a playlist 'Histórias COMPLETAS' já entra no envio (LONGO_PLAYLIST)

## [x] AVALIADO 06/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-06 10:34 — Canal novo de longos: arranque com poucas impressões (`area_dist_canal_novo_longo`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_dist_canal_novo_longo__sonnet_1026.md`
- [USA em D:\recapd-ambientes\producao\bin\test_omniroute_all.py:32] github.com/AgriciDaniel/youtuber — ★76, push 2026-09-11, Apache-2.0 — A source-cited YouTube brain: creator growth & strategy, the developer API, and paid advertising. Unofficial; not affiliated with YouTube/Go
- [INÉDITO] github.com/sergebulaev/youtube-skills — ★90, push 2026-11-04, MIT — YouTube and YouTube Shorts marketing skills for Claude Code and Codex: high-CTR titles, SEO descriptions, retention hooks, thumbnails, and a
- [INÉDITO] github.com/AgriciDaniel/claude-repurpose — ★169, push 2026-04-10, MIT — Content Repurposing Engine for Claude Code. Turn 1 piece of content into 10+ platform-optimized posts for Twitter, LinkedIn, Instagram, Face
- Avaliação (chat LONGOS 06/11): skills de título/SEO de Claude: já temos seo_generator + Thompson; prioridade de canais por ranking real (06/11) resolve o arranque melhor que regra genérica

## [x] AVALIADO 06/11 — 0 implantados, 0 reprovados, 0 deixados — 2026-11-06 10:49 — Diagnóstico de impressões baixas (YouTube Analytics leitura) (`area_dist_impressoes_diagnostico`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_dist_impressoes_diagnostico__sonnet_1041.md`
- (todos os itens desta pesquisa foram reprovados)
> Retorno (chat dos LONGOS, 12/11): nada a avaliar — o filtro automático novo já tirou tudo. Lembrete: título dos longos é SEM o nome da obra (regra da dona), então 'nome da obra + episódio' não se aplica a nós.
- Avaliação (chat LONGOS 06/11): nada aproveitável; diagnóstico feito pelo Studio (metricas_rede.py + analise_shorts_foco.py)

## [x] AVALIADO 06/11 — 0 implantados, 0 reprovados, 0 deixados — 2026-11-06 11:02 — Tela final, playlist e sessão (`area_fim_playlist`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_fim_playlist__sonnet_1056.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 06/11): nada aproveitável; tela final '1 vídeo + 1 playlist' já implantada 06/11 (extras_ledger, LONGO_TELA_FINAL)

## [x] AVALIADO 06/11 — 0 implantados, 4 reprovados, 0 deixados — 2026-11-06 11:22 — Sessão de visualização e vídeo sugerido (`area_dist_sessao_visualizacao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_dist_sessao_visualizacao__sonnet_1106.md`
- [INÉDITO] github.com/meta-recsys/generative-recommenders — ★2022, push 2026-11-05, Apache-2.0 — Repository hosting code for "Actions Speak Louder than Words: Trillion-Parameter Sequential Transducers for Generative Recommendations" (htt
- [INÉDITO] github.com/Applied-Machine-Learning-Lab/KuaiSim — ★39, push 2024-09-10, Apache-2.0 — 
- [INÉDITO] github.com/google-research/recsim_ng — ★127, push 2022-04-26, Apache-2.0 ARQUIVADO — RecSim NG: Toward Principled Uncertainty Modeling for Recommender Ecosystems
- [INÉDITO] github.com/CHIANGEL/Awesome-LLM-for-RecSys — ★1568, push 2026-10-26, MIT — Survey: A collection of AWESOME papers and resources on the large language model (LLM) related recommender system topics.
- Avaliação (chat LONGOS 06/11): bibliotecas de recomendação acadêmicas (RecBole, KuaiSim, recsim, generative-recommenders): não temos dados de sessão; não serve

## [x] AVALIADO 06/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-06 11:39 — Distribuição e algoritmos (`area_distribuicao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_distribuicao__sonnet_1126.md`
- [INÉDITO] github.com/ralphcrisostomo/n8n-nodes-meta-publisher — ★23, push 2026-10-25, MIT — Publish to Instagram, Facebook Pages, and Threads (images, videos, reels, stories, carousels) via Meta Graph APIs.
- [INÉDITO] github.com/davidmosiah/tiktok-agent-publisher — ★3, push 2026-11-02, MIT — Agent-first TikTok Content Posting API CLI and MCP server with dry-run publishing
- Avaliação (chat LONGOS 06/11): postadores de Meta/TikTok por API oficial: a postagem é pelo navegador (regra Google/redes sem API); não serve aos longos do YouTube

## [x] AVALIADO 06/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-06 12:22 — Sessão de visualização e vídeo sugerido (`area_dist_sessao_visualizacao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_dist_sessao_visualizacao__sonnet_1206.md`
- [INÉDITO] github.com/RUCAIBox/RecBole — ★4613, push 2025-02-24, MIT — A unified, comprehensive and efficient recommendation library
- [INÉDITO] github.com/RUCAIBox/RecBole3.0 — ★23, push 2026-07-05, MIT — An LLM-Inspired Recommendation Library
- Avaliação (chat LONGOS 06/11): bibliotecas de recomendação acadêmicas (RecBole, KuaiSim, recsim, generative-recommenders): não temos dados de sessão; não serve

## [x] AVALIADO 06/11 — 0 implantados, 0 reprovados, 0 deixados — 2026-11-06 12:44 — Sessão de visualização e vídeo sugerido (`area_dist_sessao_visualizacao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_dist_sessao_visualizacao__sonnet_1231.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 06/11): bibliotecas de recomendação acadêmicas (RecBole, KuaiSim, recsim, generative-recommenders): não temos dados de sessão; não serve

## [x] AVALIADO 06/11 — 0 implantados, 6 reprovados, 0 deixados — 2026-11-06 14:01 — Curva de velocidade por frase e time-stretch (`area_ritmo_climax`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_ritmo_climax__sonnet_1341.md`
- [INÉDITO] github.com/bungee-audio-stretch/bungee — ★361, push 2026-10-30, MPL-2.0 — A C++ library for time-stretching and pitch-shifting audio with high quality in realtime or offline. 
- [INÉDITO] github.com/neputevshina/nanowarp — ★14, push 2026-11-06, Apache-2.0 — a high-quality audio time stretching algorithm
- [INÉDITO] github.com/twardoch/audiostretchy — ★61, push 2026-11-03, BSD-3-Clause — AudioStretchy is a Python wrapper around the `audio-stretch` C library, which performs fast, high-quality time-stretching of WAV/MP3 files w
- [INÉDITO] github.com/robmorgan/timestretch-rs — ★27, push 2026-10-31, MIT — Pure 🦀 Rust audio time-stretching library optimized for electronic dance music.
- [INÉDITO] github.com/gregogiudici/python-stretch — ★16, push 2026-05-24, MIT — Simple python library for pitch shifting and time stretching. Wrapper of Signalsmith Stretch C++ Library
- [INÉDITO] github.com/yongaifadian1/MAGIC-TTS — ★56, push 2026-04-28, MIT — MAGIC-TTS: Fine-Grained Controllable Speech Synthesis with Explicit Local Duration and Pause Control
- Avaliação (chat LONGOS 06/11): ritmo já vem da narração (narracao_curva + climas_voz acelerando no clímax); time-stretch em C++/Rust não acrescenta e mexer na voz está pausado


## [x] AVALIADO 06/11 — 0 implantados, 0 reprovados, 0 deixados — 2026-11-06 16:38 — Crescer canal SEM recursos avançados (`area_yt_crescer_sem_recursos_avancados`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_yt_crescer_sem_recursos_avancados__sonnet_1617.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 06/11): nenhum repositório aproveitável (todos reprovados pelo motor); o que dá pra fazer sem recursos avançados já está: playlist, tela final, horário/canal por dados reais

## [x] AVALIADO 06/11 — 0 implantados, 0 reprovados, 0 deixados — 2026-11-06 16:58 — Conformidade do canal para não perder recursos (`area_yt_conformidade_canal`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_yt_conformidade_canal__sonnet_1646.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 06/11): nenhum repositório aproveitável; a conformidade está no lado da operação: trava_conta.py (não insistir em canal punido), collabs desligadas 06/11, contestação pela dona — ver postador-de-videos\docs\CONTESTACOES_RECURSOS_AVANCADOS.md


## [x] AVALIADO 07/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-06 18:28 — Recuperar recursos avançados do YouTube (caminho oficial) (`area_yt_recursos_avancados_recuperar`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_yt_recursos_avancados_recuperar__sonnet_1822.md`
- [INÉDITO] github.com/AddictedCS/soundfingerprinting — ★1043, push 2026-11-02, MIT — Open source audio fingerprinting in .NET. An efficient algorithm for acoustic fingerprinting written purely in C#.  
- [INÉDITO] github.com/Fl1s/turron — ★71, push 2026-08-21, Apache-2.0 — A search system that analyzes short video snippets (2-5 secs) and finds highly accurate matches using keyframe-based perceptual hashing; Sel
- Avaliação (chat LONGOS 07/11): tema é política do YouTube, não código: soundfingerprinting/turron não recuperam recursos. PISTA útil anotada pra dona: os longos sobem SEM a declaração 'conteúdo alterado (IA)' (postar_longos não passa sintetico) apesar de voz clonada — decisão dela (ver CONTESTACOES_RECURSOS_AVANCADOS.md)

## [x] AVALIADO 07/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-06 20:58 — Mix contínuo no beat para vídeos de 1 a 4 horas (`area_mix_continuo_longform`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_mix_continuo_longform__sonnet_2051.md`
- [INÉDITO] github.com/kckDeepak/AI-DJ-Mixing-System — ★58, push 2026-02-03, MIT — An AI-powered DJ mixing system that crafts custom mixes from your local MP3s using natural language prompts, analyzing BPM, key, and energy 
- [INÉDITO] github.com/VertexSelection/automix-engine — ★8, push 2026-08-22, LGPL-2.1 — A stem-aware AutoMix engine similar to Apple Music's AutoMix for creating beat-synced, phrase-aligned, and vocal-aware DJ transitions from a
- [INÉDITO] github.com/oguzhan-yilmaz/pyCrossfade — ★152, push 2026-08-09, MIT — pyCrossfade is the result of a personal project to use beat matching, gradual bpm shift on bars, and EQ modification to provide smooth and t
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-06 21:21 — Loops de música sem emenda (`area_loops_sem_emenda`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_loops_sem_emenda__sonnet_2111.md`
- [INÉDITO] github.com/scpedicini/loopweave — ★4, push 2026-10-23, MIT — A tool for generating audio equivalents of cinemagraphs - aka seamless, looping segments extracted from longer audio files.
- [INÉDITO] github.com/EternalBox/EternalJukebox — ★829, push 2026-06-10, MIT — The internal workings for the Eternal Jukebox, a rehosting of the Infinite Jukebox
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-06 21:32 — Embeddings de música por clima (`area_mood_audio_embedding`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_mood_audio_embedding__sonnet_2126.md`
- [INÉDITO] github.com/minzwon/musicfm — ★275, push 2024-02-14, NOASSERTION — 
- [INÉDITO] github.com/jordipons/musicnn — ★725, push 2023-12-11, ISC — Pronounced as "musician", musicnn is a set of pre-trained deep convolutional neural networks for music audio tagging.
- [INÉDITO] github.com/marl/openl3 — ★605, push 2023-06-17, MIT — OpenL3: Open-source deep audio and image embeddings
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-06 22:33 — Portão automático de qualidade de áudio antes de postar (`area_qc_audio_mos`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_qc_audio_mos__sonnet_2226.md`
- [INÉDITO] github.com/microsoft/DNS-Challenge — ★1478, push 2024-07-25, CC-BY-4.0 — This repo contains the scripts, models, and required files for the Deep Noise Suppression (DNS) Challenge.  
- [INÉDITO] github.com/microsoft/Distill-MOS — ★57, push 2026-09-14, NOASSERTION — Distillation of Self-Supervised Representation-Based Speech Quality Assessment
- [INÉDITO] github.com/pytorch/audio — ★2961, push 2026-11-06, BSD-2-Clause — Data manipulation and transformation for audio signal processing, powered by PyTorch
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 1 reprovados, 0 deixados — 2026-11-06 22:42 — Reverb por cena com RIR sintética e convolução (`area_reverb_rir_cena`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_reverb_rir_cena__sonnet_2236.md`
- [INÉDITO] github.com/nuniz/blind_rt60 — ★41, push 2024-06-06, MIT — Algorithm for blind estimation of reverberation time
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-06 23:02 — Loudness de vídeos de 1 a 4 horas (`area_loudness_longo_lra`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_loudness_longo_lra__sonnet_2256.md`
- [INÉDITO] github.com/nomonosound/libloudness — ★10, push 2025-08-14, MIT — An efficient loudness meter with support for anchoring, median, and multithreading
- [INÉDITO] github.com/ruuda/bs1770 — ★25, push 2025-12-03, Apache-2.0 — A Rust library that implements ITU-R BS.1770-4 loudness measurement
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-06 23:21 — Limiter true-peak com oversampling (`area_limiter_truepeak`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_limiter_truepeak__sonnet_2306.md`
- [INÉDITO] github.com/Signalsmith-Audio/dsp — ★282, push 2026-10-20, MIT — GitHub mirror of Signalsmith Audio's C++ DSP support library
- [INÉDITO] github.com/Signalsmith-Audio/basics — ★121, push 2026-09-30, MIT — A collection of basic effects, available as open-source (MIT) C++ classes.
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 4 reprovados, 0 deixados — 2026-11-06 23:56 — Checagem de compatibilidade mono e caixa de celular (`area_mono_fone_check`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-06\respostas\area_mono_fone_check__sonnet_2346.md`
- [INÉDITO] github.com/mpariente/pystoi — ★363, push 2023-12-29, MIT — Python implementation of the Short Term Objective Intelligibility measure 
- [INÉDITO] github.com/ludlows/PESQ — ★None, push None, None — 
- [INÉDITO] github.com/jaakkopasanen/AutoEq — ★16417, push 2026-11-05, MIT — Automatic headphone equalization from frequency responses
- [INÉDITO] github.com/pyfar/pyfar — ★138, push 2026-11-06, MIT — python package for acoustics research
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 5 reprovados, 0 deixados — 2026-11-07 00:51 — Detecção automática de golpe/impacto (`area_impact_frame_deteccao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_impact_frame_deteccao__sonnet_0041.md`
- [USA em D:\recapd-ambientes\producao\bin\censura_visual.py:254] github.com/opencv/opencv — ★91474, push 2026-11-06, Apache-2.0 — Open Source Computer Vision Library
- [INÉDITO] github.com/qiuqiangkong/audioset_tagging_cnn — ★1794, push 2024-07-25, MIT — 
- [INÉDITO] github.com/w-hc/torch_audioset — ★106, push 2025-04-16, MIT — PyTorch transcribed audioset classifier, including VGGish and YAMNet, along with utils to manipulate autioset category ontology.
- [INÉDITO] github.com/facebookresearch/perception_models — ★2408, push 2026-04-13, Apache-2.0 — State-of-the-art Image & Video CLIP, Multimodal Large Language Models, and More!
- [INÉDITO] github.com/facebookresearch/vjepa2 — ★4860, push 2026-10-29, MIT — PyTorch code and models for VJEPA2 self-supervised learning from video.
- [INÉDITO] github.com/princeton-vl/RAFT — ★4123, push 2025-08-24, BSD-3-Clause — 
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-07 01:06 — Speed ramp e time remap com fluxo óptico (`area_speed_ramp_fluxo`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_speed_ramp_fluxo__sonnet_0056.md`
- [INÉDITO] github.com/jhogsett/EMA-VFI-WebUI — ★74, push 2026-05-25, MIT — Advanced AI-Based Video Renovation UI Using EMA-VFI & Real-ESRGAN
- [INÉDITO] github.com/MCG-NJU/EMA-VFI — ★503, push 2023-05-29, Apache-2.0 — [CVPR 2023] Extracting Motion and Appearance via Inter-Frame Attention for Efficient Video Frame Interpolatio
- [INÉDITO] github.com/MCG-NJU/VFIMamba — ★159, push 2024-09-26, Apache-2.0 — [NeurIPS 2024] VFIMamba: Video Frame Interpolation with State Space Models 
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 6 reprovados, 0 deixados — 2026-11-07 01:24 — Freeze-frame com contorno e sticker (`area_freeze_contorno`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_freeze_contorno__sonnet_0111.md`
- [USA em D:\recapd-ambientes\producao\bin\doctor.py:50] github.com/danielgatis/rembg — ★None, push ?, ver repo (fallback HTML) — Rembg is a tool to remove images background. Contribute to danielgatis/rembg development by creating an account on GitHub.
- [INÉDITO] github.com/plemeri/transparent-background — ★None, push ?, ver repo (fallback HTML) — This is a background removing tool powered by InSPyReNet (ACCV 2022)
- [INÉDITO] github.com/PramaLLC/BEN2 — ★None, push ?, ver repo (fallback HTML) — Contribute to PramaLLC/BEN2 development by creating an account on GitHub.
- [INÉDITO] github.com/facebookresearch/EdgeTAM — ★None, push ?, ver repo (fallback HTML) — [CVPR 2025] Official PyTorch implementation of &quot;EdgeTAM: On-Device Track Anything Model&quot;
- [INÉDITO] github.com/yformer/EfficientTAM — ★None, push ?, ver repo (fallback HTML) — Efficient Track Anything. Contribute to yformer/EfficientTAM development by creating an account on GitHub.
- [INÉDITO] github.com/ZHKKKe/MODNet — ★None, push ?, ver repo (fallback HTML) — A Trimap-Free Portrait Matting Solution in Real Time [AAAI 2022]
- [INÉDITO] github.com/gkjohnson/three-jumpflood-demo — ★None, push ?, ver repo (fallback HTML) — Demonstration showing real time effects and application of the &quot;Jump Flood Algorithm&quot;
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 1 reprovados, 0 deixados — 2026-11-07 01:34 — Motion blur barato em CPU/Intel (`area_motion_blur_cpu`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_motion_blur_cpu__sonnet_0126.md`
- [INÉDITO] github.com/imserhatdemir/ft-motion — ★47, push 2026-10-30, MIT — Motion graphics as a pure function of time — Canvas 2D scenes, headless-Chrome rendering with motion blur, ffmpeg, synthesized sound, and a 
- [USA em D:\recapd-ambientes\producao\bin\ambientes_supervisor.py:211] github.com/FFmpeg/FFmpeg — ★66654, push 2026-11-07, NOASSERTION — Mirror of https://git.ffmpeg.org/ffmpeg.git
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-07 02:01 — Shaders com licença comercial limpa (`area_isf_shadertoy_licenca_limpa`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_isf_shadertoy_licenca_limpa__sonnet_0151.md`
- [USA em D:\recapd-ambientes\producao\bin\realce_visual.py:30] github.com/lostjared/shaders — ★None, push ?, ver repo (fallback HTML) — Collection of GLSL Shader Effects . Contribute to lostjared/shaders development by creating an account on GitHub.
- [INÉDITO] github.com/subsoap/deffx — ★None, push ?, ver repo (fallback HTML) — A collection of useful shader effects made ready to be used with the Defold game engine
- [INÉDITO] github.com/baku89/ISF4AE — ★None, push ?, ver repo (fallback HTML) — After Effects Plug-in enabling to use GLSL written in ISF as an effect
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 4 reprovados, 0 deixados — 2026-11-07 02:13 — Halação, grão e LUT de filme (`area_halacao_grao_lut`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_halacao_grao_lut__sonnet_0206.md`
- [INÉDITO] github.com/JanLohse/spectral_film_lut — ★None, push ?, ver repo (fallback HTML) — Generate LUT for film emulation based on film datasheets.
- [USA em D:\video-fila\linhas\CORTES\juri\sem-obra-507e1d_cap1_20261029\juri.json:145] github.com/stoatworks-labs/rebate — ★None, push ?, ver repo (fallback HTML) — Colour negative film and its scan, as an FFGL effect for Resolume and an OpenFX plugin for Resolve, Vegas, Nuke and Natron. It runs the proc
- [INÉDITO] github.com/mattdesl/glsl-film-grain — ★None, push ?, ver repo (fallback HTML) — natural looking film grain using noise functions. Contribute to mattdesl/glsl-film-grain development by creating an account on GitHub.
- [INÉDITO] github.com/Studio333Archives/halation-ffmpeg-flask — ★None, push ?, ver repo (fallback HTML) — Trying to make cool Halation grading with ffmpeg. Contribute to Studio333Archives/halation-ffmpeg-flask development by creating an account o
- [INÉDITO] github.com/marc-gronenberg/Marcs-Film-Emulator — ★None, push ?, ver repo (fallback HTML) — Film looks for PhotoCraft: 20 films simulated from manufacturer datasheets, with push/pull, halation and grain (WebAssembly plug-ins)
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 5 reprovados, 0 deixados — 2026-11-07 02:44 — Texto cinético sincronizado com a batida (`area_texto_cinetico_batida`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_texto_cinetico_batida__sonnet_0236.md`
- [USA em D:\recapd-ambientes\producao\bin\legenda_mix.py:146] github.com/iart-ai/motion-skills — ★None, push ?, ver repo (fallback HTML) — 50 open-source skills that teach your AI coding agent to make motion graphics, animation &amp; video — kinetic typography, data-viz, explain
- [INÉDITO] github.com/IskakovDamir/apple-motion — ★21, push 2026-09-29, MIT — Claude skill for Apple-style kinetic typography recaps in Remotion, built from frame-accurate measurements of Apple recap videos
- [INÉDITO] github.com/notivn/AIEV — ★157, push 2026-11-04, MIT — Automatic AI video editing. Claude directs HyperFrames (HTML + GSAP motion graphics) and Remotion (timeline assembly) to turn raw footage in
- [INÉDITO] github.com/vshukla7/remotion-captions-themes — ★11, push 2026-06-23, MIT — Themeable animated word-level caption library for Remotion — kinetic typography, karaoke highlights, and a relation-based layout engine.
- [INÉDITO] github.com/yuna0x0/karaoke-ass — ★2, push 2026-08-08, MIT — Two-row karaoke effect (KFX) template for ASS subtitles, with furigana
- [INÉDITO] github.com/juanitolaguna/beat-sync — ★0, push 2026-09-30, CC0-1.0 — Claude Code skill: sync a video's text, cuts and animations to its music via a millisecond beat map
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 1 reprovados, 0 deixados — 2026-11-07 02:53 — Light leaks e overlays de flash (`area_light_leak_overlay`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_light_leak_overlay__sonnet_0246.md`
- [INÉDITO] github.com/keijiro/LightLeakEffectExample — ★38, push 2026-03-02, SEM LICENÇA — Light Leak Effect with Unity URP
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 5 reprovados, 0 deixados — 2026-11-07 03:04 — Render de shaders headless na T4 (`area_shader_headless_kaggle`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_shader_headless_kaggle__sonnet_0256.md`
- [USA em D:\recapd-ambientes\producao\bin\fx_clips.py:21] github.com/moderngl/moderngl — ★2342, push 2026-10-21, MIT — Modern OpenGL binding for Python
- [INÉDITO] github.com/moderngl/glcontext — ★46, push 2026-11-01, MIT — connects moderngl to your window or create headless contexts :electric_plug:
- [INÉDITO] github.com/pygfx/wgpu-py — ★710, push 2026-11-06, BSD-2-Clause — WebGPU for Python
- [INÉDITO] github.com/pygfx/shadertoy — ★42, push 2026-04-12, BSD-2-Clause — Shadertoy implementation based on wgpu-py
- [INÉDITO] github.com/pygfx/rendercanvas — ★36, push 2026-11-05, BSD-2-Clause — One canvas API, multiple backends
- [INÉDITO] github.com/WassimAarab08/fullgpu-render — ★0, push 2026-11-06, Apache-2.0 — Programmatic video rendering that stays on the GPU end to end (NVDEC → wgpu/WebGPU → NVENC). 23× faster than headless-browser renderers like
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-07 03:26 — Whip pan, zoom punch e motion blur direcional (`area_whip_pan_motion_blur`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_whip_pan_motion_blur__sonnet_0316.md`
- [INÉDITO] github.com/alexwidua/zoom-motion-blur — ★None, push ?, ver repo (fallback HTML) — motion blur shader built using swiftui and metal. Contribute to alexwidua/zoom-motion-blur development by creating an account on GitHub.
- [INÉDITO] github.com/normalizedcrow/DirectionalBlur — ★None, push ?, ver repo (fallback HTML) — A shader for unity that renders directional blur effects
- [INÉDITO] github.com/keijiro/KinoMotion — ★None, push ?, ver repo (fallback HTML) — Motion blur post-processing effect for Unity. Contribute to keijiro/KinoMotion development by creating an account on GitHub.
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 4 reprovados, 0 deixados — 2026-11-07 03:46 — Match cut por similaridade em material existente (`area_match_cut_similaridade`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_match_cut_similaridade__sonnet_0336.md`
- [INÉDITO] github.com/ssrajadh/sentrysearch — ★4581, push 2026-10-31, Apache-2.0 — Semantic search over videos using Gemini Embedding 2 or Qwen3-VL.
- [INÉDITO] github.com/mikkoim/dinotool — ★77, push 2026-06-12, Apache-2.0 — Command-line tool for extracting DINO, CLIP, SigLIP2, TIPSv2, RADIO, features for images and videos
- [INÉDITO] github.com/Netflix/matchcut — ★105, push 2023-09-19, Apache-2.0 — 
- [INÉDITO] github.com/mlfoundations/open_clip — ★14247, push 2026-11-06, NOASSERTION — An open source implementation of CLIP.
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 5 reprovados, 0 deixados — 2026-11-07 04:14 — Overlays de tinta, fumaça e light leak com alpha (`area_overlay_tinta_fumaca`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_overlay_tinta_fumaca__sonnet_0406.md`
- [INÉDITO] github.com/PavelDoGreat/WebGL-Fluid-Simulation — ★16802, push 2024-11-12, MIT — Play with fluids in your browser (works even on mobile)
- [INÉDITO] github.com/cloydlau/webgl-fluid — ★114, push 2026-05-29, MIT — ESM support for https://github.com/PavelDoGreat/WebGL-Fluid-Simulation.
- [INÉDITO] github.com/michaelbrusegard/WebGL-Fluid-Enhanced — ★85, push 2025-06-14, MIT — WebGL Fluid Simulation for modern webpages (works even on mobile).
- [INÉDITO] github.com/Donitzo/three.js-volume-renderer — ★21, push 2026-04-21, MIT — A highly customizable real-time volume renderer for three.js
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-07 04:58 — Decomposição de ilustração em camadas (`area_camadas_anime`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_camadas_anime__sonnet_0451.md`
- [INÉDITO] github.com/QwenLM/Qwen-Image-Layered — ★2173, push 2025-12-31, Apache-2.0 — Qwen-Image-Layered: Layered Decomposition for Inherent Editablity
- [INÉDITO] github.com/tggo/ComfyUI-StableLayers — ★3, push 2026-08-10, Apache-2.0 — ComfyUI nodes for Stable-Layers (Stability AI) + Qwen-Image-Layered — decompose an image into editable RGBA layers. Includes a PEFT/diffuser
- [INÉDITO] github.com/CyberAgentAILab/LayerD — ★144, push 2026-01-19, Apache-2.0 ARQUIVADO — [ICCV 2025] LayerD: Decomposing Raster Graphic Designs into Layers
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 5 reprovados, 0 deixados — 2026-11-07 05:10 — Rig 2D automático com export de vídeo sem tela (`area_rig_2d_headless`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_rig_2d_headless__sonnet_0501.md`
- [INÉDITO] github.com/RevStudio/Rev2D — ★33, push 2026-10-06, MIT — Live2D/Spine-style 2D rigging & animation, built for AI agents. A rig is one JSON file; a deterministic headless renderer, a CLI and an MCP 
- [INÉDITO] github.com/shinshin86/mesh-avatar-studio — ★1898, push 2026-11-06, MIT — Turn one illustration into an animated 2D mesh avatar with a coding agent and a local editor
- [INÉDITO] github.com/Inochi2D/inochi2d — ★1838, push 2026-10-03, BSD-2-Clause — Inochi2D SDK - Bring your characters to life
- [INÉDITO] github.com/nijigenerate/nijigenerate — ★324, push 2026-11-05, BSD-2-Clause — nijigenerate is an open source editor for the nijilive puppet format, which is derived from Inochi2D (v0.8) technology. This application all
- [INÉDITO] github.com/Amoner/lipsync-engine — ★68, push 2026-02-07, MIT — Zero-dependency, renderer-agnostic streaming lip-sync engine for browser-based 2D animation. Real-time viseme detection via AudioWorklet + W
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-07 05:33 — Image-to-video destilado para T4 (`area_i2v_destilado_t4`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_i2v_destilado_t4__sonnet_0526.md`
- [INÉDITO] github.com/hao-ai-lab/FastVideo — ★4788, push 2026-11-06, Apache-2.0 — A unified inference and post-training framework for accelerated video generation.
- [INÉDITO] github.com/ModelTC/ComfyUI-Lightx2vWrapper — ★95, push 2026-11-04, MIT — ComfyUI custom node for lightx2v 
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-07 05:48 — Pan e zoom sem tremor (`area_pan_zoom_subpixel`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_pan_zoom_subpixel__sonnet_0536.md`
- [INÉDITO] github.com/Trekky12/kburns-slideshow — ★77, push 2025-11-09, MIT — generate slideshow movies with Ken Burns effect on images
- [INÉDITO] github.com/asweigart/pytweening — ★128, push 2024-02-20, BSD-3-Clause — A set of tweening / easing functions implemented in Python.
- [INÉDITO] github.com/casiez/OneEuroFilter — ★266, push 2026-08-05, SEM LICENÇA — Algorithm to filter noisy signals for high precision and responsiveness.
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 0 reprovados, 0 deixados — 2026-11-07 05:57 — Cinemagraph por segmentação semântica (`area_cinemagraph_segmentado`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_cinemagraph_segmentado__sonnet_0551.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-07 06:09 — Zoom sincronizado às palavras da narração (`area_zoom_por_palavra`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_zoom_por_palavra__sonnet_0601.md`
- [INÉDITO] github.com/crimeacs/product-demo-director — ★38, push 2026-11-03, MIT — Turn product evidence and raw footage into narration-paced, source-bound demo films—with Codex or Claude Code directing cuts, zooms, render,
- [INÉDITO] github.com/pcauhi/bolo-de-camadas — ★11, push 2026-10-14, MIT — Skill para o Claude Code: você só grava a fala, o Claude monta o reel em 5 camadas (legenda, rosto, gráficos, zoom e som) com Remotion. Esti
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-07 06:19 — Licença comercial dos pesos de image-to-video (`area_matriz_licenca_i2v`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_matriz_licenca_i2v__sonnet_0616.md`
- [INÉDITO] github.com/meituan-longcat/LongCat-Video — ★9355, push 2026-05-27, MIT — 
- [INÉDITO] github.com/PKU-YuanGroup/Helios — ★2254, push 2026-11-01, Apache-2.0 — [TPAMI 2026🔥] Helios: Real Real-Time Long Video Generation Model
- [INÉDITO] github.com/SandAI-org/MAGI-1 — ★3804, push 2026-06-17, Apache-2.0 — MAGI-1: Autoregressive Video Generation at Scale
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado

## [x] AVALIADO 07/11 — 0 implantados, 6 reprovados, 0 deixados — 2026-11-07 06:28 — Pipelines motion-comic completos (`area_motion_comic_pronto`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_motion_comic_pronto__sonnet_0621.md`
- [INÉDITO] github.com/ToBeWin/make-motion-comic — ★3, push 2026-07-20, MIT — Create low-cost motion comics with AI keyframes, Mandarin Edge TTS, and anti-jitter FFmpeg rendering.
- [INÉDITO] github.com/hideaway007/2d-comic-video-workflow — ★2, push 2026-05-28, MIT — Local-first 2D comic to 2.5D motion-comic video workflow with Remotion, FFmpeg, QA gates, and a Codex skill
- [INÉDITO] github.com/Mr-funny/hbg-life-simulation — ★150, push 2026-08-05, MIT — HBG Agent Skill for Chinese life-simulation narrative videos with consistent comic IP, rapid multi-life openings, Edge TTS, synchronized cap
- [INÉDITO] github.com/kha-white/manga-ocr — ★2828, push 2026-07-19, Apache-2.0 — Optical character recognition for Japanese text, with the main focus being Japanese manga
- [INÉDITO] github.com/HBAI-Ltd/Toonflow-app — ★20968, push 2026-11-05, MIT — 短剧、漫剧制作工具 Toonflow：开源 AI 视频创作平台，集成剧本创作、智能分镜、角色与场景资产管理、图像生成和视频生成。融合无限画布、AI Agent 与可视化工作流，支持本地部署、自选模型、跨平台客户端、MCP 与插件扩展。Open-source AI short dr
- [INÉDITO] github.com/bo961386926/manga-studio — ★28, push 2026-10-25, MIT — MangaStudio (漫剧工场) — AI-powered short-drama / manga / motion-comic video workbench with Script->Asset->Keyframe workflow
- Avaliação (chat LONGOS 07/11): efeitos/transições/áudio do longo NÃO mudam sem a dona (pedido dela 04/11: 'transições e efeitos fazem muita diferença, não podemos mudar'); dona viajando até 09/11 — fica registrado, não implantado


## [x] AVALIADO 07/11 — movido p/ CURTOS (9:16 não é longo) — 2026-11-07 06:54 — Detectores de rosto e pessoa com pesos comerciais em CPU (`area_reenq_detector_comercial`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_reenq_detector_comercial__sonnet_0646.md`
- [INÉDITO] github.com/LibreYOLO/libreyolo — ★1001, push 2026-11-07, MIT — LibreYOLO is a MIT licensed open source computer vision library
- [INÉDITO] github.com/Tau-J/rtmlib — ★698, push 2026-11-07, Apache-2.0 — RTMPose series (RTMPose, DWPose, RTMO, RTMW) without mmcv, mmpose, mmdet etc.
- [INÉDITO] github.com/yakhyo/uniface — ★2203, push 2026-11-06, MIT — A Unified Face Analysis Library for Python | Detection, alignment, landmarks, face-mesh, recognition, parsing, gaze, attributes and anti-spo
- [INÉDITO] github.com/yakhyo/retinaface-pytorch — ★82, push 2026-10-20, MIT — RetinaFace face detection in PyTorch - training, WIDER FACE evaluation, ONNX export and real-time inference with pretrained weights.
- [INÉDITO] github.com/Megvii-BaseDetection/YOLOX — ★10692, push 2025-06-08, Apache-2.0 — YOLOX is a high-performance anchor-free YOLO, exceeding yolov3~v5 with MegEngine, ONNX, TensorRT, ncnn, and OpenVINO supported. Documentatio
- [INÉDITO] github.com/Star-Clouds/CenterFace — ★1344, push 2021-11-12, MIT — face detection
- Avaliação (chat LONGOS 07/11): reenquadramento para 9:16 é dos Shorts; bloco copiado para ENTREGAS\CURTOS.md.

## [x] AVALIADO 07/11 — movido p/ CURTOS (9:16 não é longo) — 2026-11-07 07:04 — Suavização de caminho de câmera (`area_reenq_caminho_camera`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_reenq_caminho_camera__sonnet_0656.md`
- [INÉDITO] github.com/pantor/ruckig — ★1438, push 2026-09-29, MIT — Motion Generation for Robots and Machines. Real-time. Jerk-constrained. Time-optimal.
- Avaliação (chat LONGOS 07/11): reenquadramento para 9:16 é dos Shorts; bloco copiado para ENTREGAS\CURTOS.md.

## [x] AVALIADO 07/11 — movido p/ CURTOS (9:16 não é longo) — 2026-11-07 07:19 — Saliência de vídeo com pesos liberados para uso comercial (`area_reenq_saliencia_comercial`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_reenq_saliencia_comercial__sonnet_0711.md`
- [INÉDITO] github.com/alexanderkroner/saliency — ★216, push 2024-05-28, MIT — Contextual Encoder-Decoder Network for Visual Saliency Prediction [Neural Networks 2020]
- [INÉDITO] github.com/opencv/opencv_contrib — ★10229, push 2026-11-05, Apache-2.0 — Repository for OpenCV's extra modules
- [INÉDITO] github.com/LJOVO/TranSalNet — ★73, push 2024-07-25, MIT — TranSalNet: Towards perceptually relevant visual saliency prediction. Neurocomputing (2022)
- Avaliação (chat LONGOS 07/11): reenquadramento para 9:16 é dos Shorts; bloco copiado para ENTREGAS\CURTOS.md.

## [x] AVALIADO 07/11 — movido p/ CURTOS (9:16 não é longo) — 2026-11-07 07:35 — Preenchimento de borda para 9:16 (`area_reenq_outpaint_barato`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_reenq_outpaint_barato__sonnet_0726.md`
- [INÉDITO] github.com/mutonby/shortcast — ★396, push 2026-06-04, Apache-2.0 — Native macOS app: drop a long video → auto-cut viral shorts, captioned for TikTok/Reels/YouTube, reframed to vertical, and scheduled. 100% o
- [INÉDITO] github.com/ausboss/ComfyUI-AusBoss — ★118, push 2026-11-07, MIT — ComfyUI nodes I made for my own workflows: click or type to mask a thing, crop, rotate and pad by dragging handles, inpaint and outpaint tha
- Avaliação (chat LONGOS 07/11): reenquadramento para 9:16 é dos Shorts; bloco copiado para ENTREGAS\CURTOS.md.

## [x] AVALIADO 07/11 — movido p/ CURTOS (9:16 não é longo) — 2026-11-07 07:50 — Validação automática do enquadramento antes de postar (`area_reenq_validacao_saida`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_reenq_validacao_saida__sonnet_0741.md`
- [INÉDITO] github.com/fralapo/FrameShift — ★None, push ?, ver repo (fallback HTML) — It automatically reframes videos to a target aspect ratio while keeping faces and objects in view.
- Avaliação (chat LONGOS 07/11): reenquadramento para 9:16 é dos Shorts; bloco copiado para ENTREGAS\CURTOS.md.

## [x] AVALIADO 07/11 — movido p/ CURTOS (9:16 não é longo) — 2026-11-07 08:00 — Zonas seguras de interface por plataforma (`area_reenq_zonas_seguras_ui`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_reenq_zonas_seguras_ui__sonnet_0756.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 07/11): reenquadramento para 9:16 é dos Shorts; bloco copiado para ENTREGAS\CURTOS.md.

## [x] AVALIADO 07/11 — movido p/ CAPAS — 2026-11-07 08:11 — LoRA de personagem com licença limpa (`area_lora_personagem_comercial`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_lora_personagem_comercial__sonnet_0806.md`
- [INÉDITO] github.com/ostris/ai-toolkit — ★12572, push 2026-11-04, MIT — The ultimate training toolkit for finetuning diffusion models
- [INÉDITO] github.com/AcademiaSD/AcademiaSD_LoRAlab-TrainerStudio — ★137, push 2026-11-04, MIT — Train LoRAs for Qwen-Image 2.1, FLUX.2 Klein 9B, FLUX.3 Image Klein, Krea 2, Z-Image, MOSS-Image, ERNIE-Image, Ideogram 4, Anima, SDXL (Pony
- [INÉDITO] github.com/EnragedAntelope/dataset-deviser — ★9, push 2026-10-26, MIT — Turn a character, style, or concept into a ready-to-train LoRA dataset - consistent multi-angle shots, smart captions (prose / Danbooru / e6
- Avaliação (chat LONGOS 07/11): LoRA de personagem e upscale de rosto são das CAPAS; copiado para ENTREGAS/CAPAS.md.

## [x] AVALIADO 07/11 — movido p/ CAPAS — 2026-11-07 08:25 — Upscale e restauração de rosto anime (`area_upscale_rosto_anime`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_upscale_rosto_anime__sonnet_0816.md`
- [INÉDITO] github.com/chaiNNer-org/spandrel — ★317, push 2026-04-12, MIT — Spandrel gives your project support for various PyTorch architectures meant for AI Super-Resolution, restoration, and inpainting. Based on t
- [INÉDITO] github.com/the-database/traiNNer-redux — ★139, push 2026-10-30, Apache-2.0 — Deep learning training framework for image super resolution and restoration.
- [INÉDITO] github.com/nihui/waifu2x-ncnn-vulkan — ★3500, push 2026-04-13, MIT — waifu2x converter ncnn version, runs fast on intel / amd / nvidia / apple-silicon GPU with vulkan
- Avaliação (chat LONGOS 07/11): LoRA de personagem e upscale de rosto são das CAPAS; copiado para ENTREGAS/CAPAS.md.

## [x] AVALIADO 07/11 — movido p/ VEO_HIPERCOOL — 2026-11-07 08:48 — ComfyUI em lote no Kaggle (`area_comfy_kaggle_lote`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_comfy_kaggle_lote__sonnet_0841.md`
- [INÉDITO] github.com/robertvoy/ComfyUI-Distributed — ★649, push 2026-11-01, Apache-2.0 — ComfyUI extension that enables multi-GPU processing locally, remotely and in the cloud
- [INÉDITO] github.com/Chaoses-Ib/ComfyScript — ★705, push 2026-07-18, MIT — A Python frontend and library for ComfyUI
- [INÉDITO] github.com/pydn/ComfyUI-to-Python-Extension — ★2394, push 2026-05-10, MIT — A powerful tool that translates ComfyUI workflows into executable Python code.
- [INÉDITO] github.com/StableCanvas/comfyui-client — ★151, push 2026-10-25, MIT — all ComfyUI http/ws APIs. support NodeJS / Browser environments. and advanced programmable workflow.
- [INÉDITO] github.com/bentoml/comfy-pack — ★215, push 2025-11-10, Apache-2.0 ARQUIVADO — A comprehensive toolkit for reliably locking, packing and deploying environments for ComfyUI workflows.
- Avaliação (chat LONGOS 07/11): o longo é recap a partir do vídeo original, não gera vídeo por IA; copiado para ENTREGAS/VEO_HIPERCOOL.md.

## [x] AVALIADO 07/11 — movido p/ VEO_HIPERCOOL — 2026-11-07 08:55 — Edição com várias imagens de referência (`area_edicao_multi_referencia`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_edicao_multi_referencia__sonnet_0851.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 07/11): o longo é recap a partir do vídeo original, não gera vídeo por IA; copiado para ENTREGAS/VEO_HIPERCOOL.md.

## [x] AVALIADO 07/11 — movido p/ VEO_HIPERCOOL — 2026-11-07 09:31 — Vídeo longo e streaming autoregressivo (`area_video_longo_autoregressivo`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_video_longo_autoregressivo__sonnet_0921.md`
- [INÉDITO] github.com/OpenImagingLab/FlashVSR — ★None, push ?, ver repo (fallback HTML) — [CVPR 2026] Towards Real-Time Diffusion-Based Streaming Video Super-Resolution — An efficient one-step diffusion framework for streaming VSR
- [INÉDITO] github.com/NVlabs/Sana — ★None, push ?, ver repo (fallback HTML) — SANA &amp; Sol: Efficient Generative Models and Full-Stack Training &amp; Inference Engines for Image, Video, and World Modeling
- [INÉDITO] github.com/guandeh17/Self-Forcing — ★None, push ?, ver repo (fallback HTML) — Official codebase for &quot;Self Forcing: Bridging Training and Inference in Autoregressive Video Diffusion&quot; (NeurIPS 2025 Spotlight)
- [INÉDITO] github.com/lllyasviel/FramePack — ★None, push ?, ver repo (fallback HTML) — Lets make video diffusion practical! Contribute to lllyasviel/FramePack development by creating an account on GitHub.
- Avaliação (chat LONGOS 07/11): o longo é recap a partir do vídeo original, não gera vídeo por IA; copiado para ENTREGAS/VEO_HIPERCOOL.md.

## [x] AVALIADO 07/11 — movido p/ VEO_HIPERCOOL — 2026-11-07 09:44 — Quantização que roda em Turing (sm_75) (`area_t4_quantizacao_turing`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_t4_quantizacao_turing__sonnet_0936.md`
- [INÉDITO] github.com/Comfy-Org/comfy-kitchen — ★None, push ?, ver repo (fallback HTML) — Fast kernel library for Diffusion inference with multiple compute backends.
- [INÉDITO] github.com/vipshop/cache-dit — ★None, push ?, ver repo (fallback HTML) — A PyTorch-native inference engine with cache, parallelism, quantization and cpu offload for 100+ DiTs.
- Avaliação (chat LONGOS 07/11): o longo é recap a partir do vídeo original, não gera vídeo por IA; copiado para ENTREGAS/VEO_HIPERCOOL.md.

## [x] AVALIADO 07/11 — movido p/ VEO_HIPERCOOL — 2026-11-07 09:56 — Runtimes de pouca VRAM para vídeo (`area_low_vram_runtimes`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_low_vram_runtimes__sonnet_0951.md`
- [INÉDITO] github.com/modelscope/DiffSynth-Studio — ★None, push ?, ver repo (fallback HTML) — Enjoy the magic of Diffusion models! Contribute to modelscope/DiffSynth-Studio development by creating an account on GitHub.
- Avaliação (chat LONGOS 07/11): o longo é recap a partir do vídeo original, não gera vídeo por IA; copiado para ENTREGAS/VEO_HIPERCOOL.md.

## [x] AVALIADO 07/11 — movido p/ VEO_HIPERCOOL — 2026-11-07 10:02 — Licença e território do MiniMax H3 (`area_licenca_minimax_h3`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_licenca_minimax_h3__sonnet_1001.md`
- [INÉDITO] github.com/AtlasCloudAI/awesome-minimax-h3 — ★None, push ?, ver repo (fallback HTML) — Everything built on top of MiniMax H3 — weights, quantizations, LoRAs, ComfyUI nodes, workflows and the tricks people found. H3 only, SFW on
- Avaliação (chat LONGOS 07/11): o longo é recap a partir do vídeo original, não gera vídeo por IA; copiado para ENTREGAS/VEO_HIPERCOOL.md.

## [x] AVALIADO 07/11 — movido p/ VEO_HIPERCOOL — 2026-11-07 10:10 — Licenças Tencent (Hunyuan e VAE do Kandinsky) (`area_licencas_tencent_territorio`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_licencas_tencent_territorio__sonnet_1006.md`
- [INÉDITO] github.com/Tencent-Hunyuan/HunyuanVideo — ★12738, push 2026-10-08, NOASSERTION — HunyuanVideo: A Systematic Framework For Large Video Generation Model
- [INÉDITO] github.com/Tencent-Hunyuan/HunyuanVideo-Avatar — ★2211, push 2025-12-16, NOASSERTION — 
- [INÉDITO] github.com/Tencent-Hunyuan/HunyuanImage-3.0 — ★3301, push 2026-06-23, NOASSERTION — HunyuanImage-3.0: A Powerful Native Multimodal Model for Image Generation
- [INÉDITO] github.com/Tencent-Hunyuan/HunyuanDiT — ★4290, push 2026-10-08, NOASSERTION — Hunyuan-DiT : A Powerful Multi-Resolution Diffusion Transformer with Fine-Grained Chinese Understanding
- [INÉDITO] github.com/Tencent-Hunyuan/Hunyuan3D-2.1 — ★4383, push 2025-10-17, NOASSERTION — From Images to High-Fidelity 3D Assets with Production-Ready PBR Material
- Avaliação (chat LONGOS 07/11): o longo é recap a partir do vídeo original, não gera vídeo por IA; copiado para ENTREGAS/VEO_HIPERCOOL.md.

## [x] AVALIADO 07/11 — movido p/ VEO_HIPERCOOL — 2026-11-07 10:27 — Custo por segundo de vídeo em T4/P100 (`area_custo_por_segundo_t4`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_custo_por_segundo_t4__sonnet_1016.md`
- [USA em D:\recapd-ambientes\producao\bin\separar_trilha.py:4] github.com/meta-pytorch/torchcodec — ★1198, push 2026-11-06, BSD-3-Clause — Media decoding and encoding for PyTorch: videos, images, and audio, on CPU and GPU.
- [INÉDITO] github.com/CVCUDA/CV-CUDA — ★2733, push 2026-10-20, NOASSERTION — CV-CUDA™ is an open-source, GPU accelerated library for cloud-scale image processing and computer vision.
- [USA em D:\recapd-ambientes\producao\bin\anime_fetch.py:21] github.com/SYSTRAN/faster-whisper — ★26556, push 2026-11-06, MIT — Faster Whisper transcription with CTranslate2
- [INÉDITO] github.com/NVIDIA-AI-Technology-Center/accelerated-video-for-ai-playbook — ★8, push 2026-04-13, MIT — Video processing plays a crucial role in Large Vision and Language Models (VLMs). Video is a heavy data format to process due to its native 
- Avaliação (chat LONGOS 07/11): o longo é recap a partir do vídeo original, não gera vídeo por IA; copiado para ENTREGAS/VEO_HIPERCOOL.md.

## [x] AVALIADO 07/11 — movido p/ VEO_HIPERCOOL — 2026-11-07 10:36 — First-last frame para transições e loops (`area_primeiro_ultimo_frame`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_primeiro_ultimo_frame__sonnet_1031.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 07/11): o longo é recap a partir do vídeo original, não gera vídeo por IA; copiado para ENTREGAS/VEO_HIPERCOOL.md.


## [x] AVALIADO 07/11 — movido p/ VEO_HIPERCOOL — 2026-11-07 10:47 — Correções de movimento das LoRAs de 4 passos (`area_correcao_lora_4passos`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_correcao_lora_4passos__sonnet_1041.md`
- [INÉDITO] github.com/princepainter/ComfyUI-PainterI2V — ★636, push 2026-08-01, SEM LICENÇA — An enhanced Wan2.2 Image-to-Video node specifically designed to fix the slow-motion issue in 4-step LoRAs (like lightx2v).
- Avaliação (chat LONGOS 07/11): geração de vídeo por IA; copiado p/ VEO_HIPERCOOL.md.

## [x] AVALIADO 07/11 — movido p/ VEO_HIPERCOOL — 2026-11-07 10:57 — LTX-2.5 DFR e IC-LoRAs (`area_ltx25_dfr_iclora`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_ltx25_dfr_iclora__sonnet_1051.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 07/11): geração de vídeo por IA; copiado p/ VEO_HIPERCOOL.md.

## [x] AVALIADO 07/11 — 0 implantados, 0 reprovados, 0 deixados — 2026-11-07 13:09 — Gancho medido por retenção (`area_gancho_retencao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_gancho_retencao__sonnet_1301.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 07/11): nada aproveitável; retenção dos longos já é boa (33-36%%, ~27 min — Studio); o problema é impressão

## [x] AVALIADO 07/11 — 0 implantados, 8 reprovados, 0 deixados — 2026-11-07 13:25 — Detector de texto de IA em pt-BR e espanhol (`area_antislop_ptes`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_antislop_ptes__sonnet_1316.md`
- [INÉDITO] github.com/eurafaeldecarvalho/humanizer-pt-br — ★0, push 2026-10-29, MIT — Agent skill that removes AI-writing tells from Brazilian Portuguese, with real before/after examples and an eval set.
- [INÉDITO] github.com/MrBridgeHQ/human-writer-pt — ★0, push 2026-07-28, MIT — Human Writer (Brazilian Portuguese) - AI-text humanizer & 0-100 detector (Claude Code skill). Part of the mr-bridge.com toolkit.
- [INÉDITO] github.com/MrBridgeHQ/human-writer-es — ★0, push 2026-07-28, MIT — Human Writer (Spanish) - AI-text humanizer & 0-100 detector (Claude Code skill). Part of the mr-bridge.com toolkit.
- [INÉDITO] github.com/ljmor/my-humanizer-es-en — ★2, push 2026-07-21, MIT — Claude skill that humanizes AI-flagged academic & professional text (ES/EN) to pass stylometric detectors like Compilatio, Turnitin & GPTZer
- [INÉDITO] github.com/pablocaeg/sloptotal — ★100, push 2026-11-03, MIT — Open-source AI text detector and ChatGPT detector: 23 engines, one calibrated score, every number measured on a public benchmark. Self-hoste
- [INÉDITO] github.com/JoaquinRuiz/nonio — ★4, push 2026-09-15, Apache-2.0 — A measuring instrument for text, not an AI detector. Estimates statistical signals of machine-generated language and reports them with measu
- [INÉDITO] github.com/madebydiego/humanizador — ★0, push 2026-08-03, MIT — Humanize Spanish text in Claude Code: a skill that removes AI writing patterns, with country packs (Bolivia, Mexico, neutral) and domain pac
- [INÉDITO] github.com/Byk3y/no-slop — ★14, push 2026-04-08, MIT — A prose linter that catches AI writing patterns. Based on Wikipedia's Signs of AI Writing.
- Avaliação (chat LONGOS 07/11): humanizadores/detectores com 0-14 estrelas; o roteiro já tem _SEM_CLICHE (prompt v17) e não é texto lido, é narrado

## [x] AVALIADO 07/11 — 0 implantados, 6 reprovados, 0 deixados — 2026-11-07 13:36 — Agendador de promessas e open loops (`area_open_loops`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_open_loops__sonnet_1326.md`
- [INÉDITO] github.com/danjdewhurst/story-skills — ★394, push 2026-11-04, MIT — Agent Skills for end-to-end story writing in markdown, packaged as Codex and Claude Code plugins.
- [INÉDITO] github.com/Anshler/graphify-novel — ★79, push 2026-04-16, MIT — A knowledge-graph AI writing assistant - tracks characters, threads, and world-building across your full manuscript, scaffolds your story bi
- [INÉDITO] github.com/Lanerra/saga — ★115, push 2026-09-15, Apache-2.0 — Autonomous, agentic, creative story writing system that incorporates stored embeddings and Knowledge Graphs.
- [INÉDITO] github.com/Nigh/show-me-the-story — ★637, push 2026-10-15, MIT — <10 MB — self-hosted AI novel writer in a single Go binary with a web UI. Turn ideas into outlines and chapters with review, foreshadowing, 
- [INÉDITO] github.com/bbaz123/novel-studio — ★7, push 2026-10-25, MIT — Local-first AI writing studio for 100+ chapter novels: foreshadowing, character state and worldbuilding consistency gates. Node.js + SQLite,
- [INÉDITO] github.com/Shashank-ssls/StoryWeave — ★6, push 2026-09-30, MIT —  Spoiler-aware knowledge graph for web novels — entities & relationships fenced to the chapter you've read. Local-first, GLiNER floor + opti
- Avaliação (chat LONGOS 07/11): escritores de romance longo (knowledge graph): o roteiro do recap segue o anime original, não inventa trama; mini-ganchos já existem (L-F2)

## [x] AVALIADO 07/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-07 13:49 — Humor para narração (`area_humor_narracao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_humor_narracao__sonnet_1341.md`
- [INÉDITO] github.com/altsoph/lmfaoooo — ★3, push 2026-02-23, MIT — Supplementary materials for the paper “Humor Is an Audience: Preference Modeling for Constrained Humor Generation” (SemEval-2026 Task 1: MWA
- [INÉDITO] github.com/jmhessel/caption_contest_corpus — ★61, push 2025-03-19, MIT — Corpus to accompany: "Do Androids Laugh at Electric Sheep? Humor "Understanding" Benchmarks from The New Yorker Caption Contest"
- Avaliação (chat LONGOS 07/11): corpus acadêmico de humor (New Yorker): não aplicável ao narrador clonado

## [x] AVALIADO 07/11 — 0 implantados, 4 reprovados, 0 deixados — 2026-11-07 14:08 — Escritor+crítico com placar numérico (`area_escritor_critico`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_escritor_critico__sonnet_1401.md`
- [INÉDITO] github.com/iLearn-Lab/NovelClaw — ★None, push ?, ver repo (fallback HTML) — Dynamic-memory-first collaborative AI framework for long-form story generation, chapter planning, and coherent narrative writing
- [INÉDITO] github.com/dylanhogg/gptauthor — ★None, push ?, ver repo (fallback HTML) — GPTAuthor is an AI tool for writing long form, multi-chapter stories given a story prompt.
- [INÉDITO] github.com/DaoyuanLi2816/pairjudge — ★None, push ?, ver repo (fallback HTML) — Pairwise LLM judges (A/B/tie): budget-aware multi-turn packing, position-bias correction, pseudo-label distillation. Generalized from the 4t
- [INÉDITO] github.com/madaan/self-refine — ★None, push ?, ver repo (fallback HTML) — LLMs can generate feedback on their work, use it to improve the output, and repeat this process iteratively.
- Avaliação (chat LONGOS 07/11): self-refine/gptauthor: o melhorador_longo já faz escritor+júri com nota e desfaz se piorar

## [x] AVALIADO 07/11 — 0 implantados, 5 reprovados, 1 deixados — 2026-11-07 14:20 — Métrica de recompensa barata para otimizar roteiro (`area_recompensa_roteiro`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_recompensa_roteiro__sonnet_1411.md`
- [INÉDITO] github.com/eric-tramel/slop-guard — ★167, push 2026-07-09, MIT — Slop Scoring to Stop Slop
- [INÉDITO] github.com/yanstd888/humanizer-lint — ★100, push 2026-11-07, MIT — A local, zero-dependency prose, copywriting, UI-text, and code-comment linter that flags stiff, AI-sounding writing (stock phrases, flat sen
- [INÉDITO] github.com/lynote-ai/ai-text-detector — ★658, push 2026-10-13, MIT — A cautious, explainable AI text detector for local workflows and coding agents. Need production detection in your app? Try the Lynote AI Det
- [INÉDITO] github.com/LSYS/LexicalRichness — ★114, push 2026-05-02, MIT — :smile_cat: :speech_balloon: A module to compute textual lexical richness (aka lexical diversity).
- [INÉDITO] github.com/textstat/textstat — ★1393, push 2026-10-26, MIT — :memo: python package to calculate readability statistics of a text object - paragraphs, sentences, articles.
- [INÉDITO] github.com/thememium/dspy-auto-gepa — ★19, push 2026-07-04, MIT — AutoGEPA automates the tedious parts of setting up a DSPy optimization pipeline: converting raw data into dspy.Examples, generating a metric
- Avaliação (chat LONGOS 07/11): textstat/LexicalRichness/ai-text-detector reprovados; slop-guard DEIXADO (ver nota)
  - DEIXADO eric-tramel/slop-guard: nota de 'texto de IA' do roteiro (MIT, 167 estrelas) — poderia virar 1 sinal do júri do melhorador; NÃO implantado com a dona viajando (roteiro em produção funcionando); avaliar com ela

## [x] AVALIADO 07/11 — 0 implantados, 10 reprovados, 0 deixados — 2026-11-07 14:33 — Juiz de qualidade narrativa (`area_juiz_narrativo`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_juiz_narrativo__sonnet_1426.md`
- [INÉDITO] github.com/EQ-bench/Judgemark-v2 — ★30, push 2025-11-13, MIT — 
- [INÉDITO] github.com/Picrew/ConStory-Bench — ★186, push 2026-04-07, MIT — ConStory-Bench (ACL 26')
- [INÉDITO] github.com/EQ-bench/eqbench3 — ★71, push 2026-05-31, MIT — 
- [INÉDITO] github.com/IIIIQIIII/DramaBench — ★88, push 2026-01-01, MIT — A six-dimensional evaluation framework for drama script continuation with interactive leaderboard and case studies
- [INÉDITO] github.com/NLP2CT/NCP-Bench — ★37, push 2026-08-14, MIT — 
- [INÉDITO] github.com/X-PLUG/WritingBench — ★207, push 2025-12-19, Apache-2.0 — WritingBench: A Comprehensive Benchmark for Generative Writing
- [INÉDITO] github.com/OpenDFM/ibsen — ★60, push 2025-07-05, MIT — [ACL 2024] Official code for "IBSEN: Director-Actor Agent Collaboration for Controllable and Interactive Drama Script Generation" (TheatreMa
- [INÉDITO] github.com/Alex-Gurung/ReasoningNCP — ★79, push 2025-04-19, MIT — Official repo for Learning to Reason for Long-Form Story Generation
- [INÉDITO] github.com/Aman-4-Real/DPWriter — ★16, push 2026-09-24, Apache-2.0 — [ACL 2026 Oral] DPWriter: Reinforcement Learning with Diverse Planning Branching for Creative Writing
- [INÉDITO] github.com/OedonLestrange42/WebNovelBench — ★16, push 2025-07-02, MIT — code for paper webnovelbench
- Avaliação (chat LONGOS 07/11): benchmarks acadêmicos (EQ-bench, WritingBench...): o melhorador já tem júri (juri_longo) medido contra views do Studio


## [x] AVALIADO 08/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-07 14:54 — Retenção por export do Studio (`area_retencao_export_studio`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_retencao_export_studio__sonnet_1446.md`
- [INÉDITO] github.com/hildensia/bayesian_changepoint_detection — ★None, push ?, ver repo (fallback HTML) — Methods to get the probability of a changepoint in a time series.
- [INÉDITO] github.com/CamDavidsonPilon/lifelines — ★None, push ?, ver repo (fallback HTML) — Survival analysis in Python. Contribute to CamDavidsonPilon/lifelines development by creating an account on GitHub.
- [INÉDITO] github.com/dengss0131-bit/youtube-growth-review — ★None, push ?, ver repo (fallback HTML) — YouTube 频道增长深度复盘工具：上传 Analytics CSV，自动分析选题、CTR、涨粉效率、流量陷阱和栏目化机会。
- Avaliação (chat LONGOS 08/11): não se aplica aos longos agora (recap 16:9 do vídeo original; efeitos congelados; metadados já via seo_generator)

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-07 15:08 — Viewed vs swiped em experimento (`area_viewed_swiped_medicao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_viewed_swiped_medicao__sonnet_1501.md`
- [INÉDITO] github.com/e10v/tea-tasting — ★None, push ?, ver repo (fallback HTML) — A Python package for the statistical analysis of A/B tests
- [USA em D:\video-fila\produto_fila\disparoemmassa.ia\_postados\disparoemmassa_ia_20261029_031327.json:16] github.com/spotify/confidence — ★None, push ?, ver repo (fallback HTML) — Python library for AB test analysis. Contribute to spotify/confidence development by creating an account on GitHub.
- [INÉDITO] github.com/getyourguide/basemath — ★None, push ?, ver repo (fallback HTML) — Statistical library implementing the Basemath sequential test for A/B experiment analysis

## [x] AVALIADO 08/11 — 0 implantados, 0 reprovados, 0 deixados — 2026-11-07 15:34 — Política do YouTube: rótulo de conteúdo alterado/sintético (voz clonada) (`area_yt_politica_conteudo_sintetico`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_yt_politica_conteudo_sintetico__sonnet_1531.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 08/11): já avaliado 07/11 (pista do rótulo de IA em CONTESTACOES_RECURSOS_AVANCADOS.md)

## [x] AVALIADO 08/11 — 0 implantados, 1 reprovados, 0 deixados — 2026-11-07 15:52 — Política de conteúdo reutilizado e como documentar transformação (`area_yt_politica_conteudo_reutilizado`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_yt_politica_conteudo_reutilizado__sonnet_1543.md`
- [INÉDITO] github.com/AcademySoftwareFoundation/OpenTimelineIO — ★None, push ?, ver repo (fallback HTML) — Open Source API and interchange format for editorial timeline information.
- [USA em D:\video-fila\linhas\CORTES\juri\sem-obra-d391d9_cap1_20261104\juri.json:186] github.com/OpenTimelineIO/raven — ★None, push ?, ver repo (fallback HTML) — Raven - OpenTimelineIO Viewer Application. Contribute to OpenTimelineIO/raven development by creating an account on GitHub.
- Avaliação (chat LONGOS 08/11): lido e útil (support.google.com 1311392/2801973): o recap fica no 'permitido' por narração própria que reescreve + edição; risco real = template igual em dezenas de canais (produção em massa). Anotado p/ a dona

## [x] AVALIADO 08/11 — 0 implantados, 0 reprovados, 1 deixado — 2026-11-07 16:00 — Fontes novas de recap de anime/manhwa em inglês (vídeos de 1-3 h) (`area_fontes_recap_ingles`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_fontes_recap_ingles__sonnet_1556.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 08/11): DEIXADO p/ a dona: achado bom — Manhwa Fans (UC_gGrnUAJiTOG_T5899dxmg) 13/15 vídeos de 62-153 min, 1 a cada 3 dias = formato exato; mas não é parceiro autorizado e a política de conteúdo reutilizado vale mesmo com permissão. Fonte nova = decisão dela (anotado em RONDA_FIM_DE_SEMANA_06NOV.md)

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-07 16:30 — Loop perfeito final→início (`area_loop_final_inicio`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-07\respostas\area_loop_final_inicio__sonnet_1621.md`
- [USA em D:\video-fila\linhas\CORTES\juri\sem-obra-a07af3_cap1_20261030\juri.json:76] github.com/NolanNicholson/Looper — ★263, push 2022-06-21, MIT — A script for repeating music seamlessly and endlessly, designed with video game music in mind.
- [INÉDITO] github.com/DogNellaf/video-loop-detector — ★2, push 2026-06-22, MIT ARQUIVADO — A desktop GUI application that automatically detects seamlessly looping segments in video files and applies smooth cross-fade effects to pre
- [INÉDITO] github.com/theczechr/video-loop-detection — ★0, push 2025-12-03, MIT — Detects the seamless loop point in a video and trims it to a perfect loop — OpenCV for frame analysis, FFmpeg for frame-precise cutting.

## [x] AVALIADO 08/11 — 0 implantados, 5 reprovados, 0 deixados — 2026-11-08 00:12 — Recap de mangá e vídeo por VLM com licença clara (`area_recap_vlm_licenca`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_recap_vlm_licenca__sonnet_0001.md`
- [INÉDITO] github.com/JuneYaooo/rea-video — ★3722, push 2026-11-08, Apache-2.0 — Reverse-engineer any video, shot by shot: tells whether each shot was filmed, AI-generated or coded, how the captions, cuts and audio were m
- [INÉDITO] github.com/ogkalu2/comic-translate — ★3004, push 2026-11-06, Apache-2.0 — AI comic and manga translator app/browser extension for automatically translating comics, manga, manhwa, BDs, fumetti, and more in multiple 
- [INÉDITO] github.com/pedrovgs/DeepPanel — ★180, push 2026-01-16, Apache-2.0 — Finding a panel inside a comic page is the hardest thing I've ever done in computer science!
- [INÉDITO] github.com/MechTechnology/SmartStitch — ★142, push 2026-06-06, MIT — A small program for stitching together webtoons/manhwa/manhua raws.
- [INÉDITO] github.com/meangrinch/MangaTranslator — ★364, push 2026-10-28, Apache-2.0 — Manga translation app powered by AI
- Avaliação (chat LONGOS 08/11): não se aplica aos longos agora (recap 16:9 do vídeo original; efeitos congelados; metadados já via seo_generator)

## [x] AVALIADO 08/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-08 01:06 — Pausas em vídeos de 1 a 4 h (`area_tom_silencio_longo`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_tom_silencio_longo__sonnet_0056.md`
- [INÉDITO] github.com/BTawaifi/Audio-DeSilencer — ★28, push 2026-10-15, MIT — An audio processing tool for detecting and removing silence in audio recordings. Create text files for video silence removal using custom-de
- [INÉDITO] github.com/studio-dots-ai/dots.tts.edit-data-pipeline — ★10, push 2026-10-26, Apache-2.0 — Data pipeline for building precise speech-editing datasets with text, emotion, free-form style, prosody, and pause edits.
- [INÉDITO] github.com/Jeevav62/voxpolish — ★10, push 2026-06-22, MIT — VoxPolish - a TTS dataset cleaner. Remove noise, trim silence, normalize loudness for text-to-speech training data in one command.
- Avaliação (chat LONGOS 08/11): não se aplica aos longos agora (recap 16:9 do vídeo original; efeitos congelados; metadados já via seo_generator)

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 01:17 — Barra de progresso e cartões de capítulo em longos (`area_cap_overlay`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_cap_overlay__sonnet_0111.md`
- [INÉDITO] github.com/xytime/video-progress-bar-cli — ★4, push 2026-11-07, MIT — A Python CLI tool to add dynamic progress bars, chapter markers, and custom titles to videos using FFmpeg. (一个使用 FFmpeg 为视频自动添加动态进度条、章节标记和自定
- [INÉDITO] github.com/DrBanshan/chapter-progress-bar-plus — ★1, push 2026-05-14, Apache-2.0 — A skill to create chapter progress bar for videos
- [INÉDITO] github.com/ChecheChat/video-progress-bar-skill — ★2, push 2026-06-08, MIT — Generate transparent chapter progress bar overlays for Jianying/CapCut videos.
- [INÉDITO] github.com/ApeCodeAI/vmarker — ★19, push 2026-05-04, Apache-2.0 — vmarker (Auto Chapter Bar or `acb` in CLI) is an open-source Python tool that converts SRT subtitle files into transparent video chapter pro

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 01:37 — Loop sem emenda para streams ambiente (`area_loop_ambiente`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_loop_ambiente__sonnet_0131.md`
- [INÉDITO] github.com/Violinet-tech/seamless-loop-video — ★3, push 2026-10-27, MIT — Agent skill: looping ambient video from a still (MiniMax H3 in ComfyUI), with scripts to measure motion and build clean loops.
- [INÉDITO] github.com/Zephurion/mp3-loop — ★2, push 2026-04-21, MIT — tool to convert any MP3 into a seamless 1 hour loop with crossfades.
- [INÉDITO] github.com/micilini/EternalLoop — ★2, push 2026-06-21, MIT — A local infinite music player for Windows that analyzes audio files, detects beats, finds musical loop branches, and creates seamless endles

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 02:05 — Títulos de capítulo multilíngues (`area_cap_i18n`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_cap_i18n__sonnet_0156.md`
- [INÉDITO] github.com/pemistahl/lingua-py — ★1816, push 2026-07-20, Apache-2.0 — The most accurate natural language detection library for Python, suitable for short text and mixed-language text
- [INÉDITO] github.com/zafercavdar/fasttext-langdetect — ★175, push 2026-10-27, MIT — 80x faster and 95% accurate language identification with Fasttext
- [INÉDITO] github.com/cisnlp/GlotScript — ★24, push 2026-11-06, MIT — [LREC 2024] 🖋 Resource and Tool for Writing System Identification 
- [INÉDITO] github.com/blip-box/confusable — ★2, push 2026-11-08, MIT — Unicode spoofing and confusable detection (UTS #39) in pure Python
- [INÉDITO] github.com/cisnlp/GlotLID — ★224, push 2026-11-06, NOASSERTION — [EMNLP 2023] 💬 Language Identification with Support for More Than 2000 Labels 
- [INÉDITO] github.com/cisnlp/MaskLID — ★13, push 2026-11-06, MIT — [ACL 2024] 💬 MaskLID: Code-Switching Language Identification through Iterative Masking
- [INÉDITO] github.com/TigreGotico/linguonnx — ★1, push 2026-11-06, Apache-2.0 — CPU-first language technology models on ONNX Runtime: language identification (GlotLID, ~1600 languages), translation planned
- [INÉDITO] github.com/Unbabel/COMET — ★789, push 2026-04-21, Apache-2.0 —  A Neural Framework for MT Evaluation
- [INÉDITO] github.com/googlefonts/gftools — ★286, push 2026-11-07, Apache-2.0 — Misc tools for working with the Google Fonts library
- [INÉDITO] github.com/jquast/wcwidth — ★469, push 2026-11-01, NOASSERTION — Python and C11 library that measures the width of strings in a terminal

## [x] AVALIADO 08/11 — 0 implantados, 1 reprovados, 0 deixados — 2026-11-08 02:29 — Upload e agenda pelo navegador (`area_upload_navegador`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_upload_navegador__sonnet_0221.md`
- [INÉDITO] github.com/Kaliiiiiiiiii-Vinyzu/patchright-python — ★1592, push 2026-10-20, Apache-2.0 — Undetected Python version of the Playwright testing and automation library. 
- Avaliação (chat LONGOS 08/11): não se aplica aos longos agora (recap 16:9 do vídeo original; efeitos congelados; metadados já via seo_generator)

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 03:12 — Chat e comentários como sinal de destaque (`area_chat_como_sinal`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_chat_como_sinal__sonnet_0301.md`
- [INÉDITO] github.com/lay295/TwitchDownloader — ★None, push ?, ver repo (fallback HTML) — Twitch VOD/Clip Downloader - Chat Download/Render/Replay
- [INÉDITO] github.com/xenova/chat-downloader — ★None, push ?, ver repo (fallback HTML) — A simple tool used to retrieve chat messages from livestreams, videos, clips and past broadcasts. No authentication needed!
- [INÉDITO] github.com/timerring/auto-slice-video — ★None, push ?, ver repo (fallback HTML) — 基于弹幕密度的高能片段自动切片工具 (Auto slice the highlight shorts based on the density of danmaku.)
- [INÉDITO] github.com/hihkm/DanmakuFactory — ★None, push ?, ver repo (fallback HTML) — 支持特殊弹幕的xml转ass格式转换工具. Contribute to hihkm/DanmakuFactory development by creating an account on GitHub.
- [INÉDITO] github.com/timerring/DanmakuConvert — ★None, push ?, ver repo (fallback HTML) — 优化设计的各种弹幕渲染以及 SuperChat 渲染工具 (Python 实现的 DanmakuFactory)
- [INÉDITO] github.com/gwy15/danmu2ass — ★None, push ?, ver repo (fallback HTML) — 将哔哩哔哩的 弹幕 转化为 ass 字幕文件，实时预览. Contribute to gwy15/danmu2ass development by creating an account on GitHub.
- [INÉDITO] github.com/zaacksb/tubechat — ★None, push ?, ver repo (fallback HTML) — Connect to YouTube live chats: real-time messages, sending, polls, moderation, and VOD replay downloads.
- [INÉDITO] github.com/timerring/bilive — ★None, push ?, ver repo (fallback HTML) — 极快的B站直播录制、自动切片、自动渲染弹幕以及字幕并投稿至B站，综合多种模态模型，兼容超低配置机器。Extremely fast live recording, automatic slicing, rendering, uploading and Integrating MLL

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 03:26 — Eventos de áudio (risada, aplauso, plateia) em CPU (`area_eventos_audio_cpu`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_eventos_audio_cpu__sonnet_0317.md`
- [INÉDITO] github.com/qiuqiangkong/panns_inference — ★276, push 2024-03-05, MIT — 
- [INÉDITO] github.com/YuanGongND/ast — ★1485, push 2023-05-21, BSD-3-Clause — Code for the Interspeech 2021 paper "AST: Audio Spectrogram Transformer".
- [INÉDITO] github.com/jrgillick/laughter-detection — ★298, push 2024-07-25, MIT — 
- [INÉDITO] github.com/microsoft/unilm — ★22240, push 2026-09-21, MIT — Large-scale Self-supervised Pre-training Across Tasks, Languages, and Modalities
- [INÉDITO] github.com/Audio-WestlakeU/ATST-SED — ★174, push 2026-06-08, MIT — This repo includes the official implementations of "Fine-tune the pretrained ATST model for sound event detection".

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 03:37 — Avaliar o seletor contra rótulos (`area_avaliar_seletor`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_avaliar_seletor__sonnet_0331.md`
- [INÉDITO] github.com/leedongkyu2019/SVHighlights — ★11, push 2026-08-10, Apache-2.0 — [KDD 2026 Datasets & Benchmarks Track] SVHighlights: a benchmark for highlight detection in extremely long sports videos
- [INÉDITO] github.com/AmenRa/ranx — ★704, push 2025-08-07, MIT — ⚡️A Blazing-Fast Python Library for Ranking Evaluation, Comparison, and Fusion 🐍
- [INÉDITO] github.com/jayleicn/moment_detr — ★358, push 2026-03-09, MIT — [NeurIPS 2021] Moment-DETR code and QVHighlights dataset
- [INÉDITO] github.com/cvangysel/pytrec_eval — ★354, push 2023-10-10, MIT — pytrec_eval is an Information Retrieval evaluation tool for Python, based on the popular trec_eval.

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 04:03 — Variante por plataforma e revisão antes de postar (`area_variantes_plataforma`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_variantes_plataforma__sonnet_0356.md`
- [INÉDITO] github.com/hermoso-ai/social-media-specs — ★0, push 2026-11-05, MIT — Every social and ad platform's real limits as data: caption and ad-copy lengths counted the way each platform counts, image and video sizes,
- [INÉDITO] github.com/HumanSignal/label-studio — ★28648, push 2026-11-07, Apache-2.0 — Label Studio is a multi-type data labeling and annotation tool with standardized output format
- [INÉDITO] github.com/SamurAIGPT/postiz-cheap — ★1394, push 2026-10-26, MIT — Free, open-source Postiz alternative: self-host a social media scheduler with an AI post writer, content calendar, and publishing across 8 p
- [INÉDITO] github.com/zhouxiaoka/autoclip — ★None, push ?, ver repo (fallback HTML) — AutoClip｜一个链接，一键出片。开源 AI 视频剪辑桌面工具，将播客、访谈、课程等长视频自动剪成短视频，生成字幕、封面和发布文案，适配抖音、小红书、TikTok、Reels 与 YouTube Shorts。Open-source AI video clipping &am

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 04:13 — Facecam automática e reação (`area_facecam_auto`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_facecam_auto__sonnet_0406.md`
- [INÉDITO] github.com/kleZ799/clipmint — ★None, push ?, ver repo (fallback HTML) — Free, open-source AI clip generator and Opus Clip alternative. Turns podcasts, vlogs, tutorials and stream VODs into captioned YouTube Short
- [INÉDITO] github.com/Nilson89/nightcut — ★None, push ?, ver repo (fallback HTML) — AI Video Editor. Contribute to Nilson89/nightcut development by creating an account on GitHub.
- [INÉDITO] github.com/mehbul/chopify — ★None, push ?, ver repo (fallback HTML) — Free local AI video clipper for Shorts, Reels and TikTok. Browser dashboard and CLI with resumable batch projects, editable captions/SRT, br

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 04:23 — Visemas para pt-BR sem reconhecedor inglês (`area_visema_ptbr`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_visema_ptbr__sonnet_0416.md`
- [INÉDITO] github.com/lingjzhu/zipa — ★85, push 2026-10-06, MIT — A family of efficient speech models for multilingual phone recognition
- [INÉDITO] github.com/traderpedroso/xphoneBR — ★13, push 2024-08-28, MIT — XphoneBR is a Brazilian portuguese transformer base grapheme-to-phoneme and normalization  tool modeling library that leverages recent deep 

## [x] AVALIADO 08/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-08 04:37 — QA de render longo (`area_longo_qa`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_longo_qa__sonnet_0426.md`
- [INÉDITO] github.com/Eureka175/ChronoSync — ★3, push 2026-09-13, MIT — Multi-track audio timebase estimation, alignment and clock-drift correction for recordings from independent devices. TimeMap abstraction, GC
- [INÉDITO] github.com/meizhong986/WhisperJAV — ★2441, push 2026-11-05, MIT — ASR/STT subtitle generator. Uses Qwen3-ASR, local LLM, Whisper, TEN-VAD. Noise-robust for JAV
- [INÉDITO] github.com/AlexHayton/av-drift-detector — ★0, push 2026-10-26, BSD-2-Clause-Patent — Generate machine-readable A/V sync test videos and measure audio/video drift frame by frame
- Avaliação (chat LONGOS 08/11): não se aplica aos longos agora (recap 16:9 do vídeo original; efeitos congelados; metadados já via seo_generator)

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 04:59 — Roteiro para linha do tempo de poses e gestos (`area_pose_timeline_llm`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_pose_timeline_llm__sonnet_0451.md`
- [INÉDITO] github.com/567-labs/instructor — ★14101, push 2026-11-06, MIT — structured outputs for llms 
- [INÉDITO] github.com/dottxt-ai/outlines-core — ★320, push 2026-08-05, Apache-2.0 — Faster structured generation

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 05:14 — Runtimes 2D sem licença de editor pago (`area_runtime_2d_livre`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_runtime_2d_livre__sonnet_0506.md`
- [INÉDITO] github.com/thorvg/thorvg — ★None, push ?, ver repo (fallback HTML) — A production-ready C++ vector graphics engine supporting SVG and Lottie formats, featuring advanced rendering backends such as WebGPU for hi
- [INÉDITO] github.com/thorvg/thorvg.web — ★None, push ?, ver repo (fallback HTML) — ThorVG web integration for Lottie players and WebCanvas using WebGL and WebGPU
- [INÉDITO] github.com/rive-app/rive-runtime — ★None, push ?, ver repo (fallback HTML) — Low-level C++ runtime and renderer for Rive, the agent-native 2D and 3D engine for games, apps, and interactive UI.
- [INÉDITO] github.com/rive-app/rive-wasm — ★None, push ?, ver repo (fallback HTML) — Web runtime (JS/WASM) for Rive, the agent-native 2D and 3D engine for games, apps, and interactive UI.
- [INÉDITO] github.com/LottieFiles/dotlottie-rs — ★None, push ?, ver repo (fallback HTML) — High-performance Lottie &amp; dotLottie player in Rust, with bindings for Android, iOS, Web (WASM), and C/C++.
- [INÉDITO] github.com/DragonBones/DragonBonesJS — ★None, push ?, ver repo (fallback HTML) — DragonBones TypeScript / JavaScript Runtime. Contribute to DragonBones/DragonBonesJS development by creating an account on GitHub.
- [INÉDITO] github.com/jaisurya-dev-art/rigby2d — ★None, push ?, ver repo (fallback HTML) — Open-source 2D skeletal animation editor for games and film. AutoRig layered PSDs, animate with meshes, IK and physics, lip-sync from audio,
- [USA em D:\claude-code-video\remotion\package-lock.json:1338] github.com/airbnb/lottie-web — ★None, push ?, ver repo (fallback HTML) — Render After Effects animations natively on Web, Android and iOS, and React Native. http://airbnb.io/lottie/

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 05:22 — Render determinístico de WebGL e Three.js sem GPU (`area_webgl_frame_a_frame`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_webgl_frame_a_frame__sonnet_0516.md`
- [INÉDITO] github.com/alexey-pelykh/puppeteer-capture — ★None, push ?, ver repo (fallback HTML) — A Puppeteer plugin for capturing page as a video with ultimate quality
- [INÉDITO] github.com/remotion-dev/template-three — ★None, push ?, ver repo (fallback HTML) — ⚛️  🎥 3️⃣  A minimal boilerplate for Remotion + React Three Fiber
- [INÉDITO] github.com/workeffortwaste/gsap-video-export — ★None, push ?, ver repo (fallback HTML) — Expertly and easily export GreenSock (GSAP) animation to video.
- [INÉDITO] github.com/google/swiftshader — ★None, push ?, ver repo (fallback HTML) — SwiftShader is a high-performance CPU-based implementation of the Vulkan graphics API. Its goal is to provide hardware independence for adva
- [INÉDITO] github.com/jakoch/rasterizers — ★None, push ?, ver repo (fallback HTML) — Precompiled libraries for the software rasterizers Mesa&#39;s LLVMpipe and Google&#39;s Swiftshader for Windows. Builds are used by https://
- [INÉDITO] github.com/juniorxsound/headless-three-webgpu — ★None, push ?, ver repo (fallback HTML) — Render images, videos and GIFs using headless three.js with WebGPU and Dawn 🎥

## [x] AVALIADO 08/11 — movido p/ VEO_HIPERCOOL — 2026-11-08 05:40 — See-through em fp16 ou NF4 na T4 (`area_see_through_t4`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_see_through_t4__sonnet_0536.md`
- [INÉDITO] github.com/iamtie34/see-through-portable — ★2, push 2026-06-06, Apache-2.0 — One-click portable launcher for See-through anime layer decomposition | 上傳一張動漫角色插圖，自動分解為完整修補的語義圖層並依深度排序，匯出為多圖層 PSD 檔案。

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 05:54 — Apresentador de produto 100% local (`area_apresentador_local`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_apresentador_local__sonnet_0546.md`
- [INÉDITO] github.com/zhangrongxiang/LeapTalk — ★212, push 2026-10-29, Apache-2.0 — We propose LeapTalk, a novel framework that achieves stable and real-time talking-head generation with a single forward step, scaling to arb
- [INÉDITO] github.com/Soul-AILab/SoulX-FlashHead — ★1193, push 2026-05-28, Apache-2.0 — SoulX-FlashHead: A unified 1.3B-parameter framework designed for high-fidelity, infinite-length, and real-time streaming portrait video gene

## [x] AVALIADO 08/11 — 0 implantados, 0 reprovados, 0 deixados — 2026-11-08 06:17 — Dados de título × views (`area_titulo_dados_ctr`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_titulo_dados_ctr__sonnet_0611.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 08/11): não se aplica aos longos agora (recap 16:9 do vídeo original; efeitos congelados; metadados já via seo_generator)

## [x] AVALIADO 08/11 — 0 implantados, 2 reprovados, 0 deixados — 2026-11-08 06:27 — Publicar traduções de metadados sem API (`area_metadados_studio_navegador`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_metadados_studio_navegador__sonnet_0621.md`
- [INÉDITO] github.com/yxxrn/youtube-studio-uploader — ★0, push 2026-09-02, MIT — Browser-driven YouTube Studio uploader for Shorts and videos using persistent Chrome profiles.
- [INÉDITO] github.com/cryptotech407/ytmla — ★0, push 2026-10-16, MIT — Multi-language audio tracks for YouTube: API tooling plus the Studio automation the API does not expose.
- Avaliação (chat LONGOS 08/11): não se aplica aos longos agora (recap 16:9 do vídeo original; efeitos congelados; metadados já via seo_generator)

## [x] AVALIADO 08/11 — 0 implantados, 5 reprovados, 0 deixados — 2026-11-08 06:41 — Capítulos para vídeos de 1 a 4 h (`area_capitulos_topicos_longos`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_capitulos_topicos_longos__sonnet_0631.md`
- [INÉDITO] github.com/feyninc/chonkie — ★None, push None, None — 
- [INÉDITO] github.com/huggingface/sentence-transformers — ★None, push None, None — 
- [INÉDITO] github.com/nltk/nltk — ★14767, push 2026-11-05, Apache-2.0 — NLTK Source
- [INÉDITO] github.com/lucas-ventura/chapter-llama — ★103, push 2025-06-06, MIT — Official PyTorch implementation of the paper "Chapter-Llama: Efficient Chaptering in Hour-Long Videos with LLMs"
- [INÉDITO] github.com/MaartenGr/BERTopic — ★7942, push 2026-11-05, MIT — Leveraging BERT and c-TF-IDF to create easily interpretable topics. 
- Avaliação (chat LONGOS 08/11): não se aplica aos longos agora (recap 16:9 do vídeo original; efeitos congelados; metadados já via seo_generator)

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 06:51 — Hashtags e limites por plataforma (`area_hashtags_regras_plataforma`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_hashtags_regras_plataforma__sonnet_0646.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 07:02 — SEO por idioma e país (`area_seo_por_idioma`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_seo_por_idioma__sonnet_0656.md`
- [INÉDITO] github.com/askads/mcp-yandex-wordstat — ★9, push 2026-11-04, MIT — MCP server for Yandex Wordstat: search query volume, related phrases, trends and regions in Claude, Cursor, Codex
- [INÉDITO] github.com/seyka-ai/yandex-tools-mcp — ★70, push 2026-10-28, MIT — MCP servers for Yandex APIs: Search, Wordstat, Webmaster, Metrika and Direct. Keyword research, SEO analytics and PPC management for Russian

## [x] AVALIADO 08/11 — movido p/ CURTOS — 2026-11-08 07:15 — Checagem de tradução de textos curtos (`area_qualidade_traducao_titulos`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_qualidade_traducao_titulos__sonnet_0706.md`
- [INÉDITO] github.com/google-research/metricx — ★154, push 2026-07-02, Apache-2.0 — 
- [INÉDITO] github.com/deusjin/subforge — ★103, push 2026-09-02, MIT — Rust CLI for AI subtitle workflows: transcribe, segment, translate, evaluate, and burn or mux subtitles.
- [INÉDITO] github.com/mjpost/sacrebleu — ★1265, push 2026-08-20, Apache-2.0 — Reference BLEU implementation that auto-downloads test sets and reports a version string to facilitate cross-lab comparisons
- [INÉDITO] github.com/google-research/mt-metrics-eval — ★140, push 2026-04-23, Apache-2.0 — Tools for evaluating the performance of MT metrics on data from recent WMT metrics shared tasks.
- [INÉDITO] github.com/AppTek/SubER — ★28, push 2026-05-07, Apache-2.0 — SubER - Subtitle Edit Rate
- [INÉDITO] github.com/UrgenProchnoff/prozetta — ★11, push 2026-11-03, MIT — LLM pipeline for literary translation with a consistency glossary and a self-checking quality loop
- [INÉDITO] github.com/Jkaotlic/ollama-subtitle-translator — ★5, push 2026-08-26, MIT — Offline subtitle translator with 2026 LLMs (Gemma 4, Qwen 3.5, Hunyuan-MT, Llama 4 Scout) via Ollama. Web UI + CLI, 17 languages, video subt

## [x] AVALIADO 08/11 — 0 implantados, 0 reprovados, 0 deixados — 2026-11-08 07:23 — Regras de spam e metadados enganosos (`area_politica_metadados_enganosos`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_politica_metadados_enganosos__sonnet_0721.md`
- (todos os itens desta pesquisa foram reprovados)
- Avaliação (chat LONGOS 08/11): lido e útil: clickbait que não entrega e produção em massa são o risco; anotado p/ a dona

## [x] AVALIADO 08/11 — 0 implantados, 3 reprovados, 0 deixados — 2026-11-08 07:33 — Análise de títulos de concorrentes (`area_pesquisa_concorrentes_titulos`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_pesquisa_concorrentes_titulos__sonnet_0726.md`
- [INÉDITO] github.com/maximtrp/bitermplus — ★85, push 2026-08-27, MIT — Biterm Topic Model (BTM): modeling topics in short texts
- [INÉDITO] github.com/yuniko-software/bge-m3-onnx — ★46, push 2026-05-18, Apache-2.0 — ONNX implementation of the BGE-M3 multilingual embedding model and tokenizer with native C#, Java, and Python implementations. Generates all
- [INÉDITO] github.com/centre-for-humanities-computing/tweetopic — ★37, push 2026-10-05, MIT — Blazing fast topic modelling for short texts.
- Avaliação (chat LONGOS 08/11): não se aplica aos longos agora (recap 16:9 do vídeo original; efeitos congelados; metadados já via seo_generator)


## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-08 07:54 — Dublagem de mangá, manhwa e anime (`area_dub_manga_anime`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_dub_manga_anime__sonnet_0736.md`
- [INÉDITO] github.com/liuzhao1225/YouDub-webui — ★5814, push 2026-11-06, Apache-2.0 — Open-source AI video localization and dubbing for YouTube/Bilibili: speech recognition, subtitle translation, voice cloning, audio mixing an
- [INÉDITO] github.com/lukaszliniewicz/Pandrator — ★647, push 2026-11-08, MIT — Turn PDFs and EPUBs into audiobooks; subtitles or videos into dubbed videos (including translation), and more. For free. Pandrator uses loca
- [INÉDITO] github.com/heyncth/youtube-auto-dub — ★310, push 2026-10-20, MIT — AI-powered YouTube video dubbing pipeline. Automatically transcribes (Whisper), translates (Google), and generates neural dubbing (Edge-TTS)
- [INÉDITO] github.com/Bugsbunnydev2000/local_anime_dubber — ★3, push 2026-09-30, SEM LICENÇA — A local, offline AI dubbing pipeline: takes a Japanese video (anime or live-action) + a short voice sample, and produces an English-dubbed v
- [INÉDITO] github.com/agentic-lab-club/manhwa-dubbing-system — ★2, push 2026-06-16, SEM LICENÇA — An automated AI-powered pipeline for creating professional manhwa recap videos with emotional voice-over narration and background music for 

## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-08 09:57 — Sinais de ranking do YouTube em 2026 (`area_sinais_yt_2026`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_sinais_yt_2026__sonnet_0951.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-08 16:00 — Moderação e filtro de spam (`area_moderacao_comentarios`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_moderacao_comentarios__sonnet_1551.md`
- [INÉDITO] github.com/unitaryai/detoxify — ★1313, push 2026-11-08, Apache-2.0 — Trained models & code to predict toxic comments on all 3 Jigsaw Toxic Comment Challenges. Built using ⚡ Pytorch Lightning and 🤗 Transformers
- [INÉDITO] github.com/viddexa/safetext — ★59, push 2025-12-27, MIT — Fast profanity word, curse word, swear word, bad word filtering tool for English, Spanish, Chinese, Turkish and more.
- [INÉDITO] github.com/FlacSy/BadWords — ★24, push 2026-11-01, MIT — Multilingual profanity filter with a Rust core — Python, JavaScript/WASM and Rust, with optional multi-label toxicity scoring

## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-08 18:35 — Política do YouTube para conteúdo repetitivo e gerado por IA (`area_yt_policy_ia`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-08\respostas\area_yt_policy_ia__sonnet_1827.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-09 00:14 — Recuperar recursos avançados do YouTube (caminho oficial) (`area_yt_recursos_avancados_recuperar`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-09\respostas\area_yt_recursos_avancados_recuperar__sonnet_0001.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-09 01:53 — Playlists e séries para longos (`area_dist_playlists_series`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-09\respostas\area_dist_playlists_series__sonnet_0143.md`
- [INÉDITO] github.com/SethMMorton/natsort — ★1014, push 2026-10-16, MIT — Simple yet flexible natural sorting in Python.
- [INÉDITO] github.com/rapidfuzz/RapidFuzz — ★4198, push 2026-11-09, MIT — Rapid fuzzy string matching in Python using various string metrics
- [INÉDITO] github.com/suzuki3jp/PlaylistWizard — ★16, push 2026-11-05, MIT — 📝 Easily manage and organize your playlists on the web! - Playlist Manager

## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-09 02:06 — Canal novo de longos: arranque com poucas impressões (`area_dist_canal_novo_longo`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-09\respostas\area_dist_canal_novo_longo__sonnet_0201.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-09 02:17 — Diagnóstico de impressões baixas (YouTube Analytics leitura) (`area_dist_impressoes_diagnostico`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-09\respostas\area_dist_impressoes_diagnostico__sonnet_0211.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-09 02:32 — Distribuição e algoritmos (`area_distribuicao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-09\respostas\area_distribuicao__sonnet_0226.md`
- [INÉDITO] github.com/social-media-skills/skills — ★271, push 2026-10-15, MIT — 106 social media skills for AI agents - strategy, writing, video, design, platform growth, publishing, and analytics. Works with Claude, Cur
- [INÉDITO] github.com/ndesv21/socialclaw — ★107, push 2026-10-12, MIT — Social media scheduling CLI and OpenClaw skill for AI agents posting to X, LinkedIn, Instagram, Facebook Pages, TikTok, Discord, Telegram, Y
- [INÉDITO] github.com/MerlinStacks/socaliseit — ★32, push 2026-11-05, MIT — A powerful social media management platform with multi-track video editing (Remotion), unified publishing across Instagram, TikTok, YouTube 

## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-09 02:41 — Tela final, playlist e sessão (`area_fim_playlist`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-09\respostas\area_fim_playlist__sonnet_0236.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-09 02:59 — Séries e playlists em Shorts (`area_shorts_seriados`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-09\respostas\area_shorts_seriados__sonnet_0246.md`
- [INÉDITO] github.com/Hao0321/ai-short-drama — ★81, push 2026-08-13, MIT — AI short-drama story architecture, Studio routing, model-aware shot timelines, continuity, validation, and resumable workflows for Codex and
- [INÉDITO] github.com/bertramquinlan/script2video — ★37, push 2026-10-19, MIT — Script-to-video workflow for storyboards, shot clips, last-frame continuity, subtitles, export, and explicit video job boundaries.
- [INÉDITO] github.com/pixellion2262-fwtk2/series-bible — ★34, push 2026-07-29, MIT — 

## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-09 04:31 — Ponte Short -> longo (link relacionado, fixado, cards) (`area_dist_ponte_short_longo`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-09\respostas\area_dist_ponte_short_longo__sonnet_0421.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 09/11 08:55 — 0 aplicados, itens reprovados no motor (dublagem/moderação/playlist/agendador fora do gargalo; sinais_yt/ponte/fim_playlist já cobertos por pesos_canais+ligar_pontes+LONGO_TELA_FINAL; reporting_bulk exige OAuth = decisão da dona) — 2026-11-09 06:02 — YouTube Reporting API em lote com OAuth leitura (`area_yt_reporting_bulk`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-09\respostas\area_yt_reporting_bulk__sonnet_0556.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 09/11 16:40 — 0 implantados, 0 reprovados, 1 deixado (DECISÃO DA DONA: 'conteúdo não original' mira produção em massa com modelo pronto/mesmo desfecho — é o risco nº 4 da lista RONDA_FIM_DE_SEMANA_06NOV; variar estrutura/trilha/abertura entre canais precisa do ok dela) — 2026-11-09 15:04 — Política YouTube de conteúdo inautêntico/reutilizado (`area_yt_inauthentic`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-09\respostas\area_yt_inauthentic__sonnet_1501.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 09/11 16:40 — 0 implantados, 0 reprovados, 1 deixado (DECISÃO DA DONA, nº 3 da lista: voz clonada de narração NÃO exige declaração pela página do YouTube; declarar não reduz alcance; containsSyntheticMedia só via API OAuth = regra 'Google só navegador') — 2026-11-09 15:37 — Rótulo de conteúdo sintético YouTube/TikTok/Meta (`area_yt_ai_label`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-09\respostas\area_yt_ai_label__sonnet_1531.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 10/11 04:40 — 0 implantados, 0 reprovados, 1 deixado (DECISÃO DA DONA: igual ao bloco de 09/11 — voz clonada de narração não exige rótulo; declarar não reduz alcance) — 2026-11-10 04:25 — Política do YouTube: rótulo de conteúdo alterado/sintético (voz clonada) (`area_yt_politica_conteudo_sintetico`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-10\respostas\area_yt_politica_conteudo_sintetico__sonnet_0421.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 10/11 04:40 — 0 implantados, 1 reprovado, 0 deixados (o risco de 'produção em massa' já está na lista da dona, nº 5) — 2026-11-10 04:41 — Política de conteúdo reutilizado e como documentar transformação (`area_yt_politica_conteudo_reutilizado`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-10\respostas\area_yt_politica_conteudo_reutilizado__sonnet_0431.md`
- [INÉDITO] github.com/Sinoosoida/video-match-finder — ★3, push 2026-05-14, MIT — Partial near-duplicate video detection: DINOv2 + FAISS + smooth Hough-with-permutation. CLI + OpenAI-compatible embeddings server.

## [x] AVALIADO 10/11 04:40 — 0 implantados, 1 reprovado, 1 deixado (canais citados: 10HManhwaRecap, DailyManhwas232, MANHWARECAP-s3s, ManhwaRecapZone — fonte nova só com autorização da dona; a dona já escolheu 8 vídeos em config/fontes_prioridade.json 09/11) — 2026-11-10 04:51 — Fontes novas de recap de anime/manhwa em inglês (vídeos de 1-3 h) (`area_fontes_recap_ingles`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-10\respostas\area_fontes_recap_ingles__sonnet_0446.md`
- [INÉDITO] github.com/anime-db-project/anime-timestamp-db — ★2, push 2026-11-09, Apache-2.0 — Open aggregated database of anime episode timestamps, including openings, endings, recaps, previews, and other skip segments from multiple s

## [x] AVALIADO 11/11 03:45 — 1 implantado (ideia, não repo: playlist POR SÉRIE em ordem — postar_longos._playlist_do_longo / PLAYLIST_SERIES; LONGO_PLAYLIST_SERIE=0 desliga; 1ª série = Medieval Age na Fio da Meada), 0 reprovados, 0 deixados — 2026-11-11 03:41 — Séries e playlists como sinal de sessão (`area_serie_playlist`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_serie_playlist__sonnet_0336.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 11/11 16:55 — 0 implantados, 9 reprovados (recap de vídeo existente; memória de série = roteiro da parte anterior), 0 deixados — 2026-11-11 04:50 — Bíblia de série para roteiros por LLM (`area_serie_bible`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_serie_bible__sonnet_0441.md`
- [INÉDITO] github.com/zenstory-ai/oh-story-claudecode — ★8505, push 2026-11-11, MIT — AI 写网文全流程 skill 包：扫榜选材、拆解爆款、大纲细纲、长篇设定与伏笔追踪、短篇反转、去AI味与封面生成，适配 Claude Code / Codex / Antigravity / OpenCode 等 ｜ Agent skill pack for writing C
- [INÉDITO] github.com/tigerless-labs/agent-memory — ★4311, push 2026-11-10, MIT — Long-term memory runtime for AI agents — plain Markdown as the source of truth, local ranked retrieval, and an independent sleep-time Manage
- [INÉDITO] github.com/yantrikos/yantrikdb — ★73, push 2026-11-02, Apache-2.0 — Cognitive memory engine for AI agents — temporal decay, contradiction detection, autonomous consolidation, knowledge graph, ANN recall via H
- [INÉDITO] github.com/LeoYeAI/talewell — ★550, push 2026-10-01, MIT — Plugin-first long-term memory for agent platforms — reference implementation of AMP (Agent Memory Protocol).
- [INÉDITO] github.com/kitfunso/hippo-memory — ★792, push 2026-11-11, MIT — Stop re-teaching your agent. Make your agent's memory work like a brain. Hippo is long-term memory for coding agents. It's a critical layer 
- [INÉDITO] github.com/wassermanproductions/scriptbreak — ★66, push 2026-08-05, Apache-2.0 — Screenplay breakdown & AI prompt-pack studio — import a script, get scenes, elements, bibles, shot lists & a timeline, then export self-exec
- [INÉDITO] github.com/XucroYuri/how-to-make-script — ★22, push 2026-08-24, MIT — Open-source screenwriting knowledge infrastructure for writers and agents: route, generate, review, and orchestrate narrative, branded, and 
- [INÉDITO] github.com/Ardha-Eco-System/synapse — ★80, push 2026-11-09, MIT — Synapse — Temporal knowledge graph memory for AI agents. Self-hosted FalkorDB + Graphiti with hippocampus-layer memory management.
- [INÉDITO] github.com/Dataojitori/nocturne_memory — ★1426, push 2026-11-03, MIT — A lightweight, rollbackable, and visual Long-Term Memory Server for MCP Agents. Say goodbye to Vector RAG and amnesia. Empower your AI with 

## [x] AVALIADO 11/11 16:55 — 0 implantados, 6 reprovados (poucos longos por série, sem amostra; A/B já é do Studio), 0 deixados — 2026-11-11 05:26 — Teste A/B de formato em séries (`area_teste_ab_series`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_teste_ab_series__sonnet_0516.md`
- [INÉDITO] github.com/sdfordham/pysyncon — ★None, push ?, ver repo (fallback HTML) — A python module for the synthetic control method. Contribute to sdfordham/pysyncon development by creating an account on GitHub.
- [INÉDITO] github.com/srpankratyev/switchback-power-calculator — ★None, push ?, ver repo (fallback HTML) — Calculator that computes statistical power, MDE and required sample size for switchback experiments; based on paper Pankratev (2026) &#39;Po
- [INÉDITO] github.com/VowpalWabbit/coba — ★None, push ?, ver repo (fallback HTML) — Contextual bandit benchmarking. Contribute to VowpalWabbit/coba development by creating an account on GitHub.
- [INÉDITO] github.com/david-cortes/contextualbandits — ★None, push ?, ver repo (fallback HTML) — Python implementations of contextual bandits algorithms
- [INÉDITO] github.com/WillianFuks/tfcausalimpact — ★None, push ?, ver repo (fallback HTML) — Python Causal Impact Implementation Based on Google&#39;s R Package. Built using TensorFlow Probability.
- [INÉDITO] github.com/google/CausalImpact — ★None, push ?, ver repo (fallback HTML) — An R package for causal inference in time series. Contribute to google/CausalImpact development by creating an account on GitHub.

## [x] AVALIADO 11/11 16:55 — 1 implantado (ideia: PLAYLIST_SERIES/_playlist_do_longo + 'PARTE N |' no título, LONGO_TITULO_PARTE), 0 reprovados, 0 deixados — 2026-11-11 06:13 — Playlist como série oficial no YouTube Studio (`area_playlist_serie_studio`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_playlist_serie_studio__sonnet_0606.md`
- [INÉDITO] github.com/mickpletcher/yt-librarian — ★0, push 2026-08-11, MIT — Local-first app that crawls, classifies, and playlist-sorts your YouTube Liked Videos via browser automation.

## [x] AVALIADO 11/11 16:55 — 1 implantado (playlist já vai por HTTP: upload_http._playlist), 4 reprovados (Playwright/userscript não acrescentam), 0 deixados — 2026-11-11 06:25 — Automação de playlists pelo navegador (Playwright) (`area_playlist_nav`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_playlist_nav__sonnet_0616.md`
- [INÉDITO] github.com/microsoft/playwright-mcp — ★None, push ?, ver repo (fallback HTML) — Playwright MCP server. Contribute to microsoft/playwright-mcp development by creating an account on GitHub.
- [INÉDITO] github.com/browserbase/stagehand — ★25998, push 2026-11-11, MIT — The SDK to extract data and interact with any site on the web. Get started with Claude Code, Codex, Eve, Mastra, and more.
- [INÉDITO] github.com/mozarkai/optics-framework — ★90, push 2026-11-11, Apache-2.0 — Open-source test automation for Android, iOS, web, smart TV (Android TV, Tizen, webOS) and Bluetooth (BLE) devices. Write tests as CSV/YAML,
- [INÉDITO] github.com/RobertWesner/YouTube-Play-All — ★85, push 2026-11-11, MIT — YTPA - YouTube Play All: A sophisticated userscript adding the Play-All button back to YouTube.
- [INÉDITO] github.com/Fred-Vatin/yt-playlist-filter — ★10, push 2026-08-13, MIT — UserScript that adds an input to the “save to playlist” menu to filter them. Also offers a shortkey to open the “Save to playlist” menu dire

## [x] AVALIADO 11/11 16:55 — 1 implantado (descrição da parte aponta a saga: postar_longos LONGO_TITULO_PARTE), 0 reprovados, 0 deixados — 2026-11-11 06:37 — Título e descrição de playlist para busca (`area_titulo_playlist_busca`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_titulo_playlist_busca__sonnet_0631.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 11/11 16:55 — 0 implantados, 4 reprovados (id estável já é o ID do vídeo original), 0 deixados — 2026-11-11 07:34 — Catálogo local de obras com metadados e identificador estável (`area_catalogo_obras`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_catalogo_obras__sonnet_0726.md`
- [INÉDITO] github.com/simonw/sqlite-utils — ★2193, push 2026-10-11, Apache-2.0 — Python CLI utility and library for manipulating SQLite databases
- [INÉDITO] github.com/akhundMurad/typeid-python — ★153, push 2026-10-26, MIT — Python implementation of TypeIDs: type-safe, K-sortable, and globally unique identifiers inspired by Stripe IDs
- [INÉDITO] github.com/mdomke/python-ulid — ★575, push 2026-10-27, MIT — ULID implementation for Python
- [INÉDITO] github.com/oittaa/uuid6-python — ★182, push 2026-03-27, MIT — New time-based UUID formats which are suited for use as a database key

## [x] AVALIADO 11/11 16:55 — 0 implantados, 2 reprovados (decolando já medido em views_ultimo_longo.json), 0 deixados — 2026-11-11 09:12 — Impressões vs idade e frequência de upload (`area_reach_vs_conteudo_novo`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_reach_vs_conteudo_novo__sonnet_0852.md`
- [INÉDITO] github.com/apache/otava — ★182, push 2026-11-11, Apache-2.0 — Change Detection for Continuous Performance Engineering
- [INÉDITO] github.com/doccstat/fastcpd — ★107, push 2026-10-17, Apache-2.0 — Fast Change Point Detection

## [x] AVALIADO 11/11 16:55 — 1 implantado (playlist por série + PARTE N), 0 reprovados, 0 deixados — 2026-11-11 10:17 — Séries e playlists como alavanca de sessão (`area_series_playlist`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_series_playlist__sonnet_1007.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 11/11 16:55 — 0 implantados, 1 reprovado (API do Google proibida; métricas pelo Studio), 0 deixados — 2026-11-11 14:24 — Playlists e séries no YouTube (`area_pesquisa_playlist_series`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_pesquisa_playlist_series__sonnet_1421.md`
- [INÉDITO] github.com/conorbronsdon/yt-analytics-mcp — ★3, push 2026-11-10, MIT — Curated read-only YouTube Analytics MCP server — owner-side channel, video, and playlist analytics via reports.query. The analytics leg alon

## [x] AVALIADO 2026-11-11 — 0 implantados (já feito hoje: playlist por série em ordem + 'PARTE N |'), 0 reprovados, 0 deixados — 2026-11-11 17:26 — Sequência de episódios em playlist (`area_yt_serie_ordem`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_yt_serie_ordem__sonnet_1721.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-11 — 0 implantados, 0 reprovados, 1 deixado: tela final (até 4 elementos, últimos 20 s) é recurso do Studio por canal; vários canais estão com recursos avançados negados até dez/jan — rever quando voltarem — 2026-11-11 17:36 — Layout do trecho final do longo (`area_yt_telafinal_layout`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_yt_telafinal_layout__sonnet_1731.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-11 — 0 implantados (já existe: produção x postagem independentes, pico de cada país; publishAt +25 min), 0 reprovados, 0 deixados — 2026-11-11 18:07 — Horário de postagem por público (`area_yt_horario_publico`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_yt_horario_publico__sonnet_1801.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-11 — 0 implantados, 0 reprovados, 1 deixado: fixar = recurso avançado, negado em 11 canais até dez/jan (recursos_negados.json); o extras já pula esses canais — 2026-11-11 18:18 — Comentário fixado e perguntas (`area_yt_comentario_fixado`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_yt_comentario_fixado__sonnet_1811.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-11 — 0 implantados (já existe: cortes do longo e pontes Short->longo), 0 reprovados, 0 deixados — 2026-11-11 18:29 — Shorts do mesmo tema do longo (`area_yt_shorts_mesmo_tema`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_yt_shorts_mesmo_tema__sonnet_1821.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-11 — 0 implantados, 0 reprovados, 0 deixados (fora da linha dos longos: TikTok/Insta é do postador) — 2026-11-11 20:40 — Políticas de TikTok e Instagram Reels (`area_tiktok_instagram_politicas`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_tiktok_instagram_politicas__sonnet_2036.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-11 — 0 implantados, 0 reprovados, 1 deixado: medir só com mais partes no ar (hoje 9, 11 e 12 com horas de vida); métrica vem do Studio (--metricas) — 2026-11-11 20:49 — Retenção entre episódios (`area_yt_metricas_serie`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_yt_metricas_serie__sonnet_2046.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-11 — 1 implantado (política de spam 'promessa enganosa': tira '(COMPLETO)'/'Capítulo 1 COMPLETO' do título — postar_longos, LONGO_TITULO_SEM_PROMESSA=0 desliga), 0 reprovados, 0 deixados — 2026-11-11 21:05 — Títulos, descrições e tags (`area_metadata_spam`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_metadata_spam__sonnet_2056.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-12 — 0 implantados (já cumprido: narração nova + comentário do narrador + falas de personagem + memes = transformador; conferido 12/11: 0 de 73 longos com a mesma fonte em 2 canais), 0 reprovados, 0 deixados — 2026-11-11 22:22 — Política de conteúdo reutilizado para anime e mangá (`area_reused_content`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-11\respostas\area_reused_content__sonnet_2216.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-12 — 0 implantados, 0 reprovados, 1 deixado p/ dona: caminho oficial = verificação por documento/vídeo do titular (24 h) ou ~2 meses de histórico limpo; telefone vale só 2 canais por número (explica parte dos 11 canais negados) — 2026-11-12 00:11 — Recuperar recursos avançados do YouTube (caminho oficial) (`area_yt_recursos_avancados_recuperar`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_yt_recursos_avancados_recuperar__sonnet_0006.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-12 — 0 implantados (já: trava_conta, recursos_negados, vídeo único por canal), 0 reprovados, 0 deixados — 2026-11-12 00:30 — Conformidade do canal para não perder recursos (`area_yt_conformidade_canal`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_yt_conformidade_canal__sonnet_0026.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-12 — 0 implantados (já: ligar_pontes/relacionado; recurso avançado negado em 11 canais — extras pula), 0 reprovados, 0 deixados — 2026-11-12 00:47 — Ponte Short -> longo (link relacionado, fixado, cards) (`area_dist_ponte_short_longo`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_dist_ponte_short_longo__sonnet_0041.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-12 — 0 implantados (já: playlist por série + PARTE N), 2 reprovados (anibridge, Shoko), 0 deixados — 2026-11-12 00:59 — Playlists e séries para longos (`area_dist_playlists_series`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_dist_playlists_series__sonnet_0051.md`
- [INÉDITO] github.com/anibridge/anibridge-mappings — ★38, push 2026-11-07, MIT — Mappings for the AniBridge project
- [INÉDITO] github.com/ShokoAnime/ShokoServer — ★788, push 2026-11-10, MIT — Shoko is a media metadata aggregator that solves all of the annoying edge cases that face anime's differing structure from western media. It

## [x] AVALIADO 2026-11-12 — 0 implantados, 0 reprovados, 0 deixados (Fio da Meada VIP + prioridade por views já cobrem) — 2026-11-12 01:06 — Canal novo de longos: arranque com poucas impressões (`area_dist_canal_novo_longo`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_dist_canal_novo_longo__sonnet_0101.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-12 — 0 implantados (métricas já vêm do Studio --metricas; API do Google proibida), 0 reprovados, 0 deixados — 2026-11-12 01:18 — Diagnóstico de impressões baixas (YouTube Analytics leitura) (`area_dist_impressoes_diagnostico`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_dist_impressoes_diagnostico__sonnet_0111.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-12 — 0 implantados, 0 reprovados, 0 deixados (genérico; nada acionável novo) — 2026-11-12 01:29 — Distribuição e algoritmos (`area_distribuicao`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_distribuicao__sonnet_0121.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-12 — 0 implantados, 0 reprovados, 1 deixado: tela final = Studio por canal; esperar recursos voltarem — 2026-11-12 01:44 — Tela final, playlist e sessão (`area_fim_playlist`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_fim_playlist__sonnet_0137.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-12 — 0 implantados, 0 reprovados, 0 deixados (linha CURTOS, não LONGOS) — 2026-11-12 01:57 — Séries e playlists em Shorts (`area_shorts_seriados`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_shorts_seriados__sonnet_0151.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 2026-11-12 — 1 implantado (tela final é recurso PADRÃO: os longos de 12 canais 'parceiro' não ganhavam — extras_ledger.pendentes trata tipo 'completo' como longo, LEDGER_LONGO_POR_TIPO=0 desliga; longo de série aponta a playlist da série, _playlist_serie), 0 reprovados, 1 deixado (fonte 'Playlists' no metricas_rede: medir depois de 1 semana de tela final) — 2026-11-12 03:35 — Crescer canal SEM recursos avançados (`area_yt_crescer_sem_recursos_avancados`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_yt_crescer_sem_recursos_avancados__sonnet_0331.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 12/11 — 0 aplicados, 1 reprovado, 0 deixados — 2026-11-12 08:15 — Loop contínuo de playlist longa

> Retorno (chat dos LONGOS, 12/11): seamless-loop-music REPROVADO — player de BGM de jogo, não gera vídeo nem playlist; a sequência da série já sai em playlist (extras_ledger._playlist_serie) e o compilado (compilar_serie.py) cobre o 'assistir em sequência'.
 (`area_loop_playlist`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_loop_playlist__sonnet_0756.md`
- [INÉDITO] github.com/CPUrising/seamless-loop-music — ★37, push 2026-09-14, MIT — A seamless loop music player for game BGM. 专为游戏音乐设计的无缝循环播放器。

## [x] AVALIADO 12/11 — 0 aplicados, 0 reprovados, 1 deixado — 2026-11-12 16:42 — Conteúdo reutilizado

> Retorno (chat dos LONGOS, 12/11): 1ª pesquisa com a orientação nova e veio NO TEMA (regras do YouTube para recap). DEIXADO: claude-outliers (ideia: vídeo que rende 3x a mediana do PRÓPRIO canal) — serve para o garimpar_fontes.py ordenar por 'views / mediana do canal' em vez de views puras; fazer quando o garimpo tiver 1 semana de dados. As regras citadas (corte de 10 mi de views em Shorts em 02/2027; 'reused content') NÃO foram conferidas por mim na página oficial — conferir antes de mudar qualquer coisa por causa delas.
 aplicado a recap de anime/manhwa (`area_yt_reused_recap`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_yt_reused_recap__sonnet_1636.md`
- [INÉDITO] github.com/chris-jk/claude-outliers — ★1, push 2026-08-01, MIT — A Claude skill that finds a channel's outliers — the videos overperforming that channel's own baseline. Catalog → median → 3x flags, then th

## [x] AVALIADO 12/11 — 0 aplicados, 0 reprovados, 0 deixados (todos já descartados pelo filtro automático) — 2026-11-12 17:57 — SEO de busca para recaps (nome da obra + episódio) (`area_busca_yt_longos`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_busca_yt_longos__sonnet_1751.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 12/11 — 0/0/0 (filtro automático já tirou tudo; nada a avaliar) — 2026-11-12 18:46 — Sons em alta no YouTube Shorts (`area_yt_shorts_audio_trend`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_yt_shorts_audio_trend__sonnet_1831.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 12/11 — 0/0/0 (filtro automático já tirou tudo) — 2026-11-12 20:48 — regras oficiais do YouTube sobre conteúdo reutilizado/recap (`area_regras_yt_2026`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_regras_yt_2026__sonnet_2046.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 12/11 — 0/0/0 (filtro automático já tirou tudo) — 2026-11-12 23:10 — Regras oficiais do YouTube que afetam recaps (`area_yt_regras_oficiais`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-12\respostas\area_yt_regras_oficiais__sonnet_2306.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 13/11 — 0 aplicados, 1 reprovado (Aniflow: pipeline concorrente) — 2026-11-13 00:25 — Fontes novas de recap de anime/manhwa em inglês (vídeos de 1-3 h) (`area_fontes_recap_ingles`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-13\respostas\area_fontes_recap_ingles__sonnet_0012.md`
- [INÉDITO] github.com/aashish254/Aniflow — ★106, push 2026-11-10, MIT — 🎬 Autonomous AI Studio for Manhwa & Webtoon Recaps — Vision Pipeline (YOLOv8 + Magi v2), Multi-Voice TTS & Video Synthesis

## [x] AVALIADO 13/11 — 0/0/0 (filtro já tirou tudo) — 2026-11-13 00:27 — Política do YouTube: rótulo de conteúdo alterado/sintético (voz clonada) (`area_yt_politica_conteudo_sintetico`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-13\respostas\area_yt_politica_conteudo_sintetico__sonnet_0026.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 13/11 — 0/0/0 (filtro já tirou tudo) — 2026-11-13 00:35 — Política de conteúdo reutilizado e como documentar transformação (`area_yt_politica_conteudo_reutilizado`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-13\respostas\area_yt_politica_conteudo_reutilizado__sonnet_0031.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 13/11 — 0/0/0 (filtro já tirou tudo) — 2026-11-13 02:34 — Séries e "assistir a seguir" em canais estrangeiros de recap (`area_playlist_serie_estrangeira`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-13\respostas\area_playlist_serie_estrangeira__sonnet_0226.md`
- (todos os itens desta pesquisa foram reprovados)

## [x] AVALIADO 13/11 — 0/0/0 (filtro automático já tirou tudo; nada a avaliar) — 2026-11-13 05:11 — Mais vistos por país (`area_trends_yt_pais`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-13\respostas\area_trends_yt_pais__sonnet_0506.md`
- (todos os itens desta pesquisa foram reprovados)

## [ ] PENDENTE — 2026-11-13 10:37 — Conteúdo reutilizado aplicado a recap de anime/manhwa (`area_yt_reused_recap`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-13\respostas\area_yt_reused_recap__sonnet_1031.md`
- [INÉDITO] github.com/maatmyali-eng/YouTube-Channel-Replication — ★1, push 2026-10-21, MIT — one reusable, $0 system for modeling any YouTube channel's style (tone, script, hook, audio, visuals, Shorts and long videos, thumbnails) an

## [ ] PENDENTE — 2026-11-13 11:34 — Regras oficiais do YouTube sobre recap e conteúdo reutilizado (`area_regras_yt_oficiais`, Sonnet 5.5 web)
Resposta bruta: `D:\hipercool-materiais\pesquisador_melhorias\rodadas\motor_2026-11-13\respostas\area_regras_yt_oficiais__sonnet_1132.md`
- (todos os itens desta pesquisa foram reprovados)
