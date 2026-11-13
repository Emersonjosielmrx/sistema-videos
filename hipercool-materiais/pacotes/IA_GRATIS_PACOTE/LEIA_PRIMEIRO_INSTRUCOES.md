# Pacote IA grátis: Argon, Sonnet web, Genspark (Opus 5.5), 1min e Cline

Este pacote tem o **código e a documentação** de 5 sistemas que dão modelos de IA de graça no Claude Code (VS Code),
montados para rodar em outro PC.

**Não vem nenhuma credencial.** Ficaram de fora: cookies, chaves de API, tokens, senhas, a lista de contas, os IPs
das máquinas e da VPS e o telefone. No lugar deles há marcadores como `COLOQUE_SUA_CHAVE`, `IP_DA_SUA_VPS`,
`sua_conta@gmail.com` e `conta_exemplo`. Os nomes reais das contas foram trocados por `conta_exemplo` também dentro
dos textos de histórico (PROGRESSO.md etc.).

---

## 0. Escolha o caminho

| Você quer… | Faça |
|---|---|
| **Só usar** os modelos num PC novo, com o servidor que já existe ligado | Seção 1 (5 minutos) |
| **Montar tudo do zero** (sua própria VPS, suas contas) | Seções 2 a 9 |

---

## 1. Só usar (o servidor e o PC principal já existem)

1. Instale o **VS Code** e, dentro dele, a extensão **Claude Code** (Anthropic).
2. Abra a pasta `SO_USAR_cliente_vscode`.
3. Clique com o botão direito em `instalar_todos_modelos.ps1` > **Executar com o PowerShell**.
4. Ele pergunta o **IP da VPS** e a **chave do OmniRoute** (começa com `sk-`). A chave fica no PC principal, nas
   configurações do VS Code (`ANTHROPIC_AUTH_TOKEN`).
5. Feche todas as janelas do VS Code e abra de novo. O seletor de modelo do chat passa a ter: Argon Pro, Argon,
   Sonnet 5.5 web, Opus 5.5 Genspark, Cline Opus 5.5 e Gemini 3.8.

Para desfazer: o instalador deixa `settings.json.bak-ia` ao lado de cada arquivo que mudou. Copie o `.bak-ia` por cima.

> O Argon, o Genspark e o Cline passam pelo PC principal (por túnel). Se ele estiver desligado, esses três falham e
> os outros continuam funcionando.

(O `INSTALAR.bat` antigo da mesma pasta instala só o Argon. Pode ignorar.)

---

## 2. Como tudo se liga (para montar do zero)

```
VS Code (Claude Code)
   │  ANTHROPIC_BASE_URL = http://IP_DA_VPS:20133
   ▼
VPS ─ proxy.mjs :20133  (gemini-argo/proxy_vps.mjs)  ── decide pelo nome do modelo
   │     ├─ gemini-4-argon, argon-pro, hx-*, gweb/*  ──► túnel ──► PC :20141  gemini_http_proxy.py  (Argon)
   │     ├─ genspark-opus-5-5                       ──► túnel ──► PC :20165  genspark_http.py     (Genspark + 1min)
   │     ├─ cline-*                                 ──► túnel ──► PC :20160  ponte.mjs            (Cline)
   │     └─ todo o resto (cw/…, agy/…, cc/…)        ──► OmniRoute :20128
   ▼
OmniRoute :20128 (Docker)  ── provedor claude-web (cw/) = contas do claude.ai  (Sonnet web)
```

- **No PC** rodam: Argon, Genspark/1min e Cline. Eles usam o Chrome das suas contas pelo **cofre**
  (`D:\logins-google\cofre.py`: um perfil de Chrome por conta Google).
- **Na VPS** rodam: o OmniRoute (que cuida do Sonnet web) e o `proxy.mjs`.
- O PC fala com a VPS por **túneis SSH reversos** (`ssh -R`), mantidos vivos pelos scripts `*_manter.py`.

