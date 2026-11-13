# Continuar daqui — melhorias da auditoria (atualizado 16/10/2026 ~10h10)

> Duas sessões mexeram no projeto hoje. Esta anota o lado das **melhorias da auditoria**; a outra fez a
> **análise do vídeo pronto, o reforço da censura e o lançamento do canal novo**. O que está escrito aqui
> já considera as duas.

## Estado agora

| O quê | Como está |
|---|---|
| Lote `refazer_caps.py 1-11 --longo 1` | parou sozinho entre 11:41 e 12:07 (sem log de fim). **Religado 12:15** pela sessão claude-be (ok do dono): `refazer_caps.py 2-11 --so-longo 1`, via WMI. Cap 1 vertical = o das 10:15, aprovado pelo dono. Ver `PEDIDOS_DO_DONO_PENDENTES.md` item 0b |
| `lancamento_pt.py` | rodando, esperando o cap 1 ficar pronto e aprovado pela análise |
| Fila automática e postagem | **desligadas** (`config/FILA_DESLIGADA.json`, `config/POSTAGEM_DESLIGADA.json`) |
| PC2 | **em dia** (16/10 10:07): recebeu `censura_visual.py`, `elenco.py` e `fx_clips.py` |

## O lote de 08:50 foi parado às 09:57 e religado às 10:01 — por quê

A revisão do código que os agentes da auditoria deixaram pela metade achou defeito no vídeo que estava
sendo produzido. Confirmei olhando o cap 1 que acabara de sair (quadro aos 95 s). Corrigido antes de religar:

1. **Painel pequeno com moldura borrada dos quatro lados** (`fx_clips._enquadrar`): painel de proporção perto
   da tela voltou a preencher cortando o que sobra. Eram 27 painéis de 109 no cap 1; sobraram 12, os de
   proporção bem diferente, onde cortar comeria a arte.
2. **Pan 2,5 a 3,6 vezes mais rápido que o catálogo** em 74 painéis de 109 (`fx_clips._pan_vertical`): o
   piso agora é no máximo o dobro da classe sorteada. Sobraram 18 no teto.
3. **Risco de o personagem trocar de voz** (`elenco._gravar`): o arquivo de elenco passou a ser gravado de
   forma atômica. Um render morto no meio da gravação deixava o JSON truncado e o personagem ganhava outra
   voz no render seguinte.
4. **Fala de uma letra ("E?!") virava erro de voz** com som de erro e perdia a legenda (`elenco.texto_para_voz`).

## Ordens do dono de 16/10 (já aplicadas)

- **Versão normal só uma vez por capítulo.** Render de revisão faz só a censurada. Feito pela outra sessão
  (`hiper-pipeline.py` ~710, `so_cens_pt`) e documentado no `CLAUDE.md` item 7.
- **Mosaico primeiro; fosco só quando não tiver jeito.** Eu havia baixado `CENSURA_MAX_FRAC_LOCAL` de 0,80
  para 0,40 por achar o mosaico grande feio — **desfeito**, voltou a 0,80. O que manda painel pro fosco agora
  é prova de que o mosaico não resolveu: cobertura abaixo de 3% com nudez forte, a conferência da imagem já
  censurada, e a lista de reprovados pela análise do vídeo pronto.
- **Não refazer o cap 1 das outras línguas**, já que só o canal pt foi punido. O registro do postador não
  mostra advertência nova nos canais de língua (hindi, indonésio, italiano, russo, tailandês seguem normais;
  francês e inglês pausados por motivo antigo; espanhol suspenso). **Confirmar no Studio ainda não foi feito.**

## O que falta

**Depende de navegador (não fiz para não disputar o Chrome com a outra sessão, que está postando):**
- Métricas de verdade: impressões, CTR e retenção aos 30 s nunca foram lidas; `workspace/metricas.json` segue
  vazio desde 15/10. Dá para medir quando o canal novo tiver alguns dias.
