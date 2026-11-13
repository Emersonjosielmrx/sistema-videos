# cline-ponte (29/10/2026)

Modelo **"Cline Opus 5.5"** (`cline-opus-5-5`) no seletor do Claude Code (VS Code) usando a **chave Anthropic ou a conta Cline** deste PC.

## Dois modos (escolhido automaticamente)

A ponte lê `actModeApiProvider` do Cline (`~/.cline/data/globalState.json`) a cada requisição:

- **`anthropic`** (padrão): repasse direto para `api.anthropic.com` com a chave `sk-ant` da dona (de `~/.cline/data/settings/providers.json`). Sem tradução de formato, sem gastar crédito Cline. A ponte só troca o nome do modelo (`cline-opus-5-5` → `claude-opus-5-5`) e a chave de autenticação.
- **`cline`**: usa os créditos Cline (OAuth, `api.cline.bot`), traduzindo Anthropic ↔ OpenAI (streaming, ferramentas, raciocínio com assinatura, imagens, cache de prompt).

## Caminho

Claude Code → proxy 20133 (VPS 157) → túnel `ssh -R` (127.0.0.1:20160 na VPS) → `ponte.mjs` (127.0.0.1:20160 no PC) → `api.anthropic.com` ou `api.cline.bot`.

## Detalhes

- Tarefa **ClinePonte**: liga no logon e confere a cada 5 min, sem janela (`rodar_oculto.vbs` → `iniciar.bat`). O mesmo processo mantém o túnel e o refaz se cair.
- VPS: o patch do proxy está em `vps/patch_proxy.py` (backup `proxy.mjs.bak-cline-*`). A porta 20160 fica fechada pra fora pelo `fechar-20160.service`, porque o `GatewayPorts yes` abriria em 0.0.0.0.
- Outros nomes também funcionam: `cline-opus-4-8`, `cline-sonnet-5-5`, `cline-fable-5-1`.
- Saúde: `curl http://127.0.0.1:20160/saude` — mostra qual provedor está ativo.
- Log: `ponte.log`.
- Se o PC ou o túnel estiver fora do ar, só esse modelo falha (erro 529). Os outros modelos não dependem dele.
- O Cline deslogou → abrir o Cline e entrar de novo na conta Cline (só importa no modo `cline`).
- Teste: `python -I teste.py [url]`.
