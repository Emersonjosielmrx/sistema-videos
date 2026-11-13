# -*- coding: utf-8 -*-
"""teste_cadeia_a_seco.py — simula as falhas da cadeia de alternativas do Veo (23/10/2026) SEM gerar video e SEM
gastar credito: o gera_auto e trocado por uma saida falsa, maquinas/medicoes sao simuladas e TODOS os arquivos de
estado vao para uma pasta temporaria (sessoes_status, creditos, castigos, aviso). Nada de ssh, Chrome, LLM ou Flow.

    D:\\veo\\venv\\Scripts\\python.exe -X utf8 teste_cadeia_a_seco.py
"""
import datetime
import os
import subprocess
import sys
import tempfile
import types

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.environ.update(VEO_VALIDAR="0", VEO_CONFERIR_FALA="0",
                  VEO_FOTO_NA_HORA="0", VEO_CONFERIR_ROSTO="0")  # 24/10: a seco = sem abrir o Flow pra foto
TMP = tempfile.mkdtemp(prefix="veo_cadeia_")

import cron_gerar_video_llm as cron  # noqa: E402
import cadeia_veo  # noqa: E402
import creditos_contas  # noqa: E402
import recursos  # noqa: E402
import fila  # noqa: E402

# ---------- tudo que grava vai pro TMP ----------
cron.SESSOES_FILE = os.path.join(TMP, "sessoes_status.json")
creditos_contas.ARQ = os.path.join(TMP, "creditos_contas.json")
cadeia_veo.ARQ_CASTIGO = os.path.join(TMP, "maquinas_veo.json")
cadeia_veo.ARQ_SEM = os.path.join(TMP, "veo_sem_alternativa.json")
cron.VIDEOS_DIR = os.path.join(TMP, "videos")
cron.BASE = TMP  # logs\worker_*.log do gera_auto falso tambem vao pro TMP
os.makedirs(os.path.join(TMP, "logs"), exist_ok=True)
LOG = []
cron.log = lambda m: LOG.append(m)
cadeia_veo._log = lambda m: LOG.append("[cadeia] " + m)
AVISOS = []
cadeia_veo._enviar_aviso = lambda t: AVISOS.append(t)
creditos_contas.resumo_do_dia = lambda *a, **k: None
cron._auto_fetch_metricas = lambda *a, **k: None
cron._reservar_notebooks = lambda *a, **k: None
cron.porta_em_uso = lambda p: False
cron._checar_saldo_conta = lambda *a: None
cron.save_hist = lambda: None
cron._fotos_com_marca = lambda: set()
cron.sem_repetir = lambda f, c: f
PAUSAS = []
cron.pausar_sistema = lambda *a, **k: PAUSAS.append(k or a)
cron.montar_prompt = lambda canal: dict(FORMULA)
recursos.disco_ok = lambda: True
recursos.resumo = lambda: "simulado"
try:
    import pos_producao.flags as _fl
    _fl.is_on = lambda n: True
except Exception:
    pass
FORMULA = {"prompt": "teste a seco", "fala": "teste", "fonte": "teste", "score": 8, "iteracoes": 1, "cenario": "x"}
CANAL = {"nome": "Aulas IA", "tema": "Micro-aulas e Tutoriais"}
fila.desenfileirar = lambda: {"formula": dict(FORMULA), "canal": CANAL, "foto": "foto.jpg", "tentativas": 0}
fila.enfileirar = lambda *a, **k: None
fila.reenfileirar_no_erro = lambda *a, **k: True
fila.tamanho = lambda: 0


class Gerou(Exception):
    pass


def _registrar_formula(*a, **k):
    if a[6]:  # out_path: o video "saiu" (dummy) — para aqui, sem cache/copia/thumbs/postar.json
        raise Gerou(a[6])
cron.registrar_formula = _registrar_formula

# ---------- cenario ----------
CEN = {}
CHAMADAS = []
_run_real = subprocess.run


def _subprocess_falso(cmd, *a, **k):
    if not (isinstance(cmd, list) and len(cmd) > 1 and str(cmd[1]).endswith("gera_auto.py")):
        return _run_real(cmd, *a, **k)
    sess, maqs = os.environ.get("FLOW_SESSION"), os.environ.get("VEO_MAQUINAS")
    CHAMADAS.append((sess, maqs))
    rc, out = CEN["worker"](sess, maqs)
    if rc == 0:
        os.makedirs(os.path.dirname(cmd[3]), exist_ok=True)
        with open(cmd[3], "wb") as f:
            f.write(b"\0" * 200_000)
    return subprocess.CompletedProcess(cmd, rc, out, "")


cron.subprocess.run = _subprocess_falso
_cadeia_real = cadeia_veo.cadeia


