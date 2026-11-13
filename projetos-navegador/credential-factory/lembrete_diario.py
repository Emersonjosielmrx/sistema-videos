"""Hook UserPromptSubmit (todas as conversas): lembrete diário da fábrica de credenciais até 29/10/2026, a partir
das 17:50. Some no dia em que o robô rodou (o registro dele muda de data); depois de 29/10 não faz nada."""
import json
from datetime import date, datetime, time
from pathlib import Path

FIM = date(2026, 10, 29)
A_PARTIR_DE = time(17, 50)
DIR = Path(r"D:\projetos-navegador\credential-factory")
TAREFAS = [
    # Groq saiu em 25/10 (dono): o Groq passou a bloquear quase toda organização nova destas contas
    # SightEngine saiu em 25/10 à noite (dono: "usei, retire os avisos, não precisamos mais")
]


def _hoje(nome):
    try:
        return date.fromtimestamp((DIR / nome).stat().st_mtime) == date.today()
    except OSError:
        return False


if date.today() <= FIM and datetime.now().time() >= A_PARTIR_DE:
    falta = [txt for arq, txt in TAREFAS if not _hoje(arq)]
    if falta:
        aviso = ("LEMBRETE DIÁRIO pedido pelo dono (até 29/10/2026). No FINAL da sua resposta, acrescente um "
                 "lembrete curto, em linhas separadas, só destes itens que ainda não foram feitos hoje:\n- "
                 + "\n- ".join(falta))
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": aviso}}))
