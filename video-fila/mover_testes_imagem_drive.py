# -*- coding: utf-8 -*-
r"""Dona 20/11: "vamos mover para o Drive todos os seus testes antigos e outros testes de imagem anteriores a você e
deixar os locais apenas documentados com o endereço de onde estão no Drive e o que são".

Para cada item: rclone copy -> rclone check --one-way (tamanho) -> só então apaga o local (Python, sem rm com *)
-> deixa <nome>__NO_DRIVE.md no lugar. Retomável: item já com .md e sem a pasta local = pula.
Índice geral: D:\hipercool-materiais\TESTES_IMAGEM_NO_DRIVE.md  | log: D:\video-fila\mover_testes_imagem_drive.log
"""
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RCLONE = r"D:\tools\rclone.exe"
BASE_DRIVE = "manhwa-drive:arquivo-pc1/testes/imagem_20nov"
LOG = Path(r"D:\video-fila\mover_testes_imagem_drive.log")
INDICE = Path(r"D:\hipercool-materiais\TESTES_IMAGEM_NO_DRIVE.md")
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# (caminho local, o que é)
ITENS = [
    (r"D:\fabrica-poses\referencias\obras\snhb\video",
     "vídeo-fonte da obra SNhb (1,9 GB) + grades/folhas de teste de rosto e roupa (15-16/11). original_heroi.jpg e "
     "capa_B_bruxas.jpg continuam no PC (lote.py usa)"),
    (r"D:\fabrica-poses\referencias\TODAS\PARA_VER",
     "1ª rodada das 28 poses da Fábrica de Poses (14/11), substituída pela PARA_VER_V2"),
    (r"D:\fabrica-poses\referencias\TODAS\PARA_VER_V2",
     "2ª rodada das poses com elenco da obra + Maria (14/11 23h). lote.py recria a pasta se rodar de novo"),
    (r"D:\fabrica-poses\referencias\TODAS\_V2_rosto_errado", "poses V2 reprovadas: rosto errado (14-15/11)"),
    (r"D:\fabrica-poses\referencias\TODAS\_VERSAO1_heroi_generico", "poses V1 reprovadas: herói genérico (14/11)"),
    (r"D:\fabrica-poses\referencias\TODAS\TESTE_GEMINI_X_FLOW",
     "teste Gemini x Flow com rostos reais do vídeo SNhb (teste_gemini_flow.py, 14/11)"),
    (r"D:\fabrica-poses\referencias\TODAS\TESTE_GEMINI_HTTP", "pasta de teste Gemini HTTP (vazia)"),
    (r"D:\fabrica-poses\referencias\episodios\_teste", "teste do elenco_episodio (16/11)"),
    (r"D:\fabrica-poses\_t", "rascunhos soltos da Fábrica de Poses"),
    (r"D:\fabrica-poses\_teste1.jpg", "imagem de teste solta da Fábrica de Poses"),
    (r"D:\gemini-argo\_teste_http", "testes do Gemini imagem/vídeo sem navegador (trio 14/11)"),
    (r"D:\gemini-argo\_teste_imagem", "prints de teste do gemini_imagem.py (14/11). A pasta fica vazia (o código grava prints nela)"),
    (r"D:\gemini-argo\_teste_video", "prints de vigia do gemini_video.py (14/11). A pasta fica vazia (o código grava prints nela)"),
    (r"D:\flow-imagens\saidas\mr_teste", "saídas de teste do Flow Imagens"),
    (r"D:\flow-imagens\teste_fabrica", "teste da fábrica de imagens do Flow (02/11)"),
    (r"D:\hipercool-materiais\capas_teste_01nov", "testes de capa de 01/11"),
    (r"D:\hipercool-materiais\teste_capas", "testes de capa antigos"),
    (r"D:\hipercool-materiais\engenharia_reversa\capas_teste_ab", "capas do teste A/B da engenharia reversa"),
    (r"D:\hipercool-materiais\capas_longos_refeitas\_teste_tema_cor", "teste de tema/cor das capas dos longos"),
]
# arquivos soltos das capas dos longos (folhas de comparação e testes de 02-19/11) -> 1 pasta no Drive
SOLTOS_DIR = Path(r"D:\hipercool-materiais\capas_longos_refeitas")
SOLTOS_PADROES = ["_folha_*.jpg", "_teste_frase.jpg", "_orig4.jpg"]
RECRIAR_VAZIA = {r"D:\gemini-argo\_teste_imagem", r"D:\gemini-argo\_teste_video"}


