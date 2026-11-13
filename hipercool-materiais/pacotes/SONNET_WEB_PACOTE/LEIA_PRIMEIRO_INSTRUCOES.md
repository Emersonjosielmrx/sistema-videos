# Pacote Sonnet web: Claude Sonnet 5.5 de graça, pelas contas gratuitas do claude.ai, no Claude Code

Este pacote tem o **código e a documentação** do "Sonnet web": várias contas **gratuitas** do claude.ai ligadas a um
servidor (OmniRoute) que aparece no Claude Code do VS Code como o modelo `cw/claude-sonnet-5-5`, com rodízio entre as
contas. Responde em 1 a 7 segundos e aceita ferramentas (ler arquivo, editar, rodar comando).

**Não vem nenhuma credencial:** nem cookies, nem chaves, nem tokens, nem a lista de contas, nem IPs, nem telefone. No
lugar há marcadores como `COLOQUE_SEU_TOKEN_JWT`, `IP_DA_SUA_VPS`, `sua_conta@gmail.com` e `conta_exemplo`. Os nomes
reais das contas foram trocados por `conta_exemplo` também dentro dos textos de histórico (`PROGRESSO.md`).

---

## 0. Escolha o caminho

| Você quer… | Faça |
|---|---|
| **Só usar** o Sonnet web num PC novo, com o servidor que já existe ligado | Seção 1 (5 minutos) |
| **Montar do zero** (sua VPS, suas contas do claude.ai) | Seções 2 a 7 |

---

## 1. Só usar

1. Instale o **VS Code** e, dentro dele, a extensão **Claude Code** (Anthropic).
2. Na pasta `SO_USAR_cliente_vscode`, clique com o botão direito em `instalar_sonnet_web.ps1` > **Executar com o PowerShell**.
3. Ele pergunta o **IP da VPS**, a **porta** (Enter = 20133) e a **chave do OmniRoute** (começa com `sk-`; fica no PC
   principal, nas configurações do VS Code, em `ANTHROPIC_AUTH_TOKEN`).
4. Feche todas as janelas do VS Code e abra de novo. O chat já começa no **Sonnet 5.5 web**.

Desfazer: copie os `settings.json.bak-sonnet` por cima dos `settings.json`.

Bom saber:
- **Não vê imagem de forma nativa.** Se a VPS tiver o `visao.mjs` (seção 4), outro modelo seu que enxerga descreve a
  imagem e a descrição entra como texto. Sem isso, imagem não funciona.
- Conta gratuita do claude.ai tem **limite por janela de 5 horas**. Quando uma conta bate no limite (erro 429) o servidor
  põe ela 10 minutos de lado e usa a próxima. **Mais contas = mais cota.**
- Sempre vai em esforço máximo (o proxy injeta `reasoning_effort: max`).

---

## 2. Como funciona

```
VS Code (Claude Code)  ── ANTHROPIC_BASE_URL = http://IP_DA_SUA_VPS:20133   (ou :20128 direto no OmniRoute)
   ▼
VPS: proxy.mjs :20133   (opcional) ── esforço máximo + descreve imagens (visao.mjs)
   ▼
VPS: OmniRoute :20128 (Docker) ── provedor "claude-web" (prefixo cw/), N contas, rodízio "fill-first"
   ▼
claude.ai ── cada conta entra com o cookie de sessão (sessionKey) dela
```

- **No PC** ficam os scripts que criam/entram na conta do claude.ai pelo "Continuar com Google" (Chrome de cada conta no
  **cofre**), tiram o cookie `sessionKey` e renovam antes de vencer (a sessão dura ~4 semanas).
- **Na VPS** fica o OmniRoute (programa de terceiros, não vem no pacote), que já traz o provedor `claude-web`, e alguns
  scripts pequenos que leem/organizam as contas no banco dele.
- O OmniRoute joga o histórico inteiro como uma conversa nova do claude.ai a cada pedido. Por isso as contas grátis
  esgotam mais rápido que no site: planeje várias.

Leitura recomendada (dentro de `sonnet web`): `PROGRESSO.md` (tudo o que foi descoberto, com datas) e
`COMPARACAO_ARGON_x_CLAUDEWEB.md`.

---

## 3. Preparar o PC

### 3.1 Programas
**Python 3.11+** (marque "Add python.exe to PATH"), **Git for Windows** (traz o `ssh`) e **Google Chrome** em
`C:\Program Files\Google\Chrome\Application\chrome.exe`.

