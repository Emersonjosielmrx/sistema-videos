# -*- coding: utf-8 -*-
"""Cortes AUTOMÁTICOS dos vídeos reais do Google Fotos -> assets\\videos_reais\\clipes.json (dono 25/10: "criar vídeos
desse material usando projetos como cortes"). Até 25/10 eram 7 trechos aprovados a olho para 225 vídeos baixados.

Mesmo critério da aprovação a olho de 22/10 (_leia do clipes.json): sem rosto, sem tela de app/texto, sem clipe de IA,
resolução >= 480 — agora conferido por visão em 3 quadros de cada trecho (produto\\cortes.py). Entra com "auto": true;
o video_real_ms.py usa como os outros. Retomável: cache\\cortes_ms_estado.json guarda o resultado de cada vídeo.

    python cortes_ms.py [--max 50] [--refazer-erros]
"""
import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\postador-de-videos\bin")
from produto import cortes  # noqa: E402

DIR = Path(r"D:\ms-energy")
VIDEOS = DIR / "assets" / "fotos_instagram" / "google_fotos" / "videos"
INDICE_G = DIR / "assets" / "fotos_instagram" / "google_fotos" / "indice_google.json"
CLIPES = DIR / "assets" / "videos_reais" / "clipes.json"
ESTADO = DIR / "cache" / "cortes_ms_estado.json"
MAX_POR_VIDEO = 4

PERGUNTA = (
    "Este é um quadro de um vídeo do celular do dono de uma empresa de energia solar no Pará (Brasil). Responda SÓ JSON:\n"
    '{"energia_solar": true se aparece placa/painel solar, instalação, estrutura de painel, inversor, usina solar ou '
    "telhado sendo preparado para placas,\n"
    ' "rosto": true se aparece QUALQUER rosto humano (mesmo pequeno, de lado ou ao fundo),\n'
    ' "tela_ou_texto": true se aparece tela de celular/computador/aplicativo, print, texto ou legenda sobreposta, '
    "marca d'água, telefone ou @,\n"
    ' "parece_ia": true se parece imagem gerada por IA, desenho ou animação,\n'
    ' "qualidade": 1 a 10 (nitidez e luz; quadro tremido ou borrado = nota baixa),\n'
    ' "mostra": "placas_no_telhado" | "usina_no_solo" | "equipe_instalando" | "estrutura" | "inversor" | "drone" | "outro",\n'
    ' "descricao": "frase curta em português do que aparece"}')

PAUTAS_POR_MOSTRA = {
    "placas_no_telhado": ["experiencia", "telhado_tipo", "durabilidade", "valorizacao", "quantas_placas", "calor_ar",
                          "chuva", "investimento"],
    "usina_no_solo": ["energia_limpa", "investimento", "comercio"],
    "equipe_instalando": ["processo", "experiencia", "manutencao", "empresa_local"],
    "estrutura": ["processo", "telhado_tipo", "manutencao"],
    "inversor": ["monitoramento", "processo"],
    "drone": ["experiencia", "empresa_local", "valorizacao", "quantas_placas"],
}


def triagem(r):
    return bool(r.get("energia_solar"))


# 25/10 (revisão a olho dos 17 primeiros): vídeo SEM data de gravação = baixado de WhatsApp/internet (pode ser obra de
# outra empresa, e o Reel diz "instalação da MS Energy" -> propaganda enganosa); a conta de afiliado tem material de
# fornecedor. Só entra vídeo com data, de conta do dono.
CONTAS_FORA = {"vendeafiliados3"}
TRECHOS_FORA = {"auto_zvnhIIgtBhvG_1"}  # telhado metálico sem placa e um pé no canto


def origem_ok(nome):
    return "_sem-data_" not in nome and nome.split("_")[0] not in CONTAS_FORA


def aprova(r):
    return (bool(r.get("energia_solar")) and not r.get("rosto") and not r.get("tela_ou_texto")
            and not r.get("parece_ia") and int(r.get("qualidade") or 0) >= 6)


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return padrao


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=0, help="no máximo N vídeos nesta rodada (0 = todos)")
    ap.add_argument("--refazer-erros", action="store_true")
    a = ap.parse_args()
    estado = _ler(ESTADO, {})
    clipes = _ler(CLIPES, {"clipes": []})
    ja = {c["arquivo"] for c in clipes["clipes"] if not c.get("auto")}  # os aprovados a olho ficam como estão
    ind = _ler(INDICE_G, {})
    videos = sorted(Path(n).name for n, v in ind.items() if v.get("tipo") == "video" and (VIDEOS / Path(n).name).exists())
    pendentes = [v for v in videos if v not in ja and origem_ok(v)
                 and (v not in estado or (a.refazer_erros and estado[v].get("tentar_de_novo")))]
    # limpa do clipes.json o que a regra de origem / a revisão a olho tiraram
    clipes["clipes"] = [c for c in clipes["clipes"] if not c.get("auto")
                        or (origem_ok(c["arquivo"]) and c["id"] not in TRECHOS_FORA)]
    CLIPES.write_text(json.dumps(clipes, ensure_ascii=False, indent=1), "utf-8")
    if a.max:
        pendentes = pendentes[:a.max]
    print(f"vídeos: {len(videos)} | já cortados: {len(estado)} | nesta rodada: {len(pendentes)}", flush=True)
    novos = 0
    for i, nome in enumerate(pendentes, 1):
        try:
            res = cortes.cortar(VIDEOS / nome, PERGUNTA, aprova, triagem)
        except Exception as e:  # noqa: BLE001
            res = {"status": f"erro: {type(e).__name__}: {str(e)[:100]}", "trechos": [], "tentar_de_novo": True}
        res["quando"] = datetime.now().isoformat(timespec="seconds")
        estado[nome] = res
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1), "utf-8")
        trechos = res.get("trechos", [])[:MAX_POR_VIDEO]
        if trechos:
            clipes = _ler(CLIPES, {"clipes": []})  # relê: outra rotina pode ter mexido
            clipes["clipes"] = [c for c in clipes["clipes"] if not (c.get("auto") and c["arquivo"] == nome)]
            for n, t in enumerate(trechos, 1):
                mostra = Counter(r.get("mostra") for r in t["visao"]).most_common(1)[0][0]
                clipes["clipes"].append({
                    "id": f"auto_{Path(nome).stem[-12:]}_{n}", "arquivo": nome, "inicio": t["inicio"], "fim": t["fim"],
                    "mostra": t["visao"][1].get("descricao") or mostra, "categoria": mostra,
                    "pautas": PAUTAS_POR_MOSTRA.get(mostra, ["experiencia"]), "auto": True,
                    "aprovado_por": "visão em 3 quadros (cortes_ms.py)", "quando": res["quando"]})
                novos += 1
            CLIPES.write_text(json.dumps(clipes, ensure_ascii=False, indent=1), "utf-8")
        print(f"[{i}/{len(pendentes)}] {nome}: {res['status']}" + (f" -> +{len(trechos)} clipes" if trechos else ""),
              flush=True)
    total = len(_ler(CLIPES, {"clipes": []})["clipes"])
    print(f"fim: +{novos} clipes automáticos | clipes no total: {total}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