def log(msg):
    linha = f"{datetime.now():%d/%m %H:%M:%S} {msg}"
    print(linha, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def rc(*args):
    r = subprocess.run([RCLONE, *args, "--tpslimit", "8", "--transfers", "4"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", creationflags=SEM_JANELA)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def destino(local: Path):
    rel = str(local).replace(":", "").replace("\\", "/")  # D/fabrica-poses/...
    return f"{BASE_DRIVE}/{rel}"


def doc(local: Path, dst, oque, tamanho):
    md = local.parent / f"{local.name}__NO_DRIVE.md"
    md.write_text(
        f"# {local.name} — foi para o Drive\n\n"
        f"- O que é: {oque}\n"
        f"- Onde está: `{dst}` (conta 32, remoto rclone manhwa-drive)\n"
        f"- Tamanho: {tamanho}\n"
        f"- Movido em {datetime.now():%d/%m/%Y %H:%M} (pedido da dona: testes antigos de imagem fora do PC)\n"
        f"- Trazer de volta: `D:\\tools\\rclone.exe copy \"{dst}\" \"{local}\"`\n"
        f"- Índice de tudo que saiu: `{INDICE}`\n", encoding="utf-8")
    return md


def tamanho_local(p: Path):
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def fmt(n):
    return f"{n / 1e9:.2f} GB" if n > 1e9 else f"{n / 1e6:.1f} MB"


def mover(local: Path, oque):
    if not local.exists():
        log(f"pula (não existe): {local}")
        return None
    tam = tamanho_local(local)
    dst = destino(local)
    log(f"copiando {local} ({fmt(tam)}) -> {dst}")
    if local.is_file():
        cod, out = rc("copyto", str(local), dst)
        cod2, out2 = rc("check", str(local.parent), dst.rsplit("/", 1)[0], "--one-way", "--size-only",
                        "--include", "/" + local.name)
    else:
        cod, out = rc("copy", str(local), dst)
        cod2, out2 = rc("check", str(local), dst, "--one-way", "--size-only")
    if cod != 0 or cod2 != 0:
        log(f"FALHOU (nada apagado): {local}\n{out[-400:]}\n{out2[-400:]}")
        return None
    if local.is_file():
        local.unlink()
    else:
        shutil.rmtree(local)
        if str(local) in RECRIAR_VAZIA:
            local.mkdir()
    doc(local, dst, oque, fmt(tam))
    log(f"OK conferido e apagado: {local}")
    return (str(local), dst, oque, fmt(tam))


def main():
    feitos = []
    for caminho, oque in ITENS:
        r = mover(Path(caminho), oque)
        if r:
            feitos.append(r)
    # soltos: junta numa pasta temporária no mesmo disco e move como 1 item
    soltos = [p for pad in SOLTOS_PADROES for p in SOLTOS_DIR.glob(pad)]
    if soltos:
        junta = SOLTOS_DIR / "_soltos_testes_capas"
        junta.mkdir(exist_ok=True)
        for p in soltos:
            p.rename(junta / p.name)
        r = mover(junta, "folhas de comparação e testes soltos das capas dos longos (02-19/11): "
                         + ", ".join(sorted(p.name for p in soltos)))
        if r:
            feitos.append(r)
    linhas = []
    if INDICE.exists():
        linhas = INDICE.read_text(encoding="utf-8").splitlines()
    else:
        linhas = ["# Testes de imagem que foram para o Drive", "",
                  "Pedido da dona 20/11. Cada pasta local virou um `<nome>__NO_DRIVE.md` com o endereço.",
                  f"Script: `D:\\video-fila\\mover_testes_imagem_drive.py` (retomável). Log: `{LOG}`", "",
                  "| Local (apagado) | Drive | O que é | Tamanho |", "|---|---|---|---|"]
    for loc, dst, oque, tam in feitos:
        linhas.append(f"| `{loc}` | `{dst}` | {oque} | {tam} |")
    INDICE.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    log(f"=== fim: {len(feitos)} itens movidos; índice {INDICE}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
