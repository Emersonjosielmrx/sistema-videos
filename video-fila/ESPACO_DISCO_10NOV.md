# Análise de espaço em disco — 10/11/2026

Pedido da dona: "analise o que está ocupando tanto espaço que não está no Drive: vídeos postados, arquivos temporários".
Medido só o tamanho REAL (sem contar atalhos/junctions duas vezes). Nada foi apagado.

## Situação
| Disco | Livre |
|---|---|
| C: | **1,9 GB** (crítico) |
| D: | 9,6 GB |

## Disco C: (70 GB usados)
| O que | GB | O que é | Dá pra liberar? |
|---|---|---|---|
| `C:\Users\Haylla\.claude\projects` | **28,0** | Histórico das conversas do Claude Code (9.635 arquivos .jsonl; quase todos dos últimos 15 dias) | **Sim, mas só a dona decide** (regra: nunca apagar dados do Claude). Opção segura: mover para o D com junction, ou zipar os de mais de 7 dias |
| Windows | 18,2 | Sistema | Não |
| AppData (Chrome 4,5, VS Code 2,1, Programs 3,0) | 13,5 | Perfis e programas | Não (perfis do Chrome não se apagam) |
| Program Files | 11,2 | Programas | Não |
| `.claude-vscode` | 3,9 | Conversas do VS Code | Mesma regra do .claude |

**Conclusão C:** 28 GB dos 70 são conversas do Claude. É a única coisa grande liberável e depende da dona. Mover pro D
(junction `C:\Users\Haylla\.claude\projects` -> `D:\caches\claude_projects`) libera os 28 GB sem perder nada.

## Disco D: (o que parecia grande e NÃO é)
- `historias-em-frames` mostrava 101 GB: são 0,5 GB reais (prod/teste/beta são atalhos para o mesmo venv e assets).
- `recapd-ambientes\producao\workspace` e `hipercool-videos\workspace` mostravam 35 GB cada: são atalhos para
  `hipercool-materiais` (contados duas vezes).
- `pagefile.sys` (24 GB) está no D, de propósito.

## Disco D: o que pesa de verdade (`hipercool-materiais`, 86,6 GB reais)
| Pasta | GB | O que é | Dá pra liberar? |
|---|---|---|---|
| `animes recap\shorts` | 21,7 | 844 Shorts de anime/manhwa, todos de menos de 30 dias. Os 1.220 já postados com cópia no Drive JÁ foram apagados do PC | Não agora: são a reserva ainda não postada (ou sem registro no catálogo) |
| `models` | 15,7 | Modelos de IA (RVC 10 GB, Whisper, Kokoro, HuggingFace) | Não (usados na produção) |
| `videos\the-inheritor` | 8,0 | Capítulos de uma obra do hipercool | Conferir se está no Drive (hipercool parado) |
| `assets` | 8,1 | Trilhas, efeitos, fontes, mascote | Não |
| `python` | 5,4 | Ambiente Python | Não (memória: NUNCA mover python\venv) |
| `veo` | 4,8 | Vídeos do Veo | Conferir postados + Drive |
| `amostras_voz` | 4,6 | Amostras e treinos de voz | Talvez (testes antigos) |

## Recomendações (dona decide)
1. **C: mover `.claude\projects` (28 GB) para o D** com junction — maior ganho, sem perder conversa.
2. `the-inheritor` (8 GB): se estiver no Drive (rclone check), apagar do PC — hipercool está parado.
3. Shorts de `animes recap`: manter (é a reserva). Os já postados+Drive já saem sozinhos.
