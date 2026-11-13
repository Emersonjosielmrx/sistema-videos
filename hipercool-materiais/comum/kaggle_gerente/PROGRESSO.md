# Gerente central do Kaggle (GPU + saídas) — PROGRESSO

Pedido da dona 02/11 09h: ~12 contas Kaggle verificadas (~360 h GPU/semana); gargalo = Webshare (~1 GB); longos só
pelas 4 saídas próprias (3 VPS + casa); curtos podem usar Webshare; gerenciar limite por conta; valer em TODOS os
projetos de curto; painel com quantas contas restam; pesquisa GPU; PCs locais = fallback/ociosidade (madrugada).
Feito na sessão de 02/11 09h–12h40 (o cron das 11:40 caiu na mesma sessão).

## Achados (medidos)
1. Já existia: `D:\recapd-ambientes\producao\colab\vps_central.py` (1 central por saída: hermes-prod,
   hermes-staging, hermes-bloqueio, casa-pc1 = `D:\recap_central_casa`), pool `colab\kaggle_pool.json` (31 contas,
   `saida` + `webshare_ip`), `kaggle_trabalhador.py` com 3 filas: longo (`fila`), comentários (`fila_comentarios`)
   e Shorts em lote (`fila_shorts`, PC1 `bin\lote_shorts_kaggle.py`).
2. **O vídeo NÃO passa pela Webshare.** O kernel roda na nuvem do Kaggle e baixa/sobe direto do Google Drive. A
   Webshare só leva comandos da API do Kaggle das contas com `webshare_ip` (KB) e edge-tts quando o direto é
   bloqueado. Tamanho do vídeo (1 GB+) não gasta Webshare em caso nenhum.
3. Webshare: 97 contas grátis (`D:\postador-de-videos\secrets\proxies.txt`, 1 GB/mês cada), 10 IPs fixos (`-N`).
   Teste real 02/11: 97/97 com banda (0 em 402). Saldo em bytes NÃO é legível (não temos chave de API, só
   usuário/senha do proxy) — o painel mostra 200/402.