| Porta | Onde | O quê |
|---|---|---|
| 20128 | VPS | OmniRoute |
| 20133 | VPS | proxy.mjs (o VS Code aponta aqui) |
| 20141 | PC (+túnel) | Argon: `gemini_http_proxy.py` |
| 20160 | PC (+túnel) | Cline: `ponte.mjs` |
| 20165 | PC (+túnel) | Genspark/1min: `genspark_http.py` |
| 20166 | PC | opcional: `proxy_cc/proxy_genspark.mjs` (Genspark direto no PC, sem VPS) |
| 9700+ | PC | Chrome de cada conta do cofre (porta de controle) |

---

## 3. Preparar o PC novo

### 3.1 Programas
1. **Python 3.11 ou mais novo** (python.org). Na instalação marque "Add python.exe to PATH".
2. **Node.js 20 ou mais novo** (nodejs.org).
3. **Git for Windows** (traz o `ssh`).
4. **Google Chrome** em `C:\Program Files\Google\Chrome\Application\chrome.exe` (o cofre procura aí).
5. **VS Code** + extensão **Claude Code**. Para o Cline, também a extensão **Cline**.

### 3.2 Copiar as pastas
O código usa caminhos fixos no disco **D:** (`D:\gemini-argo`, `D:\logins-google`...). Copie **tudo** que está dentro
de `COPIAR_PARA_O_DISCO_D` para a raiz do `D:\`, sem mudar os nomes. Fica assim:

```
D:\gemini-argo\            Argon
D:\sonnet web\             Sonnet web
D:\opus-gratis-v2-desktop\ Genspark + 1min
D:\cline-ponte\            Cline
D:\logins-google\          cofre (perfis do Chrome)
D:\hipercool-materiais\comum\sem_janela.py
D:\postador-de-videos\bin\ claude_criar.py, maquina_remota.py (versão local), netbooks\chrome_conta.py
D:\video-fila\avisos.py    avisos (versão simples; Telegram opcional)
D:\rodar_oculto.vbs        roda as tarefas sem abrir janela
```

**O PC não tem disco D?** Crie uma pasta e transforme em D: (no PowerShell como administrador):
```powershell
mkdir C:\IA
subst D: C:\IA
```
(O `subst` some ao reiniciar. Para ficar fixo, crie uma tarefa agendada "ao fazer logon" com `subst D: C:\IA`.)

### 3.3 Bibliotecas do Python
```powershell
pip install -r requirements.txt
```
(`requests`, `playwright`, `curl_cffi`, `aiohttp`. O Playwright só se conecta ao Chrome instalado, então não precisa
baixar navegador dele.)

### 3.4 Chave SSH para a VPS
Siga `VPS_exemplos\ssh_config_exemplo.txt`. O ponto principal: dê à VPS o apelido **`hermes-bloqueio`** no
`~\.ssh\config`. É o nome que todos os scripts usam. O teste `ssh -o BatchMode=yes hermes-bloqueio echo ok`
tem que responder `ok` **sem pedir senha**.

### 3.5 Contas Google no cofre
Cada conta Google que você vai usar entra no cofre uma vez (abre o Chrome, você digita a senha):
```powershell
cd D:\logins-google
python cofre.py logar sua_conta@gmail.com
python cofre.py checar          # confere quem está logado de verdade
```

> ⚠️ **Cuidado com várias contas no mesmo IP.** Todos estes sistemas usam várias contas a partir do mesmo PC.
> Os serviços podem ligar contas que saem do mesmo IP e suspender todas juntas (já aconteceu com outro serviço).
> Comece com poucas contas, não faça cadastros em rajada (o 1min trava o IP por 24 h depois de ~3 cadastros
> seguidos) e espalhe os logins ao longo do dia.

---

## 4. VPS (servidor)

Precisa de uma VPS Linux (Ubuntu) com Docker e Node.js 20+.

1. **OmniRoute** (não vem no pacote: é um programa de terceiros). Instale pela documentação dele, em Docker, com o
   contêiner chamado `omniroute`, a porta **20128** e os dados em `/opt/omniroute/data`. Ele já traz o provedor
   `claude-web` (prefixo `cw/`), usado pelo Sonnet web. No painel dele crie uma **chave de API** (`sk-...`): é a
   chave que o VS Code usa.
2. **Proxy :20133**
   ```bash
   mkdir -p /opt/antigravity-cc-proxy
   # copie do PC:  gemini-argo/proxy_vps.mjs  ->  /opt/antigravity-cc-proxy/proxy.mjs
   #               sonnet web/visao.mjs       ->  /opt/antigravity-cc-proxy/visao.mjs
   cp antigravity-cc-proxy.service /etc/systemd/system/
   systemctl daemon-reload && systemctl enable --now antigravity-cc-proxy
   ```
   O `proxy_vps.mjs` já tem as rotas do Argon, do Genspark (`genspark-opus-5-5`) e do Cline. O
   `cline-ponte/vps/patch_proxy.py` só serve para um proxy antigo sem a rota do Cline.
3. **Fechar as portas dos túneis** (obrigatório, senão ficam abertas para a internet sem senha):
   `VPS_exemplos/fechar-portas-tunel.service` (as instruções estão dentro do arquivo).
4. Libere no firewall da VPS só a **20133** (e o SSH). A 20128 pode ficar fechada para fora.

Teste da VPS (troque a chave):
```bash
curl -s localhost:20133/v1/messages -H "x-api-key: sk-SUA_CHAVE" -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"agy/gemini-3.8-flash-high","max_tokens":20,"messages":[{"role":"user","content":"oi"}]}'
```
(O `agy/gemini-3.8-flash-high` só existe se você ligou o provedor Antigravity no OmniRoute. Se não ligou, teste com
um modelo que tenha.)

---

## 5. Argon (Gemini 4 Argon, raciocínio alto) — `D:\gemini-argo`

**Precisa:** contas Google com o plano do Gemini que libera o "4 Argon" (Google One/AI Pro). Conta grátis não tem.

Leia antes: `ARGON_MELHORIAS.md` (tudo o que foi descoberto) e `docs\HTTP_PURO_GUIA.md`.

```powershell
cd D:\gemini-argo
python descobrir_pro.py                 # testa as contas do cofre e põe na fila (contas_argon.json) as que têm Argon
python sync_cookies.py                  # abre cada conta 1 vez (sem janela) e salva cookies\<conta>.json
python gemini_http_proxy.py --porta 20141   # sobe o Argon (HTTP puro, sem navegador). Deixe rodando.
```
Teste local (outra janela):
```powershell
curl.exe -s 127.0.0.1:20141/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"gemini-4-argon\",\"messages\":[{\"role\":\"user\",\"content\":\"quanto e 17x23?\"}]}"
```
Ligar na VPS: `python argon_manter.py` sobe o proxy e o túnel `-R 20141` e os religa se caírem (ponha numa tarefa
a cada 5 min, seção 9).

Outros scripts:
| script | para quê |
|---|---|
| `argon_zelador.py` | renova os cookies antes de morrerem (o Google gira o `__Secure-1PSIDTS`) |
| `monitor_argon.py` | vê a cota das contas e avisa quando acaba/volta (pelo `avisos.py`) |
| `classificar_pro.py` | confere se a resposta veio mesmo do "4 Argon" (sem cota, o Google troca pelo Flash calado) |
| `mcp_argon.py` | servidor MCP com a ferramenta `ask_argon`, para usar o Argon como ajudante dentro do Claude Code |
| `gemini_argon.py` | modo antigo por navegador (reserva) |
| `youtube_http.py` | bônus: métricas do YouTube Studio por HTTP, com o mesmo método |

---

## 6. Sonnet web (Claude Sonnet 5.5 pelas contas grátis do claude.ai) — `D:\sonnet web`

Leia antes: `PROGRESSO.md` (passo a passo e problemas resolvidos) e `COMPARACAO_ARGON_x_CLAUDEWEB.md`.

**No PC:**
```powershell
# 1) criar/entrar no claude.ai com o Google da conta (abre o Chrome; plano GRATUITO)
python D:\postador-de-videos\bin\claude_criar.py conta_do_cofre
# 2) ler o cookie da sessão (sessionKey) e guardar em segredos\cookies.json
python "D:\sonnet web\pegar_cookies.py" conta_do_cofre
```
Para várias contas: `python "D:\sonnet web\lote_contas.py" --todas-pc2` (aqui "pc2" = este PC; faz uma por vez e
pula as já feitas). Não rode dezenas de seguida: depois de ~30 logins o Google/Cloudflare começa a barrar.

**Na VPS** copie os scripts `*_vps.py` para `/opt/omniroute/` **com estes nomes** (os outros scripts chamam assim):

| do pacote | na VPS |
|---|---|
| `cadastrar_omniroute_vps.py` | `/opt/omniroute/cadastrar_claude_web.py` |
| `ler_claude_web_vps.py` | `/opt/omniroute/ler_claude_web.py` |
| `sonnet_estado_vps.py` | `/opt/omniroute/sonnet_estado.py` |
| `sonnet_oi_vps.py` | `/opt/omniroute/sonnet_oi.py` (timer a cada 1 min) |
| `ordenar_contas_cw_vps.py` | `/opt/omniroute/ordenar_contas_cw.py` (cron a cada 2 min) |
| `combo_sonnet_fila_vps.py`, `combo_inverter_vps.py` | opcionais (só se você também tem contas pagas do Claude Code) |

Cadastrar as contas no OmniRoute (do PC):
```powershell
type "D:\sonnet web\segredos\cookies.json" | ssh hermes-bloqueio 'S=$(docker exec omniroute printenv INITIAL_PASSWORD); python3 /opt/omniroute/cadastrar_claude_web.py "$S"'
ssh hermes-bloqueio "sqlite3 /opt/omniroute/data/storage.sqlite \"UPDATE provider_connections SET health_check_interval=0, test_status='active' WHERE provider='claude-web'\""
```
O 2º comando é **necessário**: o "health check" do OmniRoute é barrado pelo Cloudflare e marcaria as contas como
"expired" à toa.

Teste: modelo **`cw/claude-sonnet-5-5`** no VS Code.

Manutenção no PC: `zelador_sonnet.py` (1x por dia; renova a sessão antes de vencer, ~4 semanas) e `monitor_sonnet.py`
(a cada 10 min).

Limites: não vê imagem nativa (o `visao.mjs` da VPS pede ao Gemini para descrever); conta grátis tem limite por 5 h
(o OmniRoute põe a conta 10 min de lado quando dá 429).

---

## 7. Genspark (Claude Opus 5.5) + 1min — `D:\opus-gratis-v2-desktop`

Leia antes: `CLAUDE.md`, `LEIA-ME-V2.md`, `SEM_NAVEGADOR.md`, `PROGRESSO.md` e `RESULTADO.md` (pesquisa de todos os
sites de Opus grátis que foram testados).

### 7.1 Genspark
O Genspark dá **100 créditos/dia por conta Google** (~3 por mensagem curta). Entra só por "Continuar com Google".
Algumas contas não têm o Opus no plano grátis: o zelador acha e tira da fila.

```powershell
cd D:\opus-gratis-v2-desktop
python genspark.py semear               # põe as contas do cofre na fila (contas_genspark.json)
python login_fila.py                    # abre 3 janelas por vez; você clica "Continuar com Google" em cada uma
python zelador_genspark.py              # testa quais contas têm Opus
python genspark_http_puro.py capturar --conta conta_exemplo   # 1x por conta: salva cookies\<conta>.json
python genspark_http_puro.py --conta conta_exemplo "Quanto e 17 x 23?"   # teste sem navegador
python genspark_http.py                 # servidor :20165 (deixe rodando)
```
Ligar na VPS: `python og_manter.py` sobe o servidor e o túnel `-R 20165` (tarefa a cada 5 min). No VS Code: modelo
**`genspark-opus-5-5`**.

Modos do servidor (nome do modelo pedido ao :20165): `genspark/claude-opus-5-5` (puro → página → tela),
`puro/…` (HTTP puro, ~5 s), `pagina/…` (página quente no Chrome), `tela/…` (automação de tela antiga, ~45 s).

### 7.2 1min.ai (Opus 5.5, Opus 5, Fable 5.1 pela API)
1. Logue a conta Google no app.1min.ai e crie a chave: menu da equipe > API > New API Key.
2. Grave a chave numa linha em `segredos\1min.key` (veja `segredos\LEIA.txt`).
3. Teste: `python umin\umin.py "oi"` · saldo: `python umin\umin.py saldo`.
4. Crédito grátis renovável: **15 mil/dia** só por abrir o site logado. Agende:
   `python umin\visita_diaria.py --agendar` (todo dia 06:10).
5. Várias contas: `umin\criar_contas.py` (grava as chaves em `umin\umin_contas.json`) e `umin\login_fila.py`.
   `umin\proxy_umin.py` manda o 1min por proxies da Webshare (lê um `proxies.txt` que não vem no pacote).

Custo medido por mensagem curta: Opus 5.5 ≈ 4 a 15 mil créditos, Fable 5.1 ≈ 50 a 60 mil. Ou seja, o 1min é reserva.
Pelo servidor :20165: `1min/claude-opus-5-5`, `1min/claude-opus-5`, `claude-fable-5-1`; `claude-opus-5-5` = Genspark
primeiro e 1min se faltar crédito.

---

## 8. Cline Opus 5.5 — `D:\cline-ponte`

Usa a conta da extensão **Cline** deste PC (créditos Cline) ou uma chave Anthropic `sk-ant` configurada no Cline.
A ponte lê o login direto da pasta do Cline (`~\.cline\data`) e nunca o copia.

1. No VS Code, abra o Cline e entre na conta (ou configure a chave Anthropic nele).
2. Renomeie `config.exemplo.json` para `config.json` e preencha (as explicações estão dentro).
3. `iniciar.bat` sobe a ponte na 20160 **e** o túnel até a VPS.
4. Saúde: `curl.exe http://127.0.0.1:20160/saude`. Teste completo: `python -I teste.py`.
5. No VS Code: modelo **`cline-opus-5-5`** (também `cline-sonnet-5-5`, `cline-fable-5-1`).

