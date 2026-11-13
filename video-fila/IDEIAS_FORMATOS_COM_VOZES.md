# Formatos com vozes clonadas — ideias aprovadas e para depois (dono, 23/10/2026)

Origem: a dupla João Grilo + Chicó ficou "muito boa" e o dono pediu ideias além de "o personagem conta a história
como se fosse ele". A graça está na RELAÇÃO entre as vozes (um mente, o outro desmascara), não em cada voz sozinha.
Motor de teste: `D:\hipercool-materiais\bin\formatos_voz.py` (roteiro com quem fala cada frase -> voz por frase ->
microcortes). Amostras em `D:\hipercool-materiais\amostras_voz\formatos\`. Nada disso está na produção ainda: cada
formato é testado e só vai pros Shorts depois que o dono aprovar a amostra.

## Aprovados para testar (fazer agora)
| Formato | Como é | Vozes |
|---|---|---|
| Duplas do Chaves (todas as combinações, e trios) | Chaves conta errado, Quico se gaba ("gentalha!"), Chiquinha "pois é, pois é" | chaves_chapolin, quico, chiquinha, seu_madruga (Dona Florinda foi reprovada — só se a dona pedir de novo) |
| João Grilo + Chicó | Chicó exagera, João desmascara ("Não sei, só sei que foi assim") | joao_grilo, chico_selton |
| Transmissão esportiva | Galvão narra o resumo como se fosse um jogo, com comentarista | galvao_bueno + professor_girafales |
| Show do Milhão | Silvio para no gancho e pergunta ao público o que vai acontecer | silvio_santos |
| Jornal | Cid abre com "Boa noite" e dá a reviravolta como plantão | cid_moreira (+ repórter) |
| Videocassetadas | Faustão comenta as falhas do vilão: "Errou!", "Ô loco, meu!" | faustao |
| Escolinha | Girafales dá aula sobre a história, a turma responde errado | professor_girafales + chaves_chapolin, quico, chiquinha |
| Tribunal | João Grilo defende, Chicó testemunha (mente), Girafales julga | joao_grilo, chico_selton, professor_girafales |
| Participação especial | uma frase de outra voz no clímax ("É tetra!", "Errou!"); pode usar o ÁUDIO ORIGINAL quando o bordão é muito característico (como já faz `trechos_icones`) — bom pra meme | qualquer aprovada |
| Encerramento assinado | todo vídeo de uma série fecha com a mesma voz (Cid: "Boa noite.") | qualquer aprovada |
| Interrupção | uma voz corta o narrador ("Ei! Ei! Isso não é justo!") | pato_donald e outras |
| Batalha de narradores | cada um conta metade; o público vota nos comentários | 2 narradores + Silvio pedindo o voto |
| Fofoca | dois personagens comentando a história como fofoca da vila | chiquinha + quico (e outras duplas) |

Regra do dono pro sotaque (João Grilo/Chicó): as PALAVRAS têm que ser de sertanejo ("cabra", "home", "oxe", "num",
"abestado", "vixe", "arretado"), não corretas demais; a voz/tom da v2 era a melhor.

## Veredito da dona nas amostras (23/10)
- **Aprovados pra produção:** Show do Milhão, Chaves + Quico, trio do Chaves, Escolinha, Fofoca, Seu Madruga + Chaves,
  participação especial/interrupção (cameo_interrupcao) — este SEM o "Boa noite" no fim —, transmissão SÓ com o Galvão,
  João Grilo + Chicó (a dupla v4 escrita à mão é a referência; o roteiro da IA ficou pior).
- **Videocassetadas:** quase o PADRÃO do Faustão.
- **Só caso específico:** batalha de narradores (mais pra vídeo longo; trocar o narrador no meio pode, depende do vídeo) e tribunal.
- **Reprovado:** jornal (com essas vozes). Chaves + Chiquinha ainda sem veredito.
- **Regras gerais:** (1) falar como o personagem NÃO é usar todos os jargões — UM bordão basta pra identificar (o Mestre
  Kame pode só se apresentar "Mestre Kame"); nos trios do Chaves cada um falou todas as frases dele e o foco saiu da
  história pro narrador. (2) Short é LOOP: nada de despedida no fim; a última fala emenda na primeira.
- **Próximo passo pedido:** sistema de TESTES nos vídeos reais, devagar, com o VIGIA avaliando; quem for bem (personagem,
  modelo, formato) aparece mais vezes. **Feito em 23/10** — ver abaixo.

## Sistema de testes nos Shorts reais (23/10)
- **Quanto:** 15% dos Shorts de parceiro que já sairiam com voz clonada (~3-5 por dia); 2/3 deles em formato, 1/3 com
  uma voz nova sozinha (personagem aprovado que quase nunca saía no rodízio; pessoa real fica fora). Os outros 85% são
  o controle ("solo"). Config: `D:\recapd-ambientes\producao\config\testes_voz.json` (`ligado`, `fracao`, `pausados`).
- **Quem sai:** sorteio que favorece quem já rendeu (views em 48 h acima da mediana do canal, o mesmo critério do funil).
  Com 5 vídeos medidos: acima do solo + 0,1 = PROMOVIDO (ganha +15% dos Shorts, aparece mais vezes); abaixo do solo
  − 0,1 = PAUSADO.
- **Qualidade:** todo Short em teste é transcrito pronto e comparado com o roteiro (amostras aprovadas dão 0,90-1,00;
  Shorts reais com música 0,90-0,99). Menos de 60%, "circunflexo" ou erro da IA narrado = ruim: formato é refeito no
  solo, voz nova fica segurada (não sobe). 2 ruins = pausado.
- **Vigia:** `D:\video-fila\avaliar_testes_voz.py` a cada 3 h (dentro do vigia geral) escreve
  `D:\video-fila\TESTES_VOZ_RELATORIO.md` e avisa no Telegram quando alguém é promovido ou pausado (+ 1 resumo por dia).
- **Pessoa real** no elenco (Silvio, Faustão, Galvão, Cid...) = o upload marca "conteúdo alterado ou sintético".
- **Fora do teste:** batalha e tribunal (só caso específico), jornal (reprovado), Chaves + Chiquinha (sem veredito), Nappa
  (só com o Vegeta).
- O 1º veredito por item leva umas 2-3 semanas (cada item sai 1 vez a cada 2-3 dias, a medida vem 48-96 h depois de
  publicar e os Shorts saem agendados até 7 dias à frente).

## Para depois (documentado, não fazer agora)
1. **Dublagem dos personagens da cena** (cada personagem do anime fala com uma voz: protagonista = Goku, vilão = Vegeta).
   Só funciona onde já existe fala por personagem: o **hipercool** (vozes por balão, `bin/elenco.py`). Ideia maior do
   dono: um **projeto novo de histórias de mangá/manhwa criadas por nós**, juntando o hipercool (painéis, elenco de
   vozes por personagem, efeitos, censura) com o historias-em-frames (imagens geradas por IA, roteiro próprio). A
   história é nossa, então dá pra dublar cada personagem com uma voz aprovada. Colocar no disco D (hoje com ~4 GB
   livres — liberar espaço antes).
2. **Remake de vídeo que fez sucesso** (no lugar de "mesmo vídeo, duas versões", que pode dar problema no YouTube por
   conteúdo repetido): pegar um vídeo nosso com muitas visualizações e refazer com efeitos diferentes, nomes
   diferentes e outra narração/outra voz; comparar os números das duas versões.

## Cuidados
- Silvio, Faustão, Galvão e Cid são pessoas reais: marcar o vídeo como "conteúdo alterado ou sintético" no YouTube e
  deixar claro que é paródia. Personagem de desenho tem risco menor. Políticos ficam fora (regra do Lula/Bolsonaro).
- Microcortes valem em todos (pausa > 0,07 s sai, a fala não acelera).
