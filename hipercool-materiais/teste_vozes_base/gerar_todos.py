"""Testa TODOS os narradores com bases Francisca vs Antonio."""
import json
import subprocess
import sys
from pathlib import Path

VOZES_PY = Path(r"D:\hipercool-materiais\python\venv_vozes\Scripts\python.exe")
VOZ_CLONADA_PY = Path(r"D:\hipercool-materiais\bin\voz_clonada.py")
VOZES_DIR = Path(r"D:\hipercool-materiais\models\rvc\vozes")
RAIZ = Path(__file__).parent
SAIDA = RAIZ / "saida_todos"
SAIDA.mkdir(exist_ok=True)

# Bases a testar
BASES = {
    "francisca": "pt-BR-FranciscaNeural",
    "antonio": "pt-BR-AntonioNeural"
}

# Texto de teste (mesmo do mike)
frases = (RAIZ / "frases.txt").read_text(encoding="utf-8").strip()

# Descobrir todos os narradores disponíveis
narradores = []
for item in VOZES_DIR.iterdir():
    if item.is_dir() and not item.name.startswith("_"):
        # Verificar se tem o modelo RVC
        model_file = item / f"{item.name}.pth"
        if model_file.exists():
            narradores.append(item.name)

narradores.sort()
print(f"Encontrados {len(narradores)} narradores com modelo RVC:")
for n in narradores:
    print(f"  - {n}")

print(f"\nGerando 2 bases × {len(narradores)} narradores = {2 * len(narradores)} áudios clonados")
print(f"Texto: {len(frases.split())} palavras (~30s)\n")

# 1. Copiar as 2 bases Edge TTS já geradas (do teste anterior do mike)
import shutil
SAIDA_ANTIGA = RAIZ / "saida"
bases_wav = {}
for nome in BASES.keys():
    base_antiga = SAIDA_ANTIGA / f"{nome}_base.wav"  # francisca_base.wav, antonio_base.wav
    base_nova = SAIDA / f"_base_{nome}.wav"

    if not base_nova.exists():
        if not base_antiga.exists():
            print(f"ERRO: base {nome} não existe em {SAIDA_ANTIGA}")
            sys.exit(1)
        print(f"Copiando base {nome} de {SAIDA_ANTIGA.name}/...")
        shutil.copy2(base_antiga, base_nova)
        print(f"  Base: {base_nova.name} ({base_nova.stat().st_size // 1024} KB)")
    else:
        print(f"Base {nome} já existe: {base_nova.name}")
    bases_wav[nome] = base_nova

# 2. Preparar lote RVC para TODOS os narradores × bases
itens_lote = []
for narrador in narradores:
    for nome_base, base_wav in bases_wav.items():
        saida_clone = SAIDA / f"{narrador}_{nome_base}.wav"
        if saida_clone.exists() and saida_clone.stat().st_size > 500:
            continue  # já existe, pular

        # Tom base depende da base Edge
        tom_base = "2_edge_francisca" if nome_base == "francisca" else "2_edge_francisca"

        itens_lote.append({
            "saida": str(saida_clone),
            "tom_base": tom_base,
            "entrada": str(base_wav),
            "tom_extra": 0,
            "index_rate": 0.5,
            "protect": 0.33,
            "volume_envelope": 1.0,
            "_narrador": narrador,  # metadado para log
            "_base": nome_base
        })

if not itens_lote:
    print("\nTodos os áudios já existem. Nada a fazer.")
    sys.exit(0)

print(f"\n=== Aplicando RVC em lote ({len(itens_lote)} arquivos) ===")
print(f"Processando: {len(itens_lote) // len(BASES)} narradores × {len(BASES)} bases")

# 3. Processar narrador por narrador (cada narrador = 1 carregamento do modelo)
for narrador in narradores:
    itens_narrador = [item for item in itens_lote if item["_narrador"] == narrador]
    if not itens_narrador:
        continue

    print(f"\n--- {narrador} ({len(itens_narrador)} bases) ---")

    # Limpar metadados antes de passar pro voz_clonada.py (cópia limpa)
    itens_limpos = []
    for item in itens_narrador:
        item_limpo = {k: v for k, v in item.items() if not k.startswith("_")}
        itens_limpos.append(item_limpo)

    lista_json = SAIDA / f"_lista_{narrador}.json"
    lista_json.write_text(json.dumps(itens_limpos, ensure_ascii=False), encoding="utf-8")

    log_file = SAIDA / f"_clone_{narrador}.log"
    with open(log_file, "w", encoding="utf-8") as fh:
        r = subprocess.run(
            [str(VOZES_PY), str(VOZ_CLONADA_PY), "lote", narrador, str(lista_json)],
            stdout=fh, stderr=subprocess.STDOUT, timeout=600,
            creationflags=0x00004000 | 0x08000000
        )

    if r.returncode != 0:
        print(f"  ERRO: voz_clonada falhou (rc={r.returncode}), ver {log_file}")
        # Não desistir, continuar com próximo narrador
        continue

    # Pausa breve para liberar memória entre narradores
    import time
    time.sleep(2)

    # Verificar resultados deste narrador
    for item in itens_limpos:
        p = Path(item["saida"])
        if p.exists():
            print(f"  OK {p.name} ({p.stat().st_size // 1024} KB)")
        else:
            print(f"  FALTA {p.name}")

# 4. Resumo final
print("\n=== Resumo ===")
gerados = list(SAIDA.glob("*_francisca.wav")) + list(SAIDA.glob("*_antonio.wav"))
print(f"Total: {len(gerados)} áudios clonados")
print(f"Narradores: {len(narradores)}")
print(f"Pasta: {SAIDA}")

# 5. Abrir pasta no Explorer
print("\nAbrindo pasta no Explorer...")
subprocess.run(["explorer.exe", str(SAIDA)], shell=True)
