# Treino do melhorador: Gemini (caixa separada) x sessão Claude — mais nova em cima

## 27/10 10h — rodada dos Argon (dona: "testar todos no melhorador, comparar com o código que eu mexer, notas")
CÓDIGO (caixa isolada, tarefa: karaokê "atingiro" — vão medido no quadro: hoje 0 px). Conserto real Claude: 2 espaços
(9 px). Notas 0–10:
| modelo | tempo | o que fez | vão | nota |
|---|---|---|---|---|
| Gemini 3.8 | 506 s | 2 espaços (= Claude) | 9 px | 10 |
| Flash + Argon | 459 s | 2 espaços (= Claude) | 9 px | 10 |
| Argon + Gemini 3.8 | 908 s | \h\h\h (funciona, largo) | 18 px | 8 |
| Argon + Opus 4.6 | 443 s | não editou; sugeriu \fsp8 (funciona) | 8 px | 3 |
| Argon Pro | 157 s | Spacing 15 = espaça as LETRAS ("a t i n g i r") | — | 2 |
| Argon puro (texto) | 18 s | Spacing 2 (espaça letras) + estragou "BackColour"→"BackCloth" (quebraria o ASS) | 4 px | 1 |
| Argon + Kiro | 492 s | não editou (acabaram os turnos) | — | 0 |
| Argon puro (ferramentas) | 254 s | erro ("I seem to be encountering an error") | — | 0 |

TEXTO (mesmo prompt por HTTP: achar problemas nas 9 passagens do KwdN + reescrever). Gabarito: "caralho", "Capiroto",
"Alexandre Moreno" (pessoa real), "meu chapa" repetido. Todos acharam caralho/Alexandre/meu chapa; Capiroto só Gemini 3.8
e Flash+Argon. Nenhuma reescrita ficou com palavrão.
| modelo | tempo | achou | >25 palavras | reescrita (nota Claude) |
|---|---|---|---|---|
| Argon puro | 274 s | 14 problemas | 1/18 | 9 — mais engraçada e no personagem (Holandês Voador, 99,1%, Leôncio) |
| Argon + Kiro | 178 s | 10 | 0/18 | 8,5 — presa à história (Ojin, matinho) e no personagem |
| Argon Pro | 178 s | 16 (mais completo) | 1/18 | 8,5 |
| Flash + Argon | 31 s | 10, inclusive Capiroto/plomo | 0/18 | 8 — curta e certeira, menos história |
| Argon + Opus 4.6 | 342 s | 15 | 2/18 | 7,5 — rica, mas longa e soltou "bastardos" |
| Argon + Gemini 3.8 | 210 s | 9 | 0/18 | 7,5 — longa (média 24 palavras) |
| Gemini 3.8 | 32 s | 7, inclusive Capiroto | 0/18 | 7 — limpa, porém genérica |
Conclusão: Argon (puro/Pro/Kiro) = melhor ESCRITOR (passagens, jeito do narrador); para CÓDIGO o Argon puro errou
feio — código fica com Gemini 3.8 / Flash+Argon. Revisor de palavrão/regras: Flash+Argon (rápido e achou tudo).
27/10 11h — Kiro acabou (até 01/11): Argon+Kiro e Argon Pro (reserva Kiro) fora. Escolha sem Kiro:
CÓDIGO 1º Flash+Argon (10, 459 s) = Gemini 3.8 (10, 506 s); 3º Argon+Gemini (8, lento 908 s).
27/10 12h — CORREÇÃO: a rodada de código foi antes da trava do Flash-Lite (10:10) e em paralelo; refeita 1 por vez:
Argon puro c/ arquivo no prompt 10 (208 s, o mais rápido), Flash+Argon 10, Argon+Opus 10, Argon+Gemini 10 (18 min),
Argon puro c/ ferramentas 2 (não terminou). O "Argon errou feio" acima era Flash-Lite. Regra: Argon 1 por vez.
TEXTO/VÍDEO 1º Argon puro (9); 2º Flash+Argon (8, 31 s, melhor revisor); 3º Argon+Opus / Argon+Gemini (7,5); Gemini 3.8 (7).

## 27/10 04h — conserto na caixa: gancho cobrindo o rosto (bateu nas duas análises)
- Claude (real): deitado = fonte 46, 2 linhas de 34, faixa translúcida (BorderStyle 3) no topo (y 2,5%); retrato
  igual. Prova: quadro antes/depois no 5FDt — rosto livre.
- Gemini (caixa): diff IDÊNTICO ao do Claude, até o comentário "júri e sessão Claude" → CONTAMINADO: ele leu o arquivo
  real (editado durante a rodada dele). Comparação INVÁLIDA.
- Correção do método: (1) o Gemini roda PRIMEIRO e a sessão Claude só mexe no original depois que ele termina;
  (2) a caixa bloqueia leitura fora dela (settings deny Read nas pastas reais).

Método da dona (27/10): os dois analisam; não bateu = melhorar o prompt do Gemini; bateu = o Gemini faz o conserto
numa CÓPIA do código (caixa, sem chance de quebrar o original), a sessão Claude faz o conserto real, compara os dois
trabalhos e ajusta o prompt de novo.

## 27/10 03h — análise do 5FDt e 6d2a
| achado | Gemini | Claude (quadro real) | bateu? |
|---|---|---|---|
| gancho escrito cobre o rosto | sim (6d2a olhos, 5FDt boca) | sim (4wuf: gancho em cima da cabeça) | ✅ |
| balões/caixas em inglês | sim | sim | ✅ |
| final parado | sim | sim (4wuf: 3 quadros iguais) | ✅ |
| plano parado > 9 s no meio | sim (6,2% medido) | não conferido ainda | — |
| karaokê "atingiro" (palavras grudadas) | "grudadas" | espaço EXISTE, só estreito ("atingir o" legível) | ❌ exagerou |
| nome do narrador na legenda | sim | sim (já corrigido 26/10 22:20) | ✅ |
| gore excessivo / sem mascote | não citou | sim | ❌ não viu |

Ajustes no prompt do Gemini (juri_longo legibilidade + PROMPT_MELHORADOR): (1) "antes de dizer que palavras
grudaram, confira se há espaço estreito e descreva exatamente o que vê (estreito x ausente)"; (2) incluir sangue/gore
excessivo (risco de desmonetização) e ausência de mascote/CTA no foco de retenção.
