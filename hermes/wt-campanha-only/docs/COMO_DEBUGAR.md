# COMO DEBUGAR — Investigação multi-tenant e bugs comuns

## Cenário 1: "Conta nova vê dados da conta principal"

Sintoma: usuário cria conta em janela anônima e a lista de sessões WhatsApp mostra as sessões do admin (ou `/api/settings/ai` mostra a chave do admin, etc).

### Passo 1 — Confirmar que o backend filtra certo

Rode um teste direto na API sem passar pelo frontend:

```bash
# Registra conta nova e pega o token
RESP=$(curl -s -X POST https://hermes3.inovareinteligenciaartificial.com/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"debug_$(date +%s)@x.com","password":"<SEGREDO_REMOVIDO>","name":"Debug","plan":"trial"}')
echo "$RESP"
TOKEN=$(echo "$RESP" | python -c "import json,sys;print(json.load(sys.stdin)['token'])")
UID=$(echo "$RESP" | python -c "import json,sys;print(json.load(sys.stdin)['user']['id'])")
echo "UID=$UID"

# Lista sessões da conta nova
curl -s https://hermes3.inovareinteligenciaartificial.com/api/sessions \
  -H "Authorization: Bearer $TOKEN"

# Lista custos
curl -s https://hermes3.inovareinteligenciaartificial.com/api/ai-cost \
  -H "Authorization: Bearer $TOKEN"

# Lê settings
curl -s https://hermes3.inovareinteligenciaartificial.com/api/settings \
  -H "Authorization: Bearer $TOKEN"

# Verifica /me retorna o UID certo
curl -s https://hermes3.inovareinteligenciaartificial.com/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Se /me retorna o UID da conta nova** e `/api/sessions` retorna `[]`, mas o navegador mostra sessões:
- **O frontend está com cache velho** → Ctrl+Shift+R, ou `localStorage.clear()` no DevTools (F12 → Application → Clear storage).
- **O frontend está com JWT antigo em memória** (caso: user abriu o site em janela logada, depois abriu anônima, mas o cookie de sessão foi compartilhado por algum motivo — improvável mas possível em alguns navegadores).
- **O frontend chama o endpoint errado**: olhe no DevTools → Network → filtre `/api/sessions` → veja qual token está sendo mandado.

**Se /me retorna o UID do admin** (ou outro user), o problema é:
- O JWT foi gerado errado. Veja `auth.go:handleAuthRegister` e `generateJWT(u.ID)`. O `u.ID` é o `RETURNING id` do INSERT. Se o INSERT falhou e o `Scan` não preencheu `u.ID`, o JWT fica com `sub=""` ou com o ID da última linha (improvável mas vale checar).
- O token foi gerado certo mas a chave JWT mudou entre deploys. Veja `HERMES_JWT_SECRET` no `docker service inspect hermes_call_v3_hermes-call-v3 | grep HERMES_JWT`. Se você mudou o secret, todo JWT antigo vira lixo e parseJWT retorna string vazia.

### Passo 2 — Confirmar que o banco está OK

```bash
ssh root@209.145.60.53
CN=$(docker ps -q --filter name=hermes_call_v3_pg_v3 | head -1)
docker exec $CN psql -U hermescall -d hermescall_main

# Quantas sessões e de quem?
hermescall_main=# SELECT id, name, COALESCE(jid,''), COALESCE(user_id::text,'<NULL>') FROM sessions ORDER BY created_at;

# Quantos users?
hermescall_main=# SELECT id, email, created_at FROM users ORDER BY created_at;
```

Se todas as sessões têm `user_id = <mesmo UUID>`, é porque a migration `UPDATE sessions SET user_id = $1 WHERE user_id IS NULL` rodou **com o UUID do admin** e vinculou sessões órfãs a ele. Se você vê a conta nova listando essas sessões, o token dela está sendo resolvido como admin. Volte ao passo 1.

### Passo 3 — Ativar access log

Edite `cmd/server/httpapi.go` na função `routes()` (linha ~17). Adicione um middleware:

```go
logged := func(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        rw := &statusWriter{ResponseWriter: w, status: 200}
        next.ServeHTTP(rw, r)
        uid := ""
        if u := userFromCtx(r); u != nil {
            uid = u.ID
        }
        s.log.Info("http",
            "method", r.Method,
            "path", r.URL.Path,
            "user", uid,
            "status", rw.status,
            "dur_ms", time.Since(start).Milliseconds(),
        )
    })
}