def _cadeia_sim(pausa_carga, pc1_tem_ram):
    return _cadeia_real(pausa_carga, pc1_tem_ram, medir=lambda h: CEN["medir"].get(h, {"ocioso": True, "ram_gb": 4}),
                        livre=lambda m: m in CEN["livres"] and not cadeia_veo.castigo(m),
                        contas_pc2=lambda: CEN.get("pc2_contas", []), tocando=lambda m: m in CEN.get("tocando", ()))


cron.cadeia_veo.cadeia = _cadeia_sim

OK_SALDO = (0, "[CREDITOS] saldo lido no menu de conta: 480\nvideo baixado\n")


def preparar(nome, pausa=None, slots=1, livres=("x200ma", "acer"), medir=None, tocando=(), worker=None, creditos=None):
    for p in (cron.SESSOES_FILE, creditos_contas.ARQ, cadeia_veo.ARQ_CASTIGO):
        if os.path.exists(p):
            os.remove(p)
    LOG.clear(); CHAMADAS.clear(); PAUSAS.clear()
    cron.sistema_pausado = lambda: pausa is not None
    cron._pausa_por_carga = lambda: pausa == "carga"
    cron._tipo_pausa = lambda motivo=False: ("motivo simulado" if motivo else (pausa or "manual"))
    recursos.slots_por_recurso = lambda: slots
    CEN.update(livres=set(livres), medir=medir or {}, tocando=set(tocando), worker=worker or (lambda s, m: OK_SALDO))
    d = {"aulacomia": {"saldo": 500}, "jornalcomia": {"saldo": 300}, "entrevistacomia": {"saldo": 10,
         "renova_em": (datetime.datetime.now() + datetime.timedelta(hours=5)).isoformat(timespec="seconds")},
         "seebotsia": {"saldo": 900}, "emersonjosiel2032": {"saldo": 200}}
    d.update(creditos or {})
    creditos_contas._gravar(d)
    print(f"\n=== {nome}")


def rodar():
    try:
        r = cron.run()
        res = f"sem video (run devolveu {r!r}; motivo: {cron._MOTIVO})"
    except Gerou:
        res = "VIDEO SAIU"
    print("  tentativas (conta, maquinas):", CHAMADAS)
    for l in LOG:
        if l.startswith(("[cadeia]", "[pool]", "[creditos]", "[gerar]", "[sessao]", "[pause]", "[CREDITOS]")):
            print("   ", l[:230])
    print("  RESULTADO:", res)
    return res, list(CHAMADAS)


FALHAS = []
# 24/10: a seebotsia (900) passou a estar logada nos notebooks tambem; nos cenarios de notebook ela fica com menos
# credito pra o teste continuar medindo a troca de conta na mesma etapa (aulacomia 500 -> jornalcomia 300)
SEEBOTS_NB = {"seebotsia": {"saldo": 100}}


def confere(cond, txt):
    print("  ->", "OK " if cond else "FALHOU", txt)
    if not cond:
        FALHAS.append(txt)


# 1) PC1 em carga, notebooks livres: notebooks, conta de MAIS credito (aulacomia=500); entrevistacomia (10) nunca
preparar("1. PC1 em pausa por carga, notebooks livres", pausa="carga", creditos=SEEBOTS_NB)
res, ch = rodar()
confere(res == "VIDEO SAIU" and ch[0] == ("aulacomia", "x200ma,acer"), "notebooks com a conta de mais credito")

# 2) notebooks ocupados (acer com Chrome do TikTok, x200ma exibindo no telao) -> desktop sem chamada
preparar("2. PC1 em carga; acer ocupado; x200ma exibindo video; desktop sem chamada", pausa="carga",
         livres=("x200ma", "desktop"), tocando=("x200ma",))
res, ch = rodar()
confere(res == "VIDEO SAIU" and ch and ch[0][1] == "desktop", "desktop (conta logada la)")

# 3) desktop EM CHAMADA, notebooks ocupados, PC1 sem carga com RAM, PC2 sem conta -> PC1
preparar("3. notebooks ocupados; desktop em chamada; PC1 livre", livres=(),
         medir={"desktop": {"ocioso": False, "motivo": "dono usando: microphone:chrome.exe"},
                "pc1": {"ocioso": True, "ram_gb": 6}})
res, ch = rodar()
confere(res == "VIDEO SAIU" and ch[0] == ("seebotsia", "pc1"), "PC1, conta local de mais credito (seebotsia=900)")

# 4) conta sem credito: troca de CONTA na mesma maquina (nao de maquina)
preparar("4. PC1 em carga; 1a conta do notebook sem credito", pausa="carga", creditos=SEEBOTS_NB,
         worker=lambda s, m: ((2, "[CREDITOS] saldo insuficiente (creditos=8)\nCREDITOS_ESGOTADOS padrao='saldo'")
                              if s == "aulacomia" else OK_SALDO))
