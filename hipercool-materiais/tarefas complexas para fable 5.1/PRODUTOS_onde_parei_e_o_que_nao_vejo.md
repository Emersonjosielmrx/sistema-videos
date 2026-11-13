# [PROJETO: LINHA PRODUTOS] Para o Fable 5.1 — onde os anúncios dos produtos travaram

> **De qual projeto é este arquivo:** linha **PRODUTOS** = Reels/TikToks de anúncio dos produtos digitais da Inovare
> (Hermes Call, Cardápio, Agenda, Disparo...). Código em `D:\postador-de-videos\bin\produto\`; pasta da linha
> `D:\video-fila\linhas\PRODUTOS\`. NÃO é o hipercool, nem o manhwa-react, nem o recap, nem o Claude Code Video
> (cada um tem o seu arquivo nesta pasta). Os itens 7 (máquinas) e 2 (júri) também afetam as outras linhas.

**Respostas da dona (28/10 23h) — valem para todo o arquivo:**
- Os produtos são TODOS DIGITAIS: não existem fotos de produto. Qualquer "tela do produto" tem de ser feita por código.
- Ainda não houve venda (praticamente nada vendido): não dá para medir venda. A medida possível é views, likes,
  salvamentos, comentários, seguidores e cliques no link.
- O melhorador automático (item 8) está desligado porque ela está usando o chat; você pode melhorar o desenho dele.
- Logins do desktop: ela logou todos; estão marcados como funcionando e há um vigia de erros (`D:\video-fila\
  vigia_desktop.py`, tarefa VigiaDesktop a cada 30 min).

Escrito em 28/10/2026 23h pela sessão que cuida dos vídeos de produto (Opus 5.5). A dona quer que você olhe onde eu
cheguei no meu limite e ache o que eu NÃO estou vendo. Eu aponto o lugar, o que já tentei e a pergunta. Prioridade
dela: o que traz mais views, likes, vendas e qualidade de vídeo.

Seus tokens são caros: leia só o indicado em cada item antes de varrer pastas. Regras da casa (valem para você):
`C:\Users\Haylla\.claude-vscode\CLAUDE.md` e `C:\Users\Haylla\.claude-vscode\projects\d--\memory\MEMORY.md`.
As que mais pegam aqui: voz edge PURA proibida (só como base do clone), nada de número/preço/prazo inventado na tela
ou na fala, agendar sempre (nunca público direto), sem Opus/Kiro nos pipelines automáticos (Argon → Gemini 3.8),
PCs remotos com 1 conexão por vez (rajada de ssh trava o desktop), arquivos compartilhados só com Edit.

**O que é a linha:** 1 Reel de ~30 s por produto (Hermes Call, Cardápio, Agenda, Disparo, Follow-up, VPS, Marketing,
CRM, Mentorias, Landing, Grupos, Agentes, SuperChat...), cada um no seu Instagram/TikTok. Pipeline:
`D:\postador-de-videos\bin\produto\` (`diario.py` → `video.gerar`: roteiro `agentes.py` → dono falando pelo Veo
(`apresentador`) + fotos do Flow / conversa animada `chat_ui.py` / cena Veo → voz clonada → montagem ffmpeg com
karaokê, efeitos de transição `efeitos.py`, cartão final → trava visual → júri `lapidar.py` (4 verificadores Gemini)
→ editor Remotion `editor.py` → fila). Estado: `D:\video-fila\linhas\PRODUTOS\ESTADO.md`; decisões com prova e
como desfazer: `DECISOES.md` na mesma pasta; histórico antigo `D:\postador-de-videos\docs\PRODUTO_PROFISSIONAL.md`.

---

## 1. (MAIOR ALAVANCA) Ninguém mede o que vende — todo o "melhorar" é no escuro
Tudo é postado pelo navegador (`postar_insta_auto.py`, TikTok pelos notebooks), os tokens da API de leitura do
Instagram venceram e o medidor por navegador `produto\medir_insta.py` levou 429 na 1ª chamada (parei para não
arriscar a conta). Resultado: o agente de variantes `produto\variacoes.py` (Thompson entre 10 formatos: dono 1 cena,
dono abre/fecha, Veo no meio, sem dono...) tem o placar **todo [0, 0]** — ele sorteia às cegas. O único sinal de
qualidade é o júri (item 2), que nunca foi comparado com views.
**O que eu não consigo:** um jeito de ler views/likes/salvamentos/cliques no link dos Reels e TikToks sem ser
bloqueado, e ligar isso a cada vídeo (o `.json` ao lado de cada mp4 em `D:\video-fila\produto_fila\<conta>\_postados\`
guarda variante, voz, efeito, pauta, nota do júri). Memória: "Tokens API dos 7 canais", "Instagram: aparelho novo
suspende", "Google só pelo navegador".
**Pergunta:** qual a medição mais segura e barata de VIEWS/likes/salvamentos/cliques (venda ainda não existe — dona
28/10) — frequência, conta, endpoint, ou cliques nas landings `<slug>.opus-sem-limites.com.br` — e como fechar o ciclo
"variante → resultado → próxima variante"?

### Fable — resultado (item 1, 29/10)
**Feito e testado: `bin\produto\medir_web.py` lê views/curtidas/comentários dos Reels pelo cofre (GraphQL + TLS do
Chrome do projeto navegador-sem-navegador), sem API nem token, 1× por dia por conta, e grava no placar das variações
(`ig:<codigo>`, campo `views` que o `contagem` usa) e em `medidas.instagram` do `.json` do vídeo.** O `variacoes.medir`
chama no fim; sem `curl_cffi` ele relança por `D:\veo\venv`. Casamento vídeo ↔ Reel pelo horário (o Reel sai 1–3 min
após `postado_em`; a conta posta vários por noite, então legenda/36 h não serviam). Qualquer 401/403/429 pausa 24 h.
Primeira rodada completa (29/10 02:44, 7 contas, 10 Reels postados há 48 h–4 dias): **todos entre 0 e 2 views, 0
curtidas** (disparoemmassa 0; fabricademarketing 0; followupia 1 e 1; futebolcom 1; inovarecom 0 e 0; sintetizerisada
2 e 1; vpsblindada 1). Placar agora: sem_dono 2/1, dono_abre_fecha 1/0 — mas com 0–2 views "sucesso = ≥ mediana da
conta" é ruído. **O achado que importa:** os Reels de produto não estão sendo distribuídos (nem o lote de teste do
Reels). Variante, júri, Veo, editor Remotion — nada disso é visto por ninguém hoje. Mesmo diagnóstico dos Shorts
(ER_01) e do hipercool (ER_03): contas novas/sem histórico, conteúdo que o Instagram classifica como anúncio/baixa
qualidade, ou conta restrita (a memória "Instagram: aparelho novo suspende" e "Instagram bloqueadas 27/10" apontam
restrições). O que fazer antes de otimizar vídeo: (a) ler o `perfil_info()` de cada conta (seguidores, profissional,
categoria) e o status de restrição no app — conta com 0 seguidores e 0 views em 10 Reels pede público inicial
(seguir/engajar manual pela dona, stories, colaboração com as contas que têm alcance como @msenergycap); (b) comparar
com um Reel da mesma conta que NÃO seja anúncio (ex.: curiosidade do nicho) — se esse também fica em 0–2, é a conta;
se passa de 100, é a classificação do conteúdo de anúncio; (c) só depois voltar ao ciclo de variantes. Detalhes, limites e
o que não fazer: `FABLE_DECISOES.md` D9. TikTok dos produtos fica fora até as contas entrarem no
`reuso_plataformas.json` (o `TikTokStudio.videos()` do nsn já dá views/salvos por vídeo). Cliques no link: ainda não
(as landings `<slug>.opus-sem-limites.com.br` podem contar no Traefik/servidor — é outro projeto).

## 2. O júri visual erra a causa — e eu otimizo em cima dele
Prova de 28/10 (Hermes 15:37, nota 6,5): o verificador "movimento" disse "cenas 1 e 2 pixel a pixel idênticas por 6 s"
e "cortes secos em todas as trocas". No vídeo real: mudança de 12–15% entre 20% e 80% de cada cena (medida do
próprio `lapidar.movimento`, limite 4%) e o efeito elétrico/clarão aparece em toda troca (conferi quadro a quadro).
O júri vê 3 miniaturas 270×480 por cena numa folha (`lapidar._quadros`) — zoom lento e efeito de 0,6 s não aparecem.
Ao mesmo tempo ele ACERTOU coisas que eu não via (foto de banco com clima errado, falta de "prova" do produto).
**Pergunta:** o júri deveria ver o VÍDEO (Gemini aceita vídeo) ou clipes curtos por cena, em vez de 15 fotos? Qual
desenho de júri prevê retenção/venda de verdade? (Ligado ao item 1: sem views não dá para calibrar.)

## 3. Platô da nota ~6 e o editor Remotion não ganha nunca
Notas do molde (montagem Python): 6,25 / 6,0 / 5,75 / 6,5 nos últimos 4. O editor Gemini em Remotion (`editor.py`,
manual `D:\postador-de-videos\remotion\EDITOR.md`) estourou o prazo em 4 de 5 vídeos, e quando termina perde do molde
(28/10: "melhor nota do editor -1,0 x molde 6,5", 105 min gastos). Os graves que voltam: "parece slide", "foto de banco
genérica", "falta prova visual do produto", "gancho frio nos 2 primeiros segundos", "cartão final parado".
**Já tentei:** zoom/pan com faixa (`ajustes.py`), destaques da fala entrando na tela, punch-in nas cenas do dono,
conversa animada obrigatória no bloco "como funciona", efeitos de transição, brilho/entrada do botão, corte do dono mudo.
**O que eu acho que não estou vendo:** talvez o FORMATO inteiro (dono + 2 fotos + conversa + cartão) seja errado para
vender serviço B2B no Reels. Não tenho referência viral de anúncio de serviço analisada (o CCV tem
`D:\claude-code-video\referencias\*\ANALISE.md` para entretenimento). Vale manter o editor ou desligar e investir no molde?

## 4. Pouco fato por produto = roteiro se repete e trava
Cada produto tem poucos FATOS (`kit.py` / `D:\veo\beta\pos_producao\assets\produtos.json`) e o revisor de fatos é
rígido (de propósito: nada inventado). Com muitos vídeos, as falas ficam parecidas (limite 0,72 no
`agentes.roteiro`) e o Hermes perdeu 2 vídeos em 28/10 esgotando 4 tentativas (repetição + "@" na legenda + revisor
barrando "vende muito mais"). Já pus a correção dizendo QUAL fala antiga é parecida e tirei a conversa de reserva do
caminho da aprovação. Pautas por conta: `D:\postador-de-videos\config\produto_pautas\<conta>.json`.
**Pergunta:** como gerar ângulos novos de verdade com os mesmos fatos (situações do público, objeções, casos de uso)
sem cair em promessa? Que fatos novos valeria pedir à dona por produto (lista curta, para ela só confirmar)?

## 5. Prova do produto na tela (a queixa nº 1 do "diretor")
O bloco "como funciona" mostra uma conversa de WhatsApp simulada (`chat_ui.py`). Para o Hermes Call (ligação por
WhatsApp com voz) uma conversa de texto não prova nada; o certo seria transcrição de chamada / tela de ligação /
painel. Outros produtos (CRM, VPS, Disparo, Landing) também precisariam de "tela do produto" própria. Os produtos
são todos digitais e NÃO há foto/print deles (dona 28/10): tem de ser tela simulada por código (base: `chat_ui.py`, a
landing de cada um em `D:\landings-produtos\`, mockups de celular em `D:\landings-produtos\hero_quadros.py`).
**Pergunta:** qual a "prova visual" certa por produto, feita por código (sem inventar número), e qual dá mais retenção?

## 6. Voz: clone sobre a Francisca (mesmo limite do CCV, item 4 do arquivo deles)
Hoje: edge Francisca como base → RVC (`video.clonar_vozes`, no PC2) com voz sorteada de
`D:\postador-de-videos\config\produto_vozes.json` (fatos_desconhecidos, moana, pica_pau). Funciona (28/10 provado),
mas o ritmo/entonação continuam os da Francisca. Público = adulto que compra (memória "Vozes por público").
**Pergunta:** vale testar TTS de prosódia (GPT-SoVITS/F5/XTTS no Kaggle) para o anúncio? Qual voz vende mais para dono
de negócio (sem dado de views — item 1)?

## 7. A base de máquinas é frágil e come a produção (dono pelo Veo espera até 1 h)
Só em 28/10, cada uma parou o vídeo do dono por horas: `D:\veo\beta\logs\PAUSE_SYSTEM` de "carga" ativo desde 25/10
sem ninguém para tirar; `config\netbooks_logins.json` apagado por corrida de gravação (o Veo achou que nenhuma conta
estava nas máquinas — consertado e reconstruído, ver MURAL de 28/10); o ssh do desktop passa a RECUSAR o PC1
(provável `PerSourcePenalties` do OpenSSH: muitas conexões curtas de vários robôs) enquanto aceita o PC2; Chrome
esquecido aberto no desktop bloqueando tudo; Flow (imagens) falhando em clique com timeout nos notebooks.
Peças: `D:\postador-de-videos\bin\maquina_remota.py` (logins, vez, tentativas, ORDEM_NAVEGADOR),
`D:\veo\beta\cadeia_veo.py`, `D:\veo\beta\cron_gerar_video_llm.py` (escolher_sessao), `D:\video-fila\maquinas.py`
(medir, AGENDA_CAMERA do desktop), `chrome_conta.py` nas máquinas, `D:\flow-imagens\`.
**Pergunta:** isso pede um agendador único de máquinas/contas (uma fila com dono de cada recurso, conexões ssh
reaproveitadas, estado que não se perde) em vez de cada robô consultar cada máquina? Qual o desenho mínimo?

## 8. O melhorador automático está pronto e desligado — confira o desenho antes de ligar
`D:\postador-de-videos\bin\produto\melhorador.py` + prompts `D:\postador-de-videos\config\melhorador\
{analista,decisor,revisor}.md` (o analista tem a seção "Como pensar" com o que eu aprendi errando) + botões com faixa
`produto\ajustes.py`. Tarefa `MelhoradorProdutos` DESABILITADA (a dona está melhorando pelo chat; só liga se ela
pedir — mas você pode melhorar o desenho dele à vontade). Ele só mexe em botões e regras
curtas; mudança de código vira "ideia_codigo". Com o júri do item 2 e sem views (item 1), tenho dúvida se ele vai
otimizar a coisa certa. **Pergunta:** o desenho dele (o que pode mexer, como decide, como desfaz) está certo?

## 9. Carrosséis: dão views (MS Energy) mas gastam 30–60 min cada
`D:\postador-de-videos\bin\carrossel_marca.py`: a ilustração é reprovada várias vezes por "texto_ou_letras" (log
`logs\carrossel_marca.log`, 28/10: 6 reprovações seguidas no SuperChat). O dono disse em 24/10 "carrossel deu muitas
views, aumentar". Ninguém mede quais carrosséis rendem (item 1). **Pergunta:** gerar a ilustração de outro jeito
(sem letra por construção) e qual formato de carrossel traz mais alcance/salvamento?

---

### Fable — resultado (itens 2–9, 29/10, curto: o item 1 muda a ordem de tudo)
- **2 (júri vê 15 fotos):** sim, o Gemini aceita vídeo — mandar 3 clipes de 4 s (abertura, troca de bloco, cartão
  final) em 480p custa menos que 15 fotos em tokens e deixa ele VER zoom/efeito. Mas não reescrever o júri agora: com
  0–2 views em 10 Reels, nenhuma nota é verificável. Quando houver alcance, a métrica que o júri deve prever é
  "% assistido" (Reels mostra "tempo médio de visualização" por Reel no app profissional).
- **3 (platô 6 / Remotion):** desligar o editor Remotion (105 min, perde do molde 4 em 5) e manter o molde. O dado
  dos Shorts diz que 30 s "dono + 2 fotos + conversa + cartão" é longo: testar 15–18 s (1 problema → 1 prova visual
  → 1 CTA) quando o alcance existir.
- **4 (fatos):** pedir à dona, por produto, 5 linhas: 1 número real (clientes/mensagens/dias), 1 objeção que mais
  ouve, 1 caso de uso concreto, 1 coisa que o produto NÃO faz, 1 frase que o cliente diz. Com isso o revisor de fatos
  continua rígido e os ângulos param de repetir.
- **5 (prova visual):** por produto, a "tela" que prova é a que o cliente vê no 1º dia: Hermes = tela de ligação
  recebida + transcrição ao vivo (dá para fazer em `chat_ui.py` com o layout de chamada); Disparo = fila de envios
  com status; CRM = kanban andando; VPS = terminal com uptime; Landing = a própria landing rolando (print animado da
  `D:\landings-produtos`). Sem número inventado: usar os de item 4.
- **6 (voz):** idem CCV item 4 — sem GPU não há prosódia; fora do PC1.
- **7 (máquinas):** o que já existe desde 23–24/10 e cobre o caso: vez única por máquina (`maquina_remota.ocupar/
  reservado`), `exibindo()` (telão), `cadeia_veo` com castigo, `Remoto.vivo()`. O que falta é só ORDEM de consulta
  (máquina viva → conta) e um dono por recurso; não precisa de agendador novo — precisa que todos os robôs passem
  pelo `maquina_remota` (o Flow de imagens não passava até 24/10). `PAUSE_SYSTEM` de carga sem dono: pôr validade
  (24 h) no arquivo.
- **8 (melhorador):** não ligar (D9). Desenho certo quando ligar: alavancas com faixa (já tem), decisão só por
  `medidas.instagram` (views/alcance) com os filtros de D1, nunca por nota; desfazer = `historico` com valor anterior.
- **9 (carrossel):** "texto_ou_letras" reprovado 6× = pedir a ilustração SEM texto por construção (prompt: "no text,
  no letters, no logo" + negativo) e pôr o texto no `carrossel_marca` por cima (PIL) — a IA não sabe escrever; nunca
  pedir que escreva. Medir carrossel pelo mesmo `medir_web` (`posts()` já traz curtidas/comentários dos carrosséis).

## PRÓXIMA TAREFA DO FABLE (aberta 29/10 pela sessão PRODUTOS) — só depois dos dados abaixo ficarem prontos
**10. Por que o Instagram não dá nem o lote de teste aos Reels de produto (0–2 views em 10 Reels, 7 contas)?**
> **DADOS PRONTOS 29/10 08:31:** `D:\video-fila\linhas\PRODUTOS\alcance\PRONTO.txt` + `RESUMO.md` (16 contas: 13 de
> produto + 3 de controle sem anúncio). O teste (b) "Reel não-anúncio dentro de conta de produto" ainda NÃO foi feito.
A sessão PRODUTOS (não o Fable) vai levantar os dados que o Fable pediu no item 1 (a)/(b) e deixar em
`D:\video-fila\linhas\PRODUTOS\alcance\` (`contas.json` = perfil_info de cada conta: seguidores, seguindo, posts,
profissional, categoria, idade, se posta pelo navegador/notebook, restrições vistas no app; `teste_nao_anuncio.json` =
Reel de curiosidade do nicho postado na mesma conta × anúncio, views em 48 h). Quando `PRONTO.txt` aparecer lá:
decidir se é CONTA (idade/0 seguidores/restrição/muitas contas no mesmo IP-aparelho/automação), CONTEÚDO (classificado
como anúncio, selo "feito com IA", áudio, link/CTA, reuso) ou os dois, e dizer a estratégia mínima para sair do zero
(o que a dona faz à mão e o que o sistema muda). Não otimizar vídeo/júri/variantes antes disso (D9).

**O que a sessão PRODUTOS executa sozinha das respostas acima (não é tarefa do Fable):** tela de ligação do Hermes e
"tela do produto" por produto no `chat_ui.py` (item 5); ilustração do carrossel sem texto por construção (item 9);
validade de 24 h no `PAUSE_SYSTEM` de carga (item 7); pedir à dona as 5 linhas de fatos por produto (item 4).
Dado novo sobre o item 3 (editor Remotion): em 29/10 00:18 o editor subiu o Cardápio de 6,0 para **7,0** (primeira vez
que ganhou do molde) — por isso o editor NÃO foi desligado ainda; registrar em `FABLE_DECISOES.md` se mudar.

## Pendências que NÃO são limite (só falta fazer; não gaste tokens nisso)
- Desktop: os 56 perfis estão marcados como logados (dona) e o vigia `D:\video-fila\vigia_desktop.py` avisa
  perfil que cair e ssh bloqueado. O ssh do desktop recusa o PC1 até isentarem a Tailscale no sshd_config de lá
  (`PerSourcePenaltyExemptList 100.64.0.0/10` + Restart-Service sshd; comando seguro passado à dona em 28/10).
- MS Energy ainda narra com edge puro (`D:\ms-energy\bin\video_real_ms.py`) — é de outra linha, está no MURAL.
- Vitrine IA e Inovare Claw sem Instagram.

## O que está pronto e funcionando (não refaça)
Voz clonada obrigatória (no PC2), efeitos de transição, destaques da fala em todo bloco, conversa de reserva quando o
Veo do bloco 2 falha, cabeça livre de cartão (YuNet), corte do dono mudo, visão com 3 Gemini de reserva, render e clone
no PC2, trava com PID no diário, landings com GSAP/hero e preços aprovados. Tudo com data/prova em `DECISOES.md`.
