# Revisão do ramo do agente online (04/10/2026)

Ramo revisado: `emerson/claude/gallant-mendel-f1xney`, até o commit `9ade018` (37 commits em cima do `main`).
O `main` é a produção (`af7413e`, v0.7.0) mais 1 commit de docs.
Feita no PC por 3 revisores independentes (voz; banco/segurança/cobrança; publicação/CI/painel) e conferida na produção
com consultas só de leitura. **Nada foi publicado nem juntado ao `main`.**

## Veredito

O trabalho tem coisas boas: 3 vazamentos entre contas corrigidos, defeitos reais do painel, testes com banco,
CI mais forte e dependências atualizadas. **Mas NÃO pode ir para a produção como está.** Há 1 problema crítico
nos scripts de publicação e vários altos na voz.

## CRÍTICO, corrigir antes de qualquer publicação

1. **A volta de versão deixa de funcionar** (`ops/vps/hermes-release.sh` ~142, ~174-184, ~248).
   - O que acontece: depois da 1ª publicação com o script novo, `voltar-estavel.sh`, `VOLTAR-VERSAO-ESTAVEL.bat` e
     `reverter.sh` conferem as linhas pela rota `/saude-local`, que as versões antigas não têm. A conferência falha
     e a "volta automática" **recoloca a versão nova no ar**. A versão antiga fica de ~1,5 a 2,5 min no ar e é desfeita.
   - Correção: pular a conferência de linhas quando a versão de destino não tem `/saude-local`. Em
     `voltar-estavel`/`reverter`, conferir só se o serviço está saudável (uma volta de emergência nunca se desfaz sozinha).

## ALTO

2. **A bancada é atualizada e reiniciada em toda publicação** (`ops/publicar.sh` ~117-126), com trava fraca do aceite automático.
   - Por que a trava é fraca: ela confere depois do reinício e só avisa; procura no lugar errado (a bancada herda o
     ambiente da produção por `/opt/hermes-bancada/iniciar.sh`); e não reconhece `TRUE`/`"true"`.
   - Risco: repetir o incidente de 03/10, em que a bancada atendeu a ligação da dona.
   - Correção: a bancada só é atualizada quando pedido (`PUBLICAR_COM_BANCADA=1`). Antes de atualizar, conferir o
     ambiente real dos processos (`/proc/<pid>/environ`) e parar se o aceite estiver ligado. Validar pela `/api/version`
     da bancada.
3. **Voz, "lead quente" ligado por padrão** (`cmd/server/call_triggers.go:34`, `AdminSummonCard.tsx:93,168`, `httpapi.go:952-965`).
   - O que acontece: o card faz a dona entrar na ligação **sem calar a IA**, e as duas falam juntas. Ao sair, a ligação **cai**.
   - Correção: calar a IA ao entrar por esse card (`armPanelBridge(silent_relay)`), ou não mostrar o botão no modo só-aviso.
4. **Voz, a transcrição antecipada ignora o prazo de 3 s da resposta à isca** (`internal/voice/stt_antecipado.go:58-69`).
   - O que acontece: com o Groq lento, o cliente fica até ~30 s em silêncio entre o "alô" e a oferta.
   - Correção: `takeEarlySTT(ctx, …)` respeitando `ctx.Done()`.
5. **Voz, a IA marca horário: diz "já anotei" sem ter anotado** (`cmd/server/voz_acoes.go:130-133`).
   - Correção: marcar a vez só depois de gravar com sucesso.
6. **Agendamento da IA dispara lembretes automáticos por WhatsApp** de compromisso que a dona não confirmou
   (`voz_agendar.go:114`; `agenda_store.go:403,419`).
   - Correção: não mandar lembrete de `source='agent'` com `status='pendente'`. Enquanto não corrigir, publicar com
     `HERMES_VOICE_AGENDAR=false`.

## MÉDIO

