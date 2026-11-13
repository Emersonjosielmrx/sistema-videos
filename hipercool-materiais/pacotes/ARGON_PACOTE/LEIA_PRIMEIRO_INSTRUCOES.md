# Pacote Argon (Gemini 4 Argon, raciocínio alto) no Claude Code

Este pacote tem o **código e a documentação** do Argon: um servidor que fala com o **Gemini 4 Argon** do site
gemini.google.com por HTTP puro (sem abrir navegador a cada pergunta), usando um pool de contas Google com rodízio.
Ele aparece no Claude Code do VS Code como **Argon** e **Argon Pro**.

**Não vem nenhuma credencial:** nem cookies, nem chaves, nem tokens, nem a lista de contas, nem IPs. No lugar há
marcadores como `COLOQUE_SEU_TOKEN_JWT`, `IP_DA_SUA_VPS`, `sua_conta@gmail.com` e `conta_exemplo`.

---

## 0. Escolha o caminho

| Você quer… | Faça |
|---|---|
| **Só usar** o Argon num PC novo, com o servidor que já existe ligado | Seção 1 (5 minutos) |
| **Montar do zero** (suas contas, sua VPS) | Seções 2 a 7 |

---

## 1. Só usar

1. Instale o **VS Code** e, dentro dele, a extensão **Claude Code** (Anthropic).
2. Na pasta `SO_USAR_cliente_vscode`, clique com o botão direito em `instalar_argon.ps1` > **Executar com o PowerShell**.
3. Ele pergunta o **IP da VPS** e a **chave do OmniRoute** (começa com `sk-`; está no PC principal, nas configurações
   do VS Code, em `ANTHROPIC_AUTH_TOKEN`).
4. Feche todas as janelas do VS Code e abra de novo. O chat já começa no **Argon Pro**; troque pelo seletor.

Desfazer: copie os `settings.json.bak-argon` por cima dos `settings.json`.

> O Argon passa pelo PC principal (por túnel). Se ele estiver desligado, o Argon não responde.

| Modelo no seletor | Para quê |
|---|---|
| `argon-pro` (Argon Pro) | **código**: o Argon decide e o Gemini 3.8 executa as ferramentas |
| `gemini-4-argon` (Argon) | **texto**: roteiro, análise, revisão (Argon puro) |
| `argon-gemini` | o Argon faz tudo; o Gemini 3.8 só socorre quando ele não chama ferramenta |
| `agy/gemini-3.8-flash-high` | reserva rápida quando o Argon está sem cota |

Bom saber: o Argon é lento (10 s a alguns minutos, porque pensa no nível alto), não vê imagem/PDF e não pesquisa na web.

---

## 2. Como funciona (para montar do zero)

```
VS Code (Claude Code)  ── ANTHROPIC_BASE_URL = http://IP_DA_VPS:20133
   ▼
VPS: proxy.mjs :20133  (gemini-argo/proxy_vps.mjs)
   ├─ gemini-4-argon, argon-pro, argon-*, hx-*  ──► túnel ssh -R ──► PC :20141  gemini_http_proxy.py
   │                                                               └─► gemini.google.com (cookies das contas Pro)
   └─ resto (ex.: agy/gemini-3.8-flash-high, "mãos" do Argon Pro)  ──► OmniRoute :20128
```

- **No PC**: `gemini_http_proxy.py` (porta 20141) escolhe a 1ª conta com cota, manda o pedido direto ao endpoint
  interno do Gemini com os cookies da conta e devolve no formato OpenAI. Raciocínio no nível **Alto**. Reaproveita a
  conversa entre turnos (manda só o que é novo).
- **Na VPS**: `proxy.mjs` traduz Anthropic ↔ OpenAI, ensina ao Argon um protocolo de texto para chamar ferramentas
  (o site não tem ferramenta nativa) e monta os modelos híbridos (Argon pensa, outro modelo executa).
- **Cookies**: tirados 1 vez do Chrome de cada conta pelo **cofre** (`D:\logins-google\cofre.py`, um perfil de Chrome
  por conta). O Google gira os cookies; o `argon_zelador.py` renova antes de morrerem.

Leitura recomendada (dentro de `gemini-argo`): `ARGON_MELHORIAS.md` (tudo o que foi descoberto, com datas),
`docs\HTTP_PURO_GUIA.md` (a técnica do HTTP puro) e `PROMPT_PROXIMO_AGENTE.md`.

---

