r"""Projeto João Lucas Virjão — pasta pública do Drive do parceiro (manhwa-drive:joao-lucas-virjao).
A cada rodada (tarefa do Windows JoaoLucasVirjaoDrive, 10/10 min, oculta):
  1. vídeo novo em "1_..." (grande: editado + cortes) ou "2_..." (só cortes de Shorts), com tamanho parado desde a
     rodada anterior (upload terminou) -> cópia DENTRO do Drive pra _interno e pedido pra central da hermes-prod
     (origem_drive: o vídeo não passa pela internet de casa; o PC nunca fala com o Kaggle). O original dele vai pra
     "_ja recebidos". Memes (pasta 4) e trilhas (pasta 5) dele vão como endereço — o Kaggle baixa e prioriza.
  2. pedido pronto -> "3_SAIDA/<nome>/" (vídeo editado + cortes pra Shorts + títulos sugeridos); erro -> aviso lá.
    pythonw vigia_drive.py          log: ..\vigia_drive.log   estado: ..\vigia_drive.json"""
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
RC = r"D:\tools\rclone.exe"
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe"
VPS, VPS_ENTRADA = "hermes-prod", "/opt/recap_central/entrada"
FILA, FILA_SRC = "manhwa-drive:colab_recap/fila", "manhwa-drive:colab_recap/fila_src"
RAIZ = "manhwa-drive:joao-lucas-virjao"
# entrada -> modo (dona 04/11: cru = edição completa + Shorts; editado = só melhorar / melhorar + cortes; só cortes)
ENTRADAS = {
    "1_VIDEO CRU - sai editado completo (tira pausas, legenda, memes, trilha, efeitos) + Shorts":
        {"cru": True, "cortes": True},
    "2_VIDEO JA EDITADO - so melhorar (legenda, memes, trilha, efeitos) sem Shorts": {"cortes": False},
    "3_VIDEO JA EDITADO - melhorar + fazer os cortes pra Shorts": {"cortes": True},
    "4_SO CORTES - vira so Shorts editados (o video completo nao volta)": {"so_cortes": True},
}
P_SAIDA_VIDEOS = "5_SAIDA - VIDEOS COMPLETOS prontos"
P_SAIDA_SHORTS = "6_SAIDA - SHORTS prontos (uma pasta por video)"
P_MEMES = "7_SEUS MEMES com prioridade - videos curtos ate 12s ou imagens que voce quer nos videos"
P_TRILHAS = "8_SUAS TRILHAS com prioridade - musicas mp3 de fundo que voce quer usar"
P_RECEB, P_INTERNO = "_ja recebidos (nao mexer)", "_interno (nao mexer)"
VIDEO = (".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi")
EST = PROJ / "vigia_drive.json"
LOG = PROJ / "vigia_drive.log"
TRAVA = PROJ / "vigia_drive.lock"
SEM_JANELA = 0x08000000


def log(m):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%d/%m %H:%M}] {m}\n")


def rc(*a, saida=False, timeout=3600):
    r = subprocess.run([RC, *a], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, creationflags=SEM_JANELA)
    if r.returncode != 0:
        raise RuntimeError(f"rclone {a[0]}: {r.stderr[-300:]}")
    return r.stdout if saida else None


def ler(remoto):
    try:
        return json.loads(rc("cat", remoto, saida=True, timeout=120))
    except (RuntimeError, ValueError):
        return None


def ssh(cmd, entrada=None):
    subprocess.run([SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", VPS, cmd], input=entrada, check=True,
                   capture_output=True, timeout=300, creationflags=SEM_JANELA)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40] or "video"


def enviar(est, pasta, arq):
    nome = Path(arq["Path"]).stem
    pid = f"20261027_000200_jlv{datetime.now():%m%d%H%M%S}_{slug(nome)[:20]}"
    interno = f"{RAIZ}/{P_INTERNO}/{pid}{Path(arq['Path']).suffix.lower()}"
    rc("copyto", f"{RAIZ}/{pasta}/{arq['Path']}", interno)  # dentro do Drive (servidor), sem passar por casa
    modo = ENTRADAS[pasta]
    so_cortes = bool(modo.get("so_cortes"))
    pedido = {"titulo": nome, "enviado": datetime.now().isoformat(timespec="seconds"), "projeto": "joao-lucas-virjao",
              "origem_drive": interno,
              "longo_override": {"voz_original": True, **modo, "cortes_max": 8,
                                 "memes_drive": f"{RAIZ}/{P_MEMES}", "trilhas_drive": f"{RAIZ}/{P_TRILHAS}"}}
    remoto = f"{VPS_ENTRADA}/{pid}"
    ssh(f"mkdir -p {remoto} && cat > {remoto}/pedido.json && touch {remoto}/enviado.ok",
        json.dumps(pedido, ensure_ascii=False).encode("utf-8"))
    rc("moveto", f"{RAIZ}/{pasta}/{arq['Path']}", f"{RAIZ}/{P_RECEB}/{datetime.now():%Y%m%d_%H%M}_{arq['Path']}")
    est["pedidos"].append({"pid": pid, "nome": nome, "so_cortes": so_cortes, "estado": "enviado",
                           "enviado": pedido["enviado"], "modo": pasta[:2]})
    log(f"ENVIADO {pid}: {arq['Path']} ({arq['Size'] / 1e6:.0f} MB, modo {pasta[:40]})")


