# -*- coding: utf-8 -*-
"""🎙️ Narrador grátis sem chave: GET /webhook/gratis-voz (página) e POST /webhook/gratis-voz (devolve o MP3)."""
import sys
from pathlib import Path

AQUI = Path(__file__).parent
COMUM = AQUI.parent / "comum"
sys.path.insert(0, str(AQUI.parent))
from n8nlib import Fluxo, js  # noqa: E402

ler = lambda n: (COMUM / n).read_text(encoding="utf-8")  # noqa: E731
f = Fluxo("🎙️ Narrador grátis sem chave (voz neural do Bing, Google de reserva)")

f.nota("## 🎙️ Narrador grátis\nAbra **/webhook/gratis-voz** no navegador: escreve o texto, escolhe a voz e baixa o MP3.\n\n"
       "Outros fluxos: **POST /webhook/gratis-voz** com `{\"texto\":\"...\",\"voz\":\"thalita\",\"velocidade\":0}`.\n\n"
       "Sem chave e sem instalar nada: a voz neural vem da página pública do Bing Tradutor; se ela falhar, usa a do "
       "Google Tradutor. Vozes (só as Multilingual aprovadas): thalita, andrew, brian, emma; e google.",
       (-40, -360), 520, 300, 4)
g = f.webhook("🔔 Página do narrador (GET)", "gratis-voz", (0, 0))
p = f.codigo("🧩 Monta a página", js(AQUI, "pagina.js", PAGINA=ler("pagina.js")), (240, 0))
rp = f.responde("📤 Entrega a página", "={{ $json.html }}", (480, 0))
f.cadeia(g, p, rp)

w = f.webhook("🔔 Pedido de voz (POST)", "gratis-voz", (0, 260), "POST")
n = f.codigo("🎙️ Narra (Bing → Google)", js(AQUI, "narra.js", VOZ=ler("voz.js")), (240, 260))
s = f.se("🚦 Saiu o áudio?", "={{ $json.ok }}", (480, 260))
a = f.responde_arquivo("📤 Entrega o MP3", (720, 180), cache="no-store", cabecalhos={
    "X-Motor": "={{ $json.motor }}", "X-Segundos": "={{ $json.segundos }}", "X-Aviso": "={{ $json.aviso }}"})
e = f.responde_json("📤 Responde o erro", "{ ok: false, erro: $json.erro }", (720, 360), status=503)
f.cadeia(w, n, s)
f.liga(s, a, 0)
f.liga(s, e, 1)
print(f.grava(AQUI / "narrador_gratis.json"))
