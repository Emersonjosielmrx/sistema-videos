"""Teste a seco do motor das melhorias com todas as camadas (24/10): busca em dupla com votante C, executor,
críticos do plano, 3 revisores com ANÁLISE obrigatória, refazer com crítica, e a 3ª camada (auditoria final) com um
juiz falso. Não chama IA nenhuma nem toca no estado real (tudo em pasta temporária).
Rodar: D:\\veo\\venv\\Scripts\\python.exe D:\\video-fila\\testes\\teste_motor_camadas.py
"""
import json
import sys
import tempfile
import time
import types
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, r"D:\video-fila")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import melhoria_continua as m  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="teste_camadas_"))
m.BACKLOG, m.ESTADO, m.HISTORICO, m.LICOES, m.LOG, m.CONFIG = (tmp / "bl.json", tmp / "e.json", tmp / "h.md",
                                                               tmp / "l.md", tmp / "x.log", tmp / "c.json")
m.pacote_revisao = lambda e=None: 0
avisos = []
m._avisar = lambda t: avisos.append(t)
m._comecar_vigia = lambda e, j: None
m._recentes = lambda p, **k: "- nada"
m._consertos_recentes = lambda *a, **k: "- nada"
m._ram_gb = lambda: 99.0
m._modo = lambda: ("principal", "x")
m._avisar_modo = lambda *a: None
m._vigiar_producao = lambda e: False
m._quebrados = lambda j: []

# ─── painel_ia falso ─────────────────────────────────────────────────────────────────────────────────────────────
jobs, desfeitos, n = {}, [], [0]
pi = types.ModuleType("painel_ia")
pi.PROJETOS = {"cortes": ("Cortes", str(tmp)), "geral": ("Geral", str(tmp))}


def _novo(tipo, **kw):
    n[0] += 1
    j = {"id": f"j{n[0]:02d}", "tipo": tipo, "status": "fila", "criado": datetime.now().isoformat(timespec="seconds"),
         "resposta": "", "status_ia": None, "detalhe": None, "passos": []}
    j.update(kw)
    jobs[j["id"]] = j
    return j


def pedir(tipo, pedido, projeto="geral", contexto="", origem="painel", auto_aplicar=False, modelo=None, voltas=None,
          pensar=False):
    assert len(pedido) <= 4000, f"pedido de {len(pedido)} caracteres seria cortado"
    assert len(contexto) <= 6000, f"contexto de {len(contexto)}"
    return _novo(tipo, pedido=pedido, contexto=contexto, projeto=projeto, origem=origem, modelo_fixo=modelo,
                 voltas_max=voltas, pensar=pensar)


arq = tmp / "codigo.py"
arq.write_text("x = 1\n", encoding="utf-8")
bk = tmp / "codigo_backup.py"
bk.write_text("x = 1\n", encoding="utf-8")


def aplicar(jid):
    arq.write_text("x = 2  # mudou\n", encoding="utf-8")
    return _novo("aplicar", pai=jid, projeto=jobs[jid]["projeto"], origem="painel",
                 manifesto={str(arq): {"backup": str(bk), "existia": True}}, modelo="kr/claude-sonnet-4.5")


def desfazer(jid, forcar=False, quem="painel"):
    desfeitos.append(jid)
    jobs[jid]["desfeito_em"] = datetime.now().isoformat()


pi.pedir, pi.aplicar, pi.desfazer = pedir, aplicar, desfazer
pi.ler = lambda jid: jobs.get(jid)
pi.todos = lambda: list(jobs.values())
pi._travas_ocupadas = lambda: False
pi.mudancas = lambda jid: [{"arquivo": str(arq), "diff": "-x = 1\n+x = 2  # mudou", "mudou_depois": False}]
pi.conversa = lambda jid, limite=500: ([{"quem": "ferramenta", "texto": "rodando python -m py_compile codigo.py",
                                         "detalhe": "python -m py_compile codigo.py"},
                                        {"quem": "resultado", "texto": "", "erro": False}] if jid in jobs else [])
