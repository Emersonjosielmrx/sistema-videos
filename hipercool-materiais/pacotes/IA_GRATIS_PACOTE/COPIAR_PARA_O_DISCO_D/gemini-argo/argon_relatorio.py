#!/usr/bin/env python3
r"""Resumo do monitoramento do Argon com ferramentas (turnos gravados pelo proxy da VPS em argon_turnos.jsonl).
Mostra onde ele mais erra, para melhorar o proxy/instrução.
    python -X utf8 D:\gemini-argo\argon_relatorio.py [horas=24]
"""
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

# 30/10: o "ssh" do PATH é o OpenSSH do Windows, que travava até o timeout (o argon_manter já usava o do Git); e só o
# fim do arquivo vem (antes o cat trazia o histórico inteiro a cada relatório)
SSH = r"C:\Program Files\Git\usr\bin\ssh.exe" if os.path.exists(r"C:\Program Files\Git\usr\bin\ssh.exe") else "ssh"
horas = float(sys.argv[1]) if len(sys.argv) > 1 else 24
bruto = subprocess.run([SSH, "-n", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "LogLevel=ERROR", "hermes-bloqueio",
                        "tail -n 20000 /opt/antigravity-cc-proxy/argon_turnos.jsonl 2>/dev/null"],
                       capture_output=True, text=True, encoding="utf-8", timeout=120).stdout
desde = datetime.now(timezone.utc) - timedelta(hours=horas)
turnos = []
for linha in bruto.splitlines():
    try:
        t = json.loads(linha)
    except ValueError:
        continue
    if datetime.fromisoformat(t["ts"].replace("Z", "+00:00")) >= desde:
        turnos.append(t)
if not turnos:
    sys.exit(f"nenhum turno nas últimas {horas:g} h")

n = len(turnos)
erros = [t for t in turnos if t.get("erro")]
ok = [t for t in turnos if not t.get("erro")]
so_texto = [t for t in ok if t.get("so_texto")]
perdidos = [t for t in ok if t.get("blocos_perdidos", 0) > 0]
refeitos = Counter(t["refeito"] for t in ok if t.get("refeito"))
falhas_ferr = Counter(e["ferramenta"] for t in turnos for e in t.get("ferramentas_anteriores_com_erro", []))
chamadas = Counter(c for t in ok for c in t.get("chamadas", []))
ms = sorted(t["ms"] for t in ok if t.get("ms"))
pct = lambda x: f"{100 * x / n:.0f}%"  # noqa: E731

print(f"Argon com ferramentas — últimas {horas:g} h: {n} turnos")
print(f"  erro do Argon (sem cota, queda, timeout): {len(erros)} ({pct(len(erros))})")
for msg, q in Counter(t["erro"][:70] for t in erros).most_common(5):
    print(f"      {q}x {msg}")
print(f"  só texto (sem chamar ferramenta): {len(so_texto)} ({pct(len(so_texto))})  — inclui as respostas finais legítimas")
print(f"  bloco tool_call ilegível (chamada perdida): {len(perdidos)} ({pct(len(perdidos))})")
print(f"  pedidos de novo: {dict(refeitos) or '-'}")
if ms:
    print(f"  tempo por turno: mediana {ms[len(ms) // 2] / 1000:.0f} s, p90 {ms[int(len(ms) * .9)] / 1000:.0f} s")
print(f"  ferramentas mais chamadas: {chamadas.most_common(8)}")
print(f"  ferramentas que voltaram com ERRO depois da chamada dele: {falhas_ferr.most_common(8) or '-'}")
exemplos = [e for t in turnos for e in t.get("ferramentas_anteriores_com_erro", [])][-5:]
for e in exemplos:
    print(f"      {e['ferramenta']}: {' '.join(e['erro'].split())[:150]}")

print("\nO que melhorar:")
if len(perdidos) > 0.03 * n:
    print("  - muitas chamadas perdidas: ver o texto dos blocos e afrouxar o extrairChamadas / reforçar o formato na instrução")
if falhas_ferr:
    f, q = falhas_ferr.most_common(1)[0]
    print(f"  - {f} falha {q}x: pôr na instrucaoFerramentas a regra que ele erra (ex.: Edit exige old_string exato e Read antes)")
if len(erros) > 0.1 * n:
    print("  - muitos erros do Argon: faltam contas com cota (classificar_pro.py) ou o túnel/proxy local caiu")
if ms and ms[len(ms) // 2] > 60000:
    print("  - turnos lentos: contas sobrecarregadas ou prompts enormes (contexto sem compactar)")
