# 01 — Procedimento de Login Google (Passo a Passo)

> Técnica validada no projeto Roteador VEO. Funciona pra QUALQUER site que use
> "Entrar com Google", porque a sessão do Google fica salva no perfil do Chrome.

## O problema
O Google **bloqueia login em navegador de automação** (Chromium do Playwright/Selenium):
mostra "Este navegador ou app pode não ser seguro". Login manual no Chrome normal funciona.

## A solução: Chrome REAL + porta de debug (CDP)
Abrimos o **Chrome de verdade** com `--remote-debugging-port` e o Playwright se
conecta POR FORA (`connect_over_cdp`). Pro Google, é um Chrome normal → login OK.
Depois capturamos os cookies com `storage_state()`.

## PASSO 1 — Abrir Chrome real (perfil + porta dedicados)
Cada conta usa um **perfil** e uma **porta** diferentes (senão os cookies se misturam):
```bash
mkdir -p "D:/logins-google/chrome_profile_N"
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=PORTA \
  --user-data-dir="D:/logins-google/chrome_profile_N" \
  --no-first-run --no-default-browser-check \
  "https://accounts.google.com"        # ou direto o site do provider
```
- **PORTA:** 9222, 9223, 9224, 9225, 9226...
- **N:** 2, 3, 4, 5...
- Confirmar que subiu: `curl -s http://127.0.0.1:PORTA/json/version`

## PASSO 2 — Logar manualmente
No Chrome que abriu: fazer login no Google normalmente (funciona, é Chrome real).
Se for pra um provider específico, já clicar "Continuar com Google" e chegar na
tela desejada.

## PASSO 3 — Capturar a sessão (automático)
Rodar o script reutilizável (detecta email e nomeia sozinho):
```bash
cd D:/logins-google
PYTHONUTF8=1 D:/hipercool-videos/venv/Scripts/python.exe capturar_sessao.py PORTA
```
Isso salva em `sessions/`:
- `<apelido>.json`  — cookies (storage_state)
- `<apelido>.url.txt` — última URL
- `<apelido>.email.txt` — email detectado

## PASSO 4 — Reusar a sessão depois
Pra abrir qualquer site JÁ logado (sem relogar), carregue o storage_state:
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    ctx = b.new_context(storage_state="sessions/<apelido>.json")
    page = ctx.new_page()
    page.goto("https://aistudio.google.com/apikey")   # ex: gerar key Gemini
    # ... automatizar cliques ...
```
> Obs: cookies do Google podem expirar em dias/semanas. Se cair o login,
> repetir PASSO 1–3 na mesma conta (mesmo perfil).

## GOTCHAS aprendidos
- **Email não vem em `aria-label`** → extrair do `page.content()` com regex `[\w.\-+]+@gmail\.com`.
- **Perfis por porta** → nunca reusar o mesmo `--user-data-dir` pra contas diferentes.
- **PowerShell é case-insensitive** → cuidado com nomes de arquivo/pasta em scripts.
- **PYTHONUTF8=1 sempre** → console Windows quebra em acentos.
- Python do projeto: `D:\hipercool-videos\venv\Scripts\python.exe`.
