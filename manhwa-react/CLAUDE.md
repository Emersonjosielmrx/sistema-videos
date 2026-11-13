# ManhwaReact - regras e indice para o agente

> **OBRIGATÓRIO ANTES DE MELHORAR QUALQUER VÍDEO (dona, 01/11):** rode `python D:\video-fila\aprendizado.py aprovados`,
> leia `D:\video-fila\aprendizado\PARA_IMPLEMENTAR.md` (todos os aprovados + os candidatos do tipo que você vai mexer) e
> marque cada um aplicado/reprovado. Ninguém mais implanta isso — se você pular, fica parado. Passo a passo:
> `D:\video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md`. Mexeu em LONGO? Mesma obrigação em
> `D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md` (A FAZER / JÁ FEITO / DESCARTADO — não refazer o que já está lá).

**LEITURA OBRIGATORIA (dono, 15/10): `LEIA_MELHORIAS_HIPERCOOL.md`** (fonte oficial e mais nova:
`D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md`). Ao mexer neste projeto, aplique aqui o que vale pra ele:
- titulo/descricao/tags SEM o nome da obra, com palavras buscadas (`config/seo_palavras.json` do hipercool);
- capas em rodizio com teste A/B;
- extras do Studio (`D:\postador-de-videos\bin\youtube_studio_extras.py`);
- estrutura/retencao, efeitos 2.5D, censura so nas partes.

Copie o codigo do hipercool em vez de reinventar.

**Vozes (dono, 15/10)**:
- edge `pt-BR-AntonioNeural` é PROIBIDA (Francisca e Isabella liberadas pelo dono em 16/10; Francisca = base da voz clonada);
- usar as Multilingual aprovadas, com voz fixa por personagem (secao 4b do `LEIA_MELHORIAS_HIPERCOOL.md`);
- tarefa agendada nao pode abrir janela de cmd/python na tela (`D:\hipercool-videos\bin\sem_janela.py`).

**Postagem / rede de 19 canais do YouTube: leia PRIMEIRO `HANDOFF_REDE.md` e `REDE_ESTADO_E_PENDENCIAS.md`** (05/10).
Pipeline de video - leia nesta ordem: `HANDOFF.md` (historico completo, o que foi tentado, pendencias, armadilhas) -> `README.md` (uso) -> `AUDITORIA.md` (recursos) -> `PLANO.md`.

