from pathlib import Path
p = Path(__file__).parent / "gera.py"; t = p.read_text(encoding="utf-8")
t = t.replace('"SELECT ig_api($1::jsonb) AS r"', '"SELECT ig_api2($1::jsonb) AS r"')
if "gincana_encerrar" not in t:
    t = t.replace('''    ("gincana_pistas", "={{ $json.r && $json.r.ia === 'gincana_pistas' }}"),
], [640, -380])''', '''    ("gincana_pistas", "={{ $json.r && $json.r.ia === 'gincana_pistas' }}"),
    ("gincana_encerrar", "={{ $json.r && $json.r.ia === 'gincana_encerrar' }}"),
    ("sorteio_anunciar", "={{ $json.r && $json.r.ia === 'sorteio_anunciar' }}"),
], [640, -380])''')
    t = t.replace('[900, -640]), saida=4)', '[900, -640]), saida=6)')
    t = t.replace("""$json.error ? String($json.error.message || $json.error).slice(0, 200) : ''] }}", [1540, 920])""",
                  """$json.error ? String($json.error.message || $json.error).slice(0, 200) : ($json.message_id || $json.id || $json.recipient_id ? '' : 'sem confirmação do Instagram')] }}", [1540, 920])""")
    t = t.replace('out = grava(f, AQUI, "insta.json")',
                  'from gera_extra import blocos\nblocos(f, sw, ig, postgres, CX, OFICINA, PUB)\nout = grava(f, AQUI, "insta.json")')
p.write_text(t, encoding="utf-8")
print("saida=6" in t, "gera_extra" in t, "sem confirmação" in t)
