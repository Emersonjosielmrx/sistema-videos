# Automação de ativação do WhatsApp no Hermes — Especificação técnica

Escrito em 07/10/2026. Plano para adicionar ativação automática de número novo dentro do Hermes, usando emulador temporário.

---

## Objetivo

**Fluxo desejado no painel:**

```
Usuário clica: "Adicionar linha nova"
  ↓
[Input: Número +55 91 98888-7777]
[Botão: Ativar automaticamente]
  ↓
Backend:
  1. Cria emulador Android temporário (headless)
  2. Instala WhatsApp
  3. Insere número
  4. **Usuário recebe SMS** no chip (fora do sistema)
  5. [Input no painel: Código SMS recebido]
  6. Backend insere código no emulador
  7. WhatsApp ativa
  8. Gera código de pareamento (8 dígitos)
  9. Pareia com whatsmeow
  10. **Desliga e deleta emulador**
  ↓
Linha funcionando no Hermes
```

**Vantagens:**
- Tudo dentro do sistema
- Emulador só existe por ~2 minutos
- Não consome recursos depois
- Escalável: automatiza o processo manual

---

## Arquitetura proposta

### 1. Componentes necessários

```
┌─────────────────────────────────────────────────────┐
│ HERMES BACKEND (Go)                                 │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ ActivationService (novo)                     │  │
│  │ - CreateEmulator()                           │  │
│  │ - InstallWhatsApp()                          │  │
│  │ - InputPhoneNumber()                         │  │
│  │ - InputSMSCode()                             │  │
│  │ - GeneratePairingCode()                      │  │
│  │ - PairWithWhatsmeow()                        │  │
│  │ - CleanupEmulator()                          │  │
│  └──────────────────────────────────────────────┘  │
│              ↓                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ EmulatorManager (abstração)                  │  │
│  │ - Start/Stop/Delete                          │  │
│  │ - ADB commands                               │  │
│  │ - Screenshot/UI automation                   │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
               ↓ executa comandos
┌─────────────────────────────────────────────────────┐
│ DOCKER CONTAINER (Android x86)                      │
│ - Android 11+ headless                              │
│ - Dura 2-5 minutos                                  │
│ - Deletado após ativação                            │
└─────────────────────────────────────────────────────┘
```

### 2. Stack de automação

**Opção A: ADB + UI Automator (mais simples)**
```go
// Comandos ADB direto do Go
cmd := exec.Command("adb", "-s", emulatorID, "shell", 
    "am start -n com.whatsapp/.Main")
```

**Opção B: Appium (mais robusto)**
- Framework de automação de UI
- API em Go disponível
- Mais estável para mudanças de interface

**Recomendação inicial: ADB direto** (menos dependências)

### 3. Emulador

**Opção A: Android x86 em Docker**
```dockerfile
FROM budtmo/docker-android:emulator_11.0
# Imagem pronta com Android emulado
# Headless (sem display)
# ~2GB de RAM por instância
```

**Opção B: Genymotion Cloud (pago)**
- Mais rápido
- API REST
- Custo: ~$0.10 por hora

**Recomendação: Docker Android x86** (gratuito, controle total)

---

## Fluxo técnico detalhado

### Fase 1: Criar emulador temporário

```go
// cmd/server/activation_service.go (novo arquivo)

type ActivationService struct {
    docker *client.Client
    log    *slog.Logger
}

func (s *ActivationService) StartActivation(phone string) (*ActivationSession, error) {
    // 1. Cria container Docker com Android
    containerID, err := s.createEmulator()
    if err != nil {
        return nil, err
    }
    
    // 2. Espera emulador iniciar (~30-60s)
    if err := s.waitForBoot(containerID); err != nil {
        s.cleanupEmulator(containerID)
        return nil, err
    }
    
    // 3. Instala WhatsApp APK
    if err := s.installWhatsApp(containerID); err != nil {
        s.cleanupEmulator(containerID)
        return nil, err
    }
    
    return &ActivationSession{
        ID:          uuid.New().String(),
        ContainerID: containerID,
        Phone:       phone,
        State:       "awaiting_sms",
    }, nil
}
```

### Fase 2: Inserir número e aguardar SMS

