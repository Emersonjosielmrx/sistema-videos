# Contexto para um agente novo (outro PC ou Claude Code online)

> Escrito pelo agente do PC da dona em 05/10/2026. Junta o que estava só na memória local dele, para qualquer agente
> continuar o Hermes Call de outro lugar. **Ordem de leitura:**
> 1. topo do `CONTINUAR_DAQUI.md` (estado atual e o que falta);
> 2. este arquivo;
> 3. `docs/DIVISAO_TRABALHO_PC_ONLINE.md` (quem faz o quê);
> 4. `docs/REGRESSOES_LIGACAO.md` (obrigatório antes de mexer na voz);
> 5. `docs/PEDIDOS_AO_PC.md` e `docs/ensaios/` (testes pedidos e resultados).
>
> Histórico completo e legível da conversa do PC (02 a 05/10, sem segredos):
> `docs/archive/historico-conversa-PC-2026-10-02_a_05.md`. A conversa de 03/10 está em `docs/archive/historico-conversa-2026-10-03.jsonl`.

## 1. Onde está o código

- **Ramo de trabalho: `pc/v0.8.0`** no GitHub `Emersonjosielmrx/hermes-call` (remote `emerson`). Tem tudo:
  o v0.8.0 do agente online e as correções e ensaios do PC.
  - Comece qualquer trabalho novo a partir dele, num ramo próprio.
  - Não mexa no `main` antes de publicar.
- **Produção (desde 05/10 11:05):** v0.8.0, commit `b9bf587` (tag `PRODUCAO-20261005-1058_b9bf587`), igual ao
  `emerson/main` mais docs. O ramo `pc/v0.8.0` está à frente com a v0.8.1 (pronta, não publicada). A versão anterior
  (v0.7.0, `af7413e`) é a volta do `ops/reverter.sh`.
- O GitHub `fabricadeautomacoesia/hermes-call` (remote `origin`) ficou de propósito no `main` de 02/10, como
  referência da dona. As tags `PRODUCAO-*` estão lá. **Não empurrar código novo para o `origin` sem a dona pedir.**
- **⚠️ O repositório `Emersonjosielmrx/hermes-call` está PÚBLICO** (conferido em 05/10) e o histórico do git tem
  senhas e tokens antigos. Só a dona pode privar e trocar os segredos.
  - **Nunca** escrever senha, token, chave ou telefone completo em arquivo do repositório.

## 2. Para continuar de OUTRO COMPUTADOR (agente local)

1. `git clone https://github.com/Emersonjosielmrx/hermes-call.git D:\hermes-call` e depois:
   - `git checkout pc/v0.8.0`;
   - acrescentar o outro remote: `git remote add origin https://github.com/fabricadeautomacoesia/hermes-call.git`.
2. **Ferramentas:**
   - Go 1.26.x;
   - Node 20+ (o PC usa 24);
   - Git Bash (os scripts `ops/*.sh` rodam nele);
   - Python 3 (opcional).
   - Validar sem gcc: `CGO_ENABLED=0 go build ./... && go vet ./... && go test ./...`.
   - Painel: `cd client && npm ci && npx vite build && npx tsc --noEmit -p .` (0 erros, a CI trava).
   - O codec MLow (cgo) só compila na VPS.
3. **Acesso às VPS (só por chave, nunca senha):** o `~/.ssh/config` do PC tem estes apelidos:
   - `hermes-prod` = `root@62.171.128.241`: produção, bancada, Atlas/Lucrativa. **Compartilhada**: não mexer nos outros projetos.
   - `hermes-staging` = `root@209.145.60.53`: VPS de teste antiga, **COMPROMETIDA** (porta dos fundos no cron root desde jul).
     Não pôr segredo novo lá; só recebe cópia limpa do código.
   - `hermes-bloqueio` = `root@157.173.207.22`: OmniRoute e outros projetos.

   Um computador novo precisa de **uma chave SSH própria** autorizada pela dona no `/root/.ssh/authorized_keys` da
   produção. **Nunca** copiar a chave privada de um PC para o repositório.
4. Os worktrees `D:\hermes-wt\*` do PC antigo eram só para trabalho em paralelo e não precisam existir no PC novo.
   Tudo deles já está em `pc/v0.8.0`.

## 3. Para o agente ONLINE (sem acesso às VPS)

- Faz código, testes (inclusive com Postgres descartável, `HERMES_TEST_PG`), CI, painel e documentação.
- O que precisa de VPS, bancada, banco de produção ou ligação real vira pedido em `docs/PEDIDOS_AO_PC.md`.
- Nunca publica.

## 4. Operação na VPS (resumo; detalhes no CONTINUAR_DAQUI e em `docs/VERSOES.md`)

- **Publicar:**
  - `bash ops/publicar.sh` (compila na VPS com `-tags mlow`, faz backup do banco, volta sozinho se falhar);
  - `--so-compilar` só prepara a versão;
  - `PUBLICAR_COM_BANCADA=1` também atualiza a bancada.
- **Voltar:**
  - `bash ops/reverter.sh` ou `ops/voltar-estavel.sh` (ou o `.bat`);
  - depois de voltar, **recarregar o painel** (Ctrl+F5) em todas as abas.
