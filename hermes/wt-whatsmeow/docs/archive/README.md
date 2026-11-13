# Arquivo (histórico)

Anotações de sessão e hand-offs antigos, mantidos por contexto histórico.
**Não são documentação de produto** e podem estar desatualizados.

Para o estado atual, veja:
- [`../../README.md`](../../README.md) — visão geral
- [`../../CHANGELOG.md`](../../CHANGELOG.md) — mudanças por versão
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — arquitetura
- [`../../deploy/DEPLOY.md`](../../deploy/DEPLOY.md) — build e deploy
- [`../../VERSIONING.md`](../../VERSIONING.md) — versionamento

## O que veio para cá em 04/10/2026 (roteiros de julho)

O roteiro em vigor é `docs/PLANO_MES_OUTUBRO_2026.md`. Estes descreviam planos de julho, já feitos ou
abandonados, e confundiam agentes novos:
- `ROADMAP_MELHORIAS_2026-07.md` (estava na raiz), `ROADMAP_HERMES_CALL_2026-07.md`, `PROXIMA_RODADA_2026-07.md`;
- `BOTOES_MORTOS_E_DADOS_FAKE_2026-07.md`: o painel foi limpo na v0.6.0 (telas falsas viraram "em breve");
- `project_rules_hipercool_2026-07.md` (estava na raiz): regras de outro agente do frontend, de outro projeto;
- `CLAUDE_md_avisos_julho_2026.md`: os avisos de julho do `CLAUDE.md` (produção em Docker, `_GOLDEN_v0.2.1`).

## O que veio para cá em 02/10/2026 (limpeza da raiz)

- Relatórios/planos da raiz (`_*.md`, `RELATORIO_*.md`, `FIX-FRONT-1.md`,
  `HANDOFF_WIZARD_E_LIGACAO_20260720.md`, `QA_STATE.json`). Valores de senhas/tokens que
  havia neles foram trocados por `<removido — ver cofre/VPS>` (o histórico do git não foi
  reescrito).
- `scripts-antigos/`: scripts soltos que estavam na raiz e não são usados pelo build nem
  pela publicação (`download_*.js`, `deploy-beta.js` antigo, `inovare.html`, `build.ps1`,
  `start-all.*`, `test_plans_e2e.sh`, `openapi_xpop.yaml`).
- `logos/`: estudos de logo (`hermes_logo_*.png`) sem referência no código.
- Removidos por serem cópia idêntica ou recuperáveis pelo git: `_DOCS_PRESERVADOS/`
  (cópias iguais às da raiz), `_VERSAO_BOA_SOURCE/versao-boa-29586fa.bundle` (o commit
  29586fa está no repositório e nas tags PRODUCAO-*) e o pacote morto `internal/sessions`.