### 3.2 Copiar as pastas
O código usa caminhos fixos no **D:**. Copie tudo de dentro de `COPIAR_PARA_O_DISCO_D` para a raiz do `D:\`, sem mudar os
nomes:
```
D:\sonnet web\                                  o Sonnet web
D:\logins-google\cofre.py                       cofre (um perfil de Chrome por conta Google)
D:\hipercool-materiais\comum\sem_janela.py
D:\postador-de-videos\bin\claude_criar.py       cria/entra na conta do claude.ai
D:\postador-de-videos\bin\maquina_remota.py     versão que usa só ESTE PC (o "pc2" dos scripts = este computador)
D:\postador-de-videos\bin\netbooks\chrome_conta.py
D:\video-fila\avisos.py                         avisos (versão simples; Telegram opcional)
D:\rodar_oculto.vbs                             roda as tarefas sem abrir janela
```
Sem disco D? No PowerShell como administrador: `mkdir C:\IA` e depois `subst D: C:\IA`
(o `subst` some ao reiniciar; para ficar fixo, crie uma tarefa "ao fazer logon" com esse comando).

### 3.3 Bibliotecas
```powershell
pip install -r requirements.txt
```
(O Playwright só se conecta ao Chrome instalado: não precisa baixar navegador dele.)

### 3.4 SSH até a VPS
Siga `VPS_exemplos\ssh_config_exemplo.txt`. Dê à VPS o apelido **`hermes-bloqueio`** (é o nome que os scripts usam).
`ssh -o BatchMode=yes hermes-bloqueio echo ok` tem que responder `ok` sem pedir senha.

### 3.5 Contas Google no cofre
Cada conta Google que vai virar conta do claude.ai entra no cofre uma vez (abre o Chrome; você digita a senha):
```powershell
cd D:\logins-google
python cofre.py logar sua_conta@gmail.com
python cofre.py checar
```

> ⚠️ **Várias contas no mesmo IP é o maior risco.** Google e claude.ai podem ligar contas que saem do mesmo IP e barrar
> várias de uma vez (já aconteceu com outro serviço: 14 contas banidas juntas). Regras:
> - **uma conta por vez**, nunca um laço "faz todas"; espalhe os logins ao longo dos dias;
> - comece com 3 a 5 contas e veja se aguentam antes de criar mais;
> - depois de uns 30 logins em poucas horas o Google/Cloudflare começou a barrar ("sem_botao" / "ficou_no_login");
> - se uma conta for banida, **não reuse o IP dela** para outra conta nova.
> Por isso o `lote_contas.py` (que fazia dezenas em sequência) **não vem** neste pacote.

---

## 4. VPS (servidor)

Precisa de uma VPS Linux (Ubuntu) com Docker e Node.js 20+.

1. **OmniRoute** (não vem no pacote). Instale pela documentação dele, em Docker, com o contêiner chamado `omniroute`, a
   porta **20128** e os dados em `/opt/omniroute/data`. No painel crie uma **chave de API** (`sk-...`): é a que o VS Code usa.
2. **Scripts na VPS:** copie os `*_vps.py` de `sonnet web` para `/opt/omniroute/` **com estes nomes**:

| do pacote | na VPS |
|---|---|
| `cadastrar_omniroute_vps.py` | `/opt/omniroute/cadastrar_claude_web.py` |
| `ler_claude_web_vps.py` | `/opt/omniroute/ler_claude_web.py` |
| `sonnet_estado_vps.py` | `/opt/omniroute/sonnet_estado.py` |
| `sonnet_oi_vps.py` | `/opt/omniroute/sonnet_oi.py` |
| `ordenar_contas_cw_vps.py` | `/opt/omniroute/ordenar_contas_cw.py` |
| `combo_sonnet_fila_vps.py`, `combo_inverter_vps.py` | opcionais (só se você também tem contas pagas do Claude Code) |

3. **Tarefas na VPS** (`crontab -e`):
```
* * * * *   python3 /opt/omniroute/sonnet_oi.py          # manda um "oi" na conta quando o limite dela deveria ter passado
*/2 * * * * python3 /opt/omniroute/ordenar_contas_cw.py  # contas que respondem vão para a frente da fila
```
4. **Proxy :20133 (opcional)** dá esforço máximo e descrição de imagem:
```bash
mkdir -p /opt/antigravity-cc-proxy
# do pacote: sonnet web/proxy_vps_snapshot.mjs -> /opt/antigravity-cc-proxy/proxy.mjs
#            sonnet web/visao.mjs              -> /opt/antigravity-cc-proxy/visao.mjs
cp antigravity-cc-proxy.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now antigravity-cc-proxy
```
   O `proxy_vps_snapshot.mjs` também tem rotas de outros sistemas (Argon, Genspark, Cline): ignore, só entram em ação
   se o nome do modelo for o deles. O `visao.mjs` usa o modelo `agy/gemini-3.8-flash-high` para descrever imagens; se o
   seu OmniRoute não tem esse, defina a variável `VISAO_MODELO` no serviço com um modelo seu que enxergue.
   Sem o proxy, aponte o VS Code direto para a porta 20128 (o instalador pergunta a porta).
5. Libere no firewall só a **20133** (e o SSH). A 20128 pode ficar fechada para fora.

---

## 5. Cadastrar as contas (uma por vez)

No PC, para **cada conta** (uma de cada vez, espaçadas):
```powershell
# 1) criar/entrar no claude.ai com o Google da conta (abre o Chrome; plano GRATUITO; espera 40 s e fecha)
python D:\postador-de-videos\bin\claude_criar.py conta_do_cofre
# 2) ler o cookie sessionKey e guardar em D:\sonnet web\segredos\cookies.json
python "D:\sonnet web\pegar_cookies.py" conta_do_cofre
# 3) cadastrar no OmniRoute (atualiza as que já existem, só cria a nova)
type "D:\sonnet web\segredos\cookies.json" | ssh hermes-bloqueio 'S=$(docker exec omniroute printenv INITIAL_PASSWORD); python3 /opt/omniroute/cadastrar_claude_web.py "$S"'
# 4) OBRIGATÓRIO: desligar o health check do OmniRoute (o Cloudflare barra a VPS e ele marcaria as contas como "expired" à toa)
ssh hermes-bloqueio "sqlite3 /opt/omniroute/data/storage.sqlite \"UPDATE provider_connections SET health_check_interval=0, test_status='active' WHERE provider='claude-web'\""
```
Teste (na VPS, troque a chave):
```bash
curl -s localhost:20128/v1/chat/completions -H "Authorization: Bearer sk-SUA_CHAVE" -H "Content-Type: application/json" \
  -d '{"model":"cw/claude-sonnet-5-5","messages":[{"role":"user","content":"quanto e 17x23?"}]}'
