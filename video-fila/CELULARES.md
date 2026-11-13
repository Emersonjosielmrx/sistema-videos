# Celulares (Galaxy S20) como workers de render

Desde 04/11/2026 (dona: "adicionar um S20 ao nosso sistema ... pra renderizar vídeos"; "adicionei mais um"; "põe pra
rodar, documente"). Código: `D:\video-fila\celulares.py`.

## Os aparelhos

| alias ssh | aparelho | Tailscale | usuário Termux | CPU / RAM / disco livre | 10 s de 1080x1920 (libx264 veryfast / mediacodec) |
|---|---|---|---|---|---|
| `s20ultra` | S20 Ultra SM-G988B | 100.103.218.7 | u0_a303 | Exynos 990 (nproc 7) / 14 GB / 348 GB | 5,9 s / 2,9 s |
| `s20` | S20 SM-G980F | 100.117.134.73 | u0_a256 | Exynos 990 (8) / 7,3 GB / 40 GB | 8,4 s / 3,1 s |

- Acesso: sshd do Termux na **porta 8022**, só chave (`~/.ssh/id_rsa` do PC1). Alias em `C:\Users\Haylla\.ssh\config`.
- `~/.bashrc` de cada um sobe `sshd` e `termux-wake-lock` quando o Termux abre.
- Instalado: `openssh ffmpeg python git tmux termux-api` (FFmpeg 8.1.2, Python 3.13).
- **São descartáveis** (dona 04/11): trabalham quentes, sem limite de temperatura. Só barra o que faz o render falhar.
- Android: Termux e Tailscale com bateria **"Não restrito"**; senão o Android mata o Termux com a tela apagada.

## O que eles fazem

O celular não tem o pipeline (Python do Cortes, voz clonada, Gemini). Ele recebe **um comando FFmpeg pronto** com as
entradas e devolve a saída. Hoje está ligado em um ponto:

- **Cortes, junta-trechos** — `fx_clips._render_xfade_segment` (`D:\recapd-ambientes\producao\bin\fx_clips.py`): o
  filter_complex que junta os clipes com xfade/acrossfade (Shorts e anime longo; no longo levava até 57 min no PC1).
  Só no PC1: PC2/PC3/Kaggle não têm `D:\video-fila\celulares.py` nem a chave, e lá roda local como sempre.

Para ligar em outro ponto (qualquer projeto no PC1), troque o `subprocess.run` do ffmpeg por:

```python
if not (_celulares and _celulares.rodar_ffmpeg(cmd, timeout=900, rotulo="o que é")):
    subprocess.run(cmd, check=True, capture_output=True, timeout=900)   # local, como antes
```

carregando o módulo pelo caminho (nunca pôr `D:\video-fila` na frente do sys.path do projeto):
ver o bloco `_celulares` no topo do `fx_clips.py`.

`rodar_ffmpeg` devolve **True só se a saída chegou inteira aqui**. Recusa (e o PC renderiza) quando: entrada não é
arquivo local, o filtro aponta pra arquivo (`movie=`, `subtitles=`, `fontfile=`, `-f concat`...), entradas > 3 GB,
nenhum celular livre, ou deu erro/queda no meio. Um trecho que falhou no celular é refeito no PC (pior caso: o tempo
de uma tentativa).

## Como funciona

1. Vez: `estado\celulares\<host>.json` (1 render por celular; lock de processo morto ou > 4 h é solto sozinho).
   Preferência: S20 Ultra, depois S20.
2. Medida (vale 2 min, `estado\celulares_medida.json`): por ssh, `python3 -` lê CPU (`top`), RAM (`/proc/meminfo`),
   disco, bateria/tomada/temperatura (`termux-battery-status`) e ffmpeg rodando. Livre = no ar, sem render, RAM ≥ 1,5 GB,
   disco ≥ 5 GB e (na tomada ou bateria ≥ 20%).
3. 1ª conexão: tar das entradas pelo stdin (viram `in0.mp4`, `in1.mp4`...) + o ffmpeg em `~/render/<job>`.
   2ª conexão: `cat` da saída para `<saida>.celular.part` → renomeia. Depois `rm -rf` da pasta lá.
4. Mesmo encoder do PC (libx264, mesmo preset/crf): o `concat -c copy` dos segmentos mistura trecho do PC e do
   celular sem problema (testado 04/11: 2 × 23,03 s = 46,09 s, decodificação limpa). O `h264_mediacodec` (chip de
   vídeo, ~3x tempo real) NÃO é usado: muda o fluxo h264 e o concat por cópia quebraria.

Prova de 04/11 (S20, xfade de 3 clipes 1080x1920, 23 s, preset fast): **PC1 52,5 s × S20 44 s** com envio e volta.
Pela função real do fx_clips (4 clipes 720x1280 + transições gl): 13 s no celular, duração exata (25,2 s).

## Onde ver

- Painel :8790, Máquinas: cards **S20 ULTRA (celular)** e **S20 (celular)** (CPU, RAM, disco, bateria/temperatura no
  motivo, renders de hoje; o trecho em andamento aparece como cartão "FFmpeg: ...").
- `python D:\video-fila\celulares.py` — medida na hora.
- `python D:\video-fila\maquinas.py` e o log do controlador também listam `s20ultra`/`s20`.
- Log de cada render: `D:\video-fila\logs\celulares.log`. Contagem por dia: `estado\celulares_stats.json`.

## Comandos

```
python D:\video-fila\celulares.py                 # mede
python D:\video-fila\celulares.py testar [host]   # prova: xfade 1080x1920 no celular x PC1 + concat com trecho do PC
python D:\video-fila\celulares.py limpar          # apaga ~/render dos celulares (sobra de job que caiu)
python D:\video-fila\controle.py desligar celulares producao   # nada vai pros celulares (ligar = volta)
```
`CELULARES=0` no ambiente de um processo desliga só nele. Sobras de teste: `D:\video-fila\estado\celular_teste_*`
(o `testar` apaga sozinho; se ficou, pode apagar).

## Se um celular sumir

Card "não respondeu": Termux fechado, celular dormindo ou sem Tailscale. Abrir o Termux no aparelho (o `.bashrc` sobe
o sshd), conferir o Tailscale ligado e a bateria "Não restrito". Teste: `ssh s20ultra echo ok`.
Celular novo: rodar no Termux o comando de instalação (pkg install + chaves + sshd), pôr o alias no `~/.ssh/config`,
acrescentar em `HOSTS` (celulares.py), `LIMITES` (maquinas.py), `controlador.py`/`painel_controlador.py` (laço
`for cel in ...`) e `cols`/`CEL` no `painel_web\index.html`.

## Próximos passos possíveis (não feitos)

- Mais pontos do pipeline: `_concat_segments` (fallback de re-encode), `upscale_to_fullhd`, legenda queimada final.
- Rodar 2 segmentos ao mesmo tempo (1 por celular + PC) no `concat_with_xfade` — hoje é um segmento por vez.
- Pipeline inteiro no Termux (Shorts completos): exige portar os scripts PowerShell e o Python do Cortes para Linux;
  voz clonada (torch/RVC) não roda no celular.