```go
func (s *ActivationService) InputPhoneNumber(sessionID, phone string) error {
    sess := s.getSession(sessionID)
    
    // Abre WhatsApp
    s.adbShell(sess.ContainerID, "am start -n com.whatsapp/.Main")
    time.Sleep(2 * time.Second)
    
    // Clica em "Concordar e continuar" (coordenadas ou texto)
    s.adbTap(sess.ContainerID, 540, 1800)
    time.Sleep(1 * time.Second)
    
    // Insere número (via input text)
    s.adbInput(sess.ContainerID, phone)
    
    // Clica "Próximo"
    s.adbTap(sess.ContainerID, 540, 1900)
    
    // Estado: aguardando SMS
    sess.State = "awaiting_sms"
    return nil
}
```

### Fase 3: Usuário recebe SMS no chip físico

**Importante:** O SMS **não chega no emulador**, chega no chip físico que o usuário tem.

**No painel web:**
```tsx
// Frontend mostra:
"📱 Código SMS enviado para +55 91 98888-7777"
"Digite o código de 6 dígitos:"
[Input: ______]
[Botão: Confirmar]
```

### Fase 4: Inserir código SMS no emulador

```go
func (s *ActivationService) InputSMSCode(sessionID, code string) error {
    sess := s.getSession(sessionID)
    
    // Foca no campo de código (se não estiver focado)
    s.adbTap(sess.ContainerID, 540, 1200)
    
    // Digita código de 6 dígitos
    s.adbInput(sess.ContainerID, code)
    
    // WhatsApp ativa automaticamente após digitar
    time.Sleep(3 * time.Second)
    
    sess.State = "activated"
    return nil
}
```

### Fase 5: Gerar código de pareamento

```go
func (s *ActivationService) GeneratePairingCode(sessionID string) (string, error) {
    sess := s.getSession(sessionID)
    
    // No WhatsApp ativado, vai em:
    // Menu (3 pontos) → Aparelhos conectados → Conectar com número
    
    s.adbTap(sess.ContainerID, 650, 100)  // Menu
    time.Sleep(1 * time.Second)
    s.adbTap(sess.ContainerID, 540, 600)  // "Aparelhos conectados"
    time.Sleep(1 * time.Second)
    s.adbTap(sess.ContainerID, 540, 1800) // "Conectar com número"
    time.Sleep(1 * time.Second)
    
    // Captura screenshot e extrai código via OCR
    screenshot := s.adbScreenshot(sess.ContainerID)
    code := s.extractCodeFromImage(screenshot) // OCR ou reconhecimento de texto
    
    return code, nil
}
```

### Fase 6: Parear com whatsmeow

```go
func (s *ActivationService) PairWithWhatsmeow(sessionID, phone string) error {
    sess := s.getSession(sessionID)
    
    // Já temos o código de pareamento
    code := sess.PairingCode
    
    // Usa a função que já existe no Hermes
    sessionManager := s.hermes.sessions
    hermesSessionID, err := sessionManager.New(sess.UserID, "Linha "+phone)
    if err != nil {
        return err
    }
    
    // Inicia pareamento por código (função que já existe!)
    // O usuário NÃO precisa digitar o código, o backend faz automaticamente
    actualCode, err := sessionManager.PairPhone(hermesSessionID, phone)
    if err != nil {
        return err
    }
    
    // Verifica se o código bate
    if actualCode != code {
        return fmt.Errorf("código diverge: esperado %s, recebido %s", code, actualCode)
    }
    
    // Aguarda pareamento completar
    if err := s.waitForPairing(hermesSessionID, 30*time.Second); err != nil {
        return err
    }
    
    sess.State = "paired"
    return nil
}
```

### Fase 7: Limpar emulador

```go
func (s *ActivationService) Cleanup(sessionID string) error {
    sess := s.getSession(sessionID)
    
    // Para e deleta container Docker
    ctx := context.Background()
    if err := s.docker.ContainerStop(ctx, sess.ContainerID, nil); err != nil {
        s.log.Warn("erro ao parar container", "id", sess.ContainerID, "err", err)
    }
    if err := s.docker.ContainerRemove(ctx, sess.ContainerID, 
        types.ContainerRemoveOptions{Force: true}); err != nil {
        return err
    }
    
    delete(s.sessions, sessionID)
    return nil
}
```

---

## API REST proposta

```http
# 1. Inicia ativação
POST /api/activation/start
Body: {"phone": "+5591988887777"}
Response: {"session_id": "act_abc123", "state": "creating_emulator"}

# 2. Status (polling)
GET /api/activation/:session_id
Response: {
  "session_id": "act_abc123",
  "state": "awaiting_sms",  # ou: creating_emulator, awaiting_sms, activated, paired, error
  "phone": "+5591988887777",
  "error": null
}

# 3. Inserir código SMS
POST /api/activation/:session_id/sms-code
Body: {"code": "123456"}
Response: {"state": "activated"}

# 4. Finalizar (parear e limpar)
POST /api/activation/:session_id/finalize
Response: {
  "hermes_session_id": "sess_xyz789",
  "paired": true,
  "cleanup_done": true
}
```

