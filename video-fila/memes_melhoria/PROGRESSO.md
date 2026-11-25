# Melhoria dos memes nos vídeos — trabalho da noite 24/11 (01:30 → 08:00)

Pedido da dona (23/11 23h50): "o máximo de agentes simultâneos possível; análise profunda de tudo que pode melhorar;
explore, teste, implemente; objetivo: usar os melhores memes da forma mais inteligente possível nos vídeos".
24/11 00h: "agentes APENAS com Opus; os tokens podem acabar — não perder o progresso; crons a noite toda até 8h".

## Regras (salvaguardas)
- Agentes: o hook do usuário BLOQUEIA general-purpose/opus 5.5 ("subagentes desligados neste modelo"). Usar `subagent_type: "opus-ajudante"` (Opus 4.6, sem ferramenta Write: grava com PowerShell Add-Content -Encoding utf8). Máximo 4 ao mesmo tempo (PC1 lento). Pesquisa web (F5/F6): `argon-pesquisa` / `gemini-pro-pesquisa`, que gravam pelo PowerShell também.
- 24/11 01:45: opus-ajudante (Opus 4.6) QUEBRADO esta noite — 5 de 5 caíram no 1º-2º passo com 'response exceeded 64000 output tokens', até com tarefa de 1 leitura. Não usar até a dona dizer. Usar sonnet-ajudante (revisão/análise, tarefas curtas: 1 passo por agente, resposta <= 40 linhas, SEM escrever arquivo — o chat principal grava o resultado no frentes\<ID>.md) e argon-pesquisa/gemini-pro-pesquisa (web).
- LIMITE DE SAÍDA (F1 e F3 caíram 01:40 com 'response exceeded 64000 output tokens'): o prompt do agente deve dizer: respostas e comandos CURTOS; nunca colar arquivo inteiro nem gerar script gigante numa resposta; cada Add-Content com no máximo ~40 linhas; ler arquivos grandes em partes (Select-String / Get-Content -TotalCount).
- Cada frente grava o progresso em `frentes/<ID>.md` A CADA achado (não no fim). Topo do arquivo:
  `ESTADO: pendente | em andamento | concluída` e `PRÓXIMO PASSO: ...`. Ao (re)começar, o agente LÊ o próprio arquivo
  e continua de onde parou — nunca refaz o que já está lá.
- Token acabou / erro de API: nada se perde; o próximo disparo do cron relança só as frentes que não estão `concluída`.
- Agentes NÃO editam código de produção. Só leem, testam fora da produção (cópias em `D:\video-fila\memes_melhoria\teste\`)
  e escrevem no arquivo da frente. Quem implanta é o chat principal, com backup + chave que desliga.
- Produção dos longos = `D:\recapd-ambientes\producao` (NÃO a cópia D:\github_sistema). NUNCA git reset/checkout/stash lá.
- Nunca apagar/mover nada de `D:\hipercool-materiais\assets\memes_img` (junction compartilhada com os Shorts).
- Nada de yt-dlp em rajada (1 por vez via ytdlp_vez). Nenhuma conta/login.

## Já feito (23/11 ~23h, chat principal) — conferir na frente F1
- `memes_novos\fichas.json` (novo): ficha de uso dos 20 memes novos (expressões que pedem cada um + "nunca").
- `producao\bin\memes_visuais.py`: escolha por pontos pela ficha (frase + anterior + emoção), penalidade de uso nos
  últimos 6 vídeos (`workspace\memes_historico.json`), sem meme em cena de morte/luto, 4 memes antes excluídos
  (01, 08, 12, 14) agora podem entrar. Backup: `memes_visuais.py.antes_contexto_23nov`. Desliga: `MEMES_CONTEXTO=0`.
- `producao\bin\anime-pipeline.py` `_memes_resumo`: meme do resumo não repete; série ≥ 3 frases do meme do meio;
  loudnorm no meme do resumo; registra os memes usados. SEM backup próprio antes da edição — a versão anterior
  (sem estas mudanças) está em `D:\github_sistema\recapd-ambientes\producao\bin\anime-pipeline.py` (23/11 18:44).
- Comparação entre projetos: feita (resumo na frente F2).
- Filtro dos memes pt (`D:\video-fila\memes_pt_filtro.py`): trocado para extrair .wav (`-map 0:a:0`); testado no 111
  (cortou a propaganda: ok). No download o filtro ficou DESLIGADO (travava no fundo); rodar à parte (frente F8).

## Frentes
| ID | Frente | Estado |
|----|--------|--------|
| F1 | Revisar/testar as mudanças já feitas (memes_visuais + anime-pipeline): bugs, casos-limite, teste a seco com roteiros reais | quase concluída (falta 1 longo real) |
| F2 | Comparação entre projetos (recap × hipercool × historias) | concluída (ver frentes/F2.md) |
| F3 | Inventário do banco de memes (contagens, durações, fichas/jsons) | concluída |
| F4 | Uso real nos vídeos já feitos + ligação com views/retenção | passo 1 feito (dá p/ cruzar: pipeline.log x metricas_studio) |
| F5 | Pesquisa web: como canais grandes usam memes (frequência, momento, volume, tela) | não feita — pesquisa web caiu a noite toda (timeout/sem cota) |
| F6 | Pesquisa web: seleção inteligente (embeddings PT em CPU, LLM, punchline, fichas, anti-repetição) | não feita — idem |
| F7 | Achados anteriores (catálogo do pesquisador, ENTREGAS, aprendizado, memórias) + o que a dona já reprovou | passo 1 feito (decisões da dona) |
| F8 | Memes pt do Desktop: rodar o filtro na pasta toda, conferir, e preparar os bons (com ficha) para o catálogo | filtro concluído (48 bons / 16 revisão); fichas propostas em andamento |
| F9 | Plano final: juntar F1-F8, lista priorizada do que implantar (com teste), para o chat principal aplicar | concluída (versão da noite; ver frentes\F9.md) |





## RESUMO FINAL DA NOITE (24/11 08h30)
Agentes: Opus 5.5 bloqueado pelo hook; Opus 4.6 quebrado (5/5 "response exceeded 64000 tokens"); usado Sonnet 5.5 + trabalho direto. Pesquisa web (F5/F6) caiu a noite toda (timeout/sem cota) — fica pro dia.
IMPLANTADO na produção (recapd memes_visuais.py, anime-pipeline.py, memes_novos\fichas.json), com backups e chaves:
- Meme escolhido pela FICHA do que a frase pede; sorteio por gatilho desligado (MEMES_SORTEIO_GATILHO=1 volta); sem meme em morte/luto/massacre; variedade entre vídeos (histórico 6 vídeos); resumo sem repetir + loudnorm; série longe do meme; imagem sem sorteio cego. Tudo desliga com MEMES_CONTEXTO=0.
- Teste a seco em 2 roteiros reais: 10 e 8 memes, todos no momento certo (antes 8 e 14, maioria sorteada fora de hora).
- Registrado em D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md (24/11 JÁ FEITO).
PARA A DONA: (A) aprovar memes de Desktop\memes_pt (48 bons, 16 em revisão p/ ouvir; rascunho de fichas em teste\fichas_memes_pt_RASCUNHO.txt) — é o que aumenta a quantidade; (B) conferir o próximo longo real renderizado.
Plano completo: frentes\F9.md.