- Confirmar no Studio que os canais de língua não têm advertência.
- Os dois vídeos com título em português nos canais de hindi e tailandês (`BGjF_MKZGsw`, `G-DpRVvi5RM`).

**Código morto: RESOLVIDO em 16/10 ~10h15** (os dois arquivos não são usados pelo lote, que lê roteiro do
cache e renderiza só em pt):
- `narration.py`: as três etapas foram ligadas no fim de `gerar_recap` — tirar "(sorriso)" antes do TTS,
  juntar balão partido e reescrever a fala do narrador que dubla o desenho ou repete bordão. Medido nos 11
  roteiros: 32 painéis de balão partido, 40 falas dublando o desenho e 38 excessos de bordão passam a ser
  tratados. A junção agora exige marca de frase em aberto, senão juntava "Sim." com "Entendi.".
- `narration._sons_para_narrador`: quando a chamada ao modelo falha inteira, as falas ficam como estavam.
  Antes virava painel mudo em massa, gravado no cache e quebrando a tradução das línguas.
- `idiomas.py`: a tabela de vozes por língua passou a ser lida — personagem não usa mais a voz da narradora
  em nenhuma das 8 línguas. **Seis vozes da tabela não existiam no edge** (as quatro do hindi, mais uma do
  russo e uma do tailandês): foram tiradas, e sem voz nativa sobrando o personagem cai nas Multilingual
  aprovadas, que falam essas línguas (testado em italiano e hindi, áudio real). `it-IT-IsabellaNeural`, que
  é proibida pelo dono, saiu da lista.
- `idiomas.falar`: quatro tentativas, como no português. Com uma só, o "No audio was received" do edge (que
  aconteceu 2 vezes em 3 no teste) virava painel mudo e o vídeo saía "pronto" assim.

**Código, só depois que o lote terminar** (editar agora atinge o próximo capítulo do lote):
- Três frentes da auditoria que nunca começaram: `fx_parallax.py` (balão cortado no zoom, rosto grande
  descartado, espelho invertendo texto), `split-shorts.py` (corte no meio da fala, cartão final mudo, render
  não determinístico) e `seo.py` (palavras de busca por idioma). Achados em
  `workspace/tmp/auditoria_15out/grupos/g3_parallax.json`, `g4_shorts.json`, `g7_seo.json`.
- **Código morto deixado pelos agentes** (a revisão mediu): em `narration.py`, seis funções criadas e nunca
  chamadas — narrador dublando o desenho, balão partido e bordão repetido continuam acontecendo em todo vídeo.
  Em `idiomas.py`, a tabela de vozes nativas por idioma não é lida por ninguém, então a narradora e a
  protagonista seguem com a mesma voz nas línguas. Antes de ligar: a junção de balão partido precisa exigir
  marca de frase em aberto, senão junta duas respostas curtas e deixa o painel seguinte mudo.
- **Voz proibida**: `it-IT-IsabellaNeural` entrou na tabela nova do italiano em `idiomas.py`. Inofensiva
  enquanto nada lê a tabela, proibida no minuto em que alguém ligar.
- `_sons_para_narrador`: quando a chamada ao modelo falha inteira, todas as falas de gemido viram texto vazio
  e isso é gravado no cache — painel mudo permanente, e a tradução das línguas quebra com texto vazio no meio.

**Verificação pendente do que já foi feito:**
- Olhar um capítulo refeito inteiro (não só quadros) antes de liberar a postagem em massa.
- As capas dos capítulos refeitos podem mudar: a detecção de gemido ficou mais abrangente e o `capa_ia` usa
  a mesma função para escolher a frase da capa.

## Lista de pendências (conferida item a item em 16/10 ~11h)

### Estudo dos narradores de referência — o ponto que se perdeu (dono, 16/10)
A ideia original era **baixar os textos dos 15 canais autorizados e ESTUDAR cada um** para melhorar o nosso
narrador: piadas, jargões, bordões, tudo que der, **além** do dicionário que já existe. Hoje está pela metade:

