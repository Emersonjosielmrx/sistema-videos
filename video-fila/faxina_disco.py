"""faxina_disco.py — libera espaço SEM perder nada que precise de login (dona 23/10/2026: "não pode remover nenhum
perfil; pode remover os caches do disco C, mas sem precisar logar de novo; pode deixar automático; os arquivos do
Claude só os com mais de 7 dias").

  1. Chrome normal (C:) e perfis do cofre (D:): SÓ as pastas de cache (lista cofre.CACHE). Cookies, Login Data,
     Local State e Preferences nunca. Perfil aberto: o rename da pasta de cache falha e ele é pulado (fica pra próxima).
  2. %LOCALAPPDATA%\\Temp: arquivos com mais de 3 dias, fora de Temp\\claude.
  3. %LOCALAPPDATA%\\Temp\\claude: só os com mais de 7 dias.
  4. Cache do uv (C: e D:\\hipercool-materiais\\python\\uv_cache).
  5. Vozes RVC paradas (.index) e fontes do anime já usadas -> Drive (hipercool-materiais\\bin\\vozes_drive.py e
     fontes_drive.py); voltam sozinhas na hora do uso (voz_clonada/kaggle_conversor e anime_fetch.download_video).
  6. (02/11) Upscale 1080p que morreu no meio (*.tmp.mp4 parado há 6 h): o politica.garantir_1080 refaz do zero.
  7. (02/11) Testes vencidos do registro testes.py (lista em TESTES_TEMPORARIOS.md): todo chat registra o que testa.
  8. (02/11) Prints do postador do YouTube (logs\\yt_web) > 7 dias; sobras do produto_tmp > 3 dias; cache de sombras
     da placa Intel; instaladores velhos do Google Updater (crx_cache > 3 dias); Chromium do Playwright que nenhum
     Python instalado usa mais (pergunta a cada Python qual versão ele usa antes de apagar).
  O cache do Chrome inclui (02/11) o banco de uploads do YouTube Studio (1,7 GB num perfil) — login fica nos Cookies.

    python faxina_disco.py            # faz e mostra quanto liberou
    python faxina_disco.py --simular  # só mede
O vigia geral chama 1x por dia (SUBVIGIAS "faxina_disco", 4 h).
"""
import os
import shutil
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402

