# HANDOFF — supervisor da postagem/recuperação (sessão de 25/11 21h → 26/11 08h45)

Para: o próximo agente que assume este chat. Leia inteiro antes de mexer em qualquer coisa.
Escrito em 26/11 às 08h45. Os números de "estado agora" foram conferidos às 08h41.

---

## 0. Como trabalhar aqui (obrigatório)

- **Dona:** responda sempre em PT-BR informal, curto e para leigo. O detalhe técnico vai no código e nos .md, não no chat.
- **Fim de toda resposta:** uma linha `STATUS: CONCLUÍDO — …` ou `STATUS: AGUARDANDO USUÁRIO — <a pergunta>`.
- **Omarchy (esta máquina) é só central de comando.** Todo o trabalho roda no **PC1** (`ssh pc1`, Windows, cmd é o shell
  padrão do ssh: use `&` e não `;` quando encadear no cmd; em PowerShell 5 use `;` e nunca `&&`). Para scripts .ps1:
  escrever em /tmp → `scp` para `D:/video-fila/tmp_x.ps1` → `powershell -NoProfile -ExecutionPolicy Bypass -File …`
  → apagar os dois.
- **Diário do sistema:** toda decisão/conserto/ciclo vira 1 linha em `D:\video-fila\ARQUITETURA_PC1_SUPERVISOR.md`.
- **Memórias do PC1:** `C:\Users\Haylla\.claude-vscode\projects\d--\memory\` (ler `feedback_formato_ronda.md` e
  `project_medico_recuperacao.md` antes de relatar).

### Regras que não se quebram
1. **Nunca 2 contas pelo mesmo IP.** Antes de qualquer script que fale como conta, ler
   `D:\hipercool-materiais\comum\kaggle_gerente\INCIDENTE_BANIMENTO_02NOV.md`.
2. **Nunca usar conta viva do Kaggle para postar** (ex.: `murilodoctor192` ficou pausada no TikTok por isso).
3. **Nunca apagar vídeo do canal** sem a dona mandar, e no PC1 nunca apagar/sobrescrever sem perguntar.
4. **Fato Chocante fica DESLIGADO** (`usar=false`) até a dona logar a conta.
5. **PC2 só com a dona.**
6. Conta nova com captcha/confirmação no celular = **parar e avisar**, nunca forçar.
7. Sem senha em script.

---

## 1. Estado agora (conferido 08h41)

| Item | Estado |
|---|---|
| Postagem | **ligada** (`D:\postador-de-videos\config\POSTAGEM_DESLIGADA.json` não existe) |
| Shorts de parceiro agendados desde 25/11 21h | **30** |
| TikTok hoje (26/11) | **87** OK |
| Longos postados hoje | **2**: https://youtu.be/pRp1FBnCkts (02:58) e https://youtu.be/UoikCaCn1Wc (04:00, Fio da Meada, público, capa aplicada pelo STI) |
| Fato Chocante | `usar=false` (sem login) |
| PC1 | commit 5,8 GB (leve) |
| Fish | sti e asusx ativos; **itau fora da rede** desde ~02h (outras contas cobrem a voz) |
| Drive | ok (`rclone lsd manhwa-drive:` responde) |
| desktop (desktop2222) | **offline** (ssh timeout) desde ~01h |

**ATENÇÃO:** os crons e monitores da sessão anterior **morreram junto com ela** (eram só da sessão). O resumo das 9h
**não vai sair sozinho**. Recrie (ver seção 6).

---

## 2. O que foi feito nesta sessão (com como desfazer)

| # | Problema | Conserto | Arquivo | Como voltar |
|---|---|---|---|---|
| 1 | Shorts de canais **punidos** agendados para **jan–fev** (ForjaReact 14/02, Bilionário/Clínica/Empresário 15/02…) | Causa: teto 1/dia − reserva do dono 1 = 0 vaga todo dia; o laço andava 40 dias. Agora, com teto ≤ reserva, não há reserva (a vaga é de quem tiver vídeo). Mesma regra na `cota_restante` (antes dava 0 até 23h) | `D:\postador-de-videos\bin\politica.py` (`horario_publicacao`, `cota_restante`) — **sem .bak** | env `RESERVA_COM_TETO_BAIXO=1` |
| 2 | Mesma causa, segunda trava | O parceiro não agenda se o horário efetivo passar de `DIAS_FRENTE+1` (8 dias); o canal sai da rodada | `D:\recapd-ambientes\producao\bin\parceiro_diario.py` — **sem .bak** | env `PARCEIRO_TETO_LONGE=0` |
| 3 | Caixa "Hashtags sugeridas" por cima do título → espera de 60 s estourava **com o vídeo já enviado** (rascunho privado) | `_escrever` tenta 3x: fecha a sugestão pelo cabeçalho do diálogo, Escape **só** se `tp-yt-iron-dropdown:visible` (senão fecharia o diálogo), 3ª com `force` | `D:\postador-de-videos\bin\youtube_web_poster.py` | `.bak_25nov_titulo` (conferir se é desta sessão antes de restaurar) |
| 4 | Dona: "comparar sempre com o dia anterior" | Recuperação agora é **ontem × anteontem** (🟢 +10%, 🔴 −10%, ⚪ igual); % da média pré-ban fica só de referência e continua decidindo as alavancas | `D:\video-fila\medico_recuperacao.py`, `D:\video-fila\relatorio_ronda.py` (`sec_recuperacao`) | `.bak_25nov_diaant` nos dois |
| 5 | Dona aprovou religar o TikTok | 18 de 19 contas "MORTA" de 12/11 religadas (`pausada` → `pausada_antes_25nov`). **murilodoctor192 continua pausada** (conta viva do Kaggle) | `D:\postador-de-videos\config\reuso_plataformas.json` | `.bkp_25nov_despausar` |
| 6 | Dona aprovou a 1ª postagem do Fato Chocante | Ligado, **falhou** ("perfil do navegador não está logado", prendeu a rodada ~30 min) → **desligado de novo** | `D:\postador-de-videos\config\youtube_navegador.json` | `.bkp_25nov_fato` |
| 7 | Dona aprovou mover estoque dos 17 canais travados para os vivos | **Não movido, de propósito:** todo canal vivo pt já tem 10–110 dias de estoque (o limite é o teto 1/dia dos punidos); esportes/jogos/animais não têm canal vivo | — | — |
| 8 | Rodada antiga (22:47) rodando com código velho | Encerrada às 23h25 enquanto só baixava do Drive (sem upload no meio) e disparada uma nova | — | — |

**Resultado verificado do conserto 1+2:** todos os punidos voltaram a agendar para 26–28/11, por exemplo:
ForjaReact 27/11 21:45, Fio da Meada 28/11 21:00, Assist-IA 26/11 22:15, Empresário 27/11 22:00, Clínica 27/11 21:15,
Imóvel 26/11 21:30, Vendas 26/11 21:45, Bilionário 27/11 21:30, Filme Noturno 28/11 21:15 (https://youtu.be/yECSeiZJF-I),
Lei e Lucro 27/11 22:00 (https://youtu.be/KFKL7LuCkBg).

**Falhas da noite:**
- Filme Noturno 00:29: título (conserto 3), **deixou rascunho**; reenviou e agendou às 02:25.
- Lei e Lucro 01:49: timeout **antes** do arquivo entrar (print `logs\yt_web\20261126_014903_falha_leielucro.png` = tela
  "Enviar vídeos" vazia), sem rascunho; agendou às 02:30.
- Tech Noturno 04:39: timeout de 60 s **sem print e sem log** de qual campo; agendou às 04:52.
- A correção 3 ainda **não foi exercitada**: nenhum "campo #title… não aceitou" nos logs.

---

## 3. Coisas acontecendo que NÃO são defeito (não "consertar")

- **inovare manhwa br:** limite diário de envios do YouTube até **26/11 09:41**. O sistema respeita e não insiste.
- **Mistérios Noturnos:** segurando envios porque um vídeo decolou (+4.459 views/6 h contra média 1.400).
  `viral_desde = 26/11 03:34`, `VIRAL_MAX_H = 18` → solta **no máximo às 21:34**. O número igual se repete porque o
  histórico de views é lido poucas vezes ao dia (`rampa_canais.segurar_viral` / `_ganhos_6h`).
- **Canais punidos com "cota do dia 0":** já usaram a 1 vaga do dia (com o conserto 1 isso agora é real, não bug).
- **17 canais travados pelo YouTube:** pulados antes do Drive (`config\contas_travadas.json`).
- **Dorama Noturno:** 21 agendados em dezembro, mas o canal está travado, então não abrem.

---

## 4. Pendências que esperam a DONA (perguntar, não fazer sozinho)

1. **Apagar 2 rascunhos privados quebrados:** Fio da Meada `cPQnT-EZuxE` e Filme Noturno o "1795663138 video".
2. **Logar o Fato Chocante:** `python D:\logins-google\cofre.py logar phikhanh141173` (conta nova, ela faz no PC). Depois
   religar `usar=true` em `youtube_navegador.json` (31 Shorts prontos, teto 3/dia).
3. **13 Shorts em canais vivos agendados para 30/12–15/02** (feitos antes do conserto). Abrem sozinhos nas datas.
   Trazer para perto = mexer na data no Studio de vídeo já aceito (risco) → só com o "sim" dela, 1 por 1.
   Lista: ledger `D:\postador-de-videos\logs\uploads_ledger.jsonl` com `publish_at` > hoje+9d (ex.: ForjaReact
   `crzU0IYbgCc` 02/01 e `i7G4qZqz7J8` 14/02; Bilionário `_Qg95vT24j0` 01/01 e `bEGldYJUSUI` 15/02; Clínica
   `upX4qX6eqek` 30/12 e `sL3bLZ0wSek` 15/02; Empresário `xmt9iUk6SbQ` 30/12 e `bkoYuOfd8PU` 15/02; Assist-IA
   `L1l9CetVvc0` 02/01 e `vCRE48etqOE` 13/02; HistoriasEmFrames `2O7gu9p18UM`; `novo_codigo_inteligente_n7j`
   `T--uLoevcps`; `novo_universo_ia_d6s` `DqPbzQ_wsuo`).
4. **Alerta de conteúdo:** Clínica Lucrativa `eW5Mj0bCtgQ` (27/11 21:15), título sobre "Tadalafila". Remédio pode chamar
   atenção do YouTube. Avisado, não mexido.

---

## 5. Tarefas abertas do AGENTE (fazer sem perguntar)

1. **Agora:** mandar o **resumo da noite** (o cron das 9h07 morreu). Modelo na seção 7. Contar desde 25/11 21h.
2. Recriar o acompanhamento (seção 6) se a dona quiser continuar com ronda; os monitores morreram.
3. Depois de **09:41**: confirmar que o inovare manhwa br voltou a agendar (vídeo `sem-obra-eadb43_cap1_20261122` na fila).
4. **Itau fora da rede** desde ~02h: ver no Tailscale/ssh se voltou; se não, avisar a dona (é notebook físico).
5. **desktop offline:** só conferir; PC2/desktop não se mexe sem a dona.
6. **Timeout do Tech Noturno 04:39 sem print:** se repetir, descobrir em qual espera (`youtube_web_poster.py`: espera do
   `input[type=file]` 60 s na linha ~1017 ou do título 120 s) e fazer o `_shot` sair em toda falha.
7. Quando aparecer "campo #title… não aceitou" no log, conferir se o envio terminou (prova do conserto 3).
8. **Médico 07:10** decidiu: Fio da Meada e Imóvel em Foco em **descanso 3 dias**; Filme Noturno e Assist-IA como
   **controle**. Resultado só mensurável a partir de ~29/11 (`DIAS_AVALIAR`).
9. Fazer `.bak` de `politica.py` e `parceiro_diario.py` (ficaram sem cópia desta sessão).

---

## 6. Ronda noturna/automática (como era e como recriar)

Era um cron de 30 em 30 min (`13,43 * * * *`) + um Monitor de 30 min religado a cada expiração:

```
tail -n0 -F D:/recapd-ambientes/producao/logs/parceiro_postar.log D:/recapd-ambientes/producao/colab/postar_longos.log \
 | grep --line-buffered -E "AGENDADO|DESLIGADA|Traceback|não subiu|ok: https|erro DEPOIS" \
 | grep --line-buffered -vE "decolando|limite diário"