```
Tem que vir `391` e um id começando com `chatcmpl-`.

> O `cookies.json` é **segredo**: é a sessão logada de cada conta. Não copie nem compartilhe. Ele nunca sai de
> `D:\sonnet web\segredos\`.

Conta nova no claude.ai pode pedir **telefone/SMS**: o `claude_criar.py` para e não pede código. Resolva à mão.

---

## 6. Deixar cuidando sozinho (PC, sem janela)

```powershell
$py = (Get-Command python).Source -replace 'python.exe$','pythonw.exe'
schtasks /Create /TN "ZeladorSonnet" /SC DAILY /ST 04:20 /TR "wscript.exe D:\rodar_oculto.vbs $py `"D:\sonnet web\zelador_sonnet.py`"" /F
schtasks /Create /TN "MonitorSonnet" /SC MINUTE /MO 10 /TR "wscript.exe D:\rodar_oculto.vbs $py `"D:\sonnet web\monitor_sonnet.py`"" /F
```
- `zelador_sonnet.py`: renova o cookie das contas que vencem em menos de 14 dias (no máximo 5 por rodada). Apaga o
  `sessionKey` no Chrome da conta, entra de novo pelo Google e atualiza a conta no OmniRoute sem duplicar. Se a conta
  continuar dando 403 com sessão nova, ela está **barrada no claude.ai**: o zelador a desliga e lista em
  `contas_barradas.json`. `--simular` só mostra quem renovaria.
- `monitor_sonnet.py`: avisa quando todas as contas estão sem uso e quando voltam (confirma com 2 respostas reais).
  `--status` só imprime.
- Avisos no Telegram (opcional): veja o topo de `D:\video-fila\avisos.py`. Sem configurar, vão só para
  `D:\video-fila\avisos.log`.

---

## 7. Problemas comuns

| Sintoma | O que fazer |
|---|---|
| 429 "Rate limited by Claude Web API" | limite do plano grátis; a conta fica 10 min de lado e volta sozinha. Mais contas = mais cota |
| Conta aparece "expired" sem motivo | faltou o `UPDATE ... health_check_interval=0` do passo 4 da seção 5 |
| 403 `permission_denied` mesmo com sessão nova | conta barrada no claude.ai (o zelador desliga). Religar: `UPDATE provider_connections SET is_active=1 WHERE provider='claude-web' AND name='claude-web <conta>'` |
| claude.ai "Não foi possível verificar seu navegador" | o Cloudflare barrou o Chrome automatizado. Tente mais tarde, com menos contas seguidas |
| 502 "message_start is out of order" | falha ocasional do claude.ai; repita o pedido |
| Imagem não é entendida | instale o `visao.mjs` no proxy (seção 4) |
| Modelo não aparece no seletor do VS Code | rode o instalador de novo e feche TODAS as janelas do VS Code |
| Script reclama de `D:\...` não encontrado | as pastas não foram para a raiz do D: com os nomes certos (seção 3.2) |

---

## 8. O que ficou de fora (de propósito)

- `segredos\cookies.json`, logs, estados (`estado.json`, `monitor_sonnet.json`, `contas_*.json`), backups `.bak`.
- O `lote_contas.py` (criava dezenas de contas em sequência pelo mesmo IP: perigoso).
- O `maquina_remota.py` original (mapa de máquinas com IPs): no lugar vai uma versão que usa só este PC.
- O `avisos.py` original (bots do Telegram): no lugar vai uma versão simples.
- O OmniRoute (programa de terceiros: instale pela documentação dele).
