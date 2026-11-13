# Uma VPS por empresa, cada uma com o Kaggle da empresa (dona 25/10/2026)

Regra: o PC prepara, mas não fala com o Kaggle. Tudo que vai pro Kaggle passa pela VPS da empresa, que usa a conta
Kaggle DAQUELA empresa (nunca a de outra). Projetos antigos que já mandam direto (ex.: voz clonada dos Shorts) ficam
pra 2ª versão.

| Empresa | VPS | Kaggle | Estado |
|---|---|---|---|
| Inovare (Hermes Call) — 1º teste: recap longo | hermes-prod | emersonjosiel649 | no ar 25/10 |
| MS Energy | (a definir) | (conta da MS Energy) | falta |
| outras | uma VPS cada | conta própria | falta |

## Ligar uma empresa nova
1. Na VPS: `mkdir /opt/recap_central` (nome pode ser /opt/<empresa>_central), copiar `vps_central.py` e o
   trabalhador do Kaggle do projeto; `python3 -m venv venv && venv/bin/pip install kaggle`.
2. `config.json` (chmod 600):
   ```json
   {"empresa": "MS Energy", "base": "<remoto rclone da empresa>:pasta", "fila": "...", "fila_src": "...",
    "kaggle": {"username": "...", "key": "...", "kernel": "<usuario>/<kernel>", "dataset": "<usuario>/<conf>",
               "trabalhador": "kaggle_trabalhador.py"},
    "telegram": {"bot_token": "...", "chat_id": "..."}, "pagina": "<empresa>-<código>"}
   ```
   + `rclone.conf` só com os remotos da empresa (chmod 600).
3. Cron: `*/5 * * * * root cd /opt/<pasta> && flock -n .trava venv/bin/python vps_central.py >> central.log 2>&1`.
4. No PC, o projeto envia com `scp` pra `<vps>:/opt/<pasta>/entrada/<pid>/` + `enviado.ok` (modelo:
   `colab\cliente.py enviar`).
