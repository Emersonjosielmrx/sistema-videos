# Plano de melhorias — hipercool (pesquisa de 14/10/2026, ~14h-15h)

Pedido do dono: pesquisar a fundo e trazer listas por categoria e prioridade, já planejadas para implementar:
efeitos 2.5D ("a maioria só treme"), profundidade de cenário, memes (estilo @Laestro1), edição/retenção,
desempenho, outro PC, título/descrição/tags/capa com agentes que aprendem com o histórico e testam variações,
narração mais viral. Protótipos e imagens em `C:\Users\Haylla\AppData\Local\Temp\pesquisa\`.

Legenda: **P1** = fazer primeiro, P2, P3. Esforço P/M/G. Custo medido nesta máquina (i5-8365U 4 núcleos,
16 GB, só Intel UHD 620), com a CPU dividida com o render do cap 3.

## Ordem geral sugerida (top 12)

| # | Item | Categoria | Esforço | Por quê |
|---|---|---|---|---|
| 1 | Tirar a propaganda do scan do MEIO do capítulo | Conteúdo | P | 9 s de "lançado primeiro na Blackout Comics" no 1º minuto do cap 2 |
| 2 | Acabar com o tremor contínuo (tensão/impacto) | Efeitos | P | é o que faz "só tremer" |
| 3 | Profundidade de cenário (novo modo) | Efeitos | M | ~40% dos painéis hoje sem efeito; testado, ficou bom e é barato |
| 4 | Memes: figurinha durante a narração + reação em tela cheia | Memes | M | testado; estilo Laestro |
| 5 | Legenda maior, estilo viral | Edição | P | a nossa é pequena perto do Laestro |
| 6 | SEO com agentes + histórico + teste A/B de títulos/capas no Studio | Algoritmo | G | o que mais mexe no alcance |
| 7 | Dicionário de segurança de anúncios (título/descrição/tags/narração) | Algoritmo/Narração | P | existe no manhwa-react, falta no hipercool |
| 8 | Personagem "vivo" (cabeça/respiração/cabelo) + entrada deslizando | Efeitos | M | testado: movimento local e natural |
| 9 | Marca d'água do scan apagada dos painéis | Conteúdo | M | BLACKOUTCOMICS.COM grande em vários painéis |
| 10 | Vídeo final em 30 quadros/s constantes | Qualidade | P-M | sai com ~26,7 q/s (faltam ~11% dos quadros) |
| 11 | Narração mais viral (estrutura + bordões + aprendizado por retenção) | Narração | M | — |
| 12 | Outro PC: render das línguas e IA de animação (se tiver GPU) | Infra | G | depende do hardware dele |

---

## 1. Conteúdo do painel (rápido e de alto impacto)

### 1.1 P1 — Propaganda do scan no meio do capítulo (esforço P)
- Evidência: cap 2 pt, 0:31–0:40 — página "상속자" + "Esse capítulo foi lançado primeiro na Blackout Comics.
  Entre para verificar o acesso antecipado… blackoutcomics.com / discord" (folha `pesquisa\nosso_1min.jpg`).
  O `effects_engine.is_propaganda(desc, texto)` não pegou porque o narrador falou por cima ("Eita! Começou...").
- Plano: em `fx_detect`/`effects_engine.is_propaganda`, olhar a DESCRIÇÃO da visão (que transcreve o texto do
  painel) com regex `lan[cç]ad[oa] primeiro|acesso antecipado|blackout\s*comics|discord(\.gg)?|leia (no|em) nosso|
  tradu[cç][aã]o (por|de)|scan(lation)?\b|\.com\b` e pular o painel (já existe o `continue` no laço do
  hiper-pipeline ~linha 334). Teste: rodar `is_propaganda` nas descrições em cache dos caps 1–3 e listar o
  que cai; conferir à mão (não pode pegar painel de história com placa de rua etc.).

### 1.2 P2 — Marca d'água do scan (esforço M)
- Evidência: "BLACKOUTCOMICS.COM — Aqui você lê com a melhor qualidade" em azul, grande, em vários painéis do
  cap 1 e 2 (`pesquisa\comparacao_vivo.jpg`, `nosso_1min.jpg`); às vezes entra na máscara do personagem.
- Plano: novo `bin/limpa_painel.py`: achar caixas de texto com OCR ONNX em CPU (rapidocr-onnxruntime) contendo
  BLACKOUT/COMICS/.COM/QUALIDADE → `cv2.inpaint` (TELEA) na caixa dilatada → painel limpo em cache por md5
  (`workspace/cache/paineis_limpos/`). O pipeline usa o painel limpo em tudo (clips, máscara, capa). Custo:
  ~0,5–1 s por painel uma vez (as línguas reaproveitam). Risco: borrão onde a arte é detalhada — melhor que a
  marca. Teste: 20 painéis com marca, folha antes/depois.

## 2. Efeitos 2.5D

### Diagnóstico (código do `fx_parallax._render_camadas` + `fx_clips`)
- `tensao` (9–11 clipes/capítulo): parallax + **tremor contínuo de 3 px a ~11 Hz** (`sin(f*2.3)`).
- `impacto`: **tremor de 11 px durante 45% do clipe** + salto de 16%.
- `parallax`: recorte RÍGIDO desliza ~30 px e cresce 17% em 3–5 s → "figurinha deslizando".
- `andar` (o bom): ~100 px com passo, mas só ~1 por capítulo.
- Cobertura: 45–50% dos clipes. Cap 1: 55/109 painéis fora (≈42 sem personagem, 8 pequeno, 5 enchendo).
- Clip comum de tensão (`build_clip_with_shake(shake_intensity=5, shake_freq=8)`) também treme.

### 2.1 P1 — Trocar tremor por movimento (esforço P)
- `_render_camadas`: `tensao` sem tremor; no lugar, aproximação lenta mais forte (z_f 1.0→1.22) + balanço
  lento ±4 px a 0,5 Hz + vinheta pulsando. `impacto`: tranco de 0,12 s (4 quadros, 8 px) e para; mantém linhas
  de velocidade e o salto. Linhas ~479-484 (`amp`, `jx`, `jy`).
- hiper-pipeline ~440-451: tensão vai pro 2.5D/profundidade em vez de `build_clip_with_shake`; impacto com
  `shake_dur=0.15`.
- Teste: 1 painel de cada, folha de contato + fluxo óptico (deslocamento acumulado > vibração).

### 2.2 P1 — Profundidade de cenário (novo modo `profundidade`, esforço M) — TESTADO
- Modelo: Depth Anything V2 Small ONNX em `D:\hipercool-materiais\models\depth-anything-v2-small\model.onnx`
  (fp32; o int8 é MAIS LENTO nesta CPU: 3,3 s vs 1,2 s). Inferência: **0,5–0,6 s/painel** (4 threads).
- Render (`pesquisa\profundidade.py`, função `render`): mapa por pixel com `cv2.remap` — perto aproxima e
  desliza mais que longe; balões/quadros de texto andam como bloco (profundidade = mediana dentro da caixa de
  `fx_parallax.baloes`). **2,5–6 s por clipe de 3,5 s** (mais barato que o recorte). Resultado bom nos painéis
  001 (prédio), 019 (cidade à noite), 028 (multidão: cada pessoa separada) — `prof_comparacao.jpg`,
  `prof_mapa_panel_028.jpg`. Painel "esfumaçado" (031) não vale (profundidade em degradê).
- Plano:
  1. `fx_parallax.profundidade(img)` com cache `workspace/cache/profundidade/<md5>.png` (16 bits).
  2. `_render_profundidade(img, out, duration, panel_idx)` = `render()` do protótipo + painel alto (só a janela
     visível, pan vertical) + direção alternando por `panel_idx`.
  3. `build_clip_parallax`: modo `profundidade` (entra no cache de clipes 2.5D e no espelho por língua).
  4. Escolha no hiper-pipeline (~465-505), antes do `elif eleg`: se `not eleg` e painel não é liso/texto
     (`std>40`, escuro<50%, branco<50%) e a profundidade varia (p95−p5 > 0,25) → `profundidade`; e às vezes
     (30%) em painel elegível sem rosto, pra variar.
  5. Teste: cap 1 inteiro só a etapa de clips (sem acabamento) e contar modos; olhar 6 clipes.

### 2.3 P2 — Personagem "vivo" + entrada (esforço M) — TESTADO
- Protótipo `pesquisa\vivo.py`: só a camada do personagem deforma (`cv2.remap`): cabeça inclina ±2,6° com
  pivô no pescoço (caixa do rosto do YOLO), respiração 1,4% no tronco, cabelo 5 px; balões e onomatopeias
  parados. `comparacao_vivo.jpg`: movimento local, sem rasgo. Entrada: personagem desliza 30% da tela com
  "passa e volta" (0,55 s).
- Custo hoje ~240 ms/quadro → otimizar: mapas numa grade 1/2–1/4 só na caixa do personagem e ampliar
  (`cv2.resize` dos mapas); meta ≤60 ms/quadro. Cache de clipes já cobre as línguas.
- Plano: dentro do `_render_camadas`, quando houver rosto: aplicar a deformação na camada `bgr/alpha` antes do
  `warpAffine`; novo modo `entrada` (deslizar + vivo). Rebalancear: profundidade ~30%, vivo/entrada ~30%,
  foco/close ~20%, andar ~10% (relaxar `pode_andar`/palavra de movimento), impacto só em impacto real.
- Corrigir no protótipo: painel alto (câmera desce e o rosto sai) → ancorar a câmera no rosto.

### 2.4 P3 — Mais modos baratos
- Revelação de painel alto de cima pra baixo com pausa no rosto; foco seletivo (desfoque do fundo crescendo);
  varredura de luz em cena de poder; onomatopeia (texto de efeito) pulsando. Cada um P–M.

## 3. Memes

### O que o Laestro faz (folhas `C:\...\Temp\laestro\*-folha*.jpg`, 1,1 mi e 963 mil views)
- Reação em TELA CHEIA trocando a cada 1–3 s ENQUANTO a narração continua (o meme ilustra a frase).
- "Cartão" pequeno com sombra sobre fundo cinza/escuro, surgindo e crescendo (gancho).
- Figurinha pequena por cima do vídeo principal por 1–3 s.
- Legenda 1–4 palavras, centralizada, laranja/amarelo com brilho escuro, CAIXA ALTA na ênfase.

### Acervo
- Catálogo pronto (feito por visão no manhwa-react): `D:\historias-em-frames\config\memes_catalogo.json` —
  251 memes (146 vídeos, 126 com áudio; 105 imagens), todos existem, 239 ok; vídeo mediano 4 s (cortar 1–2,5 s).
- Cobre bem choque (85), confusão (66), deboche (40), tristeza (39), susto (38); FRACO em raiva (7),
  suspense/reviravolta (10), "ele tá ferrado" (13), romance/fofo (15), vergonha (21).
- Hoje o hipercool só tem meme de ÁUDIO (1 no cap 2 inteiro). O sistema visual do historias-em-frames
  (`memes_catalogo.py`, `fx_clips.py` "Meme System") nunca foi trazido.

### 3.1 P1 — Figurinha durante a narração (esforço M) — TESTADO
- `pesquisa\memes.py` + `fig_tempos.jpg`: figurinha inclinada (−6°), borda branca 10 px, sombra, entra
  crescendo com "passa e volta" (0,22 s), fica 1,4 s, sai encolhendo (0,15 s), por cima do painel sem cortar a
  narração. Sequência PNG com transparência + `overlay` com `setpts` (mesmo jeito dos MOVs do passe final).
- IMPORTANTE: normalizar `fps=30` no começo do grafo do passe final (sem isso a figurinha não apareceu — o
  vídeo é de quadros variáveis).
- Plano: `bin/fx_memes.py` (catálogo copiado pra `config/memes_catalogo.json`, render da figurinha, escolha) +
  encaixe no `fx_acabamento.passe_final` como lista `memes=[{t, dur, estilo, arquivo, x, y}]`. Posição: terço
  de cima, alternando esquerda/direita, longe da legenda (KEY_Y) e, quando der, do lado com menos balão no
  painel da vez (caixas de `fx_parallax.baloes`). Áudio do meme (se tiver) entra como evento de SFX no
  `masterizar_audio` a −8 dB.

### 3.2 P1 — Reação em tela cheia (esforço P, junto do 3.1) — TESTADO
- 0,8–1,3 s cobrindo a tela (corte "cover"), narração continua (`memes_tempos.jpg` em 8,5 s). Máximo 1 a cada
  ~60 s no completo; nos momentos mais fortes (impactos do editorial).

### 3.3 P1 — Quem escolhe: agente "diretor de memes" (esforço M)
- Gemini pelo proxy (sem limite): recebe as falas com tempo (já temos tempo por palavra) + lista compacta do
  catálogo (id | desc | uso) e devolve `[{fala, palavra, meme_id, estilo}]`. Regras: nunca em cena triste,
  tensa, sensual ou dentro de janela de censura; figurinha ~1 a cada 20–30 s no completo e 6–10 s nos Shorts;
  tela cheia ≤1/min. Plano B sem LLM: `memes_catalogo.escolher` (por palavras) do historias-em-frames.
- Línguas: escolha pela fala (índice), então cada língua recalcula o tempo pelo próprio áudio.
- Chave: `config/fila.json` → `"memes": {"ligado": true, "figurinha_s": 25, "tela_cheia_s": 60}`.

### 3.4 P2 — Completar o acervo (esforço P–M)
- +40–60 memes de raiva, reviravolta, "tá ferrado", romance/fofo, vergonha; descrever pelo mesmo script de
  visão do manhwa-react; checar se são seguros pro YouTube.

## 4. Edição e retenção

- Ritmo: 1º minuto do cap 2 tem **27 cortes** vs 17–19 do Laestro — troca de imagem não falta; o que falta é
  movimento real, memes e legenda forte.
- 4.1 P1 Legenda maior estilo viral (P): fonte +40–60%, 1–3 palavras, amarelo/laranja com brilho escuro, CAIXA
  ALTA nas palavras de impacto (`fx_acabamento.montar_ass` / `_blocos`). Teste: folha de 30 s.
- 4.2 P1 Tempo morto (P): painel parado >3 s vira profundidade/vivo; pular créditos/logo (item 1.1).
- 4.3 P2 Gancho (P): 1º segundo com o painel mais forte + texto de gancho (já existe) + 1 figurinha/cartão.
- 4.4 P2 Fim com meme + CTA (P).
- Risco de conteúdo (decisão do dono): painéis de lingerie aparecem sem censura (só nudez explícita é
  censurada) — pode limitar anúncios/idade.

## 5. Título, descrição, tags e capa — agentes que aprendem (o que mais mexe no algoritmo)

Hoje: `bin/seo.py` faz 1 chamada por capítulo/idioma com regras genéricas, sem testar variações e sem olhar
resultado de nenhum vídeo. Sem regra de segurança de anúncios.

### 5.1 P1 — Dicionário de segurança de anúncios (esforço P)
- Já existe no manhwa-react (`mr/editorial.py`, `mr/rede.py`, `mr/grande.py`): evitar matar, morte, morrer,
  sexo, nu, droga, arma, suicídio, sangue no título/descrição/tags; usar eufemismos ("elimina", "se vai",
  "+18"). Plano: `config/dicionario_seguro.json` (palavra → eufemismos, por idioma) + validador determinístico
  no `seo.py` (troca ou pede de novo) + o mesmo nas falas do NARRADOR (não nos balões, ver 6.2).

### 5.2 P1 — Coleta de resultados (esforço M)
- Visualizações/likes/comentários de cada vídeo do hipercool: os IDs estão no ledger do postador; o motor do
  `postador-de-videos/bin/medir_metricas.py` lê estatísticas públicas de qualquer vídeo por ID com os tokens
  OAuth que já existem (sem chave nova). Novo `bin/metricas.py`: grava `workspace/metricas/<video_id>.json`
  com views em 1 h, 24 h, 72 h, 7 d + tudo que foi usado (título, tags, capa, hora, canal, língua, tipo,
  capítulo, memes, efeitos).
- CTR, impressões e retenção (só o dono do canal vê): ler do Studio pelo Chrome já logado de cada conta
  (cofre `D:\logins-google`), aba Análise do vídeo — fase 2.

### 5.3 P1 — Agente analista (esforço M)
- Gemini pelo proxy, sem limite: compara melhores x piores (normalizado por canal e idade do vídeo), separa o
  efeito de título, capa, tags, hora, canal e conteúdo, e grava `config/aprendizados_seo.json` (regras com
  exemplos, evidência e confiança). Roda 1×/dia.

### 5.4 P1 — Gerador multiagente (esforço M)
- Estrategista (lê aprendizados) → Redator (10 títulos + descrições) → Juiz (curiosidade, clareza, segurança de
  anúncio, aprendizados) escolhe 3 → Tags. Capa: 3 variações (momento/rosto, texto curto, emoji, cor).
- Teste A/B nativo do YouTube: "Testar e comparar" faz **até 3 títulos e/ou capas, só vídeo longo (não
  Shorts), só pelo Studio no computador; vencedor = mais tempo de exibição** (support.google.com/youtube/answer/
  13861714). Os completos (~5–6 min) entram. Plano: passo novo no `youtube_web_poster` (é do postador — pedir
  à sessão dona) depois do upload; resultado do teste vira aprendizado.
- Shorts (sem A/B nativo): variar títulos entre partes e línguas de propósito e medir.

### 5.5 P2 — Capa
- Hoje `fx_acabamento` gera a capa (`_capa_sensual`). Medir CTR por estilo de capa (5.2) e gerar 3 por vídeo.

## 6. Narração

### 6.1 P2 — Estrutura viral + bordões (esforço M)
- Prompt atual (`narration.py` ~340): "envolvente, dramático, humor leve, gírias". Somar: loops abertos a cada
  20–30 s ("mas isso não é nada perto do que vem depois"), falar com o espectador ("você"), pergunta pro
  comentário no meio, cliffhanger no fim, e um repertório de bordões de grandes narradores em
  `config/dicionario_narracao.json` (variados, pra não repetir).
- Aprendizado: retenção por trecho (5.2 fase 2) → o analista aponta onde o público sai e o que a narração dizia.

### 6.2 Decisão do dono — palavras fortes nos balões
- Hoje a regra manda manter literal ("escrava, matar, palavrão ficam"). O YouTube transcreve a fala e isso pode
  limitar anúncios. Opções: manter; suavizar só no narrador; suavizar também nos balões.

## 7. Qualidade técnica e desempenho

- 7.1 P1 — **Vídeo final com ~26,7 quadros/s** (cap 2: 9.243 quadros em 345,8 s; deveria ter ~10.375). Achar
  onde caem (concat com transições ou passe final) e forçar `fps=30`. Teste: `ffprobe nb_frames` por etapa.
- 7.2 P2 — Passe final na GPU Intel: o grosso é `scale lanczos + cas` na CPU (~0,7× tempo real aqui; 5–9 min
  por vídeo). `scale_qsv`/`vpp_qsv` existem neste ffmpeg; a tentativa `hwupload,format=qsv,scale_qsv=…,
  hwdownload,format=nv12,cas` falhou na negociação de formato → testar com `format=yuv420p` depois do
  `hwdownload` e comparar SSIM com o lanczos. Ganho possível: 3–5 min por vídeo.
- 7.3 P3 — Punch-in: o ramo de zoom roda em todos os quadros, mas medido custa só ~9% (não vale mexer agora).
- 7.4 P2 — Clipes das línguas em 2 processos paralelos (sem cota de TTS no edge) + cache 2.5D já feito.
- 7.5 P2 — Visão do Gemini: 44 erros 429/503 no cap 3; adiantar a visão do próximo capítulo enquanto o atual
  renderiza.

## 8. Outro PC e IA de animação

- PC: **desktop-su00b7v, 100.73.7.19 (Tailscale), usuário Emerson. Acesso por chave FUNCIONANDO
  (`ssh -o BatchMode=yes desktop`); desde 24/10/2026 o Windows de lá está SEM SENHA — nunca usar/pedir senha.**
  Hardware: i5-7360U (2 núcleos), 8 GB RAM, sem GPU NVIDIA. É worker da fila (`D:\video-fila\maquinas.py`);
  ocupado com OBS aberto ou chamada.
- Sem GPU NVIDIA: usar como 2º renderizador (as línguas inteiras, com o cache) — dobra a vazão.
- Com GPU: IA imagem→vídeo em 3–8 painéis-chave por capítulo (movimento de verdade: andar, cabelo, expressão).
  Opções verificadas (GitHub, 14/10/2026): **Index-AniSora** (bilibili, anime, Apache-2.0; V3.1 tem versão de
  12 GB; V3 gera 5 s 360p em ~8 s numa GPU grande), **HunyuanVideo-1.5** (8,3B; ≥14 GB com offload; ~75 s por
  clipe 480p numa RTX 4090), **FramePack** (lllyasviel, ~6 GB), **Wan2.2**, **LTX-2** (áudio+vídeo; atualizado
  13/10/2026), **ToonCrafter** (interpolação de desenho). Arte +18 só nos painéis seguros.
- Trabalhador remoto: fila de jobs em JSON numa pasta compartilhada (SMB) ou scp; resultado em cache por hash
  do painel; se o PC estiver desligado, faz local.
