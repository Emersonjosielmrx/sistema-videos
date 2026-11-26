#!/data/data/com.termux/files/usr/bin/sh
# /mnt/win-bootcamp/claude-central/ronda/sonda_cel.sh - roda NO CELULAR (Termux). Somente leitura.
j=$(termux-battery-status 2>/dev/null | tr -d ' \n')
p=$(echo "$j" | sed -n 's/.*"percentage":\([0-9]*\).*/\1/p')
s=$(echo "$j" | sed -n 's/.*"status":"\([A-Z_]*\)".*/\1/p')
t=$(echo "$j" | sed -n 's/.*"temperature":\([0-9.]*\).*/\1/p')
a="ok | bateria ${p:-?}% $s | ${t:-?} C"
[ "$s" = "DISCHARGING" ] && [ "${p:-100}" -lt 40 ] && a="$a | !! BATERIA BAIXA FORA DA TOMADA"
echo "$a"