TEMP = Path(os.path.expandvars(r"%LOCALAPPDATA%\Temp"))
CHROME_UD = Path(os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"))
UV_CACHES = [None, r"D:\hipercool-materiais\python\uv_cache"]  # None = o padrão do uv (C:)
LOG = Path(__file__).resolve().parent / "logs" / "faxina_disco.log"
VEO_TMP = Path(r"D:\veo\beta\pos_producao\tmp")
# 02/11: onde o upscale 1080p (postador politica.garantir_1080) deixa <nome>_1080p.tmp.mp4 quando morre no meio
TMP_UPSCALE = [Path(r"D:\hipercool-materiais"), Path(r"D:\recapd-ambientes\producao\workspace"),
               Path(r"D:\manhwa-react"), Path(r"D:\video-fila\linhas"), Path(r"D:\postador-de-videos")]
# 02/11 (dona): (pasta, dias) que só têm sobra/registro — o que passou da idade sai sozinho
VELHOS_EXTRA = [(Path(r"D:\postador-de-videos\logs\yt_web"), 7),  # prints de cada postagem no Studio
                (Path(r"D:\video-fila\produto_tmp"), 3),  # montagem dos vídeos de produto
                # 12/11 (disco em 7 GB segurava 6 longos): cópia baixada do Drive só para postar; o catalogo.liberar
                # apaga, mas quando a postagem cai no meio ela fica (6,8 GB, 138 com mais de 2 dias). Baixa de novo.
                # 14/11 (disco 11 GB, cache voltou a 2,3 GB em 1 dia): 2 -> 1 dia. FAXINA_REUSO_DIAS muda.
                (Path(r"D:\postador-de-videos\cache_reuso"), float(os.environ.get("FAXINA_REUSO_DIAS", "1"))),
                (Path(os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\Intel\ShaderCache")), 0),  # driver refaz
                (Path(r"C:\Program Files (x86)\Google\GoogleUpdater\crx_cache"), 3)]  # instalador já aplicado
PLAYWRIGHT = Path(os.path.expandvars(r"%LOCALAPPDATA%\ms-playwright"))  # junção pra D:\caches\ms-playwright
PYTHONS = [r"D:\veo\venv\Scripts\python.exe",
           r"D:\hipercool-materiais\python\venv_vozes\Scripts\python.exe",
           r"D:\veo\venv\Scripts\python.exe",
           os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python313\python.exe")]


def playwright_sem_uso(simular):
    """Apaga chromium-NNNN / chromium_headless_shell-NNNN que nenhum Python instalado usa. Se algum Python não
    responder, não apaga nada (melhor sobrar que quebrar o postador)."""
    usados = set()
    codigo = ("from playwright.sync_api import sync_playwright as s\n"
              "with s() as p: print(p.chromium.executable_path)")
    for py in PYTHONS:
        if not os.path.exists(py):
            continue
        try:
            r = subprocess.run([py, "-c", codigo], capture_output=True, text=True, timeout=120,
                               creationflags=0x08000000)
        except Exception:  # noqa: BLE001
            return 0
        if r.returncode != 0:
            if "No module named" in (r.stderr or ""):
                continue  # esse Python não tem playwright
            return 0
        for parte in Path(r.stdout.strip()).parts:
            if parte.startswith("chromium"):
                usados.add(parte.split("-")[-1])
    if not usados or not PLAYWRIGHT.is_dir():
        return 0
    liberado = 0
    for d in PLAYWRIGHT.iterdir():
        if d.is_dir() and d.name.startswith("chromium") and "-" in d.name and d.name.split("-")[-1] not in usados:
            liberado += _tam(d)
            if not simular:
                shutil.rmtree(d, ignore_errors=True)
    return liberado
ORPHAN_PATHS = [
    Path(r"C:\recapd-e-animes\saida"),
    Path(r"D:\recapd-e-animes\saida"),  # caso exista no D: também
]


def log(m):
    linha = f"[{time.strftime('%d/%m %H:%M:%S')}] {m}"
    print(linha, flush=True)
    try:
        LOG.parent.mkdir(exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def _tam(p):
    t = 0
    for r, _d, a in os.walk(p, onerror=lambda e: None):
        for x in a:
            try:
                t += os.path.getsize(os.path.join(r, x))
            except OSError:
                pass
    return t


def cache_chrome(raiz, simular):
    """Só pastas de cache de cada perfil em `raiz` (User Data do Chrome). Pula perfil aberto."""
    liberado, pulados = 0, 0
    if not raiz.is_dir():
        return 0, 0
    for prof in raiz.iterdir():
        if not (prof / "Preferences").is_file():
            continue
        for c in cofre.CACHE:
            p = prof / c
            if not p.is_dir():
                continue
            if simular:
                liberado += _tam(p)
                continue
            tmp = p.with_name(p.name + "._apagar")
            try:
                os.rename(p, tmp)  # Chrome com o perfil aberto segura a pasta: falha -> pula
            except OSError:
                pulados += 1
                continue
            liberado += _tam(tmp)
            shutil.rmtree(tmp, ignore_errors=True)
    return liberado, pulados


def velhos(raiz, dias, pular=None, simular=False):
    lim, liberado = time.time() - dias * 86400, 0
    for r, _d, a in os.walk(raiz, topdown=False, onerror=lambda e: None):
        if pular and pular in r.lower():
            continue
        for x in a:
            p = os.path.join(r, x)
            try:
                if os.path.getmtime(p) < lim:
                    s = os.path.getsize(p)
                    if not simular:
                        os.remove(p)
                    liberado += s
            except OSError:
                pass
        if not simular and r != str(raiz):
            try:
                os.rmdir(r)  # só some se ficou vazia
            except OSError:
                pass
    return liberado


def upscale_de_postados(simular=False):
    r"""12/11: animes recap\shorts\<pasta>\video_1080p.mp4 de Short JÁ POSTADO cujo video.mp4 já foi pro Drive
    (mover_shorts_postados deixa _NO_DRIVE.txt). É a cópia ampliada (politica.garantir_1080 refaz do original se um
    dia precisar): 148 arquivos = 4,5 GB parados. Só sai com mais de 2 dias. FAXINA_1080_POSTADOS=0 desliga."""
    if os.environ.get("FAXINA_1080_POSTADOS", "1") == "0":
        return 0
    sys.path.append(r"D:\hipercool-materiais\comum")
    import mover_shorts_postados as msp
    ja, lim, total = msp.postados(), time.time() - 2 * 86400, 0
    for p in msp.BASE.iterdir():
        f = p / "video_1080p.mp4"
        if (p.is_dir() and p.name.lower() in ja and f.exists() and not (p / "video.mp4").exists()
                and ((p / "_NO_DRIVE.txt").exists() or (p / "_NO_DRIVE.md").exists()) and f.stat().st_mtime < lim):
            tam = f.stat().st_size
            if not simular:
                try:
                    f.unlink()
                except OSError:
                    continue
            total += tam
    return total


def longos_que_falharam(simular=False, horas=6):
    r"""15/11 (disco foi a 1,7 GB): longo cujo ENVIO falhou deixa o vídeo de 4-8 GB em DOIS lugares — o
    _longos_postar\<ficha>\final_anime_deitado.mp4 e a pasta de postagem animes recap\videos laterais\<x>\video.mp4 —
    e são o MESMO arquivo (link físico): apagar só um não libera nada. Pasta de postagem de longo com vídeo > 1 GB,
    NÃO postada (sem posted_url e fora do uploads_ledger), parada há > `horas` e sem envio rodando = o vídeo sai dos
    dois lugares (o original segue no Drive; o postar_longos baixa de novo na vez). FAXINA_LONGOS_FALHOS=0 desliga."""
    if os.environ.get("FAXINA_LONGOS_FALHOS", "1") == "0":
        return 0
    lat = Path(r"D:\hipercool-materiais\animes recap\videos laterais")
    postar = Path(r"D:\hipercool-materiais\_longos_postar")
    try:
        ledger = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl").read_text("utf-8", "replace")
    except OSError:
        return 0
    try:
        enviando = subprocess.run(["powershell", "-NoProfile", "-c",
                                   "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
                                   "? CommandLine -match 'youtube_web_poster' | % CommandLine"],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                                  creationflags=0x08000000).stdout
    except Exception:  # noqa: BLE001
        return 0  # sem saber o que está subindo, não apaga nada
    if enviando is None:
        return 0
    lim, total = time.time() - horas * 3600, 0
    for v in lat.glob("*/video.mp4"):
        try:
            st = v.stat()
            if st.st_size < 1e9 or st.st_mtime > lim or v.parent.name in ledger or str(v.parent) in enviando:
                continue
            # mesmo arquivo (link físico) usado por um envio que roda com OUTRA pasta = pula
            usados = [Path(m) for m in re.findall(r'--video "([^"]+)"', enviando)]
            if any(u.exists() and u.stat().st_size == st.st_size and abs(u.stat().st_mtime - st.st_mtime) < 5
                   for u in usados):
                continue
            d = json.loads((v.parent / "postar.json").read_text("utf-8"))
            if d.get("posted_url") or d.get("tipo") != "completo":
                continue
        except (OSError, ValueError):
            continue
        irmaos = [f for f in postar.glob("*/final_anime_deitado.mp4") if f.stat().st_size == st.st_size
                  and abs(f.stat().st_mtime - st.st_mtime) < 5 and str(f.parent.name) not in enviando]
        if not simular:
            for f in [v, *irmaos]:
                try:
                    f.unlink()
                except OSError:
                    pass
        total += st.st_size
        log(f"longo que falhou: {v.parent.name} ({st.st_size / 1e9:.1f} GB, +{len(irmaos)} cópia(s) ligada(s))")
    return total


def main(simular=False):
    total = 0
    l = longos_que_falharam(simular)
    log(f"longos com envio falho (vídeo preso em 2 lugares): {l / 1e9:.1f} GB")
    total += l
    l, pul = cache_chrome(CHROME_UD, simular)
    log(f"cache do Chrome normal: {l / 1e9:.1f} GB ({pul} pasta(s) de perfil aberto puladas)")
    total += l
    l = 0
    if not simular:  # cofre.limpar_pasta: só cache, pula perfil aberto, devolve MB
        for d in (cofre.PERFIS.iterdir() if cofre.PERFIS.is_dir() else []):
            if d.is_dir():
                l += cofre.limpar_pasta(d) * 1e6
    log(f"cache dos perfis do cofre: {l / 1e9:.1f} GB")
    total += l
    l = velhos(TEMP, 3, pular="\\claude", simular=simular)
    log(f"Temp (> 3 dias, fora do Claude): {l / 1e9:.1f} GB")
    total += l
    l = velhos(TEMP / "claude", 7, simular=simular) if (TEMP / "claude").is_dir() else 0
    log(f"Temp do Claude (> 7 dias): {l / 1e9:.1f} GB")
    total += l
    # 23/10: pasta temporária da montagem do Veo (4,3 GB, sobras de render) — só o que tem mais de 7 dias
    l = velhos(VEO_TMP, 7, simular=simular) if VEO_TMP.is_dir() else 0
    log(f"tmp da pós-produção do Veo (> 7 dias): {l / 1e9:.1f} GB")
    total += l
    if not simular:
        for d in UV_CACHES:
            env = dict(os.environ, **({"UV_CACHE_DIR": d} if d else {}))
            try:
                r = subprocess.run(["uv", "cache", "clean"], env=env, capture_output=True, text=True, timeout=600,
                                   creationflags=0x08000000)
                log(f"cache do uv {d or '(C:)'}: {(r.stderr or r.stdout).strip().splitlines()[-1][:120]}")
            except Exception as e:  # noqa: BLE001
                log(f"cache do uv {d or '(C:)'}: {type(e).__name__}")
    # 02/11 (dona): upscale que morreu no meio (2,8 GB em 2 arquivos) — parado há 6 h não está mais sendo escrito
    l = 0
    for raiz in TMP_UPSCALE:
        for r, ds, fs in os.walk(raiz, onerror=lambda e: None):
            ds[:] = [d for d in ds if d not in ("venv", ".venv", "node_modules", ".git", "python", "models")]
            for x in fs:
                if not x.endswith(".tmp.mp4"):
                    continue
                p = os.path.join(r, x)
                try:
                    if time.time() - os.path.getmtime(p) > 6 * 3600:
                        s = os.path.getsize(p)
                        if not simular:
                            os.remove(p)
                        l += s
                except OSError:
                    pass
    log(f"upscale 1080p pela metade (*.tmp.mp4 > 6 h): {l / 1e9:.1f} GB")
    total += l
    try:
        l = upscale_de_postados(simular)
        log(f"1080p de Short já postado (original no Drive, > 2 dias): {l / 1e9:.1f} GB")
        total += l
    except Exception as e:  # noqa: BLE001
        log(f"upscale_de_postados: {type(e).__name__}: {e}")
    for pasta, dias in VELHOS_EXTRA:
        l = velhos(pasta, dias, simular=simular) if pasta.is_dir() else 0
        log(f"{pasta} (> {dias} dias): {l / 1e9:.1f} GB")
        total += l
    try:
        l = playwright_sem_uso(simular)
        log(f"Chromium do Playwright sem uso: {l / 1e9:.1f} GB")
        total += l
    except Exception as e:  # noqa: BLE001
        log(f"playwright: {type(e).__name__}: {e}")
    # 02/11 (dona): testes registrados que venceram (testes.py; lista em TESTES_TEMPORARIOS.md)
    try:
        import testes
        total += testes.limpar(simular, log=log)
    except Exception as e:  # noqa: BLE001
        log(f"testes: {type(e).__name__}: {e}")
    # Pastas orphan_ com mais de 2 dias (vídeos que falharam ou já foram postados)
    for raiz in ORPHAN_PATHS:
        if not raiz.is_dir():
            continue
        for p in raiz.glob("orphan_*"):
            if not p.is_dir():
                continue
            try:
                if time.time() - p.stat().st_mtime > 2 * 86400:  # > 2 dias
                    tam = _tam(p) if simular else 0
                    if not simular:
                        shutil.rmtree(p, ignore_errors=True)
                        tam = _tam(p) if p.exists() else tam  # recalcula se não removeu tudo
                    if tam > 0:
                        log(f"orphan {p.name}: {tam / 1e9:.1f} GB")
                        total += tam
            except Exception as e:  # noqa: BLE001
                log(f"orphan {p.name}: {type(e).__name__}")
    livre = {u: shutil.disk_usage(u).free / 1e9 for u in ("C:\\", "D:\\")}
    log(f"TOTAL {'(simulado) ' if simular else ''}{total / 1e9:.1f} GB | livre agora: C: {livre['C:\\']:.1f} GB, "
        f"D: {livre['D:\\']:.1f} GB")
    # 25/11 (levantamento disco-arquivos): as subidas ao Drive (vozes/fontes/amostras/mapa; 76 min de timeout em
    # 23/11) vinham ANTES das limpezas locais e a faxina não chegava ao fim desde 22/11 (cache_reuso com vídeos de
    # 04/11). Agora: limpezas locais primeiro, TOTAL, e as subidas por último.
    # 23/10 (dona): vozes RVC paradas (.index) e fontes do anime já usadas vão pro Drive; voltam sozinhas quando usadas
    if r"D:\hipercool-materiais\bin" not in sys.path:
        sys.path.append(r"D:\hipercool-materiais\bin")
    # 25/10 (dona): + sobras de treino/teste de voz (amostras_drive); tudo anotado no _NO_DRIVE.md de cada pasta
    for nome in ("vozes_drive", "fontes_drive", "amostras_drive"):
        try:
            mod = __import__(nome)
            (mod.subir_paradas if nome == "vozes_drive" else mod.subir)(simular)
        except Exception as e:  # noqa: BLE001
            log(f"{nome}: {type(e).__name__}: {e}")
    if not simular:  # 23/10 (dona): mapa do Drive atualizado pra achar e pegar algo à mão (MAPA_DRIVE.md)
        try:
            import mapa_drive
            mapa_drive.main()
        except Exception as e:  # noqa: BLE001
            log(f"mapa_drive: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main("--simular" in sys.argv)
