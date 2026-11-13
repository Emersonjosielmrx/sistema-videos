#!/usr/bin/env python3
"""canais.py — cadastro ÚNICO dos canais de todos os projetos de vídeo: config/canais.json.

Dono 18/10/2026 ("os projetos funcionarem como um só, pra vários tipos de canal"): antes cada projeto tinha a sua
lista (youtube_navegador, rede_canais, canais_reservados, parceiro.json, hipercool fila.json...) e ninguém via o plano
do canal inteiro. Aqui fica, por canal: dono, quem mais alimenta (e como), teto do dia, fuso, idioma, nicho.
Quem usa: politica.py (reserva, teto por canal, vaga do dono), notificar_telegram.medir_48h, status_videos.py.

    python canais.py gerar      # monta canais.json a partir dos arquivos antigos (não mexe neles); não sobrescreve
    python canais.py gerar --refazer
    python canais.py conferir   # o que os arquivos antigos dizem diferente do cadastro
    python canais.py            # lista

Alimentador "livre" = divide o teto do canal com o dono, quem chegar primeiro. "sobra" = só posta se o canal não teve
nada no dia (regra "nunca sem postagem") ou depois de `libera_as` (hora local), quando a janela do dono acabou.
"""
import json
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import politica  # noqa: E402

CADASTRO = politica.CONFIG_DIR / "canais.json"
NAVEGADOR = politica.NAVEGADOR_FILE
REDE = politica.REDE_FILE
RESERVAS = politica.RESERVA_FILE
PARCEIRO = Path(r"D:\recapd-ambientes\producao\config\parceiro.json")
HIPER_FILA = Path(r"D:\hipercool-videos\config\fila.json")
PROJETO_ANTIGO = {"recapd": "parceiro"}  # canais_reservados chamava o parceiro pelo nome da pasta

# Decisões do dono que não estão em nenhum arquivo antigo
DECISOES = {
    # 18/10: Manhwa Noturno fica com o hipercool (até 3/dia, regra BR), parceiro só a vaga que sobrar
    # 02/11 dona: "pode liberar o InovareManhwaVerse e o Manhwa Noturno pra vídeo longo" — só o postar_longos
    # (projeto longo_recap, 1 longo/dia por canal) entra; Shorts de parceiro continuam como estavam
    "novo_manhwanoturno": {"max_dia": 3, "alimentadores": {"parceiro": "sobra", "longo_recap": "livre"},
                           "libera_as": "23:00"},
    "novo_inovaremanhwaverse": {"alimentadores": {"longo_recap": "livre"}},
    # 01/11: Comédia Noturna (emersonjosiel02) = projeto comentarios (D:\videos-comentarios), 3/dia (dona)
    "novo_comedianoturna": {"max_dia": 3},
}


def _cred_para_slug(nav):
    out = {}
    for slug, e in nav.items():
        for cid in e.get("creds") or []:
            out[cid] = slug
    return out


