# Estratégia de mistura de motores de voz — Shorts e longos (17/11/2026)

Pedido da dona: "a melhor estratégia possível de mistura dos motores pra longos e curtos parecerem o máximo humanos".
Base: estudo da GPU do Kaggle (`amostras_voz\estudo_motores_kaggle_1711\final\RELATORIO.md`, 21 vozes, 8 cenas + Short
de 10 falas) + uma medição nova, feita no STI com os mesmos áudios: **quanto a voz muda quando a frase seguinte vem de
OUTRO motor, já com o clone do Julius por cima** (`salto_motores.py`; resultado em
`D:\tmp\t_pesq\salto\` e no STI `~/teste_remoto/salto_saida.txt`).

## 1. O que o relatório do estudo mostra — e o que ele não mediu

1. **A "mistura" do estudo não misturou motores.** As duas versões ("melhor por momento" e "só rápidos") saíram
   10 de 10 falas em Supertonic F1/F2 (seção 4, coluna "Motores = 1"). Então a tabela "sozinho x misturado" não
   responde se a mistura soa mais humana: ela compara Supertonic com Supertonic.
2. **O ranking geral contradiz a medida de naturalidade.** Kitten 2 é 1º no geral (posição média) mas ÚLTIMO em
   naturalidade (2,69–2,78 contra 4,0–4,2 do Supertonic). O geral dá o mesmo peso a 8 pontos, e 4 deles quase não
   separam ninguém (acerto 0,98–0,99 em todos; pausas 0 em quase todos; estabilidade −0,02/−0,03 em todos). O Kitten
   ganha por semelhança com o Julius (0,74) — o que o RVC por cima já faz para todos.
3. **Depois do clone, as notas se achatam.** Com o RVC do Julius por cima, a naturalidade de TODOS cai para 2,2–2,6
   (era 2,7–4,2). A diferença entre o melhor e o pior motor encolhe de 1,5 para 0,4 ponto. O que a dona ouve no vídeo
   final é a versão clonada — e nela a escolha do motor importa bem menos do que a tabela sem clone sugere.
4. **O RVC piora a voz que o estudo achou mais natural.** Supertonic F1 cai de 4,19 para 2,51 com o clone. Isso diz que
   o gargalo da "voz humana" hoje é o clone, não a base.

## 2. A medida que faltava: salto entre motores, com o clone por cima

Salto normal de uma fala para a seguinte DENTRO do mesmo motor = 1,0x (referência). Troca de motor:

| Troca | Timbre | Diferença de tom | Diferença de volume |
|---|---|---|---|
| Kokoro ↔ Piper | 1,05x | 0,6 st | 0,7 dB |
| Kitten 2 ↔ Kokoro | 1,06x | 1,0 st | 1,2 dB |
| Edge ↔ Piper | 1,11x | 0,7 st | 1,0 dB |
| Edge ↔ Kokoro | 1,15x | 0,8 st | 0,8 dB |
| Kitten 2 ↔ Piper | 1,18x | 1,2 st | 1,2 dB |
| Edge ↔ Supertonic | 1,22x | 2,7 st | 2,4 dB |
| Edge ↔ Kitten 2 | 1,27x | 1,4 st | 1,9 dB |
| Piper ↔ Supertonic | 1,31x | 2,4 st | 3,1 dB |
| Kokoro ↔ Supertonic | 1,48x | 2,3 st | 3,0 dB |
| Kitten 2 ↔ Supertonic | 1,48x | 2,2 st | 4,2 dB |

Leitura:
- **Edge, Kokoro, Piper e Kitten 2 formam um grupo que emenda bem**: depois do clone, trocar entre eles muda a voz
  quase só o que ela já muda de uma frase para outra (1,05–1,27x), com até ~1 st e ~1 dB de diferença.
- **O Supertonic é o que mais destoa**: sai ~2–3 dB mais baixo e ~2 st mais agudo que os outros (o M1 sai 9 st acima),
  e o timbre salta 1,2–1,5x. Ele só entra na mistura com o volume e o tom IGUALADOS antes do RVC (e mesmo assim falta
  ouvir), ou fica para os Shorts em que ele é a voz do vídeo inteiro.
- Diferença de volume se corrige de graça (loudnorm por frase). Diferença de tom se corrige com o `tom` do RVC por
  base (o produção já tem `tom_fixo` por voz e base). O timbre é o que sobra — e é aí que os pares acima mandam.

## 3. A estratégia

### Princípio
O que soa máquina não é uma base sozinha, é a REPETIÇÃO: mesma entonação, mesmo ritmo, minutos seguidos. Um narrador
humano muda o jeito de falar com a CENA, não a cada frase. Então:
- trocar de base nas **viradas de cena** (pausa, mudança de assunto, depois de impacto), nunca no meio de uma ideia;
- nunca deixar a mesma base mais de ~40–60 s seguidos;
- emendar só pares que o ouvido não pega (seção 2) e igualar volume e tom na troca;
- cada base no tipo de trecho em que ela é melhor.

### Papéis (com o clone por cima)
| Base | Papel | Por quê |
|---|---|---|
| **Kokoro** (pm_alex / pf_dora) | narração de ação e subida para o clímax | mais viva; emenda bem com Piper, Edge e Kitten |
| **Edge Francisca** | narração calma, explicação, nomes | melhor pronúncia; emenda bem com Kokoro e Piper |
| **Piper cadu** | 3ª voz de narração, revezando com as duas | a que emenda mais suave com todas (1,0–1,1x); é a mais rápida |
| **Kitten 2** (calmo / bem solto) | gancho, frase de impacto, fala de personagem | maior semelhança com o original e mais expressivo; caro (~35 s para abrir + ~5 s por fala na GPU) |
| **Supertonic** (F1/F2) | Short inteiro quando for a voz única do vídeo; fora da mistura até ouvir o teste com volume e tom igualados | o mais natural SEM clone; o que mais destoa COM clone |

### Shorts (4–10 frases, ~20–70 s)
- Uma base de narração por Short, sorteada por vídeo entre Kokoro / Francisca / Piper (o padrão some ENTRE vídeos, que
  é o que o público vê em sequência). Dentro do Short, no máximo **uma** troca, na virada da história.
- **Gancho (1ª frase) em Kitten 2 quando houver GPU** (Kaggle de curto vivo): custa ~40 s a mais por Short. Sem GPU,
  gancho na base do vídeo com a curva de clímax mais forte.
- Custo: igual ao de hoje (± 15%) sem Kitten; +~40 s com Kitten na GPU.

### Longos (150–1.000 frases)
- Revezar **Kokoro, Francisca e Piper** por cena: troca na virada de cena, com **teto de 45 s** na mesma base e nunca
  em rodízio fixo (escolha da próxima base fixa por hash do texto, como o `narracao_curva` já faz — refazer dá o
  mesmo áudio).
- **Kitten 2 no gancho, nos impactos e nas falas de personagem**, com teto de 60–90 s de fala por vídeo e o modelo
  carregado UMA vez por vídeo (a carga é 35 s; a fala, ~5 s).
- Na troca: **loudnorm por frase** para o mesmo alvo e o `tom` do RVC por base, para a diferença de volume e tom
  ficar abaixo de ~1 dB e ~1 st.
- Custo (simulado em `custo_mix.py`): ~+7% com o revezamento; ~+20–30% com o Kitten 2 no teto.

## 4. O que falta para implantar (na ordem)

1. **Teste de ouvido da emenda** (o único que decide): o mesmo trecho corrido de 60–90 s de um longo real, com o clone
   do Julius, em 3 versões — (a) só Francisca, (b) revezamento Kokoro/Francisca/Piper com teto de 45 s e loudnorm,
   (c) = (b) + Kitten 2 no gancho e em 1 impacto. A dona ouve sem saber qual é qual.
2. **Supertonic igualado**: o mesmo trecho com o Supertonic entrando na roda, com volume e tom igualados antes do RVC.
   Se ninguém notar a troca, ele entra na mistura; se notar, fica só como voz única de Short.
3. **Melhorar o clone** rende mais que trocar a base: todas caem para 2,2–2,6 de naturalidade depois do RVC. Vale um
   teste do `index_rate`/`protect` mais baixos (menos timbre forçado, mais da prosódia da base).
4. Implantar em `anime_tts.base_da_frase` (Shorts e longos usam a mesma função) com chaves de desligar, e ligar a
   base "misto" por padrão em `colab\cliente.py:_voz_do_longo` e `anime_voz_clonada.proxima`.

## 5. Ressalvas

- O "salto" é medido por números (timbre MFCC, tom, volume, brilho), sobre 10 falas por motor de um único Short e um
  único clone (Julius). Diz quais pares têm MAIS chance de emendar; quem decide é a dona ouvindo.
- Naturalidade é o UTMOS, um modelo treinado majoritariamente em inglês: serve para comparar, não é nota de ouvido.
- Tempos do estudo são da GPU do Kaggle; no desktop sem GPU o Kitten 2 leva ~30 min por frase.
