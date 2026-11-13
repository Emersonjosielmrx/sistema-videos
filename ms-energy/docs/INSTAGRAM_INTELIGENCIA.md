# Inteligência do Instagram das empresas (MS Energy e as próximas) — 25/10/2026

Pedido do dono (25/10 ~07:00): "faça todas as melhorias possíveis no sistema de inteligência do Instagram,
principalmente focado nas empresas que têm produtos que vamos colocar como MS Energy, pra que o Instagram deles tenha o
máximo de comentários, visualizações e pessoas procurando seus produtos".

Regras: cada achado é gravado aqui NA HORA, com evidência real (arquivo:linha, dado da API, log). Ao retomar, seguir do
primeiro item não marcado. Trabalho direto (sem Agent/Workflow: memória do Opus, 4× 429). Nada de engajamento falso
(curtida/comentário por bot derrubou 18 de 44 contas em 04/09). Postagem real só pelas tarefas que já existem.

Antecedentes: `ANALISE_CAMPANHA.md` (22/10: ms_v2, trava, vigia, carrossel, vídeo real), `METRICAS_INSTAGRAM.md`,
`D:\postador-de-videos\docs\PASTAS_EMPRESAS.md` (cor e pasta por conta), painel de clientes (`D:\painel-clientes`).

## Frentes

| # | Frente | Status |
|---|--------|--------|
| A | Dados reais agora: o que rende por formato/pauta/horário (@msenergycap e contas de produto com token) | feito 25/10 07:20 (achados abaixo) |
| B | Busca ("pessoas procurando"): legenda com palavra-chave + cidade, hashtags locais, localização, texto alternativo, nome do perfil | legenda feita 08:10; texto alternativo/nome do perfil: ver abaixo |
| C | Comentários: pergunta/CTA de palavra-chave, resposta rápida, duplicidade vigia x n8n | feito 08:25 (vigia por tipo de comentário) |
| D | Visualizações: gancho, formato vencedor (carrossel), Stories, horário pelo público online, frequência | feito 08:40 (gancho pergunta, karaokê, story do carrossel; horário = placar; frequência = decisão do dono) |
| E | Aprendizado (funil): placar por pauta/formato/horário e escolha por Thompson, como no YouTube | feito 08:20 |
| F | Multiempresa: tudo por conta (cidade, palavras, hashtags, local, WhatsApp, palavra do comentário) p/ Precioso, a outra solar e os produtos | feito p/ legenda e carrossel; vigia só MS Energy (única com token vivo) |
| G | Leads: quem chamou a partir de qual post (link rastreado / Direct / comentário) | pendente |

## Achados

### Aprendizado com parceiros (regra obrigatória, lido 25/10 07:05 — 0 aprovados, 367 candidatos, 40 mais fortes)
Servem p/ Reel de empresa (avaliar/aplicar): #12 `c9627e2c` pergunta de seguidor na tela como gancho (estilo "respondendo
comentário" — puxa comentário); #34 `na sua opinião` + respostas antecipadas (debate = comentário); #6/#20/#33
`ffb4c8fe`/`62c7ec8c`/`e4fbdf10` legenda palavra por palavra com destaque (retenção); #17 `9a1f9f1f` frase fixa no topo
(o `montagem_ms` JÁ faz). Resto é anime/recap/humor (mapa, corte 3D, Naruto, true crime…): não se aplica a empresa.

### A — dados reais @msenergycap (25/10 07:10, Graph API só leitura; `_diag\analise\insta_diag_msenergycap_20261025.json`)
- 10 posts de 21 a 24/10: **Reels ms_v2 com alcance 2–8** (views 3–9, assistido 1,7–5,8 s) para **2.076 seguidores**;
  carrosséis alcance 80 (22/10, 145 views), 7 e 17. **Zero comentário, zero salvo, zero compartilhamento em todos.**
