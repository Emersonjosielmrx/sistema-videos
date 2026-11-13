# ER_02 — Métricas do Studio vazias (impressões, CTR, retenção)

## Fato (29/10)
`D:\postador-de-videos\_analise\metricas_studio.json`: 595 vídeos, só 2 com `impressoes`. 66 com erro:
- 29 "nenhuma métrica achada na página (ver print metricas_<id>)"
- 25 "TimeoutError: Locator.inner_text: Timeout 30000ms exceeded"
- 8 "TimeoutError: Page.goto: Timeout 90000ms"
- 1 "TargetClosedError"
Os outros 529 não têm erro, mas também não têm impressões/ctr/ret30/continuaram (campos None). Ou seja, o leitor
roda, acha a página e devolve só as views.

Quem lê: `D:\postador-de-videos\bin\metricas_rede.py` e `D:\postador-de-videos\bin\youtube_studio_extras.py`
(pelo navegador, sem API — regra da dona: Google só pelo navegador, nada de chave no Google Cloud).
Os tokens OAuth de leitura dos 7 canais Noturno morrem ~29/10 (memória project_tokens_api_noturnos).

## Por que importa
Sem "impressões" e "visualizado x deslizou" (Shorts feed: "Viewed vs swiped away") nenhuma regra pode ser
provada: não sabemos se o gancho perdeu o teste ou se o vídeo nem foi mostrado (ER_01).

## Tarefa para o Fable
1. Descobrir por que os 529 voltam sem os campos (seletor mudou? aba errada — Shorts têm a métrica "deslizou" na
   aba Alcance/Engajamento?). Ver os prints `metricas_<id>` que o próprio leitor salva.
2. Fazer o leitor trazer, por Short: impressões, % visualizado x deslizou, duração média, % visto, inscritos.
3. Respeitar: sem rajada no Studio, login pelo cofre (memória project_login_cofre_sem_copia), limpar RAM antes
   (`chrome_conta._liberar_ram`), nada de janela na tela da dona.

## Fable — resultado
**29/10 03:20 — feito e testado no Studio real (inovare_ita, 24 vídeos em 86 s).**
1. **Por que os 529 "vinham vazios":** não vinham. O arquivo tem `continuaram` em 367 e `dur_media` em 413 (lidos
   pelo `retencao_lista` do lote desde 23/10, guardados também em `ret_lista`). O que faltava era `impressoes`
   (2/595): o `metricas()` por vídeo lê 3 páginas do Analytics, 3 vídeos por hora, e a aba "Alcance" de um Short
   com poucas views vem em branco (print `metricas_pPslAYPYyvg.png` de 28/10: página vazia) — por isso 65 erros.
2. **O que mudou** (`D:\postador-de-videos\bin\youtube_studio_extras.py` `retencao_lista` + `metricas_rede.py`
   `coletar_lote`): a tabela do modo avançado pede agora `VIEWS, SHORTS_FEED_IMPRESSIONS, SHORTS_FEED_IMPRESSIONS_VTR,
   VIDEO_THUMBNAIL_IMPRESSIONS, VIDEO_THUMBNAIL_IMPRESSIONS_VTR, AVERAGE_WATCH_TIME, AVERAGE_WATCH_PERCENTAGE,
   ENGAGED_VIEWS` e devolve por vídeo `views_periodo, continuaram, dur_media, pct_media, impressoes (miniatura),
   ctr, intencionais, feed_impressoes`. O lote grava em `ret_lista` e preenche `impressoes/ctr/intencionais` quando
   vazios (o placar de título por CTR passa a receber dado). Espera 90 s + 1 recarga (00:50 o Studio demorou e o
   lote saiu com "retencao de 0") e rolagem tolerante (scroll_into_view estourava com mais colunas).
   Prova: print `logs\yt_web\20261029_021608_fable_impressoes.png`; linha lida
   `TY0C2PNEaXs {dur_media 18, pct_media 55.4, continuaram 63.1, views_periodo 1418, impressoes 259, ctr 1.2, intencionais 822}`.
3. **"Mostrados no feed" (impressões do feed de Shorts): o YouTube devolve "—" por vídeo** nessa tabela, até no
   Total. Então não dá para ter "impressões do feed" por Short por esse caminho (nem pelo cartão do vídeo, que vem
   em branco para Short pequeno). Substituto que funciona e já está no arquivo: `continuaram == 100 e
   views_periodo < 10` = o feed não mostrou (ER_01). Para a maioria dos usos é o que se precisa.
4. Regras respeitadas: mesma `sessao()`/trava/notebook do lote (abriu no X200MA), 1 página por canal, sem rajada.
   Nada mudou no ritmo: o lote continua 4 canais por rodada, canal relido a cada 6 h.
