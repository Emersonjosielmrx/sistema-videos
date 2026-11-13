# 🤝 HANDOFF — Veo API + n8n (gerar vídeo IA por HTTP)

> **Para o próximo agente.** Escrito em 2026-07-03. Tudo aqui foi **testado e validado
> ponta a ponta** (execução n8n `144024` = success). Leia este doc primeiro; os detalhes
> finos estão em `API_PARA_N8N.md`.

---

## 1. O QUE É / OBJETIVO

Transformamos a automação do **Google Flow/Veo** (que gera vídeo IA 9:16 com áudio e
fala PT-BR) numa **API HTTP assíncrona** que o **n8n remoto** chama. O n8n manda um
prompt, a API aciona o navegador aqui, o Flow renderiza, e o vídeo volta pro n8n por URL.

**Ciclo completo validado:**
```
Webhook n8n → POST cria job na API (via túnel Cloudflare) → API dirige o Chrome/Flow →
Veo renderiza (~1–15 min) → n8n faz polling → status "done" → n8n baixa o mp4 → success
```
Resultado: mp4 **720x1280 (9:16), h264, aac estéreo, 8s**.

---

## 2. ONDE FICA / ARQUIVOS

Pasta: **`D:\hipercool-inferior-fix\roteador-veo-api-fake\`**
Python: **SEMPRE** `D:/hipercool-videos/venv/Scripts/python.exe` + `PYTHONUTF8=1`.

| Arquivo | Função |
|---|---|
| `veo_api.py` | **Servidor da API** (assíncrono, job_id + polling). ← o que sobe |
| `gera_auto.py` | Motor da automação do Flow (Playwright/CDP). A API chama `gera_auto.gerar()` |
| `API_PARA_N8N.md` | Doc detalhada de endpoints, env e fluxo n8n |
| `_criar_workflow_n8n.py` | Cria/atualiza o workflow no n8n via Public API |
| `bin_tunnel/cloudflared.exe` | Binário do túnel Cloudflare |
| `.api_token` | Token bearer da API (valor atual: `d8d99b5ac4c49812eb00e717a5972ddd`) |
| `videos/api_jobs/{job_id}.mp4` | Vídeos gerados pela API |

⚠️ **NÃO use** o `api_server.py` antigo — ele chama `flow_bot.generate` (caminho bugado
que sai 16:9). O certo é `veo_api.py`.

---

## 3. ESTADO ATUAL (2026-07-03, tudo NO AR)

- **API** rodando em `127.0.0.1:8799` (2 instâncias background — veja §7, item "2 instâncias").
- **Túnel Cloudflare** ativo: `https://sparc-manufacturers-gig-folder.trycloudflare.com`
  ⚠️ **Esta URL MUDA toda vez que o cloudflared reinicia.** Se cair, regenerar (§6).
- **Chrome CDP** logado no Flow na porta **9224** (conta `seebotsia`, tem crédito).
- **Workflow n8n** `uT7AXT2O7RLM54oB` ("Veo Flow - gerar video (API local)"), **ATIVO**.

Sanity check rápido:
```bash
curl -s http://127.0.0.1:8799/health
curl -s https://sparc-manufacturers-gig-folder.trycloudflare.com/health
curl -s http://127.0.0.1:9224/json/version   # Chrome CDP vivo?
```

---

## 4. COMO USAR A API (direto, sem n8n)

Criar job (retorna imediato):
```bash
curl -s -X POST http://127.0.0.1:8799/v1/jobs \
  -H "Authorization: Bearer d8d99b5ac4c49812eb00e717a5972ddd" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A red fox in snow, ambient wind sound.","aspect":"9:16"}'
# -> {"job_id":"...","status_url":"..."}
```
Consultar status (polling):
```bash
curl -s -H "Authorization: Bearer d8d99b5ac4c49812eb00e717a5972ddd" \
  http://127.0.0.1:8799/v1/jobs/<job_id>
# status: queued -> running -> done (ou error). Quando done, vem "video_url".
```
Baixar o vídeo:
```bash
curl -s -H "Authorization: Bearer d8d99b5ac4c49812eb00e717a5972ddd" \
  -o saida.mp4 http://127.0.0.1:8799/v1/jobs/<job_id>/video
```
**Sempre validar:** `ffprobe` deve dar `h264 / 720 / 1280 / 8.0` + `aac / 2 / 8.0`.
Se sair `mjpeg 512x512` sem áudio = caiu no Nano Banana (imagem) → refazer.

