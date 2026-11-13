# Banimento em massa YouTube — 2026-09-04

## O que aconteceu

Em 04/09/2026, o YouTube suspendeu **22 canais brasileiros** simultaneamente.
Motivo oficial: **"violações graves ou repetidas de nossa política contra spam, práticas enganosas e golpes"**.

Os 8 canais internacionais de manhwa (espanhol, francês, hindi, indonésio, inglês, italiano, russo) **não foram afetados**.

## Diagnóstico: por que fomos classificados como spam

O problema **NÃO é o conteúdo das propagandas** (produtos reais). O YouTube detectou o **padrão de comportamento** como rede de spam coordenada:

| Comportamento nosso | Como o YouTube interpreta |
|---|---|
| Postagem 100% automatizada (sem humano no loop) | Bot / spam automatizado |
| Round-robin entre 20+ canais na mesma rede | Rede coordenada de spam |
| Centenas de vídeos por dia distribuídos | Inundação da plataforma |
| Postar até bater `uploadLimitExceeded` (limite real) | Abuso deliberado de quota |
| Shorts de IA muito similares entre si | Conteúdo repetitivo / low-effort |
| Vários canais na mesma conta Google | Uma conta = um operador = rede |
| Títulos/descrições gerados por template | Padrão detectável por ML |
| Postagem em rajada (todos de madrugada) | Padrão não-humano |

## Canais suspensos (22)

| Canal | Email | Status |
|---|---|---|
| fake News ia | andreluizdias384@gmail.com | SUSPENSO |
| fofos e absurdos | murilodoctor192@gmail.com | SUSPENSO |
| Cérebro Digital, Piada Real (2x) | emersongenc@gmail.com / e4487017 | SUSPENSO |
| Emerson AI (2x) | empressinovare@gmail.com / e4487017 | SUSPENSO |
| sintetize risada | (sem email) | SUSPENSO |
| dança e música com ia | e4487017@gmail.com | SUSPENSO |
| Game of thrones kingsroad brasil | (verificar) | SUSPENSO |
| Inovare inteligência artificial (2x) | (verificar) | SUSPENSO |
| energia solar ia | (verificar) | SUSPENSO |
| Vídeos cassetadas ia | (verificar) | SUSPENSO |
| curiosidades e fatos ia | (verificar) | SUSPENSO |
| fala com a IA | (verificar) | SUSPENSO |
| Aulas Ia | (verificar) | SUSPENSO |
| ia brasileira | (verificar) | SUSPENSO |
| IA PRO- Mentoria N8N, Dify, code e + | (verificar) | SUSPENSO |
| Fabio com ia | (verificar) | SUSPENSO |
| Inovare com ia | (verificar) | SUSPENSO |
| Re cenas ia | (verificar) | SUSPENSO |

## Canais com token morto (10)

InovareManhwaVerse, inovaremanhwabr, Inovaremanhwaversethai (2x),
@IAAgora-h3n, @IAAgora-n7h, @UniversoIA-d6s, @IASemLimites-h4b,
@CodigoInteligente-n7j, @MenteArtificial-i5r

## Canais sobreviventes (8) — PROTEGER

1. Animescomia
2. Inovare Manhwa esp
3. inovare Manhwa french
4. Inovaremanhwaversehindi
5. YouTube inovaremanhwaverseind
6. Inovare Manhwa eng
7. inovaremanhwaverseita
8. inovare manhwa verse ru

---

## Passo 1 — Apelar (chances baixas, mas tentar)

Para cada canal suspenso:
1. Fazer login no Google com a conta do canal
2. Acessar https://studio.youtube.com
3. No banner de suspensão, clicar em "Enviar recurso" / "Appeal"
4. Argumentar que o conteúdo promove produtos reais e não configura golpe
5. Aguardar resposta (7-30 dias por canal)

**Nota:** quando a mensagem diz "graves ou repetidas", a taxa de sucesso na apelação é muito baixa (~10-15%). O YouTube pode recusar sumariamente.

