# -*- coding: utf-8 -*-
"""Fluxo de teste: o que o nó Code do n8n deixa usar (WebSocket, crypto, tempo máximo) e a voz neural do Edge.
GET /webhook/gratis-teste-recursos?edge=1&dormir=0&audio=0"""
import sys
from pathlib import Path

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parent))
from n8nlib import Fluxo, js  # noqa: E402

f = Fluxo("🧪 Teste de recursos do Code (grátis sem chave) — pode desligar")
w = f.webhook("🔔 Teste (GET)", "gratis-teste-recursos", (0, 0))
c = f.codigo("🧩 Testa", js(AQUI, "teste.js", VOZ_EDGE=(AQUI.parent / "comum" / "voz_edge.js").read_text(encoding="utf-8")), (240, 0))
s = f.se("🚦 Veio áudio?", "={{ !!$binary.data }}", (480, 0))
a = f.responde_arquivo("📤 Entrega o áudio", (720, -100), cache="no-store")
r = f.responde_json("📤 Entrega o resultado", "$json", (720, 100))
f.cadeia(w, c, s)
f.liga(s, a, 0)
f.liga(s, r, 1)
print(f.grava(AQUI / "teste_recursos.json"))
