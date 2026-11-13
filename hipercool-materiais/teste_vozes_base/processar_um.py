"""Processa os narradores restantes um por um."""
import json
import subprocess
import sys
from pathlib import Path

VOZES_PY = Path(r"D:\hipercool-materiais\python\venv_vozes\Scripts\python.exe")
VOZ_CLONADA_PY = Path(r"D:\hipercool-materiais\bin\voz_clonada.py")
VOZES_DIR = Path(r"D:\hipercool-materiais\models\rvc\vozes")
RAIZ = Path(__file__).parent
SAIDA = RAIZ / "saida_todos"

# Descobrir todos os narradores
narradores = []
for item in VOZES_DIR.iterdir():
    if item.is_dir() and not item.name.startswith("_"):
        model_file = item / f"{item.name}.pth"
        if model_file.exists():
            narradores.append(item.name)

narradores.sort()

# Bases
base_francisca = SAIDA / "_base_francisca.wav"
base_antonio = SAIDA / "_base_antonio.wav"

if not base_francisca.exists() or not base_antonio.exists():
    print("ERRO: bases não existem")
    sys.exit(1)

# Verificar quais narradores já foram processados
concluidos = set()
for narrador in narradores:
    f_wav = SAIDA / f"{narrador}_francisca.wav"
    a_wav = SAIDA / f"{narrador}_antonio.wav"
    if f_wav.exists() and a_wav.exists() and f_wav.stat().st_size > 500 and a_wav.stat().st_size > 500:
        concluidos.add(narrador)

pendentes = [n for n in narradores if n not in concluidos]

print(f"Total: {len(narradores)} narradores")
print(f"Concluídos: {len(concluidos)}")
print(f"Pendentes: {len(pendentes)}")

if not pendentes:
    print("\nTodos já processados!")
    sys.exit(0)

print(f"\nProcessando {len(pendentes)} narradores pendentes:")
for n in pendentes:
    print(f"  - {n}")

# Processar um narrador passado como argumento
if len(sys.argv) > 1:
    narrador = sys.argv[1]
    if narrador not in pendentes:
        print(f"Narrador {narrador} já processado ou não existe")
        sys.exit(0)

    print(f"\n=== Processando {narrador} ===")

    # Preparar lote de 2 bases
    itens = [
        {
            "saida": str(SAIDA / f"{narrador}_francisca.wav"),
            "tom_base": "2_edge_francisca",
            "entrada": str(base_francisca),
            "tom_extra": 0,
            "index_rate": 0.5,
            "protect": 0.33,
            "volume_envelope": 1.0
        },
        {
            "saida": str(SAIDA / f"{narrador}_antonio.wav"),
            "tom_base": "2_edge_francisca",
            "entrada": str(base_antonio),
            "tom_extra": 0,
            "index_rate": 0.5,
            "protect": 0.33,
            "volume_envelope": 1.0
        }
    ]

    lista_json = SAIDA / f"_lista_{narrador}.json"
    lista_json.write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")

    log_file = SAIDA / f"_clone_{narrador}.log"
    with open(log_file, "w", encoding="utf-8") as fh:
        r = subprocess.run(
            [str(VOZES_PY), str(VOZ_CLONADA_PY), "lote", narrador, str(lista_json)],
            stdout=fh, stderr=subprocess.STDOUT, timeout=600,
            creationflags=0x00004000 | 0x08000000
        )

    if r.returncode != 0:
        print(f"ERRO: voz_clonada falhou (rc={r.returncode}), ver {log_file}")
        sys.exit(1)

    # Verificar
    for item in itens:
        p = Path(item["saida"])
        if p.exists():
            print(f"OK {p.name} ({p.stat().st_size // 1024} KB)")
        else:
            print(f"FALTA {p.name}")
            sys.exit(1)

    print(f"\n{narrador} concluído!")
else:
    print("\nUso: python processar_um.py <narrador>")
    print("Pendentes:", ", ".join(pendentes))
