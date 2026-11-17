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

## 5. O que eu NÃO fiz

Não mexi em `anime_tts.py`, `anime_voz_clonada.py` nem em `colab\cliente.py` — você está trabalhando neles. Os itens
da seção 2 ficam para você aplicar junto com o motor novo, ou me avise que eu implemento o teto por base (item 2) e o
loudnorm por frase (item 4), que são independentes do motor escolhido.
