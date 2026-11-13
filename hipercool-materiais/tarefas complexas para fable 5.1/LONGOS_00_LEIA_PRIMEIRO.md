# Tarefas complexas para o Fable 5.1 (escrito em 28/10/2026 pela sessão Opus que cuidou dos LONGOS)
> **29/10 — decisões do Fable:** `FABLE_DECISOES.md` nesta pasta. Quem quiser mudar algo marcado "Fable" no código
> ou nos ajustes lê lá antes (regra da dona). Resultados por tarefa: seção "Fable — resultado" de cada arquivo.
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

A dona pediu: o Fable varre o sistema de vídeos e melhora o que os outros modelos não conseguem — **prioridade para o
que traz mais views, likes e qualidade de vídeo**. Cada arquivo `LONGOS_NN_*.md` desta pasta é uma frente da linha LONGOS (os outros prefixos — CORTES_, PRODUTOS_,
CLAUDE-CODE-VIDEO_ — são das outras linhas): **o objetivo**,
**por que importa**, **onde olhar** (arquivos), **o que já se sabe**, **onde a sessão anterior parou** e **como medir**.
A ideia é apontar o lugar; a análise e a solução são suas. Procure também o que **não** está aqui (o que nós não vimos).

## Mapa rápido dos projetos (ler antes)
| Projeto | Onde | O que é |
|---|---|---|
| recapd (recap de anime/manhwa: Shorts de parceiro + LONGOS) | `D:\recapd-ambientes\producao` (`bin\`, `colab\`, `config\`) | pipeline `bin\anime-pipeline.py`; longo roda no Kaggle via `colab\cliente.py` → VPS `hermes-prod:/opt/recap_central` → `colab\kaggle_trabalhador.py` |
| hipercool (manhwa narrado, canais Inovare/Manhwa Noturno) | `D:\hipercool-videos` (ler `CLAUDE.md`, `docs\correcoes_pendentes.md`) | `bin\hiper-pipeline.py`, efeitos 2.5D, capas |
| Materiais comuns | `D:\hipercool-materiais` (`assets\`, `comum\`, modelos, Python) | `comum\` = 1 versão do código comum; cópia "# COMUM" nos `bin\` |
| Postagem | `D:\postador-de-videos` (`bin\politica.py`, `config\youtube_navegador.json`) | YouTube pelo navegador (sem API), sempre agendado |
| Controle/painel | `D:\video-fila` (painel :8790 `painel_controlador.py`, `avisos.py`, `linhas\*`) | linhas de trabalho: `linhas\LONGOS`, `linhas\CORTES`, `linhas\PRODUTOS`, `linhas\CLAUDE-CODE-VIDEO` |
| Veo / Flow | `D:\veo\beta` (`gera_auto.py`, `cron_gerar_video_llm.py`), `D:\flow-imagens` | vídeo/imagem pelo Google Flow automatizado |
| Gateway de IA | OmniRoute na VPS 157 (`secrets\omniroute.json`) | modelos `gemini-fila`, `antigravity/gemini-3.8-flash-tiered`, Argon... |

Regras da dona que valem para qualquer mudança (estão na memória do Claude Code, `C:\Users\Haylla\.claude-vscode\projects\d--\memory\MEMORY.md`):
nunca postar público direto (sempre agendado); nada de janela na tela dela (tudo oculto); yt-dlp sem rajada (bloqueia o
IP de casa); vozes edge puras proibidas (só com clone); nada no disco C:; não mexer nos workers do PC2; Google só pelo
navegador (sem API do Cloud).

## Prioridade sugerida (maior efeito em views primeiro)
| # | Frente | Por quê |
|---|---|---|
| 01 | Retenção real do YouTube → o que cada efeito/trecho faz com a audiência | hoje melhoramos às cegas (só views totais) |
| 02 | Título + capa (CTR) com teste de verdade | CTR é a maior alavanca de views e quase não é medida |
| 03 | Roteiro/narração do longo no nível do Porão Manhwa | a análise de um vídeo de 482 mil views mostrou o que falta |
| 04 | Melhorador A/B com estatística que funcione com poucos vídeos | pronto mas desligado; ruído de views engole o efeito |
| 05 | Cortes do longo para os canais de cortes (escolha multimodal + aprendizado) | Shorts dão alcance; hoje a escolha é só pelo texto |
| 06 | Mascote viva: voz igual à boca + recorte limpo | a dona quer que pareça uma mulher real dona do canal |
| 07 | IA silenciosamente fora do ar → qualidade cai sem ninguém ver | 28/10 o Gemini 3.8 "tiered" travou e o longo perderia o resumo sem erro |
| 08 | Automação do Veo/Flow frágil | baixou vídeo de outro robô; prompt que não entra; contas presas |
| 09 | Capacidade de render (GPU sem cota, CPU +35% com efeitos, RAM do PC1 esgotada) | gargalo de quantos vídeos saem por dia |
| 10 | Código duplicado/divergente entre projetos e código morto | bugs que nunca rodaram (ex.: parallax25d com erro de sintaxe) |
| 11 | Fonte de vídeo (yt-dlp, legenda, proxies) | sem fonte não há vídeo; legenda pelo proxy cai em "não é robô" |
| 12 | Controle de qualidade automático do vídeo inteiro | nós olhamos 3–4 quadros; erro no meio do vídeo passa |

Ao terminar cada frente, escreva no próprio arquivo o que fez, o que mediu e o que ficou.

## Arquivos por linha (cada sessão escreveu os seus — o prefixo diz de qual projeto é)
- `LONGOS_NN_*.md` (01 a 12 acima) — sessão dos LONGOS (este arquivo). **`LONGOS_13_auditoria_pedidos_da_dona.md`** =
  TODOS os pedidos da dona na linha LONGOS × o que foi feito (conferir no vídeo real).
- `CORTES_00_LEIA_PRIMEIRO.md` + `CORTES_01..08_*.md` — linha CORTES (Shorts de parceiros, recapd): testes A/B sem
  ligação com views (placar novo em 28/10), dado do Studio furado (21 de 591 com retenção), formato do Short x
  referência de 14 mi, júri x views, voz, acoplamentos que deram 3 defeitos, mascote/choque/Remotion, CPU do PC1.
  Complementa 01, 04, 06 e 09 daqui. **NOVO 29/10 08h30 (sem resposta ainda):**
  `CORTES_10_NOVO_29-10_PENDENTES.md` — 6 testes juntos contra a D3, nicho pela fonte e não pelo assunto, disco cheio
  derrubando a memória (produção parou 00h-05h), melhorador central x testes dos Cortes. (O CORTES_09 foi substituído.)
- `CLAUDE-CODE-VIDEO_onde_parei_e_o_que_nao_vejo.md` — linha CLAUDE-CODE-VIDEO (Remotion): alcance bimodal com os
  números do diagnostico_alcance.py, júri nunca comparado a views (nenhum vídeo do CCV postado), platô da 1ª versão
  ~6, voz (medidor de semelhança aprova o que o ouvido reprova), 2–5 h por vídeo e memória do PC1 esgotada,
  Remotion x ffmpeg.
- `PRODUTOS_onde_parei_e_o_que_nao_vejo.md` — linha PRODUTOS.
- `VEO_01_fila_central_e_creditos.md` (01/11) — todos os projetos que usam o Flow: fila central única com prioridade
  (chat > clientes > produtos > reserva) e paralelismo adaptativo; castigo "login caiu" em conta logada; saldo
  diferente da mesma conta por máquina. MVP de créditos reais já no ar (`veo\docs\CREDITOS_E_FILA_CENTRAL.md`).
- Pastas `navegador-sem-navegador`, `sonnet web`, `sonnet-web-claude` — de outras sessões (não conferido por mim).
- `hermes-call\LEIA_PRIMEIRO.md` (29/10) — Hermes Call + ativador de números: banimentos, código do WhatsApp que
  não chega ao número novo, leitura de tela do ativador, rede dos Androids, conversão da campanha.
