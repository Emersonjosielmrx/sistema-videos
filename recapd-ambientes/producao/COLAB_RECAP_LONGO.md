# Recap longo (deitado) na Colab — plano e estado

Pedido do dono (24/10/2026): os recaps longos de anime dos parceiros (anime_auto deitado) voltam a ser feitos, na
Colab grátis da conta **emersonjosiel649** (sem canal no YouTube; mesma do Kaggle). Uma conta só (termos da Colab).
Aba da Colab fica aberta no PC1 (Chrome do cofre); se faltar RAM, vai pra um notebook.

## Desenho
- PC1 (`anime_auto.py`, engine nova `colab`): baixa vídeo + legenda (yt-dlp fica no PC; IP do Google é barrado no
  YouTube) e sobe `source.mp4`, `cap_*.vtt`, `pedido.json` em `manhwa-drive:colab_recap/fila/<id>/`.
- Colab (notebook `colab_recap.ipynb`): monta o Drive, instala o código (`colab_recap/codigo.zip`), em loop pega o
  pedido sem `pronto.json`, roda `anime_worker_daemon.run_anime_task` (pula download se source.mp4 existe), copia
  `final_anime_deitado.mp4` pro Drive e grava `pronto.json` (ou `erro.json`).
- PC1: espera `pronto.json`, baixa o mp4, apaga a pasta do Drive e segue o fluxo de sempre (mid-roll, publicar).

## Passos
> **26/10:** o remoto `colab649:` foi DESATIVADO (Drive cheio; dono: nunca mais usar). Fila e arquivos passam para `manhwa-drive:colab_recap`. O trabalhador Colab (notebook no Drive da 649, lê a fila pelo Drive montado) precisa ser refeito para ler pelo rclone; Kaggle/VPS já leem pelo rclone.

1. [x] (histórico) rclone remoto `colab649:` (24/10, `credential-factory\rclone_drive_conta.py`). Pasta `colab_recap/fila` criada.
   Drive com só 3 GB livres → 1 vídeo por vez, apagar do Drive assim que baixar.
2. [~] Pacote: `colab\montar_pacote.py` (manhwa-drive:colab_recap/raiz + colab649: rclone.conf, sitecustomize,
   trabalhador, notebook). Sem vozes (deitado não usa clone). Decisão do dono 24/10: opção 1 = token do manhwa-drive
   vai no Drive da 649.
3. [~] `colab\colab_recap.ipynb` + `colab\abrir_colab.py` (cofre, Ctrl+F9, clica avisos; aba fica aberta).
   `colab\trabalhador.py` roda só o anime-pipeline.py (roteiro vem pronto do PC). Falta: vigia que reabre se cair.
4. [ ] Engine `colab` no anime_auto: `colab\cliente.py` (enviar/esperar) já existe; falta ligar no fazer_deitado.
5. [~] Teste: `python colab\cliente.py teste <work> <url> <titulo>` com aJnTMXbQnHw (DB Super, 11 min), pasta
   workspace\anime\_colab_teste_aJnTMXbQnHw, log colab\teste1.log. Dono quer ASSISTIR o resultado aqui.

## 1º recap pronto (24/10 20:37)
DB Super (aJnTMXbQnHw, original 11 min) → 8,3 min, 720p, -14 LUFS, voz edge direto (sem proxy), legenda libass,
imagem espelhada (efeito do pipeline). ~44 min de render na Colab (2 núcleos). Arquivo:
workspace\anime\_colab_teste_aJnTMXbQnHw\final_anime_deitado.mp4. Dono ia assistir.
Próximo (dono 24/10): produzir em escala (parceiro novo @Manhwa_Fresh, 237 vídeos), vídeos prontos direto pro
Drive. Rodízio entre várias contas Kaggle/Colab RECUSADO (termos: 1 conta por pessoa) → Kaggle da 649 como
principal (4 núcleos, roda sem aba) + Colab da 649 de reserva.

## Produção em escala (25/10 madrugada)
- Fila única manhwa-drive:colab_recap/fila (só arquivos pequenos) + originais/prontos de Kaggle/VPS em
  manhwa-drive:colab_recap/fila_src (Drive da 649 só tem 3 GB; rclone sem lixeira).
- Alimentador: `python colab\cliente.py alimentar https://www.youtube.com/@Manhwa_Fresh/videos` (2º plano,
  log colab\alimentar.log): do mais visto pro menos, mantém pedidos esperando, recolhe prontos → Drive
  (videos-backup/anime/1_youtube_pendente/<id>_<titulo>/video.mp4 + ficha na_nuvem). Estado: alimentar_estado.json.
