r"""instagram_perfil.py — põe FOTO, NOME e BIO no Instagram de uma conta (dona 10/11: "perfis sem foto, sem bio...
não está postando com a mesma dedicação das solares").

Abre o Chrome DO COFRE da conta, oculto, NESTE PC (o mesmo onde ela já posta — nunca máquina/IP novo: conta nova em
aparelho novo é suspensa, ver memória feedback_instagram_aparelho_novo), entra em /accounts/edit/, troca a foto pela
imagem de config\perfis_instagram\<conta>.jpg e preenche a bio. O NOME exibido fica em "Central de contas" (fora
daqui). Uma conta por execução; só conta que já está logada aqui (cofre). Print antes/depois em logs\instagram_tela.

    python bin\instagram_perfil.py <conta>           # conta = chave do reuso_plataformas.json "instagram"
    python bin\instagram_perfil.py <conta> --ver     # só abre e tira print (não muda nada)
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402

PERFIS = ROOT / "config" / "perfis_instagram"
TELA = ROOT / "logs" / "instagram_tela"
REUSO = ROOT / "config" / "reuso_plataformas.json"


def bio(conta, marca):
    b = json.loads((PERFIS / "bios.json").read_text("utf-8"))
    return b.get(conta) or f"{marca} | Vídeos curtos todo dia. Siga para não perder o próximo."


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    conta, ver = sys.argv[1], "--ver" in sys.argv
    r = json.loads(REUSO.read_text("utf-8"))["instagram"]["contas"][conta]
    pausas = json.loads((ROOT / "config" / "instagram_pausas.json").read_text("utf-8"))
    if conta in pausas:
        sys.exit(f"{conta}: em pausa ({pausas[conta].get('motivo')}) — não mexo")
    marcas = json.loads((PERFIS / "marcas.json").read_text("utf-8"))
    foto = PERFIS / f"{conta}.jpg"
    marca = (marcas.get(conta) or {}).get("nome", conta)
    texto = bio(conta, marca)
    # 11/11: conta logada SÓ num notebook (iapro/canalhistoriacomia no x200ma): abre o Chrome DE LÁ (mesmo IP de onde
    # ela já posta), manda a foto pra lá. PC2 fica de fora (regra: PC2 só avisar).
    rem, proc = None, None
    maqs = [m for m in (r.get("maquina") or []) if m != "pc2"] if isinstance(r.get("maquina"), list) else []
    if maqs and r.get("perfil_remoto"):
        import maquina_remota
        rem = maquina_remota.Remoto(maqs[0])
        porta = rem.abrir(r["perfil_remoto"], "https://www.instagram.com/accounts/edit/")
        print(f"{conta}: pelo Chrome do {maqs[0]} (porta local {porta})")
    elif r.get("cofre"):
        porta, proc = cofre.abrir(r["cofre"])
    else:
        sys.exit(f"{conta}: sem cofre neste PC e sem notebook permitido (só PC2?) — não abro")
    TELA.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            pg = br.contexts[0].new_page()
            pg.goto("https://www.instagram.com/accounts/edit/", timeout=90000, wait_until="domcontentloaded")
            pg.wait_for_timeout(8000)
            pg.screenshot(path=str(TELA / f"perfil_{conta}_antes.png"))
            if "login" in pg.url or "suspended" in pg.url or "challenge" in pg.url:
                print(f"{conta}: não está logada/liberada aqui ({pg.url[:80]}) — nada feito")
                return
            # 10/11: só completa o que FALTA — a dona já montou perfis à mão (fakenews.ia4: foto, bio, Whats)
            bio_atual = ""
            try:
                bio_atual = pg.locator("textarea").first.input_value(timeout=10000).strip()
            except Exception:  # noqa: BLE001
                pass
            # sem foto = o Instagram mostra o avatar padrão com alt "Adicionar uma foto do perfil" (visto 10/11)
            foto_padrao = pg.evaluate("""() => [...document.images].some(i =>
                /adicionar uma foto do perfil|add a profile photo/i.test(i.alt || ''))""")
            print(f"{conta}: bio atual {len(bio_atual)} car. | foto padrão (sem foto): {foto_padrao}")
            if ver:
                print(f"{conta}: print em {TELA / f'perfil_{conta}_antes.png'}")
                return
            if bio_atual and not foto_padrao:
                print(f"{conta}: perfil já montado — não mexo")
                return
            # foto: o input de arquivo existe escondido na página de edição
            try:
                if not foto_padrao:
                    raise StopIteration
                pg.locator("input[type=file][accept*='image']").first.set_input_files(str(foto), timeout=20000)
                pg.wait_for_timeout(9000)
                print(f"{conta}: foto enviada")
            except StopIteration:
                print(f"{conta}: já tem foto — mantida")
            except Exception as e:  # noqa: BLE001
                print(f"{conta}: foto falhou ({type(e).__name__}: {str(e)[:80]})")
            # bio
            try:
                if bio_atual:
                    raise StopIteration
                campo = pg.locator("textarea").first
                campo.click(timeout=15000)
                campo.fill(texto[:150])
                pg.wait_for_timeout(1500)
                pg.get_by_role("button", name="Enviar").or_(pg.get_by_role("button", name="Submit")).first.click(
                    timeout=15000)
                pg.wait_for_timeout(6000)
                print(f"{conta}: bio salva ({len(texto[:150])} caracteres)")
            except StopIteration:
                print(f"{conta}: já tem bio — mantida")
            except Exception as e:  # noqa: BLE001
                print(f"{conta}: bio falhou ({type(e).__name__}: {str(e)[:80]})")
            pg.goto(f"https://www.instagram.com/{conta}/", timeout=90000, wait_until="domcontentloaded")
            pg.wait_for_timeout(6000)
            pg.screenshot(path=str(TELA / f"perfil_{conta}_depois.png"))
            print(f"{conta}: print depois em {TELA / f'perfil_{conta}_depois.png'}")
    finally:
        try:
            if rem:
                rem.fechar()
            elif proc:
                cofre.fechar(proc, None, r["cofre"])
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    main()
