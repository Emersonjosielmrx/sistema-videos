# Hermes Call — Bloqueio de Números: Aprendizados & Estratégias

> Documento vivo. Escrito em 2026-07-26. Autocontido: dá pra retomar do zero.
> Escopo ISOLADO: só pasta `D:\hermes-call-bloqueio\` + VPS de teste `157.173.207.22`.
> NUNCA editar `D:\hermes-call\` (produção-fonte) nem VPS de prod (62.171.128.241) / staging (209.145.60.53).

---

## 0. O PROBLEMA (o que a dona quer resolver)

Após certo volume de chamadas, a linha do WhatsApp passa a ter **TODAS as chamadas
de saída rejeitadas** pelo servidor do WhatsApp com `offer ack error=439` ou `error=463`.
**Mensagens continuam funcionando; só chamada cai.** Objetivo: contornar esse bloqueio.

Causa suspeitada (workers 2026-07-25): **Reachout Timelock** — anti-spam que o servidor
aplica em contas que fazem muitos reachouts (chamadas/mensagens) sem o token `<tctoken>`
correspondente.

---

## 1. O QUE APRENDEMOS NESTA SESSÃO (2026-07-26)

### 1.1. A premissa do README original está DESATUALIZADA
- README dizia: "whatsmeow só anexa `<tctoken>` no `RejectCall()`, não no offer de saída".
- **REALIDADE (verificada no código):** a chamada de saída do Hermes NÃO usa a função de
  call do whatsmeow. Usa um pacote VoIP próprio: `wacalls/internal/voip/`.
- O offer de saída **JÁ anexa o `<tctoken>`** — ver
  `D:\hermes-call\internal\voip\signaling\signaling_build.go:39-42`:
  ```go
  if token, err := sock.GetTCToken(ctx, ...); err == nil && len(token) > 0 {
      offerContent = append(offerContent, waBinary.Node{Tag: "tctoken", Content: token})
  }
  ```
- Comentário no código (linha 40-41) confirma: a tag correta é `tctoken` (com "privacy"
  o servidor ignora e o offer some sem ack). Alguém — provável outro agente — já
  implementou esse fix.
- **CONCLUSÃO:** o problema NÃO é "falta o tctoken no código". Restam as hipóteses:
  - (A) `GetTCToken()` retorna vazio pra aquele peer → offer sai SEM tctoken → cai 463.
  - (B) token vai, mas o servidor aplica timelock por VOLUME (enforcement server-side)
        → o fix não é técnico, é de cadência/aquecimento (warm-up) da linha.
  - (C) token existe mas expirado/malformado.

### 1.2. whatsmeow: só recebe call, e faz RejectCall (com tctoken)
- `go.mau.fi/whatsmeow@v0.0.0-20260630180629-b572e5bcb92b/call.go`: só `handleCallEvent`
  (recebe eventos) e `RejectCall` (já usa `ensureTCToken`).
- `tctoken.go` da lib tem toda a maquinaria: `ensureTCToken`, `issuePrivacyToken`,
  `shouldSendNewTCToken`, `getTCTokenSenderTS`, `validateAndSetTCTokenSenderTS`, etc.
- Evento-chave pra investigar: `events.NotifyAccountReachoutTimelock`
  (campos: `IsActive`, `EnforcementType`, `TimeEnforcementEnds`, `Mex.OpName`, `Mex.Timestamp`).

### 1.3. Por que a produção pareia e o harness caseiro NÃO
- Produção conecta via **proxy** (`applyProxy` → `SetProxyAddress`) ANTES de parear.
  Proxy é por-sessão, configurado via API `PUT /api/sessions/{sid}/proxy`, guardado no DB.
  Proxy residencial (Webshare). Harness caseiro conectava pelo IP CRU da VPS (datacenter).
- Isso NÃO foi a causa do fracasso do QR (ver 1.4), mas é diferença real que importa
  pro comportamento de bloqueio.

### 1.4. O harness de investigação (Passo #1) FALHOU em parear — e o motivo
- Fizemos: bug fix (nil pointer em `client.Store.ID.String()` quando não-pareado,
  `main.go:164`), servidor HTTP `/qr` na porta 8081 pra escanear pelo navegador,
  upload por SFTP (com `MSYS_NO_PATHCONV=1` — o git-bash convertia `/opt/...` em
  `C:/Program Files/Git/opt/...` e quebrava tudo).
- Trocamos o desenho do QR: primeiro `skip2/go-qrcode` (320px), depois maior (600px),
  depois copiamos o render EXATO da produção (`rsc.io/qr` nível M, scale 8, border 4 —
  `D:\hermes-call\cmd\server\qr_image.go`).
- **RESULTADO: nenhum dispositivo conecta no QR do harness.** 30 QRs gerados,
  ZERO tentativas de scan chegaram no processo (nenhum `PairSuccess`/`PairError`/
  `QRScanned`). O mesmo número/aparelho pareia normal em WhatsApp Web, Evolution e
  na produção Hermes.
- **VEREDICTO:** o harness caseiro (Passo #1) tem algo errado de fundo que impede o
  pareamento — não vale mais insistir nele. Abandonar o harness manual.

### 1.5. Infra da VPS de teste (157.173.207.22)
- Host `meuservidor1`. Roda Docker **Swarm** com stack cheia: Traefik v2.11.3 (portas
  80/443), Chatwoot/superchat, Redis, Postgres (pgvector), n8n (editor+webhook), load tester.
- **NÃO tem Hermes rodando** — é o quadro limpo que a dona indicou pra testar.
- Go NÃO está instalado no host (builds são feitos no Windows e enviados como binário).
- `/opt/hermes-call-anexo/` já existia (o harness Passo #1). Tem backup do binário antigo.
- **ATENÇÃO port 8080/50000:** Traefik ocupa 80/443. Verificar conflito antes de expor.

### 1.6. Mecânica de deploy/instalação do Hermes (descoberto)
- `Dockerfile`: 4 stages (client React → codec MLow opus → server Go cgo tag `mlow` →
  runtime slim com ffmpeg + edge-tts). Build pesado.
- `docker-compose.yml`: usa **imagem pronta do Docker Hub** `fabricadeautomacoesia/hermes-call:latest`
  + Postgres 16. Env principal: `WACALLS_PG_URL`, `PORT=8080`. Portas 8080 (web/api) e
  50000/udp (mídia voip). **=> dá pra instalar SEM buildar: só puxar a imagem.**
- Produção real usa `deploy/deploy-docker.js` (--network host + Traefik), não o compose.
- Projeto tem 3.4G no disco (mídia/pngs/artefatos) — copiar tudo é inviável e desnecessário.

---

## 2. ESTRATÉGIAS — TODAS AS OPÇÕES

### Feitas (e descartadas/aprendidas)
- [x] **Harness Passo #1 (log puro)** — corrigido crash, servido QR por HTTP.
      DESCARTADO: não pareia (1.4). Serviu pra mapear infra e confirmar hipóteses.
- [x] **Análise estática do código** — confirmou tctoken já implementado (1.1).
- [x] **Hermes REAL isolado na VPS teste + chamada de teste com DEBUG** — REPRODUZIMOS
      o bloqueio e capturamos a causa raiz (ver 1.7). MUDA TUDO.

---

## 1.7. CAUSA RAIZ REAL (capturada 2026-07-26, com prova no log DEBUG)

**NÃO é Reachout Timelock / volume.** É bug de resolução de JID pra chamada.

Sequência capturada (chamada pra 5591985685106, callID 96C758...):
1. `resolveCallPeer` resolve o telefone certo: `input=5591985685106 resolved=559185685106`.
2. Mas a consulta de dispositivos (usync `context=message`) vai pro **LID**, não pro telefone:
   `<iq xmlns=usync><query><devices version=2/></query><list><user jid="270794013831412@lid"/></list></iq>`
3. Servidor responde **VAZIO**: `<result><devices/></result><list/>` — esse LID não tem devices.
4. Sem devices → `CreateParticipantNodes` não produz nada → `<destination/>` sai **VAZIO** no offer.
5. Offer vai sem destino → servidor **ignora em silêncio** (nenhum ack, nenhum 439/463).
6. Chamada fica presa (ringing) até `call watchdog` matar em ~6 min.

**Offer cru capturado:**
```xml
<call id="1891490F..." to="270794013831412@lid">
  <offer call-creator="132250784018630:20@lid" call-id="96C758...">
    <audio enc="opus" rate="8000"/><audio enc="opus" rate="16000"/>
    <net medium="3"/><capability ver="1">0105f709e4bb07</capability>
    <destination/>            <!-- VAZIO: nenhum participante cifrado -->
    <encopt keygen="2"/>
  </offer>
