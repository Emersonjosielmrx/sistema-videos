# -*- coding: utf-8 -*-
"""
========================================================================
contas.py  —  FONTE UNICA DE VERDADE das contas Google usadas pelo bot
========================================================================

>>> EDITE SO ESTE ARQUIVO pra adicionar, remover ou trocar uma conta. <<<

Antes existiam 5 copias dessa lista espalhadas (cron_gerar_video_llm.py,
gera_auto.py, cron_gerar_video.py, multi_conta.py e varios .bat). Elas ficavam
inconsistentes entre si e isso ja causou bug real (uma conta esgotada
continuava sendo usada). Agora TODO mundo importa daqui.

Cada conta tem 3 campos:
  - session : nome curto interno (aparece nos logs e no comando `sessoes`)
  - port    : porta do Chrome CDP (Playwright conecta nela). UNICA por conta.
  - profile : nome da pasta do perfil Chrome (onde fica o login do Google)

Pra adicionar uma conta nova:
  1. Faca login no Chrome nesse perfil (veja TUTORIAL_NOVA_CONTA.md).
  2. Adicione UM dict novo na lista CONTAS abaixo (porta e profile INEDITOS).
  3. Rode:  python validate.py   (confirma que tudo continua consistente).

Contas MORTAS (nao usar / creditos acabados / perfil sem login):
  outra, fabrica, emersonjosiel649, mundosolar1995  -> NAO entram na lista.
"""

# ----------------------------------------------------------------------
# A LISTA. Edite aqui.
# ----------------------------------------------------------------------
#
# tier: "pro" = conta paga (muito credito, vale paralelizar e insistir)
#       "free" = conta gratis (pouco credito, faz poucos videos e gira rapido)
# Se omitir o tier, assume "pro" (comportamento antigo).
CONTAS = [
    {"session": "seebotsia",      "port": "9250", "profile": "chrome_gen_seebotsia",     "tier": "pro"},
    {"session": "mundosolar",     "port": "9260", "profile": "chrome_gen_mundosolar",    "tier": "pro"},
    {"session": "canalalucinaai", "port": "9270", "profile": "chrome_gen_canalalucinaai", "tier": "pro"},
]

# ----------------------------------------------------------------------
# Derivados (NAO edite — sao calculados a partir de CONTAS).
# ----------------------------------------------------------------------

# Alias historico: o orquestrador (cron_gerar_video_llm.py) usa o nome SESSOES.
SESSOES = CONTAS

# session -> pasta do perfil Chrome. gera_auto.py usa isto.
PROFILE_MAP = {c["session"]: c["profile"] for c in CONTAS}

# session -> porta CDP.
PORT_MAP = {c["session"]: c["port"] for c in CONTAS}

# session -> tier ("pro"/"free"). Default "pro" se nao especificado.
TIER_MAP = {c["session"]: c.get("tier", "pro") for c in CONTAS}


def tier_de(session):
    """Retorna o tier ('pro'/'free') de uma sessao. Default 'pro'."""
    return TIER_MAP.get(session, "pro")


def contas_pro():
    """Lista das contas PRO (pagas) — valem paralelizar e insistir."""
    return [c for c in CONTAS if c.get("tier", "pro") == "pro"]


def contas_free():
    """Lista das contas FREE (gratis) — poucos videos, giram rapido."""
    return [c for c in CONTAS if c.get("tier", "pro") == "free"]


def profile_de(session):
    """Retorna a pasta de perfil Chrome de uma sessao.
    Fallback seguro (chrome_gen_<nome>) se a sessao nao estiver no mapa —
    nunca levanta KeyError."""
    return PROFILE_MAP.get(session, f"chrome_gen_{session}")


def porta_de(session):
    """Retorna a porta CDP de uma sessao (str). Fallback '9250'."""
    return PORT_MAP.get(session, "9250")


def _consistente():
    """Sanidade: portas e profiles unicos, sem sessao repetida.
    Retorna (ok: bool, problemas: list[str])."""
    problemas = []
    sess = [c["session"] for c in CONTAS]
    ports = [c["port"] for c in CONTAS]
    profs = [c["profile"] for c in CONTAS]
    if len(set(sess)) != len(sess):
        problemas.append(f"sessions duplicadas: {sess}")
    if len(set(ports)) != len(ports):
        problemas.append(f"portas duplicadas: {ports}")
    if len(set(profs)) != len(profs):
        problemas.append(f"profiles duplicados: {profs}")
    return (not problemas), problemas


if __name__ == "__main__":
    ok, probs = _consistente()
    print(f"{len(CONTAS)} conta(s) configurada(s):\n")
    print(f"  {'SESSION':<16} {'PORT':<6} PROFILE")
    print(f"  {'-'*16} {'-'*6} {'-'*28}")
    for c in CONTAS:
        print(f"  {c['session']:<16} {c['port']:<6} {c['profile']}")
    print()
    if ok:
        print("OK: lista consistente (sessions/portas/profiles unicos).")
    else:
        print("PROBLEMAS encontrados:")
        for p in probs:
            print(f"  - {p}")