// e no return final:
var handler http.Handler = mux
handler = s.withUserAuth(handler)
handler = logged(handler)        // ← depois do withUserAuth pra ter userFromCtx
return withCORS(handler)
```

E adicione o tipo:
```go
type statusWriter struct {
    http.ResponseWriter
    status int
}

func (w *statusWriter) WriteHeader(code int) {
    w.status = code
    w.ResponseWriter.WriteHeader(code)
}
```

Depois do deploy, `docker logs --tail 200 $CN` vai mostrar:
```
time=... level=INFO msg=http method=GET path=/api/sessions user=66efcdc1-3099-4fed-8865-79bd2a9920df status=200 dur_ms=12
```

Aí você vê EXATAMENTE qual user está pedindo o quê.

---

## Cenário 2: "Disparo em massa não dá feedback"

Sintoma: usuário pede disparo via Telegram (`/campanha <lista>` ou via painel) e não recebe nenhuma mensagem de "iniciado", "concluído", "X enviados / Y falharam".

### Onde está o código

- `cmd/server/telegram.go` (1860 linhas) — o bot que processa comandos.
- `cmd/server/broadcast.go` (869 linhas) — o engine que faz o envio.
- `cmd/server/campaigns.go` (347 linhas) — persiste a campanha no banco.

### Passo 1 — Ver o handler de comando no telegram

```bash
grep -n "func.*handleCommand\|/campanha\|/disparo\|/broadcast\|sendMessage" cmd/server/telegram.go | head -30
```

Procure pela função que recebe o comando `/campanha` ou similar. Ela provavelmente:
1. Parseia o comando
2. Cria um `Campaign` via `campaigns.Create(...)` ou chama `broadcaster.Broadcast(...)`
3. **AQUI deveria mandar uma msg de feedback** tipo "Campanha iniciada, X contatos"
4. **O bug**: a msg de feedback não está sendo enviada, ou está sendo enviada pro chat_id errado, ou está usando o bot errado.

### Passo 2 — Ver o engine de broadcast

```bash
grep -n "func.*Broadcast\|func.*Send\|func.*Start" cmd/server/broadcast.go | head -20
```

Procure por uma função que faz o loop de envio. Ela DEVERIA ter callbacks de progresso. Se não tem, esse é o bug.

### Passo 3 — Adicionar feedback manual

Se você quer testar se o disparo está rodando, monitore os logs:

```bash
ssh root@209.145.60.53
CN=$(docker ps -q --filter name=hermes_call_v3_hermes-call-v3 | head -1)
docker logs -f $CN 2>&1 | grep -E "broadcast|campaign|message sent|delivered"
```

Se aparecer `message sent jid=...` mas você não recebe a msg no WhatsApp, é problema de envio (whatsmeow disconnected, rate limit do WhatsApp, etc).

Se não aparecer NADA, o broadcast nem começou.

---

## Cenário 3: "Dark mode fica branco"

Sintoma: o site está em dark mode mas o `body` fica branco, mesmo com a classe `dark` no `<html>`.

### Causa mais comum: `<style>` inline no `<head>` do `index.html`

O `index.html` no source tinha isso:
```html
<style>
  body { background-color: hsl(0 0% 100%); }
</style>
```

Esse `<style>` é MAIS ESPECÍFICO que `.dark body { background-color: ... }` no CSS do bundle. O navegador aplica o `<style>` do `<head>` por último em ordem de cascade.

**Fix:** remova o `<style>` inline e adicione um script inline que aplica `dark` no `<html>` no boot:

```html
<script>
  (function () {
    try {
      var t = localStorage.getItem("theme");
      if (!t) t = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      if (t === "dark") document.documentElement.classList.add("dark");
    } catch (e) {}
  })();
