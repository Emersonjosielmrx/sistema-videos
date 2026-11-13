"""Teste de bases diferentes (Francisca, Antonio, Thalita) com voz clonada mike."""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import edge_tts_engine

VOZES_PY = Path(r"D:\hipercool-materiais\python\venv_vozes\Scripts\python.exe")
VOZ_CLONADA_PY = Path(r"D:\hipercool-materiais\bin\voz_clonada.py")
RAIZ = Path(__file__).parent
SAIDA = RAIZ / "saida"
SAIDA.mkdir(exist_ok=True)

BASES = {
    "francisca": "pt-BR-FranciscaNeural",
    "antonio": "pt-BR-AntonioNeural",
    "thalita": "pt-BR-ThalitaMultilingualNeural"
}

frases = (RAIZ / "frases.txt").read_text(encoding="utf-8").strip()
print(f"Texto: {len(frases.split())} palavras\n")
print(f"Gerando 3 bases + 3 clones com voz mike")
print(f"Bases: {list(BASES.keys())}\n")

itens_lote = []

for nome, voz_edge in BASES.items():
    print(f"=== {nome} ({voz_edge}) ===")

    # 1. Gerar base com edge
    base_wav = SAIDA / f"{nome}_base.wav"
    if not edge_tts_engine.speak(frases, voice=voz_edge, out_wav=str(base_wav),
                                  persona="Narrador", rate="-5%", pitch="+0Hz"):
        print(f"  ERRO: edge_tts falhou")
        continue
    print(f"  Base: {base_wav.name} ({base_wav.stat().st_size // 1024} KB)")

    # 2. Preparar item para lote RVC
    saida_clone = SAIDA / f"{nome}_mike.wav"
    itens_lote.append({
        "saida": str(saida_clone),
        "tom_base": "2_edge_francisca",
        "entrada": str(base_wav),
        "tom_extra": 0,
        "index_rate": 0.5,
        "protect": 0.33,
        "volume_envelope": 1.0
    })

# 3. Aplicar RVC em lote (todas as 3 de uma vez)
print(f"\n=== Aplicando RVC mike (lote de {len(itens_lote)}) ===")
lista_json = SAIDA / "_lista_lote.json"
lista_json.write_text(json.dumps(itens_lote, ensure_ascii=False), encoding="utf-8")

log_file = SAIDA / "_clone.log"
with open(log_file, "w", encoding="utf-8") as fh:
    r = subprocess.run(
        [str(VOZES_PY), str(VOZ_CLONADA_PY), "lote", "mike", str(lista_json)],
        stdout=fh, stderr=subprocess.STDOUT, timeout=600,
        creationflags=0x00004000 | 0x08000000
    )

if r.returncode != 0:
    print(f"ERRO: voz_clonada falhou (rc={r.returncode})")
    print(f"Ver log: {log_file}")
    sys.exit(1)

# 4. Verificar resultados
print("\n=== Resultados ===")
gerados = []
for item in itens_lote:
    p = Path(item["saida"])
    if p.exists():
        print(f"  ✓ {p.name} ({p.stat().st_size // 1024} KB)")
        gerados.append(p.name)
    else:
        print(f"  ✗ {p.name} (faltando)")

print(f"\nTotal: {len(gerados)}/3 clones + 3 bases = 6 arquivos")
print(f"Pasta: {SAIDA}")

# 5. Abrir pasta no Explorer
print("\nAbrindo pasta no Explorer...")
subprocess.run(["explorer.exe", str(SAIDA)], shell=True)
