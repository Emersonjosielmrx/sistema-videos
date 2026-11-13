# -*- coding: utf-8 -*-
r"""reel_globo.py — Reels da GLOBO SOLAR (@globosolarenergiag, Concórdia do Pará) com o CLONE do dono (dona 31/10/2026:
"esse é o dono da Globo, colete as fotos dele no insta e faça o avatar dele pra fazer as postagens de clone").

Mesmo pipeline do reel_advance (ms_v2: roteiro_ms -> Veo -> travas -> montagem_ms), trocando só neste processo a marca
para a Globo: fotos-base = dono (assets\globo\clone_bases: a foto que a dona mandou + quadros dos Reels dele, conferidos
pelo rosto), camisa preta (como nos vídeos dele), cartão final ardósia + laranja, histórico/pausa/pasta próprios
(carrossel_globo). Rodízio: clone, clone, foto real de obra. Clone que não passa no revisor de rosto = NÃO posta.
    D:\veo\venv\Scripts\python.exe reel_globo.py            # posta o pendente; senão gera 1 e posta
    D:\veo\venv\Scripts\python.exe reel_globo.py --so-gerar
"""
import argparse
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\ms-energy\bin")
sys.path.insert(0, r"D:\veo\beta")
import carrossel_globo  # noqa: E402,F401  (põe a marca/caminhos da Globo no carrossel_advance)
import carrossel_advance as ca  # noqa: E402
import montagem_ms  # noqa: E402
import reel_advance as ra  # noqa: E402
import roteiro_ms  # noqa: E402

CONTA = carrossel_globo.CONTA
BASES = Path(r"D:\ms-energy\assets\globo\clone_bases")
SAIDA = ca.REELS
LOG = Path(r"D:\ms-energy\logs\reel_globo.log")
TAG = "globo_clone"


def log(msg):
    linha = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(linha, flush=True)
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _clone_globo(cenario, fala_final, log=log):
    import foto_na_hora
    if foto_na_hora.bases_com_rosto(str(BASES)) < 3:
        log("  [CLONE] menos de 3 fotos do dono com rosto — sem vídeo")
        return None
    foto_na_hora.usar_bases(str(BASES))
    for rodada in range(3):
        f = foto_na_hora.gerar(roteiro_ms.CENARIOS[cenario], fala_final, tag=TAG,
                               pedido=roteiro_ms.PEDIDO_CLONE.format(cenario=roteiro_ms.CENARIOS[cenario]))
        if f:
            log(f"  [CLONE] dono da Globo no cenário '{cenario}': {Path(f).name}")
            return f, str(BASES)
        aprovadas = [r.get("arquivo") for r in foto_na_hora._registros()
                     if r.get("aprovada") and r.get("tag") == TAG and r.get("arquivo")
                     and Path(r["arquivo"]).exists() and r.get("cenario") == roteiro_ms.CENARIOS[cenario]]
        if aprovadas:
            return aprovadas[-1], str(BASES)
        if rodada < 2:
            log("  [CLONE] Flow sem conta livre — espero 4 min")
            time.sleep(240)
    return None


def _legendas_globo(legenda, pauta_id):
    tags = ["#energiasolar", "#concordiadopara", "#energiasolarpara", "#painelsolar", "#globosolar"]
    insta = (f"{legenda.strip()}\n\n"
             "☀️ Quer saber quanto dá para economizar? Comente SOL ou chame no WhatsApp: (91) 99394-9409.\n"
             f"📍 {ca.LOCAL}\n\n" + " ".join(tags))
    return insta, insta, tags


def _pauta(evitar=(), formato="reel", hist=None):
    usadas = {h.get("pauta"): i for i, h in enumerate(roteiro_ms._hist() if hist is None else hist)}
    cand = sorted((p for p in roteiro_ms.PAUTAS if p[0] not in evitar), key=lambda p: usadas.get(p[0], -1))[:5]
    return random.choice(cand)


def trocar_marca():
    roteiro_ms.EMPRESA = carrossel_globo.EMPRESA
    roteiro_ms.CTA_FALADO = "Orçamento com a Globo Solar."
    roteiro_ms.INSTAGRAM = "@" + CONTA
    roteiro_ms.HIST = Path(r"D:\ms-energy\cache\historico_roteiros_globo.json")
    fora = ("experiencia", "empresa_local", "manutencao", "barato_caro", "clientes")
    roteiro_ms.PAUTAS = [p for p in roteiro_ms.PAUTAS if p[0] not in fora] + [
        ("manutencao", "telhado", "Manutencao e simples: limpeza de vez em quando e revisao; a Globo Solar tambem cuida disso."),
        ("empresa_local", "comercio", "Empresa de Concordia do Para, que conhece o sol, a chuva e os telhados da regiao."),
        ("barato_caro", "telhado", "Instalacao nao e tudo igual: o barato pode sair caro; projeto e instalacao bem "
                                   "feitos evitam prejuizo."),
    ]
    roteiro_ms.RESERVA.update({
        "manutencao": ("Painel solar dá trabalho? A manutenção é simples e a Globo Solar cuida disso.", "Dá trabalho?"),
        "empresa_local": ("Somos de Concórdia do Pará e conhecemos o sol, a chuva e os telhados daqui.",
                          "Empresa da região"),
        "barato_caro": ("Instalação não é tudo igual. Feita do jeito certo, evita prejuízo e dor de cabeça.",
                        "O barato sai caro?"),
    })
    roteiro_ms.PEDIDO_CLONE = roteiro_ms.PEDIDO_CLONE.replace("plain solid red polo shirt", "plain solid black polo shirt")
    roteiro_ms._clone = _clone_globo
    roteiro_ms.legendas_finais = _legendas_globo
    roteiro_ms.escolher_pauta = _pauta
    ra.CONTA = CONTA  # o cartão final escreve @conta
    montagem_ms.cartao = ra._cartao_advance  # lê as cores/logo do carrossel_advance (já trocadas para a Globo)
    montagem_ms.VERMELHO = ca.LARANJA


