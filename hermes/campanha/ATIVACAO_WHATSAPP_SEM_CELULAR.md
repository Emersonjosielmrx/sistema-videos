# Ativação inicial do WhatsApp sem celular — Análise

Escrito em 07/10/2026. Investigação sobre registrar número no WhatsApp pela primeira vez direto no Hermes, sem celular físico nem emulador.

---

## O problema

**Hoje:** Para cada linha no Hermes é preciso:
1. Ter o WhatsApp instalado em um celular (físico ou emulado)
2. Ativar o número lá (receber SMS, confirmar)
3. Depois parear o Hermes como dispositivo secundário (QR ou código)

**O que você quer:** Comprar chip → colocar número no Hermes → receber SMS de ativação → usar direto, sem celular/emulador.

---

## Por que não funciona: Protocolo Multi-Device

O **whatsmeow** (biblioteca que o Hermes usa) implementa o protocolo **Multi-Device do WhatsApp**.

### Limitação fundamental:

O protocolo Multi-Device **não permite registro de dispositivo primário**. Ele só permite:
- ✓ Conectar dispositivos **secundários** a uma conta existente
- ✗ Ativar um número novo pela primeira vez

### Como funciona o Multi-Device:

```
┌─────────────────────────────────────────┐
│ DISPOSITIVO PRIMÁRIO (obrigatório)      │
│ - Celular com WhatsApp instalado        │
│ - Recebe SMS de ativação                │
│ - Tem o número registrado               │
│ - Pode estar offline depois de conectar │
└─────────────────────────────────────────┘
              │
              │ gera QR/código
              │
              ▼
┌─────────────────────────────────────────┐
│ DISPOSITIVOS SECUNDÁRIOS (até 4)        │
│ - WhatsApp Web                          │
│ - WhatsApp Desktop                      │
│ - Hermes Call (via whatsmeow)           │
│ - Outros apps usando a API              │
└─────────────────────────────────────────┘
```

**Conclusão:** O protocolo Multi-Device **exige** que o número seja ativado primeiro em um celular. Não há como pular essa etapa.

---

## Alternativas investigadas

### 1. WhatsApp Business API oficial (pago)

**O que é:**
- API oficial do Meta para empresas
- Permite registro via SMS sem celular
- Usada por CRMs, ERPs, plataformas de atendimento

**Problemas:**
- **Custo alto:** USD 50-100+ por mês por número
- **Aprovação lenta:** 1-3 semanas para aprovar conta
- **Limitações:** Não permite ligações VoIP (só mensagens)
- **Não resolve:** Hermes precisa de ligações, não só mensagens

### 2. Emuladores Android (o que você já faz)

**Atual:**
- Android emulado (BlueStacks, Genymotion, etc)
- Instala WhatsApp
- Recebe SMS
- Ativa número
- Depois pareia com Hermes

**Problemas que você citou:**
- Precisa de emulador rodando
- Um emulador por número
- Consome recursos
- Precisa manter online para parear

### 3. Bibliotecas não-oficiais que alegam fazer registro primário

**Risco altíssimo:**
- WhatsApp bane contas que usam métodos não-oficiais
- Bibliotecas desatualizadas (protocolo muda frequente)
- Sem garantia de funcionar
- Pode perder o número permanentemente

---

## Por que o emulador é necessário

### O WhatsApp **exige dispositivo primário** porque:

1. **Segurança:** Vincular número a dispositivo físico dificulta fraude
2. **Verificação de identidade:** SMS vai para o chip, que está no celular
3. **Prevenção de spam:** Limita automação em massa
4. **Modelo de negócio:** WhatsApp Business API paga é a alternativa oficial

### Não há como contornar legalmente

Toda solução legítima passa por:
- **Celular físico** (um por número), ou
- **Emulador Android** (um por número), ou
- **WhatsApp Business API** (caro, sem ligações)

---

## Otimizações possíveis com emulador

Se o problema é **escalar vários números**, há formas de otimizar:

### 1. Emulador headless (sem interface gráfica)

**Vantagem:** Consome muito menos recursos
**Ferramentas:**
- Android x86 em VM leve
- Genymotion Cloud (pago)
- Anbox (Linux containers)

**Processo:**
1. Cria emulador headless
2. Ativa WhatsApp via automação (recebe SMS, confirma)
3. Gera QR/código de pareamento
4. Conecta no Hermes
5. **Desliga o emulador** (não precisa ficar ligado)

### 2. Script de ativação automática

Automatizar o processo:
```bash
# Pseudo-código
criar_emulador(numero)
instalar_whatsapp()
receber_sms(numero)
ativar_whatsapp(codigo_sms)
gerar_codigo_pareamento()
conectar_hermes(codigo)
desligar_emulador()
```

