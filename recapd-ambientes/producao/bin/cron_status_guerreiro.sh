#!/bin/bash
echo "=== STATUS $(date) ===" >> /d/hipercool-inferior-fix/logs/cron_guerreiro.log
tail -n 20 /d/hipercool-inferior-fix/logs/rotina_rw_26_50.log >> /d/hipercool-inferior-fix/logs/cron_guerreiro.log
echo -e "\n\n" >> /d/hipercool-inferior-fix/logs/cron_guerreiro.log
