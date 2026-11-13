# Conexão WhatsApp sem celular físico — Análise técnica

Escrito em 07/10/2026. Análise de como o Hermes Call conecta ao WhatsApp e alternativas para conexão web sem emular celular.

---

## Como funciona hoje

O Hermes usa a biblioteca **whatsmeow** (Go) que implementa o protocolo Multi-Device do WhatsApp. Há **duas formas de pareamento**:

### 1. QR Code (método atual principal)

**Fluxo implementado:**
- Back: `session.go:997-1034` — `startPairing()` chama `client.GetQRChannel()`
- Gera QR que atualiza a cada ~20s
- Front: `SessionPairing.tsx:124-128` — renderiza QR com `QRCodeSVG`
- Usuário escaneia no WhatsApp → Aparelhos conectados → Conectar aparelho
- Telegram: QR enviado como imagem automática para o dono (linha 1018-1024)

**Arquivos:**
- Backend: `d:\hermes-call\cmd\server\session.go:997-1034`
- Frontend: `d:\hermes-call\client\src\components\domain\session\SessionPairing.tsx`

### 2. Código de 8 dígitos (JÁ IMPLEMENTADO, mas não está na UI principal)

**Fluxo implementado:**
- Endpoint: `POST /api/sessions/{sid}/pair-code` com `{"phone": "5591988887777"}`
- Back: `session.go:1070-1079` — `pairWithCode()` chama `client.PairPhone(phone, ...)`
- Retorna código de 8 dígitos
- Usuário digita no WhatsApp → Aparelhos conectados → Conectar com número de telefone

**Onde está:**
- API: `httpapi.go:821-838` — `handleSessionPairCode()`
- Lógica: `session.go:1070-1079` — `pairWithCode()`
- Chamada do manager: `sessionmanager.go:310-320` — `PairPhone(id, phone)`
- **IA já usa**: `aiagent_ops.go:220-224` — agente IA pode parear por código via Telegram

**Exemplo de resposta da API:**
```json
{"code": "12345678"}
```

**Como o usuário conecta depois:**
1. WhatsApp → Aparelhos conectados
2. **Conectar com número de telefone** (não "Conectar aparelho")
3. Digite o código de 8 dígitos
4. Pronto, conectado

---

## O que você quer: número direto no painel

**Situação atual:** Para parear por código, já existe a API mas **falta UI no painel**.

**O que precisa:**

### 1. Adicionar botão/formulário no frontend

Modificar `SessionPairing.tsx` para oferecer **duas opções**:

**Opção A: QR Code** (mantém o atual)
```
┌─────────────────────────────────┐
│   [QR Code renderizado aqui]    │
│ Escaneie no WhatsApp             │
└─────────────────────────────────┘
```

**Opção B: Código de pareamento** (adicionar)
```
┌─────────────────────────────────┐
│ Ou conecte com código:           │
│ [input: +55 91 98888-7777] [Gerar código] │
│                                  │
│ Seu código: 12345678            │
│ Digite no WhatsApp em:          │
│ Aparelhos conectados → Conectar │
│ com número de telefone          │
└─────────────────────────────────┘
```

### 2. Backend já está pronto

A API `POST /api/sessions/{sid}/pair-code` já existe e funciona. Só precisa chamar do frontend.

### 3. Código de exemplo para adicionar na UI

```tsx
// Em SessionPairing.tsx, adicionar estado:
const [pairMode, setPairMode] = useState<"qr" | "code">("qr");
const [phone, setPhone] = useState("");
const [pairCode, setPairCode] = useState("");

// Função para solicitar código:
const generateCode = async () => {
  const res = await fetch(`/api/sessions/${session.id}/pair-code`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({phone: phone})
  });
  const data = await res.json();
  setPairCode(data.code);
};

// No render, adicionar tabs/toggle entre QR e código
```

---

## Vantagens do pareamento por código

1. **Não precisa de celular físico na hora de conectar**
   - Número já está registrado no WhatsApp
   - Basta digitar o código no app (celular, web, desktop)

2. **Mais fácil para conexão remota**
   - Dona pode estar em qualquer lugar
   - Não precisa abrir câmera para escanear QR

3. **Melhor para automação**
   - IA do Telegram já usa (linha `aiagent_ops.go:220`)
   - Código pode ser copiado/colado

4. **Funciona igual ao QR**
   - Mesma segurança
   - Mesma persistência da sessão
   - Mesmo protocolo Multi-Device

---

## Sobre "emular celular"

**Não é emulação.** O protocolo Multi-Device do WhatsApp permite:

- **1 dispositivo principal** (celular com chip)
- **Até 4 dispositivos conectados** (web, desktop, outros apps)

O Hermes se conecta como **dispositivo secundário**, igual ao WhatsApp Web. Por isso:

- ✓ Celular pode estar desligado depois de conectar
- ✓ Mensagens chegam direto no Hermes (não passam pelo celular)
- ✓ Ligações VoIP são feitas direto pelo Hermes
- ✗ Celular precisa estar ligado E com internet **apenas no momento do pareamento** (QR ou código)
- ✗ Depois de conectado, celular pode ficar offline/desligado

**Conclusão:** Já funciona "sem celular todo tempo". O celular só precisa estar online nos ~10 segundos do pareamento inicial.

---

## Para a campanha: qual usar?

### Para o número novo da campanha (tarefa 0.2 do PLANO.md):

**Recomendação: Código de pareamento**

Motivos:
1. Número comercial pode não ter celular físico dedicado
2. Mais prático para reconectar se a sessão cair
3. Dona pode estar em qualquer lugar (não precisa da câmera)
4. IA do Telegram já tem o fluxo pronto

### Como implementar no painel:

**Opção 1 (rápida):** Usar a IA do Telegram
- Já funciona: `@HermesCallBot criar linha NomeDaLinha +5591988887777`
- IA gera código automaticamente
- Dona digita no WhatsApp

**Opção 2 (ideal):** Adicionar UI no painel web
- Criar formulário em `SessionPairing.tsx`
- Chamar `POST /api/sessions/{sid}/pair-code`
- Mostrar código de 8 dígitos
- Dona digita no WhatsApp

---

## Implementação sugerida

### Para deixar pronto antes da Fase 0:

1. **Decisão:** Qual usar na campanha (QR ou código)?

2. **Se código:**
   - **Via Telegram (0 trabalho):** Já funciona, basta usar
   - **Via painel (3-4 horas):** Adicionar formulário + estado no `SessionPairing.tsx`

3. **Teste:** Criar linha de teste, parear por código, confirmar que ligações funcionam

### Arquivos a modificar (se escolher UI no painel):

```
d:\hermes-call\client\src\components\domain\session\SessionPairing.tsx
  ↓ adicionar toggle QR/código
  ↓ adicionar input de telefone
  ↓ chamar POST /api/sessions/{sid}/pair-code
  ↓ mostrar código retornado
```

Backend não precisa mexer: **já está implementado**.

---

## Resumo executivo

| Pergunta | Resposta |
|---|---|
| Dá para conectar sem escanear QR? | **Sim, por código de 8 dígitos** |
| Já está implementado? | **Sim, no backend e na IA do Telegram** |
| Falta o quê? | **UI no painel web (opcional)** |
| Precisa do celular o tempo todo? | **Não, só nos 10s do pareamento** |
| Emula celular? | **Não, usa Multi-Device (protocolo oficial)** |
| Vale para a campanha? | **Sim, mais prático que QR** |

**Ação recomendada:** Usar pareamento por código para a linha nova da campanha (tarefa 0.2), via Telegram ou adicionando UI no painel.
