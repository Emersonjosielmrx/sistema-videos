"""longo_para_conferir.py — mantém SEMPRE 1 recap longo recente no PC pra dona conferir a qualidade (dona 30/10: "sempre
tenha um vídeo recente no PC pra eu ver, sem ficar baixando e apagando; só troca quando ele for postado, aí pega o mais
novo que não postou").

Pasta: D:\\hipercool-materiais\\LONGO_PARA_CONFERIR (1 mp4 + LEIA.txt com o que é e se já foi postado).
Escolha: o longo mais novo (feito_em) que ainda não foi postado nem reprovado; sem nenhum assim, fica o que está.
Roda no fim de cada rodada do postar_longos.py e pode ser rodado à mão:
    python longo_para_conferir.py
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RCLONE = r"D:\tools\rclone.exe"
FICHAS = Path(r"D:\hipercool-materiais\animes recap\na_nuvem")
PASTA = Path(r"D:\hipercool-materiais\LONGO_PARA_CONFERIR")
ESTADO = AQUI / "longos_postados.json"
FOLGA_GB = 20  # 06/11: a cópia de 10,6 GB deixou o D a 4,5 GB e segurou a postagem do próprio longo


def _postados():
    try:
        est = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, set()
    return {p["nome"]: p for p in est.get("postados", [])}, set(est.get("reprovados", []))


def _escolher():
    import postar_longos
    postados, reprovados = _postados()
    cand = []
    for nj in FICHAS.glob("*/nuvem.json"):
        try:
            d = json.loads(nj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        nome = nj.parent.name
        if (d.get("formato") == "deitado" and d.get("feito_em", "") >= postar_longos.DESDE and d.get("drive")
                and nome not in postados and nome not in reprovados):
            cand.append((d["feito_em"], nome, d))
    return max(cand) if cand else None


def _escrever_leia(nome, d, postado=None):
    linhas = [f"Longo pra conferir a qualidade — {nome}", f"Feito em: {d.get('feito_em')}",
              f"Original: {d.get('source_url', '')}", f"Baixado em: {datetime.now():%d/%m %H:%M}"]
    if postado:
        linhas.append(f"JÁ POSTADO em {postado.get('canal_nome')}: {postado.get('url')} (troca quando sair um novo)")
    else:
        linhas.append("Ainda NÃO postado. Quando for postado, este arquivo é trocado pelo mais novo que não postou.")
    (PASTA / "LEIA.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def atualizar():
    # 06/11 (dona viajando até 09/11): não baixa cópia de conferência — ninguém assiste e o disco é dos longos/clientes.
    # Apagar CONFERIR_PAUSADO_ATE ou passar da data volta ao normal.
    import os
    if datetime.now().strftime('%Y-%m-%d') < os.environ.get('CONFERIR_PAUSADO_ATE', '2026-11-09'):
        print('cópia de conferência pausada até a dona voltar (09/11)')
        return None
    PASTA.mkdir(parents=True, exist_ok=True)
    atual = next(iter(sorted(PASTA.glob("*.mp4"))), None)
    esc = _escolher()
    if not esc:
        if atual:
            postados, _ = _postados()
            nome = atual.stem
            try:
                d = json.loads((FICHAS / nome / "nuvem.json").read_text(encoding="utf-8"))
                _escrever_leia(nome, d, postados.get(nome))
            except (OSError, ValueError):
                pass
        print("nenhum longo novo sem postar — fica o que está:", atual.name if atual else "(vazio)")
        return atual
    _, nome, d = esc
    if atual and atual.stem == nome:
        print("já está aqui:", atual)
        return atual
    try:
        tam = json.loads(subprocess.run([RCLONE, "lsjson", d["drive"]], capture_output=True, text=True,
                                        timeout=300).stdout)[0]["Size"]
    except (ValueError, IndexError, KeyError, subprocess.TimeoutExpired):
        print("não achei o vídeo no Drive:", d["drive"])
        return atual
    livre = shutil.disk_usage(str(PASTA)).free
    if livre - tam < FOLGA_GB * 1e9 - (atual.stat().st_size if atual else 0):
        print(f"sem espaço no D: ({livre / 1e9:.1f} GB livres, vídeo {tam / 1e9:.1f} GB) — não baixa")
        return atual
    tmp = PASTA / f"{nome}.mp4.baixando"
    r = subprocess.run([RCLONE, "copyto", d["drive"], str(tmp)], capture_output=True, text=True, timeout=4 * 3600)
    if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size != tam:
        tmp.unlink(missing_ok=True)
        print("download falhou:", (r.stderr or "").strip()[-200:])
        return atual
    for velho in PASTA.glob("*.mp4"):
        velho.unlink(missing_ok=True)
    novo = tmp.with_name(f"{nome}.mp4")
    tmp.replace(novo)
    _escrever_leia(nome, d)
    print("pronto pra conferir:", novo)
    return novo


if __name__ == "__main__":
    sys.path.insert(0, str(AQUI))
    atualizar()
