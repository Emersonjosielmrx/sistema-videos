# 07 — Extrator "Garimpo WhatsApp" (Conversas Ativas)

**Esforço:** médio. **Impacto:** alto (cria campanhas de prospecção em 1 clique).
**STATUS: BACKEND FEITO E NO AR (2026-07-21).** `GET /api/whatsapp/chats` implementado.

> ⚠️ CORREÇÃO DA SPEC (o doc estava errado — verificado no código):
> - **NÃO é Baileys/Evolution API.** Este projeto usa **whatsmeow NATIVO** e já persiste as
>   conversas (`messagestore.listChats`). O handler reusa isso.
> - **NÃO existe tabela `contacts`** nem `POST /api/campaigns`. "Desconhecido" = número sem
>   lead em `contact_leads`. O disparo em massa usa `POST /api/mass-call` (telefones crus),
>   que **não exige cadastro prévio** — logo o "upsert silencioso" que a spec pedia é
>   desnecessário (não há onde/por que cadastrar antes).

## Onde no front
- Arquivo: `client/src/components/crm/WhatsAppExtractorTab.tsx`

## Contrato do endpoint (o que o front manda e espera)

### Listar Chats Recentes
- `GET /api/whatsapp/chats`
- Query Params:
  - `?filter=all` (Padrão: Traz chats ordenados por data decrescente da última mensagem)
  - `?filter=unknown` (Traz apenas chats cujo telefone não existe na tabela `contacts`)
  - `?filter=unread` (Traz apenas conversas não lidas/sem resposta do atendente)
  - `?timeFilter=all|today|24h|week` (Filtragem por data da última mensagem)
  - `?limit=50`
- Response esperada:
```json
[
  {
    "id": "5511999999999@s.whatsapp.net",
    "phone": "5511999999999",
    "name": "João da Silva", 
    "lastMessage": "Pode me mandar a chave pix?",
    "time": "10:42",
    "date": "2026-07-21T10:42:00Z",
    "unread": true,
    "isUnknown": false,
    "iaTag": "Pronta pra Comprar",
    "sentiment": "positive"
  }
]
```
*(Nota: `iaTag` e `sentiment` podem ser preenchidos assincronamente pela LLM ou vir nulos caso não haja inteligência processada na mensagem).*

### Disparo da campanha a partir dos selecionados (FRONT: use o que já existe)
`POST /api/campaigns` **não existe** neste backend. Pra disparar os números garimpados,
o front deve usar uma das rotas reais (aceitam telefones crus, SEM exigir cadastro prévio —
por isso não há upsert a fazer):
- **Ligação em massa:** `POST /api/mass-call` — body `{phones:[], names?:[], session_id?, delay_between_s?}`.
- **Mensagem em massa:** `POST /api/mass-message`.
- **Ou** reusar `POST /api/crm/stage-action` (doc 06) se os leads já estiverem numa etapa.
Escolha conforme o "tipo de campanha" que a dona clicar. Nenhum backend novo é necessário aqui.

## Schema (se precisa tabela/coluna nova)
Nenhuma tabela estrutural nova é necessária para a rota GET. Os dados dos chats vêm do estado do provedor do WhatsApp (Evolution API / cache do Baileys).

## Passo a passo backend (Go)
1. Criar (se não houver) um handler para conversas ativas em `cmd/server/whatsapp_api.go` ou similar.
2. Adicionar o registro `GET /api/whatsapp/chats` em `cmd/server/httpapi.go`.
3. A lógica do handler deve bater no serviço da Evolution API, cruzar com a tabela de `contacts` local para marcar quem é `isUnknown=true`, e aplicar os filtros de query string.
4. Ajustar o endpoint de criação de campanhas (`campaign_api.go` ou equivalente) para iterar sobre os leads alvo; caso algum não exista no banco, faça um `INSERT` básico.

## Como testar (pronto quando)
- A tela "Garimpo WhatsApp" carrega as conversas reais do número conectado ao carregar.
- Os botões de filtro "Desconhecidos" isolam corretamente.
- Ao selecionar um lead não-cadastrado e gerar campanha, a engine não devolve erro 404 e sim enfileira o envio.
