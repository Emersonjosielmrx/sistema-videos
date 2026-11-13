# -*- coding: utf-8 -*-
"""Health-check da producao autonoma. Roda via cron a cada 30min.
Verifica: (1) loop vivo? (2) gerou video recente? (3) status das contas.
Escreve resultado em logs/_monitor.log e, se travado, tenta relancar."""
import os, sys, time, json, subprocess, glob
import psutil

BASE = r'D:\veo\beta'
LOG = os.path.join(BASE, 'logs', '_monitor.log')
PROD_BAT = os.path.join(BASE, '_producao_10h.bat')
VIDEOS = os.path.join(BASE, 'videos')

def log(msg):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def loop_vivo():
    """True se ha um cmd.exe rodando _producao_10h.bat."""
    for p in psutil.process_iter(['name', 'cmdline']):
        try:
            if (p.info['name'] or '').lower() == 'cmd.exe':
                cl = ' '.join(p.info['cmdline'] or [])
                if '_producao_10h' in cl:
                    return True
        except Exception:
            pass
    return False

def cron_vivo():
    for p in psutil.process_iter(['name', 'cmdline']):
        try:
            args = p.info['cmdline'] or []
            if (p.info['name'] or '').lower() == 'python.exe' and '-c' not in args:
                if any(a.endswith('cron_gerar_video_llm.py') for a in args):
                    return True
        except Exception:
            pass
    return False

def ultimo_video_min():
    """Minutos desde o ultimo mp4 gerado."""
    mp4s = glob.glob(os.path.join(VIDEOS, '**', '*.mp4'), recursive=True)
    if not mp4s:
        return None
    novo = max(os.path.getmtime(f) for f in mp4s)
    return (time.time() - novo) / 60.0

def contas_status():
    fp = os.path.join(BASE, 'logs', 'sessoes_status.json')
    try:
        with open(fp, encoding='utf-8') as f:
            data = json.load(f)
        out = {}
        for k, v in data.items():
            out[k] = v.get('status', 'ativa')
        return out
    except Exception:
        return {}

def relancar():
    log('!! loop MORTO — relancando producao')
    # FIX 2026-07-27: 'start' e comando interno do cmd.exe — quando Python passa
    # como argv, Windows tenta executar start.exe ("Acesso negado"). E quando vai
    # via 'cmd /c start ...' sem shell=True, o start congela (nao retorna).
    # Solucao confiavel testada (veja logs/_monitor.log de 2026-07-27 10:44:47):
    # chamar o BAT direto com shell=True via Popen (nao-bloqueante). O bat ja
    # cuida de subir suas sub-janelas internamente.
    try:
        subprocess.Popen(PROD_BAT, cwd=BASE, shell=True,
                         creationflags=subprocess.DETACHED_PROCESS
                                      | subprocess.CREATE_NEW_PROCESS_GROUP)
        log('   relancado via Popen(bat, shell=True, detached)')
    except Exception as e:
        log(f'   FALHA: {e}')

def main():
    lv = loop_vivo()
    cv = cron_vivo()
    umin = ultimo_video_min()
    st = contas_status()
    exhausted = [k for k, v in st.items() if v == 'EXHAUSTED']
    ativas = [k for k, v in st.items() if v != 'EXHAUSTED']

    umin_s = f'{umin:.0f}min' if umin is not None else 'nunca'
    log(f'loop={"VIVO" if lv else "MORTO"} cron={"sim" if cv else "nao"} '
        f'ultimo_video={umin_s} ativas={ativas} exhausted={exhausted}')

    # regra: se TODAS exhausted, producao acabou (nao relancar)
    if st and not ativas:
        log('=> TODAS as contas EXHAUSTED. Producao concluida (creditos zerados).')
        return

    # se loop morto mas ainda ha conta com credito -> relancar
    if not lv and (not st or ativas):
        relancar()
        return

    # se loop vivo mas nenhum video ha >40min e cron nao esta rodando -> pode ter travado
    if lv and not cv and umin is not None and umin > 40:
        log('=> loop vivo mas cron parado e sem video ha >40min (possivel trava, observar)')

if __name__ == '__main__':
    main()
