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
  outra, fabrica  -> NAO entram na lista.

Fora da lista desde 12/10/2026 (perfis migrados para D:\\logins-google\\cofre; ver LEIA_PERFIS_E_COFRE.md):
  - jogoscomia (9320), emersonjosiel2030 (9430), inovaremanga (9370): repetidas — a pasta delas virou junção para a
    MESMA pasta de jogoscomia2 / emerson2030 / inovaremanhwaverseesp. Duas sessões na mesma pasta = o 2º Chrome não abre.
  - fabricadeautomacoesia (9330) e rezaulkarimul (9340): Google deslogado em todas as cópias.
    Para voltar: python D:\\logins-google\\cofre.py logar <conta> e recolocar a linha.
  - emerson2029 (9350): o Flow bloqueia por idade (flow.google.com/age-restricted). A pasta continua no cofre
    (o canal CenaReact do YouTube usa). Volta quando a dona confirmar a idade da conta no Google.
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
    # 22/10 (dono: "sim"): as 10 abaixo voltaram — estavam comentadas desde 16/10 ("Onda 1.6: teste 2 dias com 3
    # contas", nunca desfeito); com 3 contas o credito do dia acabava e o MS Energy ficava sem video.
    {"session": "filmescomia",    "port": "9280", "profile": "chrome_gen_filmescomia",    "tier": "pro"},
    {"session": "fabiovideoseducativos", "port": "9290", "profile": "chrome_gen_conta5",  "tier": "pro"},
    {"session": "fabricadeautomacoes",   "port": "9300", "profile": "chrome_gen_conta6",  "tier": "pro"},
    {"session": "emersonjosiel649",      "port": "9310", "profile": "chrome_gen_emerson", "tier": "free"},
    {"session": "emerson2030",           "port": "9360", "profile": "profiles/chrome_gen_nova_1785463299", "tier": "pro"},
    {"session": "inovaremanhwabr",       "port": "9380", "profile": "profiles/chrome_gen_nova_1785463629", "tier": "pro"},
    {"session": "emersoncunha",          "port": "9390", "profile": "profiles/chrome_gen_nova_1785464200", "tier": "pro"},
    {"session": "emersonjosiel2027",     "port": "9410", "profile": "profiles/chrome_gen_nova_1786128033", "tier": "pro"},
    {"session": "inovaremanhwaverseesp", "port": "9440", "profile": "profiles/chrome_gen_nova_1786128902", "tier": "pro"},
    {"session": "jogoscomia2",           "port": "9450", "profile": "profiles/chrome_gen_nova_1786130581", "tier": "pro"},
]

# Nome da sessao -> perfil (parte do e-mail antes do @) nos notebooks, quando os dois sao diferentes.
# emerson2030 = emersonjosiel2030 (a pasta antiga emersonjosiel2030 virou juncao pra mesma conta, nota acima).
PERFIL_NOTEBOOK = {"emerson2030": "emersonjosiel2030"}


def _contas_so_notebook():
    """23/10 (dono): "use o Veo em todas as contas que temos (TikTok e YouTube)". Toda conta Google logada nos
    notebooks/desktop (D:\\postador-de-videos\\config\\netbooks_logins.json, conferido pelo maquina_remota) que nao esta
    na lista acima entra no rodizio do Veo SO pelas maquinas: nao tem Chrome neste PC (perfil 'so_notebook/...').
    tier 'free' = vem primeiro no escolher_sessao (tira o Chrome do Flow do PC1). A porta (9600+) so serve pra trava."""
    try:
        import sys as _sys
        _sys.path.insert(0, r"D:\postador-de-videos\bin")
        import maquina_remota
        perfis = maquina_remota.contas_flow()
    except Exception:
        return []
    ja = {c["session"].lower() for c in CONTAS} | {p.lower() for p in PERFIL_NOTEBOOK.values()}
    return [{"session": p, "port": str(9600 + i), "profile": f"so_notebook/{p}", "tier": "free", "notebook": True}
            for i, p in enumerate(sorted(x for x in perfis if x.lower() not in ja))]


CONTAS = CONTAS + _contas_so_notebook()


def perfil_notebook(session):
    """Perfil da conta nas maquinas (netbooks_logins.json) para essa sessao."""
    return PERFIL_NOTEBOOK.get(session, session)


# 29/10 (D30): contas que NAO devem gerar por HTTP nas maquinas (ficam so no Chrome, como antes). Ex.: uma conta que o
# Flow recusou por HTTP (UNUSUAL_ACTIVITY) repetidas vezes. Vazio = todas podem. Tambem aceita "sem_http": True na
# linha da conta em CONTAS. Desligar para TODAS: config.FLOW_HTTP_REMOTO / FLOW_HTTP_REMOTO=0.
SEM_HTTP = set()


def sem_http(session):
    """True = esta conta nao usa o caminho HTTP (so Chrome)."""
    s = (session or "").lower()
    return s in {x.lower() for x in SEM_HTTP} or any(c["session"].lower() == s and c.get("sem_http") for c in CONTAS)


def so_notebook(session):
    """True = conta sem Chrome neste PC: so roda nas maquinas (nunca abrir local)."""
    return any(c["session"] == session and c.get("notebook") for c in CONTAS)


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
