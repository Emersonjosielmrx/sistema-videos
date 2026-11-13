# CLAUDE.md — FluxIA

> Alternativa ao n8n para agentes de WhatsApp. Usa a API do Hermes Call como backend de WhatsApp.

## O que é
Plataforma para criar e acompanhar agentes de atendimento por WhatsApp sem montar fluxo à mão.
Todo fluxo passa pelas mesmas etapas (os blocos do editor visual), cada uma com opções editáveis:
mensagem recebida → loja assumiu? → horário → agrupar mensagens → tipo de mensagem (texto/áudio/imagem/
documento/botão) → agente IA → ações (comprovante, pedido/Pix, agendamento, atendente) → enviar → botões.
Um fluxo novo nasce de um **modelo** (`delivery_link`, `delivery_pix`, `atendimento`, `agendamento`) com tudo preenchido.

Logins: **admin** (painel completo) e **cliente** (`/cliente`: conecta o WhatsApp, liga/desliga, horário,
avisos, comprovantes, conversas que a loja assumiu, troca de senha).

## Stack
- **Backend:** Python 3.12, FastAPI, SQLite (aiosqlite), httpx, cryptography (decifra mídia do WhatsApp)
- **Frontend:** React 18 + TypeScript + Vite + Tailwind v4 + @xyflow/react (editor) + lucide. Tema e componentes copiados do Hermes Call (`src/index.css`, `src/components/ui.tsx`)
- **WhatsApp:** API do Hermes Call (URL e chave em Configurações, tabela `settings`). A chave é da conta própria `fluxia@inovareinteligenciaartificial.com` no Hermes (enterprise, Agente de IA desligado); as linhas das lojas ficam nela
- **IA (OmniRoute `http://157.173.207.22:20128`, sem chave):** texto `cc/claude-haiku-5-5`; imagem e "ensinar" `cc/claude-sonnet-5-5` (o Haiku trava com imagem); áudio `groq/whisper-large-v3-turbo` em `/v1/audio/transcriptions`. Nome de modelo sem prefixo de provedor dá erro.

## Como o WhatsApp chega
O Hermes manda tudo por **webhook por sessão** (`FLUXIA_PUBLIC_URL/api/webhook/hermes/<token>`):
- `message`: `chat`, `fromMe`, `isGroup`, `type`, `text`, `pushName`, `raw` (protojson; a mídia vem com `mediaKey`/`directPath`, o FluxIA baixa de `mmg.whatsapp.net` e decifra em `media.py`)
- `poll_vote`: `pollMessageId`, `chat`, `selectedNames` → é assim que funcionam os **botões** (enquete do WhatsApp)
- `fromMe=true` que não saiu do FluxIA (IDs guardados em `engine.SENT_IDS`) = a loja respondeu à mão → IA pausa naquela conversa
Se o Agente de IA da conta do Hermes estiver ligado, o cliente final recebe duas respostas.

## Modo administrador pelo WhatsApp
Números em Configurações (`admin_phones`, padrão 5591984698653; aceita com/sem o 9 e o formato LID via
`/contacts/{jid}` do Hermes). Quem escreve desses números para o WhatsApp de um fluxo não é atendido como
cliente: `menu` (botões), texto livre = ensinar (`teach.py`, Sonnet devolve JSON com regras/campos),
`simular` / `reiniciar` / `sair`, `regras`, `apagar regra N`, `desfazer`, `ligar`/`desligar`, `status`,
`prompt`, `reiniciar 9198...`. Áudio vale como instrução. Toda mudança gera versão (`flow_versions`).

## Variáveis de ambiente
`FLUXIA_SECRET`, `FLUXIA_ADMIN_EMAIL`, `FLUXIA_ADMIN_PASSWORD` (só no 1º start), `FLUXIA_PUBLIC_URL`,
`FLUXIA_AI_URL`, `FLUXIA_MODEL`, `FLUXIA_VISION_MODEL`, `FLUXIA_SMART_MODEL`, `FLUXIA_TRANSCRIBE_MODEL`,
`FLUXIA_DB`, `FLUXIA_UPLOADS`, `FLUXIA_DIST`.

## Como rodar local
```bash
pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..
python -m uvicorn backend.main:app --port 8100
```
Teste de ponta a ponta (Hermes simulado + IA real): `D:\temp\fluxia_test\e2e_v2.py` (fora do projeto, pode não existir mais).

## Produção (VPS 157, `ssh hermes-bloqueio`)
- Pasta `/opt/fluxia` (`src/` = código, `.env` com segredos, `fluxia-stack.yml`). Stack Swarm `fluxia`, serviço `fluxia_fluxia`, volume `fluxia_fluxia_data` (banco `/data/fluxia.db`, mídias em `/data/uploads`).
- URL: https://fluxia.157-173-207-22.sslip.io (Traefik + Let's Encrypt).
- Atualizar: ver o fim do `PENDENCIAS.md` (envia para uma pasta limpa: sobras da versão antiga, como `postcss.config.js`, quebram a build).

## Mapa de arquivos
| Caminho | O que é |
|---|---|
| `backend/main.py` | Rotas: admin, cliente, webhook, teste, painel |
| `backend/flow_config.py` | Modelos de fluxo, valores padrão, validação (`normalize`), variáveis do prompt `{{...}}` |
| `backend/engine.py` | Motor: etapas de cada mensagem, registro das etapas na execução, envio |
| `backend/webhook.py` | Recebe o Hermes: agrupa mensagens, votos, pausa quando a loja responde, desvia o admin |
| `backend/admin_chat.py` | Modo administrador pelo WhatsApp |
| `backend/teach.py` | Ensinar o agente, versões, desfazer |
| `backend/media.py` | Baixar/decifrar mídia do WhatsApp e transcrever áudio |
| `backend/agent.py` | Chamada da IA (OmniRoute, formato Anthropic) |
| `backend/hermes.py`, `backend/pix.py`, `backend/db.py`, `backend/auth.py` | Hermes, Pix BR Code, banco, login |
| `frontend/src/pages/FlowEditor.tsx` | Editor visual (canvas, painel do bloco, testar, execuções, conversas, versões) |
| `frontend/src/flow/nodes.tsx`, `panels.tsx` | Blocos do canvas e formulários de cada bloco |
| `frontend/src/pages/ClientHome.tsx` | Tela da loja (celular primeiro) |
| `Dockerfile`, `deploy/fluxia-stack.yml` | Deploy |
| `PENDENCIAS.md` | O que falta |

## Regras
- Segredos (API keys, senhas) não vão para arquivos do projeto nem para o chat: ficam no `.env` da VPS ou no banco
- Responder em pt-BR