pi._sha = lambda p: "x"
pi._gravar = lambda j: jobs.__setitem__(j["id"], j)
sys.modules["painel_ia"] = pi
ir = types.ModuleType("ia_reserva")
ir.falha_de_modelo = lambda t: "API Error" in t
ir.eh_reserva = lambda mo: False
ir.marcar = lambda *a: None
sys.modules["ia_reserva"] = ir

# ─── juiz falso (camada_opus) e monitor falso ───────────────────────────────────────────────────────────────────
co = types.ModuleType("camada_opus")
co.estado = {"desligada": False, "vivo": None}
co.desligada = lambda: co.estado["desligada"]
co.lote_vivo = lambda: co.estado["vivo"]


def _extrair(texto):
    import re
    out = []
    for b in re.findall(r"<<<AUDITORIA\s*(.*?)\s*AUDITORIA>>>", texto or "", re.S):
        try:
            out.append(json.loads(b))
        except ValueError:
            pass
    return out


co.extrair_vereditos = _extrair
co.ligar = lambda: "ligada"
co.desligar = lambda: "desligada"
sys.modules["camada_opus"] = co
import auditoria_final as af  # noqa: E402

af.PASTA, af.DOCS = tmp / "opus", tmp / "docs"
af.INDICE = af.DOCS / "INDICE.md"
af.MONITOR = tmp / "monitor.json"
af.VSCODE_PROJETOS = tmp / "vscode"
disparos = []


class _Popen:
    def __init__(self, cmd, **kw):
        disparos.append(cmd)


af.subprocess = types.SimpleNamespace(Popen=_Popen, DEVNULL=None)


def monitor(com_credito, funcionando=True, idade_min=1):
    em = (datetime.now().astimezone() - timedelta(minutes=idade_min)).isoformat(timespec="seconds")
    af.MONITOR.write_text(json.dumps({"funcionando": funcionando, "leitura": {"em": em, "contas": 87,
                                                                           "com_credito": com_credito}}),
                          encoding="utf-8")


m._gravar(m.CONFIG, {"ligado": True, "projetos": ["cortes"], "pausa_min": 0, "opus_lote_espera_min": 0})


def termina(jid, **kw):
    jobs[jid].update(dict({"status": "terminou", "fim": datetime.now().isoformat(timespec="seconds")}, **kw))


def J():
    return jobs[m._estado()["atual"]]


def papel():
    e = m._estado()
    return e["papeis"].get(e["atual"]) or {}


ANAL = "ANÁLISE:\n1 ok\n2 ok\n3 ok\n4 ok\n5 ok\n6 ok\n7 ok\n8 ok\n"
G = "agy/gemini-3.8-flash-high"
monitor(0)

# 1) busca: A acha 2; B (Gemini) não responde; C (Kiro adversário) vota no lugar; A vota nos do B (nenhum)
m.passo()
assert papel() == {"papel": "buscador", "projeto": "cortes", "lado": "A"} and J()["pensar"] is True, papel()
termina(J()["id"], resposta='<<<BACKLOG\n[{"titulo":"Erro X","impacto":5,"risco":1},'
                            '{"titulo":"Coisa Y","impacto":3,"risco":1}]\nBACKLOG>>>')
