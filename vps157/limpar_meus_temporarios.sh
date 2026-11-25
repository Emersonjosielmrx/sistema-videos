#!/bin/bash
# 23/11: apaga SO os scripts temporarios de diagnostico criados por este chat na VPS (nomes exatos, sem curinga).
cd /opt/omniroute || exit 1
for f in omni_diagnostico.sh omni_kiro_neon.py omni_lentidao_opus.sh omni_modelos_contas.py omni_modelos_saude.py \
         omni_neon_kiro2.py omni_pendencias.sh omni_plano_conserto.py omni_verificar.py vigia_pressao_patch.py \
         sonnet_fila_so_web.py haiku_fila_conserto.py omni_diag_reinicio.sh; do
  [ -f "$f" ] && rm -f -- "$f" && echo "apagado $f"
done
for f in /root/omni_inspecionar_tabelas.sh /tmp/levantamento.sh; do
  [ -f "$f" ] && rm -f -- "$f" && echo "apagado $f"
done
rm -rf -- /opt/omniroute/__pycache__ 2>/dev/null
echo "fica: omni_limpeza_historico.py (limpeza, reutilizavel), cw_pausa_429.py, vigia_disjuntor_cc.py, ag55_guarda.py"