| Canal | Textos | Palavras | Analisado |
|---|---|---|---|
| MomoManhwa | 332 | 10,2 mi | sim (ANALISE_LINGUAGEM.md) |
| oporaodacidadela | 243 | 6,0 mi | não |
| mikemanhwa | 23 | 1,3 mi | não |
| KkVirjao | 64 | 817 mil | não |
| Os outros 11 | 0 | 0 | não |

Faltam: @MattzManhwa, @SR.GUUGOU, @mangaticos, @DrezinNimes, @omelhormanhwa, @Doinsuka, @iJaxManhwa,
@Solem_8037, @Jubertim, @IkiManhwa, @solem_sun. Ferramentas prontas em
`D:/hipercool-materiais/referencias_narradores/`: `baixar_legendas.py`, `baixar_tudo_lento.py`,
`analisar_linguagem.py`. A análise de hoje extraiu formato, discurso indireto, conectivos, reações, abertura e
fechamento — **não extraiu piada nem jargão**, que é o que o dono quer. O resultado vira prompt do narrador
(`narration.gerar_recap`) e um repertório em config, variado para não repetir.

### Short de RESUMO (dono, 16/10) — FEITO, falta ligar na fila
Subproduto além do Short de trecho: resumo da história, no estilo de `youtube.com/@kaijinre/shorts`. Medir se
rende mais visualização que o Short de trecho. A ideia é promover a história original, como o dono já faz nos
reacts.

**O que o canal de referência mostra** (lido em 16/10, lista de Shorts do @kaijinre): o Short SEM "Parte N" no
título é a porta de entrada e rende muito mais — "Uma MÃO Surgiu no Espaço" fez **513 mil** visualizações e a
"Parte 2" da mesma obra fez **2,4 mil**; outros sem parte fizeram 433 mil, 231 mil e 37 mil. O formato do
título deles é `<emoji> <gancho em CAPS misturado>... #manhwa #manga #anime`. É por aí que o público (e o
dono, na hora de medir) separa um do outro — era a dúvida dele: "não dá pra diferenciar se são da história
normal ou são resumos".

**Feito:** `bin/short_resumo.py` (módulo novo). Costura os momentos que o editorial já marcou no `.meta.json`,
cada um virando um BLOCO de painéis seguidos — o painel do impacto sozinho dura 3 a 8 s e não conta nada, então
o bloco cresce pra trás, pegando a fala que arma o momento. Não gera narração nova nem chama modelo. Pula
painel censurado. Título sem "Parte N", com o gancho do editorial e o emoji do primeiro impacto.
Teste real no cap 1: 6 blocos, 68,6 s, áudio e vídeo casados, 123 s pra montar; sem o bloco dariam 28,7 s.
Os 6 quadros conferidos um a um: abertura com selo, constrangimento, reação, personagem, balão de tensão,
personagem feminina — momentos diferentes e espalhados pelo capítulo (0, 78, 158, 194, 277, 371 s).

**Falta:** (1) chamar na fila/postador — não mexi em `bin/fila.py` nem em `bin/postar_hipercool.py` porque os
dois estavam rodando; (2) cartão final (hoje o resumo acaba no último momento, sem CTA); (3) o selo "CAP. 1" do
vídeo aparece na abertura do resumo, que é da obra e não do capítulo.

### Falas do manhwa sendo puladas (dono, 16/10 — CORRIGIDO, falta rodar)

> Palavras dele: "Muitas falas estão sendo puladas e isso afeta o entendimento do manhwa. (...) pra quem assiste
> só o vídeo está bem aceitável, mas se ler a história vê as lacunas inteiras. (...) se for obscena, suavize
> usando o dicionário anti-ban. E se não der mesmo, aí o narrador se vira de explicar o que está acontecendo."

**Duas causas, as duas medidas no cap 1 de The Inheritor:**