m.passo()
assert papel()["lado"] == "B" and J()["modelo_fixo"] == G and J()["pensar"] is False
termina(J()["id"], resposta="API Error: max turns")
m.passo()
assert papel() == {"papel": "votante", "projeto": "cortes", "lado": "B"}
termina(J()["id"], resposta="não votei")
m.passo()
assert papel()["lado"] == "C" and J()["pensar"] is True and "LIÇÕES" in J()["contexto"], papel()
termina(J()["id"], resposta='<<<VOTOS\n[{"n":1,"concordo":true},{"n":2,"concordo":true}]\nVOTOS>>>')
m.passo()
# 2) executor: pedido fixo + item/lições no contexto, com PROIBIDO e CHECK no pedido
assert J()["tipo"] == "propor" and "PROIBIDO" in J()["pedido"] and "CHECK" in J()["pedido"], J()["pedido"][:300]
assert "Erro X" in J()["contexto"] and "LIÇÕES" in J()["contexto"] and J()["pensar"] is True
prop = J()["id"]
termina(prop, status_ia="PROPOSTA", resposta=ANAL + "PLANO: mudar x\nSTATUS: PROPOSTA - mudar x")
# 3) crítico B reprova o plano -> nada aplicado; refaz o plano com a crítica
m.passo()
assert papel() == {"papel": "critico", "proposta": prop, "lado": "B"} and J()["modelo_fixo"] == G
termina(J()["id"], resposta=ANAL + "VEREDITO: REPROVADO - a prova é de ontem\nSTATUS: OK")
m.passo()
assert J()["tipo"] == "propor" and "a prova é de ontem" in J()["contexto"], J()["contexto"][:500]
assert not [j for j in jobs.values() if j["tipo"] == "aplicar"], "não podia ter aplicado"
prop2 = J()["id"]
termina(prop2, status_ia="PROPOSTA", resposta=ANAL + "STATUS: PROPOSTA - mudar x direito")
# 4) crítico B aprova SEM ANÁLISE (não vale) -> crítico A aprova com ANÁLISE -> aplica
m.passo()
termina(J()["id"], resposta="VEREDITO: APROVADO - ok\nSTATUS: OK")
m.passo()
assert papel()["papel"] == "critico" and papel()["lado"] == "A" and J()["pensar"] is True
termina(J()["id"], resposta=ANAL + "VEREDITO: APROVADO - ok\nSTATUS: OK")
m.passo()
ap = J()
assert ap["tipo"] == "aplicar", ap
termina(ap["id"], status_ia="CONSERTEI", detalhe="mudei x", resposta="STATUS: CONSERTEI - mudei x")
# 5) revisores B, C, A (todos aprovam com ANÁLISE) -> aceito -> fila da auditoria
lados = []
for _ in range(3):
    m.passo()
    lados.append(papel()["lado"])
    assert "COMANDOS QUE A APLICAÇÃO RODOU" in J()["contexto"] and "py_compile" in J()["contexto"]
    termina(J()["id"], resposta=ANAL + "VEREDITO: APROVADO - certo\nSTATUS: OK")
assert lados == ["B", "C", "A"], lados
assert "VOCÊ É O REVISOR ADVERSÁRIO" in [j for j in jobs.values() if j.get("pedido", "").startswith("MELHORIA CONTÍNUA — você é o REVISOR")][1]["pedido"]
m.passo()
e = m._estado()
ent = e["auditar"].get(ap["id"])
assert ent and ent["estado"] == "pendente" and ent["revisores"]["C"][0] == "APROVADO", ent
print("prioridade:", ent["prio"], ent["motivos"])
# 6) auditoria: 0 contas -> não dispara; 3 contas -> dispara lote (o executor da próxima rodada está na fila)
m.passo()
e = m._estado()
assert not disparos and "preciso de 3" in e["opus"]["espera"], e["opus"]["espera"]
monitor(3)
m.passo()
assert len(disparos) == 1 and "lote" in disparos[0], disparos
e = m._estado()
lid = e["opus"]["lote"]["id"]
ped = json.loads((af.PASTA / f"{lid}_pedido.json").read_text(encoding="utf-8"))
dos = Path(ped["dossie"]).read_text(encoding="utf-8")
assert ap["id"] in dos and "AGORA:" in dos and "DIFF" in dos and ped["exigir_modelo"] == "opus-4-6"
# o juiz devolve DESFAZER com prova e confiança 4
(af.PASTA / f"{lid}.json").write_text(json.dumps({"status": "terminou", "tokens_in": 9000, "tokens_out": 800,
    "vereditos": [{"job": ap["id"], "veredito": "DESFAZER", "por_que": "tirou a trava", "prova": "+x = 2",
                   "confianca": 4, "licao": "não tire travas sem medir"}]}), encoding="utf-8")
