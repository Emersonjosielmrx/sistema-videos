# Logins Google — Procedimento Mestre (Reutilizável)

> Pasta central sobre como logar em contas Google de forma automatizável e
> **reaproveitar essas sessões pra qualquer serviço** que use "Entrar com Google".
> Uso principal futuro: **gerar API keys de vários providers** (Gemini, Groq,
> OpenRouter, etc.) e fazer cadastros — tudo através das contas Google já logadas.

Criada em 2026-07-01. Nasceu do projeto Roteador VEO (ver `D:\roteador-veo-docs\`),
onde a técnica de login Chrome+CDP foi validada.

## Índice
| Arquivo | Conteúdo |
|---|---|
| `00_INDICE.md` | Este arquivo |
| `01_PROCEDIMENTO_LOGIN.md` | Passo a passo do login + captura de sessão |
| `02_CONTAS_GOOGLE.md` | Lista mestre de contas Google logadas |
| `03_API_KEYS_PROVIDERS.md` | Plano: gerar API keys de providers via login Google |
| `capturar_sessao.py` | Script reutilizável: captura sessão de qualquer Chrome CDP |
| **`cofre/MUDANCAS.md`** | **(12/10/2026) Onde está cada conta agora: 1 perfil por conta em `cofre/perfis/`, usado por todos os projetos. LER PRIMEIRO** |
| `cofre.py` | Abrir/fechar/checar/logar uma conta (`cofre.abrir("conta")` dá a porta CDP; entra no Chrome já aberto) |
| `cofre/contas.json` | Cadastro: conta -> pasta, porta fixa (9700+), login vivo/morto, usos |
| `migrar_para_cofre.py` / `documentar_cofre.py` | Migração das pastas antigas (atalho no caminho antigo) e geração do MUDANCAS.md |
| `chrome-profiles/` | Só ATALHOS (junções) para o cofre desde 12/10 — apagar atalho com `rmdir`, nunca `rm -rf` |
| `sessions/` | Cópia das sessões (cookies) — NÃO commitar |

## Por que isso é poderoso
Muitos providers de IA (e SaaS em geral) deixam você **criar conta e gerar API key
só clicando em "Continuar com Google"**. Se a conta Google já está logada num
Chrome controlável via CDP, dá pra automatizar:
1. Abrir o site do provider (ex: aistudio.google.com, console.groq.com, openrouter.ai)
2. Clicar "Entrar com Google" → escolher a conta já logada (1 clique)
3. Navegar até a tela de API keys → criar → copiar a key
4. Salvar a key no cofre local

Multiplicando pelas N contas Google → **N API keys grátis por provider**.

## Regra de ouro
- **13/10/2026 (decisão do dono): Google (YouTube, Drive) só pelo navegador por enquanto.** Nada de criar projeto, chave ou ID do cliente OAuth no Google Cloud. Detalhes, e os canais que ainda dependem da API até alguém logar a conta no cofre: `D:\credenciais-canais\LEIA.md`.
- Cookies de sessão = SENHA. Tudo em `sessions/` fica LOCAL, nunca commitado.
- Respeitar os Termos de cada provider (isto é pra uso próprio da Haylla, não abuso em massa).
- Trabalho local; nada de push sem confirmação.

## Ver também
- `D:\roteador-veo-docs\` — o projeto que originou a técnica (Flow como API de vídeo).

- **KIRO_PROCEDIMENTO.md**: conferir créditos do Kiro, criar e conectar contas no OmniRoute (kiro_creditos.py); repetir no desktop e no PC2.
- **CONTAS_PROCEDIMENTOS.md**: lista única de contas, Kiro, Antigravity no OmniRoute, TikTok nos notebooks e canais livres do YouTube (como refazer).
