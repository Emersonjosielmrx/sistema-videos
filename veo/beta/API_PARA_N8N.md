# 🔌 Veo API para o n8n — gerar vídeo via Flow por HTTP

> Transforma a automação do Google Flow/Veo (Chrome CDP + `gera_auto.py`) numa
> **API HTTP assíncrona** que o n8n (remoto) chama, faz polling e baixa o vídeo.
> Arquivo do servidor: **`veo_api.py`**. Não confundir com o `api_server.py` antigo
> (que usa o caminho bugado `flow_bot.generate` → sai 16:9). Usar `veo_api.py`.

---

## Por que assíncrono
O render do Veo leva de **1 a 15 min**. Segurar uma conexão HTTP tanto tempo
quebra (timeout do n8n/proxy). Então o fluxo é: cria job → consulta status →
baixa quando pronto.

---

## Subir o servidor (nesta máquina Windows)
Pré-requisito: Chrome CDP logado no Flow rodando na porta CDP (ex: 9224 = conta
`seebotsia`). Ver `COMO_LOGAR_LEIA_PRIMEIRO.md`.

```bash
cd D:/hipercool-inferior-fix/roteador-veo-api-fake
FLOW_PORT=9224 \
FLOW_PROJ="https://labs.google/fx/pt/tools/flow/project/16ecdb5d-2fc1-49f1-a87b-a82d038d76d8" \
VEO_PUBLIC_URL="http://SEU_IP_PUBLICO:8799" \
VEO_API_TOKEN="<SEGREDO_REMOVIDO>" \
PYTHONUTF8=1 D:/hipercool-videos/venv/Scripts/python.exe -u veo_api.py
```
Escuta em `0.0.0.0:8799` (todas as interfaces). Deixe rodando em background.

### Config por env
| Env | Default | Pra quê |
|---|---|---|
| `VEO_API_HOST` | `0.0.0.0` | interface de escuta |
| `VEO_API_PORT` | `8799` | porta HTTP |
| `VEO_PUBLIC_URL` | `http://127.0.0.1:8799` | **base das `video_url`** — troque pelo IP público / URL do túnel, senão o n8n remoto não acha o vídeo |
| `VEO_API_TOKEN` | (vazio) | se setado, exige `Authorization: Bearer <token>` |
| `FLOW_PORT` | `9224` | porta CDP do Chrome logado no Flow |
| `FLOW_PROJ` | (proj antigo) | URL do projeto Flow da conta |

---

## Endpoints

### POST `/v1/jobs` — cria um job
Body JSON:
```json
{
  "prompt": "A red fox walking in snow... soft ambient sound.",
  "aspect": "9:16",
  "model": "Veo 3.1 - Fast",
  "duration": "8S",
  "image": null
}
```
Só `prompt` é obrigatório. Resposta imediata (202):
```json
{ "job_id": "fd50...c63b", "status": "queued",
  "status_url": "http://SEU_IP:8799/v1/jobs/fd50...c63b" }
```

### GET `/v1/jobs/{id}` — status (polling)
```json
{ "status": "running", "logs": ["...aguardando (900s)"] }
```
`status` passa por: `queued` → `running` → `done` (ou `error`). Quando `done`:
```json
{ "status": "done",
  "video_url": "http://SEU_IP:8799/v1/jobs/fd50...c63b/video",
  "bytes": 2338406 }
```

### GET `/v1/jobs/{id}/video` — baixa o mp4
Retorna o `video/mp4`. Enquanto não pronto: 409.

### GET `/health` — sanity check (sem auth)

---

## Fluxo no n8n (remoto)
1. **HTTP Request** POST `/v1/jobs` com o prompt → guarda `job_id`.
2. **Wait** ~30s → **HTTP Request** GET `/v1/jobs/{job_id}`.
3. **IF** `status == "done"`? não → volta pro Wait (loop). sim → segue.
4. **HTTP Request** GET `video_url` (response format = File) → tem o mp4.
5. (opcional) manda pro pipeline de shorts / posta.

> Se `VEO_API_TOKEN` setado, adicionar header `Authorization: Bearer <token>` em
> todas as chamadas.

---

## Regras / limites
- **1 render por vez** (o Chrome/Flow é recurso único; a API serializa via lock).
  Jobs concorrentes ficam na fila do lock, não quebram.
- Sempre valida no fim: só marca `done` se o mp4 > 100 KB. Confirmar 9:16 é de
  ffprobe (a API não valida aspecto).
- Jobs vivem em memória (some se reiniciar o servidor). Os mp4 ficam em
  `videos/api_jobs/{job_id}.mp4`.

---

## Exposição pro n8n REMOTO (a fazer / decidir)
A máquina é Windows doméstico. Pra um n8n em VPS chamar, precisa de rota de entrada:
- **Túnel** (cloudflared / ngrok): mais simples, dá URL https pública →
  usar essa URL em `VEO_PUBLIC_URL`.
- **Port forward** no roteador + IP público/DDNS (menos seguro; usar `VEO_API_TOKEN`).
Sem isso, `127.0.0.1` só serve pra n8n na mesma máquina.
