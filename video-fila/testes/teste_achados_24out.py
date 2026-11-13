"""Testes das correções dos achados da revisão adversária (24/10). Rodar com D:\\veo\\venv\\Scripts\\python.exe."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, r"D:\video-fila")
import auditoria_final as af  # noqa: E402
import melhoria_continua as mc  # noqa: E402

FALHAS = []


def ok(cond, nome, extra=""):
    print(("  OK    " if cond else "  FALHA ") + nome + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FALHAS.append(nome)


tmp = Path(tempfile.mkdtemp(prefix="achados_"))
log = tmp / "logs" / "x.log"
log.parent.mkdir()
log.write_text("10:20 ERRO: caiu\n10:21 tudo bem\n", encoding="utf-8")

# achado 8: texto procurado com ':'
r = af._ler_trechos([f"log:{log}:ERRO: caiu"])
ok("10:20 ERRO: caiu" in r[0], "8: log:caminho:texto com ':' no texto", r[0][:200])
# achado 23: 'ver' que não é lista
ok(af._ler_trechos(None) == [] and af._ler_trechos({"a": 1}) == [], "23: 'ver' que não é lista não quebra")
ok(len(af._ler_trechos(f"log:{log}:tudo")) == 1, "23: 'ver' string vira lista de 1")
# achado 16: só manifesto/backups/logs; nunca o .jsonl do painel
outro = tmp / "outro.py"
outro.write_text("x = 1\n", encoding="utf-8")
r = af._ler_trechos([f"{outro}:1"], permitidos=[])
ok("recusado" in r[0], "16: arquivo fora do item é recusado", r[0])
r = af._ler_trechos([f"{outro}:1"], permitidos=[str(outro)])
ok("x = 1" in r[0], "16: arquivo do manifesto é lido", r[0])
ok(not af._pode_ler(r"D:\video-fila\estado\painel_ia\20261024_070109_172c.jsonl", []), "16: .jsonl do painel recusado")
cook = ".youtube.com\tTRUE\t/\tTRUE\t1790000000\tSID\tabcdef"
lim = af._limpo(f"linha boa\n{cook}\nBearer <SEGREDO_REMOVIDO>")
ok("SID" not in lim and "sk-ant" not in lim and "linha boa" in lim, "16: _limpo tira cookie e chave", lim)
ok("SID" not in mc._sem_segredo(cook) and "sk-ant" not in mc._sem_segredo("x <SEGREDO_REMOVIDO>"),
   "16: _sem_segredo dos comandos")

# achado 24: cota por item no dossiê
grande = "\n".join(f"+linha {i} " + "x" * 80 for i in range(3000))
orig_bloco, orig_ler = af._bloco_item, af.painel_ia_ler if hasattr(af, "painel_ia_ler") else None
import painel_ia  # noqa: E402
ler_orig = painel_ia.ler
painel_ia.ler = lambda jid: {"id": jid}
af._bloco_item = lambda n, ent, ap, c: (f"## ITEM {n}\n\nDIFF (1 arquivo):\n{grande}\n\nERROS NOVOS NOS LOGS DO PROJETO "
                                       f"DESDE A APLICAÇÃO:\nfim-{n}")
try:
    d = af.montar_dossie({}, {"opus_dossie_max_chars": 60000}, [{"job": f"j{i}"} for i in range(4)], "t")
finally:
    af._bloco_item = orig_bloco
    painel_ia.ler = ler_orig
ok(all(f"fim-{i}" in d for i in range(1, 5)), "24: os 4 itens mantêm os ERROS NOVOS")
ok("[CORTADO:" in d and len(d) <= 60000, f"24: diff cortado com aviso ({len(d)} caracteres)")

# achado 30/1: _para_dona com quem e enviado=False
e = {"auditoria_dona": {}, "entregar": []}
ent = {"job": "j1"}
af._para_dona(e, ent, {"veredito": "DONA"}, quem="auditoria reserva")
ok(e["auditoria_dona"]["j1"]["quem"] == "auditoria reserva" and e["auditoria_dona"]["j1"]["enviado"] is False
   and "quem" not in ent, "30/1: quem por parâmetro, enviado=False")

# achado 7: reserva parada com as melhorias desligadas
ok(af._reserva({"auditar": {}}, {"ligado": False, "opus_camada": True}) is False, "7: reserva não roda desligada")

print("\nTUDO OK" if not FALHAS else f"\n{len(FALHAS)} FALHA(S)")
sys.exit(1 if FALHAS else 0)