res, ch = rodar()
confere(res == "VIDEO SAIU" and ch[0][0] == "aulacomia" and ch[1] == ("jornalcomia", "x200ma,acer"),
        "trocou para jornalcomia (300) na MESMA etapa de notebooks")
confere(creditos_contas.fora("aulacomia") is not None, "aulacomia ficou fora (< 20) ate renovar")

# 5) conta deslogada nas maquinas -> fora 6 h, proxima conta, mesma etapa
preparar("5. PC1 em carga; 1a conta deslogada nas maquinas", pausa="carga", creditos=SEEBOTS_NB,
         worker=lambda s, m: ((1, "[notebook] falhou no acer (SessaoExpiradaError: sessao expirada)\n"
                                  "RuntimeError: SO_NOTEBOOK: maquinas ocupadas ou fora")
                              if s == "aulacomia" else OK_SALDO))
res, ch = rodar()
confere(res == "VIDEO SAIU" and ch[1][0] == "jornalcomia" and ch[1][1] == "x200ma,acer", "outra conta, mesmos notebooks")
confere(cron.sessao_em_cooldown("aulacomia"), "aulacomia fora do rodizio (deslogada, sem relogin)")

# 6) notebooks pegos na hora de abrir (acer OCUPADO pelo TikTok, x200ma FALHOU) -> castigo -> desktop
preparar("6. PC1 em carga; notebooks livres na escolha mas ocupados/falhando na hora de abrir", pausa="carga",
         livres=("x200ma", "acer", "desktop"),
         worker=lambda s, m: ((1, "  x200ma: FALHOU: o Chrome nao abriu a porta de controle\n"
                                  "  acer: OCUPADO por e4487017 desde 21:26\nRuntimeError: SO_NOTEBOOK: maquinas")
                              if m != "desktop" else OK_SALDO))
res, ch = rodar()
confere(res == "VIDEO SAIU" and ch[-1][1] == "desktop", "seguiu a cadeia ate o desktop (antes: ciclo abortado)")
confere(bool(cadeia_veo.castigo("x200ma")) and bool(cadeia_veo.castigo("acer")), "x200ma 30 min e acer 5 min de castigo")

# 7) conta com < 20 creditos conhecida nunca e escolhida; com todas as do notebook abaixo -> desktop
_baixos = {s["session"]: {"saldo": 5, "renova_em": "2099-01-01T00:05:00"} for s in cron.SESSOES}
preparar("7. todas as contas abaixo de 20, menos a do desktop", pausa="carga", livres=("x200ma", "acer", "desktop"),
         creditos={**_baixos, "emersonjosiel2032": {"saldo": 200}})
res, ch = rodar()
confere(res == "VIDEO SAIU" and {c for c, _m in ch} == {"emersonjosiel2032"},
        "so a conta com credito foi usada (as < 20 foram puladas sem abrir nada)")

# 8) nada serve por horas -> UM aviso a dona com o motivo
preparar("8. tudo fora (PC1 em carga, notebooks ocupados, desktop em chamada) por 4 h", pausa="carga", livres=(),
         medir={"desktop": {"ocioso": False, "motivo": "dono usando: webcam:Zoom"}})
if os.path.exists(cadeia_veo.ARQ_SEM):
    os.remove(cadeia_veo.ARQ_SEM)
AVISOS.clear()
t0 = datetime.datetime.now()
for h in (0, 1, 2, 3.5, 4):
    cron.run()
    cadeia_veo.registrar_falha(cron._MOTIVO, agora=t0 + datetime.timedelta(hours=h))
print("  motivo:", cron._MOTIVO)
print("  avisos:", AVISOS)
confere(len(AVISOS) == 1 and "webcam" in AVISOS[0], "1 aviso so, com o motivo exato")
confere(not CHAMADAS, "nenhum gera_auto chamado (nada de credito)")

# 9) pausa MANUAL da dona: a cadeia nao fura
preparar("9. pausa manual da dona", pausa="manual")
res, ch = rodar()
confere(not ch and "PAUSA" in res, "parou sem tentar nenhuma alternativa")
preparar("10. pausa de bloqueio", pausa="bloqueio")
res, ch = rodar()
confere(not ch and "bloqueio" in str(cron._MOTIVO), "parou; conta como falha p/ o aviso")

subprocess.run = _run_real
print(f"\nestado temporario: {TMP}")
print("TUDO OK" if not FALHAS else f"FALHAS: {FALHAS}")
sys.exit(1 if FALHAS else 0)