- Conta, 7 dias: alcance 377, views 1.043, **0 clique no link (WhatsApp)**, 2 contas engajadas, 2 interações.
- **Público certo**: 1.566 de 1.641 seguidores com cidade são do Pará — Belém 398, Capitão Poço 252, Paragominas 193,
  Ananindeua 147, Castanhal 108, Garrafão do Norte 71… (45 cidades). Gênero F 937 / M 829. Seguidores online por hora:
  a API devolve vazio (sem dado). Público engajado por cidade: "Not enough users".
- **Legenda**: 1ª linha = frase informativa morna ("Com o financiamento certo, o valor investido…"); nenhuma pergunta;
  nenhum convite a comentar; rodapé fixo igual em todo post; hashtags só com #paragominas de cidade (Belém/Capitão
  Poço/Castanhal = maiores públicos, nunca citados).
- **Publicação**: `postador\bin\instagram_poster.postar_reel` (usado pelo postador multi-conta e pelo MS Energy?) manda
  só media_type/video_url/caption — **sem `share_to_feed`**, sem capa (`thumb_offset`/`cover_url`), sem texto
  alternativo. Carrosséis (`carrossel_ms.py:353`, `carrossel_marca.py:374`) sem `alt_text`. Alcance de Reel 2–8 com 2 mil
  seguidores = nem os seguidores estão vendo (suspeita 1: Reel fora do feed; suspeita 2: conta com distribuição
  reduzida pelo histórico de agosto — 67 Reels de IA em rajada, legenda repetida; só o app mostra "Status da conta").
- **Faltou vídeo novo**: 3 horários de Insta/dia (10:17, 14:47, 19:37) e 2 vídeos gerados/dia → 24/10 19:41 saiu um vídeo
  ANTIGO de reserva (`ms_energy_solar_20261020_052841`, formato meme de antes do ms_v2, "☀️ Gere a sua própria energia…").
- Stories: cada Reel também vai pro Story (`postar_ms_energy.postar_instagram_stories`) — ok. Carrossel não vai pro Story.
- `metricas_insta.py` (semanal): calcula formato "carrossel" mas só soma "novo" e "antigo" → **carrossel nunca aparece
  no relatório**; não lê comentários, cliques no link nem alcance da conta.

### C — comentários e Direct (25/10 07:30, `_diag\analise\_ver_dm.py`, só leitura)
- **Direct parado desde 23/11/2025** (25 conversas; nenhuma nova) — bate com 0 clique no link em 7 dias.
- O robô do n8n ("Solzinho, da MS Energy") respondeu Direct em nov/2025; **em 04/11/2025 respondeu na conta da MS Energy
  com o discurso de OUTRO produto** ("Essa IA aprende sobre seu negócio… teste grátis") — o fluxo multi-conta mistura as
  empresas. Sem conversa nova desde então, não dá pra ver se ainda acontece (fluxo `zsTFymPn93V1KwhC` ativo).
- Vigia (`bin\vigia_clientes_insta.py`): todo comentário (≤ 7 dias, sem cara de spam) recebe o MESMO Direct e a MESMA
  resposta pública; não diferencia pedido de orçamento de um emoji; não confere se a empresa (ou o n8n) já respondeu
  antes de responder; só @msenergycap (empresa nova = copiar o arquivo).
- Legenda (`roteiro_ms._pedir_llm`): o LLM é instruído "SEM convite no final" e o rodapé é fixo → **o post nunca pede
  comentário nem faz pergunta**. Histórico inteiro: 8 comentários em 165 posts (2021→hoje).

## Feito (25/10) — backups `*.bak_20261025_insta`
1. **Reel no feed + capa** (`postador\bin\instagram_poster.postar_reel`): `share_to_feed=true` explícito e `thumb_offset`
   (`--capa-ms`; o MS Energy usa 1000 = foto + frase do topo). `--teste-container` cria sem publicar. Testado 07:50: a API
   aceitou os dois (container 18113768546588211 pronto, NÃO publicado). Vale p/ todas as contas do postador.
