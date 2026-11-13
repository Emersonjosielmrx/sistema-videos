# Fluxo de promoção das 3 pistas

As melhorias sobem de pista uma de cada vez, do mais arriscado pro mais estável.
A produção (prod) só recebe o que já foi validado.

```
  TESTE  ---(passou)--->  BETA  ---(validou em producao)--->  PROD (latest)
 (quebra a vontade)     (producao em experiencia)          (nunca para)
```

## As 3 pistas

| Pista | Pasta | Branch git | Papel |
|---|---|---|---|
| prod  | `D:\historias-em-frames` | `main`  | A que nunca para. Só o que funciona 100%. |
| beta  | `D:\historias-beta`      | `beta`  | Em produção, mas em fase de experiência. |
| teste | `D:\historias-teste`     | `teste` | Onde se experimenta. Pode quebrar. |

## Regra de ouro (recurso)

Quando falta RAM/CPU, o guardião desliga primeiro a **teste**, depois a **beta**.
A **prod nunca é desligada pelo guardião** — só pelo botão manual DESLIGAR_PROD.
Quando o recurso volta, o guardião religa beta/teste (respeitando o que você
deixou habilitado nos botões).

## Como promover teste → beta

Depois que uma melhoria provou que funciona na teste:

```bash
# 1. commit na teste
cd /d/historias-teste && git add -A && git commit -m "melhoria X validada"

# 2. leva pra beta (merge do branch teste no beta)
cd /d/historias-beta && git fetch && git merge origin/teste

# 3. tag de versao e push
git tag v1.1.0-beta && git push origin beta --tags
```

## Como promover beta → prod

Depois que a beta rodou em produção sem problemas:

```bash
cd /d/historias-em-frames && git fetch && git merge origin/beta
git tag v1.1.0-prod && git push origin main --tags
```

## Versionamento

- Cada promoção ganha uma **tag** (`v1.1.0-beta`, `v1.1.0-prod`).
- O estado antes desta reestruturação está na tag `backup-pre-3pistas-20260726`.
- Tudo no GitHub (repo privado `fabricadeautomacoesia/historias-em-frames`).
- Docker: ver `README_DOCKER.md` (buildar na VPS, não neste PC).