def _proximo_tipo():
    feitos = [json.loads(j.read_text("utf-8")).get("tipo_video")
              for j in sorted(SAIDA.glob("*.json"), key=lambda p: p.stat().st_mtime)]
    return "com_foto" if feitos[-2:] == ["apresentador", "apresentador"] else "criativo"


def gerar():
    trocar_marca()
    import gerar_short_veo as g
    SAIDA.mkdir(parents=True, exist_ok=True)
    tipo = _proximo_tipo()
    log(f"formato deste Reel: {'foto real de obra' if tipo == 'com_foto' else 'avatar do dono'}")
    r = g.gerar_short_veo(output_dir=SAIDA, tipo=tipo, log=log)
    if not r or r == "SEM_CONTA":
        log(f"sem vídeo ({r})")
        return None
    side = json.loads(Path(r).with_suffix(".json").read_text("utf-8"))
    if side.get("tipo_video") == "foto_real":
        return Path(r)
    if side.get("tipo_video") != "apresentador" or "clone" not in json.dumps(side):
        destino = Path(r"D:\ms-energy\videos\_revisar") / Path(r).name
        destino.parent.mkdir(exist_ok=True)
        Path(r).replace(destino)
        log(f"vídeo sem o clone do dono -> {destino} (não posta)")
        return None
    return Path(r)


def postar(mp4):
    mp4 = Path(mp4)
    side_arq = mp4.with_suffix(".json")
    side = json.loads(side_arq.read_text("utf-8"))
    if side.get("postado"):
        return side["postado"]
    # 04/11 (dona: "nunca mais"): o Reel DfTKW4-s-CD (Luiz da ADVANCE) saiu aqui na Globo. Última trava: o vídeo tem que
    # ser da Globo E o rosto tem que ser o do dono da Globo (fotos-base DESTA empresa). Recusou = _revisar + aviso.
    trocar_marca()
    import gerar_short_veo as g
    import trava_empresa
    trava_empresa.conferir(mp4, g._empresa_atual(), BASES, log)
    sys.path.insert(0, str(ca.NSN))
    from services.instagram.postar import InstagramPostar
    try:
        code = InstagramPostar(CONTA).reel(str(mp4), side["legenda_insta"])
    except RuntimeError as e:  # 06/11: HTTP limitado (1357001/spam) mas o Chrome do cofre posta -> vai pelo navegador
        if not any(s in str(e).lower() for s in ("1357001", "entre para continuar", "feedback_required")):
            raise
        # 12/11: o HTTP "limitado" às vezes JÁ publicou — o navegador postava o mesmo vídeo de novo (sem legenda)
        code = ca.reel_ja_saiu(CONTA, side["legenda_insta"])
        if code:
            log(f"HTTP respondeu erro mas o Reel JÁ SAIU ({code}) — não posto de novo pelo navegador")
            code = None if code == "ja_saiu" else code
        else:
            log("HTTP limitado pelo Instagram — tentando pelo navegador do cofre")
            if not ca.reel_pelo_navegador(CONTA, mp4, side["legenda_insta"]):
                raise
            code = None
    side["postado"] = {"permalink": f"https://www.instagram.com/reel/{code}/" if code else f"https://www.instagram.com/{CONTA}/",
                       "em": datetime.now().isoformat(timespec="seconds")}
    side_arq.write_text(json.dumps(side, ensure_ascii=False, indent=2), "utf-8")
    log(f"PUBLICADO: {side['postado']['permalink']}")
    return side["postado"]


def _pendente():
    for j in sorted(SAIDA.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if not json.loads(j.read_text("utf-8")).get("postado") and j.with_suffix(".mp4").exists():
            return j.with_suffix(".mp4")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-gerar", action="store_true")
    a = ap.parse_args()
    try:
        if a.so_gerar:
            gerar()
            return
        ca.insistir(lambda: _pendente() or gerar(), postar, log=log)  # 01/11: tenta até sair
    except Exception as e:  # noqa: BLE001
        log(f"ERRO: {type(e).__name__}: {e}")
        if any(s in str(e).lower() for s in ca.LIMITE):
            ca.pausar(str(e), log=log)
        raise


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