1. **A leitura dos painéis descrevia o texto em vez de transcrever.** O prompt pedia o texto de "BALÃO DE
   FALA" — e caixa de narração retangular (que em manhwa carrega o fio da história) não é "balão de fala" pro
   modelo. No painel 41 as três caixas **"HAN SIHYUN... / AQUELA MULHER FOI / O MEU PRIMEIRO AMOR."** viraram a
   descrição "Narrador introduz o nome e o primeiro amor do personagem": o nome da personagem central **nunca
   foi dito no vídeo**. No painel 25, a caixa "PROVAVELMENTE ESTÃO PENSANDO EM COMO TUDO PARECE SEM GRAÇA"
   virou "Uma multidão caminha por uma rua movimentada". Dos 10 painéis "sem balão" que conferi na imagem, 4
   tinham texto perdido.
   **Conserto:** os dois prompts de descrição (`_descrever_paineis_claude`) agora mandam TRANSCREVER todo texto
   escrito — balão de fala, balão de pensamento, caixa de narração, legenda, placa, tela de celular — dizendo o
   tipo, e proíbem descrever em vez de transcrever. Painel sem texto responde "sem texto".

2. **O roteiro resumia painel com várias falas e deixava parte de fora.** Agora o prompt tem a regra "NENHUMA
   FALA PODE SUMIR": a locução cobre todo o texto do painel, nome próprio tem de ser dito, fala pesada é dita
   com palavra segura (ou o narrador conta o que acontece) — nunca pulada. Só pode ficar de fora onomatopeia
   desenhada, marca d'água e número de página.

3. **A descrição ia pro painel errado.** O prompt manda o modelo responder numerado ("1. 2. 3."), mas o
   parser jogava fora o número e usava a ORDEM das linhas: bastava ele quebrar uma descrição em duas linhas
   pra todo o resto do lote andar um painel. Agora o número manda, linha sem número é continuação da anterior,
   e lote que não vier numerado direito é refeito painel a painel.

**Prova das três correções juntas** (relendo os mesmos painéis do cap 1, 16/10 16h18):

| Painel | Antes | Depois |
|---|---|---|
| 25 | "Uma multidão caminha por uma rua movimentada." | multidão + caixa de narração: "PROVAVELMENTE ESTÃO PENSANDO EM COMO TUDO PARECE SEM GRAÇA." |
| 35 | "?" saiu na descrição do painel 41 | "?" no painel 35 |
| 36 | — | os dois balões: "!!" e "AQUELA MULHER, SERÁ QUE ELA É..." |
| 41 | "Narrador introduz o nome e o primeiro amor do personagem" | caixa: "HAN SIHYUN..." / "AQUELA MULHER FOI" / "O MEU PRIMEIRO AMOR." |

**Conferência automática** (`narration.falas_perdidas` + `_completar_falas_perdidas`, rodando no fim de
`gerar_recap`): compara o texto lido com o roteiro painel a painel, por palavra-núcleo (a locução parafraseia
de propósito), e separa **fala deslocada** — saiu no painel vizinho, só avisa — de **fala perdida**, que vai
numa chamada só pra ser reescrita. Medido nos 11 capítulos já feitos: **1.118 painéis, 46 com fala perdida de
verdade (4%), 50 falas**; os piores são os caps 1, 2, 3, 7 e 11. Fora isso, 13 falas saíram com 1 a 2 painéis
de atraso.

### Repertório do narrador: piada, jargão e apelido (FEITO)

O estudo que faltava (o dono: "eram pra ser baixados os textos e estudados pra melhorar nosso narrador
adicionando piadas e jargões"). Base: **663 vídeos, 18,3 milhões de palavras** de 4 canais (MomoManhwa 332,
oporaodacidadela 244, KkVirjao 64, mikemanhwa 23).

- `D:/hipercool-materiais/referencias_narradores/extrair_piadas_jargoes.py` tira os candidatos (8.706 trechos
  em volta de gatilhos de humor, mais a contagem de cada jargão). Levava horas e não terminava; agora roda os
  4 canais em **2 minutos** (um regex por grupo em vez de 110, e posição de palavra por busca binária).
