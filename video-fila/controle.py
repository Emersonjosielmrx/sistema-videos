"""controle.py — liga/desliga ÚNICO dos projetos de vídeo (dono 18/10/2026: "funcionarem como um só").

Antes cada projeto tinha o seu botão (hipercool config/FILA_DESLIGADA e POSTAGEM_DESLIGADA, postador
config/POSTAGEM_DESLIGADA = botão do desktop, video-fila OCIOSO_DESLIGADO, parceiro.json "ligado"...), com o mesmo nome
pra coisas diferentes: o botão "desligar postagem" do desktop não parava o hipercool. Agora:

    python controle.py                          # mostra tudo (inclui os botões antigos, que continuam valendo)
    python controle.py desligar parceiro postagem
    python controle.py ligar hipercool producao
    python controle.py desligar tudo postagem   # nenhum projeto posta (a parada geral do postador continua à parte)

Em código:  sys.path.insert(0, r"D:\\video-fila"); import controle
            ok, motivo = controle.ligado("parceiro", "postagem")
Projetos: hipercool, parceiro, anime, manhwa-react, historias, veo, msenergy, controlador, postador. Etapas: producao,
postagem. "cortes" (dono 19/10: o recap não é mais só de anime) = parceiro + anime juntos.
`controlador producao` desligado = o controlador geral (controlador.py) não dispara nada.
`desktop producao` desligado = ninguém usa o desktop (PC3, onde o dono grava): maquinas.medir("desktop") devolve ocupado
sem nem entrar por ssh. Para o desktop só a etapa producao tem sentido.
Falhou ler (arquivo sumiu, JSON quebrado) = ligado: o controle nunca pode parar a produção por defeito dele.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
ARQ = BASE / "controle.json"
PROJETOS = ("hipercool", "parceiro", "anime", "manhwa-react", "historias", "veo", "msenergy", "controlador",
            "postador", "desktop", "celulares")
CORTES = ("parceiro", "anime")  # o antigo recap (pasta recapd-ambientes): Shorts de parceiros de todos os nichos + anime longo
# 04/11: `celulares producao` desligado = nenhum FFmpeg vai pros Galaxy S20 (celulares.py); tudo renderiza no PC
NOMES = {"parceiro": "cortes/parceiro", "anime": "cortes/anime", "desktop": "desktop (PC3)",
         "celulares": "celulares (S20)"}
ETAPAS = ("producao", "postagem")

# Botões antigos: (arquivo, projetos que ele desliga, etapa). Continuam valendo — quem já usa não precisa mudar.
ANTIGOS = [
    (Path(r"D:\hipercool-videos\config\FILA_DESLIGADA.json"), ("hipercool",), "producao"),
    (Path(r"D:\hipercool-videos\config\POSTAGEM_DESLIGADA.json"), ("hipercool",), "postagem"),
    (Path(r"D:\postador-de-videos\config\POSTAGEM_DESLIGADA.json"), ("manhwa-react", "parceiro", "postador", "veo",
                                                                     "historias", "anime"), "postagem"),
    (BASE / "OCIOSO_DESLIGADO.json", ("anime",), "producao"),
]
PARCEIRO = Path(r"D:\recapd-ambientes\producao\config\parceiro.json")


def _ler():
    try:
        return json.loads(ARQ.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar(d):
    tmp = ARQ.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ARQ)


def ligado(projeto, etapa):
    """(True, "") ou (False, motivo). Vale o que estiver desligado em qualquer lugar: controle.json ou botão antigo."""
    if projeto == "cortes":
        return next((r for r in (ligado(p, etapa) for p in CORTES) if not r[0]), (True, ""))
    try:
        d = _ler()
        tudo = (d.get("tudo") or {}).get(etapa, {})
        if tudo.get("ligado") is False:
            return False, f"{etapa} de TODOS desligada em controle.json ({tudo.get('motivo') or 'sem motivo'})"
        p = ((d.get("projetos") or {}).get(projeto) or {}).get(etapa, {})
        if p.get("ligado") is False:
            return False, f"{etapa} de {projeto} desligada em controle.json ({p.get('motivo') or 'sem motivo'})"
        for arq, projs, et in ANTIGOS:
            if et == etapa and projeto in projs and arq.exists():
                return False, f"{etapa} de {projeto} desligada pelo botão antigo {arq}"
        if projeto == "parceiro":
            try:
                if json.loads(PARCEIRO.read_text(encoding="utf-8")).get("ligado") is False:
                    return False, "parceiro desligado em config/parceiro.json (ligado=false)"
            except (OSError, ValueError):
                pass
    except Exception:  # noqa: BLE001 — defeito do controle não para nada
        pass
    return True, ""


def mudar(projeto, etapa, valor, motivo=""):
    d = _ler()
    d.setdefault("_leia", "Liga/desliga único (D:\\video-fila\\controle.py). Os botões antigos continuam valendo.")
    alvo = d.setdefault("tudo", {}) if projeto == "tudo" else d.setdefault("projetos", {}).setdefault(projeto, {})
    alvo[etapa] = {"ligado": valor, "motivo": motivo, "em": datetime.now().isoformat(timespec="seconds")}
    _gravar(d)


def painel():
    linhas = []
    for p in PROJETOS:
        est = []
        for e in (("producao",) if p in ("desktop", "celulares") else ETAPAS):
            ok, motivo = ligado(p, e)
            est.append(f"{e}: {'ligada' if ok else 'DESLIGADA — ' + motivo}")
        linhas.append(f"{NOMES.get(p, p):15} " + " | ".join(est))
    return "\n".join(linhas)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] in ("ligar", "desligar"):
        proj, etapa = a[1], a[2]
        if proj not in PROJETOS + ("tudo", "cortes") or etapa not in ETAPAS:
            print(f"uso: controle.py ligar|desligar <{'|'.join(PROJETOS)}|cortes|tudo> <producao|postagem> [motivo]")
            return 2
        for p in (CORTES if proj == "cortes" else (proj,)):
            mudar(p, etapa, a[0] == "ligar", " ".join(a[3:]))
            if a[0] == "ligar" and p != "tudo":
                ok, motivo = ligado(p, etapa)
                if not ok:
                    print(f"atenção: continua desligado por outro lugar — {motivo}")
    print(painel())
    return 0


if __name__ == "__main__":
    sys.exit(main())