2. **Reserva antiga só cobre o dia vazio** (`postar_ms_energy.py`): com post de hoje já feito, vídeo do formato meme
   antigo não entra (24/10 19:41). `--preview`: 2 novos hoje, 0 antigos.
3. **Legenda nova por empresa** — `postador\config\empresas_instagram.json` (MS Energy completo: 20 primeiras linhas e
   20 perguntas por pauta, palavra SOL, 5 hashtags; Precioso, Agenda IA, Cardápio Digital, Hermes Call com o básico) +
   `postador\bin\legenda_empresa.py` (`montar`, `relegendar`, `tem_palavra`). Ligado em `roteiro_ms.legendas_finais`
   (Reels e carrossel) e no `postar_ms_energy` (refaz na hora de postar o que foi gerado antes). Testado no vídeo das
   10:17 de hoje: "Como é instalar energia solar no Pará, do começo ao fim ☀️ … Qual etapa você achava mais complicada?
   👇 💬 Comente SOL…" (465–600 caracteres, 5 hashtags). `tem_palavra`: SOL/sol!/"quero sol" sim; solar/girassol não.
4. **Vigia por tipo de comentário** (`vigia_clientes_insta.py`): palavra SOL ou interesse (pergunta, orçamento, preço,
   zap…) → Direct + resposta pública; elogio/emoji → só "obrigado" público; resposta à pergunta do post ("Belém",
   "cerâmica") → agradece e convida a comentar SOL; comentário que a empresa (ou o n8n) já respondeu → não responde de
   novo. Respostas públicas variam (md5 do comentário). Campo `replies{from}` testado na API (aceito).
5. **"Comente PALAVRA" só onde há vigia** (`empresas_instagram.json` `vigia`): msenergysolar.pa (navegador, sem vigia)
   e as contas de produto ganham pergunta mas NÃO a promessa de Direct. Contas de produto: `pergunta_padrao`.
6. **Texto alternativo nas imagens** (busca/leitor de tela): `carrossel_ms` e `carrossel_marca` mandam `alt_text` em
   cada slide (capa/título+texto/final). Testado 08:00: item de carrossel com alt_text aceito (18113770145588211, não
   publicado). Carrossel já produzido e não postado tem a legenda refeita na hora de postar.
7. **Carrossel das contas de produto** (`carrossel_marca._legenda_final`): conta cadastrada ganha 1ª linha (a capa),
   pergunta, link e 5 hashtags (antes só 2–3 linhas do LLM). Conta de tema sem cadastro: igual a antes.
8. **Funil do Instagram** (`ms-energy\bin\funil_insta.py`): post com 48 h–21 dias x mediana do alcance do mesmo formato
   → placares `insta_pautas` (`msenergycap:reel`/`:carrossel`), `insta_formatos`, `insta_horarios` (placar comum, 1
   contagem por post). `roteiro_ms.escolher_pauta` e o carrossel escolhem por Thompson entre as 5 pautas mais frias (o
   rodízio continua). Roda 1x/dia pelo vigia. 1ª rodada 08:00: 11 Reels no placar; carrossel espera 4 com 48 h. Sinal
   inicial (pouco dado): apresentador 0/2, com_foto 2,5/5, criativo antigo 3,5/4.
9. **Relatório semanal** (`metricas_insta.py`): carrossel entrou (mediana 25 views x 5 dos Reels novos) + conta em 7
   dias (alcance 377, 0 clique no WhatsApp, 0 comentário). Testado sem TikTok/Telegram em pasta temporária.
