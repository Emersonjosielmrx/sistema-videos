# MEGA ENGAGE v3 — Documentação dos Módulos

## O que é isso?
Bot de cross-engagement que curte, comenta e se inscreve em vídeos do YouTube
usando múltiplas contas Google em paralelo via Chrome headless.

## Arquitetura (fluxo de execução)

```
mega_engage.py  (entry point, só importa e roda)
    └── main.py  (loop infinito)
            ├── flags.py      (verifica stop/restart)
            └── scheduler.py  (monta fila, distribui)
                    └── worker.py  (1 conta, N vídeos)
                            ├── browser.py      (abre/fecha Chrome)
                            └── engagement.py   (like/comment/subscribe)
```

## Módulos (ordem de leitura recomendada)

| # | Arquivo | Faz o quê |
|---|---------|-----------|
| 1 | `config.py` | Caminhos de arquivos, constantes, ler/salvar config |
| 2 | `comments.py` | Banco de frases por idioma (pt/en/es/fr/it/th/vi/hi/ru/id) |
| 3 | `progress.py` | Ler/salvar o JSON de progresso |
| 4 | `logger.py` | log(msg) — timestamp + arquivo + console |
| 5 | `flags.py` | Controle por arquivo (stop/restart) |
| 6 | `browser.py` | Lançar Chrome headless com perfil/proxy/fingerprint |
| 7 | `engagement.py` | Ações em 1 vídeo: watch, like, comment, subscribe |
| 8 | `worker.py` | Worker: abre 1 sessão e engaja lista de vídeos |
| 9 | `scheduler.py` | Monta fila, respeita limites, ThreadPoolExecutor |
| 10 | `main.py` | Loop principal (roda até completar ou stop) |

## Como rodar

```bash
cd D:/projetos-navegador
D:/hipercool-videos/venv/Scripts/python.exe mega_engage.py
```

Ou simplesmente clique duplo em `RODAR_ENGAGE.bat`.

## Como parar

- Criar arquivo `engage_stop.flag` na pasta
- POST http://localhost:8850/stop
- Ctrl+C no console

## Como pausar/despausar

- POST http://localhost:8850/pause (toggle)
- Ou editar `engage_config.json`: `"paused": true/false`

## Configuração (engage_config.json)

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| workers | int | 5 | Threads simultâneas (máx 19) |
| sleep_min | float | 2 | Delay mínimo entre ações (s) |
| sleep_max | float | 8 | Delay máximo entre ações (s) |
| batch | int | 500 | Vídeos por lote |
| priority | string | "" | Canal que recebe 70% do batch |
| mode | string | "both" | "likes", "comments", ou "both" |
| active_hours | [int,int] | [0,23] | Horário de operação |
| max_per_account_day | int | 200 | Limite diário por conta |
| paused | bool | false | Se true, bot não faz nada |
| watch_time | [int,int] | [10,30] | Tempo de assistência simulado |
| subscribe | bool | true | Se deve se inscrever |
| fingerprint | bool | true | Se deve variar UA/viewport |

## Pra IAs que forem mexer aqui

1. **Comece por config.py** — entenda os paths
2. **O fluxo principal é**: main → scheduler → worker → engagement
3. **Cada função tem docstring** explicando args, returns, e comportamento
4. **O log NUNCA trava** — tem try/except pro PermissionError do Windows
5. **progress.json é thread-safe** — acesso via progress_lock
6. **Chrome é headless** — não abre janela, só consume RAM/CPU
7. **CHUNK_SIZE=5** — se aumentar, Chrome pode dar OOM
8. **Cooldown exponencial** — erros consecutivos fazem o bot esperar mais

## Problemas comuns

| Sintoma | Causa | Solução |
|---------|-------|---------|
| PermissionError no log | Outro processo segura o arquivo | Matar processos fantasma, deletar log |
| 0 ações | `paused: true` no config | Setar pra false |
| Chrome OOM | CHUNK_SIZE muito alto | Manter em 5 |
| Muitos COOLDOWN | Proxy caiu ou conta bloqueada | Verificar local_proxy.py |
| "Fora do horário ativo" | active_hours não inclui hora atual | Ajustar no config |
