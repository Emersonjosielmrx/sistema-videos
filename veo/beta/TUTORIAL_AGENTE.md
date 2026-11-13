# Tutorial pro agente — receitas de problema comum

Passo a passo pra quem precisa consertar sem conhecer o código todo.
Tudo aqui é seguro (não gasta crédito à toa). Sempre use:

```
PYTHONUTF8=1 D:/veo/venv/Scripts/python.exe <comando>
```
e rode de dentro de `D:\veo\beta` (a pasta antiga `roteador-veo-api-fake` não existe mais; 16/10). Antes de mexer,
leia `D:\veo\docs\CONTINUAR_DAQUI.md`; depois de mexer, rode `python validate.py`.

---

## (a) "Não está gerando vídeo, e agora?"

Cheque nesta ordem:

**1. As contas estão vivas?**
```
python cron_gerar_video_llm.py sessoes
```
- Se **todas** aparecem como `EXHAUSTED` → todas sem crédito. Isso é normal;
  o crédito do Flow reseta à meia-noite. Só esperar. (Se você tem certeza que
  tem crédito, veja a receita (c) mais abaixo pra limpar o estado.)
- Se aparecem como `ATIVA`/`ok` mas mesmo assim nada sai → siga pro passo 2.

**2. O smoke test passa?**
```
python validate.py
```
- Se der **FALHOU** com erro de import → alguém quebrou um arquivo `.py`.
  O erro mostra qual módulo e qual linha. Conserte ou reverta essa mudança.
- Se der **TUDO OK** → o código está são; o problema é login ou crédito
  (passos 3 e 4).

**3. O Chrome está logado na conta certa?**
Esse foi o bug clássico (a conta `emersonjosiel649` "fantasma"): o **perfil do
Chrome** estava logado no Google errado, mesmo com a config certa.
- Abra o `.bat` de re-login da conta (ex.: `relogin_seebotsia.bat`), faça login
  no Google **na conta correta** e feche o Chrome quando o Flow carregar.
- Confirme no menu de conta do Flow (avatar canto superior direito) que é a
  conta esperada.

**4. Acabou o crédito de verdade?** Veja a receita (b).

---

## (b) "Como ver se uma conta esgotou o crédito"

- Estado que o bot registrou:
  ```
  python cron_gerar_video_llm.py sessoes
  ```
  Conta sem crédito aparece como `EXHAUSTED` com `creditos_renova_em`
  (quando volta — próxima meia-noite).

- Evidência do que o Flow mostrou na hora (print + texto):
  veja os arquivos mais recentes em `logs/creditos_esgotados_*.png` / `.txt`.

- Como o bot detecta (pra ajustar): tudo em **`creditos.py`**.
  - Se o Flow mudou a frase de aviso e o bot não pega mais → edite a lista
    `PATTERNS` em `creditos.py` (adicione a nova frase, minúscula).
  - A checagem de **saldo zero** (quando o Flow não mostra aviso nenhum e só
    trava) é a função `ler_saldo_creditos()` — ela lê o número no menu de conta.

---

## (c) "Limpar o estado travado (EXHAUSTED / cooldown)"

Use quando você tem certeza que a conta voltou a ter crédito mas o bot ainda
está pulando ela (ex.: reset aconteceu mas o horário do PC estava errado).

```
python cron_gerar_video_llm.py clear_exhausted
```
Isso zera `status`, `cooldown_until`, `creditos_renova_em` e `padrao_creditos`
de **todas** as contas. No próximo ciclo o bot tenta todas de novo.

> Se após limpar ela voltar pra `EXHAUSTED` no mesmo minuto, é porque o crédito
> realmente acabou — não insista, espere o reset.

---

## (d) "Mexer nas contas"

Só em **`contas.py`**. Adicionar conta nova → veja **TUTORIAL_NOVA_CONTA.md**.
Depois de qualquer mudança:
```
python validate.py
```

---