---

## Frontend (React)

```tsx
// ActivationWizard.tsx (novo componente)

export const ActivationWizard = () => {
  const [step, setStep] = useState<"phone" | "sms" | "pairing" | "done">("phone");
  const [sessionId, setSessionId] = useState("");
  const [phone, setPhone] = useState("");
  const [smsCode, setSmsCode] = useState("");
  
  const startActivation = async () => {
    const res = await fetch("/api/activation/start", {
      method: "POST",
      body: JSON.stringify({phone})
    });
    const data = await res.json();
    setSessionId(data.session_id);
    setStep("sms");
    
    // Polling do status
    pollStatus(data.session_id);
  };
  
  const submitSMSCode = async () => {
    await fetch(`/api/activation/${sessionId}/sms-code`, {
      method: "POST",
      body: JSON.stringify({code: smsCode})
    });
    setStep("pairing");
    
    // Finaliza (pareia e limpa)
    const res = await fetch(`/api/activation/${sessionId}/finalize`, {
      method: "POST"
    });
    const data = await res.json();
    
    setStep("done");
    // Redireciona para a sessão nova
    navigate(`/sessions/${data.hermes_session_id}`);
  };
  
  return (
    <Card>
      {step === "phone" && (
        <>
          <h2>Ativar número novo</h2>
          <Input 
            placeholder="+55 91 98888-7777" 
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <Button onClick={startActivation}>
            Iniciar ativação automática
          </Button>
        </>
      )}
      
      {step === "sms" && (
        <>
          <h2>Código SMS</h2>
          <p>Um SMS foi enviado para <b>{phone}</b></p>
          <p>Digite o código de 6 dígitos:</p>
          <Input 
            placeholder="123456" 
            value={smsCode}
            onChange={(e) => setSmsCode(e.target.value)}
          />
          <Button onClick={submitSMSCode}>Confirmar</Button>
        </>
      )}
      
      {step === "pairing" && (
        <>
          <Loader2 className="animate-spin" />
          <p>Pareando com o Hermes...</p>
        </>
      )}
      
      {step === "done" && (
        <>
          <CheckCircle className="text-green-500" />
          <h2>Linha ativada!</h2>
          <p>{phone} está pronto para usar.</p>
        </>
      )}
    </Card>
  );
};
```

---

## Dependências e requisitos

### 1. Docker

```bash
# No servidor Hermes
apt-get install docker.io
systemctl enable docker
```

### 2. Imagem Android

```bash
# Puxa imagem (uma vez, ~2GB)
docker pull budtmo/docker-android:emulator_11.0
```

### 3. WhatsApp APK

```bash
# Baixa APK oficial (armazena localmente)
# Versão estável conhecida
wget https://www.whatsapp.com/android/current/WhatsApp.apk
# Ou usa F-Droid / APKMirror
```

### 4. Biblioteca Go para Docker

```go
// go.mod
require (
    github.com/docker/docker v24.0.0+incompatible
    github.com/docker/go-connections v0.4.0
)
```

### 5. OCR (opcional, para extrair código)

```bash
# Tesseract OCR
apt-get install tesseract-ocr

# Ou usa screenshot + análise de posição fixa
```

---

## Estimativa de recursos

### Por ativação:

| Recurso | Quantidade | Duração |
|---|---|---|
| RAM | 2 GB | 2-5 minutos |
| CPU | 2 cores | 2-5 minutos |
| Disco | 500 MB temporário | deletado após |
| Tempo total | - | ~3 minutos |

### Escalabilidade:

- **Sequencial:** 1 ativação por vez (mais simples)
- **Paralelo:** Até N simultâneas (requer mais recursos)
- **Para campanha:** 1-3 linhas = sequencial é suficiente

---

## Riscos e mitigações

| Risco | Probabilidade | Mitigação |
|---|---|---|
| WhatsApp muda interface | Média | Coordenadas fixas + fallback manual |
| Emulador não inicia | Baixa | Timeout e retry, logs detalhados |
| SMS não chega | Baixa | Usuário pode reenviar, timeout de 5 min |
| Pareamento falha | Baixa | Rollback: deleta emulador e sessão |
| Container fica órfão | Baixa | Cleanup automático após timeout |

---

## Fases de implementação

