import sys, re
with open("D:/recapd-ambientes/producao/bin/fx_clips.py", "r", encoding="utf-8") as f:
    code = f.read()
    
# Verificando se existe as configs de Native/Reframe que haviamos planejado
if "native" in code:
    print("Possui branch de NATIVE/REFRAME")
else:
    print("Nao possui native/reframe!")
