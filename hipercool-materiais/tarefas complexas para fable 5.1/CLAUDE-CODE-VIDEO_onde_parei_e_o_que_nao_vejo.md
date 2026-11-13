# [PROJETO: CLAUDE-CODE-VIDEO] Para o Fable 5.1 — onde o Claude Code Video travou

> **Projeto:** CLAUDE-CODE-VIDEO — `D:\claude-code-video` (Reels em Remotion: anúncios de produto + entretenimento;
> linha `D:\video-fila\linhas\CLAUDE-CODE-VIDEO`). Cada item diz o projeto. Item marcado "dado de OUTRO projeto" usa
> número de outra linha só como evidência — o dono daquele problema é a outra linha.

Escrito em 28/10/2026 22h40 pela sessão que cuida do Claude Code Video (Opus 5.5 / Opus 4.6). A dona quer que você
olhe onde eu cheguei no meu limite e ache o que eu NÃO estou vendo. Eu aponto o lugar e o que já tentei. Prioridade
dela: o que traz mais views, likes e qualidade de vídeo.

Seus tokens são caros: leia o que está indicado aqui antes de varrer pastas. Cada item tem os arquivos exatos.
Regras da casa (valem para você também): `C:\Users\Haylla\.claude-vscode\CLAUDE.md` e o índice de memória
`C:\Users\Haylla\.claude-vscode\projects\d--\memory\MEMORY.md`. As mais importantes: nada de janela na tela
(`sem_janela`), nada no C:, yt-dlp sem rajada (`hipercool-materiais\comum\ytdlp_vez.py`), sem Opus/Kiro nos pipelines
automáticos (Argon → Gemini 3.8), nunca matar pythonw no PC2, arquivos compartilhados só com Edit.

---

## 1. [dado de OUTRO projeto: CORTES / Shorts de parceiro + postador] O alcance é bimodal e ninguém sabe por quê
(O CCV ainda não postou nada; usei este dado porque é a única medida real de views do sistema. Ver também o
`01_CICLO_VIEWS_DECISAO.md` da linha CORTES.)
**Dado real (28/10, `python D:\video-fila\diagnostico_alcance.py`):** 274 Shorts de parceiro com views de 48–96 h.
Mediana **4**, média 363, 62 com zero, só 1 acima de 5.000. Mas por canal: esportenoturno mediana 1.272,
filmenoturno 1.212, dicasfinanceirasdaia 1.324, fiodameada 1.285. Contra: doramanoturno 2, manhwanoturno 2,
inovare_ru/thai/ind 0 (60–75% zero), manhwa como nicho 43% zero. Por parceiro de origem: canalutopia, xiuliamelo,
futtres, papodebixo, andreu_edit1 ~1.200; vários outros 3–40.
**O que eu não consigo dizer:** se é o canal (histórico, punição, idade, reuso de conteúdo detectado), o nicho, o
horário, o título, o narrador ou o próprio vídeo. Parece "ou o YouTube testa e empurra, ou mata na hora".
**Onde olhar:** `diagnostico_alcance.py` (o que ele cruza), `D:\postador-de-videos\logs\uploads_ledger.jsonl`,
`config\telegram_estado.json` (medidas_48h), `_analise\metricas_studio.json`, `config\canais.json` (política por
canal), memória "Anti-bloqueio de direitos" e "Canal pausado pode ter advertência" (fr 2 strikes, en bloqueado).
**Pergunta pra você:** o que separa um Short de 1.200 de um de 4 DENTRO do mesmo canal? E entre canais?

