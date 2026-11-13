# Pesquisador de melhorias dos vídeos (criado 03/11/2026)

## AGORA É AUTOMÁTICO (04/11/2026): motor com o Sonnet 5.5 web, sem chat e sem Opus
- **Ver como está:** abra `PAINEL_PESQUISADOR.md` (reescrito a cada volta) ou rode `python motor_pesquisador.py status`.
- **Entrega e cobrança (dona 04/11):** cada pesquisa ok vai sozinha para `ENTREGAS\<LINHA>.md` (CURTOS, LONGOS, CAPAS,
  VEO_HIPERCOOL). A tarefa `CobradorPesquisador` (1 em 1 h, `cobrador.py`, Gemini sem Opus, igual ao sentinela) manda
  ao chat registrado de cada linha (`chats_linhas.json`; o chat se registra com `motor_pesquisador.py sou <LINHA>
  <nome>`) os blocos pendentes. 05/11: ENTREGA PROVADA (cada mensagem leva `[cobranca LINHA-AAAAMMDDHHMM]`; se o
  código não aparecer no histórico do chat na volta seguinte, reenvia, até 3x) e RESPOSTA MEDIDA (avaliados +
  implantados + reprovados da linha; chegou e nada mudou em 3 h = lembrete, até 3, depois "NÃO RESPONDE" no painel;
  bloco novo só gera mensagem se a última foi há >= 3 h). Chat fechado = não manda. Ninguém implanta sozinho: o chat da linha
  analisa, implanta o que der e retorna com `implantado` / `reprovar`. `implantados.json` também vai no pedido
  ("não pesquisar de novo"). Log: `cobrador.log`.
- **Reprovou um achado? Registre** (dona 04/11: o que os chats reprovam vira aprendizado): 
  `python motor_pesquisador.py reprovar dono/repo "motivo curto" <chat>` -> `reprovados.json`, marca REPROVADO no
  catálogo e todo pedido novo leva os motivos ("não traga de novo nem coisa do mesmo tipo").
- **Achados ainda não entregues ao chat da linha (ex.: Veo/hipercool):** `PENDENTE_ENCAMINHAR.md` — leia se for desse chat.
- **O que foi achado:** `CATALOGO_DESCOBERTAS.md` (só repos que EXISTEM; INÉDITO / USA arquivo:linha / CITADO).
- **Liga/desliga:** `python motor_pesquisador.py ligar|desligar`; teto à mão: `python motor_pesquisador.py teto N`.
- Tarefa do Windows `MotorPesquisador` (5 em 5 min, oculta) -> `motor_pesquisador.bat` -> 1 pesquisa no máximo por volta.
- Com cota: emenda uma pesquisa atrás da outra (2 min de pausa). Sem cota (ou cota acabou no meio): agenda a próxima
  para a HORA DE VOLTA que o MonitorSonnet informa (`esperar_ate` no motor_estado.json) — não espera 5 h à toa nem
  tenta antes. O teto/dia (48) é só trava de segurança e sobe sozinho se for batido sem falha. Grava cada passo na
  hora (`.eventos.jsonl`).
- Falhas ficam no registro com o tipo: `sem_cota_no_meio`, `erro_proxy` (tenta 3x), `timeout` (25 min),
  `incompleta`, `sem_web`, `interrompida` (PC desligou). Tema que falhou NÃO é marcado e volta na fila (2 falhas = amanhã).
- Limites do claude.ai e o que já medimos: `LIMITES_SONNET_WEB.md`. Desenho e motivos: `MOTOR_DESENHO.md`.
- Por que o Sonnet: na medição de 03-04/11 (5 modelos, mesmo pedido) foi o mais confiável (COMPARACAO_MODELOS.md).
- Ele NÃO implanta nada. Quem implanta é o chat do projeto, seguindo `video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md`.

