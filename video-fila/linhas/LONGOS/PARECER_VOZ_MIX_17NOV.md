# Parecer: como encaixar os motores de voz nos longos (chat CURTOS/máquinas, 17/11)

Para o chat que está fazendo o estudo dos motores (`D:\tmp\estudo_motores.py`, saída `D:\estudo_motores\`).
Pedido da dona: "a mesma voz, só que mudando como se fosse a humana — qualquer uma que a gente mantiver sozinha num
vídeo dá pra perceber o padrão". Ela pediu meu parecer de manhã e que eu instruísse os testes.

## 1. O que eu medi na produção (antes de escolher motor)

- **A mistura quase não roda.** Dos últimos 400 vídeos com voz clonada: 241 só Kokoro, 153 só Francisca, **6 em modo
  misto**. Quem decide é `anime_voz_clonada.proxima()` (sorteia a base por voz); os longos herdam isso em
  `colab\cliente.py:_voz_do_longo`.
- **Mesmo no misto, uma base domina.** Simulei `anime_tts.base_da_frase` num roteiro longo real (972 frases, 81 min de
  fala, 49 impactos): Francisca 86% da fala, Kokoro 14%; **maior trecho seguido de Francisca: 33,7 min**.
  Script: `D:\tmp\t_pesq\simula_mix.py <pasta do vídeo>` (não chama IA; reaproveite para testar regras novas).
- **Trocar só o gancho e os picos não resolve o padrão.** Pôr um motor novo no gancho + impactos dá 50 frases, ~4,5 min
  dos 81. Os 33,7 min seguidos continuam.
- **A etapa cara é o RVC, não a base.** No seu teste: base 3–20 s (edge/Kokoro) e RVC 43–86 s por frase. Com o PC1
  cheio, medi 3 frases de RVC em 52 min. Qualquer motor de base que custe minutos por frase (Kitten 2: 30 min; Qwen3:
  9 min; Chatterbox: 6–13 min) só cabe em POUCAS frases por vídeo.

## 2. O que eu recomendo (ordem de implantação)

1. **Ligar a mistura em todo longo** (base "misto" fixa em `_voz_do_longo`), sem depender do sorteio. É de graça: só
   edge + Kokoro, que já são rápidos.
2. **Teto de tempo seguido por base** em `base_da_frase`: passou de ~40–60 s na mesma base, troca na próxima pausa
   natural (fim de frase longa, mudança de cena, depois de impacto). Trocar por PAUSA + TEMPO, nunca em rodízio fixo
   (rodízio vira padrão também). A troca precisa ser fixa por vídeo (hash do texto, como o `narracao_curva` já faz),
   para refazer dar o mesmo áudio.
3. **Motor expressivo (o que a dona escolher) só onde paga o custo:** gancho, frase de impacto e falas de personagem
   (`anime-pipeline._falas_personagem`). Com teto por vídeo em SEGUNDOS de fala (ex.: 60–90 s), para o tempo de
   geração ser previsível.
4. **Igualar volume e brilho entre bases DEPOIS do RVC**, por frase (loudnorm para o mesmo alvo). Sem isso a troca de
   base vira um degrau que se ouve — pior que o padrão que se queria tirar.
5. **RVC fora do PC1** (regra da dona de 15/11: PC1 livre). Rodar a conversão no desktop/Kaggle e nunca 2+ juntas na
   mesma máquina sem GPU.

## 3. O que falta testar (é isto que eu peço)

O estudo da noite mede cada motor SOZINHO, sem RVC, por cena. Isso responde "qual motor para qual cena". Faltam os
testes que respondem "a mistura funciona?":

**Teste A — emenda entre bases (o mais importante).**
Um trecho corrido de 60–90 s (10–12 frases seguidas de um roteiro real, não frases soltas), gerado em 4 versões, TODAS
com o mesmo RVC por cima e o mesmo loudnorm no fim:
  1. só Francisca; 2. só Kokoro; 3. misto de hoje; 4. misto novo (troca a cada 2–4 frases entre Francisca, Kokoro e
  Supertonic — os três rápidos).
A dona ouve as 4 sem saber qual é qual. Pergunta única: "em qual você NÃO percebe que é máquina?". Se a 4 tiver
degrau audível na troca, a ideia precisa do item 4 acima antes de ir para produção.

**Teste B — o motor expressivo no lugar certo.**
O mesmo trecho da versão 4, trocando SÓ o gancho e 1 frase de impacto pelo motor que a dona escolher (Kitten 2 /
Qwen3 / Chatterbox pt-BR). Ouvir se ele "cola" no resto depois do RVC ou se parece outra pessoa.

**Teste C — custo real por longo.**
Com a regra escolhida, rodar `simula_mix.py` em 3 roteiros longos reais e somar: segundos de fala por base × tempo por
segundo de cada motor (do seu RELATORIO.md) + RVC. Dá o tempo de voz de um longo inteiro ANTES de implantar.
Meta que eu proporia à dona: a voz não passar de +20% do tempo de hoje.

**Teste D — Supertonic como 3ª base.**
A dona aprovou o Supertonic (fala certo, 47 s, voz pronta). Como o RVC põe o timbre por cima, "não clonar o jeito" não
é defeito para base de narração. Conferir só: sotaque pt-BR depois do RVC e se as tags `<laugh>`/`<breath>`/`<sigh>`
sobrevivem ao RVC.

## 4. Cuidados ao medir

- **Acerto pelo Whisper tem um furo:** o Qwen3 acrescentou "Amor," — isso veio do TEXTO DE REFERÊNCIA (`REF_TXT`
  termina em "…amor."). É vazamento da referência, não erro de leitura; some trocando o trecho de referência por um
  que termine em frase neutra. Vale conferir o mesmo no Chatterbox ("troca uma palavra").
- **Kitten 2 foi medido com `backend="torch"` em CPU de 2 núcleos** (30 min). O card dele cita um caminho C++
  (`kitten-tts-2-cpp`, pesos 1.58-bit) e `backend="vllm"` na GPU. Antes de descartar por lentidão, vale 1 medição no
  caminho C++ no desktop — se cair para poucos minutos, muda o ranking. Não testei: é hipótese.
- **Expressividade medida ≠ soar bem** (você já anotou isso). No teste A o juiz é o ouvido da dona.
- Tudo no desktop ou no Kaggle, nunca no PC1 (`python D:\video-fila\teste_remoto.py --tipo pesado -- <comando>`).

## 4b. Conta dos tempos — Shorts E longos (pedido da dona 17/11: "aplicar nos dois, levando em conta o tempo de cada motor")

Calculadora: `python D:\tmp\t_pesq\custo_mix.py <pasta com roteiro.txt>` (edite `CUSTO` quando o estudo fechar).
Tempos usados (segundos de máquina por segundo de áudio, DESKTOP sem GPU): Francisca 0,3 · Piper 0,6 · Supertonic 0,7 ·
Kokoro 2,6 · Chatterbox 32 (melhor caso; o "normal" deu 75) · Qwen3 55 · Kitten 2 178 · RVC 7 (em toda frase).

| Regra | Short típico (4 frases, 21 s) | Short grande (9 frases, 40 s) | Longo (152 frases, 9 min) | Maior trecho na mesma base (longo) |
|---|---|---|---|---|
| Hoje: só Francisca | 2,5 min | 4,9 min | 64 min | 527 s |
| Hoje: só Kokoro | 3,3 min (1,3x) | 6,4 min (1,3x) | 84 min (1,3x) | 527 s |
| **A. mistura rápida** (Francisca+Kokoro+Supertonic, troca a cada ~45 s) | 2,9 min (1,2x) | 5,6 min (1,2x) | 69 min (1,07x) | **48 s** |
| B. A + Chatterbox no gancho/impactos (teto 60 s de fala) | 8,8 min (3,5x) | 13,3 min (2,7x) | 85 min (1,3x) | 47 s |
| C. A + Qwen3 no gancho/impactos | 13,2 min (5,2x) | 19,1 min (3,9x) | 97 min (1,5x) | 47 s |
| D. A + Kitten 2 no gancho/impactos | 36,6 min (14x) | 50,1 min (10x) | 163 min (2,5x) | 47 s |
| E. A + Kitten 2 só no gancho (1 frase) | 22,9 min (9x) | 25,3 min (5,2x) | 78 min (1,2x) | 48 s |

Leitura:
- **A regra A é a que tira o padrão quase de graça**, nos dois formatos: +7% no longo, +15% no Short, e o maior trecho
  na mesma base cai de 527 s para 48 s. É mais BARATA que usar só Kokoro, que já é o caso de 60% dos vídeos hoje.
- **Motor caro num Short não fecha a conta sem GPU**: o Short tem 4 frases, então o gancho + 1 impacto já é metade do
  vídeo (55%). B triplica o tempo de voz; D multiplica por 14. No Short a mistura deve ser só a A.
- **No longo o motor caro cabe**, porque gancho + impactos são ~6% da fala: B custa +32% (igual a "só Kokoro" de hoje),
  E (Kitten 2 em 1 frase) +21%. C e D passam do que eu proporia.
- **O RVC é 90% do tempo em qualquer regra** (61 de 64 min no longo). Acelerar ou tirar o RVC do caminho rende mais
  que qualquer troca de base: GPU do Kaggle, ou RVC em lote numa máquina sem disputa.
- Ressalvas: tempos do desktop de 2 núcleos; na GPU os clones caem muito (falta medir). O "Short típico" é um texto
  modelo com o tamanho mediano medido em 87 Shorts de 14–16/11. O longo é o maior roteiro disponível hoje na pasta de
  trabalho (9 min); um de 80 min escala igual. A regra da calculadora é um rascunho da lógica, não o código final.

Proposta para a dona decidir de manhã:
- **Shorts:** regra A sempre. Motor expressivo só quando houver GPU de curto no Kaggle.
- **Longos:** regra A + motor expressivo no gancho e nos impactos com teto de 60 s de fala (B se ela preferir o
  Chatterbox; E se preferir o Kitten 2, limitado a 1–2 frases).

## 5. O que eu NÃO fiz

Não mexi em `anime_tts.py`, `anime_voz_clonada.py` nem em `colab\cliente.py` — você está trabalhando neles. Os itens
da seção 2 ficam para você aplicar junto com o motor novo, ou me avise que eu implemento o teto por base (item 2) e o
loudnorm por frase (item 4), que são independentes do motor escolhido.