- `config/repertorio_narrador.json`: 13 moldes de piada, jargão por tema, apelidos por tipo de personagem e
  uma lista do que NÃO usar — tudo com contagem e trecho real por trás.
- `narration.py` sorteia 3 moldes por capítulo e **não repete os dos 2 capítulos anteriores** da mesma obra
  (`logs/repertorio_usado.json`).
- **Dose: não aumentar.** O estudo mediu 1,0 a 1,3 piada por mil palavras nos canais; o prompt já pedia 2-4
  por capítulo, que é o teto. O ganho veio de trocar as piadas prontas por moldes com variável.
- **Apelidos do prompt estavam errados**: "nosso garoto" tem 27 ocorrências e ZERO no KkVirjao — é marca do
  MomoManhwa, não do nicho. O prompt agora usa a lista medida (o prota, o bicho, o protinha, o coitado, o
  figurante, o brabo...).
- **Dicionário anti-ban corrigido com o que o nicho usa**: "partida" para morte tem 47 ocorrências e todas são
  partida de jogo; "líquido escorrendo" para sangue tem ZERO. O nicho diz **"foi de Vasco"** (76) e
  **"ketchup"** (117). Entraram na frente em `config/dicionario_seguro.json`, com os antigos atrás pra variar.

### Como rodar a próxima leva pra valer (checklist)

As correções de hoje mexem em COMO o painel é lido e em COMO o clip é enquadrado. Roteiro e clip
ficam guardados em cache, então rodar sem aposentar o cache produz vídeo com os defeitos antigos.

```bash
# 1. roteiro do zero (pega a leitura que transcreve caixa de narração e a conferência de falas)
set HIPER_NARRACAO_V=v2
# 2. o cache 2.5D já está em v2 no código: os clips de movimento se refazem sozinhos
# 3. rodar
python bin/refazer_caps.py 1-11 --longo 1
```

Sem o passo 1 o roteiro velho é reusado e as falas continuam faltando. Para consertar só o roteiro
guardado, sem refazer a leitura (mais barato, mas não pega o que a leitura nem transcreveu):

```bash
python bin/conferir_falas.py --obra the-inheritor --corrigir
```

Medido em 16/10: 46 painéis dos 11 capítulos têm fala de fora (50 falas). Não rodei com `--corrigir`
porque o lote estava usando esses mesmos roteiros — fazer isso no meio deixaria o áudio já gravado
diferente do texto no arquivo.

**2ª leva (os dois canais maiores, 16,2 dos 18,3 milhões de palavras):** o repertório foi de 13 para 16
moldes. O mais valioso é **"dá-lhe uma <golpe inventado>"** (MomoManhwa, ~5.500 ocorrências): conta a
pancadaria sem descrever ferimento, o que resolve de graça a regra de não ter violência explícita —
"o cavalo deu-lhe uma cabeçada, rapaz, foi explodido na parede" no lugar de "deu um soco e quebrou a
costela". Também entrou **apelidar por traço visível** (o verdinho, o Velhão, a Ruiva): faz graça e resolve
acessibilidade, porque nome coreano difícil vira apelido que o público guarda. A lista de "não usar" subiu
para 26, com o que os canais fazem e nós não podemos: palavrão (2.262 ocorrências bipadas no MomoManhwa),
malícia sexual, "filho/fi" como vírgula (15.751 vezes — tique dele, não do nicho) e apelido por peso ou careca.

### Análise AMPLA dos narradores — a fazer (dono, 16/10)
O dono apontou que o estudo saiu estreito: "você está estudando só piada, jargão, apelido, voz etc.? Não tem
muito mais que podemos absorver? Talvez a ideia das análises seja ver TUDO que se pode absorver". O que foi
aplicado até agora cobre piada, jargão, apelido e dose. **Falta uma análise que varra tudo**: ritmo e tamanho
de frase, como abrem e fecham, como apresentam personagem novo, como explicam sistema/poder sem travar a
história, onde põem o gancho dentro do vídeo, como tratam cena +18, como encadeiam capítulos, o que fazem na
descrição e nos comentários, duração e corte dos vídeos, e o que os números do canal dizem sobre cada escolha.
Material pronto: os 4 canais extraídos, mais os 11 que `baixar_tudo_lento.py` ainda está baixando.

