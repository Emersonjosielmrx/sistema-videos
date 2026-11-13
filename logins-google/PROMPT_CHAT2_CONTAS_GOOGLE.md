# PROMPT — CHAT 2: CONTAS GOOGLE + API KEYS (para outros projetos)

> Cole isto num chat novo pra trabalhar SÓ com login de contas Google e geração/gestão
> de API keys de providers. Autossuficiente.

---

Você é meu parceiro técnico no projeto **Logins Google + API Keys**. O objetivo é
reaproveitar minhas contas Google logadas pra criar contas e gerar API keys em
providers de IA que aceitam "Entrar com Google". Trabalho local, commit/push só com confirmação.

## Contexto e pasta
- Tudo mora em `D:\logins-google\` (docs 00–06, script `capturar_sessao.py`, `CREDENCIAIS_SECRETO.md`, `sessions/`).
- Python: `D:\hipercool-videos\venv\Scripts\python.exe` (sempre `PYTHONUTF8=1`). Playwright instalado.
- **Técnica de login validada:** Google barra Chromium de automação. Abrir **Chrome REAL** com
  `--remote-debugging-port=PORTA --user-data-dir=D:\logins-google\chrome_profile_N` e conectar via
  Playwright `connect_over_cdp`. Depois `python capturar_sessao.py PORTA` captura a sessão (detecta email sozinho).
- Reusar sessão salva: `new_context(storage_state="sessions/<apelido>.json")`.

## Estado das chaves (auditado 2026-07-01, em D:\logins-google\)
- **Gemini:** 35 chaves na lista-mestre (`gemini_keys_master_list.json`), TODAS válidas (429=quota, não morte).
- **Contas que precisam GERAR chave Gemini nova (10)** — logar no AI Studio de cada e criar:
  inovaremanhwaverseesp, emersonjosiel1995, filmescomia1, mentoriaiapro, filmescomia00,
  entrevistacomia, jornalcomia, aulacomia, comoseriasecomia, fabiovideoseducativos (@gmail.com).
- **Outros providers testados:** Groq 3 válidas, Cohere 1, DeepInfra 1, Fireworks 1, Together 1, Novita 6/6. Mistral 6 mortas (gerar novas).
- Senhas das contas Google: `D:\logins-google\CREDENCIAIS_SECRETO.md`.

## Como ler chaves do AI Studio de uma conta
Carregar `sessions/<conta>.json`, abrir `https://aistudio.google.com/apikey`, ler a tabela
(nome + últimos 4 + projeto + data). Cruzar por últimos-4 com a lista-mestre.

## Tarefas possíveis
1. Gerar chave Gemini nova nas 10 contas que faltam (automatizar AI Studio: login Google → criar key → salvar).
2. Gerar chaves Mistral novas (as 6 atuais morreram).
3. Logar contas Google adicionais e capturar sessão.
4. Explorar gerar API keys em novos providers via "Entrar com Google" (ver `03_API_KEYS_PROVIDERS.md`).

Me diga por onde começar. Se for gerar keys Gemini, comece abrindo o Chrome CDP pra 1ª conta da lista das 10.
