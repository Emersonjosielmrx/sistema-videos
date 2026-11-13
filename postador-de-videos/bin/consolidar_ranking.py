#!/usr/bin/env python3
"""Consolida dados OAuth + navegador para gerar ranking completo"""
import json
import re
from pathlib import Path

# Ler dados do navegador
navegador = json.loads(Path("stats_navegador_results.json").read_text(encoding="utf-8"))

# Parsear saída do OAuth
oauth_raw = Path("C:/Users/Haylla/.claude-vscode/projects/d--/d92ebfb3-8672-4436-8e0f-4060650ef0b7/tool-results/bbwd4alf4.txt").read_text(encoding="utf-8")

oauth = {}
# Padrão: "── <nome> — <N> video(s), <M> views totais ──"
for match in re.finditer(r"── (.+?) — (\d+) video\(s\), (\d+) views totais ──", oauth_raw):
    nome = match.group(1).strip()
    videos = int(match.group(2))
    views = int(match.group(3))
    oauth[nome] = {"views": views, "videos": videos}

# Combinar
todos = {}
for canal, dados in navegador.items():
    if dados["videos"] > 0:  # Ignorar Dorama vazio
        todos[canal] = {"views": dados["views"], "videos": dados["videos"], "metodo": "navegador"}

for canal, dados in oauth.items():
    todos[canal] = {"views": dados["views"], "videos": dados["videos"], "metodo": "oauth"}

# Salvar consolidado
Path("stats_consolidado.json").write_text(json.dumps(todos, indent=2, ensure_ascii=False), encoding="utf-8")

# Gerar ranking
ranking = sorted(todos.items(), key=lambda x: x[1]["views"], reverse=True)

total_views = sum(d["views"] for d in todos.values())
total_videos = sum(d["videos"] for d in todos.values())

print(f"\n{'='*80}")
print(f"RANKING CONSOLIDADO - {len(todos)} canais")
print(f"{'='*80}\n")

for i, (canal, dados) in enumerate(ranking, 1):
    media = dados["views"] // dados["videos"] if dados["videos"] > 0 else 0
    metodo = "🌐" if dados["metodo"] == "navegador" else "🔑"
    print(f"{i:2}. {canal:35} | {dados['views']:>8} views | {dados['videos']:>3} vídeos | {media:>5} média | {metodo}")

print(f"\n{'='*80}")
print(f"TOTAL: {total_views:,} views em {total_videos} vídeos")
print(f"MÉDIA GERAL: {total_views // total_videos if total_videos > 0 else 0} views/vídeo")
print(f"COBERTURA: {len(todos)} canais de 32 totais ({len(todos)*100//32}%)")
print(f"{'='*80}\n")