### Params do POST
- `prompt` (obrigatório) — em inglês, com a **fala PT-BR entre aspas** (o Veo respeita
  melhor). Ver `PROMPTS_NICHOS_PT.md`.
- `aspect` (default `9:16`), `model` (default `Veo 3.1 - Fast`), `duration` (default `8S`),
  `image` (opcional, caminho local pra image-to-video).

---

## 5. COMO USAR VIA N8N

Workflow **ATIVO**, disparado por webhook:
```bash
curl -s -X POST https://n8n6.inovareinteligenciaartificial.com/webhook/veo-flow-gerar \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A dolphin jumping at sunset, ocean sound.","aspect":"9:16"}'
# -> responde na hora com {job_id,...}; o vídeo é baixado no fim do workflow (nó "Baixar video")
```
Estrutura do workflow: `Webhook → Params → Criar job → Wait 30s → Ver status →
IF "Pronto?"(done) → [sim] Baixar video / [não] IF "Falhou?"(error) → [sim] Erro / [não] volta Wait`.

- O **Manual Trigger NÃO dispara via Public API** — por isso é webhook.
- O nó "Params" tem um prompt **default** embutido; se o body do webhook mandar `prompt`,
  ele usa o do body.
- Editar/recriar o workflow: `WF_ID=uT7AXT2O7RLM54oB python _criar_workflow_n8n.py`
  (sem `WF_ID` cria um novo). O script **re-ativa** o workflow ao fim.
- Token do n8n Public API: `D:\hipercool-videos\secrets\n8n_inovare.json` (NUNCA commitar/expor).

---

## 6. SUBIR TUDO DO ZERO (se cair / reiniciar máquina)

**Pré-requisito:** Chrome logado no Flow na porta CDP 9224. Se não estiver, ver
`COMO_LOGAR_LEIA_PRIMEIRO.md` (abrir Chrome com `--remote-debugging-port` e logar na
conta `seebotsia`). O projeto Flow é `16ecdb5d-2fc1-49f1-a87b-a82d038d76d8`.

**Passo 1 — Túnel** (background):
```bash
cd D:/hipercool-inferior-fix/roteador-veo-api-fake
./bin_tunnel/cloudflared.exe tunnel --url http://127.0.0.1:8799 --no-autoupdate
# copiar a URL https://XXXX.trycloudflare.com que ele imprime
```

**Passo 2 — API** (background), usando a URL do túnel em VEO_PUBLIC_URL:
```bash
cd D:/hipercool-inferior-fix/roteador-veo-api-fake
FLOW_PORT=9224 \
FLOW_PROJ="https://labs.google/fx/pt/tools/flow/project/16ecdb5d-2fc1-49f1-a87b-a82d038d76d8" \
VEO_PUBLIC_URL="https://XXXX.trycloudflare.com" \
VEO_API_TOKEN="<SEGREDO_REMOVIDO>" \
PYTHONUTF8=1 D:/hipercool-videos/venv/Scripts/python.exe -u veo_api.py
```

**Passo 3 — Reaponta o workflow n8n pra nova URL do túnel:**
Editar `TUNNEL` no topo de `_criar_workflow_n8n.py` e rodar
`WF_ID=uT7AXT2O7RLM54oB python _criar_workflow_n8n.py`.

> ⚠️ Toda vez que o túnel reinicia a URL muda → **repetir passos 2 e 3** com a URL nova.
> Melhoria pendente: named tunnel (URL fixa) — ver §8.

---

## 7. BUGS JÁ RESOLVIDOS (não reabrir sem ler)

