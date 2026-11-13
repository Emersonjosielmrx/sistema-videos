# Produção automática de vídeos — guia rápido

Este projeto gera vídeos de histórias **sozinho, em loop**, sem depender do chat.
Tudo que você precisa mexer está aqui embaixo. Você **não precisa saber programar**.

## Ligar e desligar

| Ação | Como fazer |
|---|---|
| **Ligar** a produção | 2 cliques em `LIGAR_PRODUCAO.bat` (ou no atalho do desktop "LIGAR Producao Videos") |
| **Desligar** (limpar CPU/RAM) | 2 cliques em `DESLIGAR_PRODUCAO.bat` (ou atalho "DESLIGAR Producao Videos") |
| Ver o que aconteceu | abra `logs/auto-producer.md` |

Roda em segundo plano, sem janela. Fechar o chat **não** desliga. Só o botão DESLIGAR desliga.

## Mudar o que os vídeos falam (sem mexer em código)

- **`config/temas.json`** → os gêneros e os temas. Para adicionar um tema, é só
  escrever uma frase nova na lista do gênero. Para criar um gênero novo, copie um
  bloco e troque o nome. Salvou = já vale no próximo vídeo.
- **`config/settings.json`** → quantas cenas, qualidade, tempo-limite, etc.
  Cada campo tem um `_help` do lado explicando o que faz.

Não precisa reiniciar nada depois de editar os JSONs — o produtor relê a cada vídeo.

## Testar sem gastar quota

Abra o terminal na pasta do projeto e rode:

```
D:\historias-em-frames\venv\Scripts\python.exe auto_producer.py --dry-run
```

Ele mostra os próximos 5 vídeos que faria, sem gerar nada.

## Onde saem os vídeos

`workspace/videos/<genero>/<id>/v1_FINAL.mp4`

## Se algo quebrar

Existe um backup completo em `_BACKUP_auto_producer_<data>/` na raiz do projeto.
É só copiar os arquivos de lá de volta pra raiz.

## Arquivos (pra quem vai editar o código)

| Arquivo | Papel |
|---|---|
| `auto_producer.py` | orquestrador (loop). Dividido em SEÇÕES numeradas e comentadas |
| `launch_daemon.py` | lança o produtor em segundo plano (destacado) |
| `stop_auto_producer.py` | mata o produtor e os filhos, limpa o lock |
| `config/temas.json` | gêneros + temas (editável sem código) |
| `config/settings.json` | parâmetros (editável sem código) |
| `bin/story_pipeline.py` | o gerador de vídeo de verdade (chamado pelo produtor) |