### 3. Serviço de ativação (terceirizado)

**Existem serviços que:**
- Você manda o número
- Eles ativam em emulador deles
- Devolvem QR/código de pareamento
- Você conecta no Hermes

**Custo:** ~R$ 5-10 por ativação
**Risco:** Confiar o número a terceiros

### 4. Um celular físico para múltiplas ativações

**Processo:**
1. Celular físico com WhatsApp
2. Ativa número novo
3. Gera código de pareamento
4. Conecta no Hermes
5. **Faz logout do celular**
6. Ativa próximo número no mesmo celular

**Vantagem:** Um celular serve para todos os números (sequencialmente)
**Limitação:** Um por vez, mas não precisa comprar vários celulares

---

## Recomendação para a campanha

### Para o número novo da campanha (tarefa 0.2):

**Opção 1: Celular físico (mais simples)**
- Compra chip
- Coloca em celular comum
- Ativa WhatsApp
- Gera código de pareamento
- Conecta no Hermes via Telegram (`@HermesCallBot criar linha +55...`)
- Guarda o celular (não precisa mais, só para reativar se perder sessão)

**Opção 2: Emulador leve (se vai escalar)**
- Cria VM Android headless
- Script de ativação automatizada
- Desliga depois de parear
- Mais trabalho inicial, mas escala

### Para escalar (Fase 3+):

**Se chegar a 10+ números:**
1. Considerar WhatsApp Business API (se Meta liberar ligações)
2. Ou manter emuladores headless automatizados
3. Ou serviço de ativação terceirizado

**Mas para começar (1-3 números):**
- Celular físico é mais simples e confiável
- Custo baixo (R$ 200-300 por celular usado)
- Sem risco de ban
- Sem complexidade

---

## Resposta direta à sua pergunta

> "eu quero comprar o chip e colocar o numero no hermes call ele manda a mensagem via sms pra ligar ao whatsapp"

**Não é possível** pelas seguintes razões técnicas:

1. **Protocolo Multi-Device não suporta:** O whatsmeow (e qualquer biblioteca que use o protocolo oficial) **não consegue fazer registro primário**. O protocolo foi desenhado para dispositivos secundários.

2. **WhatsApp não permite:** A API do WhatsApp **exige** que o número seja ativado em um app oficial (Android/iOS) antes de parear outros dispositivos.

3. **SMS de ativação:** O código SMS precisa ser inserido no **app do WhatsApp** (Android/iOS). Não há endpoint na API que aceite o código SMS diretamente.

4. **Única exceção:** WhatsApp Business API oficial, que:
   - Permite registro sem celular
   - Mas não permite ligações VoIP
   - E custa caro por mês

### Então preciso do emulador/celular?

**Sim, mas só uma vez por número:**
1. Ativa o número no emulador/celular
2. Pareia com o Hermes (código de 8 dígitos)
3. **Desliga o emulador/celular** (não precisa mais)
4. Hermes funciona sozinho dali em diante
5. Só precisa religar se perder a sessão (raro)

### O emulador fica ligado o tempo todo?

**Não!** Depois de parear:
- Hermes é dispositivo secundário **independente**
- Mensagens chegam direto no Hermes
- Ligações funcionam direto no Hermes
- Emulador pode ficar desligado
- Só precisa ligar de novo se a sessão expirar (anos sem usar)

---

## Conclusão técnica

**Não há solução legítima** para ativar WhatsApp sem celular/emulador e ainda ter ligações VoIP.

**O que você pode otimizar:**
1. Usar celular físico para parear (mais simples que emulador)
2. Desligar o celular depois de parear (não precisa ficar ligado)
3. Um celular serve para ativar vários números (sequencialmente)
4. Emulador headless se quiser automatizar (mais complexo)

**Para a campanha:**
- Tarefa 0.2 pede "número novo só da campanha"
- Opção mais simples: chip em celular comum, ativa, pareia, guarda o celular
- Custo: ~R$ 20 (chip) + celular usado que você já tem
- Tempo: 10 minutos

**Limitação do protocolo, não do Hermes.** Qualquer sistema que use WhatsApp para ligações tem o mesmo requisito.

---

## Fontes técnicas

Esta análise foi baseada em:
- Código do whatsmeow no Hermes (`session.go`, `sessionmanager.go`)
- Documentação do protocolo Multi-Device do WhatsApp
- Limitações conhecidas da API não-oficial

Para dúvidas técnicas sobre o protocolo, comunidade whatsmeow: https://matrix.to/#/#whatsmeow:maunium.net
