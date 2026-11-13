"""sonda_perfis_veo.py - abre cada perfil candidato (copias do veo) no Studio do canal e diz se o login esta vivo.
Nao envia nada. Usa as funcoes do youtube_web_poster (abre o Chrome numa porta livre e fecha pelo CDP)."""
import sys
from pathlib import Path

sys.path.insert(0, r"D:\postador-de-videos\bin")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import youtube_web_poster as W  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

V = r"D:\veo\beta"
CANDIDATOS = [
    ("cenareact", "UCrYkau_YGtx8C29qnF9xSYQ", [rf"{V}\chrome_gen_nova_225153", rf"{V}\profiles\chrome_gen_nova_1786128564"]),
    ("cartuchoreact", "UCrskUXOpfPUkSY3HMT2c7_A", [rf"{V}\profiles\chrome_gen_nova_1785463299", rf"{V}\profiles\chrome_gen_nova_1786128712"]),
    ("historiasemframes", "UCIFvn2aqdrv8X-LYscTyjjA", [rf"{V}\chrome_gen_nova_224751", rf"{V}\profiles\chrome_gen_nova_1786128033"]),
    ("mundoquenaoexiste", "UCPTjuCzT0k82K9sE5KXdSIw", [rf"{V}\chrome_gen_conta9"]),
    ("inovaremanhwabr", "UCZfQc_UIPRzU35GEjfTMCGA", [rf"{V}\profiles\chrome_gen_nova_1785463629"]),
    ("inovare_eng", "UCSGryZuOYBYE6oCFS7n-yUg", [rf"{V}\profiles\chrome_gen_nova_1785464200"]),
]
porta = 9590
for slug, uc, pastas in CANDIDATOS:
    for pasta in pastas:
        porta += 1
        proc = None
        try:
            proc = W.abrir_chrome(pasta, porta)  # caminho absoluto: Path(PERFIS_DIR) / absoluto = absoluto
            with sync_playwright() as p:
                br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
                pg = br.contexts[0].new_page()
                try:
                    W._abrir_studio(pg, uc)
                    print(f"{slug:18} VIVO  {pasta}", flush=True)
                except W.Falha as f:
                    print(f"{slug:18} {f.status.upper():5} {pasta}  ({str(f)[:70]})", flush=True)
                except Exception as ex:  # noqa: BLE001
                    print(f"{slug:18} ERRO  {pasta}  ({type(ex).__name__}: {str(ex)[:70]})", flush=True)
                try:
                    pg.close()
                except Exception:  # noqa: BLE001
                    pass
                W.soltar(br, proc)
        except Exception as ex:  # noqa: BLE001
            print(f"{slug:18} ERRO  {pasta}  ({str(ex)[:80]})", flush=True)
        finally:
            W.fechar_chrome(proc)
