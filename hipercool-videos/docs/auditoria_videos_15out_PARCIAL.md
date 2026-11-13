> **SUPERADO.** O relatório que vale é `docs/auditoria_videos_15out.md` (16/10), com 54 achados de 5 lentes
> auditadas mais estes 15. Dois itens daqui foram CORRIGIDOS lá: a punição dos canais veio de direitos autorais,
> não da narração (`seguranca-04`), e os clips de 1,87 s têm voz — o problema é a cauda de silêncio do edge
> (`voz-05`). Este arquivo fica só como registro.

# Auditoria dos vídeos — o que pode melhorar (15/10/2026, PARCIAL — interrompida por limite de tokens)

Pedido do dono: "fora o que o outro agente está fazendo, veja tudo que pode melhorar nos vídeos do hipercool".
Estado: a auditoria foi montada como workflow de 12 lentes em paralelo + crítico de completude + 2 verificadores
por achado + síntese. Foi PARADA na 1ª fase (6 lentes rodando: narração, voz, imagem, acabamento, segurança,
Shorts; nenhuma chegou a devolver o JSON final). O que elas já tinham levantado (comandos e resultados, quadros
extraídos) está em `workspace/tmp/auditoria_15out/` (`<lente>_evidencias.txt`, pasta `quadros/`). O roteiro
do workflow está lá também (`workflow_auditoria.js`) — pra rodar de novo basta reexecutar com a ferramenta
Workflow (não há cache: nenhum agente terminou).

Abaixo: o que EU confirmei lendo código, logs, metas e estado antes de lançar os agentes. Tudo com evidência.
Não foi verificado por segundo agente. Lentes que nem começaram: longo 16:9, línguas, produção, alcance, capa,
espectador.

## Fora desta lista (outro agente já está fazendo)
1. Capas do cap 7 com as poses novas e as primeiras capas verticais dos Shorts.
2. Extras do Studio depois da verificação (fixar comentário, vídeo relacionado, teste A/B).
3. Leitor de métricas do Studio (retenção 30 s, CTR, capa vencedora) alimentando os rodízios.
4. Detector/limpeza da propaganda e marca do scan (BLACKOUTCOMICS.COM).
5. Revisão independente do código de 15/10.

## O que mais pesa (confirmado)

### 1. Os recaps não rendem view e o canal pt foi punido — a narração explícita é a causa mais provável
- Dado: `D:\postador-de-videos\_analise\aprendizado_global.json` (15/10): "recap hipercool" mediana **1 view**
  em 48 h (n=5, p75 3); Shorts de react nos mesmos canais ~1.100. Verificação do canal pt NEGADA em 15/10 por
  "violou as políticas"; fr com strike (27/09); en bloqueado 7 dias.
- Evidência no vídeo: no cap 10 o NARRADOR descreve o ato ("líquido branco gotejando", "som de sucção", "som de
  deglutição", "gemido alto"); personagens: "VOU GOZAR!!", "ENGOLI TUDO", "SIM. ESCRAVA EUN" (log
  `logs/fila_the-inheritor-cap10.log`, linhas TTS[edge]). O YouTube transcreve o áudio. O dicionário seguro
  (`config/dicionario_seguro.json`, `proibidas`) só troca palavras isoladas (sexo, nua, escrava…) e só no
  narrador (`narration._sanitizar_narrador`); "gozar", "sucção", "líquido", "deglutição" não estão nele.
- Título gravado no meta: "ELA ACEITOU SER A ESCRAVA DELE?! - THE INHERITOR CAP 10".
- O que fazer: no prompt de `narration.gerar_recap` (bin/narration.py ~linhas 480–545) mandar o narrador
  SUGERIR a cena +18 (como o MomoManhwa faz: "o clima esquenta", "a coisa fica séria") em vez de descrever;
  ampliar o dicionário com o vocabulário sexual da narração; medir depois com a lente "segurança" (quadros e
  transcrição). Decisão do dono: até onde suavizar os balões (hoje ficam literais por regra dele).