def recolher(p):
    pronto = ler(f"{FILA}/{p['pid']}/pronto.json")
    if not pronto:
        erro = ler(f"{FILA}/{p['pid']}/erro.json")
        if erro:
            aviso = (f"O video '{p['nome']}' deu erro na edicao. Ja avisamos a equipe e ele vai ser refeito.\n\n"
                     f"Detalhe tecnico: {str(erro.get('error'))[:300]}\n")
            subprocess.run([RC, "rcat", f"{RAIZ}/{P_SAIDA_VIDEOS}/{p['nome']} - ERRO.txt"],
                           input=aviso.encode("utf-8"), creationflags=SEM_JANELA)
            p["estado"] = "erro"
            log(f"ERRO {p['pid']}: {str(erro.get('error'))[:200]}")
        return
    if not p["so_cortes"]:
        rc("copyto", f"{FILA_SRC}/{p['pid']}/final_anime_deitado.mp4",
           f"{RAIZ}/{P_SAIDA_VIDEOS}/{p['nome']} - EDITADO.mp4")
    titulos = []
    try:
        if "cortes.json" in rc("lsf", f"{FILA_SRC}/{p['pid']}/cortes_longo", saida=True):
            destino = f"{RAIZ}/{P_SAIDA_SHORTS}/{p['nome']}"
            rc("copy", f"{FILA_SRC}/{p['pid']}/cortes_longo", destino, "--include", "corte_*.mp4")
            for c in ler(f"{FILA_SRC}/{p['pid']}/cortes_longo/cortes.json") or []:
                titulos.append(f"{c.get('arquivo', '')}: {c.get('titulo', '')}  (gancho: {c.get('gancho', '')})")
            leia = (f"Shorts do video: {p['nome']}\nProntos em: {datetime.now():%d/%m/%Y %H:%M}\n\n"
                    "Titulos sugeridos:\n" + "\n".join(titulos) + "\n")
            subprocess.run([RC, "rcat", f"{destino}/LEIA - titulos sugeridos.txt"], input=leia.encode("utf-8"),
                           creationflags=SEM_JANELA)
    except RuntimeError as e:
        log(f"{p['pid']}: cortes não copiados ({e})")
    for lugar in (FILA, FILA_SRC):
        subprocess.run([RC, "purge", f"{lugar}/{p['pid']}"], capture_output=True, creationflags=SEM_JANELA)
    p["estado"] = "entregue"
    log(f"ENTREGUE {p['pid']}: {p['nome']} ({len(titulos)} cortes)")


def main():
    try:  # uma rodada por vez
        if TRAVA.exists() and time.time() - TRAVA.stat().st_mtime < 3 * 3600:
            return
        TRAVA.write_text(str(datetime.now()), encoding="utf-8")
    except OSError:
        return
    try:
        est = json.loads(EST.read_text(encoding="utf-8")) if EST.exists() else {"tamanhos": {}, "pedidos": []}
        novos_tam = {}
        for pasta in ENTRADAS:
            try:
                itens = json.loads(rc("lsjson", "-R", "--files-only", f"{RAIZ}/{pasta}", saida=True, timeout=300))
            except (RuntimeError, ValueError) as e:
                log(f"lista de {pasta[:12]} falhou: {e}")
                continue
            for a in itens:
                if not a["Path"].lower().endswith(VIDEO) or a["Size"] < 1_000_000:
                    continue
                chave = f"{pasta}|{a['Path']}"
                if est["tamanhos"].get(chave) == a["Size"]:  # parado desde a rodada anterior = upload terminou
                    try:
                        enviar(est, pasta, a)
                    except Exception as e:  # noqa: BLE001
                        log(f"envio de {a['Path']} falhou: {type(e).__name__}: {e}")
                        novos_tam[chave] = a["Size"]
                else:
                    novos_tam[chave] = a["Size"]
        est["tamanhos"] = novos_tam
        for p in est["pedidos"]:
            if p["estado"] == "enviado":
                try:
                    recolher(p)
                except Exception as e:  # noqa: BLE001
                    log(f"recolher {p['pid']} falhou: {type(e).__name__}: {e}")
        EST.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    finally:
        TRAVA.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