### Fase 1: Prova de conceito (1-2 dias)
- Script bash manual
- Docker run + ADB commands
- Ativa 1 número do começo ao fim
- **Objetivo:** Validar que funciona

### Fase 2: Backend Go (3-4 dias)
- `activation_service.go`
- API REST
- Gerenciamento de sessões
- Cleanup automático

### Fase 3: Frontend (2-3 dias)
- Wizard de ativação
- Polling de status
- Input de código SMS
- UX polida

### Fase 4: Produção (1-2 dias)
- Logs e monitoramento
- Rate limiting (1 ativação por vez)
- Documentação
- Testes com números reais

**Total estimado: 7-11 dias de desenvolvimento**

---

## Alternativa mais simples (MVP)

Se 7-11 dias é muito para a campanha sair:

### **Script semi-automatizado**

```bash
#!/bin/bash
# ops/ativar-numero.sh

PHONE=$1

echo "Iniciando ativação de $PHONE..."

# 1. Cria emulador
CONTAINER=$(docker run -d --rm \
  -e EMULATOR_DEVICE="Samsung Galaxy S10" \
  -p 5555:5555 \
  budtmo/docker-android:emulator_11.0)

echo "Emulador criado: $CONTAINER"
echo "Aguardando boot..."
sleep 60

# 2. Instala WhatsApp
adb -s localhost:5555 install WhatsApp.apk
sleep 5

# 3. Abre WhatsApp
adb -s localhost:5555 shell am start -n com.whatsapp/.Main
sleep 3

echo "WhatsApp aberto. Ações manuais:"
echo "1. Clique em 'Concordar e continuar'"
echo "2. Digite o número: $PHONE"
echo "3. Clique 'Próximo'"
echo ""
read -p "Aperte ENTER após receber o SMS..."

echo "Digite o código SMS de 6 dígitos:"
read SMS_CODE

# 4. Insere código (via ADB)
adb -s localhost:5555 shell input text $SMS_CODE

echo "Código inserido. Aguardando ativação..."
sleep 10

# 5. Gera código de pareamento (manual por enquanto)
echo "No emulador, vá em: Menu → Aparelhos conectados → Conectar com número"
echo "Digite o código de 8 dígitos aqui:"
read PAIR_CODE

# 6. Pareia no Hermes (via curl ou Telegram)
curl -X POST http://localhost:8080/api/activation/pair \
  -d "{\"phone\": \"$PHONE\", \"code\": \"$PAIR_CODE\"}"

echo "Pareamento concluído!"

# 7. Limpa
docker stop $CONTAINER
echo "Emulador removido. Linha $PHONE ativa!"
```

**Uso:**
```bash
bash ops/ativar-numero.sh +5591988887777
```

**Vantagem:** 1 dia de trabalho
**Desvantagem:** Alguns passos ainda manuais, mas muito mais rápido que fazer tudo manual

---

## Recomendação

### Para começar a campanha rápido:

**Opção 1: Manual (0 trabalho, 10 min por linha)**
- Celular físico
- Ativa WhatsApp
- Pareia via Telegram

**Opção 2: Script semi-automatizado (1 dia, 5 min por linha)**
- Script bash acima
- Automatiza 70% do processo
- Alguns cliques ainda manuais

**Opção 3: Totalmente automatizado (7-11 dias, 3 min por linha, zero interação)**
- Sistema completo no painel
- Um clique, tudo automático
- Vale se vai ativar 10+ linhas

### Para a tarefa 0.2 (1 linha nova):

**Faça manual.** Não vale gastar 7 dias para economizar 10 minutos.

### Para escalar (Fase 3+, 10+ linhas):

**Aí sim vale automatizar.** Economiza horas e evita erros.

---

## Próximos passos

**Decisão necessária:**
1. Quantas linhas você pretende ativar? (1-3 ou 10+?)
2. Quando precisa da primeira linha? (urgente ou pode esperar desenvolvimento?)
3. Prefere fazer manual agora ou esperar automação?

**Se escolher desenvolver:**
1. Criar branch `feature/auto-activation`
2. Implementar Fase 1 (POC) em `ops/ativar-numero.sh`
3. Testar com 1 número descartável
4. Se funcionar, evoluir para Fase 2-4

**Arquivos a criar:**
```
d:\hermes-call\
  cmd\server\
    activation_service.go       (novo)
    activation_handlers.go      (novo)
  ops\
    ativar-numero.sh           (novo, POC)
  client\src\components\
    activation\
      ActivationWizard.tsx     (novo)
```
