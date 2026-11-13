# Como obter números para verificação SMS (obrigatório)

**Data:** 2026-10-26
**Contexto:** o ativador precisa de um número com SMS para registrar no WhatsApp. O número
recebe o código de verificação do WhatsApp e depois fica como aparelho principal (celular virtual).
Para registrar no Redroid da VPS, o chip fica no celular físico do dono e o código é passado manualmente.

---

## TL;DR — o que funciona e o que não funciona

| Método | Funciona? | Por quê |
|---|---|---|
| SMS temporário grátis (receive-smss.com, sms-online.co, freeonlinephone.org, receiveasms.com) | **NÃO** | Números públicos: qualquer um vê as mensagens, Google/WhatsApp bloqueiam por uso excessivo |
| Número descartável pago (5sim.net) | **SIM para WhatsApp** | Número exclusivo por sessão, ~US$0.08–0.37/número, cancela sem cobrar se SMS não chegar |
| Chip pré-pago (operadora) | **SIM** | Número próprio, R$10–20, 100% confiável |
| Celular do dono ou de alguém | **SIM** | Sem custo, mas gasta uma das 2 vagas/ano do Google |
| Telefone fixo + ligação de voz | **SIM para Google/YouTube** | Google aceita ligação de voz; WhatsApp também (opção "voice call") |
| TextNow / Google Voice | **às vezes** | Google e WhatsApp podem recusar; número dos EUA |

---

## 1. O que foi testado e por que falhou (21/10/2026)

### Sites de SMS temporário grátis testados

**sms-online.co** — números UK (+44): listados e acessíveis via curl. Nenhuma mensagem nova chegou
em 3 minutos de monitoramento (números esgotados ou site carrega mensagens por JavaScript).

**receive-sms-online.info** — números Holanda (+31) e Finlândia (+358): acessíveis, mas sem
mensagens visíveis no HTML.

**freeonlinephone.org** — números EUA/Alemanha/UK/Canadá: **único que funcionou para scraping**
(mensagens aparecem no HTML, ex: `receive-sms-online-18645585118.html`). Mensagens de outros
serviços (Netease, Kwai, SoulAPP) apareciam. Porém para Google/WhatsApp os números já estavam
gastos.

**receiveasms.com** — números EUA/BR/Austrália: listados mas página de mensagens carrega via
JavaScript, scraping não funcionou.

### Tentativa de verificação de conta Google

Ao tentar verificar uma conta Google com número de freeonlinephone.org (+1 864-558-5118 e outros):
- Mensagem: **"You have recently made too many attempts. Please try again later."**
- Regra do Google: **máximo 2 contas verificadas por número por ano**
- Números públicos já ultrapassaram esse limite centenas de vezes

### Tentativa de usar proxy Webshare

O bloqueio "too many attempts" fica na **conta**, não no IP. Trocar de IP via proxy não resolve e
piora o risco (IPs de data center são tratados como suspeitos pelo Google).

### Conclusão dos testes

Número público grátis **não funciona** para Google nem para WhatsApp. Ambos limitam uso por número
e reconhecem números de serviços públicos.

---

## 2. O que funciona — procedimento obrigatório

### Para o WhatsApp (ativador)

O ativador precisa de SMS para registrar o número no celular virtual. Opções em ordem de
preferência:

**A) Chip pré-pago do dono (recomendado)**
- Comprar chip (R$10–20), ativar, usar o número no ativador
- O chip fica no celular físico do dono
- O dono recebe o SMS e passa o código (via chat/Telegram/painel)
- Código expira rápido (~18 min) — digitar na hora
- Rate limit: depois de algumas tentativas, WhatsApp pede esperar ~7h
- Alternativa: opção "voice call" (robô liga e fala os 6 dígitos)

**B) Número descartável pago — 5sim.net**
- Preços em dólar (US$), a partir de ~US$0.08/número
- Criar conta, colocar saldo mínimo (US$1 dá para várias tentativas)
- Escolher serviço "WhatsApp" e país
- Se SMS não chegar, cancelar o pedido (não é cobrado)
- **Cuidado:** o número não é do dono — não serve para recuperar a conta depois

Melhores taxas de entrega para WhatsApp (consulta de 21/10/2026):

| País | Preço | Taxa de chegada |
|---|---|---|
| Indonésia | US$0.08 | ~41% |
| Estônia | US$0.18 | ~69% |
| Itália | US$0.37 | ~79% |

**C) API do 5sim (automação futura)**
- Endpoint: `GET https://5sim.net/v1/guest/prices?product=google` (ou `?product=whatsapp`)
- Retorna países, operadoras, preço, quantidade disponível e taxa de entrega (`rate`)
- Com chave de API: comprar número, monitorar SMS, cancelar se não chegar
- Cancelamento sem custo se nenhum SMS chegar antes do timeout

### Para conta Google / verificação YouTube

**A) Celular do dono ou de alguém**
- Cada número verifica até 2 contas Google por ano
- Opção de ligação de voz (telefone fixo serve)

**B) Criar pelo celular Android**
- Configurações > Contas > Adicionar conta > Google
- Muitas vezes o Google **não pede telefone** por esse caminho
- Usar dados móveis do celular (não Wi-Fi de casa, IP marcado)

**C) Número descartável pago — 5sim.net (serviço "Google")**
- Mesmo procedimento acima, escolher serviço "Google"
- Mesma tabela de preços e taxas

**D) Esperar e tentar com IP/navegador limpo**
- Bloqueio "too many attempts" some em horas a 1 dia
- Navegador em modo anônimo + IP diferente pode não pedir telefone

---

## 3. Regras de segurança

- **Nunca escrever número de chip, token, código ou credencial neste arquivo ou nesta pasta**
- Números mascarados nos logs (ex: +55 ** ****-4247)
- Códigos de SMS nunca são registrados
- Se usar 5sim.net: colocar e-mail de recuperação próprio na conta criada imediatamente
- Não usar número descartável pago para contas/canais importantes (sem recuperação futura)

---

## 4. Para o outro agente / próxima sessão

Antes de usar um número no ativador:
1. Confirmar que o celular virtual está pronto (Play Integrity passando — ver `DOCUMENTACAO_registro_whatsapp_redroid.md`)
2. Ter o método de receber SMS definido (chip do dono ou 5sim)
3. Ter quem vai digitar o código de prontidão (código expira em ~18 min)
4. Se rate-limited ("Try again in 7 hours"): usar opção "voice call" ou esperar

Arquivos relacionados:
- `D:\whatsapp-notes\DOCUMENTACAO_registro_whatsapp_redroid.md` — Play Integrity no Redroid
- `D:\whatsapp-notes\progresso.md` — progresso do registro
- `D:\whatsapp-activator2\README.md` — API e fluxo do ativador
- `D:\whatsapp-activator2\AVALIACAO.md` — avaliação dos caminhos possíveis
- `D:\whatsapp-activator2\PROXIMOS_PASSOS.md` — próximos passos do cadastro