def gerar():
    nav = politica.ler_json(NAVEGADOR, {}).get("canais", {})
    rede = {c["slug"]: c for c in politica.ler_json(REDE, {}).get("canais", [])}
    res = politica.ler_json(RESERVAS, {})
    parc = politica.ler_json(PARCEIRO, {})
    hip = politica.ler_json(HIPER_FILA, {})
    creds = {c["id"]: c for c in politica.carregar_creds()}

    canais = {}

    def entrada(cid):
        slug = _cred_para_slug(nav).get(cid)
        chave = slug or cid
        if chave not in canais:
            e = nav.get(slug, {}) if slug else {}
            c = creds.get(cid, {})
            canais[chave] = {
                "slug": slug, "creds": list(e.get("creds") or [cid]), "nome": (e.get("nome") or c.get("nome") or "").strip(),
                "handle": e.get("handle"), "channel_id": e.get("channel_id"), "navegador": bool(e.get("usar")),
                "idioma": None, "fuso": None, "nicho": None, "dono": None, "alimentadores": {}, "max_dia": None,
            }
        return canais[chave]

    for proj, ids in res.items():
        if proj.startswith("_") or not isinstance(ids, list):
            continue
        for cid in ids:
            entrada(cid)["dono"] = PROJETO_ANTIGO.get(proj, proj)
    for slug, r in rede.items():
        for cid in r.get("creds") or []:
            x = entrada(cid)
            if x["dono"] is None and r.get("status") in ("ativo", "pausado"):
                x["dono"] = politica.PROJETO_REDE
            x["nicho"] = x["nicho"] or r.get("nicho")
            x["horarios_rede"] = r.get("horarios")
            if not x["idioma"]:
                x["idioma"] = "pt"
                x["fuso"] = "America/Sao_Paulo"
    hip_pt = (hip.get("postagem_pt") or {})
    for lang, d in (hip.get("idiomas") or {}).items():
        if isinstance(d, dict) and d.get("canal"):
            x = entrada(d["canal"])
            x.update(idioma=lang, fuso=d.get("fuso"), pico_hipercool=d.get("pico"), handle=x["handle"] or d.get("handle"))
    for cid, slug in _cred_para_slug(nav).items():
        if norm_nome(nav[slug].get("nome")) == norm_nome(hip.get("canal_pt")):
            entrada(cid).update(idioma="pt", fuso=hip_pt.get("fuso"), pico_hipercool=hip_pt.get("pico"))
    for d in parc.get("pt") or []:
        x = entrada(d["canal"])
        x.update(idioma="pt", fuso=d.get("fuso"), nicho=d.get("nicho") or x["nicho"], horarios_parceiro=d.get("horarios"))
        if x["dono"] in (None, "parceiro"):
            x["dono"] = "parceiro"
            x["max_dia"] = d.get("por_dia")
        elif d.get("ativo", True):
            x["alimentadores"]["parceiro"] = "livre"
    for lang, d in (parc.get("idiomas") or {}).items():
        if isinstance(d, dict) and d.get("canal") and d.get("ativo", True):
            x = entrada(d["canal"])
            x["idioma"] = x["idioma"] or lang
            x["fuso"] = x["fuso"] or d.get("fuso")
            if x["dono"] != "parceiro":
                x["alimentadores"]["parceiro"] = "livre"
    for x in canais.values():
        for cid in x["creds"]:
            if cid in DECISOES:
                d = DECISOES[cid]
                x["max_dia"] = d.get("max_dia", x["max_dia"])
                x["alimentadores"].update(d.get("alimentadores", {}))
                if d.get("libera_as"):
                    x["libera_as"] = d["libera_as"]
    for x in canais.values():
        # dono 18/10: canal BR abre no máx 3/dia (regra "nunca sem postagem": BR 3/dia) — react incluído
        if x["dono"] == politica.PROJETO_REDE and x["idioma"] == "pt" and not x["max_dia"]:
            x["max_dia"] = 3
        # dono 18/10 ("vê o que é melhor"): parceiro programa 7 dias à frente; o dono (react da rede, línguas do
        # hipercool) sobe poucas horas antes — 1 vaga/dia (upload e publicação) fica guardada pra ele
        if "livre" in x["alimentadores"].values():
            x["reserva_dono"] = 1
    return {
        "_leia": ("Cadastro ÚNICO dos canais (bin/canais.py). politica.py lê daqui: dono, alimentadores "
                  "(livre = divide o teto; sobra = só canal vazio no dia ou depois de libera_as, hora local), max_dia "
                  "(aperta o teto da política, nunca afrouxa). Outros campos são do projeto de origem (pico_hipercool, "
                  "horarios_parceiro, horarios_rede) e servem pro status/medição. NÃO EDITE À MÃO: o arquivo se refaz "
                  "sozinho quando os arquivos de origem mudam (politica.cadastro). Decisão do dono = DECISOES no "
                  "bin/canais.py; canal novo = nos arquivos de origem (youtube_navegador, canais_reservados...)."),
        "canais": dict(sorted(canais.items())),
    }


def norm_nome(s):
    return politica.norm(s)


def carregar():
    return politica.ler_json(CADASTRO, {}).get("canais", {})


def conferir():
    cad = carregar()
    if not cad:
        print("canais.json não existe — rode: python canais.py gerar")
        return 1
    novo = gerar()["canais"]
    dif = 0
    for k in sorted(set(cad) | set(novo)):
        a, b = cad.get(k), novo.get(k)
        if a is None:
            print(f"{k}: está nos arquivos antigos e não no cadastro")
            dif += 1
            continue
        if b is None:
            print(f"{k}: está no cadastro e sumiu dos arquivos antigos")
            dif += 1
            continue
        for campo in ("dono", "alimentadores", "max_dia", "fuso", "idioma", "creds"):
            if a.get(campo) != b.get(campo):
                print(f"{k}.{campo}: cadastro={a.get(campo)!r} arquivos antigos={b.get(campo)!r}")
                dif += 1
    print(f"{dif} diferença(s)")
    return 0


def listar():
    creds = {c["id"]: c for c in politica.carregar_creds()}
    for k, x in carregar().items():
        ali = ",".join(f"{p}:{m}" for p, m in x.get("alimentadores", {}).items())
        print(f"{k:24} {politica.estado_do_cadastro(x, creds):10} dono={x.get('dono')!s:13} max={x.get('max_dia')!s:4} "
              f"{x.get('idioma')!s:3} {ali}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "listar"
    if cmd == "gerar":
        if CADASTRO.exists() and "--refazer" not in sys.argv:
            print(f"{CADASTRO} já existe (use --refazer pra montar de novo dos arquivos antigos)")
            return 1
        politica.gravar_json(CADASTRO, gerar())
        print(f"gravado {CADASTRO}")
        listar()
        return 0
    if cmd == "conferir":
        return conferir()
    listar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