---

## 9. Deixar tudo ligando sozinho (tarefas agendadas, sem janela)

Exemplo (PowerShell). Troque o caminho do Python pelo seu (`(Get-Command python).Source`, use o `pythonw.exe` da
mesma pasta):
```powershell
$py = "C:\Users\SEU_USUARIO\AppData\Local\Programs\Python\Python313\pythonw.exe"
schtasks /Create /TN "ArgonManter"      /SC MINUTE /MO 5 /TR "wscript.exe D:\rodar_oculto.vbs $py D:\gemini-argo\argon_manter.py" /F
schtasks /Create /TN "OpusGratisManter" /SC MINUTE /MO 5 /TR "wscript.exe D:\rodar_oculto.vbs $py D:\opus-gratis-v2-desktop\og_manter.py" /F
schtasks /Create /TN "ClinePonte"       /SC ONLOGON      /TR "wscript.exe D:\rodar_oculto.vbs D:\cline-ponte\iniciar.bat" /F
schtasks /Create /TN "ArgonZelador"     /SC DAILY /ST 04:00 /TR "wscript.exe D:\rodar_oculto.vbs $py D:\gemini-argo\argon_zelador.py" /F
schtasks /Create /TN "ZeladorSonnet"    /SC DAILY /ST 04:20 /TR "wscript.exe D:\rodar_oculto.vbs $py `"D:\sonnet web\zelador_sonnet.py`"" /F
schtasks /Create /TN "MonitorSonnet"    /SC MINUTE /MO 10 /TR "wscript.exe D:\rodar_oculto.vbs $py `"D:\sonnet web\monitor_sonnet.py`"" /F
schtasks /Create /TN "ZeladorGenspark"  /SC DAILY /ST 06:10 /TR "wscript.exe D:\rodar_oculto.vbs $py D:\opus-gratis-v2-desktop\zelador_genspark.py" /F
```
Avisos no Telegram (opcional): veja o topo de `D:\video-fila\avisos.py`. Sem configurar, os avisos só vão para
`D:\video-fila\avisos.log`.

