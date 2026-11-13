# Melhorias do agente online — para aplicar no D:

Branch: `claude/optimistic-rubin-8buena` do repositório `sistema-videos`. Tudo aqui foi feito **sem o D:, sem GPU e sem
vídeo real**: o que está marcado "testado" foi testado com os scripts `teste_*.py` (sem IA, sem rede). Nada foi visto
num vídeo renderizado — isso fica para quem aplicar.

## Como aplicar
1. O espelho do GitHub é de mão única (D: → GitHub). Estas mudanças **não chegam ao D: sozinhas**: copie os arquivos
   listados em cada item para o mesmo caminho no D: (ex.: `recapd-ambientes/producao/bin/viralizador.py` →
   `D:\recapd-ambientes\producao\bin\viralizador.py`).
2. **Cuidado ao copiar:** na cópia do GitHub, chave/senha vira `<SEGREDO_REMOVIDO>`. Não copie o arquivo inteiro por
   cima do original se ele tiver essa marca — aplique só o trecho mudado (`git diff 41865be..HEAD -- <arquivo>`).
   Arquivos desta lista que têm a marca: `anime_script.py` (linha `chave_cache = "<SEGREDO_REMOVIDO>" + texto_total`,
   que no D: é outro texto — manter o do D:).
3. Depois de copiar, rode os testes do item (todos saem com "tudo certo").
4. Código que roda no Kaggle (`recapd-ambientes/producao/bin`) só vale depois de refazer o pacote
   (`colab/montar_pacote.py`).
5. Não mexi em postagem, horários, narradores, fontes, nicho nem títulos (é do outro agente).

Ordem sugerida: itens 1 → 2 → 2b → 2d → 3 (texto falado e legenda, valem para todo vídeo), depois 4 e 5. O 2c muda o
som do longo: aplicar por último e ouvir.

---

## 1. O filtro de palavras estragava palavra comum em TODA narração (áudio e legenda) — testado
**Arquivos:** `recapd-ambientes/producao/bin/viralizador.py`, `postador-de-videos/bin/viralizador.py`
**Teste:** `python recapd-ambientes/producao/bin/teste_viralizador.py`

O `anti_ban` (sempre ligado, passa em toda frase antes do TTS e da legenda) casava **pedaço de palavra**. Saída real
do código antigo:

| Frase do roteiro | Saía assim |
|---|---|
| Ele **prometeu** que voltaria | Ele **promandando ver** que voltaria |
| O vilão **cometeu** um erro fatal | O vilão **comandando ver** um erro fatal |
| O herói foi **enviado** para outro mundo | foi **endiferentão** para outro mundo |
| A **heroína** da história salvou o reino | A **aditivos proibidos** da história |
| O **diamante** brilhou | O **diaffair** brilhou |
| foi **atropelado** por um caminhão | foi **atrosem roupa** por um caminhão |
| Em **homenagem** ao pai | Em **hofesta privadam** ao pai |
| Ele comeu um **biscoito** | um **bisvuco-vuco** |
| O **manuscrito** antigo | O **mpopôcrito** antigo |
| Ele chegou **molhado** da chuva | Ele chegou **acesa** da chuva |
| Ele foi **dominado** pelo medo | Ele foi **no controle** pelo medo |

Em 24.906 frases reais do repositório, o filtro antigo alterava 263 e o novo 157; **todas** as 106 de diferença eram
palavra inocente estragada (enviado ×48, exibição ×20, cometeu, biscoito, Pica-Pau, manuseio, impenetráveis...).

O que mudou (as listas `_ANTI_BAN` da dona ficaram como estavam; o bloco novo fica logo antes de `_ANTI_BAN_C`):
- cada regra só casa **palavra inteira** (plural com "s" continua valendo): `_palavra_inteira`;
- palavra que normalmente é inocente só troca **com contexto na frase** (`_GUARDAS`): meteu/meter/metendo, pau, pinto,
  rola, molhado, virgem, gala, cavalgar, dominado, exibição, "se tocar", violar só com sinal de cena picante;
  heroína só com sinal de droga; gostosa não troca com comida; chupar/mamar não trocam com sangue/vampiro/leite;
  gemido não troca com dor; "seio da família", "gozava de boa saúde", "efeito retardado", "amante das artes" ficam;