</script>
```

Já está aplicado no `d:/callagente/client/index.html`. Se o servidor ainda serve o HTML antigo, é cache do navegador (Ctrl+Shift+R) OU o deploy não rebuildou o client.

### Como saber se o deploy pegou:

```bash
curl -s https://hermes3.inovareinteligenciaartificial.com/ | grep "index-"
```

O hash do `<script src="/assets/index-XXXXX.js">` deve mudar entre builds. Se está o mesmo (`BqKvJiGE.js`) e você sabe que rebuildou, o deploy falhou.

---

## Cenário 4: "Deploy não está pegando"

Sintoma: você altera código, rebuilda, mas o site continua com a versão antiga.

### Confirme que o deploy está no service certo

```bash
ssh root@209.145.60.53
docker service ls | grep hermes
# Identifique qual service tem a regra do Traefik pra hermes3.inovareinteligenciaartificial.com
docker service inspect <service> | grep -E "traefik.http.routers|Image"
```

O `_build_and_deploy.py` foi ajustado pra apontar pra `hermes_call_v3_hermes-call-v3` (o service real que serve o domínio). Se voltar a quebrar, edite o script:

```python
# cmd 3:
"docker service update --force --image inovare/hermes-call-v3:latest hermes_call_v3_hermes-call-v3"
```

### Force cache-bust do navegador

O Traefik pode cachear. Force um hash novo no client:

```bash
# No client, force rebuild com hash novo
cd /d/callagente/client
# mude qualquer linha em src/main.tsx (ex: adicione um espaço) e salve
# vite vai gerar hash novo no bundle
```

---

## Cenário 5: "O som da ligação está cortando"

Desde 04/10 toda ligação termina com uma linha no registro da produção:

```bash
ssh hermes-prod 'journalctl -u hermes-call --since "1 hour ago" | grep "qualidade do áudio da ligação"'
```

Como ler (código: `internal/voip/call/audio_quality.go`):

| Campo | O que quer dizer | Se estiver alto |
|---|---|---|
| `resultado` | `boa`, `com cortes` ou `sem áudio` | `com cortes` também entra no diagnóstico (`call_audio_cortes`) |
| `rx_perda_pct` | % de pacotes do cliente que nunca chegaram (pela numeração) | rede do cliente ou do caminho; não é o nosso código |
| `rx_fora_ordem` | pacotes que chegaram depois do seguinte | rede instável; sem buffer de reordenação, cada um vira um estalo no que a IA ouve |
| `rx_buracos` / `rx_maior_buraco_ms` | intervalos > 200 ms sem receber nada | pode ser só silêncio (o celular para de mandar quando a pessoa cala); só pesa no `resultado` junto com perda acima de 1% |
| `rx_jitter_ms` | quanto o intervalo entre pacotes varia | acima de ~30 ms a rede está irregular |
| `tx_buracos` / `tx_maior_buraco_ms` | intervalos > 400 ms entre dois pacotes que NÓS mandamos (até ~300 ms é a passagem normal da fala pro silêncio) | o cliente ouve corte mesmo com rede boa: servidor ocupado ou voz atrasada. É nosso |
| `tx_erros_codificar` / `tx_erros_srtp` | falha ao codificar ou criptografar o que mandamos | codec ou chave; é nosso |

Regra rápida: `rx_*` ruim = rede; `tx_*` ruim = servidor. Se tudo estiver bom e a dona ainda ouvir corte, o
problema está depois do envio (celular dela, viva-voz) ou no conteúdo do áudio (gravação da oferta, voz da ElevenLabs).

## Comandos úteis

```bash
# Conexão SSH rápida
ssh root@209.145.60.53

# Container do app
CN=$(docker ps -q --filter name=hermes_call_v3_hermes-call-v3 | head -1)
docker logs --tail 200 $CN
docker exec $CN env | grep HERMES

# Container do Postgres
PG=$(docker ps -q --filter name=hermes_call_v3_pg_v3 | head -1)
docker exec $PG psql -U hermescall -d hermescall_main -c '\dt'
docker exec $PG psql -U hermescall -d hermescall_main -c "SELECT id, name, user_id FROM sessions"

# Tabelas por sessão (1 DB por sessão WhatsApp)
docker exec $PG psql -U hermescall -d hermescall_main -c "SELECT datname FROM pg_database WHERE datname LIKE 'hermescall_%'"

# Limpar uma sessão manualmente (use com cuidado!)
docker exec $PG psql -U hermescall -d hermescall_main -c "DELETE FROM sessions WHERE id='<session-id>'"
docker exec $PG psql -U hermescall -d hermescall_main -c "DROP DATABASE hermescall_<session-id>"
```
