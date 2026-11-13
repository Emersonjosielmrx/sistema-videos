# Engenharia reversa — progresso (retomável)

Missão: o que os Shorts que dão views fazem de diferente → regras/código para todos os projetos; relatório semanal.
Tarefas complexas mandadas para o Fable: `D:\hipercool-materiais\tarefas complexas para fable 5.1\ENGENHARIA_REVERSA (parceiros - o que da views)\`.

## Feito
- 28/10 diagnóstico + placar + topo do PARA_IMPLEMENTAR.
- 29/10 `alcance_projetos.py` (por projeto, faixas, hora, reuso) → `alcance_projetos.json`. `_reuso.py` provou que
  reuso entre línguas NÃO derruba em pt. Docs ER_00..ER_06 no Fable. Nota no MURAL.

- 29/10 `titulos_parceiros.py`: 57 parceiros, 35.326 Shorts da lista guardada do Cortes
  (workspace\cache\discover_canal, sem yt-dlp). NENHUM traço do título separa 10% de cima x 10% de baixo do mesmo
  parceiro (maiúsculas 26/30 parceiros, "?" 13/21, emoji 12/11...). Título não é o que decide.
- 29/10 `fonte_x_nosso.py`: 264 dos nossos Shorts com fonte achada. Fonte < 100 mil views → 12% dos nossos passam de
  500; fonte 100 mil+ → 25–29% (sem ganho acima de 1 mi). Fonte no top 5% do parceiro (143 dos 264) = 20%, meio
  (50–80%) = 40% (n 25). SUPOSIÇÃO: evitar fonte < 100 mil; não precisa ser a mais vista.
- Fontes baixadas foram limpas: no disco só 5 source.mp4; no Drive só 11. Medida de vídeo exige baixar de novo.

- 29/10 `hora_mesmo_canal.py` (taxa >=500 da faixa MENOS a do próprio canal, canais pt de parceiro com 6+ vídeos):
  19–21 h −21 pts, pior em 6 de 6 canais (26 vídeos); 22–23 h +21 (4/1, 16 vídeos); 6–10 h +14 (3/0, 23 vídeos);
  11–14 h +4 (8/5, 96); 15–18 h −15 (2/3). Proposta A/B: tirar das 19–21 h e pôr às 22–23 h ou de manhã.
- 29/10 `amostra.py` (baixa top/baixo de cada parceiro, 480p, 1 a cada 2 min pela ytdlp_vez, para no bloqueio) →
  `D:\hipercool-materiais\engenharia_reversa\amostras\`; `medir.py` (ffmpeg: cortes/s, cortes 2 s, 1º corte,
  volume 2 s, silêncio inicial + info.json) → `medidas.jsonl`; `medir_nossos.py` mede os NOSSOS mp4 do ledger →
  `medidas_nossos.jsonl` e compara >=500 x <=10 no mesmo canal.

- 29/10 00:30 D: com 1,7 GB livres (não foi esta sessão: tudo dela = ~12 MB). Rodada da amostra PARADA com 6
  vídeos (cidademaresiarp, futtres, king_chan01 — 1 cima + 1 baixo cada). amostra.py agora só baixa com D: >= 5 GB;
  medir.py apaga o .info.json (~600 KB) depois de ler.
- 29/10 tarefa `EngenhariaReversaSemanal` (segunda 08:20, escondida, `semanal.bat`): amostra (n 5, máx 30) → medir →
  medir_nossos → relatorio_semanal (relatorios\<data>.md + resumo pelo avisos.py, origem engenharia_reversa).
  1º relatório (21–27/10): ≥500 13% → 21%, mediana 1 → 3.

- 29/10 03:55 `medir_nossos.py` traz do Drive (pelo `_NO_DRIVE.md` da pasta) 1 Short por vez, mede e apaga; compara
  com a régua do Fable (elegível = feed deu lote) e grava `comparacao_nossos.md`. Com 135 medidos:
  * 2º lote x só o 1º, MESMO canal (5 canais): duração −15 s em 5/5, % assistido +53 em 5/5, volume dos 2 s +0,5 dB 5/5.
    Geral: 2º lote dura 32 s (assistido 90%), 1º lote 80 s (33%).
  * Elegível x não elegível: nenhuma medida do vídeo separa (7/4, 5/6...) — bate com o Fable: elegibilidade é canal/upload.
  * Duração 30–45 s: 64% elegíveis; 60–90 s: 22%. % assistido cai de 89% (20–30 s) para 30% (60 s+).
  REGRA candidata (= T8 do Fable): Short de 20–35 s. Medir com A/B no mesmo canal.
- 29/10 tarefa `EngenhariaReversaMedir` (de hora em hora, escondida, `medir_nossos.bat`, trava contra 2 cópias, para
  com D: < 1 GB, apaga sobra do tmp): mede TODOS os nossos Shorts do Drive até acabar e os novos quando ganham views.
  Log `medir_nossos.log`. Não depende de chat.
- 29/10 04:15 Drive deu "rateLimitExceeded" (mesma conta do backup da produção). Parei a rodada; agora: 45 s entre
  vídeos, máx 40 por rodada (hora), para no 1º limite/lentidão e tenta de novo na hora seguinte. Medidos: 135.

- 30/10 13h — revisão geral (Claude), tudo testado:
  * Bloqueio do YouTube: amostra/continuo/longos olhavam só os últimos 300 caracteres do erro do yt-dlp; o "not a bot"
    vem antes do texto de cookies → o de 04:21 passou batido. Agora olham o erro inteiro, pausam o PC com motivo
    "engenharia reversa: ..." e gravam `bloqueio_er.json` (a pausa global é sobrescrita por outros projetos).
    `amostra.bloqueio_recente()` (12 h, D41) vale para o continuo E para a amostra do semanal.bat.
  * Prioridades do painel: a passada regravava o arquivo inteiro e apagava o que o painel acrescentou durante os
    downloads → agora grava item a item. Download de prioridade agora respeita a pausa do IP; bloqueio para a fila toda;
    canal pequeno não repete vídeo em top e baixo; 0 baixados vira "erro" (antes ficava em "medindo" para sempre);
    aviso no Telegram só das concluídas na passada (antes repetia as do dia a cada 2 h); script filho que estoura o
    tempo não derruba mais a passada e o traceback vai pro log.
  * Fontes do Cortes: 13 de 36 deram TimeoutExpired (AV1 de 40 min–3,5 h; este PC decodifica AV1 a ~0,4× com libaom;
    d3d11va/dxva2 não ajudam). `medir.medir(mp4, janela=120)` mede só os 2 primeiros min (campo `janela_s`); as que
    estouraram ganham 1 nova tentativa; 4 por passada. Teste: fonte de 52 min em 185 s.
  * `dados_nossos.py`: os 7 scripts que faziam exec() da metade do alcance_projetos.py agora importam dele (conferido:
    L/led/ms idênticos, 542 Shorts).

## Frentes (em ordem)
1. [ ] Lista leve (--flat-playlist, ytdlp_vez) dos Shorts de cada parceiro com views → `parceiros_views.jsonl`.
2. [ ] Medidas por vídeo do source.mp4 já baixado: duração, cortes/s, gancho 2 s, legenda, texto na tela.
3. [ ] Comparar 10% de cima x 10% de baixo do MESMO parceiro → achados com número.
4. [ ] Hora dentro do mesmo canal (separar de canal).
5. [ ] Relatório semanal (tarefa escondida, sem Opus).
6. [ ] Studio sem impressões (ER_02) — se o Fable não pegar, tentar aqui.

## Fable 5.1 — 29/10 (scripts novos nesta pasta, só arquivos)
- `continuaram_x_views.py [--csv]` — ER_01: elegibilidade (continuaram 100% com <10 views = o feed não mostrou), platô 1.000–1.500,
  % assistido ≥ 65% = 2º lote. Gera `continuaram_x_views.csv`.
- `hora_idiomas.py` — ER_04: hora local dos canais de língua × views (não é a hora).
- `juri_x_views.py` — CORTES_05: nota do júri × views/retenção (rodar de novo a partir de 30/10; hoje 0 pares medidos).
- Frente 6 (Studio sem impressões): FEITA pelo Fable no `retencao_lista` (impressões de miniatura/CTR/intencionais; feed = "—").
- Sugestão para o `semanal.bat`: acrescentar `%PY% -u juri_x_views.py >> semanal.log` e `continuaram_x_views.py`.
- 29/10 15:15 — medição travada em 147 desde 10h: o limite de 40 buscas/rodada contava vídeo SEM registro no Drive
  (133 sem `_NO_DRIVE.md` + 22 sem linha), que vêm primeiro na lista. Consertado: só busca real conta.
  Faltam 68 buscáveis. O 403 é "Requests per minute" do client_id PÚBLICO do rclone (projeto 202264815644,
  dividido com o mundo + o backup da produção): espera 90 s ×3 e, se seguir, sai e tenta na próxima hora.
- 30/10 03h — LONGOS PRIORIDADE da dona (14 vídeos): tudo em Fable ER_07_LONGOS_PRIORIDADE.md. Medidos 203 Shorts.
  Análises na fila EngenhariaReversaFila (5/15 prontas + 2 nossos pra comparar). Capas em
  hipercool-materiais\engenharia_reversa\capas_longos. Pendente: fechar a tabela quando a fila acabar.

- 31/10 13h — IMPLEMENTAÇÃO COMPLETA DAS 5 FRENTES DE PRODUÇÃO (Engenharia Reversa validada em código e disco):
  1. Preservação de Ativos e Placar Thompson A/B:
     * `postar_longos.py`: removido o `shutil.rmtree` destrutivo que apagava a pasta antes do teste A/B no Studio; agora preserva `postar.json` e as capas variantes `capa_b.jpg`/`capa_c.jpg`.
     * `capa_ia_anime.py`: inserida regra `MESMO_PROTAGONISTA` no template `REFAZER` para não transformar protagonistas monstros/insetos em humanos genéricos na Capa A. Adicionada função `registrar_vencedora_ab()` alimentando `placar_titulos`.
     * `notificar_telegram.py`: removido o `break` prematuro no loop de capas, integrando `vencedora_ab.json` e pontuando variantes A/B/C com ID composto sem colisão.
  2. Checagem de Vencedor A/B no YouTube Studio:
     * `youtube_studio_extras.py`: implementada `checar_vencedor_ab(pg, vid)` com flag `--checar-ab` para auditar `ytcp-video-thumbnail-editor`, extrair a variante vencedora e atualizar o placar Thompson automaticamente.
  3. Mascote Chibi, Etiquetas e Rótulos com Seta portados:
     * Portados overlays para `D:\hipercool-videos\bin\capa_ia.py` e `D:\manhwa-react\mr\capa.py`.
     * Reaproveitamento central de `D:\hipercool-materiais\assets\mascote` com contorno e sombra via Pillow (sem gerar via IA).
     * Testes visuais executados e validados em disco (`test_hipercool_rotulos.jpg`, `test_hipercool_etiqueta.jpg`, `test_mr_short.jpg`, `test_mr_grande.jpg`).
     * Melhoria `ae5a41` homologada e marcada como feita no `vigia_melhorias.py` para `hipercool` e `manhwa-react`.
  4. Tabela de Longos Prioritários Consolidada (18 de 18 analisados):
     * `ER_07_LONGOS_PRIORIDADE.md` atualizado com dados completos (cortes, trocas, Whisper pt/en, duração e views).
     * Comparação direta de calibração entre nossos vídeos (`qSM3JWPFeWA` e `ggQmCvCopt8`) e os parceiros de milhões.
     * `juri_x_views.py` reexecutado e validado.
  5. Folhas das Capas mais Vistas dos 8 Parceiros Atualizadas:
     * `capas_referencia.py` executado com sucesso: feeds RSS lidos e geradas as folhas `_folha.jpg` em `D:\hipercool-materiais\engenharia_reversa\capas_referencia\<canal>\` para zenimanwhasrecap, oporaodacidadela, Doinsuka, deboxkkj, TheKingH05, NoiManhwa, Manhwatriggerr e AmericanNickas.
  * Documento de auditoria detalhado gravado para o Fable 5.1: `ER_08_AUDITORIA_ACOES_PRODUCAO.md`.
- 31/10 17h (Opus) — auditoria do trabalho acima: placares limpos de dados de teste, chave A/B própria, sem vitória
  falsa da A, capa B com foto de pessoa real tirada do A/B do -E5o1Q1JrPE, mascote x título no manhwa-react, rótulos
  sem rosto no hipercool, ER_07 corrigido (palavras do Manhwa Fresh = tradução do Whisper). Detalhe: ER_08 seção 2b.
  Pendente: agendar o --checar-ab (feito 01/11 no extras_ledger).
- 01/11 — LONGOS PRIORIDADE: 14 de 14 com ANALISE.md. O hJaAZWXA7i4 tinha falhado em 30/10 (a IA respondeu 6.584
  letras sem a linha ===LINHA_DO_TEMPO===); refeito só a chamada da IA com meta/cortes/fala já no disco (sem YouTube),
  avisando que a fala é tradução do Whisper (original em inglês). Achado novo: abre com choque visual aos ~50 s (avião
  cai na equipe de TV), zero CTA nos 10 primeiros min, 1 corte a cada ~9 s, narrador "parça" ("our boy").
- 01/11 ~13h — listas A FAZER / JÁ FEITO / DESCARTADO dos longos em linhas\LONGOS\LONGOS_MELHORIAS.md (IDs L-xx; já
  feitos marcados no código "# L-Fx"); o analisador recebe a lista (_ja_temos) pra não repetir. Rodadas ~15h e ~17h
  (cron desta sessão) mandam só o NOVO. ENVIADO: claude-a9 (pipeline de longos E Shorts) = L-05..L-12 menos L-08 +
  4 aprovados dos Shorts (64e54485, b450f844, edd839f7, 1e25c542); claude-25 (só capas A/B/C) = L-08 capa tríade.
  claude-a9 confirmou: é o chat dos LONGOS (e dos Shorts cortados dos longos); aplica L-05..L-12 e os 4 itens depois da
  PREVIA3. Disse que NÃO é o chat dos Shorts de parceiro/Cortes — perguntado a claude-1a e claude-b0 se algum é.
  Respostas: claude-b0 = limpeza do D: e consulta de postagens; claude-1a = projeto novo D:\videos-comentarios. NENHUM
  chat aberto cuida dos Shorts de parceiro/Cortes (01/11 ~13h). Rodadas: só mandar Shorts de parceiro quando a dona
  abrir/indicar um chat; até lá ficam no PARA_IMPLEMENTAR.md (obrigatório pelo CLAUDE.md do recapd).
- 01/11 15:35 RODADA: longos sem análise nova (17 analisados, fila vazia); nenhum L-05..L-12 implantado no código
  ainda. Shorts: 1 aprovado novo (b53d6dd2, mascote no ombro) REPROVADO — veio de vídeo nosso ("PREVIA") e fere a
  regra da mascote só como figurinha. Nada novo enviado a claude-a9 nem claude-25.
- 01/11 17:40 RODADA: longos sem análise nova (17, fila vazia); nenhum L-05..L-12 no código ainda. Shorts: os mesmos 4
  aprovados (já mandados). Nada enviado. Nova linha VISUAL criada (linhas\VISUAL\visual.py, 4 canais de edit/AMV, 60
  vídeos na fila) — espera o D: passar de 5 GB livres pra baixar (estava 4,1 GB).
- 01/11 ~20h VISUAL: tarefa EngenhariaReversaVisual (2 em 2 h, escondida, visual_fila.bat) rodou 18:03; decupou Toji
  (lynJABr10N4) e Sukuna (8Fyb0LXw1BU) mas o resumo falhou (importava o claude_client do hipercool, sem
  generate_text) — corrigido (carrega o do recapd pelo caminho) e resumos feitos dos blocos salvos. VISUAL_MELHORIAS.md
  com V-01..V-09; ENVIADO a claude-a9. Rodada 20:03 em andamento (MHA tFkai-TY9J8).
- 01/11 noite VISUAL: a rodada das 20:03 ainda rodou o código velho (mesmo erro no resumo) e regravou a fila; arrumado.
  3 de 49 prontos (Toji, Sukuna, Sung Jin Woo); MHA voltou pra fila (YouTube pediu login nele). claude-a9 já implantou
  V-01, V-03, V-04, V-05, V-08 (fx_visual.py) e V-09 já existia. Novo V-10 (glitch RGB no cartão de sistema) +
  ajuste "micro punch nas batidas fracas" NÃO ENTREGUES: os chats foram reabertos (~21h, nomes novos: claude-08 x2,
  claude-86, veo PRODUTOS, FLUXOS N8N, nova versao rafael) e não se sabe qual é o dos longos. Ficam na lista
  VISUAL_MELHORIAS.md (V-10 + nota do micro punch); mandar quando a dona disser qual chat é o dos longos.
- 02/11 ~20h VISUAL: 19 de 49 edits decupados (tarefa sozinha). Os 12 do kit (V-01..V-12) já estão em JÁ FEITO (chat
  dos longos implantou). Contagem nos blocos: o kit aparece em todos. Novos em A FAZER: V-13 ondulação de calor/energia
  (17× em 6 vídeos), V-14 dupla exposição (= aprovado edd839f7), V-15 corte mascarado seguindo o golpe, V-16 tela
  dividida diagonal no confronto, V-17 micro-corte de 4 quadros no olho. 6 falharam (vídeo cortado truncado, erro
  -138) — visual.py agora apaga o arquivo e tenta 1 vez mais; os 6 voltaram pra fila. Faltam 30.
