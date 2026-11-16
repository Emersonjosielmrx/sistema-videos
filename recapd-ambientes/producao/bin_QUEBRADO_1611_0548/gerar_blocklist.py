#!/usr/bin/env python3
"""Gera a BLOCKLIST de copyright (trilhas que dao problema no YouTube).

Regras (decididas pelo usuario):
- Base = trilhas classificadas como PROTEGIDO.
- EXCLUI Naruto e Re:Zero (usuario tem certeza que sao usadas livremente por todos).
- Salva JSON (pro codigo consumir) + .txt legivel.

NAO altera nenhum codigo de pipeline. Apenas produz os artefatos de dados.
"""
import os, re, json, subprocess
import importlib
from pathlib import Path.util

spec = importlib.util.spec_from_file_location("cc", str(Path(__file__).resolve().parent / "classificar_copyright.py"))
cc = importlib.util.module_from_spec(spec); spec.loader.exec_module(cc)

TRILHAS = cc.TRILHAS
OUT_JSON = r"D:\hipercool-materiais\_curadoria\copyright_blocklist.json"
OUT_TXT = r"D:\hipercool-materiais\_curadoria\copyright_blocklist.txt"

# isencoes por NOME (nao entram na blocklist)
ISENTO = [
    r"naruto",                 # usuario: todo mundo usa de boa
    r"re:?zero|rezero",        # usuario: idem, ja temos aprovadas
]
CURTO_SEG = 8.0  # < 8s: efeito, nao reivindicavel -> marca como nao-bloqueante


def isento(name):
    low = name.lower()
    return any(re.search(p, low) for p in ISENTO)


def dur(path):
    try:
        out = subprocess.run(
            ["ffprobe","-v","quiet","-show_entries","format=duration",
             "-of","default=nw=1:nk=1", path],
            capture_output=True, text=True, timeout=30)
        return round(float(out.stdout.strip()), 1)
    except Exception:
        return -1.0


def main():
    files = sorted(os.listdir(TRILHAS))
    files = [f for f in files if f.lower().endswith((".mp3",".wav",".m4a",".opus",".flac"))]

    block = []
    isentos_naruto_rezero = []
    for f in files:
        cat, motivo = cc.classify(f)
        if cat != "PROTEGIDO":
            continue
        if isento(f):
            isentos_naruto_rezero.append(f)
            continue
        d = dur(os.path.join(TRILHAS, f))
        block.append({
            "arquivo": f,
            "motivo": motivo,
            "duracao_seg": d,
            "tipo": "efeito_curto" if (0 <= d < CURTO_SEG) else "trilha",
            "bloquear": not (0 <= d < CURTO_SEG),  # efeito curto nao bloqueia
        })

    data = {
        "descricao": "Blocklist de copyright para o modo seguro do YouTube. Trilhas que "
                     "provavelmente geram Content ID / reivindicacao. Naruto e Re:Zero "
                     "FORAM EXCLUIDAS (usuario confirmou uso livre). Efeitos < 8s nao bloqueiam.",
        "gerado_de": TRILHAS,
        "regra_isencao": [
            "Naruto e Re:Zero: sempre liberadas (nao entram aqui).",
            "Arquivos em assets/sfx_prioridade/: sempre liberados (ja vieram de quem usa).",
            "Arquivos em _curadoria/_aprovados/: sempre liberados (curados e aprovados).",
            "tipo=efeito_curto (<8s): nao bloqueia (muito curto pra reivindicacao).",
        ],
        "total_bloqueados": sum(1 for b in block if b["bloquear"]),
        "total_efeitos_curtos_liberados": sum(1 for b in block if not b["bloquear"]),
        "isentos_naruto_rezero": sorted(isentos_naruto_rezero),
        "blocklist": sorted(block, key=lambda x: x["arquivo"]),
    }

    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)

    with open(OUT_TXT, "w", encoding="utf-8") as fh:
        fh.write("BLOCKLIST DE COPYRIGHT (modo seguro YouTube)\n")
        fh.write("Naruto e Re:Zero EXCLUIDAS (uso livre). Efeitos <8s nao bloqueiam.\n")
        fh.write(f"Bloqueados: {data['total_bloqueados']} | "
                 f"Efeitos curtos liberados: {data['total_efeitos_curtos_liberados']} | "
                 f"Isentos Naruto/ReZero: {len(isentos_naruto_rezero)}\n\n")
        fh.write("=== BLOQUEADOS (nao usar no modo seguro) ===\n")
        for b in sorted(block, key=lambda x: x["arquivo"]):
            if b["bloquear"]:
                fh.write(f"  {b['duracao_seg']:6.1f}s  {b['arquivo']}\n")
        fh.write("\n=== EFEITOS CURTOS (liberados, <8s) ===\n")
        for b in sorted(block, key=lambda x: x["arquivo"]):
            if not b["bloquear"]:
                fh.write(f"  {b['duracao_seg']:6.1f}s  {b['arquivo']}\n")
        fh.write("\n=== ISENTOS POR NOME (Naruto / Re:Zero) ===\n")
        for f in sorted(isentos_naruto_rezero):
            fh.write(f"  {f}\n")

    print(f"OK -> {OUT_JSON}")
    print(f"OK -> {OUT_TXT}")
    print(f"bloqueados={data['total_bloqueados']} "
          f"efeitos_curtos={data['total_efeitos_curtos_liberados']} "
          f"isentos_naruto_rezero={len(isentos_naruto_rezero)}")


if __name__ == "__main__":
    main()
