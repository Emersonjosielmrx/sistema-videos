# 3 Ambientes do Recap de Anime — REGRA PERMANENTE

> Definido pela dona em 2026-07-26. **Não afrouxar sem ordem explícita dela.**
> A produção NUNCA pode ser comprometida.

## Os 3 ambientes

As três ficam dentro de UMA pasta-mãe: **`D:\recapd-ambientes\`**.

| # | Nome | Branch git | Subpasta | Papel |
|---|------|-----------|----------|-------|
| 1 | **PROD** (produção/latest) | `master` / `prod-latest` | `D:\recapd-ambientes\producao` | O que gera vídeo de verdade. **NUNCA é desligado de vez.** É o worker padrão. |
| 2 | **BETA** (produção experimental) | `beta` | `D:\recapd-ambientes\beta` | Em produção, mas testando melhorias. Roda quando sobra recurso. |
| 3 | **TESTE** (bancada) | `teste` | `D:\recapd-ambientes\experimental` | Onde uma melhoria é validada antes de subir pro BETA/PROD. |

Cada ambiente é uma **git worktree** própria (código isolado por versão).
`venv` e `workspace` são **junctions compartilhados** com o PROD — custo zero de
disco e o cache de TTS/visão é reaproveitado pelos 3 (não retrabalha).

**Independência:** o pipeline não depende de nenhuma outra pasta `hipercool-*`
(inferior-fix / motionframes / producao / videos). Usa só o próprio venv e o hub
compartilhado `D:\hipercool-materiais` (assets/SFX/trilhas/vídeos, compartilhado
por todos os projetos). O worker do anime é o `anime_night_shift.py`.

## Regra de recurso (RAM + CPU) — reavaliada a cada ciclo

Só **1 worker ativo por vez** (a máquina não aguarda 2 renders pesados).
Prioridade: **PROD (1) > BETA (2) > TESTE (3)**.

| Recurso | Ação |
|---------|------|
| **OK** (RAM ≥ 3GB livre e CPU ≤ 70%) | PROD roda. BETA/TESTE podem pegar um turno. |
| **BAIXO** | Mata **TESTE** primeiro. Segura BETA (não inicia novo). Mantém PROD. |
| **CRÍTICO** (RAM < 1.2GB **ou** CPU > 92%) | Mata **TESTE e BETA**. Se há teste pendente de validação, PROD cede **1 turno** pro TESTE e **volta a rodar assim que o teste acaba**. Senão, PROD manda. |

Nada é morto calado: cada encerramento vira um `AVISO` no log
(`logs/ambientes_supervisor.log`).

Limiares configuráveis por env: `AMB_RAM_OK_MB`, `AMB_RAM_CRIT_MB`,
`AMB_CPU_OK_PCT`, `AMB_CPU_CRIT_PCT`.

## Como operar

```bash
# ver estado e decisão (não age)
venv/Scripts/python.exe bin/ambientes_supervisor.py --status

# supervisionar continuamente (loop) — é o que o atalho/cron liga
venv/Scripts/python.exe bin/ambientes_supervisor.py --loop --intervalo 30

# marcar que há melhoria aguardando validação no TESTE (libera a exceção da regra)
venv/Scripts/python.exe bin/ambientes_supervisor.py --marcar-teste-pendente
# baixar a flag quando a melhoria foi validada
venv/Scripts/python.exe bin/ambientes_supervisor.py --limpar-teste-pendente
```

Atalhos no desktop: **Supervisor Ambientes (LIGAR)** / **(DESLIGAR)**.

## Fluxo de promoção de uma melhoria

1. Codar/testar no **TESTE** (`D:\recapd-ambientes\experimental`, branch `teste`).
2. `--marcar-teste-pendente` pra o supervisor permitir o TESTE validar mesmo sob pressão.
3. Validado → merge `teste` → `beta`, roda em BETA por um período.
4. Estável em BETA → merge `beta` → `master`/`prod-latest`, bump do `VERSION`,
   push GitHub + Docker Hub.
5. `--limpar-teste-pendente`.

## Estado atual

- `VERSION`: ver arquivo `VERSION` na raiz.
- Estado em runtime: `workspace/ambientes_estado.json` (quem roda, teste pendente).