### 2. Formato: completo VERTICAL de 6–9 min cai no feed normal em 9:16
- Vertical acima de 3 min não é Short; o YouTube distribui como vídeo comum, em 9:16. Os únicos números que temos
  (item 1) mostram 0–5 views nesses completos. A referência do dono (`workspace/tmp/_ref_porao/lista.json`): o
  que estoura no Porão são compilados LONGOS 16:9 (54 min–3h40).
- O 16:9 por capítulo JÁ existe (`workspace/videos/longo/the-inheritor/capNN.mp4`, zero IA nova).
- O que fazer: testar postar o capítulo em 16:9 (capNN.mp4) como "completo" e manter o vertical só pros Shorts;
  medir CTR/retenção com o leitor do outro agente. Decisão do dono.

### 3. Nome da obra ainda sai do pipeline
- `hiper-pipeline.py:876-877` grava `titulo_video` e `tags` do roteiro no meta: cap 10 tem "THE INHERITOR" no
  título e "the inheritor" nas tags. A postagem usa `seo.pacote` (`postar_hipercool.py:247-250`), mas se o SEO
  falhar cai em `meta.titulo_video` (`postar_hipercool.py:256`) — e aí o nome sobe.
- O que fazer: passar `_sem_obra` também no fallback da linha 256 e nas tags do meta; ou trocar o fallback por
  um título fixo do padrão (gancho + "Manhwa Recap").

### 4. Línguas paradas: PC2 quebrado e "tempo livre" que não existe
- `bin/pc2.py:46` monta `tar -cf - -C base <todos os nomes>` na linha de comando; com centenas de arquivos do
  cache 2.5D estoura o limite do Windows: `FileNotFoundError: [WinError 206] O nome do arquivo ou a extensão é
  muito grande` (fim de `logs/fila_pc2.log`, 15/10). Antes disso o PC2 ficou fora do ar 14:52–16:52.
- Resultado: só o cap 1 existe nas línguas (+ cap 2 hindi); `logs/fila_postagem.log` mostra os canais de língua
  subindo Shorts do cap 1 há dias. No PC1, `adiantado: 10` faz a fila renderizar pt sem parar e as línguas só
  entram no "tempo livre".
- O que fazer: em `_enviar`, gravar a lista num arquivo e usar `tar -T lista.txt` (idem `_baixar`, linha 57);
  e decidir com o dono um teto de pt adiantado menor (ex.: 4) pra sobrar tempo de língua no PC1.

### 5. Clips sem voz muito curtos e em sequência
- Meta do cap 10 (`acabamento.duracoes`): várias sequências de 1,5–1,9 s sem narração (ex.: 4 clips seguidos de
  1,87 s no fim). É o painel passando antes de dar tempo de ler o balão.
- O que fazer: mínimo por painel = tempo de ler o balão (já existe no longo: 15 letras/s + 1 s) também no
  vertical (`hiper-pipeline.py`, duração do clip sem fala).

### 6. Close sumiu nos capítulos explícitos (por regra)
- `efeitos 2.5D/close`: cap 1 close=10; cap 8 close=1; cap 9 close=3; cap 10 close=1. Causa:
  `hiper-pipeline.py:470-473` bloqueia close quando `cens_scores >= 0.25` (regra do dono: nunca close em painel
  sugestivo). Nos caps +18 (31–35% censurados) quase todo painel é "sugestivo", então sobra
  parallax/foco/profundidade.
- O que fazer: permitir close no ROSTO em painel sugestivo quando a caixa do rosto (YOLO) não cruza nenhuma
  região +18 do Gemini (`<md5>.regioes2.json`) — mantém a regra e devolve variedade. Decisão do dono.

