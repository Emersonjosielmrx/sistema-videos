# Voz e narração — o que falta (anotado em 16/10/2026, 22h40)

> Escrito a pedido do dono, para não se perder se a sessão acabar. O que está **FEITO** já está no
> código; o que está **A FAZER** tem o caminho anotado e o porquê.

## O diagnóstico do dono, que é o fio de tudo

Ouvindo o cap 2 e o cap 4, ele disse: *"a voz de IA é muito estável: mesma velocidade entre
palavras, sem arrasto, todas no mesmo volume, e outras coisas que não sei explicar, mas é o que
torna a voz de IA diferente da voz humana"*.

Está certo, e tem nome. O que falta na voz sintética, em ordem de impacto:

| O que é | Como está |
|---|---|
| Curva do capítulo (acelera no clímax, respira depois) | **FEITO** — mas só passou a valer de verdade em 17/10 (ver abaixo) |
| Micro-variação de ritmo DENTRO da frase | a fazer |
| Alongamento da vogal tônica ("faaaala galerinha") | a fazer — tentativa 1 errou o lugar |
| Ênfase em palavra-chave | testado, funciona |
| Pausa irregular (não só na vírgula) | testado, funciona |
| Respiração audível | a fazer |

## FEITO em 16/10

### Curva do capítulo, como locutor de futebol
`elenco.curva_climax` + `elenco.prosodia(texto, v, indice, impactos)`. O editorial já marca 7 ou 8
falas de impacto por capítulo e elas ficam no roteiro ANTES de gravar as vozes; são usadas como os
"gols". Chegando perto a voz acelera e sobe (curva quadrática: devagar no começo, dispara no fim);
nas 3 falas seguintes ela cai, que é o respiro.

Dose atual (3ª tentativa, depois do dono ouvir): `PICO_RATE=18`, `PICO_GANHO_DB=4.0`,
`PICO_PITCH=1`, `RESPIRO_RATE=-12`, `RESPIRO_GANHO_DB=-3.0`.

**O tom quase não sobe de propósito.** Na 2ª tentativa estava em 6 Hz e o dono reprovou: *"no
clímax a fala ficou fina e aguda"*. Na voz Multilingual, subir o tom não soa empolgação, soa
criança. Quem carrega a emoção é a velocidade e o volume.

### A primeira palavra da fala sai errada
A voz entra sem embalo e erra a primeira palavra da locução. Provado com o dono em 16/10: "Herança?!"
sai torto nas três vozes testadas, e "Como assim, herança?" sai certo nas três. Reticência, "hum" e
repetir a palavra NÃO resolvem — só palavra de verdade antes.
Está no prompt (regra de escrever a fala com abertura) e numa checagem automática
(`narration.falas_curtas_arriscadas` + `_dar_corpo_as_falas_curtas`).

## FEITO em 17/10 (madrugada)

### A curva do clímax NÃO estava valendo em roteiro novo — corrigido
O log do cap 5 mostrou as 60 falas novas do narrador TODAS em "+5% +0Hz". O motivo: a curva lê os
impactos do `_editorial` do roteiro, e o editorial só era calculado no acabamento — DEPOIS das vozes
(no cap 5, o editorial apareceu no log 13 min depois da última voz). Só funcionava quando o roteiro
era reaproveitado de um render anterior. Agora o `hiper-pipeline` chama o editorial antes das vozes
(passo "1b-ter") e loga `curva do clímax: impactos nas falas [...]`. Simulado no roteiro do cap 5: o
narrador vai de +5% a +23% (+4 dB) chegando em cada impacto e cai pra −7% −4 Hz −3 dB nas 3 seguintes.
**Vale do cap 6 em diante** (o cap 5 já tinha gravado as vozes).