- **Marcar estável** (só depois de a dona aprovar uma ligação): `bash ops/marcar-estavel.sh`. Hoje a ESTÁVEL ainda é a
  v0.5.0 de 25/09.
- **Bancada** (cópia de teste na mesma VPS; `hermes-bancada.service`, porta 127.0.0.1:8091, linha 8288):
  - atualizar com `/root/lab-bancada.sh preparar <ID da versão>`;
  - chaves de teste no `/etc/hermes-bancada/bancada.env`: `HERMES_TESTE_ACEITE_POR_RELAY=true` e
    `HERMES_VOICE_ESPERA_ACEITE=false`. **Nunca** na produção, e o `publicar.sh` recusa.
- **Ensaio IA × IA:**
  - comando: `/opt/hermes-call/ops/ensaio.sh completo`.
  - Como funciona:
    - a bancada é a vendedora;
    - a produção vira cliente só para o 8288, sem som de fundo e sem palavras de apoio;
    - a janela desliga sozinha em 30 min;
    - os números completos ficam em `/etc/hermes-call/ensaio.env` (só na VPS).
  - **O ensaio faz o celular 8653 da dona TOCAR** (é a linha que serve de cliente). Avise antes e peça para não
    atender: em 05/10 ela atendeu, caiu numa ligação com duas IAs e achou "horrível". O relatório marca
    "ENSAIO INVÁLIDO" quando um celular atende.
  - **Reinicia a produção 2 vezes (~10 s cada)** e usa as **mesmas chaves grátis** da produção. Espaçar ≥ 10 min,
    fora do horário de uso.
  - Gravar o resultado em `docs/ensaios/`.
- **Segredos da produção:** `/etc/systemd/system/hermes-call.service.d/10-segredos.conf`. Não ler em voz alta, não copiar.
- **Backups manuais:**
  - `/opt/hermes-call/backups-manuais/`;
  - backups de configuração em `/opt/hermes-call/releases/config-backups/`;
  - uma cópia de 02/10 está no PC antigo em `D:\hermes-call-backups\`.

## 5. Regras e preferências da dona (valem sempre)

- Falar com ela em **português simples**, direto, sem jargão. Ela escreve rápido e com erros de digitação; entenda a intenção.
- **Só dizer "pronto" depois de verificar de verdade.** Na voz, isso quer dizer uma ligação real ou um ensaio na bancada.
- **Documentar tudo o que for testado** (`docs/ensaios/`, CONTINUAR_DAQUI) e não repetir teste sem motivo novo.
- **Publicar na produção só com OK dela.**
  - Ela autorizou decisões técnicas e publicar e testar quando estiver ausente, mas a regra atual do PC é pedir o OK
    a cada publicação (a v0.8.0 foi ao ar em 05/10 com o OK dela; a v0.8.1 espera o OK).
  - Ações irreversíveis, pagamento (Asaas) ou segurança no servidor (firewall, senhas, chaves, contas): o agente
    PREPARA e ela roda.
- Toda publicação precisa de volta fácil. A versão que está funcionando bem não pode se perder.
- Ela troca de conta e de agente (local e online) com frequência. **Mantenha o CONTINUAR_DAQUI atualizado ao fim de
  cada etapa** e commite e envie com frequência: o limite de uso costuma cortar no meio.
- Na divulgação de outros projetos dela (Lucrativa/Assist-IA) a regra é "a IA" no feminino, nunca "robô". Não é do Hermes,
  mas ela é a mesma dona.

## 6. Fatos técnicos que custaram caro descobrir

- **Aceite da ligação recebida:** o WhatsApp não reconhece o `accept` que o Hermes manda.
  - Na ligação Hermes → Hermes, quem liga nunca recebe o aceite.
  - Por isso o atendimento automático está desligado (`HERMES_AUTO_ANSWER_ACEITAR`) e o ensaio usa o aceite presumido.
  - As variantes candidatas (`HERMES_ACEITE_VARIANTE`) estão prontas.
  - **Falta capturar o aceite de um celular de verdade** (um celular da dona atendendo uma ligação da bancada) e testar
    as variantes (pedido 4).
- **8288** é ao mesmo tempo o celular de teste da dona, uma linha da produção (conta do Rafael) e a linha da bancada.
  Bancada com aceite ligado entra nas ligações da dona: foi o incidente de 03/10.
- **Chaves grátis** (Gemini "LLM Padrão" e Groq) estouram o limite por minuto em rajada. A v0.8.0 limita a transcrição
  antecipada a 1 por fala e recua 3 min após o 429.
- **Whisper inventa texto** em ruído (islandês, "Tudududu…"). O filtro de confiança (`verbose_json`) descarta;
  `HERMES_STT_CONFIANCA=false` desliga.
- **Codec MLow** compilado com `OPUS_HARDENING` derruba o processo. A lib da VPS foi recompilada sem; ver REGRESSOES §2.
- O agente "Teste E" fala do produto **Inovare Claw** a R$ 99 (outro produto da dona). Para vender o Hermes Call, use
  o **"Vendas Hermes Call"**, que desde 04/10 é o agente padrão das ligações da dona.
