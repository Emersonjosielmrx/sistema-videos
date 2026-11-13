# Docker — build e push (fazer numa VPS, NÃO neste PC)

Docker não roda nesta máquina de propósito: ele comeria a RAM/CPU que
precisamos livre pros outros projetos. O `Dockerfile` fica pronto no repo pra
ser buildado numa VPS quando quisermos rodar as pistas na nuvem.

## Pré-requisito: requirements.txt

A imagem instala as libs via `requirements.txt`. Pra gerar a partir do venv atual:

```bash
D:\historias-em-frames\venv\Scripts\python.exe -m pip freeze > requirements.txt
```

Revise e remova o que for específico de Windows (ex.: `pywin32`) antes de buildar
em Linux.

## Build + push (na VPS)

```bash
# login no Docker Hub (usuario: fabricadeautomacoesia)
docker login -u fabricadeautomacoesia

# build
docker build -t fabricadeautomacoesia/historias-em-frames:prod .

# push
docker push fabricadeautomacoesia/historias-em-frames:prod
```

Tags sugeridas: `:prod`, `:beta`, `:teste` (uma por pista) e versões `:v1.0.0`.

## Rodar (na VPS), montando volumes pra saída e segredos

```bash
docker run -d --name hef-prod \
  -e HEF_VIDEOS_DIR=/materiais/historias-em-frames/videos/prod \
  -v /caminho/materiais:/materiais \
  -v /caminho/secrets:/app/secrets:ro \
  fabricadeautomacoesia/historias-em-frames:prod
```

- **secrets** entram por volume `:ro` — nunca ficam na imagem.
- **saída** vai pro volume `materiais` — os vídeos e `postar.json` saem lá.

## Segurança

Os tokens (GitHub PAT / Docker PAT) que passaram pelo chat devem ser
**rotacionados** (gerar novos, revogar os antigos). Nunca comitar token no repo.
