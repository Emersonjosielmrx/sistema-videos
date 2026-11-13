# Auditoria dos vídeos — o que pode melhorar (15–16/10/2026)

Pedido do dono: "fora o que o outro agente está fazendo, veja tudo que pode melhorar nos vídeos do hipercool".

**Método.** Auditoria em paralelo com 12 lentes (uma por área), cada agente com ordem de só ler, e de provar cada
achado com arquivo:linha, linha de log, medição (ffprobe/ffmpeg) ou quadro extraído e olhado. **5 lentes
terminaram** (narração, voz, imagem, censura/segurança, Shorts) e entregaram 54 achados. **6 lentes não rodaram**
(acabaram os créditos da conta no meio: longo 16:9, línguas, produção, alcance/postagem, capa, espectador). A
**verificação adversarial não rodou** em nenhum achado, nem a síntese automática — este texto foi montado à mão a
partir dos achados brutos. Os 15 itens `previo-*` são do coordenador (eu), confirmados em código/log antes de
lançar as lentes.

**Confiança.** Cada achado traz a evidência que o agente diz ter visto. O que está marcado com ⚠️ ainda não foi
conferido por ninguém além de quem achou. Antes de mexer em produção, reconfira a evidência citada — ela é
específica o bastante pra isso (arquivo, linha, segundo do vídeo).

> **CORRIGIDO em 16/10** (`bin/censura_visual.py`, `bin/hiper-pipeline.py`): `seguranca-01` (parser de
> caixas), `seguranca-02` (mosaico de 1%) e a parte de `narracao-12` que era bug. Conferido painel a painel
> nos caps 1–10: 2 painéis que saíam intactos agora são censurados e 6 com mosaico invisível viraram fosco;
> 99 painéis não mudaram. O que o Gemini libera continua intacto — conferi que os casos de score alto que ele
> liberou são um casal vestido e uma mão apontando. **Falta decidir**: os vídeos já renderizados dos caps 3,
> 5, 8, 9 e 10 têm esses painéis, e o compilado `caps01-11` com eles foi postado em 16/10 01:52.

Material bruto: `workspace/tmp/auditoria_15out/` (`<lente>_evidencias.txt` = comandos e saídas de uma rodada,
`quadros/` = quadros extraídos, `achados_5_lentes_rodada2.json` = os 69 achados crus, `workflow_auditoria.js` =
o roteiro pra rodar de novo).

---

## Fora desta lista (outro agente já está fazendo)

1. Capas do cap 7 com as poses novas e as primeiras capas verticais dos Shorts.
2. Extras do Studio depois da verificação (fixar comentário, vídeo relacionado, teste A/B).
3. Leitor de métricas do Studio (retenção 30 s, CTR, capa vencedora) alimentando os rodízios.
4. Detector/limpeza da propaganda e da marca do scan (BLACKOUTCOMICS.COM).
5. Revisão independente do código escrito em 15/10.

## O que ficou sem auditar

Longo 16:9 (compilado), outras línguas, produção/robustez, alcance e postagem, capa (gerador), e a lente
"espectador" (assistir os primeiros 30 s como público). O que existe sobre essas áreas aqui veio dos itens
`previo-*`, que são rasos perto do resto. Pra completar: rodar `workspace/tmp/auditoria_15out/workflow_auditoria.js`
só com essas lentes.

---

## Resumo executivo

1. **Tem nudez sem censura na versão que vai pro YouTube.** Três falhas diferentes e independentes: um erro de
   parser que transforma "explícito, 2 regiões" em "intacto" [seguranca-01], caixas de 1% do painel que viram
   mosaico invisível [seguranca-02], e painel de fluido que nenhum detector pega [imagem-02, seguranca-03]. No
   cap 10 isso dá pelo menos 4 painéis com seios/genital nítidos no arquivo marcado "pronto". Ninguém olha a folha
   de quadros antes de postar [seguranca-07]. **É o que tem que ser consertado primeiro.**
