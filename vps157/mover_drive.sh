#!/bin/bash
# Move pastas/arquivos da VPS 157 para o Google Drive (criado 26/10/2026).
# Para cada item: copia para manhwa-drive:vps157-arquivo/<destino>, confere com rclone check
# e so entao apaga o local. Se a conferencia falhar, NAO apaga e anota no log.
# Uso: mover_drive.sh <origem> <destino_no_drive> [<origem> <destino> ...]
# Origem "imagem:<sha256:ID>" = imagem Docker: vira <tag>.tar.gz (docker save, todas as tags dela; volta com
# rclone cat ... | gunzip | docker load), confere o md5 e so entao faz docker rmi.
set -u
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"
REMOTO=manhwa-drive:vps157-arquivo
LOG=/opt/limpeza-vps/drive.log
# rede da 157 cai as vezes: pedacos pequenos e muitas tentativas por pedaco (sem isso um arquivo de 2 GB recomecava sem fim)
OPTS="--log-level ERROR --drive-chunk-size 16M --retries 5 --low-level-retries 50 --contimeout 60s --timeout 120s"
exec 8>/run/mover_drive.lock
flock -n 8 || { echo "ja tem um envio rodando"; exit 1; }

tags_da_imagem() {
  docker images --no-trunc --format '{{.ID}} {{.Repository}}:{{.Tag}}' | awk -v i="$1" '$1==i && $2!~/<none>/{print $2}' | sort -u
}

existe() {
  case $1 in imagem:*) [ -n "$(tags_da_imagem "${1#imagem:}")" ];; *) [ -e "$1" ];; esac
}

mover_imagem() {
  local id=$1 dst=$2 tags
  tags=$(tags_da_imagem "$id")
  [ -n "$tags" ] || { echo "$(date '+%F %T') pulado (imagem nao existe): $id"; return 0; }
  # nunca a imagem de um container (ligado ou parado)
  if docker ps -aq --no-trunc | xargs -r docker inspect -f '{{.Image}}' 2>/dev/null | grep -qx "$id"; then
    echo "$(date '+%F %T') pulado (imagem em uso): $tags"; return 0
  fi
  local nome; nome=$(echo "$tags" | head -1 | tr ':/' '__').tar.gz
  local md5f=/run/mover_drive.md5
  echo "$(date '+%F %T') enviando imagem $(echo $tags) -> $dst/$nome"
  rclone deletefile "$dst/$nome" --log-level ERROR 2>/dev/null
  if docker save $tags | pigz -1 | tee >(md5sum | cut -d' ' -f1 > "$md5f") |
       rclone rcat "$dst/$nome" $OPTS && [ "${PIPESTATUS[0]}" = 0 ]; then
    sleep 2
    local remoto; remoto=$(rclone md5sum "$dst" --include "/$nome" 2>/dev/null | cut -d' ' -f1)
    if [ -n "$remoto" ] && [ "$remoto" = "$(cat "$md5f")" ]; then
      docker rmi $tags >/dev/null && echo "$(date '+%F %T') OK, conferido (md5 $remoto) e removida: $(echo $tags)"
    else
      echo "$(date '+%F %T') FALHOU md5 (imagem mantida): $(echo $tags) local=$(cat "$md5f") drive=$remoto"
    fi
  else
    echo "$(date '+%F %T') FALHOU envio (imagem mantida): $(echo $tags)"
  fi
}

mover() {
  local src=$1 dst=$REMOTO/$2
  case $src in imagem:*) mover_imagem "${src#imagem:}" "$dst"; return;; esac
  [ -e "$src" ] || { echo "$(date '+%F %T') pulado (nao existe): $src"; return 0; }
  local tam; tam=$(du -sh "$src" | cut -f1)
  echo "$(date '+%F %T') enviando $src ($tam) -> $dst"
  if [ -d "$src" ]; then
    # pasta vira 1 arquivo .tar.gz enviado direto (o Drive cria so ~2 arquivos/s; milhares de arquivos levariam horas).
    # Conferencia: md5 do que o tar gerou == md5 que o Drive guardou, e o tar terminou sem erro.
    local nome; nome=$(basename "$src").tar.gz
    local md5f=/run/mover_drive.md5
    rclone deletefile "$dst/$nome" --log-level ERROR 2>/dev/null
    if tar -C "$(dirname "$src")" -cf - "$(basename "$src")" | pigz -1 | tee >(md5sum | cut -d' ' -f1 > "$md5f") |
         rclone rcat "$dst/$nome" $OPTS && [ "${PIPESTATUS[0]}" = 0 ]; then
      sleep 2
      local remoto; remoto=$(rclone md5sum "$dst" --include "/$nome" 2>/dev/null | cut -d' ' -f1)
      if [ -n "$remoto" ] && [ "$remoto" = "$(cat "$md5f")" ]; then
        rm -rf "$src"; echo "$(date '+%F %T') OK, conferido (md5 $remoto) e apagado: $src -> $dst/$nome"
      else
        echo "$(date '+%F %T') FALHOU md5 (local mantido): $src local=$(cat "$md5f") drive=$remoto"
      fi
    else
      echo "$(date '+%F %T') FALHOU envio (local mantido): $src"
    fi
  else
    rclone copyto "$src" "$dst/$(basename "$src")" $OPTS &&
    rclone check "$(dirname "$src")" "$dst" --one-way --include "/$(basename "$src")" --log-level ERROR &&
    { rm -f "$src"; echo "$(date '+%F %T') OK, conferido e apagado: $src"; } ||
    echo "$(date '+%F %T') FALHOU (local mantido): $src"
  fi
}

# ate 5 tentativas por item, esperando 1, 2, 3, 4 min (a rede da 157 oscila e o client_id compartilhado do rclone
# bate no limite por minuto do Drive: "403 rateLimitExceeded ... Requests per minute", 29/10)
while [ $# -ge 2 ]; do
  for t in 1 2 3 4 5; do
    mover "$1" "$2" >>"$LOG" 2>&1
    existe "$1" || break
    [ $t -lt 5 ] && sleep $((60 * t))
  done
  shift 2
done