- **Memória da ligação compara só os 8 últimos dígitos** (`call_memory.go:32`): pode contar a conversa de um contato a
  outro (LGPD) e faz uma consulta lenta antes da 1ª resposta. Hoje há 0 colisões na produção, mas precisa comparar
  DDD+número e rodar em paralelo.
- **Mais pontos da voz:**
  - gravação no fim da ligação e aviso no Telegram de forma síncrona (`call_health.go:226`, `voz_agendar.go:132`):
    podem travar a sinalização ou deixar o turno mudo;
  - transcrições antecipadas não canceladas: 1 a 3 pedidos a mais ao Groq por fala;
  - a recepcionista apaga o roteiro próprio da ligação recebida (`session.go:780`);
  - o lead quente dispara com "eu quero que pare de me ligar" e não tem chave para desligar.
- **Testes com Postgres sem trava contra banco real** (`internal/testpg/testpg.go`): o exemplo do `.env.example` aponta
  para o Postgres da VPS (= produção). Recusar banco sem "test" no nome.
- **Conferências do script novo:**
  - a conferência de pânico lê o log da parada da versão antiga e pode recusar a nova por engano;
  - a de linhas recusa a publicação se uma linha de cliente não reconectar.
- **Exportar contatos (CSV) da campanha:** o telefone vira 5,51E+12 no Excel e não há proteção contra fórmula vinda do lead.
- **Chatwoot:** a janela pode sumir para o dono legítimo (busca sem filtrar pela conta, `chatwoot.go:884,901`).

## O que está OK (conferido)

- **Banco:** migrações só aditivas. Conferido na produção em 04/10: chaves corretas, 0 duplicatas, 0 nulos, nenhum
  conflito de nome, nenhuma transação aberta, 0 erros de chave em 14 dias. Voltar para a `af7413e` com o banco migrado é seguro.
- **Segurança:** as correções de vazamento entre contas e de `/api/diagnostics` estão certas. A tela "Configuração do
  servidor" não mostra segredos e é só leitura, só para a administradora.
- **Dependências:** upgrade (golang-jwt 5.2.1→5.2.2, corrige CVE-2025-30204), sem quebrar logins.
- **Painel:** compila; o `tsc` passa; os defeitos corrigidos são reais; o carregamento inicial não mudou (+0,1%).
- **CI:** sem segredo exposto e sem deploy automático.
- **Testes:** `go vet` ok; testes ok. A falha de `TestEnvCatalog_DadosEmDia` no Windows é só fim de linha (CRLF), não defeito.

## Antes de publicar este ramo (depois das correções)

1. Guardar o script atual da VPS: `cp -a /opt/hermes-call/releases/hermes-release.sh /root/hermes-release.sh.antes-v080`.
2. Publicar com `PUBLICAR_SEM_BANCADA=1` até a trava da bancada ser corrigida.
3. Testar na bancada:
   - interromper a oferta;
   - latência da 1ª resposta com e sem histórico;
   - resposta à isca com Groq lento;
   - marcar horário ocupado e depois livre;
   - lead quente;
   - ligação recebida com o aceite desligado.
4. Chaves de emergência, todas com `=false`: `HERMES_VOICE_STT_ANTECIPADO`, `HERMES_VOICE_AQUECER`, `HERMES_VOICE_MEMORIA`,
   `HERMES_VOICE_AGENDAR`, `HERMES_CALL_TRACE`.

## Ligação da dona em 04/10 09:20 (produção af7413e), para comparação

- A oferta foi interrompida (`interrompida=true pct=34`): a correção de 03/10 funcionou.
- Latência fim da fala → 1º áudio de 2,7 a 2,9 s (VAD 840 ms + STT 0,2-0,4 s + IA 1,0-1,3 s + voz 0,4-0,6 s).
- Perda de pacotes 0%. Uma transcrição saiu em islandês ("Ég komstu hjá hana."): forçar o idioma pt no Whisper.
- Usou o agente "Teste E": definir o agente padrão de ligação (`/agentepadrao Vendas Hermes Call`).