### A primeira palavra em fala LONGA (era o item 2)
`narration.falas_longas_arriscadas`: fala de personagem com 5+ palavras cuja 1ª palavra tem 7+ letras,
ou 5+ com nasal/dígrafo ("Obrigada", "Acontece", "Esquece", "Então", "Nossa"). Entra na MESMA chamada
de reescrita das curtas, com regra própria: o resto da fala fica igual, só entram 1 a 3 palavras na
frente. Reescrita que abre em interjeição ("Ah, obrigada...") é recusada — o LLM fez isso 2 vezes no
teste. Testado no roteiro do cap 4: 7 falas, 7 reescritas ("Obrigada... obrigada por me dar uma
ordem!" -> "Eu, obrigada... obrigada por me dar uma ordem!"). De passagem: a reconferência depois da
reescrita comparava o índice errado e nunca recusava nada; corrigido.

### O respiro no fim do vídeo (era o item 3)
`fx_acabamento.RESPIRO_FINAL` = 1,6 s (env `HIPER_RESPIRO_FINAL`): o último quadro fica parado e a
trilha continua saindo depois da última palavra. A legenda/CTA/marca vão até o fim novo. Testado:
voz acaba em 10,0 s, imagem parada e silêncio da voz até 11,6 s, áudio e vídeo do mesmo tamanho.

### O Short de resumo fechando em loop (era o item 4)
`bin/short_loop.py`, chamado pelo `short_resumo.montar`: ouve (Groq) o começo e o fim do resumo, o
modelo escreve UMA frase do narrador que fecha e fica pendurada pro começo, grava na voz do narrador
da obra (ou da língua) e cola no fim, com o último quadro parado e a legenda no mesmo estilo. Falhou
qualquer passo -> o resumo sai como antes. Teste real no cap 4: fim *"Mas o que ele não esperava era
que o som vinha de quem ele menos imaginava, porque..."* -> recomeça *"O protagonista começa tenso ao
ouvir um gemido abafado..."*. Os Shorts de PARTE não ganharam isso de propósito: eles terminam no
cartão "continua na parte X", que é o contrário do loop.

## VOZ HUMANA — rodada de 17/10 (madrugada, tarefa agendada pelo dono)

Chaves em `config/fila.json` -> `voz_humana` (TODAS false até o dono ouvir as amostras em
`D:/hipercool-materiais/amostras_voz/2026-10-17/`). Frentes, na ordem pedida:

1. [FEITO] Medir referências x nosso — `bin/medir_narradores.py` -> `referencias_narradores/_medidas/medidas.json`
   (11 canais x 40 vídeos, 15,7 mi palavras; nosso = cap 5 pt pelo Groq). Medianas por canal:
   | | humanos (faixa) | nosso cap 5 |
   |---|---|---|
   | palavras/min | 169-266 (maioria 185-213) | **171** |
   | variação de velocidade (10 s) | 0,09-0,20 | 0,16 |
   | pausas >0,45 s /min | 21-42 | 42 |
   | pausas >1 s /min | **0,1-1,4** (mike 3,0) | **5,8** |
   | pausa média | 0,57-0,69 s | 0,74 s |
   CONCLUSÕES: (a) estamos LENTOS — falta ~+9% no narrador; (b) pausa longa demais e frequente — eles
   cortam as pausas na edição (há silêncio digital nos cortes), então a ideia 14 tem de ENCURTAR quase tudo
   e só segurar antes do impacto (valores já ajustados); (c) a variação de velocidade já está na faixa
   deles — a curva do clímax não precisa de mais dose; (d) quase não há respiração audível neles.
   MULETAS (por mil palavras, humanos | nós): "então" 5,6 | 0; "ele fala que" 5,2 | 0 (eles contam a fala
   dos personagens em discurso indireto); "só que" 1,1 | 0; "e assim" 1,0 | 0; "cara" 2,5; "né" 1,1.
   Nós ABUSAMOS de "aí" (7,2 contra 2,3), "até que" 5,8, "enquanto" 10,1, "a cena" 7,2. Interjeição de
   youtuber ("mano" 0,3, "galera" 0,1, "tipo" 0,6) é RARA neles. -> `config/muletas_narradores.json`.
   Ressalva: as referências são legenda automática do YouTube e o nosso é Whisper; os tempos vêm de
   reconhecedores diferentes, mas a diferença nas pausas longas (4x a 30x) é grande demais pra ser só isso.
2. [FEITO, desligado] Ideia 7, sem "câmera": `narration._META_CAMERA` (chave `sem_camera`). Pega 5/81
   falas do narrador no cap 5 ("a cena exibe", "a tela fica totalmente preta", "a paisagem mostra") e
   1/51 no cap 4; elas vão pra reescrita que já existe (`_reescrever_narrador_fraco`).
   Também pega "fora do quadro/da tela".
3. [código pronto, desligado] Ideia 3, muletas reais (chave `muletas`): `narration.temperar_muletas`,
   lista e dose em `config/muletas_narradores.json` (conectores de quem conta, não interjeição).
   NÃO está chamada no fluxo do roteiro ainda — entra depois do dono ouvir.
4. [código pronto, desligado] Ideia 13, respiração (chave `respiracao`) — `bin/voz_humana.py`.
   Banco: `bin/banco_respiracoes.py` -> `assets/respiracoes/` (9 respirações, das aberturas humanas
   autorizadas, conferidas pelo Groq sem palavra dentro). ACHADO: o 1º jeito (intervalo entre palavras)
   achou ZERO — esses narradores EDITAM cortando as pausas (silêncio digital -180 dB nos cortes) e quase
   não deixam respiração audível. 9 em ~3 min de fala. Por isso a respiração entra com moderação:
   85% depois de impacto, 45% antes de fala de 18+ palavras, 12% no resto, nunca na subida pro clímax.
5. [código pronto, desligado] Ideia 14, pausa variável (`voz_humana.pausa_depois`): subida 0,08-0,22 s,
   1 fala antes do impacto 0,75-1,0 s (suspense), impacto 0,6-0,85, respiro 0,45-0,7, normal 0,18-0,5.
   Hoje a produção não tem pausa planejada: o clip dura a voz (mínimo 1,5 s).
6. [código pronto, desligado] Ideia 8, ritmo por pedaço (`voz_humana.falar_em_pedacos`): corta na
   pontuação (pedaço mínimo 3 palavras, pra não abrir em palavra solta), -4% no 1º, +5% no meio, -2% no
   último, ±3% sorteado, 50-160 ms entre pedaços.
7. [código pronto, desligado] Ideia 11, Gemini nos picos (`voz_humana.falar_gemini_estilo`): falas do
   narrador do impacto e das 4 antes, com instrução de estilo SEM subir o tom (o dono reprovou voz fina).
8. [FEITO 03:34] Amostras prontas em `D:/hipercool-materiais/amostras_voz/2026-10-17/` (9 mp3 de ~50-70 s
   + LEIA.txt). Conferidas pelo Groq: nenhuma palavra perdida nos cortes da versão em pedaços.
   (Corrigido 17/10 13h: o "June Hill"/"Juim Yuuki" na transcrição NÃO é a voz errando — o dicionário
   config/pronuncia/the-inheritor.json já troca "Joo Inhyuk" -> "Jú In-hiúk" e o log mostra a voz lendo
   assim; é o Whisper que não sabe escrever o nome coreano que ouviu. Nada a consertar.)
   Era: `bin/amostras_voz.py` (cap 5, falas 106-116, impacto na 113) -> 9 versões
   (0 atual, 1-6 uma ideia cada, 7 tudo junto, 8 "ritmo das referências" = narrador +9% e pausas curtas,
   que saiu da medição). Incidente: a 1ª rodada CRIOU o figurante "mulher desconhecida|F" em
   config/elenco/the-inheritor.json (Isabella -10% -18Hz, que o edge recusa) — removido às 03:3x, e o
   script agora fixa a voz que o cap 5 usou (Francisca -12% -14Hz) sem passar pelo elenco.
   Gemini nos picos: a cota estourou em parte das falas (as que falham ficam no edge; o LEIA diz quais).
9. [ ] Ligar as chaves no hiper-pipeline (o código existe, falta a chamada) — só depois do dono ouvir.

## A FAZER

### 1. O arrasto da vogal — tentativa 1 errou o lugar
O dono: *"o arrasto deve estar no lugar errado; o Momo usa 'faaaala galerinha' (estica o a), no seu
arrasto ele pareceu estar repetindo o o duas vezes"*.

O que eu fiz foi escrever `Nissooo`, repetindo a vogal **átona final**, e o TTS leu como repetição.
O certo é esticar a **vogal tônica**, e em palavra que o narrador usa para chamar atenção, não em
qualquer uma. No exemplo dele: fa-LA → `faaala`. Em `Nisso` a tônica é o primeiro O: `niiisso`.

**Como fazer:** achar a sílaba tônica (regra do português: oxítona, paroxítona, proparoxítona, com
as exceções do acento) e repetir a vogal dela 2 ou 3 vezes, só na PRIMEIRA palavra da locução e só
quando a fala for de chamar atenção. Entra no texto que vai pra voz, nunca na legenda — o mesmo
caminho de `elenco.aplicar_pronuncia`.

### 2, 3 e 4 — feitos em 17/10, ver acima.

### 5. Micro-variação de ritmo dentro da frase
O que mais separa voz humana de IA e o que ainda não foi atacado. O edge escapa o texto, então
`<prosody>` não funciona (ver `config/pronuncia/_geral.json`). Os caminhos que sobram:
- **pontuação** (testado em 16/10 e funciona): vírgula e reticência mudam o ritmo, travessão dá
  pausa, caixa alta dá ênfase. Dá pra inserir no texto da voz sem tocar na legenda.
- **pós-processamento do wav**: variar o volume por trecho e inserir micro-pausas com ffmpeg.
- **outro motor**: o Gemini TTS aceita instrução de estilo por texto; o projeto já tem o mapeamento
  (`config/elenco/*.json` → campo `gemini`). Custa cota.

### 6. As análises dos narradores que ficaram pela metade
O download dos 15 canais de referência estava rodando (`baixar_tudo_lento.py`); 4 canais prontos
(663 vídeos, 18,3 mi de palavras) e 11 faltando. O repertório atual (16 moldes) saiu só desses 4.
Falta também a **análise ampla** que o dono pediu: *"ver tudo o que se pode absorver"*, não só piada
e jargão — ritmo, abertura, como apresentam personagem novo, onde põem o gancho, duração, etc.
Material e ferramentas em `D:/hipercool-materiais/referencias_narradores/`.


## Fora da voz: o que mais ficou pendente em 16/10

### Censura — o caso que quase passou (CORRIGIDO, mas vale a lição)
O dono assistiu o cap 4 e achou aos **3m25** um close de roupa íntima que ele classificou como
passível de banimento. O painel (040) teve score **0,433** contra um limiar de 0,45: passou DIRETO,
sem ser olhado por ninguém, por 0,017. A análise do vídeo pronto também não pegou — roupa íntima em
close não é "nudez" pros detectores, mas é conteúdo sexual pro YouTube.
**Feito:** LIMIAR_DUVIDA baixado de 0,45 pra 0,25 (custo medido: +25 painéis em 545, ou 5 por
capítulo) e aquele painel marcado pra sair em fosco.
**Lição pro futuro:** o detector erra PRA BAIXO em roupa justa, lingerie e pose sugestiva vestida.
Quem pega isso é a visão, não o score — por isso o limiar precisa ser generoso.

### Alcance do canal novo e a ideia do proxy
O canal Manhwa Noturno (criado em 16/10) está com alcance orgânico zero: o vídeo longo tem 3
visualizações, todas do próprio dono, e os dois Shorts têm 0. Tecnicamente está tudo certo (os
Shorts são reconhecidos como Shorts, 1080x1920, abaixo de 3 min).
O dono levantou a hipótese de que vídeos do mesmo IP tenham propagação reduzida, e perguntou de usar
proxy. **Minha avaliação:** improvável ser a causa — canal de 1 dia e 0 inscritos explica o zero
sozinho, e o que o YouTube pesa é desempenho (CTR, retenção), não o IP de upload. Há ainda um risco
prático: trocar o IP de uma conta logada costuma disparar verificação de segurança do Google, o que
quebraria a automação.

**O leitor de métricas RODOU em 16/10 às 19h03, mas quase não traz nada** (`workspace/metricas.json`,
5 vídeos): em 3 deles a resposta foi *"nenhuma métrica achada na página"*, e nos outros 2 veio só
`views` (1 e 26) — **impressões, CTR e retenção estão todos nulos**. São justamente os números que
diriam se o problema é não aparecer ou aparecer e não clicarem. Consertar o leitor é o passo que
destrava essa discussão: sem impressões e CTR, qualquer mudança (proxy, título, capa) é chute.
O leitor salva um print por vídeo quando não acha nada — vale olhar esses prints pra ver se a página
mudou de layout ou se o Studio pediu login.

### Os exemplos antigos da censura Exodia: não existem mais
O dono lembrava de exemplos guardados. Procurei por nome de arquivo, por pasta, no cache e no
histórico do git: não há nenhum. O que existe:
- `workspace/censura_cache/` — 1.645 arquivos, TODOS json (só os julgamentos, nenhuma imagem)
- `workspace/cache/revisao/` — 14.368 json (idem)
- `workspace/cache/mascaras/` — 1.072 png, mas são as máscaras de recorte do efeito 2.5D
  (`fx_parallax`), não censura
- `workspace/tmp/conferir_censura/` — 9 jpg de antes/depois, de 15/10. É o único material visual.
Se forem necessários, dá pra recriar: basta a obra e o capítulo, e as variações saem do painel.

### Correções no tempo ocioso (feito em 16/10, à noite)

O dono liberou o cap 4 com o quadro de 3m25 à mostra para não travar a produção (*"pode ir para o 5,
depois se der tempo cubra"*) e pediu que as correções saiam sozinhas *"quando estiver ocioso"*.

`fila.corrigir_pendentes` faz isso, e é a primeira coisa que o `tempo_livre` tenta — antes das outras
línguas e do 16:9. Não existe lista escrita à mão: cada painel forçado (`censura_visual.forcar_fosco`)
guarda a hora em que foi marcado; se essa hora é depois do `fim_render` do capítulo, o vídeo que está
lá ainda tem o painel à mostra, e o capítulo entra na fila de correção. Refaz um por rodada, e depois
do render novo o capítulo sai da lista sozinho (o `fim_render` passa a ser o mais recente) — não fica
em laço. `"corrigir_pendentes": false` em `config/fila.json` desliga.

Medido logo depois de ligar: cap 1 e cap 3 estavam pendentes, cap 2 já coberto. O cap 4 entra assim
que a fila mudar a situação dele para "pronto".
