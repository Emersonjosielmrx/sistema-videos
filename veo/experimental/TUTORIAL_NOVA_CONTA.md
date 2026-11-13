# Tutorial — adicionar uma conta Google nova

Objetivo: colocar mais uma conta no rodízio do bot. São 3 passos.
Escolha nomes/valores **inéditos** (não repetir de outra conta).

Convenção usada aqui:
- `session` = nome curto (ex.: `minhaconta`)
- `profile` = pasta do perfil Chrome, sempre `chrome_gen_<session>`
- `port`    = porta CDP livre; as usadas hoje são 9250/9260/9270 —
  use a próxima livre (ex.: `9280`).

---

## Passo 1 — logar o Chrome nesse perfil

Cada conta tem sua própria pasta de perfil Chrome (é onde o login do Google
fica salvo). Você precisa abrir o Chrome nessa pasta e logar **uma vez**.

Modelo pronto: copie um `relogin_*.bat` existente (ex.: `relogin_seebotsia.bat`)
para `relogin_<session>.bat` e troque **a porta** e **o `--user-data-dir`** pro
seu perfil novo. O conteúdo é assim:

```bat
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --no-first-run ^
  --disable-session-crashed-bubble ^
  --remote-debugging-port=9280 ^
  "--user-data-dir=D:\hipercool-inferior-fix\roteador-veo-api-fake\chrome_gen_minhaconta" ^
  "https://labs.google/fx/pt/tools/flow"
```

Rode o `.bat`, **faça login no Google na conta certa**, espere o Flow abrir com
a caixa de prompt visível, e **feche o Chrome**. O login fica salvo na pasta.

> Confirme no avatar (canto superior direito do Flow) que é mesmo a conta que
> você quer. Conta errada no perfil = o bug clássico.

---

## Passo 2 — adicionar a conta em `contas.py`

Abra **`contas.py`** e adicione **um** dict na lista `CONTAS`:

```python
CONTAS = [
    {"session": "seebotsia",      "port": "9250", "profile": "chrome_gen_seebotsia"},
    {"session": "mundosolar",     "port": "9260", "profile": "chrome_gen_mundosolar"},
    {"session": "canalalucinaai", "port": "9270", "profile": "chrome_gen_canalalucinaai"},
    {"session": "minhaconta",     "port": "9280", "profile": "chrome_gen_minhaconta"},  # NOVA
]
```

Regras:
- `port` e `profile` têm que ser **únicos** (nenhuma outra conta usa).
- `profile` = a MESMA pasta que você usou no `--user-data-dir` do passo 1.
- **Não** edite mais nenhum arquivo. `cron_gerar_video_llm.py` e `gera_auto.py`
  já leem daqui automaticamente.

---

## Passo 3 — validar

```
PYTHONUTF8=1 D:/hipercool-videos/venv/Scripts/python.exe validate.py
```

Tem que terminar em **TUDO OK** e mostrar sua conta nova na tabela. Se acusar
porta/profile duplicado, corrija no `contas.py` e rode de novo.

Confirme também que o orquestrador enxerga:
```
python cron_gerar_video_llm.py sessoes
```

Pronto. No próximo ciclo do loop a conta nova entra no rodízio.

---

## Remover uma conta

Faça o inverso: apague o dict dela da lista `CONTAS` em `contas.py` e rode
`validate.py`. (A pasta `chrome_gen_<session>` pode ficar no disco sem
problema; só não será mais usada.)
