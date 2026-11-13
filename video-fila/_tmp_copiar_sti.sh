#!/bin/bash
# 12/11: copia pro STI (Linux) o mesmo conjunto que o instalar_pc3.py manda pro desktop. tar pelo ssh, 1 por vez.
LOG=/d/video-fila/logs/copiar_sti.log
H=emerson-sti-st@100.98.49.0
M=/d/hipercool-materiais
echo "[$(date +%H:%M)] início" >> $LOG
mandar() { # $1 = pasta-base local, $2.. = itens; destino ~/hipercool-materiais/<mesmo caminho relativo>
  base="$1"; shift; rel="${base#$M}"
  ssh -o BatchMode=yes $H "mkdir -p ~/hipercool-materiais$rel"
  tar -cf - -C "$base" --exclude='__pycache__' --exclude='*.bak*' "$@" | ssh -o BatchMode=yes $H "tar -xf - -C ~/hipercool-materiais$rel" \
    && echo "[$(date +%H:%M)] ok $rel: $*" >> $LOG || echo "[$(date +%H:%M)] FALHOU $rel: $*" >> $LOG
}
mandar $M/models kokoro huggingface depth-anything-v2-small
mandar $M/models/rvc embedders formant predictors pretraineds
mandar $M/tools applio
VOZES="porao drezin mike mattz ijax momo pie mangaticos guugou omelhormanhwa kkvirjao doinsuka solem8037 jubertim iki solemsun fatos_desconhecidos luiz_carlos_persy cid_moreira walter_white_breaking_bad homem_de_ferro_tony_stark thomas_shelby_peaky_blinders optimus_prime"
existe=""; for v in $VOZES; do [ -d "$M/models/rvc/vozes/$v" ] && existe="$existe $v"; done
mandar $M/models/rvc/vozes $existe
mandar $M/assets fonts generated_batch mascote mascote_mov memes_img overlays sfx sfx_extras sfx_foley sfx_memes sfx_prioridade trilhas _divisorias _downloads_vfx
echo "[$(date +%H:%M)] FIM" >> $LOG
