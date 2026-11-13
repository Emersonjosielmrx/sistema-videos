# Plano de melhorias do Veo (auditoria de 15–16/10/2026)

> O que é: tudo o que dá para melhorar no projeto `D:\veo` (gerador de Shorts no Google Flow/Veo 3.1 + comercial dos
> produtos), trazendo o que o manhwa-react e o hipercool já têm pronto, e o que precisa mudar para o YouTube não
> classificar de novo como spam. Como foi feito: leitura do código e dos documentos dos 4 projetos (4 leitores com
> agentes, mais leitura direta), dados reais (contagens, logs, quadros extraídos dos vídeos), políticas atuais do YouTube
> e do Veo, e uma verificação adversarial das propostas (ver "Registro" no fim).
> **Regra de ouro: nada do veo volta a ser postado no YouTube, e a geração não é religada, antes de cumprir a Onda 0.**

Leia junto: `CLAUDE.md` (raiz do veo) e `docs\LEVANTAMENTO_2026-10-15.md`.

---

## 0. Resumo em 12 linhas

1. O veo produz 3 peças: o clipe criativo de 8 s com a foto da dona (Veo 3.1 Fast), um clipe de comercial do produto
   também no Veo (VO3) e um card de imagem com voz e **número de WhatsApp fixo**. O COMPLETO junta as três (15–28 s).
2. O banimento de 04/09/2026 (22 canais) veio do **comportamento**, não dos produtos: rajada automática até o limite
   diário, round-robin em 20+ canais, mesmo projeto OAuth, títulos por template, likes falsos em 06/08, mesmo vídeo em
   vários canais e o slide de WhatsApp + "Siga @InovareStories" em todo vídeo.
3. A rede do manhwa-react já corrige quase tudo isso para o que passa por ela (1 vídeo por canal por dia, agendado,
   sem rajada, agente por canal, revisor, declaração de IA). O Veo LIMPO já entra por ela: 218 aprovados, **1 postado**.
4. Mas o caminho antigo continua armado: tarefas `PostadorDeVideos` 06:40 e `AgendadorVO3` 05:00 ativas, round-robin,
   sem declaração de IA, roteando para 20 canais suspensos; só não postam porque todos os canais estão reservados à rede.
5. A política global foi afrouxada em 14/10 para 10 uploads por canal por dia, 50 por dia e intervalo 0 h; em 15/10 um
   canal recebeu 8 uploads em 42 min. É o padrão do banimento, agora permitido pela config.
6. TikTok e Instagram ainda reaproveitam o COMPLETO com o número de WhatsApp (9 posts em 15/10), com legenda aleatória
   "#fyp #viral".
7. A geração está pausada desde 12/10; ~2.200 linhas do que roda não estão no git; o laço de métricas nunca fechou
   (0 views em qualquer cache da história do projeto); ninguém confere se o Veo falou em português.
8. O card de imagem (peça 3) precisa ser refeito sem telefone e mais curto; o comercial VO3 (peça 2) precisa de pool
   real (o pool local tem 3 demos de 3 s sem áudio), prompt sem texto na tela e frequência controlada.
9. O que mais vale trazer do manhwa-react: a rede como único caminho, dedupe por quadros e por texto, revisor de
   metadados, legendas palavra a palavra, validação final, trava e `sem_janela`. Do hipercool: SEO com palavras buscadas
   e Thompson, vozes aprovadas, `_clipe_parado` (ffmpeg 8), áudio nivelado, extras e métricas do Studio pelo navegador.
10. Ordem: Onda 0 desarma o caminho antigo, trava a política e tira o WhatsApp do corte do YouTube; Onda 1 põe controle de
    qualidade e o veo pelo diretor da rede; Ondas 2–3 melhoram as três peças e fecham o aprendizado.
11. 14 decisões só a dona pode tomar (seção 6); as principais: COMPLETO fora do TikTok/Instagram, limites da política,
    quais canais recebem o veo, comercial em todo vídeo ou 1 em N, e commitar a beta.
12. Enquanto não houver 10 medições de "veo limpo" em 48 h, fica 1 veo por dia na rede. Escalar só com dado.

---

## 1. O veo hoje

Fluxo (detalhe em `docs\LEVANTAMENTO_2026-10-15.md` §3): `run_cron_loop_3contas.bat` → `cron_gerar_video_llm.run()` a
cada 30 s → escolhe conta (`contas.py`: 13 contas, 12 pro + 1 free) → prompt por agentes (`agents.py`: Trend Scout →
Hook → Scenario → Critic, via gateway `antigravity/gemini-3.1-pro-high`, fallback chaves Gemini) → foto da dona
(`D:\veo\fotos`, 305 soltas) → `gera_auto.py` (Chrome real por CDP, Flow, Veo 3.1 Fast, 9:16, 8 s) → mp4 em
`beta\videos\cron_shorts` → thumbs A/B/C + `video_cache.json` + `postar.json` → pós-produção incremental (`pos_video`
ligado) com o pipeline antigo (`pos_producao\config.yaml`: loudnorm, crop, legendas, **propaganda_inteligente,
branding_watermark**). À parte, `worker_noite.py` gera as variantes `_LIMPO` e `_COMPLETO` com `montar_final.montar()`.

| Peça | Como é feita hoje | Arquivo | O que o espectador vê (quadros conferidos em 15–16/10) |
|---|---|---|---|
| 1. Vídeo atrativo | Veo 3.1 Fast, 8 s, image-to-video com a foto da dona, fala pt-BR pedida no prompt; sem conferência de idioma/rosto; legenda distribui o texto do prompt pela duração (não ouve o áudio) | `cron_gerar_video_llm.py`, `agents.py`, `gera_auto.py`, `plugins\legendas.py` | Pessoa realista falando para a câmera, estética "neon/cyberpunk" em todas as personas, legenda queimada ("Seu dinheiro derrete porque você"), marca "@InovareStories" no canto |
| 2. Comercial Veo 3 (VO3) | Prompt do multi-agente `comercial_agents.py` (pessoa olhando para a câmera, fala ≤ 18 palavras), gerado 1x por produto e sorteado do pool | `vo3_propaganda_rotator.py`, `comercial_agents.py` | 8 s: apresentador genérico de terno sorrindo; tela de celular com "WhatsApp" e texto ilegível; personagem 3D com "Avatar IA" no celular |
| 3. Comercial de imagens (card) | PNG 1080x1920 com fundo IA, "OFERECIDO POR", nome do produto, copy, **badge com "WhatsApp 91 98469-8653"**, URL; voz ElevenLabs (fallback edge com voz proibida); slide de 5–6 s; outro "Siga @InovareStories" | `cta_card.py`, `cta_builder.py`, `omniroute_image.py`, `plugins\branding_watermark.py` | Slide parado com o número do WhatsApp em destaque; depois tela preta "Siga @InovareStories" |

Estado em 16/10/2026:
- Geração **pausada** desde 12/10 17:46 (`beta\logs\PAUSE_SYSTEM`, "manual", sem prazo); o loop seguiu abortando a cada
  30 s e o log **parou de crescer em 15/10 16:58** — o processo foi encerrado, não há nada rodando agora. Tarefa
  `VeoProducaoDiaria7h` desabilitada (última execução 31/08); `CronVeo*` desabilitadas.
- Caminho antigo de postagem **ativo**: `PostadorDeVideos` 06:40 e `AgendadorVO3` 05:00 (Ready, rodaram em 15/10).
- Caminho novo: `limpar_veo.py` → `D:\hipercool-materiais\veo\limpos` (226 jsons, 225 mp4; na política: 218 aprovados,
  5 rejeitados, 3 ainda sem entrada) → rede (`mr\rede.py`) só em inventoreact e manhwareact; **1 postado** (15/10 20:00
  BRT, InventoReact, nota 6,0). Em 16/10 05:20 a fila da rede já tinha 227 vídeos aprovados e 8 canais "sem vídeo bom".
- Estoque: 226 brutos no PC (+487 no Drive), 225 limpos, 4 em `beta\videos\cron_shorts`, 231 em
  `videos_pos\cron_shorts`, 21 COMPLETO em `pos_final\completo`, 730 finais antigos já postados nos canais encerrados.
- **Os 231 de `videos_pos\cron_shorts` não têm nenhum sidecar `.json`**: vieram do pipeline antigo (`runner.py` +
  `config.yaml`), não do `worker_noite.py` (que grava sidecar em `_gravar_sidecar`). Ou seja, o caminho "2 variantes
  LIMPO/COMPLETO" quase não rodou, e não há rastro de produto/voz/efeito por vídeo.