## 2. [CLAUDE-CODE-VIDEO] O júri de qualidade nunca foi comparado com views
O CCV (`D:\claude-code-video`) dá nota a cada vídeo com 4 verificadores Gemini (legibilidade, movimento,
roteiro_marca/historia, diretor/retencao) e um corretor sobe a nota. **Nenhum vídeo do CCV foi postado ainda**
(ficam em `saida\<conta>\`, Telegram desligado), então não há uma única view para saber se a nota prevê alguma coisa.
Números (`D:\video-fila\linhas\CLAUDE-CODE-VIDEO\evolucao.jsonl`, 15 vídeos): 1ª versão média 5,83 (4,25–6,5),
final 6,7. Meta da linha: 1ª >= 7,5. O corretor sobe ~0,8 e para.
**Ideia que eu não consegui fazer:** rodar o MESMO júri (`gerar.py` → `etapa_lapidar`, prompts em `VERIFICADORES`)
nos Shorts de parceiro que já têm views medidas (item 1) e ver se a nota separa os de 1.200 dos de 4. Se não separa,
o júri está otimizando a coisa errada e toda a linha de melhoria está mirando no lugar errado.

## 3. [CLAUDE-CODE-VIDEO] Platô da 1ª versão (~6) — o editor é fraco e eu não acho mais o que mudar no manual
O editor é Gemini 3.8 Flash ("hx-maos-gemini") escrevendo Remotion/React a partir de
`remotion\EDITOR.md` / `EDITOR_ENTRETENIMENTO.md` + `APRENDIDO*.md` (26 regras cada, escritas pelo aprendiz a cada
vídeo) + kits prontos em `remotion\src\lib\` (efeitos, karaoke, vivo = 2.5D/recorte/impacto, tres = 3D,
transicoes = rasgo raio/fogo/glitch). Defeitos que voltam sempre: movimento 5–6 (cena "parada"), legibilidade,
"parece slide", cartão final parado, rosto coberto.
**Eu já tentei:** manual com regras numeradas, kits que garantem movimento medido, still de conferência, trava de
texto, aprendiz automático. A nota não passa de ~6,5 na 1ª versão.
**O que eu acho que não estou vendo:** talvez o problema seja o FORMATO (o editor monta "cenas com foto + texto"
quando o que dá view é outra estrutura), ou o júri (item 2). Compare um vídeo nosso
(`D:\hipercool-materiais\claude-code-video\ULTIMO_VIDEO\`) com uma referência viral analisada
(`D:\claude-code-video\referencias\*\ANALISE.md`) e diga a diferença que importa.

## 4. [CLAUDE-CODE-VIDEO, voz comum a todos: hipercool-materiais\bin\voz_clonada.py] Voz: o clone copia o timbre, não o JEITO de falar
RVC (Applio, `D:\hipercool-materiais\bin\voz_clonada.py`) troca só o timbre; ritmo, entonação e respiração vêm da
base edge Francisca. A dona sente isso ("muito diferente do original", "Francisca é ruim"). Em 28/10 eu medi o
narrador do Chris na série dublada e acertei o tom (semelhança Resemblyzer 0,83 → 0,88; index/formante/entonação
moveram só ±0,005) e mesmo assim a dona achou "horrível": voz ABANDONADA e apagada. Ou seja, o medidor de semelhança
dá nota alta para algo que o ouvido humano reprova — ele não serve sozinho para aprovar voz.
**Meu limite:** copiar prosódia de verdade pede TTS que clona o jeito (GPT-SoVITS / F5-TTS / XTTS) treinado na GPU
do Kaggle. O material no formato GPT-SoVITS já é gerado (`voz_clonada.preparar` → `dataset_narradores\<voz>\*.list`)
e existe `clone2.py` (aproximação: ritmo, entonação, EQ, linguagem). Ninguém testou um TTS de prosódia contra o
RVC com o mesmo medidor. PC1 não tem GPU; Kaggle = 1 conta usável (ToS), 30 h/semana.

## 5. [comum: D:\video-fila\aprendizado.py — NÃO é tarefa do Fable, um chat comum cuida] Engenharia reversa dos parceiros
`D:\video-fila\aprendizado.py`: 1.205 achados, 571 grupos em `aprendizado\PARA_IMPLEMENTAR.md`, quase todos vistos
em 1 vídeo só, a dona não responde. Ninguém sabe quais truques dão view. Um chat comum (não você) vai cuidar dessa
engenharia reversa; aqui fica só para você saber que existe. O que eu apliquei no CCV em 28/10 está marcado como
"aplicado" lá.

## 6. [CLAUDE-CODE-VIDEO; a memória é disputada com PRODUTOS (produto.diario) e CORTES (clone)] Tempo e estabilidade: 2 a 5 h por vídeo
O CCV leva 2h–2h40 num dia bom e 5h+ num dia ruim (Pica-Pau 28/10: 16:20 → depois das 22h). Causas medidas hoje:
Gemini "high demand" (agora não gasta tentativa), verificador de legibilidade estourando 900 s três vezes, a memória
virtual do PC1 ESGOTADA (0,07 GB livre) por `produto.diario` do postador (5 GB privados parados) + clone do recapd,
render de correção travando 20 min (um às 15:05 sem causa achada). Log: `D:\claude-code-video\estado\gerar.log`.
**Pergunta pra você:** a distribuição de trabalho entre PC1/PC2/desktop/notebooks/Kaggle
(`D:\video-fila\maquinas.py`, `controlador.py`) está certa para o que cada máquina aguenta? Quem segura memória à toa?

## 7. [CLAUDE-CODE-VIDEO x todos os outros] Remotion x ffmpeg entre os projetos
O CCV edita em Remotion (React, 30 fps, kits acima); os outros projetos montam em ffmpeg/Python. Os efeitos do CCV
(recorte vivo com fundo limpo, 2.5D por profundidade, transições de rasgo, legenda karaokê com mola) não existem nos
outros, e os outros têm coisas que o CCV não tem (voz por clima, mascote, censura). Vale portar os kits para os
outros, ou o render do Remotion (~5 min/vídeo de 45 s, pesado em RAM) não compensa nos longos? Eu não medi.

---

## Fable — resultado (29/10)
- **Item 1 (alcance bimodal):** respondido com número em `ENGENHARIA_REVERSA\ER_01` e `FABLE_DECISOES.md` D1: os
  0–10 não perderam o teste do feed, **não receberam** (continuaram 100% com 2–5 views); dentro do mesmo canal o que
  separa 1.200 de 4 é se o YouTube deu o lote (canal/upload), e o que separa 1.200 de 6.000 é % assistido (13–24 s
  assistidos inteiros). Título, narrador, hora: sem sinal depois de tirar os não elegíveis.
- **Item 2 (júri × views):** o cruzamento está montado para os Cortes (`juri_x_views.py`), dado chega de 30/10 em
  diante; a métrica-alvo que o júri do CCV deveria prever é **% assistido ≥ 65%**, não "movimento/legibilidade".
  Enquanto não houver 1 vídeo do CCV postado, qualquer nota é opinião de modelo.
- **Item 3 (platô ~6):** se o júri não prevê (item 2), o platô é artefato do júri. Antes de mais regras no manual:
  postar 10 vídeos e medir. Formato: a referência de 14 mi dos Cortes (`REFERENCIA_NERDCF.md`) tem 28,8 s e 5,6
  cortes/10 s — Reel de 45 s "cena com foto + texto" é longo demais pelo dado do ER_01.
- **Item 4 (voz):** concordo com o diagnóstico (Resemblyzer aprova o que o ouvido reprova); TTS de prosódia só com
  GPU — fora do PC1. Sem opinião nova.
- **Item 6 (2–5 h por vídeo):** `baixa_prioridade.py` (D8) para testes; a memória esgotada é de `produto.diario`
  (4,8 GB) + `gerar.py --auto` (4,5 GB) — isso é decisão da dona sobre o que roda no PC1, não código.
- **Item 7 (Remotion × ffmpeg):** não portar kits antes de prova de views (CORTES_06): o PC1 não aguenta Chrome do
  Remotion na produção dos Cortes/longos, e o dado de hoje diz que o ganho está em tamanho/loop, não em efeito.

## [CLAUDE-CODE-VIDEO] Pendências novas para o Fable (29/10, depois do resultado acima)
**CORREÇÃO 29/10 09h:** eu escrevi que o CCV não posta — ERRADO. O `postar_insta_auto` pega o vídeo de
`saida\<conta>` (`produto\fila.itens_ccv`) desde 26/10: 7 posts no Instagram, sem ficha de medida (consertado, ver
registro do FABLE_DECISOES). Entretenimento (fakenews.ia4, recenas.ia) era barrado sempre pela trava de texto dos
anúncios (número da narração = "inventado"); consertado para aceitar o que a narração fala. Medidas: só Instagram.
**8. Prever % assistido ANTES de postar.** O CCV posta só no Instagram de contas com 0–2 views (D9) — nenhuma das duas linhas vai ter dado de retenção tão
cedo. Já existem curvas reais por vídeo (D11, `metricas_studio.json` → `curva`, `ret30/ret_meio/ret_fim`) dos Shorts
que receberam lote. Dá para montar um preditor sem IA cara (duração, cortes/s, fala por segundo, tempo até o 1º
texto, loop do fim, % de tela parada — o `referencia.py evidencia()` já mede vários) que dê ao júri do CCV e dos
Produtos uma nota ligada a % assistido em vez de "movimento/legibilidade"? Se o preditor não acerta nos Shorts
medidos, diga — aí o único caminho é postar.
**9. Conflito no melhorador central para linha SEM views.** `melhorador_central.py` (D12): `ligar --aplicar` liga o
`melhorador.py` do CCV, que otimiza nota de júri (`evolucao.jsonl`) — o mesmo que D1/D6 proíbem nos Cortes. A linha
CCV tem 0 vídeos no ledger, então a "pressão" dela nunca sobe por resultado. Regra sugerida (decida você): linha com
menos de N vídeos elegíveis medidos fica só em sombra, sem aplicar. Não mudei nada no central (regra do
FABLE_DECISOES).

## [CLAUDE-CODE-VIDEO] O que eu deixei pronto e funcionando (não refaça)
Trava de voz edge pura (proibida pela dona), elenco de famosos com bordões gravados nos anúncios, referência viral
automática (agora de Short de parceiro já baixado), fotos vivas, transições de rasgo, legenda com mola, trava de
texto sem alarme falso, "high demand" sem gastar tentativa. Decisões com data e como desfazer:
`D:\video-fila\linhas\CLAUDE-CODE-VIDEO\DECISOES.md`; estado: `ESTADO.md` na mesma pasta.
O melhorador automático do CCV (`melhorador.py`) está DESLIGADO por ordem da dona até ela mandar ligar.