- Trabalhadores (todos emersonjosiel649 / VPS próprias): Colab (abrir_colab.py), Kaggle (kaggle_lancar.py lancar;
  pedido novo só nas 1ªs 6 h da sessão), VPS em Docker `recap_worker` (vps_lancar.py <host> <cpus> <mem>):
  staging 4 CPU/8g, prod 2/3g, 157 2/3g (157 com só 17 GB de disco). Sinal de vida: colab_recap/vivo_*.json.
- Token: `cliente.py token_loop` (10 em 10 min). SSH da VPS: usar o ssh do Git Bash (o do Windows trava).
- Prontos: yKfgs7SXOb0 (Colab) e 3h0M55mBZfU (Kaggle) no Drive.
- 25/10 04:20: @Manhwa_Fresh = 84 vídeos até 2h30 e 153 acima (até 36 h, ex. pjOoN03xa0k "Completed"). Alimentador
  só manda até MAX_DUR_S=2h30 (render ~5x na Colab; Kaggle/Colab cortam em 12 h); os maiores vão pra
  alimentar_estado.json "longos_demais". Pendente decidir com o dono: cortar os compilados em partes de ~2 h
  (cada parte = 1 vídeo longo) ou só VPS. Gargalo atual: preparo no PC (download+Whisper+roteiro ~15 min/vídeo).
- Retrato rápido: `bash colab/checar.sh` (Git Bash).
- 25/10 06:30: 3º pronto (bXe7, VPS staging, ~1h40 de render com 4 núcleos). Pronto de Kaggle/VPS agora é MOVIDO
  dentro do manhwa-drive (fila_src → 1_youtube_pendente), sem baixar/subir pela internet de casa (480 MB levava
  >40 min). Só os da Colab ainda passam pelo PC.
- 25/10 06:40: YouTube "not a bot" até no extract_info. Alimentador agora passa pelo ytdlp_vez (vez, pausado,
  pausar no bloqueio; bloqueio não conta como falha do vídeo). Pausa de 40 min aplicada (4º bloqueio do dia).
  Preparo no PC é o gargalo e o YouTube limita: considerar baixar em ritmo menor, não mais rápido.

## Como subir a Colab (24/10, funcionando)
1. `python colab\montar_pacote.py` (código+assets no manhwa-drive; `--codigo` só código).
2. `python colab\cliente.py token_loop` em 2º plano (token de 1 h do manhwa-drive renovado a cada 10 min).
3. `python colab\abrir_colab.py` (fecha aba velha, abre, Ctrl+F9). `python colab\ver_colab.py` lê as saídas.
- Lições: `curl|bash` do rclone deu aviso "código não permitido" (não clicar em "Continuar mesmo assim");
  manhwa-drive é escopo drive.file (não compartilha) → baixar_drive.py pela API; Drive montado guarda cache dos .py
  → `force_remount=True`; saída de erro fica em iframe; Colab = Python 3.13.

## Achados
- 24/10: o DEITADO não usa voz clonada (VOZ_CLONADA só no fazer_short) → Colab NÃO precisa de Applio nem vozes
  (11,5 GB, não caberiam). Precisa: producao/bin (sem _SNAPSHOT/bkp), config, fontes, trilhas/assets, segredos de LLM.
- Worker carrega 56 módulos com 64 caminhos `D:\`/`C:\` fixos. Na Colab: `sitecustomize.py` que traduz
  `Path("D:\\...")` → `/content/raiz/D/...` (patch em PurePath.__init__), sem mexer no código do PC.
- Segredos são relativos (producao\secrets: omniroute.json, proxies.txt, gemini_estado.json); LLM via OmniRoute 157.
- Assets do render = producao\workspace\assets (junção → hipercool-materiais\assets): ~7 GB úteis (overlays 3,9 GB,
  trilhas 1,6 GB, dividers, mascote_mov, sfx...; fora models 15 GB e intros_voz). Drive da 649 só tem 3 GB livres →
  assets + código no `manhwa-drive:colab_recap/` (4,7 TB livres); Colab copia pro disco dela (~100 GB) a cada sessão.
  Pendente decidir: como a Colab lê o manhwa-drive (token do rclone dele no Drive da 649, ou compartilhar a pasta).
- 24/10: worker do PC2 já existe (`anime_worker_daemon.run_anime_task`); Colab não aceita conexão de fora (túnel
  proibido no grátis) → Drive como fila.
