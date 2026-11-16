"""postar_animes_ate_bloquear.py — Posta TODOS os pendentes de animes enquanto canais aceitam."""
import json, os, sys, subprocess
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CANAIS = [
    "repost canalanimescomia",
    "YouTube inovaremanhwaverseesp",
]
ROOT = Path(r'D:\recapd-ambientes\producao')
LOG = ROOT / 'logs/videos_postados.json'
POSTER = r'D:\recapd-ambientes\producao\venv\Scripts\python.exe'
YOUTUBE = str(Path(__file__).resolve().parent / "youtube_poster.py")

def carregar_postados():
    if LOG.exists(): return set(json.load(open(LOG, encoding='utf-8')))
    return set()
def salvar_postado(p):
    s = carregar_postados(); s.add(str(p))
    LOG.parent.mkdir(parents=True, exist_ok=True)
    json.dump(sorted(s), open(LOG, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    arquivar(p)
def arquivar(video_path):
    import shutil
    p = str(video_path)
    try:
        rel = Path(p).relative_to(ROOT)
    except ValueError:
        return
    dest = ROOT / 'postados' / 'anime' / Path(*rel.parts[1:])
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        try: Path(p).unlink()
        except: pass
    else:
        try: shutil.move(p, str(dest))
        except: pass
def is_quota_err(out, err):
    text = (out or '') + (err or '')
    return any(k in text for k in ['uploadLimitExceeded', 'rateLimitExceeded', 'quotaExceeded'])
def listar_prontos():
    return list((ROOT / 'workspace/anime').rglob('final_anime_short.mp4'))
def postar(video_path, canal):
    folder_name = video_path.parent.name
    nome = folder_name.split("_", 1)[-1].replace("_", " ").strip()
    if len(nome) < 5: nome = "Resumo Animado"
    if len(nome) > 60: nome = nome[:60] + '..'
    titulo = f"{nome} #shorts #anime"
    tags = "anime,resumo,recap,otaku,animação,ia"
    cmd = [POSTER, YOUTUBE, '--video', str(video_path), '--titulo', titulo,
           '--descricao', f"Inscreva-se para mais resumos de animes! #shorts #{tags.replace(',', ' #')}",
           '--tags', tags, '--canal', canal]
    env = os.environ.copy(); env['PYTHONUTF8'] = '1'
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=180)

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
    sucessos = 0; falhas = 0
    limite_atingido = False
    canais_bloqueados = set()
    for i, video in enumerate(pendentes):
        tentativa_canal = None
        for ci in range(len(CANAIS)):
            canal = CANAIS[(idx + ci) % len(CANAIS)]
            if canal in canais_bloqueados: continue
            tentativa_canal = canal; break
        if not tentativa_canal:
            print(f"Todos os canais bloqueados. Saindo."); break
        print(f"\n[{i+1}/{len(pendentes)}] {video.name} -> {tentativa_canal}")
        try:
            proc = postar(video, tentativa_canal)
        except Exception as e:
            print(f"   EXCECAO: {e}"); falhas += 1; continue
        out = proc.stdout or ''; err = proc.stderr or ''
        if proc.returncode == 0 and ('Video id' in out or 'youtu.be' in out):
            print(f"   OK: {out.strip()[:120]}")
            salvar_postado(video); sucessos += 1; idx += 1
        elif is_quota_err(out, err):
            print(f"   LIMITE em '{tentativa_canal}'.")
            canais_bloqueados.add(tentativa_canal)
            if len(canais_bloqueados) >= len(CANAIS):
                print("   Todos bloqueados. Saindo."); limite_atingido = True; break
            prox = None
            for ci in range(len(CANAIS)):
                canal = CANAIS[(idx + ci) % len(CANAIS)]
                if canal not in canais_bloqueados: prox = canal; break
            if not prox: print("   Sem backup."); limite_atingido = True; break
            print(f"   Backup: {prox}")
            try:
                proc2 = postar(video, prox)
                out2 = proc2.stdout or ''; err2 = proc2.stderr or ''
                if proc2.returncode == 0 and ('Video id' in out2 or 'youtu.be' in out2):
                    print(f"   OK (backup): {out2.strip()[:120]}")
                    salvar_postado(video); sucessos += 1; idx += 1
                elif is_quota_err(out2, err2):
                    print("   Backup tambem bloqueado. Pulando."); falhas += 1
                    canais_bloqueados.add(prox)
                    if len(canais_bloqueados) >= len(CANAIS):
                        print("   Todos bloqueados."); limite_atingido = True; break
                else:
                    print(f"   ERRO backup: {err2.strip()[:200]}"); falhas += 1
            except Exception as e:
                print(f"   EXC backup: {e}"); falhas += 1
        else:
            print(f"   ERRO: {(err or out).strip()[:200]}"); falhas += 1
    print(f"\n=== RESUMO ===")
    print(f"Sucessos: {sucessos}")
    print(f"Falhas: {falhas}")
    print(f"Limite atingido: {limite_atingido}")
    print(f"Canais bloqueados: {sorted(canais_bloqueados)}")

if __name__ == '__main__':
    main()