Pedido da dona (03/11): "guarde os parâmetros dessa pesquisa ... para que cada vez as buscas sejam mais abrangentes e
com mais agentes específicos para cada coisa e de cada projeto" + "repita usando argon-pesquisa e gemini-pro-pesquisa
para comparar: assim sabemos se o Argon é melhor, se pegou coisa que o outro não pegou, e juntando dá mais dados".

## Pesquisador ≠ melhorador (dona, 03/11)
- **Melhorador** (aprendizado.py, melhorador_central, variantes): roda sozinho, OBSERVA os vídeos feitos, estuda o
  que melhorar e faz as melhorias.
- **Pesquisador** (esta pasta): ferramenta do CHAT, usada quando houver MUITA cota de tokens sobrando. Guarda o
  conhecimento dos projetos e das áreas e o HISTÓRICO das rodadas (`ja_conhecidos.txt`, `historico_areas.json`)
  para nunca pesquisar as mesmas coisas nem trazer os mesmos resultados. Substitui abrir chats com pesquisas soltas.
- Agentes: comparar Argon x Claude (sonnet-ajudante) x Gemini Pro com o MESMO pedido; o `placar.json` decide.
  "Se o Argon for melhor, usaremos ele" -> deixar só ele em `config.json` agentes_pesquisa.

## Peças
| arquivo | o que é |
|---|---|
| `config.json` | contexto global (máquinas, regras), formato da resposta, **áreas** (id, nome, subtemas) e **projetos** (pasta, docs, áreas-chave). Editar aqui para mudar o alcance. |
| `ja_conhecidos.txt` | repos já pesquisados/usados -> entram no pedido como "não repetir" (a busca vai mais longe a cada rodada). |
| `pesquisador.py` | gera os pedidos, confere links na API do GitHub, compara argon x gemini, junta, cresce as áreas. Só biblioteca padrão. |
| `rodadas/<data>/` | `pedidos/*.md`, `respostas/<id>__argon.md` e `<id>__gemini.md`, `rodada.json`, `COMPARACAO.md`, `JUNTO.md`. |
| `placar.json` | placar acumulado Argon x Gemini Pro (web usada, repos citados, % que existem, novos, exclusivos). |
| `conferidos.json` | cache da API do GitHub (★, último push, licença, arquivado). |
| `historico.json` | quando cada área/projeto foi pesquisada (a mais antiga vai primeiro). |

## Como rodar uma rodada (chat)
1. `python pesquisador.py rodada --modo tudo` (ou `area`, `projeto`, `cruzado` = projeto × cada área-chave;
   filtros `--areas a,b` `--projetos x,y`). Por padrão é **DUPLA**: cada pedido sai para `argon-pesquisa` E
   `gemini-pro-pesquisa` (mesmo texto). A saída lista agente + arquivo do pedido + arquivo da resposta.
2. Para cada linha, uma chamada Agent (no máx. **20 ajudantes ao mesmo tempo**; mandar em lotes e soltar o
   próximo quando um terminar). Texto do pedido ao ajudante:
   > Leia o pedido completo em `<pedido>` e faça a pesquisa, abrindo páginas de verdade. Grave a resposta
   > COMPLETA em UTF-8 em `<resposta>` (Python open(...,'w',encoding='utf-8')). Para mim devolva SÓ a linha WEB,
   > quantos itens gravou e os 3 melhores em 1 linha cada.
   Pedido sem arquivo de resposta = ainda falta mandar (ou o ajudante não gravou: gravar a resposta dele à mão).
3. `python pesquisador.py comparar rodadas\<data>` -> COMPARACAO.md (quem achou mais repos que EXISTEM, quem usou
   web, exclusivos de cada um) + JUNTO.md (união, ordenada por estrelas, com quem achou) + placar.json.
4. `python pesquisador.py importar rodadas\<data>\JUNTO.md` (vira "já conhecido") e
   `python pesquisador.py areas_novas rodadas\<data>\respostas\*.md` (subáreas sugeridas viram áreas novas no
   config: a próxima rodada já é mais abrangente). `python pesquisador.py marcar <ids>`.
