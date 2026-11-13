# Backup da Censura "Exodia Claro Luma" (Original Cru)

Neste arquivo documentamos a string exata de FFmpeg do **Exodia Cru** (sem o Vidro Fosco OpenCV).
Esse filtro foi testado e eleito como altamente destrutivo para IAs, porem com algumas imperfeicoes esteticas pros olhos humanos caso haja muito ruido. Estamos salvando pois é 100% blindado contra strikes.

## Comando FFmpeg Filter Complex (Nível 1 Antigo)

```text
[0:v]split=2[bg][fg];
[bg]negate,scale=iw/25:-1,scale=iw*25:-1:flags=neighbor,hue=s=0,noise=alls=60:allf=t+u,drawbox=x=0:y=0:w=iw:h=ih:color=white@0.7:t=fill[bg_tratado];
[fg]lumakey=threshold=0.85:tolerance=0.20:softness=0.10[baloes];
[bg_tratado][baloes]overlay
```

Se um dia quiser restaurar essa versao no pipeline, basta trocar no `censura_visual.py` do modo sutil.