## Passo 2 — Mudanças OBRIGATÓRIAS antes de voltar a postar

### 2.1 Limitar volume por canal
```
ANTES:  --limite-canal sem teto, postar até uploadLimitExceeded
DEPOIS: máximo 3-5 vídeos/dia POR CANAL, nunca bater no limite real
```

Implementar no código: `--limite-canal 3` como DEFAULT (não opcional).

### 2.2 Espaçar os posts (anti-rajada)
```
ANTES:  postava todos em sequência rápida (segundos entre uploads)
DEPOIS: intervalo mínimo de 30-60 minutos entre uploads no mesmo canal
```

Implementar: `time.sleep(1800 + random.randint(0, 600))` entre posts no mesmo canal.

### 2.3 NÃO usar round-robin massivo
```
ANTES:  round-robin entre 20+ canais = rede coordenada
DEPOIS: máximo 3-4 canais ativos POR DIA, rodar entre eles ao longo da semana
```

Implementar: selecionar aleatoriamente N canais por dia (não todos).

### 2.4 Variar conteúdo e metadados
```
ANTES:  títulos/tags gerados por template similar
DEPOIS: cada vídeo precisa ter título/descrição ÚNICOS e naturais
```

- Nunca repetir hashtags idênticas entre vídeos
- Descrições longas e variadas (não só "#shorts #ia #viral")
- Thumbnails diferentes (se aplicável)

### 2.5 Simular comportamento humano
```
ANTES:  postagem 100% automatizada às 06:40 todo dia
DEPOIS: horários variados, pausas nos fins de semana, interação manual ocasional
```

- Variar o horário de postagem (entre 8h-22h, nunca madrugada)
- Pular 1-2 dias por semana aleatoriamente
- Fazer alguma atividade "humana" (dar like, comentar, assistir)

### 2.6 Separar contas Google
```
ANTES:  vários canais na mesma conta Google (mesmo clientId/clientSecret)
DEPOIS: 1 canal por conta Google, OAuth projects separados
```

O YouTube detecta que o mesmo projeto OAuth controla múltiplos canais = rede coordenada.
Todos os canais usavam o mesmo `clientId` (`43266821547-...`), o que facilitou a detecção.

### 2.7 Conteúdo de valor
```
ANTES:  Shorts de IA genéricos + propaganda
DEPOIS: conteúdo original com valor real, propaganda natural/orgânica
```

- Vídeos mais longos (não só Shorts)
- Descrições educativas
- Engajamento real na comunidade

## Passo 3 — Implementações no código

### postar_tudo_hoje.py — mudanças necessárias:

1. **DEFAULT `--limite-canal 3`** (hoje é None = infinito)
2. **Sleep entre posts** do mesmo canal (30-60 min)
3. **Max canais ativos por dia** (3-4, não todos)
4. **Jitter nos horários** (não postar tudo às 06:40)
5. **Detector de "esquentamento"** — se 2+ canais derem erro no mesmo dia, PARAR tudo
6. **Log de frequência** — registrar quantos posts/canal/semana e alertar se passar de 5/dia

### youtube_poster.py — mudanças necessárias:

1. **Projetos OAuth separados** por canal (cada canal com seu clientId)
2. **User-Agent variado** (hoje usa o default do urllib)
3. **IP rotation** (se possível, postar de IPs diferentes)

## Resumo de prioridades

| Prioridade | Ação | Impacto |
|---|---|---|
| URGENTE | Apelar os 22 canais | Recuperar (se der) |
| URGENTE | Proteger os 8 sobreviventes (limite conservador) | Evitar perder os últimos |
| ALTA | Separar OAuth projects | Desassociar canais entre si |
| ALTA | Implementar delays e limites | Parecer humano |
| MÉDIA | Variar metadados | Evitar detecção de template |
| MÉDIA | Jitter de horários | Parecer orgânico |
| BAIXA | Contas Google separadas | Longo prazo |