- Projeto: RPA de pos-producao de Shorts de react para a rede de canais ManhwaReact / CenaReact / InventoReact (webcam em cima, video reagido embaixo).
- Python: sempre `.venv\Scripts\python` com `PYTHONUTF8=1`. Nao usar o venv de `D:\hipercool-videos`. Para escrever arquivos grandes, use a ferramenta Write (heredocs quebram).
- ffmpeg: `D:\hipercool-materiais\bin\ffmpeg.exe` (8.1 gyan essentials). `drawtext` e instavel: texto via ASS (`mr/captions.py`) ou HyperFrames (`mr/hyperframes.py`).
- Caminhos dentro de filtros: `mr.common.ffpath()`. Overlays alpha: `tpad` transparente (nunca `-itsoffset`). Um render por vez (pagefile da maquina esta cheio).
- Quem fala: labios (MediaPipe, `mr/lips.py`) + correcao do editorial. O audio do video reagido vem misturado em mono com o mic.
- LLM: `mr/llm.py` (proxy Opus 4.6 -> Sonnet 4.5 -> Claude CLI). Groq para Whisper. Segredos: `secrets_proxy.json`, `D:\postador-de-videos\secrets\groq_keys.json`.
- Cache por etapa em `work/<slug>/`; apague o json da etapa (ou `--force`) para refazer.
- Fluxo do usuario: `1-COLOQUE-AQUI` -> botao no desktop -> `hipercool-materiais\manhwa-react\shorts\<canal>\`. Nao refazer videos prontos sem pedido.
- Teste rapido: `python manhwareact.py process "<video>" --dry-run` e conferir `work/<slug>/part1/edl.json` e `captions.ass`; para visual, extraia frames com ffmpeg e mostre.
- O usuario escreve em portugues com erros de digitacao e quer respostas diretas em portugues.

- Postagem: `manhwareact.py rede` (mr/rede.py) + mapa `D:/postador-de-videos/config/rede_canais.json`. `distribuir_videos.py` esta DESATIVADO e `CANAIS_E_DISTRIBUICAO.md` desatualizado. Nunca ligar gerador de likes (D:/projetos-navegador). O dono delegou a aprovacao dos videos ao agente (conferir quadros antes: `testes/folhas_quadros.py`).
- Rede, 3a fonte (15/10, pedido do dono): Veo LIMPO de `D:\hipercool-materiais\veo\limpos\` (feito por `D:\postador-de-videos\bin\limpar_veo.py`: sem a marca @InovareStories e sem o slide de propaganda/WhatsApp que derrubou os canais antigos do Veo). So entra nos canais de `REDE_PADRAO["canais_veo_limpo"]` (inventoreact, manhwareact), sem nota do diretor e com a nota minima: pega so a vaga que sobrar depois dos reacts do dono. Ganha o @ do canal (rebrand) e o agente do canal escreve o titulo; ao postar, so marca `posted_url` no json (a pasta nao e movida). Nunca usar `veo\pos_final\completo` (COMPLETO = com propaganda). Backup do rede.py antes: `mr/rede.py.bkp_20261015`.
- Rede, aprendizado entre projetos (15/10): o agente do canal recebe `memoria_rede` (titulos que mais/menos renderam em 48 h nos OUTROS canais e projetos, de `D:\postador-de-videos\_analise\aprendizado_global.json`, gerado por `notificar_telegram.py` medir_48h). Braco de titulo `nome_obra` virou `busca` (palavras buscadas, sem o nome da obra) e `revisar()` barra o nome da obra do editorial (`resumo.obra`). Dados de 15/10: react rende (~1.100 views/48 h); os recaps do hipercool postados no mesmo dia em 7-8 canais estao com ~0 views (padrao "mesmo video em varios canais").
- Botoes do dono: pasta "ManhwaReact e Rede de Canais" na area de trabalho (recriar: `scripts/criar_atalhos.ps1`). LIGAR/DESLIGAR a postagem automatica = `rede --ligar` / `rede --desligar` (arquivo `D:/postador-de-videos/config/POSTAGEM_DESLIGADA.json`). Desligada: rede, comentarios, ciclo 06:40 e VO3 nao postam nem abrem navegador. LIGAR faz as pendentes de hoje (secao 13 do HANDOFF_REDE.md).
- Backup no Google Drive (todos os projetos): `scripts/backup_drive.py` (tarefa BackupDriveVideos, 05:40; `--simular` mostra o plano). Quem foi postado onde vem do catalogo central `D:\postador-de-videos\bin\catalogo.py` (tambem diz ao TikTok/Instagram o que reaproveitar e baixa do Drive na hora; contas em `D:\postador-de-videos\config\reuso_plataformas.json`). Rclone em `D:\tools\rclone.exe`, remoto `manhwa-drive:videos-backup/<projeto>/` (mesma conta dos backups das VPS). Sai do PC 3 dias depois da ultima postagem; tambem os rejeitados e os brutos do Veo que ja viraram final. Filas (shorts/cortes/grandes, topo do veo\pos_final, animes recap) e reabertos ficam. So apaga do PC o que o rclone conferiu; o que saiu fica em `logs/backup_drive.jsonl` (recuperar: `rclone copyto <drive> <local>`). Apaga tambem wav/temas do `work/` sem nada na fila.

## Bugs conhecidos

- ~~Blocklist de copyright nao bloqueia nada~~ **CORRIGIDO 16/10** (`mr/music.py:_blocklist` le `x["arquivo"]` dos dicts; `_candidates` compara tambem so o nome do arquivo). Antes 163 das 324 faixas sorteaveis estavam na blocklist; agora 161 sobram. 7 favoritas da biblioteca ficaram barradas (Pokemon, HxH, Winx...), como manda a regra do proprio modulo. Blocklist: `D:/hipercool-materiais/_curadoria/copyright_blocklist.json` (165 faixas). Backup: `mr/music.py.bkp_20261016`.
- ~~Trilha com efeito sonoro/meme, prioritarias ignoradas, mesma faixa sempre~~ **CORRIGIDO 16/10** (selecao do hipercool `bin/fx_music.py` adaptada em `mr/music.py`): sai lixo (`LIXO_RE`: "Undertale Sound Effect - Taking Damage" tinha ido pra um video) e faixa < 1 min; `prefer_priority` (estava no config sem efeito) agora vale: ~85% prioritarias de `trilhas/prioritarias/` com o clima do `climas.json` (a blocklist vale pra elas tambem); nao repete as ultimas 16 (`work/trilhas_recentes.json`). Engracado tinha 1 faixa so, agora 4. Mix (ducking, -14 LUFS) nao mudou. Backup: `mr/music.py.bkp_20261016_trilha`.
