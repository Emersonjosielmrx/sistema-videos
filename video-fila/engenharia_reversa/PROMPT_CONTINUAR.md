# Prompt para outro agente continuar (30/10/2026)

## Prompt

```
Você vai continuar dois trabalhos que já estão feitos e testados. Responda à dona sempre em português do Brasil.

CONTEXTO — leia antes de mexer:
- D:\video-fila\engenharia_reversa\PROGRESSO.md (seção "30/10 13h — revisão geral")
- D:\video-fila\engenharia_reversa\CAPAS_REFERENCIA.md (capas: análise dos 8 canais de referência e o que entrou no código)
- D:\recapd-ambientes\CLAUDE.md e D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md (linha de 30/10 em "Novidades")

O QUE JÁ ESTÁ PRONTO
1. Engenharia reversa (D:\video-fila\engenharia_reversa): detecção de bloqueio do YouTube no erro inteiro do yt-dlp +
   marca bloqueio_er.json (regra D41: 12 h sem baixar depois de bloqueio causado pela ER); prioridades do painel gravadas
   item a item (config\er_prioridades.json); medição das fontes do Cortes só nos 2 primeiros minutos
   (medir.medir(mp4, janela=120)); dados_nossos.py substituiu o exec() do alcance_projetos.py em 7 scripts.
   Tarefas agendadas que rodam isso sozinhas: ERContinuo (2 h), EngenhariaReversaMedir (1 h), EngenhariaReversaSemanal (seg 08:20).
2. Capas do recap de parceiro (D:\recapd-ambientes\producao\bin\capa_ia_anime.py):
   - A = capa do parceiro melhorada (capa_melhorada), B = a mais sensual com etiqueta estilo AmericanNickas
     (capas_ab, _desenhar_etiqueta), C = o mesmo protagonista numa pose do catálogo com rótulos estilo Porão/Zeni
     (_rotulos, _seta). Mascote colada como figurinha PNG (_colar_mascote). Visão responde "exposto" (reprova nudez) e
     dá as caixas dos rostos "ele"/"ela".
   - anime_publish.py grava "thumbs_ab" no postar.json; D:\postador-de-videos\bin\extras_ledger.py passa --ab pro
     youtube_studio_extras quando o vídeo abre.
   - Teste real feito: D:\hipercool-materiais\engenharia_reversa\capas_teste_ab\_comparacao.jpg (versão 1, com os
     defeitos já corrigidos, em capas_teste_ab\v1\).

O QUE FALTA (em ordem)
1. Conferir a 1ª postagem real de longo de parceiro depois de 30/10 14h: o postar.json tem "thumbs_ab" com 3 capas?
   As capas B/C saíram com o protagonista do parceiro (não humano trocado)? Em _analise\extras_ledger.json do postador,
   o resultado de "teste_ab" do vídeo: "ok", "pendente: canal em verificação" ou "aviso: ..." (ver os prints do
   youtube_studio_extras). Se deu aviso, corrigir teste_ab() no youtube_studio_extras.py olhando os prints.
2. Ler o VENCEDOR do teste A/B no Studio e alimentar o placar de capas (placar_titulos, categoria "capas") com a pose
   de cada variante (campo "pose" no <capa>_b.capa.json / _c.capa.json). Hoje o placar só aprende com a capa A
   pelas views de 48 h (notificar_telegram.py ~linha 1108). O hipercool já tem capa_ia.registrar_vencedora — copiar.
3. Levar mascote + rótulos com seta pro hipercool (D:\hipercool-videos\bin\capa_ia.py, que já tem A/B) e pro
   manhwa-react, marcando no vigia: python D:\postador-de-videos\bin\vigia_melhorias.py --marcar <projeto> <id> feito.
4. ER: quando a fila do EngenhariaReversaFila acabar, fechar a tabela do ER_07_LONGOS_PRIORIDADE (PROGRESSO.md, último
   item). Rodar de novo juri_x_views.py (deve ter pares medidos a partir de 30/10).
5. Atualizar as folhas de referência de vez em quando: python D:\video-fila\engenharia_reversa\capas_referencia.py

COMO TESTAR UMA CAPA SEM GASTAR GERAÇÃO
  cd D:\recapd-ambientes\producao
  D:\veo\venv\Scripts\python.exe -X utf8 bin\capa_ia_anime.py --anime x --saida teste.jpg --so-compor <imagem.png> --estilo rotulos|etiqueta|frase --texto "..." --cena "..." [--checar]
Geração real (A+B+C, ~15 min pelo Flow):
  ... bin\capa_ia_anime.py --anime "x" --saida <pasta>\capa.jpg --texto "..." --cena "..." --source-url <url do vídeo do parceiro> --ab
Sempre OLHE as imagens geradas antes de dizer que está bom (o 1º teste trocou a formiga por um humano e só a
imagem mostrou isso).

Ao terminar cada item: anote no PROGRESSO.md (ou no CAPAS_REFERENCIA.md, se for de capa) com data, o que mudou e como
foi testado.
```

## Restrições (o que o agente NÃO faz)

```
RESTRIÇÕES — NÃO FAÇA:
- Não poste, não agende e não mude visibilidade de vídeo por conta própria; postar é com o sistema da fila. Nunca
  postar pela API do YouTube (só navegador; politica.postar_youtube recusa).
- Não baixe nada pelo IP de casa quando bloqueio_er.json ou D:\video-fila\ytdlp_pausa.json indicar bloqueio recente;
  yt-dlp sempre pela vez única (ytdlp_vez). Para listar canais use o feed RSS público / i.ytimg, não yt-dlp.
- Não gere capa com nudez nem cara de menor: "exposto" e "adultos=false" reprovam e isso não se afrouxa. Não copie o
  estilo do The King H (hentai explícito). Sensual = roupa reveladora que cobre tudo.
- A mascote é chibi: nunca pedir para a IA desenhá-la junto das mulheres nem em cena sensual; ela só entra como
  figurinha colada (PNG).
- Não troque o protagonista da capa do parceiro por outro personagem (é por ele que o público reconhece a obra).
- Não faça commit, push nem git checkout/reset nos projetos sem a dona pedir. anime_publish.py tem mudanças não
  commitadas de outra sessão: mexa só no bloco das capas e leia o arquivo antes.
- Não apague vídeos, amostras, medidas (*.jsonl), caches de capa nem nada em celulares\ / workspace\ de produção.
  Downloads e temporários só no disco D (nunca no C); confira o espaço livre do D antes (pare abaixo de 5 GB).
- Não mate processos pythonw de produção (recapd/hipercool) nem processos de outra sessão do Claude; confira o
  processo pai antes.
- Não suba o volume de downloads da ER (n/max/pausa da amostra) nem desligue a regra D41 de 12 h.
- Não mexa em canais_status.json, youtube_navegador.json, cotas/teto de postagem nem em credenciais/secrets.
- Não pergunte coisas à dona que dá pra resolver pelo código ou pelos arquivos; só pare para perguntar antes de ação
  irreversível ou que saia para fora (postar, publicar, apagar).
```
