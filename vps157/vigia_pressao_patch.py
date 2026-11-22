#!/usr/bin/env python3
"""22/11: o vigia passa a reiniciar quando a guarda de heap do OmniRoute esta recusando pedidos (503 resource
pressure): nesse estado as recusas viram novas tentativas e nunca fica "calmo". Faz backup antes."""
import shutil

P = "/opt/omniroute/vigia_memoria.sh"
shutil.copy2(P, P + ".bak-antes-pressao-22nov")
s = open(P).read()
velho = 'if [ "$MB" -gt "$FORCAR_MB" ] || [ "$CONN" -le "$CALMO" ]; then'
novo = (
    '# 22/11: com a guarda de heap recusando (503 resource pressure) as recusas viram novas tentativas e nunca fica\n'
    '# calmo: se a guarda disparou mais de PRESSAO vezes em 2 min, ele ja nao atende -> reinicia (-t 40 deixa terminar)\n'
    'PRESSAO=20\n'
    'NP=$(docker logs --since 2m omniroute 2>&1 | grep -c "critical pressure guard tripped")\n'
    'if [ "$MB" -gt "$FORCAR_MB" ] || [ "$CONN" -le "$CALMO" ] || [ "$NP" -gt "$PRESSAO" ]; then'
)
assert s.count(velho) == 1, "linha do if nao encontrada"
s = s.replace(velho, novo)
s = s.replace('pedidos_3min ${CONN}: reiniciando omniroute', 'pedidos_3min ${CONN}, recusas_2min ${NP}: reiniciando omniroute')
open(P, "w").write(s)
print("ok")