- Git: `beta` com 3 commits (último 31/07 00:04), +2.218/−563 linhas sem commit em 11 arquivos **e dezenas de arquivos
  novos não rastreados** (inclusive `LEIA_PERFIS_E_COFRE.md` e ~15 scripts de `pos_producao\`).
- Métricas: `video_cache.json` da beta com 2 vídeos (0 views); a cópia experimental tem 130 fórmulas de julho, também
  sem nenhuma view. Nenhuma medida de "veo limpo" ainda no `aprendizado_global.json`.

---

## 2. Por que o YouTube baniu e o que já mudou

Fontes: `D:\postador-de-videos\SPAM_BANIMENTO_2026-09-04.md`, `CONTESTACAO_YOUTUBE_2026-09-22.md`, `LEIA.txt`,
`D:\manhwa-react\REDE_ESTADO_E_PENDENCIAS.md` §5, logs do postador. Política oficial: spam, práticas enganosas e golpes
(`support.google.com/youtube/answer/2801973`: conteúdo "excessively posted, repetitive, or untargeted", o mesmo
conteúdo em vários canais, conteúdo autogerado sem cuidado, redirecionar para fora do YouTube em descrição, comentário
fixado, fala ou texto na tela), engajamento falso (`answer/3399767`), encerramento e contorno (`answer/2802168`: canais
do mesmo dono e repostagem de conteúdo de canal encerrado) e conteúdo inautêntico/produzido em massa (monetização,
`answer/1311392`, renomeado em 15/07/2025).

| Comportamento | Evidência | Status em 16/10 | Fecha com |
|---|---|---|---|
| Rajada automática até `uploadLimitExceeded`, centenas por dia | `logs\postar_tudo_20260730.log` (102 OK + 31 LIMITE), `postar_pos_final_20260824.log` (105 OK) | **Parcial**: a rede posta 1/canal/dia agendado; `politica.json` permite 10/canal, 50/dia, intervalo 0 (mtime 14/10 11:55); em 15/10 o InovareManhwaVerse recebeu **10 uploads no dia, 8 deles em 42 min** (05:27–06:09); em 14/10 o hindi recebeu 5 em 12 min | AB-01, AB-02, AB-10 |
| Round-robin em 20+ canais, em hora fixa | `postar_tudo_hoje.py:334-402`, `agendar_vo3.py:53-81,253-266`; tarefas Ready | **Dormente**: sem canal livre (todos reservados à rede), código e tarefas intactos | AB-01 |
| Mesmo projeto OAuth/clientId em todos os canais | `SPAM_BANIMENTO…:128-131`; `HANDOFF_REDE.md:86-88` (projeto 100689820764) | **Parcial**: parte sobe pelo navegador (o 1º veo limpo subiu por `youtube_web_poster.py`); parte pela Data API | AB-07 |
| Títulos/descrições por template, CTA de WhatsApp na descrição | `publicar.py:55,70-71,87-89`; `postar_tudo_hoje.py:58,160-172`; `agendar_vo3.py:166-182` | **Parcial**: a rede tem agente + revisor; os scripts do veo continuam iguais | AB-06, DS-02 |
| Slide com WhatsApp + "Siga @InovareStories" em todo vídeo | `cta_card.py:155`; `plugins\branding_watermark.py:24-26`; `config.yaml:16-21`; quadros do COMPLETO | **Parcial**: o LIMPO tira; a pós incremental ainda gera COMPLETO com número; TikTok/Instagram ainda postam COMPLETO | AB-03, AB-04, IM-01 |
| Likes/comentários falsos (MEGA ENGAGE, 06/08) | `HANDOFF_REDE.md:215-222`; tarefa `MegaEngageMonitor` Disabled | **Corrigido** (nunca religar) | regra de ouro |
| Mesmo vídeo em vários canais | `mr\rede.py:11-12,269-276`; `LEIA.txt:131-136` | **Corrigido na rede**; o hipercool repetiu em 13/10 (0–5 views); o veo não tem dedupe próprio | AB-08 |
| Shorts de IA muito parecidos | `llm_client.py:424`, `agents.py:417` ("neon vibrant"); mesma foto e estrutura em 25 personas | **Continua** | AT-05, AT-04, AT-06 |
| Sem declaração de conteúdo sintético | scripts antigos não passam `--sintetico` (`postar_tudo_hoje.py:224-226`, `postar_pos_final.py:273-275`, `agendar_vo3.py:278-280`) | **Parcial**: a rede declara (`mr\rede.py:183,926`) | AB-05 |
| Roteamento para canais mortos, sorteio por `hash()` | `roteamento.py:15-35,60`; só animescomia vivo | **Continua** (código morto perigoso) | AB-06, BX-06 |
| Reupload de material de canal encerrado | 730 finais do `pos_final` já postados nos canais suspensos (catálogo); parte dos brutos de 8 s veio do TikTok | **Parcial**: catálogo marca a pasta como SUSPENSOS; detector só pega a logo do TikTok | AB-08, AB-09 |

Risco vizinho (não é do veo, mas derruba a rede inteira pela parada geral `parar_tudo_ao_detectar_suspensao`): o
hipercool subiu 8 partes em 42 min no canal pt em 15/10 e a mesma parte em 7–8 canais em 13/10; o canal pt já teve
"recursos avançados negados" até 14/11/2026. Ver decisão 13.

---

## 3. Regras de ouro antibanimento do veo (checklist antes de qualquer postagem)

1. Vídeo do veo só sobe pela rede do manhwa-react (`manhwareact.py rede`), nunca por `postar_tudo_hoje.py`,
   `postar_pos_final.py`, `agendar_vo3.py` ou `roteamento.py`.
2. Só a versão LIMPA vai ao YouTube: sem número de telefone, sem slide de produto, sem cartão "Siga @…", sem marca de
   outro canal. COMPLETO nunca como limpo. Nunca repostar os 730 do `pos_final`.
3. 1 vídeo por canal por dia, agendado (`private` + `publishAt`), só nas próximas 3 h, com jitter; nunca o mesmo vídeo
   em 2 canais; nunca 2 uploads do mesmo canal com menos de 2 h.
4. Título, descrição e tags escritos pelo agente do canal e aprovados pelo revisor; sem "#shorts #ia #viral" por
   template, sem emoji em série, sem telefone, sem URL, sem "clique no link", sem promessa de ganho.
5. Declarar "conteúdo alterado ou sintético" em todo upload do veo (`--sintetico`): a pessoa que fala é gerada.
6. Antes de aprovar: quadros vistos (início, meio, fim), áudio em português conferido, sem texto ilegível, sem logo
   de terceiro, duração 7,5–8,5 s no clipe cru.
7. Comercial do produto: no máximo 1 em N vídeos por canal (decisão 4), nunca em 2 dias seguidos no mesmo canal, nunca
   número ou URL falado ou na tela.
8. Nada de engajamento comprado ou automatizado (MEGA ENGAGE desligado para sempre).
9. Google/YouTube só pelo navegador; nunca criar chave de API; o autocompletar público pode.
10. Política do postador com piso: ≤ 4 por canal por dia, ≤ 20 por dia, ≥ 1 h de intervalo, parada geral ligada.
11. Canal recuperado ou novo: 1 vídeo por dia nas primeiras 2 semanas, horário de pico do público, sem comercial.
12. Medir 48 h antes de escalar; se dois canais derem erro de upload no mesmo dia, parar tudo e avisar no Telegram.

---

## 4. Melhorias por frente

Legenda: **Impacto** 1–5 (5 = evita banimento ou muda muito o resultado); **Esforço** P (horas) / M (1–2 dias) /
G (mais); **Risco** de quebrar o que funciona. "De onde copiar" aponta código já pronto nos outros projetos.

### 4.1 Antibanimento (AB)

#### AB-01 — Desarmar o caminho antigo de postagem do veo
- **Problema:** `bin\postar_tudo_auto.bat:16-24` ainda chama `postar_tudo_hoje.py` (round-robin entre canais ativos,
  `privacy public`, título por Gemini "com #shorts": `postar_tudo_hoje.py:5,160-172,178`) e `postar_pos_final.py`
  (`_candidatos(giro)`, `:297-310`); a tarefa `AgendadorVO3` (05:00) roda `agendar_vo3.py` (tetos de 8 a 45 por canal,
  5 slots, varredura final com postagem imediata: `:53-81,253-266`; o que sobra no fim do dia sai **público na hora**,
  `publish_at = None` → `privacy = "public"` em `:262-263,277`). Nenhum dos dois passa `--sintetico`
  (`postar_tudo_hoje.py:224-226`, `agendar_vo3.py:278-280` chamam `politica.postar_youtube` sem o parâmetro, que vale
  `False` por padrão). Hoje só não postam porque `politica._reservas` (`politica.py:175-201`) reserva todos os canais
  vivos à rede. **Dois agravantes achados na verificação:** (a) `_resolver_video_vo3` (`postar_tudo_hoje.py:90-104`)
  procura o mp4 em 5 lugares, entre eles `videos_pos\cron_shorts` e `pos_final` — ou seja, pode pegar justamente a
  versão COM o slide de WhatsApp; (b) os dois freios globais (`config\PARADO.json` e `config\POSTAGEM_DESLIGADA.json`)
  **não existem no disco hoje**: nada está segurando esse caminho além da reserva de canais.
- **O que fazer:** tirar as etapas 1 e 2 do `.bat` (ou protegê-las com `if exist config\VEO_ANTIGO_LIGADO.json`),
  desabilitar a tarefa `AgendadorVO3`, mover os três scripts para `bin\_legado\`. Antes, conferir se alguma fonte que
  não é veo (recaps de anime, "materiais": `coletar_materiais` em `postar_tudo_hoje.py`) ainda depende deles e migrar
  essa fonte para a rede ou para o hipercool.
- **De onde copiar:** nada; é remoção. A rede já faz o papel (`mr\rede.py:846-979`).
- **Impacto/Esforço/Risco:** 5 / P / baixo.
- **Como validar:** `schtasks /query /tn AgendadorVO3` desabilitada; log do ciclo 06:40 sem "Inicio postar_tudo_hoje";
  `python bin\politica.py` mostra 0 uploads fora da rede por 7 dias.

#### AB-02 — Piso de segurança na política, no código
- **Problema:** `config\politica.json` está em 10 uploads por canal por dia, 50 por dia e intervalo 0 h desde 14/10
  11:55; o padrão do próprio código é 3/12/2 h (`politica.py:48-54`, dict `PADRAO`, aplicado em `politica()` `:89-91`
  com `cfg = dict(PADRAO)` + `cfg.update(json)`), e o `LEIA.txt:172-175` ainda anuncia 3/12/2 h. O hipercool zerou o
  intervalo porque o agendamento pelo Studio só funciona em pt/en (`D:\hipercool-videos\docs\correcoes_pendentes.md:32`).
  Resultado medido no ledger: InovareManhwaVerse com 10 uploads em 15/10, sendo 8 entre 05:27 e 06:09.
- **O que fazer:** em `politica.politica()` (`politica.py:89-92`) aplicar um piso que o json não consegue afrouxar
  (≤ 4 por canal por dia, ≥ 1 h entre uploads do mesmo canal, ≤ 20 por dia) e permitir limites **por projeto** (bloco
  `hipercool` / `veo` / `manhwa-react`) em vez de um global; logar no Telegram quando o json pedir acima do piso.
- **De onde copiar:** `D:\hipercool-videos\bin\fila.py:461-484` (`_pode_postar`: pico, intervalo 2 h, max 3/dia) como
  modelo de limites por canal.
- **Impacto/Esforço/Risco:** 5 / P / baixo (o hipercool precisa de exceção para o intervalo em canais de língua: decisão 2).
- **Como validar:** `python bin\politica.py` imprime o piso em vigor; teste com json em 10/50/0 → upload nº 5 do dia
  no mesmo canal é recusado.

#### AB-03 — Nenhum vídeo novo do veo nasce com WhatsApp ou marca
- **Problema:** depois de cada vídeo gerado, o cron roda a pós incremental (`cron_gerar_video_llm.py:1587-1599`,
  `pos_producao\flags\pos_video.flag = on`) com o pipeline de `config.yaml:16-21`, que inclui `plugins.propaganda_inteligente`
  e `plugins.branding_watermark` (`@InovareStories`, "Siga pra mais historias IA": `branding_watermark.py:24-26`,
  `assets\branding.json`). O `worker_noite.py` gera a variante `_COMPLETO` com o card de WhatsApp (`montar_final.py:108-150`,
  `cta_card.py:155`). Log de 12/10 17:12:53: "[pos] rodando pipeline no video recem-gerado".
  **Atenção:** `@InovareStories` não está só na config — está **escrito no código** dentro de `_gerar_outro_mp4`
  (`branding_watermark.py:100,104`), então trocar `branding.json` não resolve sozinho.
- **O que fazer:** no `config.yaml` deixar só `loudnorm`, `crop_9_16` e as legendas novas (AT-09); desligar
  `propaganda_inteligente` e `branding_watermark`; `_COMPLETO` só sob demanda, nunca para o YouTube, e já com o card
  novo (IM-01). O vídeo novo sai **sem marca**: o rebrand da rede grava o @ do canal de destino na hora de postar
  (`mr\rede.py:281-316`).
- **De onde copiar:** `D:\postador-de-videos\bin\limpar_veo.py` (regra "COMPLETO nunca como limpo").
- **Impacto/Esforço/Risco:** 5 / P / baixo.
- **Como validar:** gerar 1 vídeo de teste e extrair quadros (início/meio/fim): sem número, sem "@", sem cartão.

#### AB-04 — TikTok e Instagram só com a versão limpa e legenda pela fala
- **Problema:** `config\reuso_plataformas.json` tem `veo_so_limpo: false` nas duas redes ("desligado até o dono
  decidir"); `catalogo.py:234-261` só troca pela versão limpa com a flag ligada; em 15/10 saíram 9 COMPLETO no TikTok e
  em 14/10 2 no Instagram (`logs\tiktok_auto_posted.json`, `logs\instagram_auto_posted.json`). Legenda do TikTok é
  `random.choice` de 8 frases com "#viral #fyp" (`tiktok_cdp_poster.py:21-30,318`); Instagram `"{tema} 🤯 #ia … #viral"`
  (`postar_insta_auto.py:44-46`).
- **O que fazer:** com o OK da dona, `veo_so_limpo: true` nas duas redes; legenda gerada do campo `fala`/`tema` do json
  do limpo (ou do título do `publicados.json`), sem #fyp/#viral e com a frase de IA; limites atuais (3 e 2 por conta
  por dia) mantidos.
- **De onde copiar:** `D:\manhwa-react\mr\rede.py:487-523` (`adaptar`, agente de metadados) para a legenda.
- **Impacto/Esforço/Risco:** 4 / P (flag) + M (legenda) / baixo. **Decisão 1.**
- **Como validar:** `python bin\catalogo.py disponiveis tiktok` lista só `limpos\…`; 3 posts seguidos com legendas diferentes.

#### AB-05 — Declarar conteúdo sintético em todo caminho e tratar falha como falha
- **Problema:** o postador sabe declarar (API `status.containsSyntheticMedia`: `youtube_poster.py:151-152`; Studio
  `VIDEO_HAS_ALTERED_CONTENT_YES`: `youtube_web_poster.py:584-585`), mas só se o chamador pedir. A rede pede para veo e
  histórias (`mr\rede.py:183,926`); os scripts antigos nunca pediram; no navegador, opção não marcada vira só "aviso"
  (`youtube_web_poster.py:387-388`). O YouTube exige a divulgação para conteúdo realista gerado, inclusive voz e pessoa
  (`support.google.com/youtube/answer/14328491`); em Shorts o rótulo aparece como sobreposição. Repare que essa é a
  **única** conferência do poster que não interrompe nada: título, descrição e "não é para crianças" levantam `Falha`
  nas linhas vizinhas (`:380,384,386`); a da IA só escreve um aviso no log.
- **O que fazer:** em `youtube_web_poster.py`, quando `sintetico=True` e a opção não ficou marcada → falhar o upload
  (não publicar); nos scripts que sobrarem do veo, `sintetico=True` sempre; no `postar.json` do veo gravar
  `"sintetico": true`.
- **De onde copiar:** `D:\hipercool-videos\bin\postar_hipercool.py:352-353` (passa `True`).
- **Impacto/Esforço/Risco:** 4 / P / baixo.
- **Como validar:** no Studio, o vídeo de teste mostra o rótulo "conteúdo alterado ou sintético"; log do poster sem "aviso: a opção…".

#### AB-06 — Limpar `roteamento.py` e `publicar.py`
- **Problema:** `roteamento.py:15-35` aponta **19 handles únicos** (11 em `_DIRETO` + 10 no pool, 2 repetidos);
  **18 estão na lista de suspensos** e só `animescomia` está vivo — e esse está reservado à rede. `:60` usa `hash()`
  (muda a cada processo) e `:58` tem `if p in _GENERICAS or True:`, que torna o `return []` de `:62` inalcançável; o
  `postar.json` de 12/10 roteou para `gameoftroneskingsroadbrasil` (suspenso). `publicar.py:54-57` pede "1-2 emojis" e "5 hashtags"; `:70-71` anexa
  "👉 {cta}" (o CTA é o mesmo para todos os vídeos do dia: `inteligencia.py:231-242`); `:87-89` fallback
  "#shorts #ia #viral #brasil"; `:139` grava um único `postar.json` por pasta, sobrescrito a cada vídeo e antes de validar.
- **O que fazer:** apagar `_DIRETO`/`_POOL_HUMOR`; não preencher `canais` (o diretor da rede decide) ou ler os ativos
  de `rede_canais.json` com `hashlib.md5`; tirar emoji/hashtag/CTA do prompt e do fallback; gravar `<stem>.postar.json`
  no formato que `limpar_veo`/rede leem (`fala`, `tema`, `sintetico`), só depois da validação (AT-02).
- **De onde copiar:** `D:\manhwa-react\mr\rede.py:431-456` (AGENTE_INSTR, PROIBIDO_*), `:526-550` (`_validar_meta`).
- **Impacto/Esforço/Risco:** 4 / P / baixo.
- **Como validar:** `python roteamento.py` só devolve slugs presentes em `rede_canais.json` com status ativo; 2
  execuções seguidas dão o mesmo resultado.

#### AB-07 — Tirar a Data API e o projeto OAuth compartilhado do caminho
- **Problema:** o relatório do banimento aponta o mesmo `clientId` em todos os canais; hoje quase todos os canais novos
  usam o projeto 100689820764 (`HANDOFF_REDE.md:86-88`). Parte dos canais ativos ainda sobe pela Data API
  (`politica.py:454-455` só usa `youtube_web_poster.py` para canal marcado em `youtube_navegador.json`; os dois
  leitores divergiram sobre quais canais estão marcados: conferir arquivo a arquivo). A rede também priva, edita
  metadados e comenta pela API (`mr\rede.py:585-624`, `mr\publish.py:118-134`). Regra da dona: só navegador.
- **O que fazer:** logar os perfis dos canais que faltam (`youtube_web_poster.py --logar <slug>`), marcar `usar: true`,
  e mover comentário/privar/editar para `youtube_studio_extras.py`; Data API só para leitura (views), enquanto a dona
  aceitar.
- **De onde copiar:** `D:\postador-de-videos\bin\youtube_studio_extras.py` (`comentar_fixar`, `editar_metadados`).
- **Impacto/Esforço/Risco:** 4 / M / médio (cada perfil precisa de login manual). **Decisão 8.**
- **Como validar:** ledger mostra `script: youtube_web_poster.py` em 100% dos uploads da rede por 7 dias.

#### AB-08 — Dedupe de vídeo e de fala antes de postar (e contra os 730 antigos)
- **Problema:** o veo não compara vídeos entre si (nem quadros nem texto); só satura por tema (≥ 5 em 24 h,
  `cron_gerar_video_llm.py:404-411`). O mesmo produto/persona repete frases ("O oceano esconde…"); os 730 finais
  antigos já saíram em canais encerrados (repostar = contorno, `answer/2802168`).
- **O que fazer:** no inventário da fonte `veo` da rede (`mr\rede.py:165-188`) e ao entrar um limpo novo, descartar
  (`revisar: "duplicado"`) quem tiver trigramas ≥ 30% iguais a vídeo postado nos últimos 30 dias ou dHash de quadros
  parecido (limiar 0,35) com qualquer já publicado ou com os 730 do `pos_final`; índice inicial (730 + 296) uma vez
  (~1 h de CPU). Filtrar 1º e último segundo (cartões).
- **De onde copiar:** `D:\manhwa-react\mr\memoria.py:35-43` (impressão), `:46-112` (`hashes_quadros`, `_parecido`,
  `repetido`), `:132-158` (`repetido_texto`).
- **Impacto/Esforço/Risco:** 4 / M / baixo.
- **Como validar:** copiar um limpo com outro nome → não entra na fila; 2 vídeos da mesma persona com a mesma frase →
  o 2º é marcado.

#### AB-09 — Aprovação com olhos para o que não é formato padrão
- **Problema:** `limpar_veo.py:199-214` aprova sozinho os de formato conhecido; o detector só cobre a logo padrão do
  TikTok (`MARCA_TIKTOK`, limiar 0,57); parte dos brutos de 8 s veio do TikTok (6 pegos) e a origem dos demais não foi
  conferida quadro a quadro; aprovação humana está "ligada" mas na prática é automática.
- **O que fazer:** para limpos com `revisar` e para qualquer bruto cuja origem não seja o próprio cron (sem entrada no
  `video_cache`/`hist`), gerar folhas de quadros (5 quadros × 3 vídeos) e aprovar pelo agente olhando telefone/URL/logo/
  texto ilegível/quadro congelado; reforçar o detector com máscara de marca fixa por quadros parados.
- **De onde copiar:** `D:\manhwa-react\testes\folhas_quadros.py`, `mr\rede.py:998-1028` (`aprovar`),
  `mr\capa.py:65-127` (`mascara_marca`/`tirar_marca`).
- **Impacto/Esforço/Risco:** 3 / P (folhas) + M (máscara) / baixo.
- **Como validar:** lote de 15 limpos "revisar" passa pela folha; nenhum aprovado com logo ou número visível.

#### AB-10 — Alertas de volume e de política no Telegram
- **Problema:** nada avisou o afrouxamento de 14/10 nem os 8 uploads em 42 min de 15/10.
- **O que fazer:** em `notificar_telegram.py` (`checar_logs`/avisos a cada ~30 min): avisar se um canal passou de 3
  uploads no dia, se 2 uploads do mesmo canal saíram com < 1 h, se `politica.json` difere do piso, e se 2 canais deram
  erro de upload no mesmo dia (então criar `PARADO.json`).
- **De onde copiar:** `D:\postador-de-videos\bin\notificar_telegram.py` (já lê o ledger); `bin\politica.py` (parada geral).
- **Impacto/Esforço/Risco:** 3 / P / baixo.
- **Como validar:** simular 4 linhas no ledger para o mesmo canal → mensagem no Telegram.

#### AB-11 — Escalar só com dado (regra operacional)
- **Problema:** 0 medidas de "veo limpo"; o veo entra em 2 canais com nota fixa 6 (`mr\rede.py:249-250`).
- **O que fazer:** manter 1 veo por dia na rede até `aprendizado_global.json` ter ≥ 10 medidas de origem `veo limpo`
  (`notificar_telegram.py:598-664` já prevê essa origem); só ampliar canais/teto se a mediana de 48 h ≥ 50% da mediana
  do react no mesmo canal; expor "veo limpo" no resumo diário.
- **Impacto/Esforço/Risco:** 3 / P / nenhum.
- **Como validar:** resumo das 08:00 traz a linha "veo limpo: n=…, mediana=…".

#### AB-12 — Conferir dois sinais de alerta nos canais que recebem o veo
- **Problema:** `D:\manhwa-react\logs\rede_20261015.log` repete a cada hora "404 videoNotFound" para o vídeo
  `wKiGkUQ6bBc` (InventoReact, agendado 13/10 23:00, fonte `completo`) e "403 insufficientPermissions" nos comentários
  do Inovare Manga ind; `mr\publish.py:178-180` só desiste depois de 3 dias.
- **O que fazer:** abrir o Studio do InventoReact e ver se o vídeo foi removido pelo YouTube (aviso) ou privado pela
  dona; se removido, pausar o veo nesse canal e registrar; no código, desistir no 1º 404 de vídeo (não de comentário).
- **Impacto/Esforço/Risco:** 3 / P / nenhum.
- **Como validar:** log sem o 404 repetido; estado do canal anotado em `rede_canais.json`.

### 4.2 Vídeo atrativo (AT)

#### AT-01 — Conferir idioma, fala e rosto antes de aceitar o vídeo
- **Problema:** `validar_video` (`cron_gerar_video_llm.py:1280-1298`) só olha largura/altura e codec de áudio; vídeo
  sem áudio segue como SUCESSO (`:1577-1582`); `gera_auto.py:852` ignora o retorno de `_subir_imagem` (se a foto não
  anexar, o Flow gera uma pessoa genérica e o cron registra a foto como usada) e `:845` ignora `garantir_modo_veo`.
  Não há transcrição na beta. O `RUNBOOK` já avisa: "ffprobe não ouve o idioma".
- **O que fazer:** depois do download: (a) se `_subir_imagem`/`garantir_modo_veo` falharam, abortar com exit próprio
  em vez de gerar; (b) extrair o áudio (FLAC), transcrever com Groq pelo proxy Webshare, exigir `language == pt` e
  similaridade por trigramas ≥ 0,5 com a fala pedida; (c) se falhar, marcar `revisar`, não registrar como sucesso e
  trocar o prompt (sem queimar conta nova); gravar `fala_ouvida`, `idioma`, `foto_anexada` no cache.
- **De onde copiar:** `D:\manhwa-react\mr\transcribe.py:66-119` (`transcribe_groq`, palavras com tempo) + `mr\groq_api.py`
  (ou `D:\hipercool-videos\bin\groq_api.py:60-122`); `mr\memoria.py:132-158` (`repetido_texto`); `limpar_veo.py:163-171`
  já transcreve assim.
- **Impacto/Esforço/Risco:** 5 / M / baixo (custo: ~1 MB de banda do proxy por vídeo; decisão 9).
- **Como validar:** forçar um prompt em inglês → vídeo vai para `revisar`; vídeo normal grava `idioma: pt` e
  similaridade ≥ 0,5.

#### AT-02 — Validação forte antes de qualquer cópia, thumb ou `postar.json`
- **Problema:** `postar.json`, thumbs e cópia para `hipercool-materiais` acontecem antes de `validar_video`
  (`cron_gerar_video_llm.py:1545-1575` vs `:1577`); erro do ffprobe devolve `(None, <erro>)` e a mensagem conta como
  "áudio presente" (`:1297-1298`, `:1579`); não confere duração 7,5–8,5 s, 9:16, quadros pretos/congelados nem loudness;
  caminho fixo `D:\hipercool-materiais\bin\ffprobe.exe` (`:1284`).
- **O que fazer:** portar `validate_output` (streams, duração esperada ± 1 s, LUFS, `blackdetect`) + `freezedetect`;
  tratar erro do ffprobe como falha; usar `FFMPEG_PATH` de `pos_producao\config.py`; só depois gerar `postar.json`
  (por vídeo), thumbs e cópia.
- **De onde copiar:** `D:\manhwa-react\mr\validate.py:8-52`; `GUIA_AUTOMACAO_FLOW_VEO.md:34-41`.
- **Impacto/Esforço/Risco:** 4 / P / baixo.
- **Como validar:** arquivo mjpeg 512x512 (Nano Banana) e vídeo de 4 s são reprovados; vídeo bom passa.

#### AT-03 — Fechar o laço de métricas sem chave de API
- **Problema:** `metrics_client.py:21-23,39-41` depende de `YOUTUBE_API_KEY` (regra da dona proíbe criar chave) e, sem
  ela, **devolve vazio em silêncio** em vez de avisar; a regex `:154,224` (`(?:v=|youtu\.be/)`) não casa URL de
  `/shorts/`, então mesmo com chave o Short não seria medido; `_auto_fetch_metricas` é no-op; `analisar_padroes_viralizacao` usa `re` sem importar (`:618`, NameError
  engolido em `:202-205`); `medir_metricas.py` do postador não é chamado por ninguém; vencedoras exigem views ≥ 100
  (`vencedoras.py:55-60`) → sempre vazias. Replicação de fórmulas, keywords virais, ranking de ganchos e "foto
  inteligente" rodam sobre o score do próprio crítico: o sistema aprende a agradar o LLM.
- **O que fazer:** apagar a dependência de API key; ler views de 48 h do `aprendizado_global.json` (por `video_id` do
  `publicados.json`) e, 1x/dia, CTR/retenção pelo Studio no navegador; gravar em `video_cache.metrics` via
  `update_metrics`; corrigir o import de `re`; espelhar `posted_url`/`video_id` no cache quando a rede postar.
- **De onde copiar:** `D:\postador-de-videos\bin\notificar_telegram.py:598-664` (`medir_48h`),
  `D:\hipercool-videos\bin\metricas.py:68-147`, `youtube_studio_extras.py:579-601` (`metricas`; **não testado em página
  real**; Shorts têm rótulos diferentes).
- **Impacto/Esforço/Risco:** 5 / M / baixo.
- **Como validar:** após 48 h do 1º veo da rede, `video_cache.json` tem `metrics.views > 0`; 1 rodada `--agora` do
  leitor do Studio num Short real confere os rótulos.

#### AT-04 — Não repetir ideia: dedupe de fala antes de gastar crédito e memória antiga
- **Problema:** anti-repetição = últimas 10 falas/8 cenários do MESMO tema no prompt (`llm_client.py:380-383,430-433`),
  sem similaridade e sem cruzar temas; memória zerada em 12/10 (cache com 2 vídeos); a experimental guarda 130
  fórmulas de julho (`D:\veo\experimental\logs\video_cache.json`).
- **O que fazer:** antes de disparar `gera_auto`, comparar trigramas da fala nova com todas as falas do cache (500
  itens) → ≥ 30% igual pede outra ao Hook Generator; importar as 130 fórmulas da experimental (sem `video_path`) para
  anti-repetição e saturação; manter a saturação por tema.
- **De onde copiar:** `D:\manhwa-react\mr\memoria.py:132-158`.
- **Impacto/Esforço/Risco:** 4 / P / baixo. **Decisão 11.**
- **Como validar:** repetir a mesma fala 2x no teste → 2ª é rejeitada antes de abrir o Chrome.

#### AT-05 — Estética própria por persona (acabar com o neon padrão)
- **Problema:** `llm_client.py:424` manda "Estilo: viral TikTok, dinâmico, cores vibrantes, lighting chamativo";
  `agents.py:417` "ultra HD, neon vibrant lighting"; os 2 cenários de 12/10 são "neon rain… cyberpunk" e "neon water
  droplets… dark lab". Mesma foto, mesma estrutura de 8 s, mesma estética em 25 personas = "Shorts de IA muito parecidos".
- **O que fazer:** campo `visual` (paleta, locação, lente, ritmo, luz) em cada persona de `inteligencia.PERSONAS`
  (`:30-181`), injetado no `gerar_prompt_viral`/`_agent_scenario_director_multi` no lugar do texto fixo; proibir termos
  usados nos últimos N cenários de qualquer tema; pedir "no subtitles, no on-screen text" (AT-08).
- **De onde copiar:** `D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md` §4 (estrutura de retenção) como
  guia; código novo.
- **Impacto/Esforço/Risco:** 4 / M / baixo.
- **Como validar:** 10 cenários seguidos de personas diferentes sem repetir paleta/locação; conferir por quadros.

#### AT-06 — Usar as 334 fotos das subpastas por tema
- **Problema:** `cron_gerar_video_llm.py:941-953` usa `glob.glob` sem `**`/`recursive`, então sorteia só entre as 305
  fotos soltas da raiz; as **333 das subpastas** (`comedia` 30, `epocas` 170, `guerra` 73, `herois` 54, `jornal` 6)
  nunca entram; a "foto inteligente" nunca atua (`registrar_match` não é chamado em lugar nenhum do projeto;
  `logs\foto_cenario_match.json` não existe).
- **O que fazer:** mapa tema → pasta (humor/ETs → comedia; releitura/"E se" → epocas; notícias → jornal; motivação/
  recordes → herois; hipotéticos → guerra), fallback na raiz, escolha por md5 do id do vídeo; registrar a foto no cache
  para medir depois (ou remover a "foto inteligente" morta).
- **Impacto/Esforço/Risco:** 3 / P / baixo. **Decisão 14** (a dona continua em todas as personas?).
- **Como validar:** 5 vídeos de "Notícias de IA" usam fotos de `jornal\`.

#### AT-07 — Crítico de verdade
- **Problema:** `agents.py:433` tenta trocar o modelo do crítico pela env `LLM_MODEL`, mas `llm_client.py:31/268` lê a
  constante no import → mesmo modelo e temperatura 0,9 fixa (`:117,:274`) para gerador e juiz; no fallback para chaves
  Gemini `maxOutputTokens` é 120 para tudo (`:272-277`), trunca o JSON do crítico e ele devolve 6 por padrão
  (`agents.py:490`) → regenera 3x e sai com 6; o Trend Scout é descartado no caminho single (`agents.py:312-328`);
  o crítico só lê texto, nunca o vídeo.
- **O que fazer:** modelo e `max_tokens` como parâmetros de `_call_gemini_native` (subir para 512); crítico num modelo
  diferente do gerador; usar `trend_data` no hook single ou tirar o Trend Scout; opcional: depois do render, mandar 2
  quadros + a transcrição (AT-01) para uma nota de "a dona aparece / fala em pt-BR / gancho visual no 0–1 s".
- **De onde copiar:** `D:\veo\beta\pos_producao\comercial_agents.py:239-261` (crítico com critérios nomeados);
  `D:\manhwa-react\mr\llm.py:17-48` (`extract_json` robusto) e `:124-137` (`ask_json` com cadeia de provedores).
- **Impacto/Esforço/Risco:** 4 / M / baixo.
- **Como validar:** log mostra modelo do crítico ≠ do gerador; sem score 6 "por padrão" em 20 vídeos.

#### AT-08 — Usar o que o Veo 3.1 e o Flow têm de novo (15/10/2025)
- **Problema:** o veo usa só "starting frame + prompt" (`gera_auto.py:808-814`); o Veo queima legendas/texto ilegível
  (visto nos quadros do VO3: "WhatsApp" com texto sem sentido) e às vezes fala outra língua.
- **O que fazer:** (a) no prompt: dialogo entre aspas com dois-pontos, "no subtitles, no on-screen text", uma frase só
  (guias de prompt do Veo 3); (b) testar **Ingredients to Video** (até 3 imagens de referência) para manter a dona e o
  produto consistentes em vez de só a foto como 1º quadro; (c) **Extend** para 15–20 s quando a fala pedir mais que 8 s
  (medir retenção antes de adotar); (d) Fast (20 créditos) por padrão, Quality (100) só para comerciais aprovados.
  Cada item exige automação nova na UI do Flow (`flow_bot.py`) e teste real com a dona olhando.
- **De onde copiar:** anúncio oficial `blog.google/technology/ai/veo-updates-flow/` (15/10/2025); créditos: 9to5google
  (Fast 20 / Quality 100; Pro 1.000 por mês).
- **Impacto/Esforço/Risco:** 4 / M–G / médio (UI do Flow muda; a automação de 12/10 já teve de ser reescrita).
- **Como validar:** 5 vídeos com "no subtitles" sem texto queimado (quadros); 1 Extend de 16 s válido por ffprobe.

#### AT-09 — Legendas palavra a palavra a partir do áudio
- **Problema:** `plugins\legendas.py:47-72` distribui o texto do PROMPT pela duração, sem ouvir o áudio (o Veo nem
  sempre fala o que foi pedido); `legendas.py:124-126` e `subtitles_veo.py:150-171` usam uma entrada `-loop 1` por
  trecho num único grafo (padrão que trava o ffmpeg 8.1). `limpar_veo.py:163-171` transcreve mas joga fora
  `res['words']`.
- **O que fazer:** guardar `words` (com tempo) na transcrição de AT-01/`limpar_veo`; gerar um ASS único (blocos de até
  3 palavras/1,4 s, palavra ativa com pop, gancho nos 0–2 s, CTA textual nos 2–3 s finais sem telefone) e queimar com
  `-vf ass=…:fontsdir=…` no passe final (IM-04). Se o Veo falou diferente, a legenda segue o áudio e a `fala` do json é
  atualizada.
- **De onde copiar:** `D:\manhwa-react\mr\captions.py:33-172` (`chunk_words`, `build_ass`; sem divisória a legenda vai a
  62% da altura) ou `D:\hipercool-videos\bin\fx_acabamento.py:715-834` (`montar_ass`); fontes em
  `D:\manhwa-react\assets\fonts` / `D:\hipercool-materiais\assets\fonts`.
- **Impacto/Esforço/Risco:** 4 / M / baixo.
- **Como validar:** quadro a 2 s mostra a palavra que está sendo dita; nenhum `-loop 1` no comando do ffmpeg.

#### AT-10 — Áudio nivelado (e trilha opcional)
- **Problema:** o COMPLETO medido está em −17,2 LUFS integrado (pico −1,7 dBFS) e o LIMPO não passa por nivelamento;
  `montar_final.py`/`worker_noite.py` não chamam loudnorm; só o trecho do CTA tem loudnorm −16 e ducking fixo
  `volume 0.25` (`cta_builder.py:354-356`); o plugin antigo é de 1 passo em −16 (`plugins\ffmpeg_loudnorm.py:33`).
- **O que fazer:** master em 2 passos −14 LUFS / −1 dBTP no vídeo inteiro ao fim de `montar`/`limpar_veo`; se a dona
  quiser trilha (decisão 10): 1 faixa de `prioritarias` fora da blocklist, −28 LUFS, ducking por sidechain pela fala,
  sem repetir as últimas 16; SFX leves (whoosh na transição, 1 impacto no gancho).
- **De onde copiar:** `D:\manhwa-react\mr\audio.py:49-63` (`loudnorm_two_pass`); `D:\hipercool-videos\bin\fx_acabamento.py:606-656`
  (`masterizar_audio`), `bin\fx_music.py:146-184`. **Atenção:** `mr\music.py:29` tem o bug da blocklist (nada é
  bloqueado): corrigir antes de copiar.
- **Impacto/Esforço/Risco:** 3 / M / baixo.
- **Como validar:** `ffmpeg -af ebur128` no final: I = −14 ± 1 LUFS, TP ≤ −1 dBFS.

#### AT-11 — Thumbs A/B/C: escolher, checar e medir
- **Problema:** `thumbnail_client` gera 3 variantes por vídeo (3.411 arquivos em `thumbnails\`), mas só a "A" vai ao
  `postar.json` (`cron_gerar_video_llm.py:1545-1569`), ninguém mede e `postar_tudo_hoje` nem passa thumbnail; capa
  personalizada exige canal verificado por telefone (`youtube_web_poster.py:489-509`).
- **O que fazer:** rodízio Thompson entre A/B/C com exploração mínima de 2 usos, checagem (sem número/URL/handle, rosto
  visível, texto legível), `<mp4>.capa.json` com a variante usada e vitória registrada pela medição (AT-03); só subir
  capa em canal verificado; apagar as thumbs órfãs.
- **De onde copiar:** `D:\hipercool-videos\bin\seo.py:230-244` (Thompson), `bin\capa_ia.py:201-233,306-326` (checagem,
  `registrar_teste`/`registrar_vencedora`), `bin\intros_voz.py:49` (`USOS_PRA_EXPLORAR`). As poses de manhwa não se aplicam.
- **Impacto/Esforço/Risco:** 3 / M / baixo.
- **Como validar:** `logs\rodizios.json` com contagem por variante; capa enviada confere com a variante registrada.

#### AT-12 — Créditos, timeouts e log do worker
- **Problema:** conta pro vazia vira EXHAUSTED só até 00:05 (`cron_gerar_video_llm.py:744-779`) embora o próprio
  comentário diga que pro acumula 1.050 créditos (`:868-871`); o cron mata o worker em 1.200 s × fator (`:1231`,
  `recursos.py:90-96`) mas o worker só desiste em 1.800 + 120 s (`gera_auto.py:914-922`); em 12/10 um TIMEOUT de
  1.500 s precedeu "sem créditos" na mesma conta; o stdout do worker (prompt final, saldo, foto anexada) é descartado
  (`:1236` `capture_output`), só 300 chars do stderr em falha (`:1275`); o cooldown por falhas acumuladas (`:735-739`)
  mistura falhas do robô MS Energy que escreve no mesmo `sessoes_status.json`.
- **O que fazer:** guardar o saldo lido em `sessoes_status`; conta pro só reabre quando saldo ≥ 20 for lido de novo;
  timeout do cron = deadline do worker + 60 s; reler o saldo antes de contar timeout como falha; gravar
  `logs\worker_<sessao>_<ts>.log`; estado de sessão por projeto (decisão com o MS Energy).
- **Impacto/Esforço/Risco:** 3 / P / baixo.
- **Como validar:** conta sem crédito não é reaberta à meia-noite; log do worker existe para cada tentativa.

### 4.3 Comercial com Veo 3 (VO)

#### VO-01 — Pool pequeno, desbalanceado e com um clipe deitado
- **Problema (conferido):** `_pool_dir` (`vo3_propaganda_rotator.py:52-61`) resolve para
  `D:\hipercool-materiais\veo\propagandas_vo3\vo3` (9:16) e `…\vo3_lateral` (16:9) — **não** para
  `pos_producao\propagandas_pool\`, onde ficam só 3 demos de 3 s sem áudio (ignorados). O pool real tem **8 clipes de
  01/08**: hermes_call ×4, avatar_ia ×2, follow_up_2, superchat_1 — ou seja, 4 dos 9 produtos sem nenhum clipe, e
  **`hermes_call_1.mp4` está deitado (1280x720) dentro da pasta vertical**. `vo3_lateral\` está vazia, então a variante
  16:9 nunca tem clipe.
- **O que fazer:** validar dimensão/duração/áudio na entrada do pool (ffprobe) e recusar quem não bater com a
  orientação da pasta; ≥ 3 clipes por produto top em 9:16, regenerados com o prompt de VO-02; apagar ou mover
  `hermes_call_1.mp4`; apagar os 3 demos locais para não confundir o próximo agente; rotação por md5 (já existe)
  evitando repetir o último clipe no mesmo canal; registrar no sidecar qual clipe entrou.
- **Impacto/Esforço/Risco:** 4 / M / baixo (crédito: ~20 por clipe Fast; 4 produtos × 3 = ~240 créditos).
- **Como validar:** `python pos_producao\vo3_propaganda_rotator.py listar` mostra ≥ 3 por produto, todos verticais,
  8 s, com áudio; ffprobe em cada um.

#### VO-02 — Prompt do comercial sem texto na tela e com produto consistente
- **Problema:** o fallback de `montar_prompt` pede "the product name appears as clean on-screen text"
  (`vo3_propaganda_rotator.py:141-146`): o Veo erra texto (quadros mostram "WhatsApp" com letras sem sentido); o
  diretor (`comercial_agents.py:196-237`) não pede "no subtitles"; não há imagem de referência do produto.
- **O que fazer:** no diretor e no fallback: "no subtitles, no on-screen text, no captions", fala entre aspas com
  dois-pontos, uma frase, pessoa olhando para a câmera (já); nome do produto entra depois, pela legenda ASS/HyperFrames
  (AT-09, IM-02), não pelo Veo; testar Ingredients to Video com 1 imagem do produto (print real da tela) + 1 foto da
  dona como apresentadora (AT-08); marcar `sintetico` no json.
- **De onde copiar:** guias de prompt do Veo 3 (aspas + dois-pontos acionam lip-sync; sem elas o texto vira legenda);
  `comercial_agents.py` já tem a estrutura.
- **Impacto/Esforço/Risco:** 4 / P (prompt) + M (referência) / baixo.
- **Como validar:** 3 clipes novos sem texto queimado (quadros); produto reconhecível.

#### VO-03 — Conferir o clipe gerado: fala, idioma, legenda, loudness
- **Problema:** `_critico` (`comercial_agents.py:239-261`) avalia só o prompt; nada confere se o Veo falou a fala em
  português; o clipe entra no pool sem checagem.
- **O que fazer:** mesma cadeia de AT-01 (transcrição Groq: `language == pt`, similaridade ≥ 0,5 com a `fala` do
  roteirista) + legenda ASS da fala ouvida + master −14 LUFS; reprovado não entra no pool.
- **De onde copiar:** AT-01, AT-09, AT-10.
- **Impacto/Esforço/Risco:** 4 / P (depois de AT-01) / baixo.
- **Como validar:** clipe com fala em inglês é reprovado; pool só com `idioma: pt`.

#### VO-04 — Frequência do comercial: 1 em N, nunca em todo vídeo
- **Problema:** `worker_noite._VARIANTES` gera COMPLETO (VO3 + card) para 100% dos vídeos; anúncio do mesmo produto em
  todo Short de 20+ canais é "conteúdo repetitivo" e "redirecionar para fora" aos olhos da política.
- **O que fazer:** formato por vídeo decidido na rede/pós: `limpo` | `comercial_curto` (só clipe VO3, sem card) |
  `comercial_com_card` (só TikTok/Instagram, se a dona mantiver); por canal, no máximo 1 comercial a cada N vídeos
  (sugestão N = 3) e nunca o mesmo produto em 2 dias seguidos; gravar `formato` e `produto` no json para o aprendizado
  medir (DS-04).
- **Impacto/Esforço/Risco:** 4 / P / baixo. **Decisão 4.**
- **Como validar:** `publicados.json` dos últimos 7 dias: ≤ 1/3 dos veo com `formato` comercial por canal.

#### VO-05 — CTA do comercial sem número e sem URL; medir conversão
- **Problema:** hoje o contato aparece no card (número) e a fala não cita contato (bom). Links em descrição e
  comentários de Shorts não são clicáveis desde 08/2023; comentário fixado exige canal verificado.
- **O que fazer:** CTA falado = benefício + "procura <produto> no Google/Instagram" ou "link no perfil"; contato só na
  aba "Sobre" do canal (link em destaque) e no site; UTM por canal/produto no link do "Sobre" para medir; nada de
  número na tela.
- **Impacto/Esforço/Risco:** 3 / P / nenhum. **Decisão 5.**
- **Como validar:** quadros do comercial sem dígitos de telefone; relatório de UTM por canal.

#### VO-06 — Contas de propaganda e documento desatualizados
- **Problema:** `VO3_PROPAGANDA_ROTACAO.md` lista 5 contas (conta5…conta9); `chrome_gen_conta9` não existe mais
  (`LEIA_PERFIS_E_COFRE.md`, 12/10); conferir a lista que `_porta_da_conta`/`gerar_pool` usam
  (`vo3_propaganda_rotator.py:176-284`).
- **O que fazer:** ler as contas de `contas.py` (fonte única) com um campo `papel: propaganda`; atualizar o doc.
- **Impacto/Esforço/Risco:** 2 / P / baixo.
- **Como validar:** `gerar --tops --n 1` não tenta conta inexistente.

### 4.4 Comercial com imagens / card CTA (IM)

#### IM-01 — Card sem telefone, sem "OFERECIDO POR", sem "@InovareStories"
- **Problema:** `cta_card.py:155` `whatsapp = "91 98469-8653"` fixo e badge em destaque; `:200-202` "OFERECIDO POR";
  `assets\branding.json`/`branding_watermark.py:24-26` handle e "Siga pra mais historias IA". O `LEIA.txt:101-103` do
  postador liga exatamente esse slide à queda dos canais; a política de spam cita contato/redirecionamento em texto na
  tela.
- **O que fazer:** versão YouTube do card = nome do produto + 1 benefício (do `cta_curto`) + pergunta ou "link no
  perfil"; sem número, sem URL, sem handle; cores do produto; 2–3 s. Número/URL só numa variante `tiktok` se a dona
  quiser (decisão 5); `_meta.whatsapp` de `produtos.json` deixa de ir para a tela.
- **De onde copiar:** `cta_card.py` (manter fundo IA, auto-fit e variantes); regra de "nome proibido em lugar nenhum,
  inclusive texto na tela" do hipercool (§4b2), aplicada a telefone/URL/handle.
- **Impacto/Esforço/Risco:** 5 / P / baixo.
- **Como validar:** regex de dígitos/URL/@ sobre o texto desenhado = 0; quadro do card conferido.

#### IM-02 — Card animado e proporcional, no lugar do slide parado de 5–6 s
- **Problema:** hoje são 8 s de conteúdo + 8 s de VO3 + 5–6 s de slide parado (COMPLETO de 15,4 ou 28 s): mais da
  metade é anúncio; o slide é um PNG com `-loop 1` (`cta_builder.py:199,342`).
- **O que fazer:** end-card de 2–3 s em MOV com alfa (HyperFrames: nome do produto + benefício animados) sobreposto nos
  últimos segundos do clipe com `overlay` + `tpad` (nunca `-itsoffset`), ou parallax 2.5D leve no fundo IA
  (`efeitos_imagem.py` já faz zoompan sem `-loop`); comercial curto fica com 8–12 s.
- **De onde copiar:** `D:\manhwa-react\mr\hyperframes.py:21-127` (templates `cta_question`, `big_number`; render via
  Playwright Chromium — conferir `playwright install chromium` no venv do veo) e `mr\render.py:223-224` (composição).
- **Impacto/Esforço/Risco:** 4 / M / baixo.
- **Como validar:** COMPLETO novo ≤ 12 s; card aparece animado nos últimos 2–3 s (quadros).

#### IM-03 — Vozes aprovadas e fixas por produto
- **Problema:** fallback do card usa `pt-BR-FranciscaNeural` e `pt-BR-AntonioNeural` (`edge_tts_veo.py:24-44`,
  `_NARRATOR_PROFILE`), também em `assets\voz_config.json`, `plugins\_tts_helper.py:68` e `plugins\voz_whatsapp.py:36`:
  vozes **proibidas** pela dona em qualquer projeto (15/10). O pool ElevenLabs (`sarah, bella, matilda, adam, eric`) e o
  sorteio por md5 (`cta_builder.py:127-135`) estão certos.
- **O que fazer:** trocar os perfis edge pelas Multilingual aprovadas (`EDGE_F`/`EDGE_M` + variações), recusar
  `PROIBIDAS`, voz fixa por produto (md5 do id do produto), cache por voz+rate+pitch+texto. Não copiar
  `edge_tts_engine.py` do hipercool (é legado com Francisca e `hash()`).
- **De onde copiar:** `D:\hipercool-videos\bin\elenco.py:43-52` (listas), `:103-104` (md5), `:247-274` (`falar_edge`).
  Facilita: `edge_tts_veo` só é chamado de um lugar em todo o projeto (`cta_builder.py:169`), então a troca é contida.
- **Impacto/Esforço/Risco:** 3 / P / baixo.
- **Como validar:** `grep -r "FranciscaNeural\|AntonioNeural" D:\veo\beta` = 0; áudio do card gerado com Thalita/Andrew.

#### IM-04 — `-loop 1` → clipe parado em cache; passe final único
- **Problema:** 5 lugares usam `-loop 1` em comando ffmpeg — `cta_builder.py:199` e `:342`, `plugins\legendas.py:126`,
  `plugins\propaganda_inteligente.py:262` e `subtitles_veo.py:166` (várias entradas assim num mesmo grafo travam o
  ffmpeg 8.1 sem usar CPU; o hipercool perdeu horas: `MELHORIAS…:180-186`); `montar_final` ainda encadeia 4–6 encodes
  intermediários.
- **O que fazer:** converter toda imagem parada em `.mov qtrle` com alfa em cache (`pos_producao\cache\clipes_parados`)
  e juntar overlays, card, emoji e ASS num único `filter_complex` (fps 30, scale lanczos, cas 0,35), com `h264_qsv`
  (UHD 620) e fallback x264 por timeout.
- **De onde copiar:** `D:\hipercool-videos\bin\fx_acabamento.py:893-906` (`_clipe_parado`), `:909-999` (`passe_final`),
  `:93` (`ffmpeg_retry`).
- **Impacto/Esforço/Risco:** 3 / M / médio (encode novo: validar por quadros e ffprobe).
- **Como validar:** `grep -r "\"-loop\"" D:\veo\beta\pos_producao` só em código morto; tempo de montagem cai; sem
  processo ffmpeg parado > 10 min.

#### IM-05 — Variar o card entre vídeos
- **Problema:** mesmo card (produto, variante) em centenas de vídeos; o cache por `(produto, variante)` é bom para
  custo, ruim para "repetitivo".
- **O que fazer:** 3 copies por produto (`cta_curto`, 1 frase do `cta_longo`, pergunta) e 3 fundos, combinados por
  md5 do vídeo; cache por (produto, copy, fundo); texto normalizado para TTS (já: `_tts_normalizar`).
- **Impacto/Esforço/Risco:** 3 / P / baixo.
- **Como validar:** 10 COMPLETO do mesmo produto com ≥ 3 cards diferentes.

### 4.5 Distribuição, SEO e medição (DS)

#### DS-01 — O veo passa pelo diretor da rede, em mais canais, com teto global
- **Problema:** `mr\rede.py:43` `canais_veo_limpo = ['inventoreact', 'manhwareact']` — e o `config.json` do
  manhwa-react **não tem a chave `rede`**, então vale 100% o `REDE_PADRAO` do código (`_rc`, `:47-50`); `:247-250` dá ao
  veo **nota fixa** = `nota_min` (6), sem passar pelo diretor, porque ele entra como "restrito" → só pega a vaga que
  sobra depois de qualquer react com nota ≥ 6. Resultado medido: em 16/10 05:20 a fila tinha **227 vídeos aprovados**,
  **8 canais sem vídeo bom** (animescomia, inovaremanhwabr, cartuchoreact, forjareact, mundoquenaoexiste,
  historiasemframes, fiodameada, dicasfinanceirasdaia) e **1 vídeo agendado** na rodada
  (`D:\manhwa-react\logs\rede_20261016.log:36,42,44`); em 15/10, 10 aprovados na fila, 7 esperando aprovação e 1
  agendado (`rede_20261015.log:136,143`). Ou seja: há vaga sobrando em 8 canais e estoque parado de 225 limpos.
- **O que fazer:** chave `rede` no `config.json` do manhwa-react com `canais_veo_limpo` ampliado (mundoquenaoexiste
  — nicho "vídeos de IA, situações absurdas, e se…" — e, só para a persona Dicas Financeiras e com as `regras` do dono,
  dicasfinanceirasdaia/assistiainvestimentos), `veo_max_dia_rede` (sugestão 3) e nota pelo diretor por nicho (o json do
  limpo já tem `tema` e `fala`); manter 1 por canal por dia e nunca o mesmo vídeo em 2 canais.
- **De onde copiar:** `mr\rede.py:207-277` (`notas`, `distribuir`); `config\rede_canais.json` (nichos).
- **Impacto/Esforço/Risco:** 5 / M / baixo. **Decisão 3.**
- **Como validar:** log da rede com notas do diretor para itens `veo:`; ≥ 1 veo agendado por dia enquanto houver vaga.

#### DS-02 — Metadados pelo agente do canal + revisor antipropaganda
- **Problema:** `publicar.py` (emoji, 5 hashtags, CTA do dia, "#viral #brasil") ainda é o que o veo escreve; o revisor
  da rede (`mr\rede.py:454-475`) não tem regra para telefone/URL/"chama no zap".
- **O que fazer:** fonte `veo` usa só `adaptar()` da rede; acrescentar `PROIBIDO_PROPAGANDA` (telefone, whatsapp,
  "chama no zap", URL, "clique no link") a `revisar`; campo `produto` no resumo para o agente citar o produto pelo nome
  na descrição quando o vídeo for comercial; aposentar `_caption_llm`/`_caption_fallback`.
  **Confirmado na verificação:** hoje o revisor só tem `PROIBIDO_TITULO` (violência/sexo/drogas, só no título),
  `PROIBIDO_DONO` (promessa financeira: "garantido", "fique rico", "prevê o mercado"… só em canal com `regras`) e a
  checagem de "o criador" (`mr\rede.py:454-475`). **Nenhuma regra barra telefone, "whatsapp", URL ou "clique no link"** —
  "Sem links" existe só como instrução ao LLM no prompt (`:445`), sem verificação depois.
- **De onde copiar:** `mr\rede.py:431-451` (AGENTE_INSTR), `:454-484`, `:526-550`.
- **Impacto/Esforço/Risco:** 4 / P / baixo.
- **Como validar:** descrição com número de telefone é barrada no teste; 10 títulos seguidos sem template.

#### DS-03 — SEO com palavras buscadas e Thompson por estilo de título
- **Problema:** nenhum título do veo usa palavras que o público busca; nenhum estilo é medido.
- **O que fazer:** banco de palavras por tema/produto com o autocompletar público (`suggestqueries…client=youtube&hl=pt-BR`,
  permitido), 3 estilos (busca/provocação/curiosidade) sorteados por Thompson, `estilo` gravado no `publicados.json`,
  vitória registrada pela medição (DS-04); para a fonte `veo`, alimentar o agente do canal com 2–3 sugestões do
  autocompletar sobre o tema da fala; dicionário de segurança de anúncios.
- **De onde copiar:** `D:\hipercool-videos\bin\seo.py:147-184` (REGRAS, `_palavras`), `:193-220` (`_sem_obra` →
  termos de spam), `:230-244` (Thompson), `config\seo_palavras.json`, `config\dicionario_seguro.json`; `docs\seo_titulos.md:14`.
- **Impacto/Esforço/Risco:** 3 / M / baixo.
- **Como validar:** `logs\titulos_estilos.json` com testes por estilo; títulos contêm ≥ 2 termos do banco.

#### DS-04 — Medir o veo em 48 h e no Studio, e alimentar os rodízios
- **Problema:** `medir_48h` já prevê origem "veo limpo" (`notificar_telegram.py:598-664`), mas não há amostra; o
  leitor do Studio (`youtube_studio_extras.py:579-601`) nunca rodou em página real e exclui Shorts (`metricas.py:28`).
- **O que fazer:** garantir que todo veo postado entra no `publicados.json` com `origem`, `formato`, `estilo`,
  `gancho`; 1 rodada manual do leitor do Studio num Short real para acertar os rótulos ("Visualizações", "assistiram x
  deslizaram"); alimentar `registrar_resultado` (título), rodízio de thumbs e de formato (limpo × comercial).
- **De onde copiar:** `D:\hipercool-videos\bin\metricas.py`, `bin\seo.py:230-244`, `D:\postador-de-videos\bin\painel_canais.py:74-108`.
- **Impacto/Esforço/Risco:** 4 / M / baixo.
- **Como validar:** `aprendizado_global.json` com `veo limpo` n ≥ 10; `workspace\metricas` do veo com CTR de 1 Short.

#### DS-05 — Extras do Studio quando a conta permitir
- **Problema:** nada do veo chama `youtube_studio_extras.py`; comentário fixado, vídeo relacionado e teste A/B exigem
  canal verificado (o pt do hipercool está negado até 14/11/2026: `PEDIDOS_DO_DONO_PENDENTES.md:76-87`); a rede comenta
  pela API e falha com 403 em alguns canais.
- **O que fazer:** plano de `extras` por vídeo postado (comentário fixado com pergunta, **sem número e sem link**;
  limpar rascunhos 1x/dia; `editar_metadados` para tirar número/handle de vídeos antigos ainda públicos); repetir
  pendente a cada 3 h; "bloqueado até data" respeitado; mapear canal a canal o que está liberado.
- **De onde copiar:** `D:\hipercool-videos\bin\postar_hipercool.py:375-445` (`_extras_de`, `rodar_extras`).
- **Impacto/Esforço/Risco:** 3 / M / baixo.
- **Como validar:** comentário fixado aparece no 1º veo de canal verificado; vídeos antigos sem número na descrição.

#### DS-06 — Catálogo e backup cobrindo as pastas novas
- **Problema:** `catalogo.py` e `backup_drive.py` já tratam o veo; pastas novas (comerciais, pool, limpos novos) e o
  `posted_url` do json do limpo precisam continuar visíveis para o arquivo sair do PC 3 dias após postar e nunca ser
  repostado.
- **O que fazer:** conferir `catalogo.pasta_de` para `limpos\`, `videos_pos\` e a pasta do pool; `--simular` do backup.
- **De onde copiar:** `D:\manhwa-react\scripts\backup_drive.py`, `D:\postador-de-videos\bin\catalogo.py`.
- **Impacto/Esforço/Risco:** 2 / P / baixo.
- **Como validar:** `python bin\catalogo.py` lista as pastas; `backup_drive.py --simular` inclui limpos postados há 3 dias.

### 4.6 Base, operação e DX (BX)

#### BX-01 — Versionar o que está no ar
- **Problema:** `git -C D:\veo\beta diff --stat`: 11 arquivos, +2.218/−563 desde 31/07 (reescrita do upload/download
  para a UI do Flow de 12/10, projeto por conta, trava por porta, exit 3/7, modo paralelo…), **mais dezenas de arquivos
  novos nunca rastreados** (`LEIA_PERFIS_E_COFRE.md`, ~15 scripts de `pos_producao\`, `.bat` de produção). O repositório
  tem 3 commits, o último de 31/07 00:04. O que roda hoje não está no git.
- **O que fazer:** conferir `.gitignore` (secrets, sessions, perfis, `thumbnails\`, `videos*`, `tmp`), normalizar CRLF
  (`.gitattributes`), commit "estado de 12/10 restaurado + auditoria 15/10", tag; a partir daí, 1 commit por item deste
  plano. **Commit só com o OK da dona** (regra global).
- **Impacto/Esforço/Risco:** 4 / P / nenhum. **Decisão 7.**
- **Como validar:** `git status` limpo; `git log` com a tag.

#### BX-02 — Pausa de verdade, retomada segura e tarefas sem janela
- **Problema:** com `PAUSE_SYSTEM` manual o loop seguiu vivo abortando a cada 30 s por 3 dias; `SKIP_RESOURCE_CHECK=1`
  ignora a pausa (`cron_gerar_video_llm.py:251-252,271-272`, `gera_auto.py:1011-1012`); `FLOW_HEADLESS` (setado por
  `Veo_START_DIARIO_7H.bat:14` e `supervisor.py:98-99`) não é lido por `gera_auto` (`:493-508`); a tarefa das 7 h roda
  `cmd /c .bat` com `title` (abre janela); nenhum ponto de entrada importa `sem_janela`.
- **O que fazer:** pausa manual → loop dorme até a flag sumir; modo paralelo respeita a pausa; `sem_janela.py` na 1ª
  linha de `loop_cron.py`, `cron_gerar_video_llm.py`, `worker_noite.py`, `cron_pos_producao.py`, `supervisor.py`;
  tarefas por `pythonw.exe`; testar se o Flow aceita Chrome `--headless=new` para gerar (login continua visível) antes
  de religar a tarefa das 7 h.
- **De onde copiar:** `D:\hipercool-videos\bin\sem_janela.py` (= `D:\manhwa-react\mr\sem_janela.py`);
  `D:\hipercool-videos\bin\limitador.py` (pausa que dobra e encolhe) no lugar dos 60 min fixos de `pausar_sistema`.
- **Impacto/Esforço/Risco:** 3 / P / baixo. **Decisão 6.**
- **Como validar:** com `PAUSE_SYSTEM`, 0 linhas novas no log em 10 min; tarefa agendada roda sem janela na tela.

#### BX-03 — Trava de 1 render por vez
- **Problema:** `worker_noite.py`, `cron_pos_producao.py`/`montar_final` e `limpar_veo` podem renderizar ao mesmo tempo
  (sem lock); regra da dona: um render pesado por vez; o manhwa-react já perdeu lotes por memória.
- **O que fazer:** copiar a classe `Trava` (arquivo `.lock` com pid/hora, abandono após N min) e envolver `montar`,
  `limpar_veo.processar` e o worker.
- **De onde copiar:** `D:\manhwa-react\mr\rede.py:668-688`.
- **Impacto/Esforço/Risco:** 3 / P / baixo.
- **Como validar:** 2 workers lançados juntos → o 2º espera.

#### BX-04 — `validate.py` completo e limpeza de código morto
- **Problema:** `validate.py:22-27` não importa `inteligencia`, `fila`, `publicar`, `roteamento`, `recursos`,
  `creditos`; código morto: `AGENTS_CONFIG`/`GeminiFlashLiteLLM`, `*_i18n`, `ajustar_score_com_historico`,
  `gerar_fila_safe`, `HOOK_VISUAL_INSTR`/`LOOP_INSTR`, `registrar_match`; `loop_cron.py` importa `run` sem `load_hist`
  (se usado, `save_hist` apagaria o histórico); `flow_bot.py` (1.680 linhas) usado por 6 nomes; 3 listas de stopwords e
  4 loaders de cache; `experimental\` é cópia divergente.
- **O que fazer:** incluir os módulos vivos no smoke test; remover o morto; arquivar `experimental\` (depois de
  importar a memória, AT-04); unificar loaders.
- **Impacto/Esforço/Risco:** 3 / P–M / baixo (fazer depois do commit BX-01, item a item).
- **Como validar:** `python validate.py` verde; `grep` dos nomes mortos = 0.

#### BX-05 — Determinismo e caminhos
- **Problema:** `hash()` em `roteamento.py:60` e `plugins\propaganda_inteligente.py:61`; ffmpeg/ffprobe fixos em
  `D:\hipercool-materiais\bin` em 25+ arquivos; erro do ffprobe tratado como sucesso (AT-02).
- **O que fazer:** md5 em todo sorteio; `FFMPEG_PATH`/`FFPROBE_PATH` só em `pos_producao\config.py` (e `config.py` da
  raiz), lidos por todos.
- **De onde copiar:** regra "md5, nunca hash()" (`MELHORIAS…` §4b); `montar_final._pick` já faz certo.
- **Impacto/Esforço/Risco:** 2 / P / baixo.
- **Como validar:** `grep -rn "hash(" D:\veo\beta --include=*.py` só em `hashlib`; 2 execuções = mesmo sorteio.

#### BX-06 — Documentação que bate com a realidade
- **Problema:** `beta\README.md:16,72,76` e `TUTORIAL_AGENTE.md:7-9` citam o venv do hipercool, `D:\hipercool-inferior-fix`,
  `tools\` e `_LIXO_2026-07-26\` (não existem); `ARQUITETURA.md` diz Flash Lite (hoje gateway pro); `LEIA.txt:172-175` do
  postador anuncia 3/12/2 h; `HANDOFF_REDE.md:81-110` lista 19 ativos incluindo os inovare* que passaram ao hipercool.
- **O que fazer:** corrigir os quatro; `CLAUDE.md` da raiz do veo (criado em 15/10) é o ponto de entrada; registrar
  progresso neste plano.
- **Impacto/Esforço/Risco:** 2 / P / nenhum.
- **Como validar:** próximo agente consegue ligar/pausar e achar o venv certo só pelos documentos.

#### BX-07 — Saúde das contas Google antes de gerar
- **Problema:** a conta só "cai" quando o Flow falha (exit 3/7); `chrome_gen_conta9` sumiu em 12/10; o MS Energy
  escreve no mesmo `sessoes_status.json`.
- **O que fazer:** sonda diária de login (sem gerar nada) sobre os perfis do cofre usados por `contas.py`; marcar
  deslogadas; estado de sessão por projeto.
- **De onde copiar:** `D:\manhwa-react\scripts\saude_perfis.py:22-27`, `scripts\sonda_perfis_veo.py`.
- **Impacto/Esforço/Risco:** 2 / P / baixo.
- **Como validar:** relatório diário "13 contas: 11 logadas, 2 deslogadas".

#### BX-08 — Ambiente `prod` só depois de provar
- **Problema:** `ambientes.json`: `prod` inexistente, `beta` é a live, `experimental` desativada (mesmas portas).
- **O que fazer:** depois da Onda 1 validada e do commit, promover a beta para `prod\` (cópia + perfis apontando para o
  cofre), `experimental\` vira a pasta de teste de verdade (portas próprias).
- **Impacto/Esforço/Risco:** 2 / P / baixo.
- **Como validar:** `python supervisor.py status` lista prod ativa e beta como teste.

#### BX-09 — Ciclo 06:40 de 15/10 terminou com erro
- **Problema:** `logs\postar_auto.log` para em "Inicio TikTok"; `LastTaskResult 0x8007042B`; `tiktok_20261015.log`:
  erro em `tiktok_cdp_poster.py:67` e "nenhum Chrome disponível"; etapas 3b, 4 e o resumo da política não rodaram.
- **O que fazer:** cada etapa do `.bat` com `call`/timeout próprio e `exit /b` controlado, para uma falha não engolir as
  seguintes; investigar o Chrome do TikTok.
- **Impacto/Esforço/Risco:** 2 / P / baixo.
- **Como validar:** `postar_auto.log` do dia seguinte com "FIM CICLO COMPLETO".

---

## 5. Ordem de execução em ondas

**Onda 0 — antes de religar qualquer postagem ou geração do veo (1 dia):**
AB-01, AB-02, AB-03, AB-05, AB-06, IM-01, AB-12, BX-01 (commit, com OK), AB-04 (flag, com OK).
Pronto quando: tarefa `AgendadorVO3` desabilitada e etapas 1–2 fora do `.bat`; piso da política no código; pipeline
incremental sem propaganda/marca; `--sintetico` em todo upload do veo; `roteamento.py` sem handles mortos; card sem
número; git limpo. Destrava: a rede como único caminho, sem risco de o VO3 antigo voltar.

**Onda 1 — primeira semana (controle de qualidade e o veo na rede):**
AT-01, AT-02, DS-01, DS-02, AB-08, AB-09, AB-10, AB-11, BX-02, BX-03, IM-03, AT-04, AT-12, DS-06.
Pronto quando: 5 vídeos de teste passam por transcrição + validação + folha de quadros; veo entra pelo diretor em ≥ 3
canais com teto 3/dia na rede; dedupe barra cópia; alertas no Telegram; pausa funciona; sem vozes proibidas.
Destrava: religar a geração com poucas contas (decisão 6) e medir.

**Onda 2 — semanas 2–3 (as três peças melhores e o aprendizado):**
AT-03, DS-04, AT-05, AT-06, AT-07, AT-09, AT-10, IM-02, IM-04, IM-05, VO-01, VO-02, VO-03, VO-04, VO-05, VO-06, DS-03,
AT-11, BX-04, BX-05, BX-06.
Pronto quando: cada vídeo tem legenda do áudio, áudio −14 LUFS, estética por persona, card animado ≤ 3 s; pool VO3
real com ≥ 3 por produto; `aprendizado_global.json` com ≥ 10 medidas de "veo limpo"; títulos com estilo medido.
Destrava: decidir com dado se o formato Veo de 8 s rende e onde o comercial converte.

**Onda 3 — depois (estrutural):**
AT-08 (Ingredients/Extend/"no subtitles" na automação do Flow), DS-05 (extras do Studio), AB-07 (migração total para
o navegador), BX-07, BX-08, BX-09.
Pronto quando: 100% dos uploads pelo navegador; comentário fixado nos canais verificados; `prod` promovida.

Justificativa da ordem: impacto no risco de banimento primeiro (tudo que o YouTube lê: volume, repetição, contato na
tela, declaração de IA), depois o que impede vídeo ruim de entrar na fila, depois qualidade e medição; o que depende da
UI do Flow ou de login manual fica por último porque custa mais e quebra mais.

---

## 6. Decisões que só a dona pode tomar

1. **COMPLETO fora do TikTok/Instagram?** Hoje `veo_so_limpo: false` e 9 posts com o número em 15/10. Recomendação:
   `true` nas duas redes; se quiser contato lá, só na bio.
2. **Limites da política:** voltar a 3 por canal/dia, 12 por dia e 2 h para todos, ou limites por projeto (o hipercool
   precisa de intervalo 0 em canais de língua porque o Studio não agenda lá). Recomendação: piso no código (4/20/1 h) +
   bloco por projeto; o hipercool com 3/dia e 2 h no canal pt.
3. **Quais canais recebem o veo** além de inventoreact/manhwareact e **teto diário na rede toda**.
   **Agora há dado para decidir** (16/10): o diretor da rede avaliou 40 vídeos do veo e deu nota por canal.
   Nenhum tirou nota ≥ 7 nos dois canais permitidos hoje; **35 tirariam ≥ 7 em canais bloqueados**:

   | Canal hoje bloqueado para o veo | Vídeos com nota ≥ 7 |
   |---|---|
   | mundoquenaoexiste | 21 |
   | assistiainvestimentos | 14 |
   | dicasfinanceirasdaia | 14 |

   É por isso que só 1 veo foi postado desde sempre: o estoque está preso em canais onde ele não encaixa.
   Recomendação: liberar **mundoquenaoexiste** (nicho "vídeos de IA, situações absurdas, e se…", é a cara do veo) e
   manter o teto em 2 por dia até haver 10 medições de 48 h. Os dois financeiros só com as `regras` do dono já
   cadastradas (nunca prometer lucro), e só para as personas de finanças.
   Para liberar, basta pôr no `config.json` do manhwa-react (não precisa mexer em código):
   `"rede": {"canais_veo_limpo": ["inventoreact", "manhwareact", "mundoquenaoexiste"], "veo_max_dia": 2}`
4. **Comercial em todo vídeo ou 1 em N?** Recomendação: 1 em 3 por canal, nunca 2 dias seguidos do mesmo produto, e só
   depois de 2 semanas de canal "limpo".
5. **CTA aceitável:** nome do produto + "link no perfil"/pergunta; número e URL só no "Sobre" do canal e no site.
   Número na tela, nem no TikTok (recomendação).
6. **Religar a geração** quando (depois da Onda 1) e com quantas contas por dia; aceitar teste de Chrome headless para
   a tarefa das 7 h.
7. **Commitar a beta** (2.218 linhas) agora, antes de qualquer mudança.
8. **Migrar os canais que ainda sobem pela Data API para o navegador** (login manual de cada perfil) e tirar o projeto
   OAuth compartilhado; e se os tokens existentes podem continuar só para leitura (views, comentários).
9. **Transcrever o áudio com Groq pelo proxy** (áudio vai a um terceiro; ~1 MB de banda por vídeo) como critério
   automático de aprovação, ou só folhas de quadros.
10. **Trilha de fundo** sobre o áudio que o Veo já gera: testar 2–3 amostras antes de ligar.
11. **Importar as 130 fórmulas de julho** da experimental para a memória anti-repetição ou começar limpo.
12. **Multi-fala (3 beats em 30% dos vídeos, ao acaso):** manter até medir ou desligar.
13. **Hipercool no canal pt:** 10 uploads em 15/10, 8 deles em 42 min, e o mesmo recap em 7–8 canais em 13/10 (0–5
    views). Uma suspensão lá para a rede inteira pela parada geral. Recomendação: 1 por canal por dia e 2 h de
    intervalo também para o pt.
14. **A dona continua como protagonista em todas as 25 personas** ou algumas personas saem sem a foto dela (muda AT-06).

---

## 7. O que foi avaliado e descartado

| Ideia | Por que não |
|---|---|
| Aberturas com voz humana (`intros_voz.py`) | só para vídeo longo 16:9; proibido em Shorts verticais (`hipercool CLAUDE.md:387`) |
| Poses/roupas e checagem +18 do `capa_ia.py`, censura visual, `fx_parallax` 2.5D de painel | específicos de painel de manhwa; o veo é vídeo realista de 8 s |
| Teste A/B nativo do Studio e tela final | só vídeo longo; Short não tem tela final (`youtube_studio_extras.py:9`) |
| Link clicável na descrição/comentário do Short | não clicável desde 31/08/2023 (anúncio do YouTube); contato vai no "Sobre" |
| Métricas via `YOUTUBE_API_KEY` (`metrics_client.py`) | regra da dona: nunca criar chave de API; substituído por 48 h + Studio no navegador |
| Copiar `bin\edge_tts_engine.py` do hipercool | legado com Francisca e `hash()`; o certo é `elenco.py` |
| Repostar os 730 do `pos_final` em canais novos | já saíram em canais encerrados: contorno de encerramento |
| Gerador de likes/comentários (MEGA ENGAGE) | engajamento falso; foi um dos gatilhos do banimento |
| Postar pelo `postar_tudo_hoje`/`agendar_vo3` "com limites menores" | mantém round-robin, template e sem declaração de IA; a rede já faz melhor |
| Número de WhatsApp na descrição em vez da tela | continua "redirecionar/contato" em texto; o revisor passa a barrar |

---

## 8. Dados usados e fontes

Dados (16/10/2026, contagens conferidas duas vezes no PC):
- Limpos: 226 jsons e 225 mp4 em `D:\hipercool-materiais\veo\limpos`; em `aprovacoes.json`, 223 entradas desta pasta:
  218 aprovados e 5 rejeitados (3 jsons ainda sem entrada); 1 com `posted_url`; 8 com `revisar`; layouts: 166 cru,
  55 cheio, 4 3:4.
- Catálogo (`config\catalogo_videos.json`, 1.604 itens): veo 1.443; **730 com postagem no YouTube** (canais
  encerrados), 9 no TikTok, 2 no Instagram.
- Fila da rede: 227 aprovados e 8 canais sem vídeo bom em 16/10 05:20; 1 único veo postado até agora (15/10, nota 6,0).
- Ledger (`uploads_ledger.jsonl`, 04–16/10): 149 uploads; pico 22/dia em 14 e 15/10; InovareManhwaVerse 10 em 15/10
  (8 entre 05:27 e 06:09). Pré-banimento (logs do postador): 30/07 102 OK + 31 LIMITE; 24/08 105 OK.
- Aprendizado 48 h (`aprendizado_global.json`, 30 dias): react n=16 mediana 195 views, p75 1.211, 44% passam de 1.000;
  recap hipercool n=8 mediana 1; `medidas_48h` react n=13 mediana 1.106. Nenhuma medida de "veo limpo".
- Geração (log de 12/10): LLM ~19 s; vídeo OK em 3m13s–3m29s; ~20 créditos; 4 OK, 20 timeouts, 4 "sem créditos".
- Áudio do COMPLETO de exemplo: −17,2 LUFS integrado, pico −1,7 dBFS. Pool VO3 real: 8 clipes de 01/08 (1 em 16:9).
- Experimental: 130 fórmulas (25–26/07), 0 views, 0 `posted_url`.

Fontes oficiais (lidas em 16/10/2026):
- Spam, práticas enganosas e golpes: https://support.google.com/youtube/answer/2801973
- Links externos: https://support.google.com/youtube/answer/9054257 · Engajamento falso: https://support.google.com/youtube/answer/3399767
- Encerramento de canal e contorno: https://support.google.com/youtube/answer/2802168
- Divulgação de conteúdo alterado ou sintético: https://support.google.com/youtube/answer/14328491 e
  https://blog.youtube/news-and-events/disclosing-ai-generated-content/ (rótulo em sobreposição nos Shorts:
  https://blog.google/intl/en-in/products/platforms/improving-ai-labels-for-viewers-and-creators/)
- Políticas de monetização / conteúdo inautêntico (15/07/2025): https://support.google.com/youtube/answer/1311392
- Veo 3.1 e Flow (Ingredients, Frames, Extend; 15/10/2025): https://blog.google/technology/ai/veo-updates-flow/
- Créditos do Flow (Fast 20, Quality 100; Pro 1.000/mês): https://9to5google.com/2025/06/09/gemini-veo-3-fast/
- Links de Shorts não clicáveis (31/08/2023): https://www.tubefilter.com/2023/08/10/youtube-shorts-comments-spam/

Documentos locais: `D:\postador-de-videos\LEIA.txt`, `SPAM_BANIMENTO_2026-09-04.md`, `CONTESTACAO_YOUTUBE_2026-09-22.md`;
`D:\manhwa-react\CLAUDE.md`, `HANDOFF_REDE.md`, `REDE_ESTADO_E_PENDENCIAS.md`; `D:\hipercool-videos\CLAUDE.md`,
`docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md`, `docs\PEDIDOS_DO_DONO_PENDENTES.md`; `D:\veo\beta\*.md`,
`pos_producao\*.md`. Material bruto desta auditoria em `D:\veo\docs\auditoria_2026-10-15\`: os 4 mapas de leitura
(`ler_geracao.json`, `ler_postagem_banimento.json`, `ler_manhwa_react.json`, `ler_hipercool.json`, cada um com fatos,
problemas e oportunidades com caminho:linha) e as folhas de quadros conferidas (`completo_sheet.png`, `limpo_sheet.png`,
`vo3_real_sheet.png`, e os dois quadros do slide de WhatsApp e do cartão final).

---

## 9. Para o próximo agente

1. Leia `D:\veo\CLAUDE.md`, este plano e `docs\LEVANTAMENTO_2026-10-15.md`. Não religue nada antes da Onda 0.
2. Cada item: faça, **valide de verdade** (render real, quadros extraídos e vistos, ffprobe, log), e marque no
   "Registro" abaixo com data, commit e o que foi conferido.
3. Mudou procedimento, botão ou caminho? Atualize o `CLAUDE.md` da raiz.
4. Decisão da dona pendente? Não adivinhe: faça o resto e deixe o item marcado como "aguarda decisão N".
5. Segredos (cofre, `secrets\`, chaves) nunca em documento, commit ou chat.

## Registro

| Data | Item | O que foi feito | Validado como |
|---|---|---|---|
| 15/10/2026 | — | Levantamento, `CLAUDE.md` da raiz, primeira versão deste plano | leitura de código, quadros extraídos dos vídeos, contagens |
| 16/10/2026 | — | Verificação adversarial de 37 evidências por 3 revisores independentes; correções incorporadas | ver abaixo |
| 16/10/2026 | AB-03 | `pos_producao\config.yaml`: pipeline passou a ser só loudnorm + crop + legendas; propaganda e marca saíram | vídeo de teste renderizado e quadros vistos: sem marca, sem slide, sem cartão final |
| 16/10/2026 | IM-01 | `cta_card.py` sem telefone, sem URL e sem "OFERECIDO POR"; layout v5 (o bump invalida os 88 cards em cache, que tinham o número); contato só com `contato="..."`, que ninguém passa | 3 cards gerados e olhados: só nome, benefício e "LINK NO PERFIL" |
| 16/10/2026 | IM-01 | `cta_builder._narracao_cta`: a voz não diz mais "Chama no WhatsApp que tá na tela", e o **texto entrou na chave do cache** (era só produto+voz, então os 38 áudios antigos continuariam falando o número) | texto conferido para os 4 produtos top |
| 16/10/2026 | IM-01 | `plugins\propaganda_inteligente.py`: número saiu do slide e da fala; `plugins\branding_watermark.py` e `assets\branding.json` sem "@InovareStories" (estava escrito no código também) | greps limpos; plugin devolve o vídeo intacto com a config vazia |
| 16/10/2026 | IM-03 | Vozes proibidas trocadas pelas edge Multilingual aprovadas em `edge_tts_veo.py`, `voz_config.json`, `_tts_helper.py`, `voz_whatsapp.py`; 120 vozes virtuais, voz fixa por md5, voz proibida levanta erro | banco e recusa testados; **áudio real não pôde ser gerado: o serviço edge-tts responde 403 direto e timeout por proxy — falha anterior à mudança (a voz antiga também falha)** |
| 16/10/2026 | AB-06 | `roteamento.py` reescrito: sem os 18 handles suspensos, sem `hash()`, sem o `or True`; devolve `[]` para o diretor da rede decidir. `_DIRETO`/`_POOL_HUMOR` ficaram vazios só para não quebrar a tarefa `AgendadorVO3` | rodado 2x com resultado igual; lista os 12 canais ativos da rede |
| 16/10/2026 | AB-06 | `publicar.py`: sem "1-2 emojis", sem "5 hashtags", sem `👉 CTA`, sem a cauda "#shorts #ia #viral #brasil"; filtro que apaga telefone, link, @ e convite a sair do YouTube (mantendo o nome do produto); grava `<vídeo>.postar.json` e marca `"sintetico": true` | filtro testado em 6 frases; fallback conferido |
| 16/10/2026 | extra | **Defeito antigo corrigido:** `plugins\crop_9_16.py` emoldurava antes de escalar quando o vídeo já era 9:16 (todo clipe do Veo), deixando o conteúdo num quadrinho com ~45% da tela em preto | quadros antes e depois comparados: agora preenche a tela |
| 16/10/2026 | Onda 0 | Commit `a1cee7e` (14 arquivos, +518/−254), **juntado no `main`** por avanço direto. **Nada foi enviado ao GitHub** (o remoto `fabricadeautomacoesia/veo-beta` continua no commit de 31/07). O branch `pc/onda0-antibanimento` pode ser apagado | `git log`, `validate.py` verde |
| 16/10/2026 | infra | **Groq voltou a funcionar**: a dona mandou 39 proxies novos (total 50 em `secrets\proxies.txt`, backup `.bkp_20261016`). Transcrição passou de 15–22 s no modelo local para **5,8 s** no `whisper-large-v3`. As 9 chaves que ela mandou já estavam no arquivo | transcrição real de um clipe de 8 s |
| 16/10/2026 | infra | **Voz destravada**: o 403 não era proxy, era a versão da biblioteca. `edge-tts` do venv do veo subiu de **7.2.8 para 7.3.1**, a mesma que o hipercool usa em produção | áudio real gerado, 5,93 s, voz Thalita |
| 16/10/2026 | AT-02 | `validar_video.py` novo (9:16 por proporção, duração, áudio, codec de imagem disfarçado, quadro preto e congelado, volume opcional) e **plugado como porteiro no `run()`**, antes de registrar, copiar, gerar thumb e escrever o `postar.json`. Reprovado vai para `videos\rejeitados\` com o motivo, e a escada tenta outro prompt | aprovou bruto real de 8 s; reprovou vídeo de 15,4 s e arquivo de 500 bytes |
| 16/10/2026 | AT-01 | `conferir_fala.py` novo: transcreve e compara o que foi **ouvido** com o que foi **pedido**, por trigramas. Não dá para usar o campo de idioma: `mr\transcribe.py:119` devolve o idioma que você pediu, não o que detectou. Se não der para transcrever, **não reprova** | fala certa deu 1,00; fala trocada deu 0,31 e reprovou; áudio em inglês dá 0,00 |
| 16/10/2026 | AT-04 | Dedupe de fala antes de gastar crédito, comparando com **todo** o histórico (não só o mesmo tema). Limiar 0,62, calibrado nas 132 falas existentes (entre falas diferentes: mediana 0,12 e p95 0,35; repetições reais: 0,82–0,89). Se repetir, pede outra; se insistir, passa com aviso | repetidas pegas em 1,00; falas novas passaram |
| 16/10/2026 | AT-04 | 130 falas antigas importadas para `beta\logs\falas_historicas.json` — arquivo **só de memória**, sem caminho de vídeo, para nenhum postador confundir com fila | dedupe passou a enxergar 132 falas |
| 16/10/2026 | DS-01 | Na rede (`D:\manhwa-react\mr\rede.py`, backup `.bkp_20261016`): o veo passou a receber **nota do diretor** restrita aos canais autorizados, em vez de nota fixa; `veo_max_fila` (40) evita 12 chamadas de LLM por rodada com 227 na fila; `veo_max_dia` (2) limita o veo na rede inteira | `manhwareact.py rede --simular`: 4 vídeos, 1 deles veo pelo diretor no InventoReact |
| 16/10/2026 | DS-02 | Revisor da rede passou a barrar telefone, site, @, "chama no zap" e "link na bio" em título, descrição, comentário e tags. Link do **próprio YouTube** é permitido | 6 casos testados; falso positivo achado na 1ª simulação (link de vídeo do YouTube) e corrigido |
| 16/10/2026 | AT-05 (quebrados) | Eram **28**, não 27 (faltava `transformacao_20260727_062012`). Os 28 json em `veo\limpos` com `revisar: "arquivo quebrado..."` + `decodifica: false` | `rede.inventario` real: 0 dos 28 na disputa nem na espera |
| 16/10/2026 | 3.3 (teto por dia) | **Teto de UPLOADS do Veo por canal por dia** em `mr\rede.py` (`veo_uploads_dia`, 0 = degrau da `veo_rampa`, hoje 3), contado no ledger pela hora do upload. Motivo: o Veo dos 3 dias adiantados subiu 8 por canal em 16/10, o YouTube cortou (`uploadLimitExceeded`) e o react do dono das 18:53 e o completo das 20:40 do ManhwaReact **não subiram** | `rede --simular` às 19:00: os 7 Veo pendentes ficaram "teto de 3 uploads hoje"; só o react e o completo seguiram para o ManhwaReact |
| 16/10/2026 | fluxo Veo novo | O gerador religado grava em `beta\videos\cron_shorts`, mas o `limpar_veo` só lia `veo_videos_iniciais` (último de 25/08): **nenhum Veo novo chegava na rede**. `limpar_veo.py` lê `NOVOS` (menos `teste*`) e `manhwa-react\scripts\rede_hora_em_hora.bat` roda `limpar_veo --max 3` antes da rede | 3 novos limpos de verdade; sem novo, o passo leva 0,4 s |
| 16/10/2026 | AB-09 (marca Grok) | Os 3 Veo novos foram barrados por **marca do Grok** — vem da FOTO de entrada. `beta\separar_fotos_marcadas.py`: **298 das 305 fotos** de `D:\veo\fotos` têm marca (292 Grok, 5 Meta AI, 1 OpenAI). **Não movidas** (sobrariam 6); decisão da dona: fotos novas sem marca | amostra de 9 cantos vista no olho: marca em todas as Grok; quadro do vídeo de 16/10 com "Grok" no canto |
| 16/10/2026 | AT-09 | **Legenda pelo áudio** (o plano geral chamou de AT-03 por engano; o AT-03, métricas, NÃO foi feito): `limpar_veo.legendar` queima a legenda palavra a palavra com `mr\captions.build_ass` (só legenda; 78% da altura, abaixo do queixo) nos limpos aprovados, depois dos detectores | quadros de um teste: sincronizada com a fala (começa em 2,6 s), boca livre; `decodifica` ok |
| 16/10/2026 | vozes (3.2) | Postador: a troca das proibidas já existia DENTRO de `edge_tts_engine._generate_edge_tts` (única chamada ao edge); a que a Onda 1 pôs na entrada de `speak()` foi **retirada** (atropelava a marca "Antonio" que manda voz masculina ao Gemini primeiro). `test_all_voices.py` chamava o edge direto: passou pela mesma troca. `curadoria.py` usa `speak()` → coberto | `py_compile` + import; só 1 `Communicate(` no motor, depois da troca |
| 16/10/2026 | telefone no git (3.2) | O número estava em **5** arquivos versionados (não só `produtos.json`): + `voz_config.json`, `propaganda_inteligente.py`, `propaganda_pool_pre_gerada.py`, `voz_whatsapp.py`. Trocado por `{whatsapp}`; o número foi para `beta\secrets\contato.json` (ignorado). `voz_whatsapp._numero()` lê de lá e, sem ele, o plugin não roda. **Sem commit** (há mudanças de outra sessão no mesmo repositório) e o número **continua no histórico** (`a1cee7e` e anteriores; o remoto está em 31/07): decisão da dona antes de qualquer push | `git grep` e grep nos não versionados: 0; frase montada com o número e sem marcador |
| 16/10/2026 | filtro de contato (3.2) | `mr\rede.py` `PROIBIDO_CONTATO`: telefone só em formato BR (celular 9XXXX-XXXX ou DDD + 8/9 dígitos, +55 opcional); convite aceita até 3 palavras entre o verbo e o "no" (+ segue/siga/entra/vem/clica; + whats/wpp/pv/dm/tiktok/kwai); domínios + ly/link/site/org/info/gg. Casos em `D:\manhwa-react\testes\teste_filtro_contato.py` | antes: 14 falhas em 33 casos (7 textos limpos barrados, 7 convites passando); depois: 0, e 0 barrados em 211 textos publicados + 438 metas da rede |
| 16/10/2026 | BX-03 | `beta\trava_render.py`: um render do veo por vez — arquivo criado de forma atômica (O_EXCL), reentrante no mesmo processo, abandonada após 90 min. `montar_final.montar` (cobre worker_noite, blitz_*, driver_noite) espera até 30 min; `limpar_veo` não espera (sai e a próxima rodada tenta) e nem pega a trava quando não há pendente | 2 processos reais: B "ocupado" na hora, C entrou após 10 s de espera, reentrância ok, trava apagada no fim; `limpar_veo` sem pendente 0,5 s |
| 16/10/2026 | AB-10 | `notificar_telegram.checar_ritmo` (entra no `avisos_projetos`, a cada ~30 min): canal com > 5 uploads no dia, rajada de 3+ uploads em 1 h, 2 vídeos publicando com < 1 h (ignora os retirados de `rede_retirados.json`), recusa do YouTube (limite/cota/morto/suspenso) por canal — 2+ canais sugere PARADO.json, **não cria sozinho** —, política acima do piso (4/20/1 h). Avisa 1 vez por ocorrência por dia | dados reais de 16/10 com `enviar` trocado por print: 7 avisos (8 uploads em InventoReact e ManhwaReact-ia, rajadas às 01:52 InovareManhwaVerse e 11:37 nos 2 do Veo, limite nos 2, política 10/50/0 h); 2ª rodada não repete. Falso alarme de "mesmo horário" achado e corrigido (vídeo retirado e reposto) |
| 16/10/2026 | BX-02 | `beta\sem_janela.py` (cópia do hipercool) importado no topo de `cron_gerar_video_llm.py`, `loop_cron.py`, `cron_pos_producao.py`, `pos_producao\worker_noite.py` (o `supervisor.py` não está no beta: fica em `D:\veo\supervisor.py` — recebeu o import às 23:20, ver linha abaixo). `sistema_pausado()`: com `SKIP_RESOURCE_CHECK=1` o modo paralelo só pula a pausa de **carga**; a manual e a de bloqueio valem (antes nem lia o arquivo). `loop_cron` **dorme 5 min** enquanto pausado em vez de chamar `run()` e abortar a cada 30 s | `py_compile` dos 5; `Popen._sem_janela` ativo no import; PAUSE_SYSTEM de teste: paralelo + manual = pausado, paralelo + carga = não (arquivo apagado depois) |
| 16/10/2026 | AT-12 (parcial) | `cron_gerar_video_llm.gerar_video`: timeout = no mínimo `GEN_TIMEOUT_S` + 120 + 60 = **1.980 s** (o worker só desiste em 1.920; antes o cron matava em 1.200 e contava falha da conta); saída inteira do worker em `logs\worker_<FLOW_SESSION>_<ts>.log`, inclusive no TIMEOUT. **Não feito:** "pro só reabre com saldo ≥ 20 lido de novo" — o worker já lê o saldo ANTES de gerar e sai com código 2 sem gastar se < 20 (`gera_auto.py:718-733`), então reabrir à meia-noite custa 1 checagem, não crédito; estado de sessão separado do MS Energy fica para a decisão com o MS Energy | `py_compile`; worker falso (rc 9): log gravado com rc, stdout e stderr (apagado depois) |
| 16/10/2026 | 3.3 (fala_repetida) | A FALHA TOTAL grava a fórmula no cache com `video_path` None e devolve o prompt à fila; o ciclo seguinte achava a própria fala (1,0) e descartava o prompt pago. `fala_repetida` só compara com o que virou vídeo (+ as históricas) | cache simulado: fala de falha não barra mais; fala de vídeo feito continua barrada (1,0) |
| 16/10/2026 | 3.3 (chave da validação) | A decodificação completa (a que pega os quebrados) estava DENTRO de `checar_imagem`: desligar preto/congelado desligava ela junto. Agora roda sempre; `VEO_VALIDAR_IMAGEM=0` no cron desliga só preto/congelado (`VEO_VALIDAR=0` e `VEO_CONFERIR_FALA=0` seguem como antes) | `transformacao_20260727_062012` reprovado com `checar_imagem=False` ("Invalid NAL unit size"); o bom passa nos dois modos |
| 16/10/2026 | AB-02 | Dono aprovou 4/canal/dia, 20/dia, 1 h. `politica.PISO` no código: o json só aperta (null/0/maior vira o piso); `politica.json` 4/20/1. `horario_publicacao`: 1 h do VIZINHO mais próximo, não depois do ÚLTIMO agendado (o Veo agenda 2 dias à frente: com 1 h o react de hoje ia para depois de amanhã). Rede: o Veo fica com o que sobra depois do react (`max_dia`) e do completo (`grandes\<slug>`) → **2 por canal** (a `veo_rampa` de 23/10 e 30/10 fica limitada a isso enquanto o piso for 4) | `politica()` = 4/20/1 com o json antigo 10/50/0; pedido 21:43 (15 min de outro) → 22:58 (antes ia a 17/10 22:50); `rede --simular` 20:03: Veo "teto de 2 uploads hoje", react e completo do ManhwaReact no plano |
| 16/10/2026 | BX-01 + telefone no histórico | Dono aprovou commit e limpeza. Backup antes: `D:\veo\_backup_git_beta_20261016.bundle` (verificado, 3 branches; **contém o número** — fica só no disco). Commit da Onda 2 (37 arquivos revisados: sem chave/senha/número; fora: `videos_pos` 11 GB, `cache_pexels`, `.bkp`, `_test_*`, `LEIA_PERFIS_E_COFRE.md`). `git filter-branch --tree-filter` nos 6 commits dos 3 branches trocou "91 984698653"/"91 98469-8653" por `{whatsapp}`; refs/original, reflog e gc apagados. **Hashes mudaram**: Onda 0 `a1cee7e`→`2b6dc33`, Onda 1 `8ad167a`→`c7dadb7`, Onda 2 `43c2a14`. O remoto (GitHub, de 31/07) dá 404 de fora = privado; um push agora exige `--force` (decisão do dono) | `git log --all -p`: 0 ocorrências; `git grep` em todos os commits: 0; `fsck --unreachable`: 0 |
| 16/10/2026 | AT-06 + fotos com marca | Dono: todas as 25 personas são ele, com as fotos dele; fotos sem marca. `escolher_foto(canal)`: subpasta por persona (`FOTOS_POR_PERSONA`: comedia/epocas/jornal/herois; resto e sem foto limpa → raiz); **nunca** foto com marca do relatório `logs\marcas_fotos.json` (`_fotos_com_marca`), nem na "foto inteligente" nem no item vindo da fila (troca); sem foto limpa **não gera** (não gasta crédito num vídeo que a rede barra). Separador nas 638: **limpas** épocas 157, guerra 64, heróis 50, raiz 6; comédia 0/30 e jornal 0/6 todas com marca. Persona sem foto limpa no tema → qualquer foto limpa do dono (277); "E Se..." = épocas + guerra | 200 escolhas (5 personas × 40): 0 com marca, 26–39 fotos distintas por persona; Motivação só em heróis |
| 16/10/2026 | fotos novas (teste) | Gerar "o dono em cena nova" pelo gateway NÃO funciona: `antigravity/gemini-3.1-flash-image` só aceita `/v1/images/generations` (texto); o campo `image` com a foto de referência é ignorado — saiu outro homem (cabelo, rosto e idade diferentes, 1024x1024). Caminhos que sobram (decisão do dono): fotos reais novas dele, ou recortar a faixa de baixo das fotos do Grok (onde fica a marca), com o vídeo seguindo declarado como IA | 1 imagem gerada com a foto `epocas/203736f7…` de referência, comparada lado a lado |
| 16/10/2026 | DS-05 (rede) | `postador\bin\extras_rede.py` (padrão do hipercool): Short de react público ganha "vídeo relacionado" = completo público mais recente do mesmo canal; repete pendente a cada 3 h, desiste após 5 avisos; estado `config\extras_rede.json`. Entrou na tarefa `ManhwaReact-Rede` depois da rede, 2 por rodada (dono aprovou) | `--ensaio`: 7 Shorts do InventoReact → completo `wKiGkUQ6bBc` |
| 16/10/2026 | AB-11 (rampa por dado) | `mr\rede._veo_por_dia`: subir além do 1º degrau da `veo_rampa` exige `_veo_rende` — mediana de views 48 h da origem "veo limpo" no `aprendizado_global.json` (≥ 5 vídeos, medido pelo `notificar_telegram.medir_48h`) ≥ mediana dos canais do Veo; sem dado fica no 1º (3). Hoje o piso da política ainda limita o Veo a 2/canal | sem dado: 16/10, 24/10 e 31/10 → 3; dado simulado (Veo 900 x canais 500/3) → 31/10 = 5 |
| 16/10/2026 | AB-12 | `wKiGkUQ6bBc` (completo do InventoReact, 13/10): página do vídeo = **"Este vídeo foi removido por ser muito longo"** (31 min de react num canal SEM a verificação por telefone, limite 15 min) — não é violação. O Studio também recusa "vídeo relacionado" no canal pelo mesmo motivo. `rede_canais.json` (backup `.bkp_20261016`): `inventoreact.verificado = false` + nota; a rede não manda completo > 15 min a canal `verificado: false`. `mr\publish.comentarios_pendentes`: 404 confirmado pelo oEmbed desiste na hora; vídeo de `rede_retirados.json` não é comentado. `extras_rede`: alvo só se o oEmbed diz no ar; canal "bloqueado" não é tentado de novo. **Dono:** verificar o InventoReact por telefone; conferir se o ManhwaReact é verificado (o completo pendente dele tem 31 min) | oEmbed: wKiGkUQ6bBc 404, GIFfxhU107c 403 (retirado), PKGOIGHQL_4 200; `_fora_do_ar` True/False/False; `extras_rede --ensaio` sem alvo removido |
| 16/10/2026 | AB-04 (resto) | `catalogo.legenda_reuso(v)`: Veo → a FALA do limpo + "Vídeo feito com IA."; react/historias → o título que o agente da rede escreveu (publicados.json pelo id do YouTube); senão o tema. Tira #fyp/#foryou/#viral/#shorts/#reels/#trending. TikTok (`postar_tiktok_auto` → `tiktok_cdp_poster --desc`, numa linha) e Instagram (`postar_insta_auto.legenda`). Lista de reserva do TikTok sem #viral/#fyp. **Defeito antigo corrigido:** `post_one_subprocess` colava a legenda num código Python entre aspas simples (apóstrofo/quebra de linha quebrava) → `repr()`; conferência do texto ignora qualquer espaço; `import re` que faltava | prévia das 3 origens; código gerado com aspas + quebra de linha volta igual (`ast`); `postar_tiktok_auto --simular` e `postar_insta_auto --simular` sem erro (Instagram sobe o limpo `cru` aprovado) |
| 16/10/2026 | AT-10 | `limpar_veo`: volume em 2 passos −14 LUFS / −1 dBTP (`loudnorm_filtro`, copiado de `mr\audio.loudnorm_two_pass`) nos aprovados — junto da legenda na MESMA recodificação; sem legenda, só o áudio (`nivelar`, vídeo copiado); `volume` no json. **Trilha de fundo: não** (decisão 10 delegada pelo dono: o Veo já gera som e fala; sem dado de que ajude) | Veo novo do gerador medido em −20,9 LUFS; teste: −14,4 → −14,1 LUFS, pico −1,0 dBFS, `decodifica` ok |
| 16/10/2026 | DS-06 (conferido) | `catalogo.PASTAS` cobre brutos, `beta\videos` (inclui o `cron_shorts` novo), `pos_final\completo`, `_postados\vo3` e `work\rede_marca` (o arquivo que SOBE: `veo_<clipe>__<canal>.mp4`, com backup). `veo\limpos` fica de fora DE PROPÓSITO: é a fila da rede e a fonte do TikTok/Insta (`catalogo.versao_limpa` precisa dele no PC); o postado fica marcado (`posted_url`, 17 hoje) e a rede nunca reposta. Regra do dono: fila não se limpa | leitura de `catalogo.py`/`backup_drive.py` e contagem dos `posted_url` |
| 16/10/2026 | DS-03 | `beta\seo_palavras_veo.py`: banco do autocompletar PÚBLICO do YouTube (suggestqueries, sem chave) por tema do arquivo (23 temas, ~15 palavras cada, sem nome de música) → `logs\seo_palavras_veo.json`; rodar 1x/semana. `mr\rede.adaptar`: clipe do Veo leva `palavras_buscadas` do seu tema ao agente, com a instrução de usar 1–2 que combinem de verdade. (Medir o estilo vem do aprendizado da rede, que já mede título por Thompson) | chamada real às 20:31 (cache novo): vendas_com_ia → título "ASSISTENTE IA vende sozinho no WhatsApp 24h", tags com "vender no whatsapp" e "whatsapp business" |
| 16/10/2026 | AT-08 (a) | `agents.prompt_com_fala` (usado no pipeline e no caminho de reserva do cron): fala entre aspas DUPLAS depois de `saying:`, aspas da fala trocadas por simples, "9:16 vertical portrait." e "No subtitles, no captions, no on-screen text." acrescentados só se faltarem. (b) Ingredients to Video e (c) Extend ficam para teste com crédito | 3 cenários (sem marcador, já com "sem texto", já com 9:16): saída certa nos 3; `py_compile` |
| 16/10/2026 | BX-07 | `beta\sonda_contas_veo.py`: 1x/dia (etapa 5 do `postar_tudo_auto.bat`, 15 min de prazo), sem gerar: cada sessão de `contas.py` → conta do cofre pela junção do perfil → `cofre.checar` (Chrome fora da tela, myaccount). Morta → cooldown 24 h em `sessoes_status.json` (o gerador pula) + "DESLOGADA: x" no log → aviso no Telegram (`ALERTAS_LOG`); viva → tira o cooldown que a sonda pôs. Chrome da sessão aberto (gerando) → próxima. (Estado de sessão separado do MS Energy segue para decisão com o MS Energy) | rodada real 20:57: seebotsia, mundosolar1995, canalalucinaai = vivo; formatação do aviso testada |
| 16/10/2026 | DS-04 / Onda 3.1 (rede) | 1ª leitura REAL do leitor do Studio num Short (CenaReact `ulImyjbO86w`): rótulos de Short acertados em `youtube_studio_extras.metricas` — `continuaram` ("Continuaram assistindo" = % que não deslizou), `intencionais`, views exatas da frase do topo (espaço não separável). `postador\bin\metricas_rede.py`: vídeos da rede de 48 h a 21 dias, relê a cada 72 h, 1 sessão de Chrome por canal; decide 1x por vídeo com ≥ 3 do canal: Short → `continuaram`/mediana vira nota do braço do **gancho**; completo → CTR/mediana (≥ 100 impressões) vira nota do **título**, em `_analise\rede_aprendizado.json` (o que a rede lê). Na tarefa `ManhwaReact-Rede`, 3 por rodada. Dados em `_analise\metricas_studio.json` | rodada real 22:07: 4 do CenaReact — 2 completos (52,7% / 631 intencionais / 16 s; 43,2% / 525 / 24 s), 1 com 18 views (sem retenção ainda), 1 sem dado (Studio "—", print conferido); decidir com dados simulados: notas 1,2/1,0/0,8, sem duplicar |
| 16/10/2026 | AT-03 | Laço do gerador fechado sem chave de API: `metricas_rede.alimentar_veo` grava o número real do Studio (views, continuaram, intencionais, duração, `posted_url`) em `metrics` da fórmula do `video_cache.json` (mesmo nome de arquivo do limpo), 1x por leitura. `cron_gerar_video_llm._auto_fetch_metricas` não chama mais o `metrics_client` (dependia de `YOUTUBE_API_KEY`, proibida, e devolvia vazio em silêncio); só reanalisa padrões quando há número real; `fetch` aponta para o `metricas_rede`. Commit `ddc2c57` | cache simulado: 1 fórmula atualizada, 2ª vez 0; `_auto_fetch_metricas()` roda sem o metrics_client |
| 16/10/2026 | BX-04 (validate) | `validate.py` cobre os 8 módulos novos (validar_video, conferir_fala, dedupe_video, trava_render, sem_janela, sonda_contas_veo, seo_palavras_veo, separar_fotos_marcadas) e ganhou a etapa 3 de comportamento: prompt com "sem texto na tela"/9:16/aspas, `escolher_foto` nunca com marca, `sistema_pausado` responde, trava cria e apaga, dedupe(x,x)=1. Commits `549bc76`, `55a63d3`. (Código morto e arquivar `experimental\` seguem pendentes) | `python validate.py`: 20 módulos OK, 3 contas consistentes, 5 comportamentos OK |
| 16/10/2026 | BX-06 | `README.md` e `TUTORIAL_AGENTE.md`: venv certo (`D:/veo/venv`, não o do hipercool) e pasta certa (`D:\veo\beta`; `roteador-veo-api-fake` não existe), com o ponto de entrada (CLAUDE.md, CONTINUAR_DAQUI, `validate.py`). `ARQUITETURA.md`: fluxo real depois do mp4 (porteiro → limpar_veo na tarefa da rede → rede → métricas pelo Studio → cache) e os estados novos em `logs\`. Commit `94d0a10` | grep: nenhuma referência ao venv/pasta errados |
| 16/10/2026 | AB-09 (folhas) | `manhwareact.py rede --aprovar` gera no início as folhas de quadros do lote (`testes\folhas_quadros.py`, que ninguém chamava: 5 quadros × 3 vídeos por folha, mesma numeração das perguntas) em `work\folhas_aprovar\<data>\` e abre a 1ª — aprovar olhando, não no escuro. (A outra metade do AB-09, detector de marca de IA, já estava no `limpar_veo.marca_ia`) | lote de 3 limpos reais: `folha_01.jpg` gerada e vista (3 linhas numeradas, 5 quadros, título e duração); abertura da folha e do vídeo conferida sem abrir janela |
| 16/10/2026 | VO-04/VO-05 (comercial 1 em 3) | Dono: "sim, com cuidado". `postador\bin\comercial_veo.py`: no TikTok/Instagram, quando as últimas 2 postagens do Veo da conta foram limpas, a próxima vai COM propaganda montada na hora do LIMPO aprovado (`montar_final`, card **v6**: nome + benefício + "LINK NO PERFIL"; voz "…o link está no perfil"); produto nunca repete o último comercial da conta; **checagem por visão** em 3 quadros do fim (telefone/URL/@/QR) — qualquer "sim" ou falha → posta o limpo. Arquivo no `cache_reuso` (apagado depois). Ligado em `reuso_plataformas.json` → `veo_comercial` {ligado, a_cada: 3} (backup `.bkp_20261016_comercial`); logs gravam `tipo`/`formato`/`produto`. YouTube nunca. **cta_card v6:** benefício em branco com contorno (sumia verde sobre verde) | 2 amostras renderizadas e vistas em quadros; fala transcrita sem número; checagem: amostra limpa = ok, mesma amostra com "WhatsApp (11) 91234-5678" desenhado = barrada; ponta a ponta sem postar (histórico simulado): comercial avatar_ia montado, checado e apagado do cache |
| 16/10/2026 | VO-01 (parte) | `hermes_call_1.mp4` (1280x720) saiu da pasta 9:16 para `vo3_lateral\`; `vo3_propaganda_rotator` só escolhe clipe cuja orientação bate (`_orientacao_ok`, ffprobe). Commit `5462220`. (O comercial 1 em 3 não usa esse pool: `com_vo3_propaganda=False`.) Falta: ≥ 3 clipes por produto top, regenerados com o prompt do VO-02 | pool 9:16 do hermes = 3 clipes em pé; 16:9 = o deitado |
| 16/10/2026 | VO-02 (prompt) | `vo3_propaganda_rotator.montar_prompt`: os dois caminhos (agentes e reserva) terminam com "No subtitles, no captions, no on-screen text"; a reserva não pede mais o nome do produto escrito na tela (o Veo erra texto; o nome entra pelo card). Commit `2e215ae`. (Ingredients to Video com a imagem do produto fica para teste com crédito) | prompt de reserva gerado e lido |
| 16/10/2026 | VO-03 + foto da propaganda | `vo3_propaganda_rotator.gerar_um`: clipe gerado passa por `validar_video` (8 s) e `conferir_fala` contra a fala entre aspas do prompt; reprovado é apagado e não entra no pool. `_escolher_foto`: raiz + subpastas, sem as bloqueadas e **sem as com marca de IA** (antes só a raiz: 299/305 com "Grok"); sem como saber as marcadas → não gera | 30 escolhas: 0 com marca, 29 distintas; `py_compile` (a conferência roda na próxima geração real) |
| 16/10/2026 | VO-06 | `vo3_propaganda_rotator._CONTAS_PROPAGANDA` lê o `contas.py` (`papel: "propaganda"`, senão as sessões ativas); a lista fixa tinha 4 contas que não existem mais (cairiam na porta da seebotsia com perfil errado). Commit `e8c1d4c` | resolve seebotsia/mundosolar/canalalucinaai nas portas 9250/9260/9270 |
| 16/10/2026 | IM-05 | `cta_card.gerar_card`: além do visual (`_VARIANTES`), o texto do benefício varia com a variante — `cta_curto` ou a 1ª frase do `cta_longo` se ≤ 52 caracteres e sem dígitos longos/@/link/`{marcador}`. Commit | prévia dos 9 produtos: 6 com 2 textos, 3 com 1; nenhum com contato |
| 16/10/2026 | IM-02 (conferido) + AT-10 | O slide do card JÁ é animado (`cta_builder._slide_clip`: zoompan lento até 1,08 + fade de entrada/saída); texto animado tipo HyperFrames fica para depois. Slide passou de −16 para **−14 LUFS / −1 dBTP**, igual ao limpo (o volume caía na hora da propaganda) | `py_compile`; filtro lido |
| 16/10/2026 | comentários da rede pelo navegador | Os comentários da rede pela API falhavam com **403 de permissão** 21x/dia nos 2 canais do Veo (e 4 do Inovare Ind ficaram em erro). `mr\publish.comentarios_pendentes`: 403 "insufficient" (vídeo no ar) → `comentario = "navegador"` e para de repetir. `extras_rede`: esses (e os "erro: 403 insufficient" antigos) são comentados **e fixados pelo Studio**; bloqueio do Studio agora é por ação (canal bloqueado para "relacionado" continua comentando); "comentário postado, fixar depois da verificação" conta como feito. `youtube_studio_extras._fechar_dialogo`: janela com botão que não era "ok/entendi" travava 30 s — aceita OK/Entendi/Continuar/Comentar/Fechar, 5 s, e loga o texto da janela (backup `.bkp_20261016_dialogo`) | 1ª tentativa real: timeout na janela (print em branco); depois da correção: `qMCPpRURUtw` → "comentário postado; fixar libera depois da verificação do canal", sem duplicar (acha pelo texto) |
| 16/10/2026 | Onda 4.1 (worker comum) | `postador\bin\workers.py` (generaliza o `pc2.py` do hipercool): `livre` (desktop: OBS fechado = dono não está gravando, CPU ≤ 50%; PC2 só leitura, regra do dono), `enviar`/`baixar` por tar no ssh, `sincronizar` (só o que mudou), `disparar` (processo desligado da sessão via `Win32_Process.Create`), `esperar` (`Wait-Process` lá, 1 conexão), 2 falhas → pausa 6 h, 3 s entre conexões. **Problema do desktop:** depois de CADA job o OpenSSH 7.7 de lá recusa toda conexão por ~10 min (3 vezes; não é o nº de conexões) → `descansar`: 12 min de folga após o job. **Dono:** atualizar o OpenSSH Server do desktop | 2 idas e voltas reais: livre → copiou → rodou desligado ("rodou") → acabou → trouxe "ok de DESKTOP-SU00B7V"; folga conferida |
| 16/10/2026 | capa pelo navegador | `mr\rede.py`: a capa do react/historias e do completo vai NO upload pelo navegador (`politica.postar_youtube(thumbnail=)`); saiu o `PB._thumbnail` (API `thumbnails.set`) depois do upload — ordem do dono 16/10: nada pela API | `py_compile`; nenhuma chamada `_thumbnail(yp` restante na rede; o web poster sobe sem capa se ela falhar |
| 16/10/2026 | AB-05 | `youtube_web_poster._conferir_detalhes`: vídeo **sintético** sem a opção "conteúdo alterado (IA)" marcada tenta marcar 1x mais e, se continuar desmarcada, **falha** (não sobe) — era a única conferência que só avisava. A rede passa `sintetico` (Veo/historias) e o hipercool passa True | upload REAL em ensaio (rascunho privado) no historiasemframes: "detalhes preenchidos e conferidos" → a opção é detectada marcada. **Incidente:** para apagar o rascunho rodei `--limpar-rascunhos`, que apaga TODO rascunho preso do canal: foi junto um antigo, "Aulas IA - Micro-aulas e Tutoriais #shorts" (upload travado, nunca publicado; irreversível). O de teste (`DwzlNTVpHEM`) não era listado como rascunho e foi apagado por um script que confere título E id. **Regra:** listar com `--limpar-rascunhos --ensaio` antes de apagar |
| 16/10/2026 | BX-02 (supervisor) + BX-04 (experimental) | `D:\veo\supervisor.py` (raiz, fora do git do beta) importa `beta\sem_janela.py`: o PowerShell e o cron que ele dispara não abrem janela. A pasta `experimental\` **não foi arquivada**: é um ambiente do `ambientes.json`, ligado/desligado pelo `supervisor.py` e pelo `Veo_PAINEL*.bat` — arquivar quebraria o painel; o destino dela vem com o BX-08 (decisão do dono). A memória dela já foi importada (AT-04) | import do supervisor: `Popen._sem_janela` ativo; leitura de `ambientes.json`, do painel e do supervisor |
| 16/10/2026 | BX-04 (código morto) | Removida a `validar_video` de dentro do `cron_gerar_video_llm.py` (obsoleta desde a Onda 1; grep em todos os projetos: ninguém chama; lia erro do ffprobe como "tem áudio"). Commit `20c6f85`. **Mantido** o `metrics_client.py`: o gerador não chama mais (AT-03), mas o `postador\bin\medir_metricas.py` ainda importa e o `postar_tudo_hoje` (caminho do anime) o cita | `validate.py` TUDO OK depois da remoção |
| 16/10/2026 | produção 23:17 (conferência) | 1ª rodada real da tarefa `ManhwaReact-Rede` com tudo: rede sem erro (Veo no teto de 2, 0 agendado — o limite do dia já tinha estourado); `extras_rede` postou 2 comentários pelo navegador no Inovare Ind (fixar espera a verificação do canal); `metricas_rede` com 81 vídeos na idade de medir. Comentários 403 dos canais do Veo eram de vídeos retirados (10 marcados "retirado" pela mudança do AB-12) | `logs\rede_20261016.log`, `extras_rede.log`, `metricas_rede.log` |
| 16/10/2026 | métricas: retirado/removido | Na rodada real das 23:17 o `metricas_rede` gastou 1 min de Chrome no `wKiGkUQ6bBc` (removido). Agora `pendentes` pula os de `rede_retirados.json` e os marcados `removido`; quando o Studio não mostra métrica, o oEmbed decide: 404 = `removido` (nunca mais), privado (403) continua. Achado de produção: os Shorts de react do **InventoReact** estão com 6 e 9 views após 2+ dias | fila 81 → 78 (retirados fora); `_fora`: wKiGkUQ6bBc True, GIFfxhU107c (privado) False |
| 16/10/2026 | avaliados, não feitos | **AT-11** (capa A/B/C): o Veo sai como Short e o Studio web não põe capa nem teste A/B em Short — só vale quando houver vídeo longo do Veo. **IM-04** (cache de clipe parado + 1 `filter_complex` + QSV): otimização de tempo de render; o comercial monta em ~1 min, sem gargalo hoje. **BX-05 resto** (ffmpeg pela constante central): 25 arquivos com o mesmo caminho, que não muda — risco maior que o ganho. **BX-08** (beta → prod): decisão do dono. **AT-08 b/c** (Ingredients/Extend) e **Onda 4.2** (historias animada): gastam crédito do Flow; a 4.2 é da sessão de qualidade. **Kwai**: precisa de conta logada (dono) | — |
| 16/10/2026 | BX-09 | `postador\bin\etapa.py`: roda uma etapa com prazo e, se estourar, encerra só a árvore dela (`taskkill /T` no PID que abriu) e sai com 124. No `postar_tudo_auto.bat`: TikTok 90 min, Instagram 60 min. O ciclo de 15/10 morreu no TikTok; 13, 14 e 16/10 chegaram ao "FIM CICLO COMPLETO" (16/10: TikTok levou 52 min) | etapa de 30 s com prazo de 3 s → encerrada, rc 124, aviso no log; etapa rápida → rc 0 |
| 16/10/2026 | AB-01 | Dono: "o postador unificado é o caminho". `postar_tudo_auto.bat`: etapa 1 só `--so animes` (o anime é o único que ainda sai por ali, com `pronto` só após a revisão), etapa 2 (`postar_pos_final`) fora. `postar_tudo_hoje`: padrão só `animes` (recap/historias/vo3 ali duplicariam o hipercool e a rede, público e em rodízio); `vo3` só com `config\VEO_ANTIGO_LIGADO.json`. `postar_pos_final.py` e `agendar_vo3.py` em `bin\_legado\`; `agendar_vo3_auto.bat` sai na hora; `aprovar.py` sem as fontes antigas | `--preview`: inventário só animes (0 hoje); `--so vo3`: "DESARMADO"; `aprovar.coletar_pendentes()` 9 itens sem erro; `py_compile` |
| 16/10/2026 | AB-08 | `beta\dedupe_video.py` (copiado de `mr\memoria.py`: dHash 1 quadro/0,5 s do quadrado central de 80%, fora da legenda e do @); índice `logs\hashes_videos.json` com os 243 limpos (os 730 antigos não estão no disco). `limpar_veo.processar` confere cada limpo novo e indexa; repetido → `revisar: "clipe repetido de X"`, e a rede pula "clipe repetido". **Limiar 0,9, não 0,35**: nos clipes de IA o fundo igual engana | `--duplicados`: 11 pares a 0,35; nos quadros só os 5 de **1,00** eram o mesmo clipe (2 nomes, legenda diferente) — 0,75/0,62/0,38 eram pessoas/cenas diferentes no mesmo estúdio. Os 5 pares já estavam barrados por moldura/Grok ou retirados (GIFfxhU107c). `repetido()`: o repetido aponta o par (1,0); 3 clipes diferentes → None |
| 16/10/2026 | BX-05 (md5) | `plugins\propaganda_inteligente._escolher_produto_inteligente`: md5 no lugar de `hash()` (último `hash()` de string no beta) | 3 processos: os mesmos 3 produtos para os mesmos 3 vídeos. **Ficou para depois:** ffmpeg pela constante central (24 caminhos fixos), `validate.py` e os 3 docs desatualizados |
| 23/10/2026 | cadeia de alternativas + créditos (dona: "pra ter uma ordem de fallbacks do Veo, justamente pra não ter como dar errado em todos, algum vai fazer") | `cadeia_veo.py` (ordem notebooks → desktop sem chamada → PC2/PC1 o mais livre; castigo de máquina; não usa notebook exibindo vídeo; 1 aviso após 3 h), `creditos_contas.py` (saldo por conta, mínimo 20, mais crédito primeiro), `cron_gerar_video_llm.py` (etapas no laço; máquina ocupada não aborta o ciclo; EXHAUSTED que não dá pra reler é liberado depois da renovação), `gera_auto.py` (`VEO_MAQUINAS`, castigo, nunca cai pro PC1 numa etapa remota, `VEO_CREDITO_MINIMO`). Backups `*.bak_20261023_fallback`. Detalhes: `CONTINUAR_DAQUI.md` seção 0 | `teste_cadeia_a_seco.py`: 10 cenários TUDO OK (sem gerar, sem crédito, estado em pasta temporária); `validate.py` TUDO OK; `py_compile`; leitura ao vivo da cadeia (só leitura) |
| 16/10/2026 | 3.3 (whisper com render) | **Feito do lado do Veo (23:15)**, sem mexer no `mr\transcribe.py` (da outra sessão): `conferir_fala.transcrever` roda o subprocesso de transcrição DENTRO da `trava_render` (espera até 15 min; ocupada → None = "não deu para saber", que o porteiro não reprova). Pelo Groq a trava fica ~6 s; se cair no whisper local, ele não roda junto de montagem/legenda. Commit `8f525cb` | conferência real: ok, semelhança 1,0, groq, 6,2 s; trava apagada no fim |

### Verificação adversarial da Onda 1 (16/10) e as correções que ela obrigou

Quatro revisores independentes tentaram derrubar a implementação. **Três deram "não pode ir assim"** e acharam
defeitos reais, com prova. Tudo abaixo já foi corrigido e re-testado.

| O que estava errado | Prova que o revisor trouxe | Correção |
|---|---|---|
| **O validador aprovava vídeo que não abre.** Ele lia só o texto de erro do ffmpeg e ignorava o código de saída | varreu a pasta `limpos` e achou que **27 dos 240 vídeos (11%) não decodificam** — e o validador aprovou 10 de 10 testados. É a pasta de onde a rede publica | passa a reprovar por código de saída e por erro de decodificação (`Invalid NAL unit`, etc.). **Varredura depois do conserto: dos 240, o ffmpeg reprova 27 e o validador reprova 28 — nenhum escapou** (o 28º, `transformacao_20260727_062012.mp4`, só aparece quando se decodifica o vídeo com os filtros, e o teste simples não pegava) |
| **As duas portas do porteiro falhavam juntas no mesmo arquivo**: o corrompido passava na validação e, na conferência de fala, o ffmpeg morria e o resultado virava "não sei", que não reprova | reproduziu o porteiro inteiro em 2 arquivos: "OK 1080x1920" + "não consegui transcrever" = passou | a extração de áudio que falha agora devolve "arquivo ilegível" (reprova), separado de "a transcrição caiu" (não reprova) |
| **Fala truncada passava com nota 1,00.** A métrica dividia pelo conjunto menor, então "Cansado" contra a frase inteira dava 1,00 | 5 variantes de corte, todas aprovadas. É o defeito mais comum em clipe de 8 s, quando a frase não cabe | entrou a **cobertura**: quanto da frase pedida foi realmente dita (mínimo 60%) |
| **O veo ficava pior do que antes na rede.** Quando o diretor dava nota baixa num canal permitido, o vídeo saía da disputa | dos 40 na fila, **20 ficaram abaixo do mínimo e 20 entraram pelo fallback**; nenhum entrou por nota real. A simulação que eu li como "entrou pelo diretor" era fallback | nota baixa do diretor é respeitada; quando ele só indica canal não liberado, mantém o comportamento antigo **e escreve no log** onde ele encaixaria |
| **"Os mais novos primeiro" ordenava por nome, não por data** | os 6 limpos mais novos caíam na posição ~200 de 241 e nunca entravam; sobras de teste (`v1`, `teste1`) encabeçavam a fila | ordena pela data do nome; arquivo sem data vai para o fim |
| **`veo_max_dia: 0` liberava tudo em vez de proibir** | `0` é falso em Python e desligava a checagem | zero agora proíbe mesmo |
| **Tipo errado na config matava a rodada dos 12 canais** | `"veo_max_dia": "dois"` levanta exceção que sobe até o processo morrer, e nada é postado | leitura tolerante, que avisa no log e usa o padrão |
| **A janela de 40 também cortava a fila de aprovação humana** | um limpo novo podia nunca aparecer no `rede --aprovar` | o corte vale só para a disputa |
| **Reprovar vídeo punia a conta que funcionou** e podia gastar até 12 gerações pagas num ciclo sem publicar nada | leu a escada inteira e simulou a contagem | contador próprio de reprovas, que marca sucesso da conta e encerra o ciclo em 2 reprovas (`VEO_MAX_REPROVAS`) |
| **Vídeo reprovado podia ficar na pasta de produção** se o arquivo estivesse preso (antivírus, player aberto) | no Windows o `move` copia e só depois apaga; o original ficava e seria varrido pelo worker | o motivo é escrito antes, o destino nunca sobrescreve, e se o move falhar o arquivo é renomeado para sair do `*.mp4` |
| **A troca de prompt dentro da escada não passava pelo dedupe** | o dedupe só rodava uma vez por ciclo | virou a função `sem_repetir`, usada nos três pontos que montam prompt |
| **`re` não estava importado** no `cron_gerar_video_llm.py` | `analisar_padroes_viralizacao` levantaria erro assim que houvesse 3 vídeos com métricas, e o erro era engolido | import no topo; a função agora roda (defeito antigo, de antes desta auditoria) |

**Commit da Onda 1:** `8ad167a` (3 arquivos, +741/−29), juntado no `main`. Nada enviado ao GitHub. As mudanças na
rede (`D:\manhwa-react\mr\rede.py`) **não têm commit**, porque aquele projeto não usa git: a proteção é o backup
`mr\rede.py.bkp_20261016`.

### ATENÇÃO: outra sessão mexeu no mesmo arquivo, e o teto do veo mudou (16/10, 11:27)

Enquanto esta auditoria trabalhava, **outra sessão do Claude editou `mr\rede.py`** a pedido da dona
("publique apenas nos 2 canais … 3 por dia e aumentando"). Duas consequências que o próximo agente precisa saber:

1. **Houve ~50 segundos com o arquivo quebrado** (`NameError: _ocupados_veo`), entre dois salvamentos. A tarefa
   `ManhwaReact-Rede` roda no minuto 17 de cada hora; se calhasse nessa janela, a rodada teria falhado. Duas sessões
   editando o motor de postagem ao mesmo tempo é risco real: combine quem mexe antes de abrir o arquivo.
2. **A rampa substitui o teto desta auditoria.** O novo `veo_rampa` dá ao Veo **vagas próprias**, fora da disputa com
   o react: 3 por canal por dia desde 16/10, 4 desde 23/10 e 5 desde 30/10. Em 2 canais isso é **6 por dia agora,
   indo a 10**. O comentário do código diz, corretamente, que `veo_max_dia` e `veo_pelo_diretor` (itens DS-01 desta
   auditoria) **só valem quando `veo_rampa` está vazia**. A simulação passou de 4 para 15 vídeos.

   Isso contraria a recomendação AB-11 deste plano (1 a 2 por dia até haver 10 medições de 48 h) e o volume é o
   comportamento que o YouTube pune. Não é erro de ninguém: é uma decisão da dona, tomada com outra sessão. Fica
   registrado para que a escolha seja consciente, e para quem for medir depois saber de onde veio o número.
   Para voltar ao teto desta auditoria, basta `"veo_rampa": []` no `config.json`.

Achados de gravidade média que **ficaram para depois** (estão na lista de trabalho, não foram feitos):
vozes proibidas ainda em uso em `D:\postador-de-videos\bin\edge_tts_engine.py` (a Onda 0 fechou só o lado do veo);
o telefone da dona está commitado em `produtos.json`, num repositório com remoto no GitHub; o regex de contato ainda
barra faixas de números (capítulo, ano, placar) e deixa passar vários convites de contato; o teto de veo é por rodada,
não por dia; e `--simular` grava caches, então não é leitura pura.

**O que a verificação de 16/10 corrigiu nesta primeira versão:**

| Afirmação anterior | O que é verdade |
|---|---|
| "161 vídeos aprovados na fila e 0 agendados" (15/10) | 15/10: 10 na fila, 7 esperando aprovação, 1 agendado. 16/10 05:20: **227 na fila**, 8 canais sem vídeo bom, 1 agendado |
| "8 uploads em 42 min" no canal pt | **10 uploads no dia**, sendo 8 entre 05:27 e 06:09 |
| "21 handles, 20 suspensos" em `roteamento.py` | **19 handles únicos: 18 suspensos, 1 ativo** (animescomia, reservado à rede) |
| "334 fotos nas subpastas" | **333** (comedia 30, epocas 170, guerra 73, herois 54, jornal 6) |
| "o pool VO3 pode ser a pasta local" | `_pool_dir` resolve para `D:\hipercool-materiais\veo\propagandas_vo3\vo3`; os 3 demos locais nunca foram usados |
| "`subtitles_veo.py:152,166` com `-loop 1`" | só `:166`; ao todo são 5 ocorrências reais |
| "`metrics_client` exige a chave" | sem a chave ele devolve vazio **em silêncio**; e a regex nem cobre URL de Shorts |

**O que a verificação acrescentou (não estava na primeira versão):**

- `postar_tudo_hoje._resolver_video_vo3` procura o mp4 também em `videos_pos\cron_shorts` e `pos_final`: o caminho
  antigo pode pegar justamente a versão com o slide de WhatsApp.
- Os freios globais `PARADO.json` e `POSTAGEM_DESLIGADA.json` **não existem no disco hoje**.
- `@InovareStories` está escrito no código em `branding_watermark.py:100,104`, não só na config.
- A conferência de "conteúdo sintético" no poster do navegador é a única que não interrompe o upload.
- Os 231 vídeos de `videos_pos\cron_shorts` não têm sidecar: o fluxo de 2 variantes quase não rodou.
- O pool VO3 tem 8 clipes para 9 produtos, e `hermes_call_1.mp4` está deitado dentro da pasta vertical.
- Além das 2.218 linhas sem commit, há dezenas de arquivos nunca rastreados pelo git.
- O log da geração parou em 15/10 16:58: o loop pausado foi encerrado.

**Achados novos da execução da Onda 0 (16/10), que viram trabalho:**

| Achado | O que fazer | Onde |
|---|---|---|
| O serviço edge-tts responde **403** a este PC (direto) e dá timeout pelos proxies de `secrets\proxies.txt`. Vale para qualquer voz, inclusive a antiga: não é regressão. Com isso a voz do card só sai se o ElevenLabs estiver disponível | conferir chave do ElevenLabs e renovar a lista de proxies; entra como item novo na Onda 2 junto de AT-10 | `pos_producao\edge_tts_veo.py`, `secrets\proxies.txt` |
| Os **88 cards** e **38 áudios** em cache foram gerados com o número. O card está protegido pelo bump de layout e o áudio pela nova chave, mas os arquivos continuam no disco | apagar `cta_cache_cards\` e `cta_cache_audio\` depois que a dona aprovar o visual novo | `pos_producao\cta_cache_*` |
| O bruto `slowmo_20260725_141403.mp4` usado no teste tem **marca d'água do Grok** no canto. Ou seja, há brutos de outras ferramentas na pasta do Veo, e o detector do `limpar_veo` só procura a logo do TikTok | ampliar o detector (item AB-09) para marca fixa por quadros parados, não só o template do TikTok | `D:\hipercool-materiais\veo\veo_videos_iniciais` |
| Com fundo em gradiente (sem a imagem de IA), o texto do benefício fica em cor do produto sobre fundo da mesma cor e some | contraste do card: texto do benefício em branco quando o fundo for o gradiente | `pos_producao\cta_card.py` |