### 7. Visão do Gemini: erro 400 sem modelo no log e modelos de IMAGEM no pool de visão
- `logs/fila_the-inheritor-cap11.log`: tempestade de 429 em todas as chaves e "HTTP 400: Request contains an
  invalid argument" repetido; a reserva via proxy responde (lenta). Em `bin/gemini_llm.py` a linha que loga o 400
  não grava o modelo (só código e mensagem), então não dá pra saber quem falha. O pool `VISION_MODELS`
  (`gemini_llm.py:100-111`) inclui `gemini-3.1-flash-image`, `-image-preview`, `gemini-2.5-flash-image` (modelos
  de GERAR imagem) pra descrever painel.
- O que fazer: logar `model` e `key` no 400; testar tirar os modelos "-image" do pool de visão e medir o tempo
  da etapa (cap 11: ~5 min pra 40 painéis).

### 8. Trilhas com Content ID (decisão do dono, risco registrado)
- `D:\hipercool-materiais\assets\trilhas\prioritarias\`: Hans Zimmer (Cornfield Chase), Re:Zero (Styx Helix,
  creepy theme), HxH, Tensura OST, MC Jhey, Infraction phonk. Tocam ~85% das vezes; 6 faixas em 6,4 min no cap 10.
- Risco: reivindicação em todo vídeo (receita vai pro dono da música) e, com pedido de remoção, strike.
  O canal pt já tem advertência de direitos autorais (08/10) e o fr um strike — conferir no Studio se a
  origem foi música ou painel.

### 9. Balões em português nos vídeos das línguas
- Os painéis vêm do scan brasileiro; em hindi/thai/russo o balão na imagem fica em português e a legenda
  traduzida só cobre a fala (CLAUDE.md, "Legenda nos idiomas"). Pra esse público o texto na tela é ruído.
- O que fazer (custo baixo primeiro): nos Shorts das línguas, cobrir o balão com a legenda traduzida no lugar
  dele (a máscara de balões já existe em `censura_visual._mascara_baloes`); depois avaliar OCR + inpaint.

### 10. Pendências antigas que continuam valendo (docs já listam; não foram feitas)
- B2 OCR dos balões + seta (quem fala) — `docs/correcoes_pendentes.md`.
- C4 ritmo por painel / corte no tempo da música; C5 "no capítulo anterior / próximo capítulo".
- Biblioteca de efeitos do 16:9 (`docs/longo_efeitos.md`: itens 1–11, só o básico entrou).
- Abertura com voz humana no completo vertical (hoje só no compilado) — `PEDIDOS…` item 5 "Falta".
- Elenco fixo nas línguas (`idiomas._perfil` por md5, sem normalizar apelido) — item 11b "Falta".
- TTS local como reserva no PC2; Groq no PC2 (tempo por palavra proporcional lá).
- Shorts das línguas não ligam no catálogo do postador (backup/reuso TikTok) — `correcoes_pendentes.md`.

## Outros achados menores
- `workspace/shorts/` tem as partes do cap 2 soltas na raiz E na pasta `the-inheritor-cap2/` (duplicado).
- `workspace/videos/` raiz guarda 4 capas antigas do cap 2 (sobra da organização de 14/10).
- `fila_postagem.log` 20:48: "extras do Studio falharam: 'list' object has no attribute 'items'" e "métricas:
  0 vídeo(s)" — frente do outro agente (código de hoje), só registrado aqui.
- Cap 6 continua `sem_censurado` (passe final travou 2 h em 15/10 de madrugada); não foi refeito.

## Como continuar
1. Rodar de novo o workflow (`workspace/tmp/auditoria_15out/workflow_auditoria.js`) — ou só as 6 lentes que
   faltaram (longo, línguas, produção, alcance, capa, espectador) e a verificação.
2. Aproveitar as evidências já extraídas em `workspace/tmp/auditoria_15out/<lente>_evidencias.txt`.
3. Priorizar com o dono: itens 1, 2 e 4 (decisões) e 3, 5, 7 (correções de código pequenas).
