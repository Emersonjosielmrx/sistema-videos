"""Cobre, no tempo ocioso, os painéis que ficaram à mostra em capítulo já publicado/pronto.

Pedido do dono em 16/10, depois de liberar o cap 4 com o quadro de 3m25 à mostra pra não travar a
produção: *"pode ir para o 5, depois se der tempo cubra, se não acho que dá pra postar assim; aí
que vale aquilo que te falei: quando estiver ocioso aí ele faz as correções"*.

Como ele sabe o que corrigir: cada painel forçado (`censura_visual.forcar_fosco`) guarda a hora em
que foi marcado. Se essa hora é DEPOIS do `fim_render` do capítulo, o vídeo que está lá ainda tem o
painel à mostra. Depois do render novo o `fim_render` passa a ser o mais recente e o capítulo sai da
lista sozinho — refaz uma vez por capítulo, nunca fica em laço.

Por que existe separado de `fila.tempo_livre` (que chama a mesma `fila.corrigir_pendentes`): o
`tempo_livre` só roda com a fila de produção LIGADA, e ela fica desligada enquanto uma leva manual
(`refazer_caps.py`) está rodando. Este script não depende disso — ele espera o render que estiver
em andamento acabar e só então corrige, um capítulo por vez.

    venv/Scripts/python.exe -X utf8 bin/corrigir_pendentes.py            # fica esperando a máquina ficar ociosa
    venv/Scripts/python.exe -X utf8 bin/corrigir_pendentes.py --listar   # só diz o que está pendente
    venv/Scripts/python.exe -X utf8 bin/corrigir_pendentes.py --horas 6  # desiste depois de 6 h
"""
import argparse
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fila  # noqa: E402

ESPERA = 120  # s entre uma olhada e outra enquanto há render rodando
# Só começa depois de a máquina ficar parada por este tempo seguido. Serve pra NÃO entrar no
# intervalo entre dois capítulos de uma leva (`refazer_caps.py`), que dura segundos: o dono quer os
# capítulos novos primeiro ("pode ir para o 5, depois se der tempo cubra").
OCIOSO_MIN = 15


def diz(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)
    try:
        fila.log(msg)
    except Exception:  # noqa: BLE001 — registrar nunca derruba a correção
        pass


def _pc1_ocupado():
    """Medição COMUM entre projetos (D:\\video-fila\\maquinas.py, 17/10): o PC1 está ocupado se alguém (hipercool,
    anime, parceiro, histórias) está na fila_render. Sem a medição comum, vale só a checagem do próprio hipercool."""
    try:
        sys.path.insert(0, r"D:\video-fila")
        import maquinas
        m = maquinas.medir("pc1")
        return not m.get("ocioso", True), m.get("motivo", "")
    except Exception:  # noqa: BLE001
        return False, ""


def pendentes(est):
    """[(chave, quando_foi_marcado, fim_do_render)] dos capítulos cujo vídeo é mais velho que a marcação."""
    import revisao_video
    censura_visual = revisao_video.modulo("censura_visual")
    marcados = {}
    for p in censura_visual._forcados().values():
        try:
            quando = datetime.strptime(p.get("em", ""), "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        chave = Path(p["painel"]).parent.name
        if quando > marcados.get(chave, datetime.min):
            marcados[chave] = quando
    fora = []
    for chave, _obra, _n, _pasta in fila.capitulos():
        e = fila.ler_estado().get(chave) or {}
        if e.get("situacao") != "pronto" or not e.get("fim_render") or chave not in marcados:
            continue
        if e.get("pt_completo_em"):
            continue  # já no ar em pt: refazer não muda o vídeo publicado (17/10: capítulos novos primeiro)
        fim = datetime.fromisoformat(e["fim_render"])
        if marcados[chave] > fim:
            fora.append((chave, marcados[chave], fim))
    return fora


def main():
    ap = argparse.ArgumentParser(description="cobre no tempo ocioso os painéis que ficaram à mostra")
    ap.add_argument("--listar", action="store_true", help="só mostra o que está pendente e sai")
    ap.add_argument("--horas", type=float, default=24.0, help="desiste depois de tantas horas esperando")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    est = fila.ler_estado()
    falta = pendentes(est)
    if a.listar or not falta:
        for chave, quando, fim in falta:
            print(f"{chave}: painel marcado {quando:%d/%m %H:%M}, vídeo de {fim:%d/%m %H:%M}")
        if not falta:
            print("nada pendente — todo capítulo pronto já foi renderizado depois da última marcação")
        return
    diz(f"correções pendentes: {', '.join(c for c, *_ in falta)} — esperando a máquina ficar ociosa")

    limite = time.time() + a.horas * 3600
    feitos = []
    parada_desde = None
    while time.time() < limite:
        vivos = fila._renders_vivos()
        if vivos or _pc1_ocupado()[0]:
            parada_desde = None
            time.sleep(ESPERA)
            continue
        if parada_desde is None:
            parada_desde = time.time()
        if time.time() - parada_desde < OCIOSO_MIN * 60:
            time.sleep(ESPERA)  # pode ser só o intervalo entre dois capítulos da leva
            continue
        est = fila.ler_estado()
        falta = [p for p in pendentes(est) if p[0] not in feitos]
        if not falta:
            break
        chave = falta[0][0]
        alvo = next(((c, o, n, p) for c, o, n, p in fila.capitulos() if c == chave), None)
        if not alvo:
            feitos.append(chave)
            continue
        _c, obra, n, pasta = alvo
        diz(f"tempo livre: refazendo {chave} pra cobrir o painel que ficou à mostra")
        try:
            fila.avisar(f"tempo livre: refazendo {chave} pra cobrir o painel que ficou à mostra")
        except Exception:  # noqa: BLE001
            pass
        t0 = time.time()
        try:
            ok = fila.renderizar(chave, obra, n, pasta, est)
        except Exception:  # noqa: BLE001
            diz(f"{chave}: ERRO\n{traceback.format_exc()[:1200]}")
            ok = False
        feitos.append(chave)  # deu certo ou não, não tenta o mesmo de novo nesta rodada
        e = fila.ler_estado().get(chave, {})
        diz(f"{chave}: {'coberto' if ok else 'FALHOU'} em {(time.time() - t0) / 60:.0f} min "
            f"| situacao={e.get('situacao')} | análise={(e.get('revisao') or {}).get('status')}")
    sobrou = [c for c, *_ in pendentes(fila.ler_estado()) if c not in feitos]
    diz(f"correções: {len(feitos)} feito(s)" + (f"; ainda pendente: {', '.join(sobrou)}" if sobrou else "; nada pendente"))


if __name__ == "__main__":
    main()
