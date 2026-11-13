# Claude Code Video (25/10/2026)

> **OBRIGATÓRIO ANTES DE MELHORAR QUALQUER VÍDEO (dona, 01/11):** rode `python D:\video-fila\aprendizado.py aprovados`,
> leia `D:\video-fila\aprendizado\PARA_IMPLEMENTAR.md` (todos os aprovados + os candidatos do tipo que você vai mexer) e
> marque cada um aplicado/reprovado. Ninguém mais implanta isso — se você pular, fica parado. Passo a passo:
> `D:\video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md`. Mexeu em LONGO? Mesma obrigação em
> `D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md` (A FAZER / JÁ FEITO / DESCARTADO — não refazer o que já está lá).

Reels de propaganda dos NOSSOS produtos feitos do zero, com o **Claude Code (Opus 5.5 das contas Claude Pro do
OmniRoute) como diretor**. Inspirado no vídeo do Tiago Lemos ("Como o Claude 5.5 está acabando com editores"): o
Claude não renderiza, ele escreve, OLHA as fotos e o vídeo pronto e decide; o Python renderiza.

## Arquivos
- `cota_claude.py` — gerente de cota (usado também pelo projeto adicional). Lê no banco do OmniRoute (157, só
  leitura) as janelas `session (5h)` e `weekly (7d)` das contas `provider='claude'`. Pontos = menor % das duas;
  livre = soma. `decidir(custo, certeza)` deixa sempre `reserva_dono` pontos para o chat do dono. Diz a hora em que
  a cota volta. `python cota_claude.py` mostra tudo.
- `motor.py` — `claude.exe -p` (o da extensão do VS Code mais nova) com o gateway 20133 e `--setting-sources project`
  (sem os hooks do chat do dono), só ferramenta Read. `SemCota` vs `MotorErro`. Consumo em `estado/consumo.jsonl`.
- `efeitos.py` — cena quadro a quadro: `texto_atras` (rembg isnet recorta o assunto e o texto passa atrás) e
  `kenburns` (texto na frente com caixa). Zoom lento rumo ao foco.
- `gerar.py` — roteiro (Claude) → narração edge → imagens Flow → plano (Claude olha as fotos) → render → revisão
  (Claude olha folha de 8 quadros, até 2 refações) → final (saida/<conta>/ + Telegram). Estado por etapa em
  `trabalhos/<id>/estado.json`; `SemCota` no meio = `aguardando_cota` + `retomar_apos`.
- Reaproveita `D:\postador-de-videos\bin\produto\video.py` (narrar, imagem, Camada/karaokê, emendar, card_final,
  nivelar). Mexeu lá, conferir aqui.

## MODO EDITOR (padrão desde 25/10 noite — `"modo": "editor"` na config)
O dono reprovou o molde ("não é isso que vejo nos vídeos que me mandam"): o Claude Code tem que EDITAR.
`etapa_preparar_editor` junta narração (mp3 único + tempo absoluto de cada palavra), fotos, trilha e `briefing.json`
em `trabalhos/<id>/public`; `etapa_editar` roda o Claude Code com Read/Write/Edit/Bash em `remotion/` seguindo
`remotion/EDITOR.md` (motion design, telas de celular, texto cinético, karaokê, cartão) — ele gera quadros com
`npx remotion still`, OLHA e corrige; `etapa_render_remotion` renderiza (falhou → volta pro Claude com o erro).
1º vídeo editor 26/10 00:26 (Cardápio): 18 quadros vistos, ~45 min, ficou nível agência. Custo ~45 pontos.
Remotion 4.0.538 em `remotion/` (node_modules ~300 MB; o navegador interno baixa no 1º render).

## Empresas solares (01/11, dona: "esses estilos são variantes muito boas, por que não estão nos vídeos de energia solar?")
- `advance_novoestrela`, `globosolarenergiag`, `msenergycap` estão em `contas`. Kit em `postador-de-videos\bin\produto\kit.py`
  (`SOLARES`): fatos só da bio/pasta delas, nada de preço/% /"zerar"/garantia; `SOLAR_REGRAS` no roteiro e no briefing
  (sem chatbot/app: telas = conta de luz, telhado, inversor, orçamento no WhatsApp).
- Apresentador = só as fotos aprovadas do dono DELA (`dono_tag`: advance_clone / globo_clone / msenergy_clone), nunca
  o Emerson. Sem voz de personagem famoso (elenco) em cliente.
- Pronto: além de `saida/<conta>/`, vai para a fila da empresa (`ccv_<id>.mp4` + sidecar `legenda_insta`,
  `tipo_video: animacao`) em reels_advance / reels_globo / shorts_veo — o postador dela pega no próximo horário e o
  placar (`placar_estilos`, formato `animacao`) mede contra o clone Veo.

## Operação
- Tarefa `ClaudeCodeVideo` a cada 20 min → `cron_auto.bat` → `gerar.py --auto` (log `estado/gerar.log`, `cron.log`).
  Só COMEÇA vídeo novo com `livre - reserva >= custo_video_zero * margem_certeza`; `videos_por_dia` na config.
- NÃO posta sozinho: o vídeo vai para `saida/` e para o Telegram do dono.
- Desligar: `"ligado": false` no config.json.
- Custos da config são chute inicial (15 pontos por vídeo): recalibrar comparando `estado/consumo.jsonl` com a
  queda de pontos em `cota.json`.

## SEMPRE OCULTO (dona 28/10: "python vai invadir a minha tela, faça ser oculto e deixe documentado")
- Nenhum processo deste projeto pode abrir janela. A tarefa roda por `wscript D:\rodar_oculto.vbs`; todo ponto de
  entrada (.py) começa com `import sem_janela` (cópia COMUM: põe CREATE_NO_WINDOW em todo subprocess) e o
  `motor.executar` passa 0x08000000 SEMPRE (junto com a prioridade baixa). Script/ponto de entrada novo = mesma coisa;
  `subprocess` com creationflags próprio = some `| 0x08000000`. Teste à mão pelo Bash não conta como produção.

## Armadilhas
- edge-tts entrega palavras SEM pontuação: legenda tem que ser agrupada por fala (senão gruda fala com fala).
- O chat do dono gasta as MESMAS contas (25/10: 24 pontos em ~20 min) → a reserva existe por isso.
- Render ~5 min por vídeo de 20 s (PIL quadro a quadro).
