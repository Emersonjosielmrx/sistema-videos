# -*- coding: utf-8 -*-
"""revisar_instalacao.py — dona 29/10: "nem tudo que tem lá de fotos de painel são de coisas boas, algumas são reparos
de instalações ruins dos outros" e uma foto com os painéis TORTOS estava indo nos vídeos. Passa cada foto boa
(roteiro_ms.fotos_boas) por visão e grava em indice.json -> "instalacao": {"ok": bool, ...}. fotos_boas() pula as
reprovadas (MS Energy e Advance Solar usam o mesmo banco).

    python revisar_instalacao.py          # revisa só as que ainda não têm "instalacao"
    python revisar_instalacao.py --todas  # revisa de novo todas
"""
import io
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

sys.path.insert(0, r"D:\ms-energy\bin")
import qa_ms  # noqa: E402
import roteiro_ms  # noqa: E402

PERG = ('Você é um instalador sênior de energia solar revisando fotos para a propaganda de uma empresa que quer mostrar '
        'SÓ trabalho bem feito. Responda SÓ JSON: {"paineis_tortos": true se algum painel está desalinhado, torto, '
        'fora de esquadro, em alturas/ângulos diferentes dos vizinhos ou fileira irregular, "mal_feita": true se há '
        'sinal de instalação ruim ou reparo (gambiarra, fiação solta/exposta bagunçada, painel quebrado/trincado/'
        'faltando, estrutura improvisada ou enferrujada, telhas quebradas, obra pela metade, peças soltas no telhado), '
        '"marca": true se aparece logotipo, nome de empresa ou marca d\'água, "bonita": 1 a 10 (serve para mostrar '
        'serviço caprichado?), "motivo": "uma frase"}')
TRAVA = threading.Lock()


def revisar(nome):
    im = Image.open(roteiro_ms.FOTOS_DIR / nome).convert("RGB")
    im.thumbnail((1024, 1024))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    v = qa_ms.visao_json(buf.getvalue(), PERG)
    if "_erro" in v:
        return nome, None
    v["ok"] = not (v.get("paineis_tortos") or v.get("mal_feita") or v.get("marca")) and int(v.get("bonita") or 0) >= 6
    return nome, v


def main():
    arq = roteiro_ms.FOTOS_DIR / "indice.json"
    ind = json.loads(arq.read_text("utf-8"))
    nomes = [n for n, _ in roteiro_ms.fotos_boas(com_reprovadas=True)
             if "--todas" in sys.argv or "instalacao" not in ind.get(n, {})]
    print(f"{len(nomes)} fotos para revisar", flush=True)
    ok = ruim = 0
    with ThreadPoolExecutor(6) as ex:
        for i, (nome, v) in enumerate(ex.map(revisar, nomes), 1):
            if v is None:
                print(f"  {nome}: visão falhou", flush=True)
                continue
            with TRAVA:
                ind = json.loads(arq.read_text("utf-8"))
                ind[nome]["instalacao"] = v
                arq.write_text(json.dumps(ind, ensure_ascii=False, indent=1), "utf-8")
            ok += v["ok"]
            ruim += not v["ok"]
            if not v["ok"]:
                print(f"  REPROVADA {nome}: {v.get('motivo')}", flush=True)
            if i % 25 == 0:
                print(f"{i}/{len(nomes)} ({ok} ok, {ruim} reprovadas)", flush=True)
    print(f"FIM: {ok} ok, {ruim} reprovadas", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
