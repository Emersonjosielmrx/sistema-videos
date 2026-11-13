# Campanha à prova de deploy — como usar na prática

## O que mudou (resumo)

Antes, se você disparasse uma campanha e a gente fizesse um deploy no meio, a campanha
**morria** e não voltava. Agora ela é **salva no banco** e **retoma sozinha** depois do deploy,
ligando/mandando mensagem só pra quem **ainda não foi atendido** (quem já foi `completed`,
`no-answer`, `failed` ou já recebeu a mensagem **não** é refeito).

Vale pra **campanha de ligação** e pra **disparo de mensagem** (em massa e normal).

## Por que não são 2 ambientes rodando ao mesmo tempo

O WhatsApp só deixa **1 conexão ativa por número/aparelho**. Se subíssemos 2 versões ligadas ao
mesmo WhatsApp, elas brigariam e derrubariam uma à outra. Por isso a solução é: **1 ambiente só**,
mas com a campanha **persistida** — o deploy dá um "blip" de ~15-30s e a campanha continua.

## Fluxo do dia a dia

1. **Rode a campanha normalmente** pelo painel (Contatos → Ligar em Massa / Disparo).
   - A campanha e a lista de números ficam salvas no banco automaticamente.
   - O nome do perfil (push name) de cada número é resolvido **uma vez** e reusado — no painel de
     resultados aparece o **nome** em vez de só o número.

2. **Quando você/eu formos editar e subir versão nova**, é sempre este ciclo seguro:
   ```
   node deploy/_compile_check.js      # confere que o Go compila (sem subir nada)
   node deploy/deploy-beta.js         # sobe a versão nova (a estável fica guardada p/ rollback)
   ```
   - Ao subir, o container reinicia (~15-30s). **A campanha em andamento é retomada
     automaticamente ~15s depois do boot**, continuando de onde parou.
   - Valide em https://hermescall.opus-sem-limites.com.br
     (se a tela estiver com cara antiga, é cache do navegador → **Ctrl+Shift+R**).

3. **Se ficou bom:**
   ```
   node deploy/promote-stable.js      # marca essa versão como a nova "estável"
   ```
   **Se deu ruim:**
   ```
   node deploy/rollback.js            # volta pra versão estável anterior
   ```

## Detalhes de como o resume funciona

- No boot, ~15s depois de reconectar o WhatsApp, o sistema procura campanhas **abertas**
  (não finalizadas) e re-dispara **só os números pendentes**.
- Se a sessão WhatsApp ainda não voltou naquele momento, a campanha fica aberta e é retomada
  no próximo boot (não perde).
- Idempotente: cada número tem chave única na campanha, então retomar **nunca duplica** ligação
  nem mensagem.

## Observação

- O "blip" de ~15-30s existe porque é 1 container só (limitação do WhatsApp, ver acima). Se um dia
  precisar de zero-downtime real, seria necessário um 2º número de WhatsApp dedicado a teste — não
  é o caso hoje.