## Coisas que você NÃO deve fazer

- Não recriar a lista de contas dentro de `cron_gerar_video_llm.py` ou
  `gera_auto.py`. Ela vem de `contas.py` de propósito (evita o bug antigo de
  listas divergentes).
- Não mudar o exit code 2 nem o texto `CREDITOS_ESGOTADOS padrao='...'` no
  `gera_auto.py` / `creditos.py` — é o contrato que o orquestrador entende.
- Não rodar 2 loops ao mesmo tempo (competem pelas mesmas contas/portas).

---

## (e) "Pos-produção: ligar, desligar, processar backlog"

Sistema **modular** que aplica nos vídeos gerados:
loudnorm → crop 9:16 → propaganda inteligente → branding.

Os 4 atalhos novos no Desktop:
- **Veo - POS (LIGAR tudo)** / **(DESLIGAR tudo)** — liga/desliga todos os subsistemas de uma vez.
- **Veo - POS Flag** — toggle de **um flag específico** (interface de texto). Útil pra desligar só propaganda sem parar a geração.
- **Veo - POS Rodar (incremental)** — processa **só os vídeos novos** que ainda não passaram pelo pipeline.
- **Veo - POS Rodar (retroativo 5)** — processa o **backlog antigo** (recursivo, espelha subpastas).

### Os 4 subsistemas (flags)

| Flag | Estado padrão | O que faz |
|------|---------------|-----------|
| `cron_video`      | ON  | Gera novos vídeos Veo (o cron principal) |
| `pos_video`       | ON  | Roda pos-produção (incremental, depois de gerar) |
| `cron_pos_retro`  | OFF | Processa backlog retroativo (gasta CPU extra) |
| `voz_whatsapp`    | OFF | Injeta voz PT-BR no áudio (plugin opcional) |

Cada flag vive em `pos_producao/flags/<nome>.flag` (conteúdo `on` ou `off`).
Se o arquivo não existir, usa o **estado padrão**.

### Casos práticos

**1. Pausar geração mas continuar pos-produção** (acelerar backlog):
```
Veo - POS FLAG → cron_video off
```
Cron principal pula (`[flag] cron_video OFF`), mas `cron_pos_producao.py`
se rodado continua processando.

**2. Pausar pos-produção mas continuar gerando:**
```
Veo - POS FLAG → pos_video off
```
Geração segue, mas cada vídeo novo não passa pelo pipeline.
Útil quando a máquina tá pesada.

**3. Processar backlog depois de gerar muitos vídeos:**
```
Veo - POS (LIGAR tudo)         # garante que tudo tá ON
Veo - POS Rodar (retroativo 5) # roda 5 por passada
```
Repete o `Rodar` até enjoar. Espelha `cron_shorts/`, `nichos/` em
`videos_pos/`. Não apaga o original.

**4. Estado atual (linha de comando):**
```
D:/veo/venv/Scripts/python.exe pos_producao/flags.py list
```

### Arquivos importantes

- `pos_producao/` — pasta nova (não destruir!)
  - `config.yaml` — pipeline ativo, ordem dos plugins, ffmpeg path
  - `runner.py` — orquestrador (run_pipeline / run_one)
  - `flags.py` — leitura/escrita dos flags
  - `plugins/` — 4 plugins (loudnorm, crop, propaganda, branding)
- `cron_pos_producao.py` — cron paralelo (incremental ou retro)
- `Veo_POS_TUDO.bat`, `Veo_POS_FLAG.bat`, `Veo_POS_RODAR.bat` — toggles no Desktop

### Coisas que você NÃO deve fazer

- Não apagar `videos_pos/` com vídeo gerado — o pipeline é não-destrutivo (o
  original fica em `videos/`).
- Não rodar retroativo e incremental ao mesmo tempo (competem pela fila).
- Não editar `config.yaml` na mão sem testar com 1 vídeo dummy primeiro
  (`Veo - POS Rodar (incremental)`).
