# Levantamento do projeto Veo — 15/10/2026 (ponto de salvamento)

> Escrito pelo agente antes de rodar a auditoria com subagentes, para não perder o que já foi apurado caso o limite
> de uso da sessão bata de novo. O resultado final vai em `D:\veo\docs\PLANO_MELHORIAS_VEO.md`. Tudo aqui foi lido no
> código e nos documentos citados; o que é hipótese está marcado como tal.

## 1. O pedido da dona

"Veja todas as melhorias que pode fazer no projeto veo, usando coisas do manhwa-react (que está bem atualizado) e do
hipercool. Tive problemas com os comerciais dos meus produtos: o YouTube identificou como spam e baniu meus canais.
Tenho que melhorar o veo e fazer também que não dê mais banimento. Hoje ele cria um vídeo atrativo, depois um
comercial com o Veo 3 e outro com imagens, que também pode melhorar."

## 2. Onde está cada coisa

| Pasta | O que é | Guia |
|---|---|---|
| `D:\veo` | projeto auditado; `beta\` é a versão que roda ("LIVE"); `experimental\` é cópia antiga desativada em 12/10; `prod\` não existe; `supervisor.py` + `ambientes.json` controlam os ambientes | `beta\README.md`, `beta\ARQUITETURA.md`, `beta\LEIA_PERFIS_E_COFRE.md` (12/10, o mais novo) |
| `D:\postador-de-videos` | postagem compartilhada (YouTube, TikTok, Instagram), política de uploads, relatórios do banimento | `LEIA.txt`, `SPAM_BANIMENTO_2026-09-04.md`, `CONTESTACAO_YOUTUBE_2026-09-22.md` |
| `D:\manhwa-react` | projeto mais atualizado; a "rede" de 19 canais (`mr\rede.py`) é hoje o único caminho saudável até o YouTube | `CLAUDE.md`, `HANDOFF_REDE.md`, `REDE_ESTADO_E_PENDENCIAS.md` |
| `D:\hipercool-videos` | recap de manhwa; fonte oficial das melhorias para todos os projetos de vídeo | `docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md` (15/10), `CLAUDE.md`, `docs\PEDIDOS_DO_DONO_PENDENTES.md` |
| `D:\hipercool-materiais\veo` | saídas do veo: `veo_videos_iniciais` (226 brutos; +487 no Drive), `limpos` (296 arquivos, versão sem marca e sem slide), `pos_final\completo` (22 COMPLETO), `propagandas_vo3` | — |
| `D:\AUDITORIA_MELHORIAS_20261015` | auditoria de hoje feita por outro agente (Sonnet) sobre manhwa-react/historias/recapd; **não auditou o veo** | `RESUMO_EXECUTIVO.md` |

Sem `CLAUDE.md` na raiz de `D:\veo` e sem git na raiz (só `beta\` tem git local).

## 3. Como o veo funciona hoje

### 3.1 Geração do "vídeo atrativo" (`D:\veo\beta`)

`loop_cron.py` → `cron_gerar_video_llm.run()`:
1. escolhe uma conta Google viva (`contas.py`: 13 contas, 12 "pro" e 1 "free"; perfis do Chrome no cofre
   `D:\logins-google\cofre\perfis`);
2. monta o prompt (`montar_prompt`, linha 1077): 30% de chance de replicar uma fórmula vencedora (score ≥ 8), senão o
   multi-agente de `agents.py` (Trend Scout → Hook Generator → Scenario Director → Quality Critic, Gemini Flash Lite
   via `llm_client.py`) com personas de `inteligencia.py`; fallback LLM simples; fallback lista fixa;
3. escolhe uma **foto da dona** em `D:\veo\fotos` (image-to-video) com "foto inteligente" por histórico;
4. dispara `gera_auto.py` como subprocesso: Playwright por CDP num Chrome real logado no Google Flow, modelo
   "Veo 3.1 - Fast", 9:16, 8 s, com áudio; detecta créditos esgotados (exit 2) e troca de conta; detecta recusa por
   direitos autorais e bloqueia a foto/prompt;
5. mp4 em `videos\cron_shorts\`; `thumbnail_client` gera 3 thumbs (A/B/C); `metrics_client` + `logs\video_cache.json`;
   `publicar.py` gera título/descrição/tags por LLM e o `postar.json`; `roteamento.py` mapeia persona → canal real.

Escada de tentativas: 2 tentativas por prompt, 2 prompts por conta, até 3 contas (vídeo fraco: menos).

### 3.2 Pós-produção (`D:\veo\beta\pos_producao`)

`worker_noite.py` gera 2 variantes por vídeo cru, via `montar_final.montar()`:
- `_LIMPO`: punch no gancho → overlay de intro → overlay de impacto (efeitos sorteados por md5 do nome);
- `_COMPLETO`: o mesmo + **clipe VO3 do produto** (sorteado do pool `propagandas_pool\vo3\<produto>_<n>.mp4`, gerado
  por `vo3_propaganda_rotator.py` com prompt do multi-agente `comercial_agents.py`: estrategista → roteirista →
  diretor → crítico, Gemini) → transição elemental → **card CTA** (`cta_card.py`: PNG 1080x1920 com fundo IA de
  `omniroute_image.py`, texto "OFERECIDO POR", nome do produto, copy, **badge com o número de WhatsApp fixo no código**
  e URL; `cta_builder.py`: voz ElevenLabs "sarah" com fallback edge-tts; slide de 5-6 s).

Plugins antigos do `runner.py`/`config.yaml` (loudnorm, crop 9:16, legendas, `propaganda_inteligente`,
`branding_watermark` com marca "@InovareStories" e outro "Siga pra mais historias IA").

As 3 peças que a dona cita: (1) atrativo = clipe criativo de 8 s com a foto dela falando pt-BR; (2) comercial Veo 3 =
clipe VO3 de propaganda (pessoa olhando pra câmera dizendo a fala do roteirista); (3) comercial de imagens = card CTA.

Catálogo de produtos: `pos_producao\assets\produtos.json` (Hermes Call, Avatar IA, Follow-up IA, SuperChat IA como
"top"; Agenda IA, Vitrine IA etc. como secundários; `_meta.whatsapp`).

### 3.3 Postagem

- Caminho antigo (ainda agendado): tarefa `PostadorDeVideos` 06:40 → `bin\postar_tudo_auto.bat` →
  `postar_tudo_hoje.py` (fonte VO3 = `D:\veo\beta\logs\video_cache.json`, round-robin entre canais ativos, título por
  Gemini com "#shorts" e emoji) → `postar_pos_final.py` → … ; tarefa `AgendadorVO3` 05:00 (`agendar_vo3.py`, distribui
  `pos_final` em horários de pico). Hoje "não acham canal livre" porque todos os canais vivos estão reservados à rede.
- Caminho novo (15/10): `bin\limpar_veo.py` tira a marca e corta antes do slide de propaganda → `limpos\` →
  `D:\manhwa-react\mr\rede.py` posta como 3ª fonte só em `canais_veo_limpo` (inventoreact, manhwareact), 1 por
  canal por dia, com título do agente do canal, rebrand do @ e aprovação. Primeiro agendado: 15/10 às 23:00.
- Política (`D:\postador-de-videos\config\politica.json`): **10 uploads por canal por dia, 50 por dia no total,
  intervalo 0 h**, aprovação humana ligada, parada geral se houver suspensão. (A rede do manhwa-react aplica os
  próprios limites, mais rígidos: 1 por canal por dia, janela de 3 h, sem rajada.)

### 3.4 Estado em 15/10

- Geração **pausada** desde 12/10 17:46 (`beta\logs\PAUSE_SYSTEM`, motivo "manual"); o loop segue rodando e abortando
  a cada 30 s ("sistema pausado, abortando").
- Tarefa do Windows `VeoProducaoDiaria7h` desabilitada desde 31/08; `CronVeo*` desabilitadas.
- `beta\` tem **~2.200 linhas sem commit** desde 31/07 (`flow_bot.py` +1079, `gera_auto.py` +1066,
  `cron_gerar_video_llm.py` +160, `montar_final.py` +163, `cta_card.py` +91, `omniroute_image.py` +86, `creditos.py`,
  `contas.py`, `llm_client.py`, `cta_builder.py`). O que está no ar não está no git.
- `logs\video_cache.json` só tem 2 vídeos (12/10); o laço de métricas (views → fórmula) não tem dados.
- Pool VO3 local: só 3 demos (`avatar_demo`, `hermes_demo`, `superchat_demo`); em `propagandas_vo3\vo3` e
  `vo3_lateral` há 8 arquivos de 01/08.
- Em 12/10 várias contas deram "créditos esgotados" (`logs\creditos_esgotados_20261012_*`).

## 4. O banimento (04/09/2026) e o que já mudou

Fonte: `D:\postador-de-videos\SPAM_BANIMENTO_2026-09-04.md`, `CONTESTACAO_YOUTUBE_2026-09-22.md`, `LEIA.txt`,
`D:\manhwa-react\REDE_ESTADO_E_PENDENCIAS.md` §5. 22 canais brasileiros suspensos de uma vez por "violações graves ou
repetidas da política contra spam, práticas enganosas e golpes". Os 8 canais internacionais (menos volume) ficaram.

| Comportamento | Status hoje (apurado) |
|---|---|
| Postagem 100% automática em rajada (06:40) até bater `uploadLimitExceeded`; centenas por dia; round-robin em 20+ canais | Parcial: a rede do manhwa-react posta 1/canal/dia agendado e sem rajada; mas `politica.json` ainda permite 10/canal, 50/dia e intervalo 0, e `postar_tudo_hoje.py`/`agendar_vo3.py` continuam agendados (hoje sem canal livre) |
| Mesmo projeto OAuth/clientId em todos os canais; vários canais por conta Google | Parcial: hipercool e manhwa migraram para postagem pelo navegador (cofre); `youtube_poster.py` (Data API) ainda é usado pela rede |
| Shorts de IA muito parecidos; títulos/descrições por template | Parcial: a rede tem agente por canal + revisor; mas `publicar.py` (fallback "#shorts #ia #viral #brasil") e `postar_tudo_hoje.rota_vo3` ("título com #shorts") seguem iguais |
| Gerador de likes/comentários falsos (MEGA ENGAGE) rodado em 06/08 | Desligado; decisão firme de nunca religar |
| Mesmo vídeo em vários canais | Corrigido na rede ("nunca o mesmo vídeo em 2 canais"); recaps do hipercool repetiram o padrão em 13/10 e deram 0 views |
| **Slide de propaganda com WhatsApp + cartão "Siga @InovareStories" em todo vídeo** | Corrigido só na versão LIMPA (`limpar_veo.py`); o `montar_final`/`cta_card` continuam produzindo o COMPLETO com o número fixo, e o TikTok/Instagram ainda reaproveitam o COMPLETO (`reuso_plataformas.json` `veo_so_limpo: false`, decisão da dona pendente) |
| Declaração de conteúdo sintético/alterado | **A conferir** (o que `youtube_poster.py`/`youtube_web_poster.py` enviam) |
| `roteamento.py` aponta para handles de canais suspensos (fakenewsia, fofoseabsurdos, recenasia…) e usa `hash()` não determinístico | Continua (código morto perigoso se o caminho antigo voltar) |

## 5. Achados já confirmados no código (com onde)

- `pos_producao\cta_card.py` `gerar_card`: `whatsapp = "91 98469-8653"` fixo; badge verde de WhatsApp em todo card.
- `pos_producao\plugins\branding_watermark.py`: `_DEFAULT` com `@InovareStories` e "Siga pra mais historias IA".
- `pos_producao\worker_noite.py` `_escolher_metadados`: canal/tema/**fala** deduzidos do nome do arquivo com frases
  FIXAS por slug (ex.: "ETs roubam nosso wifi…") — a fala usada na legenda/metadados pode não ser a do vídeo.
- `publicar.py`: título com "1-2 emojis", descrição com "5 hashtags" e CTA "👉 …" na descrição; fallback com
  "#shorts #ia #viral #brasil".
- `roteamento.py`: `_DIRETO`/`_POOL_HUMOR` com handles suspensos; `hash()` por processo.
- `postar_tudo_hoje.py` `rota_vo3`: pede ao Gemini "título viral… com #shorts"; round-robin.
- `config\politica.json`: 10/canal/dia, 50/dia, intervalo 0.
- `comercial_agents.py`: fala ≤ 18 palavras, pessoa olhando pra câmera, sem número na fala (bom); crítico aceita ≥ 8;
  modelo `gemini-flash-lite-latest`.
- `vo3_propaganda_rotator.montar_prompt`: reforça 9:16/8 s; fallback com "product name appears as on-screen text"
  (o Veo erra texto na tela).
- `montar_final.montar`: ordem criativo → [b-roll] → [VO3] → transição → card; md5 para sorteio (bom); card e clipe
  do mesmo produto (bom); sidecar de rastreabilidade (bom).
- `README.md` da beta cita o venv do hipercool; o `.bat` do painel usa `D:\veo\venv`.
- `D:\veo\experimental` é cópia desatualizada dos mesmos arquivos (drift).

## 6. O que os outros projetos têm para o veo (a confirmar função por função)

- manhwa-react: `mr\rede.py` (estratégias por braço com aprendizado de 48 h, agente por canal, revisor, rebrand do @,
  horário que aprende, trava anti-rajada, `canais_veo_limpo`), `mr\memoria.py` (dedupe por hash de quadros e
  trigramas), `mr\validate.py`, `mr\captions.py` (ASS palavra a palavra), `mr\hyperframes.py` (texto animado),
  `mr\triggers.py` (SFX por palavra), `mr\music.py` (trilha por mood; blocklist com bug), `mr\groq_api.py`,
  `scripts\backup_drive.py`, `mr\sem_janela.py`.
- hipercool: `bin\seo.py` (palavras buscadas do autocompletar + 3 estilos com Thompson + `_sem_obra`),
  `bin\capa_ia.py` (rodízio/A-B/Thompson; as poses de manhwa não se aplicam), `bin\metricas.py` (lê o Studio pelo
  navegador), `bin\elenco.py`/`bin\edge_tts_engine.py` (vozes aprovadas; proibidas pt-BR-AntonioNeural,
  pt-BR-FranciscaNeural, it-IT-IsabellaNeural), `bin\groq_api.py` (proxy Webshare), `bin\fx_acabamento._clipe_parado`
  (ffmpeg 8 trava com vários `-loop 1`), `bin\fx_music.py`, `bin\sem_janela.py`,
  `D:\postador-de-videos\bin\youtube_studio_extras.py`.

## 7. Hipóteses de melhoria (a verificar pelos agentes; não são conclusões)

- Antibanimento: tirar o slide com número de WhatsApp do corte que vai ao YouTube (CTA só na descrição/comentário,
  com link); apertar `politica.json` (3/canal, 20/dia, ≥ 2 h); aposentar `postar_tudo_hoje`/`agendar_vo3`/
  `roteamento.py` e fazer da rede o único caminho; declarar conteúdo sintético quando a pessoa gerada é realista;
  dedupe por hash antes de postar; nunca o mesmo vídeo em 2 canais; warm-up dos canais; metadados únicos sem template.
- Vídeo atrativo: conferir o idioma da fala por Whisper (ffprobe não ouve); legendas ASS; loudness; trilha com
  ducking; "no subtitles" no prompt; usar recursos do Veo 3.1 (referência de personagem, extend); thumbs A/B com
  Thompson; fechar o laço de métricas pelo aprendizado global de 48 h.
- Comercial Veo 3: imagem de referência do produto; pool ≥ 3 por produto; rotação; não em todo vídeo; conferência de
  fala; UTM por canal/produto para medir conversão.
- Card de imagens: versão sem número (end-card de 2-3 s "link na descrição"), animado (HyperFrames/parallax), voz
  aprovada fixa por produto, `_clipe_parado` em vez de `-loop 1`, duração proporcional.
- Base: commitar a beta; criar `D:\veo\CLAUDE.md`; promover para `prod`; `sem_janela`; documentar como retomar a
  geração (PAUSE_SYSTEM) e as tarefas desabilitadas.

## 8. Decisões que provavelmente só a dona pode tomar

1. O COMPLETO (com WhatsApp) continua indo para TikTok/Instagram? (`reuso_plataformas.json` `veo_so_limpo`)
2. O veo volta a postar no YouTube só pela rede (inventoreact, manhwareact) ou ganha mais canais?
3. O comercial VO3 entra em todo vídeo, em 1 a cada N, ou só em alguns canais?
4. Religar a geração (PAUSE_SYSTEM manual desde 12/10) e com quantas contas por dia?
5. Commitar e versionar a beta (o código no ar não está no git).

## 9. Próximo passo

Rodar a auditoria com subagentes (workflow `auditoria-veo-melhorias`, run `wf_e5a163ab-740`): 8 leitores, 6 frentes de
propostas, verificação adversarial em 3 lentes, crítico de completude e redação do plano em
`D:\veo\docs\PLANO_MELHORIAS_VEO.md`. A primeira tentativa (15/10 ~21:15) falhou inteira por limite de uso da
sessão; nenhum agente rodou.
