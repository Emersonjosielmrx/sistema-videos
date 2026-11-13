#!/bin/bash
# Report de avanço rápido
LOG_FILE="/d/hipercool-inferior-fix/logs/rotina_rw_26_50.log"
REPORT_FILE="/d/hipercool-inferior-fix/workspace/STATUS_PROGRESSO_FILAS.md"
echo "### Status da fila 26 a 50 (Hora local: $(date))" > $REPORT_FILE
echo "- **Última ação**: " >> $REPORT_FILE
tail -n 2 $LOG_FILE >> $REPORT_FILE

echo "- **Caps iniciados**: " >> $REPORT_FILE
grep "CAPÍTULO" $LOG_FILE >> $REPORT_FILE

echo "- **Erros?**: " >> $REPORT_FILE
grep -i "falhou\|erro" $LOG_FILE | tail -n 5 >> $REPORT_FILE
