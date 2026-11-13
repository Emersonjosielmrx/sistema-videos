# PADRAO_DOC_POSTAGEM — SEO Otimizado para Recaps de Anime (YouTube PT-BR)

> Dados extraídos dos 16 maiores recaps de anime/manhwa em PT-BR (2M-8.7M views).
> Atualizado: 2026-08-24.

---

## 1. TÍTULO (máx 100 chars)

### Fórmula que funciona (60%+ dos tops usam):

```
[Ele/Garoto/Homem] [SITUAÇÃO RUIM em CAPS] [mas/e] [RESULTADO ABSURDO em CAPS] - Recap Anime
```

### Padrões validados por views:

| Padrão | Exemplo Real (canal / views) |
|--------|------------------------------|
| **A: Fraco → Forte** | "Um PERDEDOR Intimidado Vai Para Outro Mundo e Volta Com Uma Habilidade de Nivel Deus" (Mattz / 6.1M) |
| **B: RESUMÃO + obra** | "RESUMO DE ONE PIECE ATE O CAPITULO 1000!" (Chapéus de Palha / 4.1M) |
| **C: Vingança** | "TIRARAM TUDO OQUE ELE TINHA E AGORA ELE VAI ATRAS DE VINGANCA!" (Otakunelas / 2.7M) |
| **D: Nasceu com poder** | "Garotinho NASCEU com 7 BENÇOES DIVINAS e todos seus ATRIBUTOS MAXIMIZADOS" (NoteLey / 8.7M) |
| **E: Reencarnação** | "LORDE DEMONIO Reencarna depois de 2000 ANOS com UM PODER ABSOLUTO" (Tio San / 2.4M) |

### Regras do título:
1. **CAPS LOCK seletivo** nas palavras-chave de impacto: PERDEDOR, LIXO, NASCEU, VINGANÇA, DEUS, FRACO, PODER
2. **NÃO usar nome real do anime** no título (copyright strike) — descrever o enredo
3. **1-2 emojis max** (🔥 ⚡ 😱) — os tops brasileiros usam pouco ou nenhum emoji
4. **Sufixo identificador**: "- Recap Anime" ou "- Resumo Completo" ou "(1-12)"
5. **Adaptar do original**: pegar o título do vídeo-fonte (que já tem views) e traduzir/adaptar pra PT-BR

### Palavras-chave que MAIS aparecem nos tops:
```
NASCEU, Mais Forte, Mais Fraco, Skill, Habilidade, Poder, Nível Deus,
Rank SS, Absoluto, Reencarna, VINGANÇA, Resumo Completo, RESUMÃO,
LIXO, PERDEDOR, Descartado, Outro Mundo
```

### Templates prontos (copiar e adaptar):

```python
TEMPLATES_TITULO = [
    "Ele Foi Chamado de LIXO Até Despertar o PODER Mais Forte do Mundo",
    "Ele NASCEU Fraco Mas Se Tornou o Guerreiro MAIS FORTE de Todos",
    "TODOS Riram Dele Até Ele Mostrar Seu Verdadeiro PODER",
    "Garoto REJEITADO Renasceu Com Uma HABILIDADE de Nível DEUS",
    "Ele PERDEU Tudo e Voltou Com o PODER ABSOLUTO",
    "NINGUÉM Acreditava Nele Até Ele Se Tornar INDESTRUTÍVEL",
    "O MAIS FRACO Recebeu Um PODER Secreto e Surpreendeu a Todos",
    "Ele Era DESCARTADO Até Ganhar a SKILL Mais Rara do Mundo",
    "Após Ser TRAÍDO Ele Voltou 1000x MAIS FORTE Para Se Vingar",
    "O Garoto Que TODOS Desprezavam Se Tornou o LORDE Mais Temido",
]
```

---

## 2. TAGS (máx 30 — campo oculto do YouTube)

### Base obrigatória (24 tags — usar em TODOS os recaps):

```python
TAGS_ANIME = [
    # Core nicho
    "anime", "recap anime", "anime recap", "resumo anime",
    "anime recap portugues", "recap anime pt-br", "anime pt-br",
    "resumo de anime", "anime recap completo",
    # Gênero
    "isekai", "anime isekai", "anime ação", "anime magia",
    "anime fantasia", "reencarnação anime",
    # Formato
    "recap completo", "resumo completo", "anime dublado",
    "anime em português", "anime legendado",
    # Trending geral
    "animes 2025", "animes 2026", "anime novo",
    # Typos propositais (captura buscas erradas)
    "animê", "anine",
]
```

### Tags dinâmicas (+6, completar até 30):

```python
# Adicionar baseado no conteúdo:
# - Gênero detectado: "anime romance", "anime terror", "anime comédia"
# - Tema: "herói rejeitado", "poder oculto", "reencarnação"
# - Adaptação: slug do título original (sem nome da obra)
# - Formato: "recap longo", "resumão anime"
```

### Estratégia: incluir erros de digitação propositais
Os canais grandes (Otakunelas, Recap-kun) incluem typos como tags:
```
"manha", "anine", "animê", "recapp", "resumão"
```

---

## 3. DESCRIÇÃO (máx 5000 chars)

### Estrutura padrão (75%+ dos tops usam):

