# Guia: como plugar PROPAGANDA de produtos num projeto de vídeo

Este guia descreve o esquema de propaganda construído no `veo/beta` pra ser
**replicado em qualquer projeto** que já gere vídeos (shorts, recaps, anime, etc).
A ideia: pegar um vídeo criativo pronto e anexar propaganda dos SEUS produtos,
sem gastar crédito à toa e de forma rastreável.

## A receita final (ordem do vídeo)

```
VÍDEO CRIATIVO  →  [transição]  →  CLIPE-PROPAGANDA (Veo, pessoa falando)  →  [transição]  →  CARD ESTÁTICO (imagem + voz + WhatsApp/link)
```

- **Vídeo criativo**: o que o projeto já produz.
- **Clipe-propaganda (vo3)**: um comercial de ~8s do produto, gerado 1x e
  **rotacionado** (não gera um por vídeo — gera alguns por produto e reusa).
- **Card estático**: slide final ~5s com fundo IA + nome do produto + voz
  (ElevenLabs) + WhatsApp/link. Custo zero (não gasta crédito de vídeo).

O clipe-propaganda é OPCIONAL: se o pool estiver vazio, o vídeo sai só com o
card (nada quebra).

## Peças (arquivos) e o que cada uma faz

| Arquivo | Papel |
|---|---|
| `assets/produtos.json` | Catálogo dos produtos (fonte única da verdade) |
| `cta_card.py` | Gera o CARD premium (fundo IA + texto + link) |
| `omniroute_image.py` | Gera imagem IA de fundo (gateway → Pollinations fallback) |
| `cta_builder.py` | Escolhe produto + voz ElevenLabs + monta o slide do card |
| `montagem.py` | Efeitos ffmpeg CPU (punch, overlay, transição) |
| `comercial_agents.py` | Multi-agente que PROJETA o comercial Veo (garante fala) |
| `vo3_propaganda_rotator.py` | Gera o pool de clipes Veo por produto + rotaciona |
| `montar_final.py` | Orquestra tudo (criativo → vo3 → card) |

## Passo a passo pra replicar

### 1. Catálogo de produtos (`produtos.json`)
Cada produto:
```json
{
  "id": "hermes_call", "nome": "Hermes Call", "tag": "hermes",
  "url": "https://link-real-do-produto.com",
  "cta_curto": "Ligações WhatsApp com IA 24h",
  "cta_longo": "Pitch de 1-2 frases pra voz do comercial.",
  "tema_alvo": ["atendimento","vendas","ia"],
  "peso": 5, "cor": "#25D366", "prioridade": "top"
}
```
Mais um `_mapeamento_tema_video` (palavra do tema → produto), pra casar o
produto certo com o assunto do vídeo. `peso` faz o sorteio ponderado.

### 2. Card estático (`cta_card.py` + `omniroute_image.py`)
- Fundo cinematográfico via IA (gateway de imagem; se falhar, Pollinations).
- Texto: nome do produto, `cta_curto`, WhatsApp e **o link real do produto**
  (NÃO um @handle genérico).
- Cache por produto (gera 1x, reusa). Bump de versão do layout invalida o cache.

### 3. Voz do card (`cta_builder._narracao_cta`)
- ElevenLabs multilingual (fala PT-BR), com rotação de chaves + Edge-TTS fallback.
- **Normalizar o texto pra TTS** antes de falar (senão lê abreviação errado):
  `24h → 24 horas`, `R$ 199 → 199 reais`, `24/7 → 24 horas por 7 dias`, `30min → 30 minutos`.
- WhatsApp/número NÃO vai na fala (TTS erra número) — vai só no card visual.

### 4. Clipe-propaganda Veo (`comercial_agents.py` + `vo3_propaganda_rotator.py`)
O **pulo do gato** — pra o Veo FALAR (não só som ambiente):
- Tem que haver uma **pessoa visível falando OLHANDO pra câmera** (não só o produto).
- A fala tem que ser **LITERAL, curta e entre aspas**: `... says in Brazilian Portuguese: "..."`.
- Marcar **lip-sync explícito**: `"lips moving, speaking directly to camera, clear voice"`.
- Fala curta o bastante pra caber em 8s (~18 palavras).

O multi-agente (`comercial_agents.py`) projeta isso em 4 passos: Estrategista
(dor+ângulo) → Roteirista (fala falável) → Diretor (prompt Veo com pessoa
falando) → Crítico (nota; regenera se <8).

O rotator gera o pool (`propagandas_pool/vo3/<produto>_<n>.mp4`) chamando o
gerador de vídeo do projeto, e `escolher_vo3_propaganda(produto_id, stem)`
rotaciona de forma estável.

### 5. Orquestrador (`montar_final.py`)
Junta na ordem da receita. Regras importantes:
- **Card e clipe vo3 têm que ser do MESMO produto** (escolhe o produto UMA vez).
- Só insere o clipe vo3 se existir um clipe **daquele produto** (sem fallback
  pra outro produto — senão mistura anúncios).
- Grava um **sidecar `.json`** ao lado do vídeo (rastreabilidade: prompt, foto,
  efeitos, produto, voz — pra reproduzir e auditar).

## Erros que já pagamos (não repita)

1. **`hash()` do Python é randomizado por processo** → o mesmo vídeo dava
   produto/efeito diferente a cada execução. **Use `hashlib.md5`** pra escolha
   determinística/reproduzível.
2. **Project ID fixo hardcoded** (no gerador Veo) → toda conta nova caía em
   "Algo deu errado". **Projeto por conta**: salva o project-url de cada
   sessão num json e entra no dela; se não tem, vai pra home e cria.
3. **"Algo deu errado. Tente novamente"** é erro transitório do Flow → basta
   **re-submeter o prompt** (implementar retry automático, ~3x).
4. **Prompt com "a narrator says"** (voz off) → Veo gera só SOM AMBIENTE. Use
   pessoa falando à câmera + lip-sync (item 4 acima).
5. **Segredos**: nunca versione perfis Chrome, sessions (cookies), chaves.
   Chave de gateway em arquivo gitignored, lido em runtime.
6. **Custo**: gere POUCOS clipes Veo por produto (pool) e rotacione. O card é
   grátis; o clipe Veo gasta crédito — só 1x por clipe, reusa em todos os vídeos.

## Dependências externas
- ffmpeg/ffprobe (efeitos e montagem, CPU-only).
- Gateway de imagem (Gemini/FLUX) com Pollinations de fallback keyless.
- ElevenLabs (voz) com Edge-TTS de fallback.
- Um gerador de vídeo Veo/Flow (pro clipe-propaganda) — reusa o do projeto.
