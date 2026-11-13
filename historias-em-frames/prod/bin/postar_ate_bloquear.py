"""postar_ate_bloquear.py — Posta TODOS os pendentes enquanto os canais aceitam.

Para cada vídeo pendente:
  1. Tenta canal[idx % len(CANAIS)]
  2. Se limite, tenta canal[(idx+1) % len(CANAIS)]
  3. Se ambos negados, sai do loop (cota diária esgotada)
  4. Se sucesso, marca no log e segue pro próximo
"""
import json, os, sys, subprocess, time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CANAIS = [
    "raiz3 emersonjosielmrx1995(curiosidade",
    "raiz fabricadeautomacoes0(ia pro",
]
ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / 'logs/videos_postados.json'
# venv e poster da PROPRIA pista (sem depender de outro projeto)
_local_py = ROOT / 'venv' / 'Scripts' / 'python.exe'
POSTER = str(_local_py) if _local_py.exists() else sys.executable
YOUTUBE = str(ROOT / 'bin' / 'youtube_poster.py')

def carregar_postados():
    if LOG.exists():
        return set(json.load(open(LOG, encoding='utf-8')))
    return set()

def arquivar(video_path):
    """Move o vídeo recém-postado pra <raiz>/postados/<categoria>/... pra não misturar com originais."""
    import shutil
    p = str(video_path)
    try:
        rel = Path(p).relative_to(ROOT)
    except ValueError:
        return
    parts = rel.parts
    cats = ['terror', 'misterio', 'comedia', 'romance', 'drama',
            'superacao', 'motivacional', 'religioso', 'fantasia']
    cat = next((c for c in cats if c in parts), 'outros')
    try:
        idx = parts.index(cat)
        sufixo = Path(*parts[idx+1:])
    except ValueError:
        sufixo = Path(p).name
    dest = ROOT / 'postados' / cat / sufixo
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        try: Path(p).unlink()
        except: pass
    else:
        try: shutil.move(p, str(dest))
        except: pass

def salvar_postado(p):
    s = carregar_postados()
    s.add(str(p))
    LOG.parent.mkdir(parents=True, exist_ok=True)
    json.dump(sorted(s), open(LOG, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    arquivar(p)

def is_quota_err(out, err):
    text = (out or '') + (err or '')
    return any(k in text for k in ['uploadLimitExceeded', 'rateLimitExceeded', 'quotaExceeded'])

def listar_prontos():
    P = ROOT / 'workspace/videos'
    r = []
    for pat in ['*_FINAL_ULTIMO.mp4', '*_APROVADO_*.mp4']:
        for p in P.rglob(pat):
            s = str(p).lower()
            if '_quarantine' in s or '_quarentena' in s: continue
            r.append(p)
    return r

def postar(video_path, canal):
    texto = video_path.stem
    if 'superacao' in str(video_path).lower():
        tags = 'história,superação,motivação,ia,animação'
        titulo = f"{texto.replace('_', ' ')} - Superação Incrível #shorts"
    else:
        tags = 'terror,assustador,história,ia,creepypasta'
        titulo = f"{texto.replace('_', ' ')} - Terror Perturbadora #shorts"

    cmd = [POSTER, YOUTUBE, '--video', str(video_path), '--titulo', titulo,
           '--descricao', f"Inscreva-se! #shorts #{tags.replace(',', ' #')}",
           '--tags', tags, '--canal', canal]
    env = os.environ.copy(); env['PYTHONUTF8'] = '1'
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=180)
    return proc

def main():
    postados = carregar_postados()
    prontos = listar_prontos()
    pendentes = [p for p in prontos if str(p) not in postados]
    pendentes.sort(key=str)
    print(f"Total prontos: {len(prontos)} | ja postados: {len(postados)} | pendentes: {len(pendentes)}")
    if not pendentes:
        print("Nada a postar.")
        return

    idx = 0
    sucessos = 0
    falhas = 0
    limite_atingido = False
    canais_bloqueados = set()

    for i, video in enumerate(pendentes):
        # tenta cada canal, parando se todos estiverem bloqueados
        tentativa_canal = None
        for ci in range(len(CANAIS)):
            canal = CANAIS[(idx + ci) % len(CANAIS)]
            if canal in canais_bloqueados: continue
            tentativa_canal = canal
            break
        if not tentativa_canal:
            print(f"Todos os canais ja marcados como bloqueados nesta rodada. Saindo.")
            break

        print(f"\n[{i+1}/{len(pendentes)}] {video.name} -> {tentativa_canal}")
        try:
            proc = postar(video, tentativa_canal)
        except Exception as e:
            print(f"   EXCECAO: {e}")
            falhas += 1
            continue
        out = proc.stdout or ''
        err = proc.stderr or ''
        if proc.returncode == 0 and ('Video id' in out or 'Upload resumable concluido' in out or 'youtu.be' in out):
            print(f"   OK: {out.strip()[:120]}")
            salvar_postado(video)
            sucessos += 1
            idx += 1
        elif is_quota_err(out, err):
            print(f"   LIMITE no canal '{tentativa_canal}'. Marcando bloqueado.")
            canais_bloqueados.add(tentativa_canal)
            if len(canais_bloqueados) >= len(CANAIS):
                print("   Todos os canais com cota esgotada. Saindo.")
                limite_atingido = True
                break
            # tenta próximo canal pra esse mesmo video
            prox = None
            for ci in range(len(CANAIS)):
                canal = CANAIS[(idx + ci) % len(CANAIS)]
                if canal not in canais_bloqueados:
                    prox = canal; break
            if not prox:
                print("   Sem mais canais disponiveis. Saindo.")
                limite_atingido = True
                break
            print(f"   Tentando canal backup: {prox}")
            try:
                proc2 = postar(video, prox)
                out2 = proc2.stdout or ''; err2 = proc2.stderr or ''
                if proc2.returncode == 0 and ('Video id' in out2 or 'youtu.be' in out2):
                    print(f"   OK (backup): {out2.strip()[:120]}")
                    salvar_postado(video)
                    sucessos += 1
                    idx += 1
                elif is_quota_err(out2, err2):
                    print(f"   LIMITE tambem no backup. Pulando video.")
                    canais_bloqueados.add(prox)
                    if len(canais_bloqueados) >= len(CANAIS):
                        print("   Todos bloqueados. Saindo.")
                        limite_atingido = True
                        break
                    falhas += 1
                else:
                    print(f"   ERRO backup: {err2.strip()[:200]}")
                    falhas += 1
            except Exception as e:
                print(f"   EXCECAO backup: {e}")
                falhas += 1
        else:
            print(f"   ERRO: {err.strip()[:200] or out.strip()[:200]}")
            falhas += 1

    print(f"\n=== RESUMO ===")
    print(f"Sucessos: {sucessos}")
    print(f"Falhas: {falhas}")
    print(f"Limite atingido: {limite_atingido}")
    print(f"Canais bloqueados: {sorted(canais_bloqueados)}")

if __name__ == '__main__':
    main()