Depois disso, rode a seção 1 neste PC (ou em outro) para ligar o VS Code.

---

## 10. Problemas comuns

| Sintoma | Causa provável / o que fazer |
|---|---|
| Argon responde, mas fraco/rápido demais | a cota do Argon acabou e o Google trocou pelo Flash calado. `monitor_argon.py` mostra a hora em que volta |
| "Nenhuma conta com cota do Argon agora" | todas as contas esgotaram; a mensagem diz a hora da volta |
| Argon/Genspark/Cline com erro 529 ou "inacessível" no VS Code | PC desligado ou túnel caído. Rode `argon_manter.py` / `og_manter.py` / `iniciar.bat` e veja se `ssh hermes-bloqueio echo ok` responde |
| Sonnet web 429 "Rate limited" | limite do plano grátis; a conta volta sozinha (o `sonnet_oi.py` confere). Mais contas = mais cota |
| Sonnet web "expired" sem motivo | faltou o `UPDATE ... health_check_interval=0` da seção 6 |
| Sonnet web 403 permission_denied mesmo com sessão nova | conta barrada no claude.ai; o zelador desliga e lista em `contas_barradas.json` |
| claude.ai "Não foi possível verificar seu navegador" | o Cloudflare barrou o Chrome automatizado. Tente mais tarde, com menos contas seguidas |
| Genspark responde "benefício da assinatura" | essa conta não tem Opus no grátis; o zelador tira da fila |
| 1min `IP_LOCKED` | muitos cadastros seguidos do mesmo IP: espere 24 h ou use o `proxy_umin.py` |
| 1min `INSUFFICIENT_CREDITS` | acabou o saldo; só a visita diária (15 mil) renova |
| Script reclama de `D:\...` não encontrado | as pastas não foram copiadas para a raiz do D: com os nomes certos (seção 3.2) |
| Pouca RAM / Chrome travando | cada conta aberta é um Chrome; os scripts abrem poucas de cada vez. Feche Chromes esquecidos |

---

## 11. O que ficou de fora (de propósito)

- Todas as pastas `cookies\`, `cookies_youtube\` e `segredos\`, além de `config.json`, `contas_*.json`, `umin_contas.json`,
  `proxies.txt`, a senha da VPS e o token do OmniRoute.
- Capturas de rede (`rede.json`, `captura\`, `ultimo_pedido.json`, `diag_ajudante\`), que têm tokens e conversas.
- Logs, prints de tela, backups `.bak` e arquivos de estado.
- O `maquina_remota.py` original (mapa das suas máquinas com IPs e usuários): no lugar dele vai uma versão que usa
  só este PC.
- O `avisos.py` original (bots do Telegram): no lugar dele vai uma versão simples.
- O OmniRoute (programa de terceiros: instale pela documentação dele).

Ficou dentro só a *sitekey* do reCAPTCHA do Genspark (`genspark_api.py`). Ela é pública: aparece no próprio site do
Genspark, não é credencial sua.
