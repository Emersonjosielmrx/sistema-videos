# Avisos de julho/2026 que estavam no topo do CLAUDE.md

> **HISTÓRICO.** Tirados do `CLAUDE.md` em 04/10/2026. Desde agosto a produção roda via systemd e é
> publicada por `ops/publicar.sh`; nada abaixo vale para a produção atual. Mantido só pra entender o passado.

> **NOTA 2026-07-25:** Diretório renomeado de `D:\hipercool-refactor` para
> `D:\hermes-call` para evitar confusão com o projeto de vídeos
> (`D:\hipercool-videos`, que é coisa separada).

> ## ⚠️ 2026-07-26 — FONTE-VERDADE E REGRA ANTI-CONTAMINAÇÃO (LEIA)
>
> **A versão CORRETA de produção é a imagem Docker imutável
> `fabricadeautomacoesia/hermes-call:v0.2.1`** (= `:stable` = `:latest`,
> digest `sha256:e9076d20...`, build `20260723-2224`, bundle `index-BYgTiieN.js`).
> É o que roda em `hermescall.opus-sem-limites.com.br` e em
> `hermescall.inovareinteligenciaartificial.com`. Cópia extraída em
> `_GOLDEN_v0.2.1/` (binário + dist + MANIFEST). **NÃO é rastreada pelo git.**
>
> **O que aconteceu:** um agente buildou a v0.2.1 de um working-tree NÃO
> commitado e o fonte exato se perdeu (não está no git, nem em backup, nem na
> imagem — que só tem binário+bundle). Depois, telas antigas foram salvas por
> cima de novas: o fonte local tem arquivos novos (`ChatPage`, telas de billing)
> misturados com um `App.tsx`/roteador ANTIGO que não os importa. Por isso um
> build do fonte local sai mais pobre que a v0.2.1 (faltam chat, tags, blocks,
> follow-up, sub-abas funil/garimpo do CRM).
>
> **REGRAS PERMANENTES:**
> 1. **NUNCA buildar/deployar de working-tree sujo.** `deploy/deploy.js` agora
>    bloqueia git sujo (fure só com `--allow-dirty`, último caso). Commite antes.
> 2. **NÃO rebuildar a imagem do fonte da VPS** (`/opt/hipercool-refactor`).
>    `deploy/rebuild.js` está travado atrás de `--sim-eu-quero-rebuildar-da-vps`.
>    Para restaurar produção, dê `docker run` da imagem `:v0.2.1`, não rebuilde.
> 3. **Cada build registra** git-hash + md5 do bundle em `deploy/BUILD_LEDGER.tsv`.
> 4. **Reconstrução do fonte limpo** (religar o `App.tsx`/menu às telas boas,
>    conferindo contra `_GOLDEN_v0.2.1/`) é tarefa pendente — só com aprovação
>    da dona. Ver memória `project_hermes_versao_limpa_v021`.
