# Humor: o que o Virjão e a Momo fazem e os nossos longos ainda não (26/11)

Pedido da dona: "analise o que mais poderíamos adicionar que ficasse engraçado — elementos dos vídeos do Virjão ou
Momo que ainda não tem". Só análise; nada implantado.

## Como foi medido
- Fala REAL: transcrição (Whisper, com tempo) dos vídeos baixados na coleta de 21/11:
  `C:\Users\Haylla\Desktop\coleta_narradores\_pedacos\{kkvirjao,momo,mike}\*\*.json` (Virjão 22,6 mil palavras,
  Momo 22,4 mil, Mike 204 mil) + trechos separados por tipo em `...\separado\<narrador>\<tipo>\*.txt`.
- NOSSO: `roteiro.txt` dos longos prontos em `D:\hipercool-materiais\animes recap\na_nuvem\` (Momo: 48,7 mil palavras;
  outros 6 longos: 348 mil). Script: `D:\tmp\compara_humor.py`.
- Limite: só ÁUDIO dos vídeos deles foi baixado; elementos VISUAIS (zoom, texto na tela, corte) não foram medidos.

## Números (ocorrências a cada 1000 palavras)
| recurso | Virjão | Momo | Mike | NOSSO Momo | NOSSO outros |
|---|---|---|---|---|---|
| narrador em 1ª pessoa (eu/nem eu/até eu) | 8,6 | 13,7 | 20,5 | 0,2 | 0,2 |
| pergunta (?) | 11,4 | 17,7 | 13,5 | 1,2 | 1,1 |
| interjeição (nossa/rapaz/eita/caramba/pô) | 4,0 | 9,2 | 7,1 | 0,7 | 1,1 |
| fala com o público (rapaziada/fi/vocês/mano) | 6,0 | 3,7 | 4,0 | 1,3 | 1,0 |
| exclamação (!) | 3,9 | 1,6 | 5,0 | **0,0** | **0,0** |
| reticência (pausa/fala arrastada) | 2,3 | 5,0 | 2,3 | **0,0** | **0,0** |
| marcador de conversa (né/tá ligado/tipo) | 5,8 | 4,0 | 1,6 | 1,6 | 1,8 |
| onomatopeia de golpe (tijolada/pá/lapada) | 0,9 | 0,1 | 0,1 | 0,5 | 0,1 |
| palavras por frase | 9,3 | 9,7 | 10,2 | 15,4 | 15,3 |
| "nosso garoto/prota" | 0,0 | 0,8 | 0,2 | **7,7** | 3,4 |
Top do Virjão: rapaziada (74), meu compadre (22), rapaz, pô, véi. Top da Momo: nossa (65), rapaz (57), fi (35),
caramba (32), eita (24). Apelidos por traço que se repetem: o Lourinho (18x), o Cedrinho, o Bichão, o Bodão, a Mãozinha.

## O que falta (ordem de impacto)
1. **Narrador REAGINDO ao vivo, em 1ª pessoa** (0,2 x 9-14/mil). Eles param e reagem: "Isso aqui não é possível não,
   cara", "Nem eu entendi", "Até eu ia ficar com medo". O nosso conta a história na 3ª pessoa o tempo todo.
2. **Perguntas e eco incrédulo** (1 x 11-18/mil). A Momo repete o absurdo em pergunta: "Pera aí, 1 metro por hora?",
   "Cadê esse cara aí?". O molde `sera_que_esse_cara` existe no repertório, mas quase não sai.
3. **Interjeição na hora** (1 x 4-9/mil): "Nossa", "Eita", "Caramba", "Rapaz" grudados no fato, não frase solta.
4. **Frases mais curtas** (15 x 9-10 palavras). A piada precisa de frase curta pra ter tempo de efeito.
5. **Exclamação e reticência = zero.** O texto pronto não tem NENHUM "!" nem "...". (a) A voz sai sem energia;
   (b) PROVÁVEL efeito em cadeia: `anime_segments.py:909` usa frase terminada em "!"/"?" para decidir onde entra a
   REAÇÃO REAL gravada do narrador — sem "!", entram menos reações reais. Conferir se o "!" some na geração ou num
   filtro depois (não achei regra que remova).
6. **Comentários repetidos e de fórmula.** Num mesmo longo: "Sinceramente, esse cara não aprende, né?" 3 vezes;
   "Sinceramente," abre quase todo comentário. Falta trava de não repetir frase no vídeo.
7. **A piada de virada ("Mentiraaa, galera!") não saiu NENHUMA vez** em 2 longos da Momo, apesar de pedida no prompt
   (`anime_script._COMENTARIO_NARRADOR`). Falta conferir depois de gerar e refazer o trecho que não tiver.
8. **Piada recorrente com escalada** (não existe nada parecido): a Momo repete "a sanidade do coitado caiu pra 10" e
   vai baixando o número. Ideia: 1 piada fixa por vídeo (contador de sanidade, "mais uma pra conta do coitado",
   placar de vergonhas) que volta 3 a 5 vezes, piorando.
9. **Imitação caricata do personagem** pelo narrador (Virjão "Seu giiii", Momo: a tartaruga "Eu... Sou..."). Já há a
   sub-voz `_agudo`; falta o roteiro MARCAR essas falas (com reticência/alongamento) para ela ser usada.
10. **"Nosso garoto" demais** (7,7/mil, ~1 a cada 130 palavras). Eles usam apelido por TRAÇO e variam
    (o Lourinho, o Bichão, o Bobão, a Mãozinha) — o nosso repete a mesma muleta.
11. Onomatopeia de golpe na luta ("tijolada!", "pá!", "lapada") — molde `da_lhe_golpe` existe, sai pouco.

## O que NÃO aumentar (regra da dona)
- Palavrão: Virjão usa 10/mil, mas a regra é "no máximo o que ele usa, na dúvida menos", e a postagem reprova
  palavrão na narração. Não mexer.
- Bordão: regra de 23/10 = no máximo 1 bordão por vídeo. "Rapaziada" como vocativo pode contar como bordão: a dona decide.

## Próximo passo sugerido
Itens 5, 6 e 7 são conserto (o pedido já existe e não está saindo); 1, 2, 3, 8 e 10 são regras novas no prompt do
roteiro (`anime_script.py`), cada uma com chave para desligar, testando em 1 trecho antes de valer.
