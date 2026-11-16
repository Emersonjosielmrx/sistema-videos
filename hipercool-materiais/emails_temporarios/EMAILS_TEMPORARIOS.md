# E-mails temporários operáveis por programa: testes reais de 15/11/2026

Pasta: `D:\hipercool-materiais\emails_temporarios\`. Todos os testes saíram pelo **Webshare grátis**, nunca pela casa:
a criação e a leitura das caixas pelo proxy rotativo (`-rotate`), e o Kaggle por uma saída fixa `-N` diferente
por conta de teste (a lista fica em `saidas_usadas.json`). Nenhuma conta Google ou real foi usada. A dona autorizou
usar o Webshare grátis no Kaggle para este teste.

## Resumo
1. **Criar e ler caixa por API funciona em 9 serviços**: mail.tm, guerrillamail, tempmail.lol, maildrop.cc,
   tempmail.plus, temp-mail.io, mailnesia, inboxkitten, harakirimail e **emailnator (Gmail real, pelo navegador)**.
2. **O Kaggle recusa no próprio campo de e-mail TODOS os domínios descartáveis testados (32)**, com "Invalid Email."
   Como a recusa acontece antes de qualquer envio, nenhum desses serviços recebe e-mail do Kaggle.
3. **Só o emailnator passou**, porque dá um endereço `@gmail.com` de verdade (truque dos pontos). O Kaggle aceitou
   `yaranvaer.nta@gmail.com` no campo. O cadastro parou no **reCAPTCHA v2 de imagens**, que precisa de uma pessoa.
4. Prova de que a caixa do emailnator recebe e-mail de fora: a lista dela já trazia mensagens reais (ex.: SHEIN).
   **Ainda falta provar a chegada do e-mail do Kaggle**: alguém precisa resolver o captcha uma vez.

## Tabela: API (criar e ler) + Kaggle
| Serviço | Criar caixa | Ler | Kaggle aceita? | Como (endpoint) |
|---|---|---|---|---|
| **emailnator** | OK | OK | **SIM** (gmail.com) | Chrome headless pelo proxy; `fetch POST /api/generate-email {"ids":[3]}` (3=dotGmail, 2=+Gmail, 8=googlemail, 1=domínio próprio) e `POST /api/message-list {"email":..}`. Cloudflare e botwafguard bloqueiam requests puro. Fechar a janela de anúncio (`.fc-message-root`). `emailnator.py` |
| mail.tm | OK | OK | não (fldubai.com) | `GET api.mail.tm/domains` → `POST /accounts` → `POST /token` → `GET /messages` (Bearer) |
| mail.gw | proxy 502/402 | - | não testado | mesma API do mail.tm em `api.mail.gw` (só falhou o proxy) |
| tempmail.lol | OK | OK | não (*.roomsranked.com, *.marchslurp.com) | `POST api.tempmail.lol/v2/inbox/create` → `GET /v2/inbox?token=` |
| guerrillamail | OK | OK | não (guerrillamailblock, sharklasers, grr.la, pokemail, spam4.me, guerrillamail.com/.net) | `ajax.php?f=get_email_address` / `get_email_list&sid_token=`. **Enviar (`send_email`) pede captcha** |
| maildrop.cc | OK | OK | não | GraphQL `api.maildrop.cc/graphql`: `inbox(mailbox:"x"){id headerfrom subject}`. Às vezes dá 403 por IP |
| tempmail.plus | OK (qualquer nome) | OK | não (mailto.plus, fexpost, fexbox, mailbox.in.ua, rover.info, chitthi.in, fextemp, any.pink, merepost) | `GET tempmail.plus/api/mails?email=x@mailto.plus` |
| temp-mail.io | OK | OK | não (os 7 domínios: bwmyga, lnovic, ruutukf, gmeenramy, olipii, ooynib, tanpony) | `POST api.internal.temp-mail.io/api/v3/email/new` → `GET /api/v3/email/{e}/messages` |
| mailnesia | OK (qualquer nome) | OK (HTML) | não | `GET mailnesia.com/mailbox/{nome}` (raspagem) |
| inboxkitten | OK (qualquer nome) | OK | não | `GET inboxkitten.com/api/v1/mail/list?recipient=` |
| harakirimail | OK (qualquer nome) | OK | não | `GET harakirimail.com/api/v1/inbox/{nome}` |
| mailinator | endereço sim | **X** (a API pública devolve HTML) | não | a leitura por API exige token pago |
| yopmail | endereço sim | **X** | não | sem API; captcha e tokens `yp`/`yj` |
| dropmail.me | **X** | - | - | `legacy_token_disabled`: o token público acabou; precisa de token novo do site |
| 1secmail | **X** | - | - | certificado SSL inválido: serviço morto |
| developermail | proxy 402/502 | - | - | `PUT /api/v1/mailbox` (não chegou a responder) |

Prova: `resultado_api.json`, `kaggle_dominios_1.json`, `kaggle_dominios_2.json`, `resultado_kaggle.json`, `prints\`.
Domínios reais (gmail, outlook, proton.me) foram aceitos no mesmo campo, o que confirma que a recusa é por lista de descartáveis.

## Caminhos fechados (não repetir)
- **SMTP direto** (enviar ao MX `in.mail.tm:25`): o Webshare bloqueia a porta 25 (`client_connect_forbidden_port`).
- **Guerrilla como remetente** (`send_email`): pede captcha (`needs_captcha:true`).
- **Saída -7 do Webshare grátis**: o Kaggle devolve 404 na página (IP bloqueado, já anotado no METODOS).

## Achado sobre o Webshare grátis (atenção, regra de IP)
Na 1ª exploração, a saída `-7` de uma conta saiu por **23.129.254.124**. Depois, por 4 contas diferentes, saiu sempre
por **38.154.185.97**. Ou seja, **o `-N` NÃO é o mesmo IP em 100% das contas grátis**: há contas com outra lista.
Isso não muda a regra (IP de banida não se reusa), mas o mapa N → IP precisa ser conferido por conta.

## Saídas -N gastas neste teste (contas de teste descartáveis, nenhuma criada de fato)
-7 (38.154.185.97, 404), -1 (198.23.243.226), -2 (45.38.107.97, também usada para checar domínios), -3 (104.164.49.38).
Nenhum formulário foi enviado: o captcha expirou nas 2 tentativas, então **nenhuma conta Kaggle existe**.

## Próximo passo para fechar a prova de chegada
`python kaggle_email_teste.py testar emailnator 5` abre o Chrome **visível** na tela. A dona marca o "I'm not a robot"
e resolve as imagens (há 4 min). Depois disso o script envia, lê o `message-list` do Gmail do emailnator a cada 20 s
por até 6 min e grava em `resultado_kaggle.json` se o e-mail do Kaggle chegou e em quantos segundos.
Atenção: a caixa do emailnator é **compartilhada e pública** (outros usuários veem). Não serve para conta que importa.

## Arquivos
- `testar_provedores.py`: 15 provedores (criar e ler). `python testar_provedores.py [prov...]` e `ler <prov>`.
  Usa só contas grátis com banda no momento (testa antes; 402 = troca).
- `emailnator.py`: Gmail temporário pelo navegador headless (classe `Emailnator`: `criar()`, `ler()`, `fechar()`).
- `kaggle_email_teste.py`: `explorar N`, `dominios N <emails...>` (checa só o campo, não cria conta), `testar <prov> N`.
  Recusa repetir uma saída e para se o IP de saída for o da casa.
- `teste_chegada.py`: envio entre caixas (bloqueado pelo captcha do Guerrilla; fica para outro remetente).
- `espiar_xhr.py <url>`: lista as chamadas XHR de um site para descobrir a API interna dele.