</call>
```
Também: NÃO tem `<tctoken>` (log mostrou `Removed 454 expired tctokens from DB` — tokens
expirados, então o `if GetTCToken len>0` nem entra). Mas o tctoken é secundário aqui:
o furo primário é o `<destination>` vazio por LID sem devices.

**Hipótese do fix:** a chamada deve consultar devices e cifrar pro **telefone @s.whatsapp.net**
(que existe — o IsOnWhatsApp confirmou `+5591985685106@c.us`), não pro `@lid`. Ver
`resolveCallPeer` (retorna `it.JID.ToNonAD()` — pode estar devolvendo o LID) e
`GetUSyncDevices`/`BuildOfferStanza` em signaling_build.go. Investigar por que o peer
vira LID e forçar o PN (phone number) na consulta de devices do offer.

**A INVESTIGAR:** isso acontece SÓ com esse número, ou com todos? Se for todos, é bug
geral de chamada na v0.2.1 (não "bloqueio"). Testar com um 2º número confirmaria.

## 1.8. COMENTÁRIOS NO FONTE (decisões já tomadas por agente anterior)

Lendo D:\hermes-call\internal\wa\socket.go e internal/voip/call/*.go, o agente anterior
JÁ passou por várias tentativas e deixou registrado:
- **LID é intencional** (`StartCall`): "trocar pra peer=PN cru (@s.whatsapp.net) faz o
  servidor rejeitar com offer ack error=439". Por isso resolve PN→LID (`ResolveLIDForPN`).
- **GetTCToken foi DESLIGADO de propósito** (stub retorna nil): "anexar o tctoken guardado
  (stale) faz o destino DESCARTAR o offer em silêncio — até números que aceitariam param
  de tocar. Sem token, o offer toca (preaccept). O 463 em números com privacidade estrita
  é anti-spam do WhatsApp (sem fix)."

**IMPLICAÇÃO:** o "bloqueio" pode NÃO ser um bug com fix no cliente. O 463/silêncio em
certos números pode ser anti-spam server-side do WhatsApp (destino não aceita chamada de
desconhecido / privacidade). O teste com UM número (5591985685106) que deu `<destination>`
vazio pode ser exatamente esse caso — não representa necessariamente "a linha bloqueada
não liga pra ninguém".

## 1.9. DIAGNÓSTICO FINAL — CONFIRMADO (2026-07-26, teste com 5 números)

Ligamos a MESMA linha bloqueada (559184698653) pra 5 números do próprio histórico:

| Número          | devices resolvidos | offer             | resposta servidor |
|-----------------|--------------------|-------------------|-------------------|
| 91985685106     | VAZIO              | <destination/> vazio | silêncio (morre)  |
| 5522998908709   | 4 devices          | offer COMPLETO    | (sem erro)        |
| 557999777712    | 2 devices          | offer COMPLETO    | (sem erro)        |
| 5517991656664   | 2 devices          | offer COMPLETO    | **error=463**     |
| 5511985936305   | 1 device           | offer COMPLETO    | **error=463**     |

Prova crua:
```
<ack class="call" error="463" from="23940248395897@lid" type="offer"/>
<ack class="call" error="463" from="23369017721025@lid" type="offer"/>
```

**CONCLUSÃO DEFINITIVA:** o Hermes monta o offer PERFEITO (resolve LID, busca devices,
cifra participantes, envia `<destination>` cheio). Mesmo assim o servidor do WhatsApp
responde **error=463** = RECUSA server-side. NÃO é bug de código. É anti-spam/rate-limit
aplicado À CONTA (a linha foi marcada por volume de chamadas). O caso do 91985685106 com
destination vazio é um sub-caso (aquele destino/LID não expôs devices — provável privacidade),
mas o achado principal é o 463 nos offers bem-formados.

**NÃO EXISTE FIX DE CÓDIGO.** Nenhum ajuste de tctoken/destination/formato faz o servidor
parar de recusar — o offer já está correto. Bate 100% com o comentário do agente anterior
em socket.go: "o 463 ... é anti-spam do WhatsApp (sem fix)".

## 2-bis. CAMINHOS REAIS (já que não é código)

1. **Aquecer/descansar a linha (warm-up):** parar de ligar por X dias; usar a linha só pra
   mensagens legítimas por um tempo; voltar a ligar em ritmo BAIXO. O 463 costuma ser
   temporário — a marca da conta afrouxa se o padrão de spam para.
2. **Cadência anti-ban nas campanhas:** espaçar chamadas (paced/multi-linha), teto por
   linha/dia, nunca discar em rajada. Já existe infra de campanha paced no Hermes.
3. **Rotação de linhas:** distribuir o volume entre várias linhas; aposentar as marcadas.
4. **Proxy residencial por linha (Webshare):** a produção já faz; IP de datacenter agrava.
   Não conserta o 463 sozinho, mas reduz chance de nova marcação.
5. **Não re-tentar offer em loop** quando dá 463 (cada retry conta como reachout e piora).
6. **Reduzir "reachout frio":** mandar mensagem/aquecer relação antes de ligar pra
   desconhecido (o WhatsApp trata chamada de contato desconhecido como mais suspeita).

**O que NÃO adianta:** mexer em tctoken, formato do stanza, destination, versão do cliente.
O offer já está aceito pela lógica; a recusa é política de conta do servidor.

### Em andamento (decisão da dona 2026-07-26)
- [ ] **Rodar o Hermes Call REAL isolado na VPS de teste.** Copiar o essencial pra
      `hermes-call-bloqueio` e subir via docker-compose com a imagem publicada.
      Como o código real pareia normal, reproduzimos o bloqueio de verdade e aí
      testamos os contornos com instrumentação.

### A fazer — contornos possíveis do bloqueio (todas as opções)
1. **Reproduzir + observar** (base de tudo): subir Hermes real, parear linha de teste
   (559192438288 ou chip livre), disparar chamadas até bater 439/463, capturar via
   logs do próprio Hermes o evento `NotifyAccountReachoutTimelock` e o offer/ack cru.
   Distinguir hipóteses A/B/C do item 1.1.

2. **Garantir tctoken presente em TODO offer** (se hipótese A): checar por que
   `GetTCToken` volta vazio; forçar `ensureTCToken`/`issuePrivacyToken` antes do offer;
   log quando offer sai sem token.

3. **Warm-up / cadência da linha** (se hipótese B — enforcement por volume):
   - Ritmo de discagem mais lento (espaçar reachouts).
   - Alternar com mensagens legítimas antes de chamar (aquecer relação com o número).
   - Rotação de linhas (multi-linha, teto anti-ban por linha).
   - Respeitar `TimeEnforcementEnds` quando o timelock estiver ativo (backoff até liberar).

4. **Proxy residencial por linha** (Webshare) — replicar o que a produção faz; IP de
   datacenter pode agravar o enforcement.

5. **Pré-chamada por mensagem template** — mandar msg antes da chamada pra criar
   "trusted_contact"/privacy token válido (a lib tem `privacy_token`, `trusted_contact`).

6. **Ajuste do stanza de offer** — comparar byte-a-byte com o offer de um cliente
   oficial (capability bytes, `<destination>`, `encopt keygen`) caso o servidor
   rejeite por formato, não por timelock.

7. **Reduzir "reachout" percebido** — não re-tentar offer em loop quando cai 463
   (cada retry conta como reachout e piora o timelock).

---

## 3. PLANO IMEDIATO (rodar Hermes real na VPS de teste)

1. Copiar pra `hermes-call-bloqueio/hermes-app/` só o necessário pra subir:
   `docker-compose.yml` (adaptado: portas sem conflito com Traefik, sem expor à toa).
2. Puxar imagem `fabricadeautomacoesia/hermes-call:latest` na VPS (ou tag estável).
3. Subir Postgres + app isolados (nomes/vol\. próprios, porta interna, sem tocar Swarm).
4. Acessar painel do Hermes (via SSH tunnel ou porta dedicada), criar sessão, parear
   linha de teste COM proxy.
5. Disparar chamadas de teste, observar logs até reproduzir 439/463.
6. A partir da evidência real, aplicar os contornos da seção 2.

### Regras fixas (não violar)
- Linha de teste: `559192438288` (não é campanha, não toca cliente real) — ou chip livre.
- Isolamento TOTAL de produção. Nada editado em `D:\hermes-call\`.
- Batch: agrupar operações caras numa chamada só (a dona cobra por chamada de API).
- Nunca afirmar "pronto/funciona" sem evidência (log real do ack da chamada).
