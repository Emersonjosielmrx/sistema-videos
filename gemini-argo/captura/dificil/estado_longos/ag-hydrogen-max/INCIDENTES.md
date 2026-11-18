# Incidentes reais com o estado dos longos (longos_postados.json) — todos depois do conserto de 03/11

Formato do estado: {"postados": [{"nome", "url", "titulo", "canal"}], "reprovados": [nomes],
"cortes_postados": [nomes], "presos": {nome: {"status": "enviando"|"erro", ...}}, "presos_soltar": [nomes]}.
Várias rodadas rodam juntas; cada uma lê no começo e grava (com _gravar_estado) quando termina um envio, horas depois.

1. 13/11 20h45 — Parte 4 do Medieval VOLTOU a "reprovada" sozinha. Ela estava reprovada por palavrão; o
   bipar_palavrao.py bipou o áudio, criou fichas/<nome>/SEM_PALAVRAO.txt e tirou o nome dos "reprovados" no arquivo.
   A rodada que já estava rodando (leu antes, com ela reprovada) gravou no fim e ela voltou pra lista. Regra: ficha
   com SEM_PALAVRAO.txt está liberada e nunca pode ficar em "reprovados".
2. 14/11 — "presos" (longo cujo envio travou/está em andamento) sumiam: a rodada antiga gravava o "presos" que tinha
   lido de manhã por cima do que outra rodada marcou depois. Preso marcado por qualquer rodada não pode sumir por isso.
3. 14/11 15h20 — Título do jardineiro: o título real "Por que a academia inteira tremeu..." foi corrigido à mão no
   arquivo (antes era a nota "(reposto 03/11 do uploads_ledger...)"). A rodada que já estava rodando gravou e o
   título voltou a ser a nota. Título que começa com "(" é NOTA provisória: perde para um título de verdade do
   arquivo para o mesmo url. Título de verdade novo (da rodada) continua valendo.
4. 16/11 — Era preciso SOLTAR um preso de propósito quando o envio dele terminou (marca "enviando" que ficou para
   trás). Como "presos" nunca pode sumir (item 2), a rodada põe o nome em est["presos_soltar"]; ao gravar, cada
   nome de presos_soltar (da rodada ou do arquivo) sai de "presos" SÓ se lá o status for "enviando" (preso com
   "erro" nunca é solto por aqui). "presos_soltar" não fica gravado no arquivo depois de aplicado.

Tudo do conserto de 03/11 continua valendo: postado/reprovado/corte que existe no arquivo nunca se perde, e postado
não duplica (mesmo nome+url).