```
[2-3 frases de sinopse dramática SEM nome da obra — copiar/adaptar do original]

Nome da obra: nos comentários 📌

⏱ Capítulos:
00:00 — Introdução
[timestamps se aplicável]

🔔 INSCREVA-SE e ative o sininho para mais recaps!
💬 Comenta o que achou!
❤️ Deixa o LIKE se curtiu!

━━━━━━━━━━━━━━━━━━━━━━━
🏷 TAG:
anime, recap anime, resumo anime, anime recap portugues, anime pt-br,
anime isekai, anime ação, recap completo, anime dublado, resumo completo,
[+15 keywords separadas por vírgula]

#anime #animerecap #recap #isekai #ação
```

### Truques testados e comprovados:
1. **"Nome da obra: nos comentários"** — evita claim de copyright
2. **Timestamps** — YouTube promove vídeos com marcadores de tempo (aparecem como capítulos)
3. **Bloco TAG na descrição** — 20-30 keywords em texto DENTRO da descrição (além das tags ocultas)
4. **Sinopse em 3ª pessoa dramática** sem revelar o nome — descrever o enredo
5. **CTA triplo** (inscreva + comente + like) no final antes das tags

---

## 4. HASHTAGS (3-5 no título/descrição)

### Fixas (SEMPRE usar):
```
#anime #animerecap #recap
```

### Rotativas (escolher 2 por vídeo):
```
#isekai #ação #magia #reencarnado #resumoanime
#animebr #animerecapbr #manhwa #resumomanhwa
```

---

## 5. ESTRATÉGIA: COPIAR SEO DO VÍDEO ORIGINAL

Como nossos vídeos-fonte já são selecionados por MAIS VIEWS (via `anime_discover.py`),
a metadata do original já é otimizada. A estratégia:

### 5.1. Dados disponíveis do original:
- **Título**: salvo no nome da pasta (`{video_id}_{slug_titulo}`)
- **Views**: retornado pelo discover
- **URL**: `https://www.youtube.com/watch?v={video_id}`

### 5.2. Pipeline de SEO (implementar no `postar_animes.py`):

```
1. Extrair título original do nome da pasta
2. yt-dlp --print "%(title)s\x1f%(description)s\x1f%(tags)s" URL
   → captura título, descrição e tags REAIS do original
3. Traduzir título pra PT-BR (se não for)
4. Adaptar pro template viral (Padrão A-E acima)
5. Mesclar tags do original + TAGS_ANIME base
6. Gerar descrição com sinopse adaptada do original
7. Aplicar anti_ban() em TUDO (título + descrição + tags)
```

### 5.3. Extrair metadata do original via yt-dlp:
```bash
yt-dlp --skip-download --print "%(title)s" --print "%(description)s" \
       --print "%(tags)s" "https://www.youtube.com/watch?v=VIDEO_ID"
```

---

## 6. ANTI-BAN (obrigatório)

O `viralizador.py` tem 211 regras regex que trocam termos de risco.
**Aplicar `anti_ban()` em:**
- Título
- Descrição
- Tags (cada tag individual)

Termos que NUNCA devem aparecer no título/descrição:
- Nomes de obra com copyright
- Palavras +18 (sangue, morte, etc → o anti_ban já troca)
- "Hentai", "ecchi", "nudez" → substituídos automaticamente

---

## 7. CONFIGURAÇÃO YOUTUBE

```json
{
  "category": "24",
  "made_for_kids": false,
  "language": "pt-BR",
  "privacy": "public"
}
```

- Categoria **24 = Entertainment** (testada; Film & Animation = 1 também funciona)
- **Nunca** marcar como "feito pra crianças" (recap de anime tem violência leve)

---

## 8. CANAIS E ROTAÇÃO

```python
CANAIS = [
    "repost canalanimescomia",
    "YouTube inovaremanhwaverseesp"
]
```

Rotação round-robin por vídeo. Se um canal bloquear (uploadLimitExceeded), tentar o próximo.

---

## 9. REFERÊNCIA: CANAIS CONCORRENTES PT-BR

| Canal | Handle | Nicho | Views top |
|-------|--------|-------|-----------|
| NoteLey | @NoteLeyZerandoAnimes | Recap longo (1-2h) | 8.7M |
| Mattz | @MattzRecaps | Recap longo, isekai | 6.1M |
| Anime no kokoro | @Animenokokoro | Resumo cronológico | 2.3M |
| Otakunelas | @otakunelas | Manhwa recap | 3.9M |
| Tio San | @Tio_San | Recap + games | 2.4M |
| Resumindo Animes | @ResumindoAnimes | Temporada completa | 2.1M |
| Reis Anime | @reis-anime | Recap temporada | 1.7M |

---

## 10. CHECKLIST PRÉ-POSTAGEM

- [ ] Título ≤ 100 chars, sem nome real da obra, com CAPS seletivo
- [ ] 20-30 tags (base + dinâmicas + typos)
- [ ] Descrição com sinopse + timestamps + TAG block + hashtags
- [ ] `anti_ban()` aplicado em título, descrição e tags
- [ ] Categoria = 24, made_for_kids = false
- [ ] ffprobe confirma vídeo válido (áudio + vídeo, duração OK)
