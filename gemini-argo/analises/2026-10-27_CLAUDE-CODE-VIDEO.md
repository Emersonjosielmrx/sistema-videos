# 27/10 — Linha CLAUDE-CODE-VIDEO (D:\claude-code-video, Reels em Remotion) — Argon x outros modelos

Chat: sessão do sistema Gemini + Claude Code Video. Pedido da dona: "teste todos no melhorador … me traga as notas" +
"as notas do vídeo e da criação do vídeo". Notas minhas (Opus 5.5).
Dados brutos: `dados\2026-10-27_CLAUDE-CODE-VIDEO_*` (respostas de cada papel, roteiros, chave do teste às cegas e
os 2 scripts para repetir). Também em `D:\video-fila\linhas\CLAUDE-CODE-VIDEO\DECISOES.md`.

## Modelos (gateway :20133)
gemini-4-argon (puro), argon-pro (= hx-socorro-kiro neste dia), argon-kiro, argon-gemini, argon-opus, argon-flash e a
referência agy/gemini-3.8-flash-high. O Kiro acabou às ~10:45 (volta 01/11): argon-kiro e argon-pro ficam fora da escolha.

## Prova 1 — melhorador (análise + proposta de mudança no manual do editor), sombra, nada aplicado
Entrada igual para todos: a 1ª versão dos 4 últimos anúncios (notas e defeitos do júri) e o manual `remotion\EDITOR.md`.
Papéis do `melhorador.py`: analista → propositor → crítico, com a validação em Python no meio.
Gabarito = os defeitos REAIS do anúncio de hoje (`vpsblindada_ia_20261027_042208`, 1ª versão 6,0): card em cima da
cabeça do dono, cenas 2 e 4 iguais, gancho fraco, "100%"/"garantido" inventados e caixa de legenda vazia. Também:
a regra de rosto (linha 68) e a de molde (linha 65) JÁ existem no manual e só foram medidas em 1 vídeo.

| modelo | nota | tempo | o que fez |
|---|---|---|---|
| argon-pro | 7,5 | 218 s | análise 8 (juntou parada + molde repetido); ESPERAR (a regra nova só foi medida 1 vez) — correto |
| argon-gemini | 7,5 | 192 s | análise 8 (rosto, parada, gancho = o real); ESPERAR, viu que a regra de rosto já existe |
| gemini-4-argon | 6,5 | 138 s | análise 7 (errou: culpou letra < 34 px); "proibir molde repetido": alvo certo, regra vaga |
| argon-kiro | 6,5 | 451 s | análise 7; esperar, motivo fraco |
| argon-flash | 6,0 | 311 s | análise 7; "micro-movimento em tudo": concreta, mas o movimento já não era o defeito principal |
| argon-opus | 5,5 | 278 s | análise 8; propôs a regra de rosto que JÁ existe; o crítico dele aprovou sem ver |
| gemini 3.8 (ref., sombra das 02h) | ~7,5 | ~3 min | esperar |

Nenhum achou o texto inventado nem a legenda vazia: esses só a trava de texto e o júri pegaram.

## Prova 2 — CRIAÇÃO: roteiro do anúncio (VPS Blindada), às cegas
O mesmo prompt da produção (`gerar.prompt_roteiro`, só os fatos do kit). Embaralhei, dei a nota e só depois abri a
chave (`dados\…_chave_cega.json`). Critérios: gancho, fala natural, nome da marca, texto de tela forte, só fatos, imagem
por cena.

| modelo | nota | tempo | por quê |
|---|---|---|---|
| argon-pro | 8,0 | 31 s | melhor gancho ("vive com medo do servidor cair"), texto de tela concreto, só fatos |
| argon-kiro | 7,5 | 87 s | gancho de dor forte, imagens com gente do público; cena 3 cheia demais |
| argon-gemini | 7,0 | 203 s | bom; exagera um pouco ("o tempo todo", "sempre protegida") |
| gemini-4-argon | 6,5 | 101 s | correto, mas NÃO diz "VPS Blindada" em nenhuma cena ("Nós entregamos") |
| argon-opus, argon-flash, gemini 3.8 | ✗ | > 15 min | travaram quando o Kiro acabou |

Roteiro de entretenimento (Fato ou Fake): nenhum terminou, no mesmo horário.

## Conclusão (1 rodada por prova)
- Sem o Kiro, o mais equilibrado aqui é o **argon-gemini** (empatado em 1º no melhorador, 3º no roteiro, sem deslize).
- O **Argon puro não foi o melhor em texto curto** (bate com a PRODUTOS). Na análise do melhorador ele ficou em 6,5
  aqui e 9,5 na PRODUTOS: a diferença está no gabarito (lá era um conserto de movimento já medido; aqui o certo era
  esperar). Conclusão provisória: ele vai bem quando há um defeito concreto para achar.
- **Falta a nota de VÍDEO:** o próximo anúncio sai com o argon-gemini no roteiro e a nota da 1ª versão (mesmo júri) vai
  ser comparada com a dos últimos anúncios do Gemini 3.8 (6,0–6,5). Resultado aqui quando sair.
