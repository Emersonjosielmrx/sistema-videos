"""Claude Code (CLI) com o Argon (ou um híbrido argon-*) pelo proxy de ferramentas: tem que rodar, ler, editar e testar sozinho.
    python teste_tools_rodar.py [base_url] [modelo]
Cada modelo trabalha numa cópia própria de teste_tools (com os bugs), então dá para rodar vários ao mesmo tempo."""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"D:\claude-code-video")
import motor

base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:20199"
modelo = sys.argv[2] if len(sys.argv) > 2 else "gemini-4-argon"
cfg = Path(r"C:\Users\Haylla\Desktop\Claude VS Code - Trocar Modelo\settings_1_OPUS-4.6_ANTIGRAVITY.json").read_text("utf-8")
chave = re.search(r'"ANTHROPIC_AUTH_TOKEN", "value": "([^"]+)"', cfg).group(1)

BUGADO = '''def media_movel(valores, janela):
    """Média móvel simples: uma média para cada posição onde a janela inteira cabe."""
    saida = []
    for i in range(len(valores) - janela):
        saida.append(sum(valores[i:i + janela]) / janela)
    return saida


def mediana(valores):
    v = sorted(valores)
    meio = len(v) // 2
    if len(v) % 2:
        return v[meio]
    return v[meio] + v[meio - 1] / 2
'''
pasta = Path(r"D:\gemini-argo\captura") / f"teste_tools_{modelo.replace('/', '_')}"
pasta.mkdir(exist_ok=True)
shutil.copy(Path(r"D:\gemini-argo\captura\teste_tools\test_calc.py"), pasta / "test_calc.py")
(pasta / "calc.py").write_text(BUGADO, "utf-8")

env = dict(os.environ, ANTHROPIC_BASE_URL=base, ANTHROPIC_AUTH_TOKEN=chave,
           ANTHROPIC_MODEL=modelo, ANTHROPIC_DEFAULT_OPUS_MODEL=modelo,
           ANTHROPIC_DEFAULT_SONNET_MODEL=modelo, ANTHROPIC_DEFAULT_HAIKU_MODEL="kr/claude-haiku-4.5",
           ANTHROPIC_SMALL_FAST_MODEL="kr/claude-haiku-4.5", CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
env.pop("ANTHROPIC_API_KEY", None)
prompt = (f"Na pasta {pasta} os testes de test_calc.py falham. Rode `python test_calc.py`, leia calc.py, ache e "
          "conserte os bugs em calc.py (não mexa no teste) e rode o teste de novo até imprimir TODOS OS TESTES PASSARAM.")
cmd = [motor._exe(), "-p", "--output-format", "json", "--max-turns", "15", "--setting-sources", "project",
       "--allowedTools", "Read,Edit,Write,Bash,Glob,Grep", "--disallowedTools", "WebFetch,WebSearch,Agent"]
t0 = time.time()
p = subprocess.run(cmd, cwd=pasta, env=env, input=prompt.encode("utf-8"), capture_output=True, timeout=900)
cod, saida = p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")
print(f"[{modelo}] tempo {time.time() - t0:.0f}s, código {cod}")
for linha in reversed(saida.strip().splitlines()):
    if linha.startswith("{"):
        r = json.loads(linha)
        print("turnos:", r.get("num_turns"), "| erro:", r.get("is_error"), "| resposta:", str(r.get("result"))[:400])
        break
else:
    print(saida[-1500:])
r = subprocess.run([sys.executable, "test_calc.py"], cwd=pasta, capture_output=True, text=True)
print("CONFERÊNCIA INDEPENDENTE:", (r.stdout + r.stderr).strip()[-300:])