- gênero e conjugação (`_ANTES`): escrava → serva (era "a servo"), excitada → acesa (era "aceso"), seduziu → encantou
  (era "encanta"), "enforcou o traidor" → "deu a gravata definitiva no traidor" (era "ele gravata definitiva o
  traidor"), cueca → peça de baixo (era "a a peça de baixo"), "os seios" → "os frontais" (era "os os frontais").
- Termo de strike continua saindo (21 casos no teste). A regra do gore (`_so_gore`) não mudou.

**Conferir no D::** ouvir 1 Short novo e procurar nos roteiros antigos por "mandando ver", "diferentão", "aditivos
proibidos" fora de contexto — some depois da troca. Para acrescentar palavra nova à lista de contexto: `_GUARDAS`.

## 2. A narração perdia números, nomes e siglas — testado
**Arquivos:**
- `recapd-ambientes/producao/bin/anime_script.py` (`_limpa_linha`, `_clean_lines`)
- `recapd-ambientes/producao/bin/claude_client.py`, `recapd-ambientes/producao/_pc2_claude_client.py`,
  `postador-de-videos/bin/claude_client.py`, `historias-em-frames/{bin,beta/bin,prod/bin,teste/bin}/claude_client.py`
  (`_balloon_lines`)
- `_tts_filter.py` em `recapd-ambientes/producao/bin`, `postador-de-videos/bin`,
  `historias-em-frames/{bin,beta/bin,prod/bin,teste/bin}`, `hipercool-videos/{bin,bin_dev}`
- `recapd-ambientes/producao/bin/anime_tts.py` (`_RX_ROMANO_1`, `_seguro`)

**Teste:** `python recapd-ambientes/producao/bin/teste_limpeza_roteiro.py`

| Onde | Antes | Agora |
|---|---|---|
| roteiro (toda linha da IA) | "300 soldados cercaram a vila" → "soldados cercaram a vila"; "2 anos depois" → "anos depois"; "1995 foi o ano" → "foi o ano" | o número fica; só sai marcador de lista ("1. ", "2) ", "- ") |
| roteiro | `"Você não é nada", disse ela.` → `Você não é nada", disse ela.` (aspa pela metade) | aspas de fala ficam as duas; `**negrito**` e `## título` saem |
| balões do manhwa | "100 anos se passaram" → "anos se passaram" | o número fica |
| filtro do TTS (manhwa/hipercool/histórias) | "Kang Dong-su entrou" → "Kang -su entrou"; "cantora de K-pop Ann" → "cantora de K-"; "um click", "um crash", "o boom" sumiam | nome e palavra ficam; onomatopeia só sai em CAIXA ALTA ou com "!" |
| filtro do TTS | "O NPC entregou a missão" → "O entregou a missão"; "O HP dele caiu e o MP zerou" → "O dele caiu e o zerou"; rank SSS, TV, RPG, PVP sumiam | siglas ficam (lista `_SIGLAS`) |
| filtro do TTS | "prêmio de 10000000 de wons" → "prêmio de de wons" | número fica |
| filtro do TTS | linha começando com "if/for/return..." ou "[Missão concluída] Recompensa: 300 moedas" era descartada inteira como código; "[CORTE] Ele acordou." sumia inteira | a frase fica; só a diretiva sai |
| narração do anime | "o X da questão" → "o 10 da questão"; "Sr. X", "Projeto X", "Rank X" → "10" | "V"/"X" sozinhos só viram número depois de capítulo/parte/temporada... ou nome de rei ("Henrique V") |

## 2b. Roteiro: frase curta de impacto e abreviação sumiam; erro da IA confundido com narração — testado
**Arquivo:** `recapd-ambientes/producao/bin/anime_script.py` (`_sentencas`, `_RX_CURTA`, `_clean_lines`,
`rewrite_longo_com_tempo`, `_RX_ERRO_IA`)
**Teste:** `python recapd-ambientes/producao/bin/teste_limpeza_roteiro.py`

- "[12s] Ele abriu a porta. **Vazio.** Ninguém estava lá." → o "Vazio." era jogado fora (tudo com menos de 8 letras
  sumia: "Não!", "Fugiu.", "Tarde.", "Nada."). É justamente a frase de impacto. Agora gruda na frase vizinha (não cria
  clipe de 1 palavra). Lixo curto ("Fim", "Ok", "---") continua saindo.
- "O Sr. Kim chegou cedo." virava "Kim chegou cedo." (o ponto de "Sr." fechava a frase e o pedaço "O Sr." era
  descartado). Vale para Sr., Sra., Dr., Dra., Prof., Mr., Mrs., Ms., St., vs., nº.
- `resposta_de_erro`: nos canais de negócios/IA, frase com "prompt", "api key", "rate limit", "envie o vídeo",
  "cole o texto", "conteúdo sensível" era tratada como erro da IA — a linha saía e, no Short com tempo, o roteiro
  **inteiro** era descartado e pedido de novo. Agora só casa a forma que o provedor/recusa escreve ("Invalid API key",
  "rate limit exceeded", "o prompt acima", "envie a transcrição para que..."). 14 frases de narração e 18 erros reais
  no teste. O `conferir_audio.py` usa a mesma função, então também para de reprovar esses vídeos.

## 2c. Longo: a voz só variava em 5% das frases — testado sem IA, **ouvir antes de valer**
**Arquivos:** `narracao_curva.py` (7 cópias iguais): `hipercool-materiais/comum`, `hipercool-videos/bin`,
`recapd-ambientes/producao/bin`, `historias-em-frames/{bin,beta/bin,prod/bin,teste/bin}`
**Teste:** `python recapd-ambientes/producao/bin/teste_impactos_longo.py`

A curva de locutor (acelera chegando na frase de impacto, respira depois) tinha teto de **8 impactos por vídeo**,
pensado pro capítulo de ~100 frases. O longo tem 1.000–1.500 frases: só ~80 frases (5%) recebiam variação e o resto
das 2 h saía plano. Além disso o LLM recebia as 1.500 frases numa chamada só, com 60 s de prazo.

- Até 96 frases (Short, capítulo): **nada muda**.
- Acima disso: 1 impacto a cada 20 frases (`NARRACAO_IMPACTOS_CADA`), escolhidos por janela de ~120 frases (uma
  chamada de LLM por janela; se uma falhar, o resto vai de heurística — não fica esperando vários timeouts). Em 1.500
  frases: ~75 impactos, mais de 30% das frases na curva, pelo menos 2 em qualquer trecho de 150 frases.
- **Voltar ao antigo:** `NARRACAO_IMPACTOS_MAX=8`.
- **Atenção (efeito colateral):** a mesma lista liga outras coisas na montagem — efeito mais forte no clipe de impacto,
  ênfase na legenda, fala real depois do impacto e a paralaxe 2.5D (`ANIME_FX_25D=1`, 1 a cada `ANIME_FX_25D_CADA`=5
  impactos: de ~2 cenas passa a ~15 por longo). **Medir o tempo de render do 1º longo**; se passar, subir
  `ANIME_FX_25D_CADA` para ~40 (mantém ~2 cenas 2.5D) ou usar `NARRACAO_IMPACTOS_MAX`.
- `_impactos.json` antigo ao lado da fonte continua valendo (mesmo roteiro = mesma lista); apagar para recalcular.
- De quebra: palavra de virada da heurística agora é palavra inteira ("mas" casava "massa", "máscara"; "choc"
  casava "chocolate").

## 2d. Karaokê da legenda fora do tempo quando voz e roteiro não têm a mesma contagem de palavras — testado
**Arquivos:** `fx_subtitles.py` em `recapd-ambientes/producao/bin` (3 pontos: `render_subtitles_progressive`,
`burn_subtitles_ass`, `render_subtitles_short`), `recapd-ambientes/producao/_pc2_fx_subtitles.py`,
`historias-em-frames/{bin,beta/bin,prod/bin,teste/bin}/fx_subtitles.py`, `postador-de-videos/bin/effects_engine.py`
(funções novas `_chave_palavra` e `_alinhar_tempos`)
**Teste:** `python recapd-ambientes/producao/bin/teste_legenda_tempos.py`

O tempo real de cada palavra (sidecar `.words.json` da voz) só era usado quando o **número de palavras** era igual
ao da legenda. Bastava a voz partir "Dong-su" em duas, ler "1.500" como "mil e quinhentas" ou a fala trocar uma
palavra do roteiro (o anti_ban troca "matou" por "tirou a vida"; a legenda fica com o roteiro) para a frase
**inteira** cair na estimativa por tamanho da palavra — o amarelo acendia adiantado ou atrasado.
Agora casa palavra com palavra: as que batem ficam no tempo real e só o pedaço diferente reparte o tempo dele. Se
menos da metade casar, fica a estimativa (como antes). Sidecar estragado não derruba a legenda.

**Conferir:** num Short com nome com hífen ou número, ver se a palavra amarela acompanha a voz.

## 3. Tom da legenda (SUB_CONTEXT=1) com falso positivo — testado
**Arquivos:** `fx_subtitles.py` em `recapd-ambientes/producao/bin`, `recapd-ambientes/producao/_pc2_fx_subtitles.py`,
`historias-em-frames/{bin,beta/bin,prod/bin,teste/bin}`; `postador-de-videos/bin/effects_engine.py`;
`veo/beta/pos_producao/subtitles_veo.py` (função `detect_context`).

Só vale com `SUB_CONTEXT=1` (hoje desligado por padrão). "olhou para baixo" virava legenda de sussurro (menor e
cinza), "recompensa"/"compensa" virava pensamento, "o prédio mais alto" virava grito. Agora exige a palavra certa
(sussurr-, baixinho, "em voz baixa"; grit-, berr-; pens-ou/ava/amento; important-).

## 4. Longo de 3 h+ que nunca terminava no Kaggle — testado sem IA, falta longo real
**Arquivos:** `recapd-ambientes/producao/bin/anime_script.py` (`TETO_FRASES_LONGO`, `alvo_com_teto`,
`rewrite_longo_com_tempo`), `recapd-ambientes/producao/bin/anime_preparo_longo.py`
**Teste:** `python recapd-ambientes/producao/bin/teste_teto_frases_longo.py`
**Registro:** `video-fila/linhas/LONGOS/LONGOS_MELHORIAS.md`, seção "A FAZER (10/11)", item (a).

Alvo de frases acima de 1500 vira 1500 e só nesse caso cada trecho recebe "NO MÁXIMO N frases". Fonte de 206 min:
de 1854 para no máximo 1617 frases (≈ 10,8 h a 24 s/frase, dentro das 11,5 h). Longo normal não muda.
Desliga: `LONGO_TETO_FRASES=0`. Depois de 1 longo de 3 h+ terminar: dá para subir `LONGO_MAX_MIN` (170) e tirar
HZRT/VgQU do "ignorar". **Falta** o item (b) da mesma lista (conferir `_cabe` de novo depois do roteiro gerado na GPU).

## 5. Bugs de código — conferidos com pyflakes
- `historias-em-frames/{bin,beta/bin,prod/bin,teste/bin}/fx_clips.py`: o cache de clipes nunca valia (a chave usava
  `color_filter` antes de existir; o erro era engolido). Mesma correção que já estava em `recapd-ambientes`.
- `recapd-ambientes/producao/bin/{duracao_protegidos,gerar_blocklist,listar_protegidos}.py`: não abriam
  (`from pathlib import Path.util`).
- `hipercool-videos/temp_codigo_pc3/cron_gerar_video_llm.py`: usava `re` sem importar.
- `projetos-navegador/_deploy_pc3.py`: docstring com `\U` (erro de sintaxe).
- `hipercool-materiais/comum/salvar_github.py` + `teste_salvar_github.py`: a limpeza de segredos quebrava código e
  JSON na cópia; token do Telegram colado em URL e cookie do Google não eram pegos; perfis do Chrome com outro nome
  subiam. O padrão de e-mails/IPs continua como a dona definiu.

---

## Achados que NÃO mexi (para quem tem o D: decidir)
- `recapd-ambientes/producao/colab/postar_longos.py:255`: `politica` usado sem import dentro de `_segura_longo`
  (só quebra com `LONGO_VIRAL_SO_LONGO=0`). É da postagem — fica para o outro agente.
- `recapd-ambientes/producao/bin/elemental_transitions.py`: chave repetida no dicionário — `"luz"` aparece 2 vezes
  (divine e depois swipelight; vale a última) e `"snow"` 2 vezes (iguais).
- `viralizador`: "suicídio" → "ir de base" fica sem sentido como substantivo ("O ir de base do pai mudou tudo").
  Não troquei porque é escolha de estilo da dona.
- Itens da lista dos longos que dependem de imagem/dados que não vêm no espelho: L-08 (capa tríade), L-11 (tags).
- `video-fila/aprendizado/PARA_IMPLEMENTAR.md`: 635 candidatos, nenhum marcado (a regra exige teste em vídeo real).