5. Revisão: mandar o JUNTO.md ao `sonnet-ajudante` ("aponte erros com prova, o que serve a cada projeto").
   Depois o resumo para a dona + linha em `D:\gemini-argo\COMPARACAO_MODELOS.md` com o placar.

## Cuidados
- Ajudante pode responder SEM web (de memória) — a 1ª linha "WEB:" e o `comparar` (repo existe?) pegam isso.
  Argon sem cota vira Flash-Lite/Gemini 3.8 calado: placar ruim de repente = cota acabou, não o modelo.
- API do GitHub sem token: 60 consultas/h (o cache segura; `GITHUB_TOKEN` no ambiente sobe para 5000/h).
  Não envolve nenhuma conta do pool (regra do IP não se aplica), mas não rodar em laço sem pausa.
- Licença: canais monetizados -> marcar NÃO-COMERCIAL/sem licença/AGPL; ler o LICENSE antes de implantar.
- Pesquisa NÃO implanta. Implantar segue `D:\video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md` e, nos longos,
  `D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md`.
- No Opus: só esses ajudantes baratos (nada de opus-ajudante/Workflow).

## Histórico
- 03/11: 1ª onda (20 frentes, um ajudante cada) -> `D:\hipercool-materiais\pesquisa_github_03nov2026.md`.
  Rodada `rodadas\2026-11-03_1205` (32 áreas × 3 agentes = 96 pedidos) gerada, NÃO enviada (cotas zeradas);
  mandar depois das 21:41 em lotes de 6-8 (a de 11:26 foi apagada: perdeu tudo por 429).
- 03/11 ~11h40: Argon SEM COTA em todas as contas até 21:41; Gemini Pro (ponte do PC) caiu; Sonnet web 429.
  Causa provável: ~20 ajudantes ao mesmo tempo. Lição: mandar no máx. ~6-8 por vez. Retomar a rodada dupla
  DEPOIS das 21:41 (pedido sem arquivo em `respostas\` = refazer). Comparação feita com Argon sem cota não vale.
  Gemini Pro também ficou sem cota (volta 21:41). 1ª onda: VOLTARAM efeitos, melhorador, mascote, anime/QC,
  distribuição, nichos, trilha, longos (resumo em pesquisa_github_03nov2026.md); FALHARAM (refazer na dupla):
  áudio, visual, retenção/capa/SEO, voz rápida+humana, desempenho GPU, roteiro, legenda, capa/imagem,
  localização, direitos, orquestração. Diagnóstico local (sonnet) retomado após 429.

## 12/11 — ORIENTAÇÃO do que pesquisar (dona: "procura muita coisa que não usamos, aí é lixo")
Medido: 1210 reprovados x 4 implantados; 2547 das 2579 áreas foram sugeridas pelo próprio Sonnet (TTS, ONNX, LoRA, licença de pesos...).
- `orientacao.json` (o motor lê a cada volta): **foco** (áreas que vão na frente, na ordem: recap/mais vistos, outras línguas, séries/compilados, título/capa, retenção, distribuição, roteiro/memes, celular/ffmpeg/disco, política) · **nao_pesquisar** (área pulada e recusada como área nova: 605 das 2575) · **texto** (vai em todo pedido: o que SERVE e o que é LIXO). Editar o JSON = muda na próxima pesquisa. `PESQUISADOR_ORIENTACAO=0` desliga.
- Filtro automático antes de ir pros chats (`lixo_automatico`): sem licença/GPL, arquivado ou parado há mais de 18 meses não entra no catálogo nem nas caixas (vai pro ja_conhecidos; `motor_registro.jsonl` evento descarte_auto). Estrelas NÃO filtram (os 4 implantados tinham 0 a 5). `PESQUISADOR_FILTRO_AUTO=0` desliga.
- Área nova: no máximo 3 por pesquisa e só dentro da orientação.
