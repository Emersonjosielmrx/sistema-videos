# Variações da mesma voz por momento da história

Arquivo de controle da análise (retomável: cada achado é gravado aqui na hora).

## Pedido do dono (20/10, palavra por palavra)

> algusn nao combinou com a voz do antonio no caso as vozes da mulheres masi me permitiu ter uma ideia quando mudamos
> da base do tahlita ou francisca para o antonio a voz em si e a mesma mais parece que ele mesmo esta imitando uma voz
> de um personagem maligno isso e uam caraterisca da voz huamna e dos narradores em si quando estao narrando eles mudam
> sua voz dependendo da situacao do clima do video e como narrar uma parte boa engracad adepois anrrar uma luta onde a
> voz do kororo e ir acelerando ela e como o momento do gol no futebol que o anrrador vai flando masi rapido conforme
> vai chegando eprto do gol, e a mudar pra um momento de terror, nenhum deixa de ser a mesma voz mais ela muda podemos
> fazer isso talvez aqui mesmo provocando essas mudancas como ja acontece quando mudamos da thalita para o antonio
> pdoemos criar varias variacoes e usar elas depenendo do momento da historia assim ficaria relamente parecido com o
> humano  analise tudo e veja como pdoemos fazer

## Frentes

| # | Frente | Status |
|---|--------|--------|
| F1 | Estado do teste francisca × antonio (19 narradores) | em andamento |
| F2 | Medir POR QUE o Antonio soou "vilão" e por que nas mulheres não combinou | pendente |
| F3 | Mapear o que a produção já tem de variação (voz_clonada, narracao_curva, misto, patches do Applio, clone2) | pendente |
| F4 | Botões disponíveis (base TTS, velocidade, tom, faixa de entonação, formante, volume, pausas, efeitos) | pendente |
| F5 | Paleta de climas (parâmetros por clima, calibrados por narrador homem/mulher) | pendente |
| F6 | Como escolher o clima de cada trecho (marcação no roteiro + regras de transição) | pendente |
| F7 | Amostras pro dono ouvir (cada clima + mini-história trocando sozinha) | pendente |
| F8 | Plano de integração na produção (arquivos, tempo, todos os projetos) | pendente |

## Achados

