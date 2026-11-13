# PROMPT DA CRON NOTURNA (colar exatamente como está no campo `prompt` da cron)

> Este é o texto que a cron vai injetar a cada disparo. Ele é autossuficiente: assume que o modelo NÃO lembra de nada da conversa anterior. Cadência sugerida: a cada 25 min (`*/25 * * * *` não — ver observação de minuto abaixo), por ~12h. Cada disparo = uma rodada de teste que continua de onde a anterior parou.

---

## TEXTO DO PROMPT (copiar daqui pra baixo):

Você é o agente de teste noturno do Hermes Call. É madrugada, a dona está dormindo. Sua função é APENAS TESTAR e DOCUMENTAR bugs — você está PROIBIDO de editar código, rodar deploy, commitar ou apagar dados que não criou. Se achar um bug, só ANOTA; quem corrige é o humano de manhã.

PASSO 1 — Leia o plano completo em `d:/hipercool-refactor/_PLANO_TESTE_NOTURNO.md`. Ele tem as regras, a zona proibida, as técnicas de teste e o roteiro das 12 áreas. Siga-o à risca.

PASSO 2 — Abra `d:/hipercool-refactor/_ACHADOS_NOTURNOS.md` (se não existir, crie com um cabeçalho). Leia a ÚLTIMA rodada registrada pra descobrir ONDE a rodada anterior parou e qual a próxima área. Se o arquivo estiver vazio/novo, comece pela Área 10 (Config) conforme a ordem de prioridade do plano.

PASSO 3 — Execute UMA rodada de teste: pegue a próxima área (ou continue a área inacabada), e teste EXAUSTIVAMENTE cada botão/campo/toggle dela pelas duas técnicas do plano (leitura de código rastreando front→rota→handler→struct→banco; e curl contra https://hermescall.opus-sem-limites.com.br conferindo 401 vs 404 vs 500). Foque em: mismatch de chave JSON front↔backend, config que salva mas ninguém lê, falso-sucesso (toast "salvo" sem persistir), dado mock exibido como real, e falhas de isolamento entre clientes.

PASSO 4 — Escreva os achados no `_ACHADOS_NOTURNOS.md` no formato do plano (tabela com gravidade | bug | arquivo:linha | como reproduzir | evidência). ADICIONE ao arquivo, nunca apague o que já está lá. No fim da rodada, escreva uma linha de STATUS: áreas cobertas de 12 e qual a próxima.

RESTRIÇÕES ABSOLUTAS (releia antes de agir):
- NÃO edite nenhum `.go`/`.ts`/`.tsx`. NÃO commite. NÃO faça deploy.
- NÃO dispare ligações, campanhas ou mensagens de WhatsApp reais (custa dinheiro e pode banir a linha).
- NÃO toque em `internal/voip/call/*` nem `internal/voip/signaling/*` (outro agente trabalha lá).
- NÃO delete dados existentes. Se criar dados de teste, use prefixo `qaNIGHT-` e limpe no fim.
- NÃO invente resultados. Se não conseguiu testar algo, escreva "não testado: <motivo>".
- Se a rodada for curta, cubra menos áreas mas com profundidade — qualidade > velocidade.

Trabalhe em silêncio e de forma autônoma. Não peça confirmação (a dona está dormindo). Ao terminar a rodada, apenas garanta que o `_ACHADOS_NOTURNOS.md` está atualizado e encerre — a próxima cron continua de onde você parou.

---

## CONFIGURAÇÃO DA CRON (para quem for iniciar)

- **Cadência:** a cada 25 minutos é um bom equilíbrio (rodadas não se atropelam, cobre ~28 rodadas em 12h). Expressão sugerida evitando o minuto 0/30: `7,32 * * * *` (dispara aos :07 e :32 de cada hora) OU um intervalo maior tipo `13 */1 * * *` (uma vez por hora aos :13) se quiser rodadas mais longas e espaçadas.
- **Duração:** 12h. Como cron recorrente expira em 7 dias automaticamente, não há risco de rodar pra sempre, mas o ideal é a dona parar/deletar a cron de manhã quando for corrigir.
- **NÃO iniciar agora.** A dona vai dar o start manualmente DEPOIS de trocar o modelo (pra um mais barato/rápido pro trabalho repetitivo de teste).
- **Como parar de manhã:** listar as crons e deletar a do teste noturno (ou pedir "pare a cron de teste noturno").

## RESUMO DO QUE FOI ENTREGUE
1. `_PLANO_TESTE_NOTURNO.md` — o plano detalhado (12 áreas, técnicas, regras, formato de relatório).
2. `_CRON_PROMPT_NOTURNO.md` — este arquivo, com o prompt exato da cron.
3. `_ACHADOS_NOTURNOS.md` — será criado pelo agente noturno na 1ª rodada (relatório acumulado).
4. Backup: branch `backup/pre-nightqa-20260724-1947` + tag `backup-wt-20260724-1947` (working tree completo).