m.passo()
e = m._estado()
assert ap["id"] in desfeitos and e["auditar"][ap["id"]]["estado"] == "feito", (desfeitos, e["auditar"][ap["id"]])
assert "não tire travas" in m._licoes(20000) and af.INDICE.exists() and "AUDITORIA OPUS" in m.HISTORICO.read_text(encoding="utf-8")
assert e["opus"]["tokens"] == 9800 and e["opus"]["placar"]["kr/claude-sonnet-4.5"]["derrubado"] == 1
assert any("Auditoria final" in a for a in avisos), avisos
# 7) DESFAZER sem prova -> vai pra dona (nunca desfaz sozinho); queda do processo -> reaproveita o .txt
ap2 = aplicar(prop2)
termina(ap2["id"], status_ia="CONSERTEI", resposta="STATUS: CONSERTEI - y")
af.enfileirar(e, m.cfg(), ap2, "teste", {}, None)
ap3 = aplicar(prop2)
termina(ap3["id"], status_ia="CONSERTEI", resposta="STATUS: CONSERTEI - z")
af.enfileirar(e, m.cfg(), ap3, "teste", {}, None)
e["auditar"][ap2["id"]]["prio"] = e["auditar"][ap3["id"]]["prio"] = 0
e["opus"]["horas"] = []
m._gravar(m.ESTADO, e)
m.passo()
e = m._estado()
lid2 = e["opus"]["lote"]["id"]
assert lid2 != lid
(af.PASTA / f"{lid2}.txt").write_text('<<<AUDITORIA {"job": "%s", "veredito": "DESFAZER", "por_que": "acho", '
                                       '"prova": "", "confianca": 2} AUDITORIA>>> e caiu aqui...' % ap2["id"],
                                       encoding="utf-8")
e["opus"]["lote"]["inicio"] = time.time() - 600  # processo "morreu" sem .json
m._gravar(m.ESTADO, e)
m.passo()
e = m._estado()
assert e["auditar"][ap2["id"]]["estado"] == "dona" and ap2["id"] not in desfeitos, e["auditar"][ap2["id"]]
assert e["auditar"][ap3["id"]]["estado"] == "pendente" and e["auditar"][ap3["id"]]["tentativas"] == 1
assert e["opus"]["fora_ate"] > time.time() and ap2["id"] in e["entregar"]
txt = m.texto_entrega(jobs[ap2["id"]])
assert "Auditoria final" in txt and "DESFAZER" in txt, txt
# 8) botão desligado e dona usando o Opus
co.estado["desligada"] = True
assert af.disponivel(m.cfg(), m._estado()) == (False, "desligada pelo botão da área de trabalho")
co.estado["desligada"] = False
e = m._estado()
e["opus"]["fora_ate"], e["opus"]["fora_desde_leitura"] = 0, None
m._gravar(m.ESTADO, e)
(af.VSCODE_PROJETOS / "p").mkdir(parents=True)
(af.VSCODE_PROJETOS / "p" / "s.jsonl").write_text('{"message":{"model":"antigravity/claude-opus-4-6-thinking"}}\n',
                                                   encoding="utf-8")
ok, mot = af.disponivel(m.cfg(), m._estado())
assert not ok and "preciso de 8" in mot, mot
monitor(9)
assert af.disponivel(m.cfg(), m._estado())[0]
monitor(9, idade_min=40)
assert "velha" in af.disponivel(m.cfg(), m._estado())[1]
print(m.status())
print("\nTUDO OK —", len(jobs), "pedidos falsos; avisos:", len(avisos))