### Paradas (não começaram)
1. **Leitor de métricas do Studio** — `workspace/metricas.json` tem 1 vídeo e nenhum CTR ou retenção. Trava
   saber qual abertura, qual capa e qual estilo de título ganha.
2. **Voz local de reserva no PC2** — existe só o ambiente de teste local (`D:/tools/tts-teste`).
3. **Narrador diferente por obra e nos compilados** — só existe `config/elenco/the-inheritor.json`.
4. **Vozes proibidas no histórias em frames** — ainda em 5 arquivos (`bin/edge_tts_engine.py`, `bin/elenco.py`,
   `bin/_VERSAO_ESTAVEL_20260712/`, `prod/bin/`).
5. **Compilado com narração extra nos caps 1 a 5** — só saem se os capítulos forem refeitos.
6. ~~Efeitos 2.5D~~ — **FEITO 16/10 tarde** (`bin/fx_parallax.py`): o trilho do enquadramento agora prende
   o balão dentro da tela (23 painéis altos do cap 10: balão inteiro em 53% do clip -> 100%, nenhum cortado);
   rosto grande deixou de ser descartado (ROSTO_FRAC até 0,65; cap 10: 15 -> 27 painéis com close, mirando os
   olhos); o espelho por língua foi DESLIGADO (ESPELHO_CHANCE=0) porque invertia texto — dos 11 painéis que o
   inglês espelharia no cap 1, 9 tinham texto na tela. **A chave do cache 2.5D subiu pra `v2`**, senão o
   conserto não valeria nos 1.202 clips já guardados (1,4 GB); eles ficam no disco sem uso e podem ser apagados.
7. ~~Palavras de busca por idioma~~ — **FEITO 16/10 tarde**: `config/seo_palavras.json` ganhou a chave
   `idiomas` com hi, id, it, ru, th e vi, colhida do autocompletar público do YouTube (224 buscas, 2.018
   sugestões), com validador que recusa termo sem prova na coleta ou com marca de português. `bin/seo.py` passou
   a ler o banco da língua (`_palavras(obra, idioma)`) e `VERSAO` subiu pra `v3` porque 44 dos 65 pacotes
   guardados tinham "completo" em título de outra língua. Descoberta: em tailandês a grafia do YouTube é
   มังฮวา, não มันฮวา — com a errada a busca voltava vazia.

### Pela metade
8. **Capas** — caps 5, 7 e 10 têm 3 ou 4; o cap 2 tem uma só; a do compilado 1-11 é da madrugada, sem as poses
   novas. Há 23 capas verticais de Shorts geradas, mas as do cap 7 com as poses novas dependem da cota.
9. **Extras do Studio** — tela final funcionou em 7 vídeos; comentário fixado e vídeo relacionado seguem
   bloqueados pela conta (25 tentativas). O dono decidiu não contestar, então isso não é mais pendência.

### Feito (conferido hoje, não refazer)
Aberturas com voz humana (20 montadas, 6 canais, prévias na área de trabalho) · títulos dos 34 vídeos já
postados sem o nome da obra · playlists renomeadas · voz fixa por personagem nas 8 línguas · Groq pelo proxy
no manhwa-react · chave do Groq no PC2 · PC2 se atualizando sozinho · projeto no controle de versão ·
Shorts com duração dinâmica e corte no gancho.

## Material

- Backup de antes das melhorias: `workspace/tmp/backup_antes_melhorias_16out/`.
- Estado parcial e transcrições dos agentes: `workspace/tmp/melhorias_16out/`.
- Achados da auditoria: `workspace/tmp/auditoria_15out/` e `docs/auditoria_videos_15out.md`.