10. **Story da capa do carrossel** (`carrossel_ms._story_da_capa`): o carrossel publicado vai pro Story (Reels já iam).
11. **Gancho em pergunta = cartão de comentário** (`montagem_ms._png_pergunta`, aprendizado #12 `c9627e2c` aplicado):
    cartão branco "Pergunta que a gente sempre recebe" (sem inventar seguidor); no apresentador desce pro peito (no
    topo cobria o rosto — visto no quadro de teste). Frase que não é pergunta: caixa vermelha de antes.
12. **Legenda palavra por palavra** (`montagem_ms`, aprendizado `ffb4c8fe`/`62c7ec8c`/`e4fbdf10` aplicados): palavra
    falada em amarelo; `MS_KARAOKE=0` desliga; ffmpeg falhou com ela = refaz sem. Teste real: remontei o short de
    25/10 00:07 em `_diag\analise\folhas\teste_karaoke_000720.mp4` (original intocado) — quadros
    `teste_karaoke_quadros.jpg`. Aprendizado `fc9ec8d6` (pergunta que puxa debate) aplicado na legenda.

### Produção real (25/10)
- **10:17 — 1º post com as mudanças**: https://www.instagram.com/reel/De6zTwHG9pd/ (media 18331555303263860) +
  Story 18099347810424638. Log: "legenda refeita no formato novo", exit 0. Legenda publicada = a nova (1ª linha
  "Como é instalar energia solar no Pará…", pergunta, Comente SOL, 5 hashtags). **Às 11:07: alcance 1** mesmo com
  share_to_feed — reforça a suspeita de distribuição de Reels travada na conta (carrossel chega a 7–80). Só o app
  mostra: Configurações → Status da conta / "Recomendações". Pedir ao dono.
- Vigia rodando com o código novo desde 08:00 a cada 15 min, sem erro ("avisos: 0"); funil gravado 08:04.
- **12:37 carrossel** https://www.instagram.com/p/De7EqhoIEIf/ ("Quanto vale um telhado solar?", pauta valorizacao):
  publicado 12:50 com alt_text nos 6 slides, legenda nova conferida pela API (pergunta + Comente SOL + 5 hashtags) e
  **Story da capa publicado** (17993955159058739). exit 0.

### Clone do apresentador por empresa (25/10 tarde) — dono: "por que não usa fotos base e cria novas pro tema como o
### Veo normal? todo cliente tem que ter uma subpasta no Drive pra colocar suas fotos base para seus clones"
- Drive: `manhwa-drive:empresas/<conta>/fotos_base` criada nas 11 contas (herda o link de edição da pasta da conta;
  `pastas_empresas.criar` já cria nas novas). Baixa: `pastas_empresas.fotos_base(conta)` / `python pastas_empresas.py
  fotos_base [conta]` → `postador\cache\fotos_base\<conta>`.
- `D:\veo\beta\foto_na_hora.py`: `usar_bases(pasta)` (troca as bases + cache dos rostos), `bases_com_rosto(pasta)`,
  `gerar(..., pedido=)` (pedido de outra pessoa; o padrão descreve o dono).
- `roteiro_ms._clone`: no formato apresentador, com >= 3 fotos com rosto na pasta da empresa (MS Energy =
  `empresas/msenergysolar.pa/fotos_base`, `pasta_drive` no empresas_instagram.json), a foto é criada NA HORA no cenário
  da pauta (camisa vermelha lisa) e o Veo anima dela (`prompt_clone`); `qa_ms` confere o rosto do clipe contra as bases
  (`rosto_clone`). Pasta vazia/Flow falhou = apresentador gerado como antes. `MS_CLONE=0` desliga.
- Teste 12:22: pasta vazia → "0 foto(s)… apresentador gerado"; pasta TEMPORÁRIA com 5 fotos do dono (só teste, nada
  postado nem no Drive) → 1ª foto reprovada (nota 0,50), 2ª aprovada 0,51: `veo\fotos_na_hora\msenergy_clone_20261025_
  122138_2.png` (técnico de capacete no terraço com placas, rosto preservado).
- **Dono 25/10 tarde: a foto do teste (nota 0,51; 0,553 contra as 30 bases) "não é meu rosto"** → `foto_na_hora`
  LIMIAR 0,50 → **0,57** (as que ele aprovou: 0,578–0,700; sósias 0,27–0,33), vídeo 0,45 → 0,50, 3 referências pro
  Flow (era 2). Vale pro Veo normal e pro clone (mesmo módulo). Antigas reprovadas: 392 de 638. Vídeos do Veo de hoje
  reconferidos com o limite novo: todos passam (mediana 0,56–0,65).
- **Clone por conta (25/10 13:45)**: `pastas_empresas.clone_bases(conta)` — fotos_base com >= 3 fotos = essa pessoa;
  conta da casa vazia = o dono (fotos locais; não vão pro Drive); `"cliente": true` (marcas_instagram.json; MS Energy
  marcado) vazio = sem clone. `criar` rodado: 13 contas com entrada/usados/fotos_base + link (novas: disparoemmassa.ia,
  followupia.ia). Teste: msenergysolar.pa → (False, cliente sem fotos); inovarecom.ia/followupia.ia → (None, dono);
  `roteiro_ms._clone` → apresentador gerado. Nenhum outro agente tinha feito estrutura de clone (Drive conferido).
- **25/10 14:14 — 1º vídeo inteiro no sistema novo, postado**: https://www.instagram.com/reel/De7OFPclRKv/
  (`ms_energy_solar_20261025_135341`, vídeo real: cartão de pergunta + palavra amarela + legenda nova). Dono: "muito
  curtos, sem conclusão, pergunta sem responder" → `roteiro_ms`: video_real 25–45 palavras (pergunta → resposta com 2
  fatos → conclusão), fala NUNCA termina em "?" (Veo: 12 palavras, mas responde); `video_real_ms`: até 5 trechos (usa
  os necessários). Teste 14:22: `ms_energy_solar_20261025_142211` 21,6 s, 4 trechos, 17 legendas, aprovado → sai 14:47.