## 3. Preparar o PC

### 3.1 Programas
- **Python 3.11+** (marque "Add python.exe to PATH"), **Git for Windows** (traz o `ssh`) e **Google Chrome** em
  `C:\Program Files\Google\Chrome\Application\chrome.exe`.

### 3.2 Copiar as pastas
O código usa caminhos fixos no **D:**. Copie tudo de dentro de `COPIAR_PARA_O_DISCO_D` para a raiz do `D:\`,
sem mudar os nomes:
```
D:\gemini-argo\                          o Argon
D:\logins-google\                        cofre (perfis do Chrome)
D:\hipercool-materiais\comum\sem_janela.py
D:\postador-de-videos\bin\netbooks\chrome_conta.py   (libera RAM antes de abrir o Chrome)
D:\video-fila\avisos.py                  avisos (versão simples; Telegram opcional)
D:\rodar_oculto.vbs                      roda as tarefas sem abrir janela
```
Sem disco D? No PowerShell como administrador: `mkdir C:\IA` e depois `subst D: C:\IA`.
(O `subst` some ao reiniciar; para ficar fixo, crie uma tarefa "ao fazer logon" com esse comando.)

### 3.3 Bibliotecas
```powershell
pip install -r requirements.txt
```

### 3.4 SSH até a VPS
Siga `VPS_exemplos\ssh_config_exemplo.txt`. Dê à VPS o apelido **`hermes-bloqueio`** (é o nome que os scripts usam).
O teste `ssh -o BatchMode=yes hermes-bloqueio echo ok` tem que responder `ok` sem pedir senha.

### 3.5 Contas Google
Precisa de contas com o plano do Gemini que libera o **"4 Argon"** (Google One / AI Pro). Conta grátis não tem.
Ponha cada conta no cofre (abre o Chrome; você digita a senha):
```powershell
cd D:\logins-google
python cofre.py logar sua_conta@gmail.com
python cofre.py checar
```

> ⚠️ **Várias contas no mesmo IP:** o Google pode ligar contas que saem do mesmo IP. Comece com poucas, não faça
> logins em rajada e espalhe ao longo do dia.

---

## 4. Ligar o Argon no PC

```powershell
cd D:\gemini-argo
python descobrir_pro.py          # testa as contas do cofre e põe na fila (contas_argon.json) só as que têm o Argon
python sync_cookies.py           # abre cada conta 1 vez (sem janela) e salva cookies\<conta>.json
python gemini_http_proxy.py --porta 20141    # sobe o Argon. Deixe esta janela aberta.
```
Só quer pôr uma conta à mão? `python -c "import sys; sys.path.insert(0, r'D:\gemini-argo'); import gemini_argon as g; g.adicionar_conta('sua_conta@gmail.com')"`

Teste (outra janela):
```powershell
curl.exe -s 127.0.0.1:20141/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"gemini-4-argon\",\"messages\":[{\"role\":\"user\",\"content\":\"quanto e 17x23?\"}]}"
```
Tem que vir `391`. Se vier rápido e raso demais, a conta está sem cota de Argon (o Google troca pelo Flash calado):
veja a seção 7.

---

## 5. VPS (para usar no VS Code)

Precisa de uma VPS Linux com **Node.js 20+**.

1. **Proxy :20133**
   ```bash
   mkdir -p /opt/antigravity-cc-proxy
   # do pacote:  gemini-argo/proxy_vps.mjs  ->  /opt/antigravity-cc-proxy/proxy.mjs
   #             VPS_exemplos/visao.mjs     ->  /opt/antigravity-cc-proxy/visao.mjs
   cp antigravity-cc-proxy.service /etc/systemd/system/
   systemctl daemon-reload && systemctl enable --now antigravity-cc-proxy
   ```
2. **Fechar a porta do túnel** (obrigatório): `VPS_exemplos/fechar-portas-tunel.service` (instruções dentro).
   Sem isso a 20141 fica aberta para a internet, sem senha.
3. Libere no firewall só a **20133** (e o SSH).
4. **OmniRoute** (opcional, programa de terceiros, não vem no pacote): só é preciso para o **Argon Pro** e os híbridos,
   porque as "mãos" (quem executa as ferramentas) vêm dele, e para a chave `sk-` do VS Code. Instale pela
   documentação dele, em Docker, na porta **20128**. Sem ele, use o modelo `gemini-4-argon` puro.
5. **Qual "mão" o Argon Pro usa:** o arquivo `/opt/antigravity-cc-proxy/argon_pro.txt` diz qual híbrido vale. Sem o
   arquivo é `hx-socorro-kiro` (precisa do Kiro no OmniRoute). Só tem o Gemini 3.8? Grave `hx-socorro-gemini` nele:
   `echo hx-socorro-gemini > /opt/antigravity-cc-proxy/argon_pro.txt`. Lista dos modos em `ARGON_MELHORIAS.md`.

Depois, no PC:
```powershell
python D:\gemini-argo\argon_manter.py    # sobe o proxy local e o túnel -R 20141 até a VPS; religa se cair
```
E rode a seção 1 no PC que vai usar o VS Code.

---

## 6. Deixar ligando sozinho (sem janela)

```powershell
$py = (Get-Command python).Source -replace 'python.exe$','pythonw.exe'
schtasks /Create /TN "ArgonManter"  /SC MINUTE /MO 5   /TR "wscript.exe D:\rodar_oculto.vbs $py D:\gemini-argo\argon_manter.py" /F
schtasks /Create /TN "ArgonZelador" /SC DAILY /ST 04:00 /TR "wscript.exe D:\rodar_oculto.vbs $py D:\gemini-argo\argon_zelador.py" /F
schtasks /Create /TN "MonitorArgon" /SC MINUTE /MO 15  /TR "wscript.exe D:\rodar_oculto.vbs $py D:\gemini-argo\monitor_argon.py" /F
```
Avisos no Telegram (opcional): veja o topo de `D:\video-fila\avisos.py`. Sem isso eles vão só para
`D:\video-fila\avisos.log`.

---

## 7. Scripts e problemas comuns

| script | para quê |
|---|---|
| `gemini_http_proxy.py` | servidor do Argon (OpenAI-compatível), porta 20141 |
| `gemini_http.py` | o cliente HTTP puro (cookies, tokens da página, raciocínio Alto, reuso de conversa) |
| `argon_manter.py` | mantém o servidor e o túnel vivos |
| `argon_zelador.py` | renova os cookies das contas antes de morrerem |
| `monitor_argon.py` | cota de cada conta, hora em que volta, avisos |
| `probe_argon.py` | manda um "oi" na conta quando a cota dela deveria ter voltado (confirma de verdade) |
| `classificar_pro.py` / `descobrir_pro.py` | descobrem quais contas têm o "4 Argon" |
| `sync_cookies.py` / `extrair_cookies.py` | tiram os cookies do Chrome do cofre |
| `mcp_argon.py` | servidor MCP com a ferramenta `ask_argon` (usar o Argon como ajudante dentro do Claude Code) |
| `gemini_argon.py` + `gemini_proxy.py` | modo antigo por navegador (reserva; porta 20140) |
| `ordenar_contas_gemini.py`, `argon_relatorio.py` | ordem da fila; relatório dos turnos com ferramentas |
| `cadastrar_omniroute.py`, `enviar_contas_omniroute.py` | opcional: põe as contas como provedor `gemini-web` dentro do OmniRoute |

| Sintoma | O que fazer |
|---|---|
| Resposta rápida e fraca | cota do Argon acabou e o Google trocou pelo Flash. `monitor_argon.py` mostra quando volta |
| "Nenhuma conta com cota do Argon agora" | todas esgotaram; a mensagem traz a hora da volta. Use o Gemini 3.8 até lá |
| Conta "deslogada" de repente | cookie girou; rode `python sync_cookies.py <conta>` ou espere o zelador |
| VS Code: erro "argon inacessível" | PC desligado ou túnel caído: `argon_manter.py` e `ssh hermes-bloqueio echo ok` |
| Argon Pro dá erro, Argon puro funciona | a "mão" não existe no seu OmniRoute: ajuste o `argon_pro.txt` (seção 5) |
| "não encontrado D:\..." | as pastas não foram para a raiz do D: com os nomes certos (seção 3.2) |

---

## 8. O que ficou de fora (de propósito)

- `cookies\`, `cookies_youtube\`, `contas_argon.json`, `captura\` (tem cookies e tráfego gravado), logs, backups e
  estados. Também o token do OmniRoute que estava escrito no `enviar_contas_omniroute.py` (agora `COLOQUE_SEU_TOKEN_JWT`).
- Os scripts da pasta que não são do Argon (login do claude.ai, crédito do Opus, YouTube).
- O OmniRoute (programa de terceiros).