1. **Saía 16:9** em vez de 9:16. Causa: 2 grupos de botão de aspecto (imagem Nano ~y=351,
   vídeo Veo ~y=534) com mesmo rótulo; o clique por texto pegava o errado. Fix: clicar por
   coordenada em TODOS os botões com ícone `crop_9_16` (clicar nos 2 grupos é inofensivo).
   Log esperado: `[veo] aspecto 9:16: 2 botao(oes) clicado(s)`.

2. **Download falhava** (timeout sem vídeo). Causa: render chegava perto/depois do deadline.
   Fix: `poster_ids_ordenados()` (ordem do DOM) + varredura final no deadline.

3. **Jobs em sequência travavam** no `.type()` da caixa de prompt. Causa raiz: ao fim de um
   render, o Flow deixa aberto o modal *"Gerar vídeo, que custa N créditos?"* com botões
   renderizados **FORA da tela (y≈-3200)**. Esse modal **NÃO fecha por clique** (testei mouse
   real, `.click()` nativo do DOM, `dispatchEvent`, locator `force=True` — TODOS falham) e
   bloqueia o `.type()` do próximo job. **Único jeito de dispensá-lo: recarregar a página.**
   Fix: `gerar()` sempre renavega ao projeto no início + loop de **retry (3x)** que recarrega
   se preparar/digitar falhar. Detecta o modal por `"custa"+"crédito"` no texto.

⚠️ **Fragilidade conhecida:** reloads repetidos podem **crashar o app React do Flow**
("Application error: a client-side exception"; página fica com ~130 chars, sem caixa). O
retry se recupera (recarrega e digita na 2ª tentativa), mas rodar jobs muito colados
estressa o Flow. Se travar de vez, recarregar manualmente o Chrome resolve.

**2 instâncias da API:** hoje há 2 processos `veo_api.py` no ar (reinício durante o dev).
Idealmente deixar **só 1** — mate o duplicado (`TaskStop` ou pelo PID) pra não confundir.
Jobs vivem em memória de cada processo, então status some se você matar a instância errada.

---

## 8. PENDÊNCIAS / PRÓXIMOS PASSOS

- [ ] **URL fixa do túnel:** trocar Quick Tunnel por *named tunnel* do cloudflared (exige
      conta Cloudflare + domínio) ou rodar como serviço. Hoje a URL muda a cada restart.
- [ ] **Persistir jobs:** hoje ficam em memória (somem se reiniciar `veo_api.py`). Se
      precisar durabilidade, salvar em disco/sqlite.
- [ ] **Deixar 1 instância só** da API e, se quiser, virar serviço/tarefa do Windows.
- [ ] **Idioma da fala:** o ffprobe confirma que TEM áudio, não que a fala saiu em PT-BR.
      Conferência de idioma é de ouvido (a dona valida).
- [ ] **Robustez do `garantir_modo_veo`:** esperar a caixa (`contenteditable`) existir antes
      de configurar, pra reduzir tentativas desperdiçadas quando o Flow está lento/crashado.
- [ ] **Prompt default do workflow:** decidir com a dona se fixa um prompt "viral BR" no nó
      Params ou se sempre manda pelo body do webhook.
- [ ] **Integração com pipeline de shorts:** plugar os mp4 gerados no fluxo de postagem
      (ver `POSTAGEM_YOUTUBE_PLAYBOOK.md`).

---

## 9. REGRAS DE OURO (não errar)

- Trabalhar SÓ em `D:\hipercool-inferior-fix\...` (não nas outras cópias).
- `PYTHONUTF8=1` sempre; Python = `D:/hipercool-videos/venv/Scripts/python.exe`.
- **NUNCA dar "pronto" sem ffprobe** (duração + áudio + 720x1280).
- Créditos do Flow são finitos: não disparar renders à toa; 1 job por vez (a API serializa).
- Segredos (`.api_token`, `secrets/n8n_inovare.json`) NUNCA no chat/commit.
- Memória relacionada: `project_veo_api_n8n` (índice em `MEMORY.md`).