```
(Isso rodava **dentro do PC1**. Daqui do Omarchy, rode o mesmo via `ssh pc1` ou peça para a sessão do PC1.)

Checklist de cada ciclo, com 1 linha no ARQUITETURA_PC1_SUPERVISOR.md:
1. `POSTAGEM_DESLIGADA.json` não pode existir (se existir com CENTRAL-RESERVA, renomear com sufixo da hora).
2. `parceiro_postar.log`: AGENDADO nas últimas rodadas, 0 Traceback, nenhum "tão longe" em canal com vaga.
3. `uploads_ledger.jsonl` crescendo; TikTok `logs\tiktok_AAAAMMDD.log` com "OK #".
4. Longos (`colab\postar_longos.log`) e capas (`colab\capas_depois.log`) sem erro repetido.
5. Controlador (`D:\video-fila\logs\controlador_AAAAMMDD.log`) rodando; `systemctl --user is-active fabrica-fish` em
   sti/asusx/itau.
6. PC1 com commit < 30 GB; Drive respondendo.

Ao explicar uma trava para a dona, diga o motivo real (limite, decolando, cota, intervalo de 45 min) e não chame de erro.

---

## 7. MODELO DE RELATÓRIO COMPLETO (o que a dona combinou)

Fonte: memória `feedback_formato_ronda.md` (PC1). Resumo das regras:

1. **Rodar o script** `python D:\video-fila\relatorio_ronda.py` (todas as seções, com as colunas **desde a última** e
   **hoje**; guarda a hora em `estado\relatorio_ronda.json`). Faltou um dado: acrescente uma seção **no script**, não à
   mão no chat.
2. **Colar o relatório do script INTEIRO**, sem cortar nem resumir. A dona já reclamou disso em 16/11.
3. Depois dele, nesta ordem:
   - **🔍 Análise: onde melhorar e o que vou fazer.** Escolher o(s) pior(es) número(s) de: Gemini/Flow (com e sem
     navegador, erro por tipo), celulares (render/Gemini/postagem), Shorts 3D, erros do vigia/melhoradores,
     pesquisador × gargalo. Para cada um: número → causa provável → o que faço AGORA, feito na mesma ronda com chave e
     teste.
   - **🛠️ O que consertei:** cada conserto em 1 parágrafo (o que estava errado, o que mudou, testado como, número antes
     × depois).
   - **🙋 Só você pode fazer:** pendências da dona, cada uma dizendo onde e qual conta (usar a seção 4 deste handoff).
   - **🔜 O que faço em seguida:** lista curta.
4. Títulos com emoji, frases curtas, tabelas quando houver número, português informal. **Só fato verificado.**
5. **Recuperação dos canais:** começar SEMPRE pelo **dia a dia** (quantos subiram/caíram ontem × anteontem, tabela por
   canal). O % de antes do ban fica só de referência. Fonte: `MEDICO.md` (07:10) e `relatorio_ronda.sec_recuperacao`.
   Último médico (26/11 07:10): **5 subiram, 8 caíram, 1 igual**. Fio da Meada +88%, Curiosidades +33%, Clínica +24%,
   CenaReact +19%, Filme +13% | Imóvel 0% | Tech −13%, Mistérios −14% (ainda 216% da média pré-ban), HistoriasEmFrames
   −19%, Comédia −20%, Assist-IA −20%, inovare br −42%, Vendas −82%, Lei e Lucro −87%. A queda de 24/11 tem a ver com
   a postagem parada pelo MacBook nesse dia. Os Shorts que voltaram em 25–26/11 só aparecem nas views de 27/11 em diante.
6. Itens FIXOS em toda ronda (com "desde a última" e "do dia"): Instagram pelos IPs grátis (avisar na hora se travar),
   Flow imagem/vídeo (pedidos, ok, falhas por tipo/máquina, tempo médio), envio por HTTP × Chrome, máquinas com % de
   aproveitamento na última hora e no dia.
7. Terminar com a linha `STATUS:`.

### Resumo da noite (o que o cron das 9h07 ia mandar e ainda falta)
Em português, começando pelo que importa:
- Shorts de parceiro agendados desde 25/11 22h (ledger + `parceiro_postar.log`), TikTok, longos e capas.
- Recuperação ontem × anteontem (item 5 acima).
- O que quebrou e como consertou (seção 2).
- O que precisa dela (seção 4).
- Anotar no ARQUITETURA_PC1_SUPERVISOR.md.

---

## 8. Atalhos

- Disparar rodada do parceiro: `Start-ScheduledTask ParceiroKaijinre-Postagem` (antes confira que não está `Running`).
- Ver vaga de um canal: no PC1, em `D:\postador-de-videos`:
  `python -c "import sys;sys.path.insert(0,'bin');import politica as p;c,_=p.achar_canal('novo_X');print(p.horario_publicacao(c,None,'parceiro'),p.cota_restante(c,'parceiro'))"`
- Médico em ensaio (não aplica): `python D:\video-fila\medico_recuperacao.py`. Ele **sobrescreve o MEDICO.md**:
  copie antes e restaure depois. Aplicar = `--aplicar` (só a tarefa das 07:10 faz isso).
- Prints das falhas do Studio: `D:\postador-de-videos\logs\yt_web\*falha_<canal>.png`.
