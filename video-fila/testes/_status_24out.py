import sys
sys.path.insert(0, r"D:\video-fila")
import melhoria_continua as mc
import auditoria_final as af
c, e = mc.cfg(), mc._estado()
print("ligado:", c.get("ligado"), "| opus_camada:", c.get("opus_camada"), "| multiagente:", c.get("multiagente"))
print("atual:", e.get("atual"))
print(af.status_txt(e, c))
