# nginx P1-1 patch — /login rewrite

## Symptom
`/login` na landing publica mostra a landing page (HTML da landing, nao o app React).
A app React sobe em `/` e em `/dashboard`, mas a rota `/login` nao existe na landing — cai no catch-all da landing que devolve o index.html dela.

## Diagnose
```bash
curl -sS -o /dev/null -w "%{http_code}\n" https://hermescall.opus-sem-limites.com.br/login
# 200 (landing, nao app)
```

## Fix
No VPS, editar `/etc/nginx/sites-available/hermescall` (ou o arquivo correspondente) e garantir:

```nginx
server {
    listen 443 ssl http2;
    server_name hermescall.opus-sem-limites.com.br;

    # ... SSL config existente ...

    # Frontend React (client/) — serve index.html pra qualquer rota SPA
    location / {
        root /var/www/hermescall/client-dist;
        try_files $uri $uri/ /index.html;
    }

    # /login e outras rotas SPA: rewrite pro mesmo index.html
    # (necessario pq /login e rota client-side, nao tem arquivo estatico)
    location ~ ^/(login|dashboard|chat|calls|agents|crm|catalog|agenda|meeting|manager) {
        root /var/www/hermescall/client-dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend Go
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Depois:
```bash
sudo nginx -t
sudo systemctl reload nginx
curl -sS -o /dev/null -w "%{http_code}\n" https://hermescall.opus-sem-limites.com.br/login
# agora deve ser 200 com HTML da app React (procurar por <div id="root">)
```

## Verificacao automatica
Rodar o teste smoke apos o reload:
```bash
cd tests
npm run test:e2e -- 02-ui-smoke --grep "smoke UI @ start_voz"
# espera nao redirecionar pra landing HTML
```

## Por que nao foi feito automaticamente
- O VPS nao esta acessivel pelo Node do deploy (deploy-beta sobe codigo, nao reconfigura nginx).
- Precisa sudo pra editar /etc/nginx/sites-available/.
- O usuario aplica este patch manualmente junto com `node deploy/deploy-beta.js`.
