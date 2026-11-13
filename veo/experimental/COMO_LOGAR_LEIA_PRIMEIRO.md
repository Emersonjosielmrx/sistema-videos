# COMO LOGAR NO GOOGLE FLOW (LEIA ANTES DE TUDO)

## ⛔ O ERRO QUE VOCÊ QUER EVITAR

Ao tentar logar, o Google mostra:

> **"Não foi possível fazer o login. Esse navegador ou app pode não ser seguro."**

Isso acontece **SEMPRE** que o login é tentado dentro do navegador
automatizado que o Playwright abre sozinho (`p.chromium.launch(...)`).
O Google detecta que é um Chromium de automação e **bloqueia o OAuth**.

**NÃO adianta insistir, mudar cookies, mexer em flags nesse navegador.**
Ele nunca vai deixar logar. É bloqueio do lado do Google.

---

## ✅ O JEITO CERTO (E O ÚNICO QUE FUNCIONA)

Usar o **Chrome REAL** instalado na máquina
(`C:\Program Files\Google\Chrome\Application\chrome.exe`), aberto com uma
**porta de depuração** (`--remote-debugging-port`). O Playwright então se
conecta **POR FORA** via CDP (`connect_over_cdp`), sem abrir navegador próprio.

Para o Google, é um Chrome normal → **o login funciona.**

### Passo a passo para (re)logar uma conta

```bash
cd D:/hipercool-inferior-fix/roteador-veo-api-fake
D:/hipercool-videos/venv/Scripts/python.exe chrome_cdp.py open
```

1. Um **Chrome REAL** vai abrir apontando pro Flow.
2. **Faça o login normalmente** (email + senha da conta, ex.:
   `fabricadeautomacoesia@gmail.com`).
3. Entre no Flow até ver a **caixa de escrever o prompt**.
4. O script **captura a sessão sozinho** em ~5 min (salva os cookies em
   `sessions/<apelido>.json`). Não precisa fechar nada.

> Para capturar na hora, sem esperar os 5 min, rode em outro terminal:
> ```bash
> D:/hipercool-videos/venv/Scripts/python.exe chrome_cdp.py capture fabrica
> ```

---

## 🔑 REGRAS DE OURO (decoreba)

| ❌ NUNCA                                   | ✅ SEMPRE                                    |
|-------------------------------------------|---------------------------------------------|
| `p.chromium.launch()` para logar          | Chrome real via `chrome_cdp.py` (porta CDP) |
| Tentar logar no navegador do Playwright   | Logar no Chrome de verdade que abriu        |
| Reaproveitar cookies velhos p/ "burlar"   | Recapturar a sessão quando expira            |

- O bloqueio **"navegador não seguro"** = você está no navegador ERRADO.
  Feche e use `chrome_cdp.py`.
- Só o **login** precisa do Chrome real. Depois de logado, a geração de
  vídeo (`flow_bot.py generate`) reusa os cookies salvos e roda via CDP.

---

## 🧩 POR QUE FUNCIONA (resumo técnico)

- `p.chromium.launch()` → Chromium "de teste" → Google barra o OAuth.
- Chrome real + `--remote-debugging-port=9222` → Playwright conecta com
  `connect_over_cdp("http://127.0.0.1:9222")` → controla o Chrome de fora →
  Google enxerga um Chrome legítimo → login liberado.

Arquivo que faz isso: [`chrome_cdp.py`](chrome_cdp.py)
(perfil dedicado em `chrome_profile/`, porta `9222`).
