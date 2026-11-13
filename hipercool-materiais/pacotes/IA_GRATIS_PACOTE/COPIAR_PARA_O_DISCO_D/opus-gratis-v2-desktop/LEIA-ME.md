# opus-gratis — pool do Genspark para o Claude Opus 5.5 de graça

Projeto no mesmo molde do **gemini-argo** (Argon) e do **sonnet web**: um POOL de contas Google que,
pela automação do navegador do cofre, fala com o **Claude Opus 5.5** no chat do Genspark — que dá
**100 créditos/dia por conta** (renova por dia) e já vem com o Opus 5.5 selecionado.

## As perguntas da dona (respondidas, conferido ao vivo 30/10)

- **O cadastro do Genspark é "1 por 1"?** É. O Genspark **não tem cadastro próprio** — entra só por
  **"Entrar com Google" (OAuth)**. Como cada conta do cofre já está logada no Google, o "cadastro" vira
  **um clique por conta**, feito uma vez (`python genspark.py login`) e que **persiste no perfil**.
- **Dá pra RPA usar sem cadastro?** Sem login não há Opus. Mas o login é um OAuth de 1 clique por conta,
  a RPA faz sozinha, e **vale em todas as contas Google do cofre** (as `ig_*` são de Instagram, sem Google — ficam de fora).

## Conta e capacidade

- Custo medido: **~3 créditos por mensagem curta** → ~30 msg/dia por conta.
- Cofre tem **~62 contas Google vivas** → **~2.000 mensagens Opus 5.5/dia** somando todas.
- O modelo se identificou como "Claude Opus 5.5, da Anthropic" e acertou 17×23=391 (teste 30/10).

## Como usar

```bash
python genspark.py semear                 # 1x: põe as contas do cofre na fila (pula Instagram)
python genspark.py login                  # 1x por conta: faz o "Entrar com Google" (1 por 1)
python genspark.py listar                 # estado da fila: login, créditos, capacidade
python genspark.py "Quanto é 17 x 23?"    # pergunta pela 1ª conta pronta da fila
python genspark.py --conta conta_exemplo "oi"  # conta fixa
python monitor_genspark.py                # painel: logadas, com cota, próxima renovação
```

Como módulo (nos pipelines, igual ao `gemini_http.perguntar`):

```python
import sys; sys.path.insert(0, r"D:\opus-gratis")
from genspark import perguntar
texto = perguntar("Explique X em 3 linhas")     # 1ª conta pronta; roda a fila sozinho
```

Servidor HTTP compatível com a OpenAI (pra Cline, OmniRoute, qualquer cliente):

```bash
python genspark_http.py                    # http://127.0.0.1:20160  (modelo genspark/claude-opus-5-5)
curl 127.0.0.1:20160/v1/chat/completions -H "Content-Type: application/json" \
     -d '{"model":"genspark/claude-opus-5-5","messages":[{"role":"user","content":"oi"}]}'
```

## Arquivos

| arquivo | o que faz |
|---|---|
| `genspark.py` | núcleo: fila de contas + cota + login (1 por 1) + driver do navegador + CLI/módulo |
| `genspark_http.py` | servidor HTTP estilo OpenAI (`/v1/chat/completions`, `/v1/models`, `/cota`) |
| `monitor_genspark.py` | painel/zelador: quantas logadas, com cota, capacidade, quem falta logar |
| `contas_genspark.json` | estado da fila (login, créditos do dia, cota, erros) |
| `nav.py` | helper manual antigo (um Chrome de teste); usado para investigar o site |
| `RESULTADO.md` | pesquisa de todos os sites de Opus/Fable grátis (o Genspark foi o melhor) |
| `genspark.log` | log rotativo do pool |
| `umin\` | **1min.ai pela API**, sem navegador (Opus 5.5 a ~4 mil créditos/msg, Fable 5.1, Opus 5) + visita diária agendada (15 mil créditos/dia). Veja `umin\LEIA-ME.md` |

## Como funciona (resumo)

1. `cofre.abrir(conta)` dá o Chrome logado no Google daquela conta (1 perfil por conta, compartilhado com os outros projetos).
2. O driver reutiliza a aba existente (aba nova via CDP num Chrome escondido não desenha), navega ao chat, confere o modelo Opus 5.5, digita e lê a resposta em `.answer-markdown`.
3. A fila (`proxima_conta`) usa a 1ª conta pronta (logada, com crédito hoje, sem bloqueio). Quem bate no paywall sai da fila até o dia virar; 3 erros seguidos bloqueiam por 30 min.
4. Cota rastreada localmente: 100/dia, −3 por mensagem, renova à meia-noite (o Genspark renova por dia).

## Limites conhecidos

- É **automação de navegador** (não API pura): ~30–60 s por mensagem, mais quando a máquina está carregada
  (produção de vídeo subindo arquivos satura a rede/CPU e o Genspark carrega devagar — o driver espera com
  `commit`+polling em vez do `domcontentloaded`).
- Concorrência limitada por RAM (cada conta = 1 Chrome). O `genspark_http.py` usa semáforo `GENSPARK_VAGAS` (padrão 2).
- Créditos são **estimados** localmente (a barra de créditos do Genspark fica num menu recolhido). O paywall é detectado pelo texto da resposta.