### F1 — teste francisca × antonio
- 20/10 10:10: 31 de 38 clones prontos em `saida_todos\`. Faltam: jubertim_antonio, mangaticos (2), mattz (2), momo (2).
- Tom aplicado (o MESMO nas duas bases, calibrado pra Francisca, `tom_base="2_edge_francisca"`): billie_eilish -5,
  rihanna -5, ijax -5, drezin -6, porao/omelhormanhwa/solem8037/solemsun -10, iki -13, guugou/pie -14, morgan_freeman -15.
- Dono ouviu: nas vozes de MULHER o Antonio não combinou; nos homens deu a mesma voz "imitando um personagem maligno".
- O 403 em todos os proxies (sessão anterior) NÃO era bloqueio: o teste rodava com o Python do C: (edge-tts 7.2.8).
  Com o edge-tts 7.3.1 (venv) Antonio, Thalita e Francisca respondem direto, sem proxy (testado 20/10 10:20).

### F2 — por que soou "vilão" e por que nas mulheres não combinou (medido, RMVPE)
- **As bases do teste não eram as que o nome dizia.** `edge_tts_engine` (COMUM) sem a variável `VOZ_CLONADA` troca as
  vozes "proibidas": Francisca → Thalita e **Antonio → Andrew** (`VOZES_PROIBIDAS`, linha 31). O `gerar_teste.py` não
  define `VOZ_CLONADA`, então:
  - "francisca" = Thalita (mesmo nº de amostras que a "thalita", diferença ~2%) → por isso "Thalita = Francisca";
  - "antonio" = **Andrew Multilingual** (semelhança do espectrograma: Andrew real 0,77 × Antonio real 0,37).
  - Francisca real (gerada direto, `bases_reais\francisca.wav`) tem tom 238 Hz; a Thalita 181 Hz — são diferentes.
- Tom mediano (RMVPE): Thalita 181 Hz, Andrew 110 Hz (8,7 semitons mais grave), Andrew 11% mais lento (30,8 × 27,7 s)
  e entonação mais "chapada" (faixa 9,5 × 10,3 st).
- O tom do clone foi calibrado na Francisca REAL (238 Hz, `tom_2_edge_francisca.txt`) e aplicado em bases mais graves:
  - versões "francisca" (Thalita) saíram **~5 st abaixo** da voz natural de TODOS os narradores (-4,4 a -5,8);
  - versões "antonio" (Andrew) saíram **12–14,5 st abaixo** (mais de uma oitava). Homens: 54–67 Hz (mike 59,
    guugou 54, porao 65) = registro de monstro/vilão. Mulheres: billie 84, rihanna 82, ijax 83, drezin 78 Hz =
    faixa de voz MASCULINA → "não combinou".
- O f0.txt dos narradores está certo (RMVPE no voz.wav bate ±1 st: mike 121, porao 134, momo 210, doinsuka 294).
- Conclusão: o "mesmo narrador fazendo voz de vilão" veio de **tom bem mais grave + fala mais lenta e mais chapada**,
  com o timbre do narrador preservado pelo RVC. Dá pra produzir isso de propósito, na dose certa, em QUALQUER base e
  em qualquer narrador (mulher com descida menor, sem cruzar pra faixa masculina).

### F3 — o que a produção JÁ tem (reaproveitar, não refazer)
- `voz_clonada.py lote` aceita POR FRASE: `entrada` (wav de qualquer base) ou `texto`+`velocidade` (Kokoro),
  `tom_extra` (semitons inteiros), `f0_escala` (faixa de entonação, patch APPLIO_F0_ESCALA), `final_st` (fim de frase,
  patch APPLIO_F0_FINAL_ST), `eq`, `index_rate`, `protect`, `volume_envelope`. Formante: só por narrador
  (`perfil_v2.json` aplicar.formant) e é aplicado na BASE antes da conversão (rvc\lib\utils.py load_audio_infer).
- `narracao_curva.py` (COMUM) faz a INTENSIDADE: impactos escolhidos 1x por vídeo (LLM ou heurística), subida tipo
  gol (+18% e +4 dB, curva quadrática), respiro depois (-12%, -3 dB), grito/reticência, `variacao()` por trecho de
  3–7 frases (respiração real do narrador, pausa, ênfase, ritmo dentro da frase, sala, de-esser, onda de energia).
- `anime_tts.preparar_clone` + `base_da_frase("misto")`: já troca a BASE por frase (Kokoro na abertura e na subida
  pro impacto, Francisca no resto) — é exatamente o mecanismo do pedido, só que com 2 climas fixos.
- `perfil_v2.json` por narrador (ritmo, faixa de entonação, EQ, fim de frase, por base) e `linguagem_v2.json`
  (jeito de falar: mike "debochado, empolgado"; momo "debochado, dinâmico e irreverente").
- hipercool: `fx_detect.detect_mood_from_text` dá o CLIMA de cada fala por palavra-chave (tense_dramatic,
  sad_emotional, romantic_sexy, funny_lighthearted, calm_chill, neutral_chill) e já muda cor, partícula, meme e
  TRILHA por clima (`fx_music`). Luta e terror caem juntos em tense_dramatic — pra voz precisa separar.
- `edge_tts_engine` tem VOCAL_ARCHETYPES (vilão, mentor, cômico, assustado...) pros PERSONAGENS das histórias — só
  rate/pitch do edge, sem clone.
- O que falta: nada escolhe o TIPO de clima pra voz do narrador; todo trecho sai com o mesmo "jeito" (só muda a
  intensidade).

### F4 — botões que dá pra girar sem perder a identidade (o RVC mantém o timbre)
| Camada | Botão | Já existe? |
|---|---|---|
| base | voz (Francisca, Thalita, Kokoro, Antonio, Andrew), velocidade, tom, contorno (SSML) | sim (por frase) |
| clone | tom (semitons, relativo à voz natural), faixa de entonação, fim de frase, mistura de timbre, proteção | sim (por frase) |
| clone | formante (voz "maior/escura" ou "menor/clara") | só por narrador → aplicar na base antes |
| depois | volume, pausa antes/depois, respiração real, EQ (escuro/brilhante), sala/eco | sim (humanizar), EQ/eco não por clima |

### F5 — paleta de climas (1ª dose, pra o dono ouvir e ajustar) — em `variacoes\gerar_variacoes.py` (CLIMAS)
Tom em semitons RELATIVO à voz natural do narrador (homem / mulher); mulher nunca desce abaixo de 165 Hz.
| Clima | Base | Velocidade | Tom | Entonação | Volume | Pausa | Timbre | Extra |
|---|---|---|---|---|---|---|---|---|
| normal | Francisca | a do narrador | 0 | a dele | 0 | 0,30 s | — | — |
| engraçado | Francisca | +8% | 0 | ×1,25 (mais melodia) | +1 dB | 0,20 s; 0,55 s antes da frase que fecha a piada | 1,04 (sorrindo) | brilho +2 dB 3 kHz |
| tensão | Francisca | -8% | -1 | ×0,80 | -2 dB | 0,50 s | 0,98 | respira antes |
| terror | Francisca | -16% | -2 | ×0,65 (quase reto) | -4 dB | 0,80 s | 0,96 | escuro (-3/-5 dB agudos), eco leve, respira |
| vilão | Francisca (A/B c/ Antonio, Andrew) | -12% | -8 / -3 | ×0,75 (frio) | +1 dB | 0,60 s | 0,92 (voz "maior") | peito +2,5 dB 140 Hz |
| luta (gol) | Kokoro pm_santa | sobe pedaço a pedaço até +35% | 0, +1 no "gol" | ×1,15 | 0 → +4 dB | 0,06 s; 0,85 s + respiro depois do gol | — | presença +1,5 dB 2,5 kHz |
| épico | Francisca | -6% | -1 | ×1,10 | +2 dB | 0,70 s | 0,97 | eco de sala |
| triste | Francisca | -10% | -1 | ×0,85 | -3 dB | 0,65 s | — | fim de frase caindo (-1,5 st), respira |
O tom NÃO sobe nos climas fortes (dono 17/10: +6 Hz soou "fina e aguda"): quem leva a emoção é velocidade, volume,
pausa e a faixa de entonação. No vilão o tom DESCE (é o efeito que o dono gostou).

### F6 — como escolher o clima de cada frase
- Produção já faz 1 chamada de LLM por vídeo pra escolher os impactos (`narracao_curva._pelo_llm`). A mesma
  chamada passa a devolver também o clima de cada frase, da lista fixa acima (custo ≈ zero a mais).
- Reserva sem LLM: palavras-chave (como `fx_detect.detect_mood_from_text`, mas separando luta × terror × tensão e
  vilão = fala entre aspas/ameaça).
- Regras pra soar humano e não "picotado": normal é a casa (volta pra ele); trecho mínimo de 2 frases (exceto a fala
  do vilão e o gol); luta sempre termina num impacto e tem respiro depois; o "tom" do narrador (`linguagem_v2.json`:
  debochado → mais engraçado) pesa na escolha.
- hipercool: o mesmo rótulo alimenta a trilha (`fx_music`), cor e partícula — voz e música mudam juntas.

### F7 — amostras (20/10 11:12, prontas em `variacoes\`)
- `1_mike_HOJE.mp3` (como a produção faz hoje), `2_mike_COM_CLIMAS.mp3`, `3_momo_COM_CLIMAS.mp3`, `vilao_ab\`
  (mike: Francisca/Antonio/Andrew a -8 st + Andrew "igual ao teste"; momo: Francisca/Antonio a -3 st), `trechos\`.
- Conferido com RMVPE em cada trecho: doses entraram (±1–2 st = entonação da frase). Vilão mike 81 Hz (-7 st),
  momo 178 Hz (-2,8 st, segue voz de mulher). Clone: mike 40 trechos em 919 s, momo 22 em 365 s (PC ocupado).
- Nenhum arquivo da produção foi alterado por esta análise (só leitura). Aguardando o dono ouvir.

### NO AR (20/10 ~14:30) — dono: "variações da mesma voz no mesmo vídeo... todos os tipos possíveis, pode aplicar"
- Novo `D:\recapd-ambientes\producao\bin\climas_voz.py` (paleta CLIMAS, escolha por LLM 1 chamada + reserva por
  palavra-chave, cache `_climas_voz.json` na pasta dos áudios, piso de tom mulher 165 Hz / homem 60 Hz, eco).
- `anime_tts.preparar_clone`: cada frase recebe o clima (base, velocidade, tom, entonação, fim de frase, EQ, volume,
  pausa, eco). Clima forte (≠ normal/engraçado) ignora a curva de gol (senão o vilão acelerava). Tudo em try:
  falhou = frase sai como antes. `VOZ_CLIMAS=0` desliga. O clima sobrepõe o rodízio de base (francisca/kokoro/misto).
- Teste de ponta a ponta (`preparar_clone` real, mike v2, 9 frases, 8 climas): todas com voz (-21 a -30 dBFS).
- Pendente: levar pro hipercool/histórias/manhwa-react pelo COMUM; formante por clima (só no protótipo).

### F8 — plano de integração (depois do dono aprovar as doses)
1. `comum\narracao_curva.py`: CLIMAS (doses aprovadas) + `escolher_climas()` (junto dos impactos, com cache e
   reserva) + o clima entra em pausa/respiração/eco/EQ do `humanizar`. Sobe pros projetos com `recursos.py subir`.
2. `bin\voz_clonada.py lote`: aceitar "formante" por frase e tom-alvo relativo à voz natural (tabela de bases medida
   com RMVPE — hoje a calibração usa pyin e só conhece Francisca/Kokoro/Andrew).
3. recapd `anime_tts.preparar_clone`: `base_da_frase` vira "base do clima" (o misto é o caso de 2 climas) e cada
   frase leva velocidade/tom/entonação/volume/pausa do clima. Primeiro nos Shorts de parceiro (onde o clone roda).
4. hipercool (`elenco.py`/`narration.py`), historias-em-frames, manhwa-react: mesma paleta pelo COMUM (sem clone =
   só velocidade/tom/contorno/volume/pausa/EQ do edge).
5. Tempo de produção: igual (o RVC converte a mesma duração de áudio; a escolha do clima vai na chamada que já existe).
