# D:\video-fila\ANALISE_CANAIS_PUNIDOS_28NOV.md — o que pode melhorar nos canais punidos e no que está baixo

Feito em 28/11/2026 00h30 pelo chat "Chat de projetos ativos", a pedido da dona ("analise tudo que pode ser melhorado nos
canais que estão com punição e todas as coisas que estão baixas"). Só leitura e teste em cópia; **nada de postagem foi
mudado** (regra: postagem só 10h–17h). Fontes: `MEDICO.md`, `estado\sinais_shorts.json` (2.628 Shorts),
`postador-de-videos\logs\uploads_ledger.jsonl`, `config\rampa_canais.json`, `bin\politica.py`, `relatorio_ronda.py`.

---

## 1. ACHADO PRINCIPAL — vídeos de canal punido agendados para FEVEREIRO de 2027

| Canal | Agendados no futuro | Último agendado | Dias à frente |
|---|---:|---|---:|
| Empresário Inteligente IA | 3 | 15/02/2027 09:30 | 79 |
| Clínica Lucrativa IA | 7 | 15/02/2027 09:30 | 79 |
| Bilionário Noturno | 3 | 15/02/2027 07:30 | 79 |
| ForjaReact | 3 | 14/02/2027 11:00 | 78 |
| AssistIA Investimentos | 2 | 13/02/2027 07:45 | 77 |
| CenaReact | 1 | 01/01/2027 07:30 | 34 |
| @CodigoInteligente-n7j | 4 | 01/01/2027 07:30 | 34 |
| HistoriasEmFrames | 2 | 30/12/2026 07:30 | 32 |
| Dorama Noturno | 28 | 22/12/2026 13:00 | 24 |
| Imóvel em Foco (cálculo do próximo) | — | 07/01/2027 | 40 |

**Por quê:** canal punido tem teto de 1 vídeo/dia + descanso do médico. Cada vídeo novo procura a próxima vaga livre, e o
laço `horario_publicacao` anda até 40 dias por volta; os vídeos se empilham meses à frente. O canal fica sem vídeo novo
saindo hoje, então o YouTube não vê sinal de recuperação. O Empresário Inteligente IA caiu 766 → 22 (−97%) nesse cenário.

**Melhoria proposta (para a dona aprovar):**
1. Teto de agenda: nenhum Short agendado a mais de 7 dias. Passou disso → o vídeo vai para outro canal vivo do mesmo nicho
   (o sistema já sabe redistribuir: `remarcar\redistribuir.py`) em vez de ficar parado meses.
2. Reagendar para os próximos dias, em horário nobre, os que já estão em 2027 (só no Studio, sem subir de novo).
3. Descanso do médico = canal sem vídeo NOVO, mas os já agendados não podem ser empurrados para depois do descanso.

## 2. A ALAVANCA "SÓ HORÁRIO NOBRE" NUNCA FOI APLICADA DE VERDADE

O médico marcou 9 canais como "só nobre (21–23 h)" porque 21 h dá **8,9 vezes** a mediana de views (2.628 Shorts).
O placar dele diz que a alavanca "não funcionou" em 7 de 9. Mas os vídeos não saíram no nobre:

| Canal (marcado só nobre) | Shorts em 10 dias | No nobre 21–22 h |
|---|---:|---:|
| Comédia Noturna | 17 | 0 (0%) |
| Curiosidades Noturnas | 32 | 7 (21%) |
| CenaReact | 38 | 9 (23%) |
| Imóvel em Foco | 33 | 10 (30%) |
| HistoriasEmFrames | 34 | 11 (32%) |
| Filme Noturno | 24 | 9 (37%) |
| Vendas que Escalam | 29 | 13 (44%) |
| Lei e Lucro | 18 | 10 (55%) |

**Causa (achada no código, `politica.py` linhas 653–677):** o código põe o vídeo às 21 h, mas quando o dia está cheio
ou há outro vídeo perto, empurra para o dia seguinte no **primeiro horário do canal** (9h30, 12h, 13h), saindo da janela.
Por isso a conclusão "o nobre não funciona" está errada: ele nunca foi testado.

**Conserto pronto e testado em cópia** (`D:\sistema\mapa\politica_nobre_PRONTO.py`):

| Canal | Próximo horário hoje | Com o conserto |
|---|---|---|
| Lei e Lucro | 29/11 09:30 | 29/11 21:00 |
| Vendas que Escalam | 29/11 09:30 | 30/11 21:00 |
| Imóvel em Foco | 07/01/2027 09:30 | 07/01/2027 21:00 |
| Comédia Noturna | 28/11 21:00 | 28/11 21:00 |

Aplicar entre 10h e 17h (mexe em postagem), com `.bak`. Volta: `MEDICO_ALAVANCAS=0` ou o `.bak`.
**Depois de aplicar:** zerar o placar "so_nobre" do médico, porque ele julgou uma alavanca que não rodou.

## 3. O QUE OS 2.628 SHORTS ENSINAM (sinais_shorts.json, views do Short ÷ mediana do canal)

| Sinal | Melhor | Pior | Usar mais? |
|---|---|---|---|
| Hora de publicação | **21 h = 8,9x**, 22 h = 2,0x | 16 h = 0,67x, 20 h = 0,78x | **sim — o maior sinal de todos** |
| Tipo de mídia | fatos 1,28x, pesca 1,23x, dorama 1,20x | **finanças 0,27x** (EVITAR) | parar finanças nos punidos |
| Narrador | pie 1,8–2,4x (RECEITA) | voz patolino 0,63x (EVITAR) | sim |
| Parceiro de origem | ultravoxfilmes01 4,8x, crystalcine 4,5x, xiuliamelo, sobanalisee, danielarecapsbr | — | priorizar esses parceiros |
| Saudação no início | A = 1,29x | — | sim |
| Fala rápida | A = 1,20x | B = 1,0x | sim |
| Título | > 80 caracteres 1,21x, estilo "busca" 1,11x | ≤ 40 caracteres: 70% zerados | títulos longos |
| Legenda | lateral 1,10x | centro 1,0x | lateral |
| Efeito de choque | raio azul 00d1ff 1,31x | raio amarelo ffc83d 0,86x | trocar o amarelo |
| Cobertura de logo | delogo 1,11x | tarja 0,97x | delogo |

**Achados para os canais punidos de finanças/negócios:** Lei e Lucro, Vendas que Escalam, Assist-IA, Empresário
Inteligente e Clínica Lucrativa são de finanças/negócios — justamente a mídia **pior (0,27x)**. Eles estão punidos E
recebendo o tipo de vídeo que menos rende. Proposta: para esses canais, só vídeos dos parceiros com RECEITA e títulos
no estilo "busca" > 80 caracteres, no nobre; ou mudar o nicho deles para fatos/curiosidades.

## 4. O QUE MAIS ESTÁ BAIXO (do relatório de 27/11 23:18)

| Item | Número | Causa | O que fazer |
|---|---|---|---|
| Kaggle | 0 de 54 GPUs | 401 em massa (4º banimento) | dona confere; conserto da central espera OK |
| Longos | 0 postados, 43 h | sem GPU do Kaggle | volta com o Kaggle |
| Celulares | 10 ok, 15 erros (28%) | 13x "lista de Contas não abriu" no A2 + S20 Ultra recusa adb | dona liga depuração do S20U; investigar a tela do A2 |
| TikTok | 114 ok, **212 falhas** | 2 perfis deslogados, 13 contas sem postar | investigar (próxima ronda) |
| Carrossel MS Energy | 169 h parado | provavelmente o Instagram @msenergycap bloqueado | conferir |
| Shorts 3D | 0 prontos, 11 falhas | PC3 desligado | dona liga o PC3 |
| Hydrogen (consertos de código) | 0 de 14 | modelo não entrega | parar de usar e deixar o Gemini 3.8 (9 de 11) |
| Gemini mídia | 17 erros de cookie/login | contas aulacomia (11), inovaremultiatendimento (10) | relogar essas 2 contas |
| Capas | 0 aplicadas hoje | fila vazia (98 feitas, 0 pendentes) | normal |
| Facebook Comédia Noturna / Cena React / Histórias em Frames | 0 Reels hoje | — | investigar |

## 5. ORDEM SUGERIDA (do que mais rende para o que menos)
1. **Aplicar o conserto do horário nobre** (pronto, 10h–17h) — maior sinal medido (8,9x).
2. **Trazer de volta os vídeos agendados para 2027** (teto de 7 dias + redistribuir/reagendar) — dona aprova.
3. **Canais punidos de finanças:** só parceiros RECEITA, títulos longos de busca, nobre.
4. Parar o Hydrogen nos consertos; relogar as 2 contas do Gemini.
5. Investigar TikTok (212 falhas) e a tela do A2 nos celulares.
