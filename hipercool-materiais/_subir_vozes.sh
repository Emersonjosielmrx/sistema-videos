#!/bin/bash
# 03/11: sobe as vozes que faltam no cache do Kaggle (colab_recap/vozes), mei_overwatch primeiro
cd /d/hipercool-materiais
for v in mei_overwatch $(grep -v "^mei_overwatch$" _vozes_faltam.txt); do
  /d/tools/rclone.exe copy "models/rvc/vozes/$v" "manhwa-drive:colab_recap/vozes/$v" --exclude .ultimo_uso --exclude "*.bkp*" --retries 3 --timeout 120s && echo "$(date +%H:%M) ok $v" || echo "$(date +%H:%M) FALHOU $v"
done >> _subir_vozes.log 2>&1
echo "$(date +%H:%M) FIM" >> _subir_vozes.log
