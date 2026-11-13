#!/usr/bin/env python3
"""Roda NA VPS em /opt/antigravity-cc-proxy. Liga o visao.mjs no proxy.mjs (backup: proxy.mjs.bak_antes_imagem_29out).
Desfazer: cp proxy.mjs.bak_antes_imagem_29out proxy.mjs && systemctl restart antigravity-cc-proxy"""
p = "proxy.mjs"
s = open(p, encoding="utf-8").read()
if "visao.mjs" in s:
    raise SystemExit("ja ligado")
a = 'import fs from "node:fs";\n'
assert a in s
s = s.replace(a, a + 'import { precisaOlhos, temImagem, descreverImagens } from "./visao.mjs";\n', 1)
velho = ('  req.on("end", () => {\n    let buf = Buffer.concat(chunks);\n    try {\n'
         '      const j = JSON.parse(buf.toString("utf8"));\n')
assert s.count(velho) == 1, s.count(velho)
novo = ('  req.on("end", async () => {\n    let buf = Buffer.concat(chunks);\n    try {\n'
        '      const j = JSON.parse(buf.toString("utf8"));\n'
        '      // 2026-10-29: Sonnet web (cw/ e sonnet-fila) e Argon nao recebem imagem -> o Gemini descreve (visao.mjs)\n'
        '      if (precisaOlhos(j.model) && temImagem(j)) {\n'
        '        try {\n'
        '          await descreverImagens(j, req.headers, (m) => console.log(new Date().toISOString(), j.model + ": " + m));\n'
        '          buf = Buffer.from(JSON.stringify(j));\n'
        '        } catch (e) { console.log(new Date().toISOString(), "visao falhou: " + e.message); }\n'
        '      }\n')
s = s.replace(velho, novo, 1)
open(p, "w", encoding="utf-8").write(s)
print("ok")