- **Disco (dono: "vídeo/foto usa o Drive")**: `assets\fotos_instagram\google_fotos` 5,1 GB → só as 320 usadas
  (fotos_boas + vídeos do clipes.json); 4.506 apagados depois de `rclone check` 0 diferenças com
  `manhwa-drive:ms-energy/material_real` (script `_diag\analise\_liberar_google_fotos.py`). D:\ms-energy 5,6 GB → 804 MB.
- **Estoque só do dia, pra todos os Instagram (dono 25/10)**: `ms-energy\bin\arquivar_drive_ms.py` (pelo vigia, 1x/dia:
  postados Insta+TikTok, TODOS os antigos, crus > 3 dias; trechos recortados — 11 vídeos-fonte 182 MB fora do PC) e
  `postador\bin\arquivar_insta_drive.py` (fim do carrossel_marca --todas: carrosséis postados -> empresas/<conta>/
  postados; cache das empresas > 2 dias; `D:\veo\fotos_na_hora` > 2 dias -> manhwa-drive:veo/fotos_na_hora). Resultado
  25/10: D:\ms-energy 5,6 GB -> 612 MB; carrosseis_marcas 97 -> 38 MB; `D:\fotos para videos\fotos` 162 -> 3 MB (só as
  fotos-base do dono; resto em manhwa-drive:fotos-para-videos/fotos, check 0 diferenças). Instagram não tem agendamento
  pela API (só Meta Business Suite pelo site, com página do FB): proposto, esperando o dono.
- Teste do clone do dono no MS Energy (regra nova de 25/10 17h): 1ª rodada falhou (fala 14–15 palavras > 12 -> reserva;
  Flow travou na foto; erro no Veo escondido pelo filtro) -> Veo aceita 15 palavras, CTA falado "Orçamento grátis com
  a MS Energy."; 2ª rodada em `_diag\analise\teste_clone_video.log` -> saída `_diag\teste_clone`.
- **Falta a empresa colocar as fotos** (rosto de quem vai aparecer, com autorização; de frente e de lado, boa luz).