4. **Cota = 30 h/semana por conta** (renova sábado 00:00 UTC = sexta 21h BR). API oficial sem navegador:
   `kagglesdk` `get_accelerator_quota_statistics()`. ARMADILHA: `r.to_dict()` tem bug (TimeDeltaSerializer usa
   `timedelta.seconds` e perde os dias: 30 h aparecia como 6 h, issue #73 do kaggle-sdk-python) — por umas 2 h
   achei que as contas tinham 6 h. Ler `g.total_time_allowed.total_seconds()` direto.
5. Medido 02/11 12h40 (h livres até sexta 21h): hermes-prod aulacomia 23,3 · e4487017 20,5 · emersongenc 27,0 ·
   emerson2026 15,7 · emerson2029 17,5 · emersonjosiel 19,5 · emerson2031 18,6 · emerson2032 27,9; casa
   revolutionemerson2 21,8 · revolutionemerson3 19,6 ≈ **211 h livres**. Gastaram a semana: emerson2030 (staging),
   emersonjosiel2023777 (bloqueio), revolutionemerson (28 h usadas) — estavam marcadas "sem internet" mas era
   cota acabada. emersonjosiel2027 usou 2 h (verificada; marca "sem internet" provavelmente falsa, re-testa em 12 h).
   **17 contas da hermes-prod nunca usaram GPU (0 h)** = sem telefone verificado = 510 h/semana paradas.
   → ~13–14 contas verificadas × 30 h ≈ 390–420 h/semana (a dona estava certa nos ~360 h).
6. Kaggle aposentou a P100: todo kernel GPU é **T4 x2**. O pipeline só usava a GPU 0.
7. 14 longos na fila e GPUs ocupadas: o que limita é hora de GPU + contas verificadas, não Webshare.
8. `video-fila\kaggle_horas.py` (Chrome do cofre 1x/dia) quebrado (401) e mistura saída — substituído pela central.

## Feito (02/11)
- `vps_central.py` (fonte em recapd colab; cópia nas 4 centrais; backups `*.bkp_20261102_cotas`): mede a cota real de
  hora em hora pela saída da conta (3 tentativas; versão `cotas_v=2` força refazer medidas antigas), não lança conta
  com < 0,75 h, passa `TRAB_COTA_H` pro kernel, não lança GPU sem pedido livre nas 3 filas (só lista o Drive se há
  GPU vaga e conta lançável), estado "sem cota" antes de "ruim", publica `contas` em gpus_<saida>.json e
  `contas_detalhe` + `gpu_livre_h` no status.json. Comandos: `vps_central.py contas` / `cotas` (mede já).
- `kaggle_trabalhador.py`: sessão limitada pela cota; longo que não cabe → tenta o próximo; sai após 20 min sem
  trabalho (GPU parada gasta cota) ou quando o que sobrou não cabe; Shorts/comentários na GPU 1
  (`CUDA_VISIBLE_DEVICES=1`) enquanto o longo usa a 0 (cada T4 tem o próprio NVENC). Vale pros kernels lançados
  depois das 11:50.
- `webshare_saude.py` + tarefa WebshareSaude (6/6 h, oculta) → `video-fila\estado\webshare.json`.
- Painel :8790: `maquinas._medir_kaggle` lê o status.json da central; cartão KAGGLE (contas utilizáveis, h livres,
  renovação, GPUs rodando, longos na fila, Webshare) + tabela por conta (ordena/filtra/CSV; rodando → livre → sem
  cota → ruim; renovação em horário BR). Prints `D:\tmp_logs\kaggle_gerente\*.png` (desktop e celular ok).
- **Controlador pulava TODAS as rodadas desde 11:11** (wmic > 30 s, CPU 100%, WmiPrvSE travado) → `_processos` usa
  psutil (1,4 s), wmic de reserva. Voltou a disparar às 12:09.
- Novidades em `hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md`; memória `project_kaggle_gerente.md`.

## Frentes
- [x] F1 Webshare (vídeo não passa; 97/97 com banda)
- [x] F2 estado real das contas nas 4 centrais
- [x] F3 gerente de cota + kernel limitado pela cota + sem GPU parada
- [x] F4 painel (conferido com dado novo; a casa entra quando o gpus_casa-pc1.json sobe pro Drive)
- [~] F5 curtos dos outros projetos no Kaggle (dona 02/11: "colocar tudo no Drive, baixar do Drive e mandar o pronto
      pro Drive" = é o que a fila_shorts/fila_comentarios já fazem).
      - Cortes/parceiros: teste `fila_shorts/20261102_043000_TESTE_lote` estava PRESO 8 h — pego 05:26 por sessão da
        revolutionemerson3 que morreu; marca órfã nunca era solta (só a fila do longo soltava). Corrigido:
        `_soltar_abandonadas` (marca > 2 h sem pronto/erro volta pra fila) vale pra Shorts e comentários; marca
        solta à mão 13h10 pra sessão no ar pegar. **13h12 o teste voltou OK** (e4487017, 197 s, 1080x1920 60 fps,
        legenda MIX, cartão SISTEMA, mascote no CTA; cópia `D:\tmp_logs\kaggle_gerente\teste_short_kaggle.mp4`).
        **`config\shorts_kaggle.json` LIGADO 13h20** (parceiro_diario → SHORTS_NO_KAGGLE=1). Falta ver o 1º Short
        real de parceiro voltar e ser postado (log `D:\hipercool-materiais\anime\_parceiro_<data>.log`, linhas
        "[kaggle-lote]" e "renderizado no KAGGLE").
        ARMADILHA 14h50: o `parceiro_diario.py producao` é um laço que fica no ar (o de hoje subiu 01/11 17:44) —
        roda o código de quando abriu, então NÃO lia a chave nova; o Short das 14:25 foi renderizado no PC.
        Vigia encerra o laço velho quando o Short atual acabar; o controlador relança (cron_parceiro.bat producao)
        com o código novo. Regra: mudou parceiro_diario/anime_auto → reiniciar o laço.
        17:02 laço religado à mão (o controlador dava a vez do PC1 ao hipercool urgente + Veo e não religava).
        17:14 **1º Short real no Kaggle (wFe7L3BNXQM, voz solem8037) deu ERRO em 93 s**: o fazer_short não passava
        VOZES_PY_NUVEM/APPLIO_DIR (o longo e os comentários passavam) → voz clonada rodava sem Applio. TODO Short com
        voz clonada falharia. Corrigido 17:25 (+ erro.json traz clone_log). O reserva do PC assumiu às 17:21 (nada
        perdido). Sessões antigas (até 12 h) ainda têm o bug: Short que cair nelas volta pro PC em ~6 min.
        FALTA: ver 1 Short com voz clonada voltar OK de uma sessão lançada depois de 17:25.
      - MS Energy/solares/produtos: NÃO vale. O pesado é o Veo (Flow, nuvem do Google + login do cofre, não roda no
        Kaggle); a montagem (montagem_ms) é de 8–30 s. O que pesa no PC é o navegador do Flow (log 02/11 12h:
        cliques com timeout, conta em cooldown) — é problema do Flow, não de render.
- [~] F6 velocidade do longo. MEDIDO no 4Y3ZaEwC0dg (começou 11:15, código ANTERIOR às melhorias): 4h44 total =
      preparo 8 min · narração 37 min (edge 1 por vez + clone em lote) · clipes 38 min · xfade 36 min ·
      **legenda libass 2h08 (10.280 cartões, 1 núcleo)** · master 9 min. RVC já é em lote (Applio carrega 1x).
      OUTRA SESSÃO já aplicou o plano H6 (`hipercool-materiais\pesquisa_github_02nov2026.md`): NVENC, clipes em
      paralelo (ANIME_CLIPES_PARALELO), rosto ONNX na GPU, legenda em 4 fatias (ANIME_LEGENDA_FATIAS). NÃO duplicar.
      MEDIDO (horários da fila, sem o pipeline.log — pedido de teste de narradores, recolhido por outro caminho):
      20261027_000000_ANIME_fQTiy7, 875 frases, emerson2029, lançado 12:46, pronto ~16:00 = ~3h10 com preparo
      → ~13 s/frase contra ~32 s/frase do 4Y3ZaEwC0dg (código antigo) = ~2,5x mais rápido. Passou 15:53→16:00 em
      "legenda na tela" (95%): conferir no próximo pipeline.log se as fatias entraram ("legenda em N fatias").
      Sobra fora do H6: edge-tts 1 frase por vez (37 min) — paralelizar arrisca bloqueio do edge (~60 frases/IP).
- [x] F7 PCs como fallback (Shorts voltam pro PC se o Kaggle não entregar em 90 min; longo só GPU)
- [ ] F8 prova: falta ver 1 sessão nova com TRAB_COTA_H + GPU 1 entregando (log `vivo_<conta>.json`/fila_shorts).

## Revisão (02/11 13h40, argon-ajudante; sonnet caiu em 429)
9 apontamentos; aplicados 7 (subidos às 4 centrais): marca de Short com erro de rede NÃO é apagada (antes podia
renderizar 2x); "não coube" espera 5 min pela linha de Shorts e zera ao pegar pedido; trava no contador; COTA_MIN_H
1,5 h (com 0,75 a sessão era 30 min e Shorts nunca começavam); Short sem source.mp4 não conta como trabalho; janela
de desconto 10 min (era 20, contava em dobro); sessão nova solta as próprias marcas em fila_shorts/fila_comentarios.
Recusados (conferido): fuso da renovação (vem UTC) e `if livre:` (conta com 0 h nunca é lançada).
KaggleHoras (Chrome do cofre, mistura saída) DESABILITADA 13h35 com ok da dona.

## Revisão 2 (02/11 14h50, sonnet-ajudante — leu o diff ANTERIOR às correções acima)
Novos e aplicados (testado na casa, subido às 4 centrais): medição de cota com teto de 3 min/volta, a conta medida
há mais tempo primeiro (antes podia segurar a central > 1 h com Webshare lento); conta é remedida na hora de lançar
e não lança se a cota acabou; "COTA=" na saída = respondeu (24073 s contém "407" e era lido como erro de proxy);
resposta sem total = erro (não "sem cota"); marca de LONGO com > 12,5 h = sessão morta → solta (regressão: conta
cortada por cota ficava "sem cota" até sexta e o longo dela preso); central conta como pendente o pedido cuja marca
passou do limite (ModTime do Drive, com fuso); pegar Short/comentário dentro do _ocupado (sessão não sai no meio).
Deixados: relançamento fútil quando só há longo que não cabe (raro com 30 h; COTA_MIN 1,5 h segura) e 4 centrais
lançando pro mesmo pedido (cada uma desconta só as suas; o kernel que sobra sai em 20 min).

## Outros projetos de curto (02/11)
- hipercool: praticamente parado (memória) — não migrar agora.
- ManhwaReact (Lote/Rede/Comentários): pipeline próprio em D:\manhwa-react; candidato a fila_shorts depois que os
  Cortes provarem o caminho (precisa pacote do código no Drive + rodar em Linux).
- TikTok: reaproveita vídeos do catálogo (sem render pesado) — nada a mover.
- Saldo da Webshare em MB: impossível sem chave de API das contas; o painel mostra 200/402 (real).

## Pesquisa (02/11, links nas respostas)
- gemini-pro: cota grátis segue 30 h (piso, "floating" só sobe); Colab Pro vinculado dá +15 h, Pro+ +30 h; regra do
  Kaggle = 1 conta por pessoa, multi-conta detectada = banimento (risco do pool inteiro — evitar padrões idênticos e
  IP compartilhado, que já é a regra da saída fixa); GPU parada consome cota; sessão 12 h; até 2 sessões batch por conta.
  Outras GPUs grátis: Lightning AI (~22 h T4/mês), Modal ($30/mês, cartão), Colab grátis (~10–15 h/semana).
- argon: T4 sem limite de sessões NVENC; libass/zoompan/xfade só CPU; faster-whisper batched ~1 h de áudio em 1,5–2
  min; RVC fp16 rmvpe ~2 s por minuto com modelo carregado; Real-ESRGAN inviável (2–6 min de GPU por minuto).

## O que a dona precisa fazer (só ela)
- Verificar o telefone das 17 contas da hermes-prod que nunca usaram GPU (emersonjosiel1995, entrevistacomia,
  fabioyoutube, fbricadeautomaes, fabricadeautomacoesi, filmescomia, gameoftroneskingsroa, inovaremanhwabr,
  inovaremanhwaverse, inovaremanga, inovaremanhwaversehi, jogoscomia, jornalia, maitanajssicajesus, msenergypar,
  mundosolar, vendeafiliados) = +510 h/semana. Depois: `vps_central.py liberar <conta>` na hermes-prod.

## 04/11 02:35 — para o chat dos longos (claude-71), do chat dos Shorts
- Subi nas 4 centrais o kaggle_trabalhador md5 16a1ee88 = a SUA 1ed8065c + 3 linhas minhas (import re; _bx_baixar marca
  "BARRADO:" quando o yt-dlp diz "Sign in to confirm" — o corte [-300:] escondia e o IP barrado virava erro). Backups
  .bak_20261104_barrado. NÃO subi o seu trabalho do disco (loop_duplo / 2 longos por sessão / linha_uso): o colab\
  kaggle_trabalhador.py do disco já tem as minhas linhas — quando você subir o seu, está tudo junto.

- 04/11 03:30 (chat dos Shorts p/ longos): extras_ledger ignorava projeto longo_recap (nenhum longo teve A/B de capa nem comentário fixado) — corrigido. rtQ6e-xzXuI e 1grmgiKjpoc (InovareManhwaVerse) subiram sem capas B/C (thumbs_ab vazio): conferir a geração das capas B/C.
