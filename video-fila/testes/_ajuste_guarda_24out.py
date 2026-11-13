"""Ajuste único (24/10) do config\\melhoria_guarda.json: achados 14, 15, 18, 19 e 21. Rodar 1 vez."""
import json
from pathlib import Path

P = Path(r"D:\video-fila\config\melhoria_guarda.json")
g = json.loads(P.read_text(encoding="utf-8"))

# 15: os .jsonl do painel têm o conteúdo do cookies.txt
jsonl = r"(?#registro do painel com conteúdo de cookies)estado[\\/]+painel_ia[\\/]+[^\\/\s]*\.jsonl"
if jsonl not in g["segredos"]:
    g["segredos"].append(jsonl)

b = g["bloquear"]
# 21: lookaheads ancorados no começo (antes: O(n²), 60 KB = 153 s)
for i, r in enumerate(b):
    if r.startswith("(?#gravar por cima de mídia com .save/imwrite)(?=") :
        b[i] = r.replace("(?#gravar por cima de mídia com .save/imwrite)(?=",
                         "(?#gravar por cima de mídia com .save/imwrite)\\A(?=", 1)
    # 14: mais jeitos de ler variável de ambiente
    if r.startswith("(?#ler variáveis de ambiente"):
        extra = (r"|(?:/[cC]|-c)\s+['\"]?set\s*['\"]?\s*$|(?:^|[;&|({])\s*export\s*$|\bos\.getenv\b|\bos\.environ\b"
                 r"|GetEnvironmentVariables?\b|-Path\s+['\"]?Env:|\bprocess\.env\b|ANTHROPIC_AUTH_TOKEN")
        if "os\\.getenv" not in r:
            b[i] = r + extra

novas = [
    # 18: robocopy que move/espelha e git que apaga/volta arquivo
    r"(?#robocopy que move/espelha/apaga)\brobocopy\b[^\n]*\s/(?:MOVE?|MIR|PURGE)\b",
    r"(?#git que apaga/volta arquivo)\bgit\b[^\n]*\s(?:rm|mv|checkout\s+(?!-b)\S|restore|stash(?!\s+list))\b",
    # 19: porta lateral do painel (roda tarefa, muda controle, desfaz forçado)
    r"(?#ação no painel :8790 pelo terminal — só a dona clica)(?:127\.0\.0\.1|localhost):8790/api/"
    r"(?:tarefa_rodar|controle|ia_acao|ia_pedir|ia_corrigir_todos|abrir)\b|X-Painel",
    # 11: comando escondido em base64
    r"(?#comando escondido em base64)\s-(?:EncodedCommand|enc|ec|e)\s+[A-Za-z0-9+/=]{16,}",
]
for n in novas:
    if n not in b:
        b.append(n)

json.loads(json.dumps(g))
P.write_text(json.dumps(g, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("ok", len(g["segredos"]), len(b))