2. **O áudio entrega o que a imagem esconde.** O narrador descreve o ato ("líquido branco gotejando", "som de
   sucção"); o YouTube transcreve. O maior canal do nicho não usa nenhuma dessas palavras em 367 mil palavras
   medidas [narracao-01]. A legenda pop ainda queima as mesmas palavras em letra gigante [seguranca-03].
3. **Metade do roteiro é enchimento por causa de uma regra do próprio prompt.** A visão responde "Cena intensa"
   em 26 dos 80 painéis do cap 10, e o narrador, proibido de inventar, escreve frase que serve pra qualquer cena
   [narracao-02]. É a causa mecânica do "detalhes não ficam claros" que o dono reclamou.
4. **Um bug de enquadramento deforma 30–40 clips por capítulo.** Todo clip sem 2.5D passa por `zoompan` com
   `s=720x1280` sem corrigir proporção: painel alto fica achatado, painel médio esticado [imagem-01]. O vídeo
   alterna rosto certo (caminho OpenCV) e rosto deformado (caminho ffmpeg).
5. **Os Shorts cortam no meio da fala** (4 de 5 cortes no cap 2) e terminam com 3,5 s de tela parada e muda
   [shorts-01, shorts-02]; o render de cada parte não é determinístico [shorts-03].
6. **A punição dos canais provavelmente não veio da narração.** O registro do projeto diz direitos autorais, e as
   datas mostram que o canal pt foi advertido antes de qualquer vídeo do hipercool subir nele [seguranca-04].
   Isso corrige o que eu havia escrito no relatório parcial: corrigir a narração é prevenção, não conserto.
7. **O backup dos caches de 15/10 abortou** e ninguém foi avisado; é a única proteção das vozes e dos roteiros
   [voz-10].

---

## Top 12 por impacto

| # | Achado | Por quê | Esforço | Área |
|---|---|---|---|---|
| 1 | [seguranca-01] Parser perde as caixas e painel explícito sai intacto | Cap 10 painel 27: Gemini disse "explícito" com 2 caixas, vídeo postável mostra nudez frontal | P | Censura |
| 2 | [seguranca-02] Caixa de 1% = mosaico invisível | 10 painéis "censurados" com ≤2% de cobertura e score até 2,04 | P | Censura |
| 3 | [imagem-02] Fluido no rosto/mãos passa sem censura e ainda ganha close | Score 0,02–0,32 não chama o Gemini; 6 s em close | M | Censura |
| 4 | [imagem-01] `zoompan` deforma todo clip sem 2.5D | Círculo de teste vira 0,55 de proporção em painel 3,2:1; 30 de 79 clips no cap 10 | P | Imagem |
| 5 | [narracao-02] "Cena intensa" em 1/3 dos painéis gera enchimento | 26/80 no cap 10; 43% de enchimento no cap 8 | P | Roteiro |
| 6 | [narracao-01] Narração explícita transcrita pelo YouTube | MomoManhwa: 0 ocorrências de sexo/gozar/gemendo em 367 mil palavras | P | Roteiro |
| 7 | [shorts-01] Shorts cortam no meio da palavra | 4 de 5 cortes do cap 2 caem dentro de uma palavra do alinhamento Groq | P | Shorts |
| 8 | [voz-01] Gemidos soletrados letra por letra | Groq transcreve o áudio final como "N.N.G.H." e "NGH NGH NGH NGH" | P | Voz |
| 9 | [narracao-03] Roteiro não sabe o que houve no capítulo anterior | 0 ocorrências de "capítulo anterior" em 8 roteiros; cap 8 chama o protagonista de "voz misteriosa" | M | Roteiro |
| 10 | [voz-10] Backup dos caches abortou em 15/10 sem aviso | Tarefa terminou 0x8007042B; nenhum log do dia; roteiros e censura não foram copiados | P | Produção |
| 11 | [shorts-02] Cartão final mudo de 3,5 s em todas as partes | Vídeo − áudio = 3,4–3,5 s nas 24 partes medidas; quebra o loop do Short | P | Shorts |
| 12 | [seguranca-06] Um terço do vídeo é sexo mosaicado e a fila aprova sozinha | 24–38 painéis por capítulo; único filtro é "< 50% censurado" | M | Censura |

---

## Bugs que estragam a produção agora

- `bin/censura_visual.py` `_parse_caixas`: regex não casa `"box_2d": [[y,x,y,x]]`; o painel vai pro vídeo intacto
  e o log diz "visão julgou não explícito" [seguranca-01].
- `bin/fx_clips.py:409-427`, `:545-550`, `:613-618`: `zoompan` com `s=720x1280` sem normalizar a proporção antes
  [imagem-01].
- `bin/narration.py:133-139`: regex `_SOM` não cobre `ngh`, `uungh`, `kyah`, `hmph` — o TTS soletra [voz-01].
- `bin/elenco.py:252-261` e `bin/idiomas.py:160`: texto vai cru pro edge, sem `clean_for_tts` (hangul e "(sorriso)"
  são lidos em voz alta) [voz-02].
- `bin/idiomas.py:156-164`: uma tentativa só no TTS das línguas; falha vira painel mudo de 0,8 s e o vídeo sai
  "pronto" (7 painéis no cap 1 tailandês, 2 no cap 2 hindi) [voz-06].
- `bin/backup_caches.py`: copia o `tts_cache` primeiro (1h54 de rclone) e morre antes dos roteiros; não avisa
  ninguém [voz-10].
- `bin/pc2.py:46` e `:57`: lista de arquivos na linha de comando do `tar` estoura o limite do Windows
  (WinError 206) [previo-04].
- `bin/split-shorts.py`: três encodes com streams incompatíveis; uma parte saiu com cartão de 7,3 s quase preto,
  outra sem cartão [shorts-03].

---

## Censura e segurança

### ⚠️ [seguranca-01] Gemini disse "explícito" com 2 regiões, o parser perdeu as caixas e o painel saiu intacto
Quando a resposta vem com colchete duplo (`"box_2d": [[y,x,y,x]]`), `_parse_caixas` não lê nada; `localizar_regioes`
devolve `[]`, que é o mesmo valor de "não explícito", e `censurar_imagem` grava "intacto".
**Evidência:** `workspace/censura_cache/<md5 panel_027 cap10>.regioes2.json` tem `explicito: true` com caixas de
"genitalia" e "mamilo"; log 19:30:58 "panel_027.jpg -> intacto (score=2.08, visão julgou não explícito)"; quadro aos
158,1 s do cap 10 **censurado**: homem nu de corpo inteiro e moça nua com mamilos nítidos. 4 de 218 respostas no
cache têm esse formato e todas perdem 100% das caixas.
**O que fazer:** aceitar `\[\s*\[?` no regex; `localizar_regioes` devolver `None` (não `[]`) quando é explícito e não
saiu caixa, pra cair no fosco; nunca deixar intacto quando `score >= LIMIAR_NSFW` e `sexual_display >= 0,3`. O cache
guarda a resposta crua, então corrigir o parser já conserta os painéis antigos sem gastar chamada.
**Esforço:** P · **Prioridade:** alta

### ⚠️ [seguranca-02] Caixa de 1% do painel: mosaico invisível, seios nítidos na versão postável
O Gemini marca uma região minúscula e o pipeline aceita qualquer fração maior que zero como censura "local".
**Evidência:** cap 10 panel_028 (720x1836), uma caixa de ~31x65 px, log "local (1% do painel)", Sightengine
sexual_activity 0,97; quadro 160–166 s do censurado: moça nua com os dois seios nítidos por 6 s. Também panel_024
(28x76 px) e, no cap 8, os painéis 023, 037, 056, 061, 104 — 10 painéis com ≤2% de cobertura e score 0,84–2,04.
**O que fazer:** com `score >= LIMIAR_NSFW` e fração < 3%, pedir segunda localização ("liste TODOS os mamilos,
genitais e nádegas, um box por item") e, se continuar pequena, ir pro fosco; folga mínima absoluta por caixa.
**Esforço:** P · **Prioridade:** alta

### ⚠️ [imagem-02] Fluido no rosto e nas mãos passa sem censura e ainda recebe close
O Sightengine só pontua ato e nudez; rosto com líquido branco ou mãos com fluido ficam abaixo de 0,45 e nem chegam
ao Gemini.
**Evidência:** cap 10 clip 13 (painel 12, modo foco, 6,17 s): rosto com líquido branco na boca, score 0,3162; clip 8
(painel 7, parallax, 6,3 s): mãos e pele com fluido, score 0,0227. Nenhum dos dois está na lista de censurados do
meta. Narração do painel 14: "a gente vê o líquido branco gotejando".
**O que fazer:** quando a descrição ou a fala tiver fluido/líquido/gotejando/sucção/engol, mandar pro Gemini mesmo
com score baixo, pedindo também "fluido corporal sobre pele ou rosto" como região; nesses painéis proibir close e
foco.
**Esforço:** M · **Prioridade:** alta

### ⚠️ [narracao-12] Painel marcado +18 pelo Sightengine sem mosaico no cap 10 (32,5 s)
Achado de fora da lente, ao conferir a narração do "balão de libido".
**Evidência:** log linha 6 "Censura: 32/80 painéis +18 [1, 2, 6, 10, 11, ...]"; o meta não tem janela de censura
entre 18,2 s e 53,7 s; o clip do painel 6 é 29,38–35,62 s; quadro aos 32,5 s do arquivo CENSURADO mostra a
personagem de boca aberta e um seio com a mão por cima, sem mosaico.
**O que fazer:** quando o Sightengine marca +18 e o detector local não acha região, aplicar fallback (fosco) em vez
de deixar passar. Conferir os outros painéis da lista do log que não têm janela no meta.
**Esforço:** P · **Prioridade:** alta

### ⚠️ [seguranca-07] Ninguém olha a imagem censurada antes de postar
A "revisão da folha" virou checagem automática que só olha validação e fração censurada. Os erros acima saíram no
cap 10 com situação "pronto".
**Evidência:** `hiper-pipeline.py:302-304` só loga "revise a folha"; `fila.py:334-348` gera a folha e ninguém lê;
`fila.py:353` posta com `--aprovado`.
**O que fazer:** rodar o Sightengine na imagem **já censurada** dos painéis "local" e dos "intacto com score alto"
(24–38 chamadas por capítulo, com cache); se ainda pontuar, refazer como fosco; se insistir, marcar "revisar" e
mandar a folha pelo Telegram em vez de postar.
**Esforço:** P · **Prioridade:** alta

### ⚠️ [imagem-03] Mosaico cobre 45–72% da tela por 5–7 s e ainda ganha parallax
**Evidência:** meta do cap 10: panel_015 "1 região, 72% do painel" (clip de 6,63 s, modo parallax), panel_080 61%,
panel_036 54%, panel_037 e 038 45%. Quadro do clip 16: tela inteira pixelada, só a legenda legível. O limiar que
troca local por fosco (que fica melhor) só dispara acima de 80%.
**O que fazer:** baixar `CENSURA_MAX_FRAC_LOCAL` pra ~0,40 e não aplicar parallax/foco em painel com mosaico grande.
**Esforço:** P · **Prioridade:** média

### ⚠️ [seguranca-06] Um terço do vídeo é sexo mosaicado e o único filtro é "< 50%"
**Evidência:** cap 8 144 s de 411 s (35%, 38 painéis), cap 9 132/461 (29%), cap 10 119/384 (31%);
`fila.py:334-348` aprova sozinho abaixo de `max_censura` 0,5. A referência do nicho sugere a cena em 1–2 painéis.
**O que fazer:** decisão do dono — baixar `max_censura` do avulso pra ~0,2 e condensar a sequência de sexo em 1–2
painéis sugeridos (pular os demais na seleção de painéis, com a narração resumindo), em vez de 24 painéis
mosaicados. Shorts: pular parte com mais de 20% censurado.
**Esforço:** M · **Prioridade:** média

### ⚠️ [seguranca-05] "QUER SEM CENSURA?" na tela 7 vezes, na descrição e no comentário
**Evidência:** `fx_acabamento.py:856-884`; log do cap 10 "chamada 'SEM CENSURA' em 7 de 13 trechos censurados";
quadros mostram o cartaz sobre corpo nu mosaicado. A política de nudez cobre oferecer acesso a conteúdo sexual
explícito; as diretrizes de anúncios limitam vídeo com referência sexual em título ou descrição. Sem link, é
plausível, não regra literal.
**O que fazer:** manter a medição só no comentário fixado (que é o que o dono pediu) e tirar o cartaz da tela e o
parágrafo da descrição; ou trocar por "quer a versão COMPLETA? comenta COMPLETA".
**Esforço:** P · **Prioridade:** média · Decisão do dono

### ⚠️ [seguranca-04] As punições dos canais vieram de direitos autorais, não da narração
Corrige o que eu havia afirmado no relatório parcial.
**Evidência:** `docs/correcoes_pendentes.md:17-18` ("fr = advertência de direitos autorais, strike 27/09; en =
bloqueou envios por avisos das diretrizes"); CLAUDE.md ("InovareManhwaVerse preso no aviso de advertência de
direitos autorais, 08/10"); `D:/postador-de-videos/logs/uploads_ledger.jsonl`: o canal pt tem 0 uploads antes de
15/10/2026 01:11, e o primeiro render do hipercool é de 13/10. A mensagem da verificação negada fala do histórico
anterior do canal.
**O que fazer:** abrir no Studio a página de direitos autorais e a de diretrizes do pt e do fr e registrar a origem
real; se for música, rever a lista de trilhas prioritárias. Os itens de narração continuam valendo como prevenção.
**Esforço:** P · **Prioridade:** média

### ⚠️ [seguranca-08] Fallback de título/tags não passa pelo dicionário seguro
**Evidência:** `postar_hipercool.py:254-265` aplica só `_sem_obra`; `_sanitizar_seo` só roda dentro de
`seo.pacote()`. O título do roteiro do cap 10 é "ELA ACEITOU SER A ESCRAVA DELE?! - THE INHERITOR CAP 10" e
"escrava" está na lista de proibidas. Na noite de 15/10 o SEO caiu em 429 em todas as chaves — é exatamente quando
o fallback entra.
**O que fazer:** aplicar `seo._sanitizar_seo` antes de `_sem_obra` no fallback (completo e Shorts) e sanitizar
`titulo_video`/`tags` em `narration.py` antes de gravar no cache.
**Esforço:** P · **Prioridade:** média

### ⚠️ [seguranca-09] A versão normal do pt nunca é postada mas custa 20 min de passe final e até 480 MB
**Evidência:** `fx_acabamento.py:1773-1774` (`so_censurado` só quando é idioma); log do cap 10: passe final do
normal das 19:41 às 20:03; pastas `pt/normal` dos caps 7–10 com 480M/428M/311M/210M.
**O que fazer:** rodar o pt com `so_censurado=True` por padrão, com variável de ambiente pra ligar quando o dono
quiser ver a versão sem censura; apagar os normais dos capítulos já postados na limpeza.
**Esforço:** P · **Prioridade:** baixa

### ⚠️ [seguranca-10] Cache da censura é pelo md5 do arquivo: painel reescrito paga tudo de novo
**Evidência:** a chave de `<md5>.json` e `<md5>.regioes2.json` é o md5 do jpg atual; caps 2, 3, 6 e 7 têm 15–20
painéis em `_originais/` sem cache correspondente. Uma das 4 chaves Sightengine já esgotou em 15/10.
**O que fazer:** ao reescrever um painel, copiar as entradas do md5 antigo pro novo; ou chavear pelo md5 do
`_originais/<nome>` quando existir.
**Esforço:** P · **Prioridade:** baixa

---

## Narração e roteiro

### ⚠️ [narracao-02] A visão responde "Cena intensa" e o narrador enche linguiça
O prompt da visão manda descrever conteúdo adulto "só como cena intensa", e o da narração manda narrar "apenas o
que está descrito". O narrador fica sem fato pra contar.
**Evidência:** `narration.py:328-329` e ~575-577; 26 dos 80 painéis do cap 10 têm só "Cena intensa" na descrição;
as locuções correspondentes são "o clima entre os dois continua pegando fogo", "a energia no quarto só aumenta",
"a interação segue sem freio". Enchimento medido: 34% no cap 10, 43% no cap 8, 29% no cap 9. E quando a visão
resolve descrever, passa o detalhe explícito ("marcas de fluido").
**O que fazer:** trocar a regra da visão por "diga quem está com quem, onde, a emoção de cada um e quem controla a
situação, sem anatomia, roupa, fluido nem som"; na narração, "painel íntimo: 1 frase sugerindo + o que isso muda na
relação". Resolve o enchimento e a explicitação pelo mesmo caminho.
**Esforço:** P · **Prioridade:** alta

### ⚠️ [narracao-01] Narrador e personagens descrevem o ato; os canais grandes só sugerem
**Evidência:** roteiro do cap 10: "VOU GOZAR!!" aos 10 s, "solta um gemido alto", "líquido branco gotejando...
o serviço foi completo", "som de sucção", "som de deglutição". `narration.py:509-511` manda manter o balão "sem
suavizar palavras fortes"; o dicionário não tem gozar, gemido, fluido, sucção, deglutição, engolir. No MomoManhwa,
3 transcrições (367 mil palavras): sexo 0, transar 0, gozar 0, gemendo 0 — a cena íntima vira "Ela toda grudadinha
ali, tão quentinho... O quarto do capiroto, moleque".
**O que fazer:** bloco "CENA +18" no prompt (sugerir em 1 frase e contar a consequência, nunca ato, parte do corpo,
fluido ou som); tirar "palavrão ficam" da regra do balão; ampliar o dicionário e aplicá-lo também nas falas de
personagem. Medir: zero palavras da lista nos roteiros novos.
**Esforço:** P · **Prioridade:** alta · Balões literais são decisão do dono

### ⚠️ [narracao-03] O roteiro não sabe quem é quem nem o que houve antes
A única memória entre capítulos é a ficha de nomes.
**Evidência:** `narration.py:440-463` e 563-569; nos 8 roteiros, "capítulo anterior" e "próximo capítulo" aparecem
0 vezes; o cap 8 abre com "uma voz misteriosa exige o que quer" (é o protagonista), o cap 9 com "alguém ali leva um
susto", o cap 10 com "finalmente conseguiu o que queria" sem dizer o quê, o cap 5 com "pede desculpas pelo ocorrido".
**O que fazer:** uma "bíblia" da obra (premissa em 2 frases, quem é quem, resumo de 2 frases por capítulo gerado uma
vez) injetada no prompt; primeira locução com "no capítulo anterior"; última com gancho e "no próximo capítulo".
**Esforço:** M · **Prioridade:** alta

### ⚠️ [narracao-04] O narrador dubla o desenho: balão de efeito, linhas de velocidade, "a câmera"
**Evidência:** cap 10, 16 das 55 falas do narrador (29%): "até um balão de libido surge flutuando", "com as linhas
de velocidade na tela", "reagir só com símbolos de coração", "rola um close no rosto dela", "a gente vê o perfil
deles"; cap 1 "aí aparece o logo do site". Quadros conferidos aos 32,5 s e 56,9 s.
**O que fazer:** na visão, "painel que é só efeito gráfico: responda TRANSIÇÃO + a emoção que ele reforça"; na
narração, proibir narrar balão, linhas, close, foco, câmera, logo e título. Checagem por regex depois, reescrevendo
só as falas que caírem.
**Esforço:** P · **Prioridade:** média

### ⚠️ [narracao-05] Texto de narrador sai na voz do personagem
**Evidência:** cap 8, falas 87, 88, 90 e 107 com persona de personagem e texto em terceira pessoa — a Ava (voz da
Yeseul) diz "A moça espalha o fluido no rosto, que isso, gente?" e o Andrew diz "O Joo Inhyuk tá em choque". No cap 2,
"Rapaz" diz "Ela acabou de dizer isso mesmo?!". A revisão por LLM está desligada porque errou no teste.
**O que fazer:** regra fixa em `falantes.py` (sem LLM): fala de personagem que contém o próprio nome em terceira
pessoa, "a moça", "o cara", "nosso garoto", "a gente vê", "dá uma olhada" vira narrador. Testar nos caches dos
caps 2 e 8 (deve pegar os 8 casos e nenhum falso positivo).
**Esforço:** P · **Prioridade:** média

### ⚠️ [narracao-07] Balão partido em vários painéis vira 3–4 falas de 1–2 palavras
**Evidência:** cap 10, falas 72–75 ("P-PERAI... ?", "VOCÊ DISSE QUE...", "ERA PRA GENTE...", "COMPRAR ROUPA...") em
4 clips seguidos de 1,87 s sobre painéis de cenário vazio. Falas de personagem com até 2 palavras: 13 de 25 no
cap 10, 21 de 43 no cap 11, 20 de 30 no cap 9.
**O que fazer:** juntar falas consecutivas do mesmo personagem quando a anterior termina em reticências ou tem até
3 palavras, deixando o painel seguinte com narrador curto ou mais tempo de tela.
**Esforço:** P · **Prioridade:** média

### ⚠️ [narracao-08] A correção de abertura e gancho não vale pros capítulos já roteirizados
`_abertura_e_fim` foi escrita depois do roteiro novo do cap 1 e só roda dentro de `gerar_recap`; quando o cache
existe, não passa por lá.
**Evidência:** `narration.py:192-237` e 659; `hiper-pipeline.py:212-215`; mtime do arquivo 15/10 05:27 contra o
roteiro do cap 1 das 02:56. O cap 1 — porta de entrada de quem nunca viu a obra — abre com "o dia começa como
qualquer outro, com o prédio da escola sob um céu bem claro" e termina com o personagem dizendo "Herança?!", sem
gancho.
**O que fazer:** guardar uma flag no cache e rodar `_abertura_e_fim` também no caminho de cache quando faltar
(1 chamada de LLM e 2 falas de TTS). O cap 1 está sendo renderizado nas línguas agora: pega a correção.
**Esforço:** P · **Prioridade:** média

### ⚠️ [narracao-10] `titulo_video` e tags do roteiro levam o nome da obra e palavra proibida
**Evidência:** cache do cap 10 e do cap 11 ("...NO CAPÍTULO 11 DE THE INHERITOR"); `narration.py:538-545` pede
título e tags sem regra e sem dicionário; `hiper-pipeline.py:876-877` grava no meta; `:907` usa como texto da capa;
`postar_hipercool.py:256` usa como fallback.
**O que fazer:** tirar título e tags do prompt de narração (o `seo.py` já faz isso direito) ou passar pelo
`_sem_obra` e pelo dicionário antes de gravar; no fallback da postagem, usar o gancho do editorial.
**Esforço:** P · **Prioridade:** média · Mesmo problema do [previo-03]

### ⚠️ [narracao-09] A revisão de coerência desfaz o dicionário seguro
`gerar_recap` sanitiza e só depois o pipeline chama `_revisar_coerencia`, que reescreve todas as falas do narrador e
grava sem sanitizar de novo.
**Evidência:** `narration.py:666` e 677-739; `hiper-pipeline.py:248-256`; palavras que reapareceram no texto final:
"morte" 3x e "morre" (cap 2), "bomba" e "tiro" (cap 3), "matando" (cap 4), "morrendo" (cap 10). É 1 das ~23 chamadas
Gemini do capítulo, sem medição do que melhora.
**O que fazer:** mover a sanitização pra depois da revisão; medir a revisão num capítulo (diff antes/depois) e, se
for cosmética, desligar e economizar a chamada. Rever trocas artificiais do dicionário ("carga explosiva sobre a
moradia").
**Esforço:** P · **Prioridade:** baixa

### ⚠️ [narracao-11] Bordões repetem acima do limite do próprio prompt e piadas saem literais
**Evidência:** cap 6 "rapaz" 7x e "nosso garoto" 5x em 69 falas; cap 10 "a gente" 7x e "porém" 5x em 55; cap 11
"nisso" 6x e "aí" 5x em 48; "dá uma olhada" abre 8 falas. Piadas dadas como exemplo no prompt saem literais ("F pro
nosso garoto!" fecha o cap 11). Entre capítulos não há frase repetida.
**O que fazer:** contagem pós-geração (sem LLM) e reescrita só das falas excedentes; tirar as piadas literais do
prompt, deixando só a descrição do estilo.
**Esforço:** P · **Prioridade:** baixa

---

## Voz

### ⚠️ [voz-01] Gemidos escapam do filtro e o edge soletra letra por letra
**Evidência:** `narration.py:133-139`; teste com as falas reais: "Ngh-", "Nnnngh!!", "Aangh... Hngh!!", "Uungh!",
"Nugh?!", "UNGH..!", "Nngh", "Hmph!" todas vão pro TTS. A transcrição Groq do áudio final registra "Vou gozar.
N.N.G.H." e "NGH NGH NGH NGH NGH". Cada uma ocupa um clip de 1,87 s no clímax da cena.
**O que fazer:** ampliar o regex (`n+g+h+`, `[aeiou]+n+g+h+`, `h+m+p+h+`, palavra curta só de consoante) e, quando a
reescrita pelo LLM falhar, não mandar a fala ao TTS em vez de soletrar.
**Esforço:** P · **Prioridade:** alta

### ⚠️ [voz-02] Texto coreano e rubrica "(sorriso)" vão pro edge
O filtro `clean_for_tts` só é aplicado no caminho do Gemini; `elenco.falar_edge` e `idiomas.falar` mandam o texto cru.
**Evidência:** log do cap 9: "Noh Yeseul (Ava) — 싱긋 (sorriso)" e "Joo Inhyuk (Andrew) — 푹 (impacto) 웩 (reação)";
`hiper-pipeline.py:347` → `elenco.py:252-261`.
**O que fazer:** passar o texto por `clean_for_tts` nos dois caminhos e remover hangul/CJK e parênteses de rubrica;
se sobrar vazio, tratar como fala só de som.
**Esforço:** P · **Prioridade:** média

### ⚠️ [voz-05] A cauda de silêncio do edge vira painel parado
Correção importante do que eu havia escrito no parcial: os clips de 1,87 s **não** são painéis sem voz — têm voz
de 0,6–0,8 s e depois 1,1 s de silêncio do próprio edge.
**Evidência:** `silencedetect` nos wavs do cache: "ENTÃO?" fala de 0,11 a 0,56 s num arquivo de 1,872 s; idem
"P-PERAI... ?", "Ngh-", "COMPRAR ROUPA...". `fx_clips.py:379-389`: a duração do clip é a do wav. 18 dos 82 clips do
cap 10 são assim.
**O que fazer:** cortar a cauda na conversão (`areverse,silenceremove,areverse`, deixando ~0,25 s) e decidir a
duração do clip pelo tempo de leitura do balão, não pelo tamanho do wav.
**Esforço:** P · **Prioridade:** média

### ⚠️ [voz-06] Nas línguas o TTS não tenta de novo: falha vira painel mudo e o vídeo sai "pronto"
**Evidência:** `idiomas.py:156-164` (uma tentativa) contra `elenco.py:259-267` (4 tentativas no pt);
`hiper-pipeline.py:383-394` gera "clip rápido" de 0,8 s. No cap 1 tailandês foram 7 falas perdidas (painéis 33, 34,
61, 73, 96, 103, 105 de 106); no cap 2 hindi, 2 — e os dois vídeos foram marcados prontos.
**O que fazer:** mesmo laço de tentativas nas línguas, registrar no limitador na última, e tratar "clip rápido por
falha de TTS" como reprovação na validação (refazendo só o painel).
**Esforço:** P · **Prioridade:** alta

### ⚠️ [voz-03] Nomes coreanos sem dicionário de pronúncia
**Evidência:** não existe mapa de pronúncia em nenhum módulo do caminho de voz (o único está num arquivo morto). A
transcrição Groq do áudio final do cap 10 mostra o resultado: "o Ezeu esquentou de vez no quarto" (Yeseul), "Você
disse que é Yueni, né? Sim, é escrava Yueni. Mestre Yuk" (Ye-Eun / Hyuk), "O Inhuk começa". O edge-tts escapa o
texto, então não dá pra usar `<phoneme>`: tem que ser reescrita fonética.
**O que fazer:** `config/pronuncia/<obra>.json` aplicado só no texto que vai pro TTS (não na legenda), com variante
por voz quando pt-BR e en-US soarem diferente.
**Esforço:** P · **Prioridade:** média

### ⚠️ [voz-04] Grito sai mais baixo que a narração; nenhuma prosódia por fala
**Evidência:** no mix final do cap 10, "VOU GOZAR!!" está a -17,2 LUFS contra -15,1 da narração anterior; nos wavs
do cache o RMS do grito é igual ao da narradora. `elenco.py:261` manda rate e pitch fixos por personagem; não há
nivelamento por fala.
**O que fazer:** derivar da pontuação (caixa alta ou "!!" → mais rápido, mais agudo, +3 dB; reticências → mais
lento) e nivelar cada wav a -20 LUFS na conversão. A chave de cache já inclui rate e pitch, então não invalida o
que existe.
**Esforço:** P · **Prioridade:** média

### ⚠️ [voz-07] As variações de voz não diferenciam: figurante ganhou a base da Professora
**Evidência:** no elenco do The Inheritor a Professora é Seraphina pura e a "mulher desconhecida" do cap 10 recebeu
Seraphina +8%/+4 Hz — 4 Hz em ~200 Hz é cerca de 0,3 semitom. Só narrador, protagonista e par têm base exclusiva, e
sobram 3 bases femininas.
**O que fazer:** base exclusiva para todo personagem nomeado enquanto houver base livre; passo maior nas variações;
pedir ao dono mais bases aprovadas.
**Esforço:** P · **Prioridade:** média

### ⚠️ [voz-08] Nas línguas, narradora e personagens usam a mesma voz
**Evidência:** `idiomas.py:18-33` tem uma voz feminina e uma masculina por língua; a Noh Yeseul hindi é a narradora
a -5%/-6 Hz; em tailandês a "Mulher" também.
**O que fazer:** usar o elenco fixo da obra também nas línguas (as vozes Multilingual falam hi/id/it/ru/th/vi), com
a narradora na voz nativa; onde não servir, cadastrar 2–3 vozes nativas por gênero.
**Esforço:** M · **Prioridade:** média · Mesmo tema do [previo-13]

### ⚠️ [voz-09] No motor gemini/misto a fala cai pra voz da narradora e o cache reusa voz de outro personagem
Latente hoje (o motor é edge), mas é o caminho que o dono quer como "misto".
**Evidência:** `tts_stage.py:143-146` (segunda tentativa grava com Kore, a voz da narradora); `tts_cache.py:36` e
69-79 (qualquer fala com até 3 palavras é reusada por gênero, não por voz) — 18 falas do cap 10 se encaixam.
**O que fazer:** não cair pra Kore quando o personagem tem voz fixa; incluir a voz na chave de cache das frases
curtas.
**Esforço:** P · **Prioridade:** média

### ⚠️ [voz-10] O backup diário dos caches abortou em 15/10 e ninguém foi avisado
**Evidência:** tarefa `BackupCachesHipercool`, última execução 15/10 06:10, resultado 0x8007042B (processo
encerrado); `logs/backup_caches.log` termina em 14/10; o rclone passou 1h54 só no `tts_cache` (1347 arquivos,
254 KiB/s) e morreu antes de copiar `narration_cache` (o mais caro, de LLM) e a censura. Desde que as vozes sumiram
em 12/10 "por causa desconhecida", essa cópia é a única rede.
**O que fazer:** copiar roteiros e censura antes do `tts_cache`, logar o início de cada pasta, avisar no Telegram
quando falhar, e usar `--transfers 8 --checkers 16 --max-age 3d` pra copiar só o novo.
**Esforço:** P · **Prioridade:** alta

### ⚠️ [voz-11] `edge_tts_engine.py` está morto mas ainda tem a Francisca (proibida) como padrão
**Evidência:** nenhum módulo importa o arquivo; ele tem `pt-BR-FranciscaNeural` como voz padrão, narradora e no pool
feminino. O item 11 dos pedidos ainda cita o arquivo como se estivesse em uso.
**O que fazer:** renomear pra `.bak` (ou apagar) e corrigir a menção no documento de pedidos.
**Esforço:** P · **Prioridade:** baixa

---

## Imagem e efeitos

### ⚠️ [imagem-01] Todo clip sem 2.5D sai deformado
O `zoompan` recorta uma janela e espreme pra 720x1280 sem respeitar proporção. Painel alto (acima de 2,0) passa por
`scale=1080:-1` e fica achatado; painel médio fica esticado na vertical.
**Evidência:** `fx_clips.py:409-427`, `fx_assets.py:34-46` e 86-90, `fx_clips.py:545-550` (shake) e 613-618 (flash).
Teste com um círculo pelo mesmo filtro: vira 0,55 de proporção em painel 720x2320, 0,84 em 720x1509, 1,14 sem
prescale. Quadros: a onomatopeia 푸확 do painel 3 aparece larga e baixa no vídeo e alta e estreita no original.
Atinge 30 dos 79 clips do cap 10 e 40 dos 107 do cap 8 — por isso o vídeo alterna rosto certo e rosto deformado.
**O que fazer:** levar o painel à proporção do canvas antes do `zoompan` (`scale`+`crop` 720x1280, ou pan por crop
com expressão em t), nos três caminhos. Conferir com o mesmo teste do círculo (tem que dar 1,00).
**Esforço:** P · **Prioridade:** alta

### ⚠️ [imagem-05] Balões cortados pela borda nos modos com zoom
O docstring promete que balões nunca são cortados, mas o painel é encaixado na largura e ainda ganha zoom inicial.
**Evidência:** `fx_parallax.py:7`, `:540-541`, `:577-586`. Quadros: clip 27 (modo tensão) com o topo do balão "..."
cortado; clip 53 com "TÁ TUDO BEM" cortado embaixo, só "TÁ" e parte de "TUDO" visíveis; clip de profundidade com
fragmento de balão cortado. A função que acha os balões já existe, mas não entra no enquadramento.
**O que fazer:** calcular a janela vertical de modo que as caixas dos balões fiquem dentro da tela e limitar o zoom
quando isso quebrar.
**Esforço:** M · **Prioridade:** média

### ⚠️ [imagem-06] Close quase não acontece: além da regra +18, rosto grande é descartado
**Evidência:** `fx_parallax.py:44` aceita rosto entre 8% e 40% da largura; nos painéis de reação o rosto costuma
ocupar mais da metade. Dos 37 painéis do cap 10 com cache de rosto, só 5 passaram. Com a regra do +18 por cima, o
close caiu de 10 (cap 1) pra 1 (caps 8 e 10).
**O que fazer:** subir o limite pra ~0,65 e, com rosto grande, fazer close nos olhos em vez de punch-in. Liberar
close em painel sugestivo só quando a caixa do rosto não cruzar região +18 (decisão do dono).
**Esforço:** P · **Prioridade:** média · Mesmo tema do [previo-06]

### ⚠️ [imagem-04] Rajadas de clips de 1,5–1,9 s com cor, movimento e corte diferentes a cada 2 s
Cada clip sorteia o próprio filtro de cor e vinheta, então 4 painéis da mesma frase passam com 4 tons diferentes.
**Evidência:** cap 10 clips 73–76 (1,87 s cada) e 59–61; 20 clips abaixo de 2,2 s; `fx_clips.py:390`, `:394-401`,
`fx_assets.py:208-220`.
**O que fazer:** juntar falas curtas consecutivas num clip só e fixar o filtro de cor por cena, trocando só quando o
clima mudar.
**Esforço:** M · **Prioridade:** média

### ⚠️ [imagem-07] "Nunca dois efeitos seguidos" só vale pro parallax
**Evidência:** `hiper-pipeline.py:490` checa o anterior; `:494-497` (foco e profundidade) não; `:503-504` não
atualiza o controle no modo foco. No cap 10 repetem nos clips 14, 22, 29, 51, 52, 56 e 67.
**O que fazer:** guardar o modo anterior e trocar quando repetir.
**Esforço:** P · **Prioridade:** baixa

### ⚠️ [imagem-09] Painel largo vira quadro parado com barras chapadas
**Evidência:** `fx_clips.py:424-434` faz `pad` com cor fixa e nenhum movimento, apesar do docstring prometer fundo
borrado; mesmo caminho no shake e no flash. Quadro da cidade ao pôr do sol: faixa no meio com barras pretas por 5 s.
**O que fazer:** montar como o `fx_parallax` faz (o próprio painel borrado e escurecido ao fundo, nítido por cima,
com zoom leve).
**Esforço:** P · **Prioridade:** baixa

### ⚠️ [imagem-08] O espelhamento por língua inverte onomatopeias e letreiros
**Evidência:** `fx_parallax.py:48` (30% de chance) e `:751-755` (só checa se tem balão). Onomatopeias coreanas,
letreiros ("OPEN MOTEL"), placas e a marca do scan aparecem espelhados; painel com dois quadros tem a ordem de
leitura invertida.
**O que fazer:** desligar o espelho quando houver texto fora de balão, ou zerar a chance até existir detector;
variar por língua trocando o modo do efeito.
**Esforço:** P · **Prioridade:** baixa

### ⚠️ [imagem-10] Figurinha de comédia sobre a cena de sexo da abertura
**Evidência:** a primeira figurinha do cap 10 é o emoji chorando de rir, grande, sobre o painel 0, enquanto o
editorial escolheu clima tenso ("ELE ABRIU A PORTA E..."). `fx_acabamento.py:1752-1768` evita cobrir balão, mas não
olha o clima.
**O que fazer:** só permitir tags de comédia quando o clima do clip for de humor; nunca nos 10 primeiros segundos
nem em clip +18.
**Esforço:** P · **Prioridade:** baixa

---

## Shorts

### ⚠️ [shorts-01] Os cortes caem no meio da fala
A narração de um painel termina depois da fronteira do painel, então a parte acaba no meio da palavra.
**Evidência:** alinhamento Groq do cap 2 contra o `meta_shorts.json`: corte em 109,57 s dentro de "encaixa."
[108,80–109,96]; 163,84 dentro de "passou."; 217,78 entre "nada" e "por nós?"; 272,55 dentro de "qualquer". No
cap 1, 8 dos 9 cortes não têm pausa no ponto. A parte 3 abre com a legenda "ENCAIXA." sozinha.
**O que fazer:** no `plan_cuts`, aceitar a fronteira só se nenhuma palavra atravessa o ponto, com 0,3 s de folga;
na raiz, a duração mínima do clip no pipeline deveria ser o fim do áudio da locução mais 0,3 s (isso conserta o
completo também).
**Esforço:** P · **Prioridade:** alta

### ⚠️ [shorts-02] Cartão final de 3,5 s mudo e parado em todas as partes
**Evidência:** nas 24 partes medidas (cap 1 pt, cap 2 pt, cap 1 hindi), vídeo menos áudio dá 3,4–3,5 s em todas; o
cartão usa `anullsrc`, então a trilha morre de repente e o loop do Short quebra. O texto é o mesmo até na última
parte ("CONTINUA NO PRÓXIMO VÍDEO!"), enquanto dentro dela o completo diz "SEGUE PRO CAP. 3!" e o narrador pergunta
"Querem a parte 3?" — três chamadas diferentes no mesmo Short.
**O que fazer:** tirar o cartão parado e escrever "PARTE X/Y ▶ continua" sobre os últimos 2 s da própria cena, com
a trilha seguindo; na última parte, "FIM DO CAP. N → CAP. N+1".
**Esforço:** P · **Prioridade:** alta

### ⚠️ [shorts-03] O render de cada parte não é determinístico
Três encodes (trecho, cartão, concat) com streams incompatíveis (25 contra 30 fps, 44,1 contra 48 kHz).
**Evidência:** cap 2 parte 3 com 61,57 s em vez de 57,8 e um cartão de 7,3 s cujos 3 primeiros segundos são quase
pretos; parte 4 com 53,60 s e sem cartão nenhum. Cada parte passa duas vezes por libx264 CRF 23 (~2 min por parte,
3,0 Mbps contra 5,3 da fonte).
**O que fazer:** gerar cada parte num comando só (corte + texto final + reamostragem), um encode, e validar duração
e áudio antes de gravar o meta.
**Esforço:** P · **Prioridade:** alta

### ⚠️ [shorts-04] 6 a 11 partes por capítulo contra cota de 3 por dia
**Evidência:** cap 1 = 10 partes, cap 2 = 6, cap 7 = 11. Nas línguas são 2 Shorts por dia depois do completo, e a
fila sempre pega o capítulo mais antigo: o hindi subiu a parte 8 em 15/10 de um completo de 13/10. Em pt, a fila
repetiu "part_09=cota" a cada 20 minutos o dia inteiro. O limite de 58 s é de antes do YouTube aceitar Shorts de
3 min (e as partes já saem com 52–77 s).
**O que fazer:** decisão do dono — alvo de 110 s (máximo 170 s), o que dá 3–4 partes por capítulo com o mesmo
render, ou subir só as 2–3 partes mais fortes e priorizar o capítulo mais novo.
**Esforço:** P · **Prioridade:** alta

### ⚠️ [shorts-06] Parte pulada por censura deixa buraco na numeração
A decisão de pular acontece depois de cortar, numerar e gerar os cartões.
**Evidência:** simulação sobre os metas: cap 8 parte 1/7 com 56% (pulada) e parte 6/7 com 50%; cap 9 parte 4/8 com
57%; cap 10 parte 4/7 com 68%, parte 5/7 com 44%. `postar_hipercool.py:614-618` roda depois de `cortar_shorts`.
**O que fazer:** calcular a fração censurada dentro do `plan_cuts`, escolher cortes que concentrem as janelas numa
parte, e excluí-la antes de numerar. Baixar o limiar pra ~35%.
**Esforço:** M · **Prioridade:** média

### ⚠️ [shorts-05] Shorts em pt sobem em rajada de madrugada
**Evidência:** no cap 1, as partes 1 a 8 subiram entre 05:27 e 06:09. `fila.py:391-401` não usa pico nem intervalo
no pt — só as línguas têm.
**O que fazer:** aplicar ao pt a mesma regra das línguas (1 por ciclo, intervalo de 2 h, janela de pico BR).
**Esforço:** P · **Prioridade:** média

### ⚠️ [shorts-07] Descrição idêntica nas 10 partes, sem "Parte X de Y" nem link pro completo
**Evidência:** `postar_hipercool.py:603-606` copia a mesma string pra todas; a linha "CONTINUA NA PARTE N" que o
`split-shorts` gera é descartada. Com o "vídeo relacionado" bloqueado pela verificação, a descrição é hoje o único
caminho do Short pro completo.
**O que fazer:** prefixar com "Parte X de Y", o link do completo (que já está no estado da postagem) e o da parte
anterior.
**Esforço:** P · **Prioridade:** média

### ⚠️ [shorts-08] Shorts em hindi e tailandês saem com tags em português
**Evidência:** `seo.py:174-184` não recebe idioma e lê um banco só em pt-BR; o cache tailandês tem as tags "todas
elas querem ele" e "ele herdou uma garota"; o hindi tem "manhwa recap pt br" e "recap manhwa português"; um título
em hindi traz "Completo".
**O que fazer:** banco por idioma montado com o autocompletar do YouTube naquela língua; enquanto não houver,
mandar o prompt traduzir e filtrar tags em alfabeto latino nos idiomas não latinos.
**Esforço:** M · **Prioridade:** média

### ⚠️ [shorts-09] Os Shorts das línguas levam a marca d'água do canal pt
**Evidência:** `hp_common.py:23` tem o handle como constante única e `fx_acabamento.py:806-807` grava no ASS o vídeo
inteiro; quadro do Short hindi mostra "@InovareManhwaVerse" no canto, balões em português e legenda em hindi.
**O que fazer:** campo `handle` por idioma na config e variável de ambiente no render das línguas.
**Esforço:** P · **Prioridade:** média · Balões: ver [previo-09]

### ⚠️ [shorts-10] Primeiro quadro da parte 1 é cara de clímax; o cartão final é topless borrado
**Evidência:** a parte 1 do cap 2 abre com o teaser, cujo primeiro quadro é rosto feminino chorando, corado, boca
aberta — exatamente o que o dono proíbe na capa; os Shorts do cap 1 subiram sem capa (as capas foram criadas às
12:48, depois do upload das 05:27), então é esse quadro que vira miniatura. O cartão da parte 6/6 usa o último
painel (topless com censura só no mamilo) borrado.
**O que fazer:** abrir com um quadro limpo quando não houver capa e usar a capa do capítulo como fundo do cartão;
no teaser, excluir painéis cuja fala é +18, não só pelo score.
**Esforço:** P · **Prioridade:** média

### ⚠️ [shorts-11] Partes 2 em diante abrem sem gancho e sem selo
**Evidência:** só a parte 1 herda o teaser; a parte 2 do cap 2 abre num painel cinza com uma onomatopeia e 1 s sem
legenda, a parte 3 na nuca do rapaz com a palavra "ENCAIXA.". O selo de capítulo só existe entre 0,3 e 6 s do
completo, então nenhuma parte além da primeira mostra onde o espectador está.
**O que fazer:** escrever nos 2 primeiros segundos de cada parte a provocação que o SEO já gera pra ela, mais o selo
"CAP. 2 • 3/6"; preferir fronteiras seguidas de painel com rosto ou impacto.
**Esforço:** M · **Prioridade:** média

---

## Alcance, línguas, produção e longo (sem lente: só os itens do coordenador)

Estas áreas **não foram auditadas** nesta rodada. O que segue é o que eu confirmei em código e log antes de lançar
os agentes.

### [previo-02] Completo vertical de 6–9 min cai no feed normal em 9:16
Vertical acima de 3 min não é Short. Os completos têm 0–5 views em 48 h; a referência do dono (Porão) estoura com
compilados 16:9 longos, e o 16:9 por capítulo já existe em `workspace/videos/longo/the-inheritor/capNN.mp4`.
**O que fazer:** testar postar o 16:9 por capítulo como "completo" e deixar o vertical só pros Shorts.
**Esforço:** P · **Prioridade:** alta · Decisão do dono

### [previo-04] PC2 quebrado e línguas sem tempo livre no PC1
`pc2.py:46` e `:57` passam centenas de nomes na linha de comando do `tar` (WinError 206 no fim do log); só o cap 1
existe nas línguas; `adiantado: 10` faz o PC1 renderizar pt sem parar.
**O que fazer:** usar `tar -T lista.txt`; combinar um teto menor de capítulos adiantados.
**Esforço:** P · **Prioridade:** alta

### [previo-07] Erro 400 da visão sem modelo no log; modelos de imagem no pool de visão
`gemini_llm.py:100-111` inclui `gemini-3.1-flash-image` e similares (modelos de gerar imagem) pra descrever painel, e
a linha que loga o 400 não grava qual modelo falhou.
**O que fazer:** logar modelo e chave no 400; testar tirar os modelos de imagem do pool e medir a etapa.
**Esforço:** P · **Prioridade:** média

### [previo-15] Cap 6 continua sem versão censurada e não foi refeito
`fila_estado.json` marca `sem_censurado` desde 15/10 de madrugada (o passe final travou 2 h). Agora que existe
limite de 1 h e fallback pro x264, dá pra refazer com cache, sem IA nova.
**Esforço:** P · **Prioridade:** média

### Outros itens do coordenador, ainda válidos
- [previo-10] OCR dos balões e direção da seta pra saber quem fala (B2 de `correcoes_pendentes.md`).
- [previo-11] "No capítulo anterior" e "no próximo capítulo" (C5) — virou [narracao-03], com mais evidência.
- [previo-12] Abertura com voz humana também no completo vertical.
- [previo-13] Elenco fixo nas línguas — virou [voz-08].
- [previo-14] Partes do cap 2 duplicadas na raiz de `workspace/shorts`.
- [previo-08] Trilhas prioritárias com Content ID — ver decisões abaixo.

---

## Decisões que só o dono pode tomar

1. **Até onde suavizar.** A narração explícita é o maior risco de restrição de idade e limitação de anúncio
   [narracao-01, seguranca-03], e o maior canal do nicho não usa nenhuma dessas palavras. Mas o dono mandou manter
   os balões literais. Proposta: narrador sugere, balão continua literal.
2. **Quanto de cena +18 por vídeo.** Hoje 29–35% do tempo é sexo mosaicado e a fila aprova sozinha abaixo de 50%
   [seguranca-06]. Condensar a sequência em 1–2 painéis sugeridos muda o produto.
3. **Cartaz "SEM CENSURA" na tela** [seguranca-05]: o dono pediu a chamada; a sugestão é manter só no comentário.
4. **Trilhas com Content ID** [previo-08]: Hans Zimmer, Re:Zero, HxH, Tensura, MC Jhey tocam em ~85% dos vídeos.
   Antes de decidir, vale ver no Studio se a advertência do canal pt veio de música ou de imagem [seguranca-04].
5. **Formato do completo**: vertical de 6–9 min ou 16:9 por capítulo [previo-02].
6. **Tamanho dos Shorts**: 55 s (6–11 partes) ou ~110 s (3–4 partes, um terço da cota) [shorts-04].
7. **Close em painel sugestivo** quando o rosto não cruza região +18 [imagem-06].

---

## Como completar esta auditoria

1. Rodar `workspace/tmp/auditoria_15out/workflow_auditoria.js` só com as 6 lentes que faltaram (longo, línguas,
   produção, alcance, capa, espectador).
2. Rodar a verificação adversarial sobre os 54 achados já listados (o roteiro tem a fase pronta; o estado salvo
   está em `achados_5_lentes_rodada2.json`).
3. Os quadros já extraídos estão em `workspace/tmp/auditoria_15out/quadros/` e em
   `scratchpad/quadros2/<lente>/` — vale conferir os de censura antes de qualquer postagem nova.
