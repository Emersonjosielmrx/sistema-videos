# -*- coding: utf-8 -*-
# Roda no PC1. Liga os memes novos (21 em diante) no codigo dos longos.
# Backup .antes_aprovados_26nov, tudo-ou-nada (confere sintaxe antes de gravar), idempotente.
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BIN = Path(r"D:\recapd-ambientes\producao\bin")

# (marca de que ja foi aplicado, trecho antigo, trecho novo)
PATCHES = {
    "memes_visuais.py": [
        (
            "ficha.get(\"palavrao\")",
            r'''        emo = EMOCAO_NOVOS.get(m["arquivo"][:2])
        if arq.exists() and emo and not meme_proibido(arq):''',
            r'''        ficha = fichas().get(m["arquivo"]) or {}
        # 26/11: os memes aprovados em 26/11 (numero 21 em diante) nao estao em EMOCAO_NOVOS: a emocao vem da ficha
        emo = EMOCAO_NOVOS.get(m["arquivo"][:2]) or ficha.get("emocao")
        if ficha.get("palavrao") and os.environ.get("MEMES_PALAVRAO", "1") == "0":
            continue  # 26/11: MEMES_PALAVRAO=0 tira os memes com palavrao na fala (padrao: entram, a dona aprovou)
        if arq.exists() and emo and not meme_proibido(arq):''',
        ),
        (
            "def fora_do_resumo",
            r'''def _ficha(m):
    return fichas().get(Path(m["file"]).name)
''',
            r'''def _ficha(m):
    return fichas().get(Path(m["file"]).name)


def fora_do_resumo(nome):
    # 26/11: meme com palavrao na fala ou so de som (ficha resumo=false) nao entra na ABERTURA do video
    try:
        return (fichas().get(str(nome)) or {}).get("resumo") is False
    except Exception:  # noqa: BLE001
        return False
''',
        ),
    ],
    "anime-pipeline.py": [
        (
            "_fora_resumo",
            r'''        if novos_dir:
            nv = [p for p in sorted(novos_dir.glob("*.mp4")) if not meme_proibido(p)
                  and 0 < (video_duration(str(p)) or 0) <= MEME_RESUMO_MAX_S]''',
            r'''        if novos_dir:
            try:  # 26/11: ficha resumo=false (palavrao / so som) nao entra na abertura
                from memes_visuais import fora_do_resumo as _fora_resumo
            except Exception:  # noqa: BLE001
                _fora_resumo = lambda _n: False  # noqa: E731
            nv = [p for p in sorted(novos_dir.glob("*.mp4")) if not meme_proibido(p) and not _fora_resumo(p.name)
                  and 0 < (video_duration(str(p)) or 0) <= MEME_RESUMO_MAX_S]''',
        ),
    ],
}


def main():
    prontos = {}
    for nome, trocas in PATCHES.items():
        p = BIN / nome
        dados = p.read_bytes()
        crlf = b"\r\n" in dados
        txt = dados.decode("utf-8")
        if crlf:
            txt = txt.replace("\r\n", "\n")
        mudou = False
        for marca, velho, novo in trocas:
            if marca in txt:
                print(f"ja aplicado: {nome} ({marca})")
                continue
            if txt.count(velho) != 1:
                print(f"ERRO: ancora achada {txt.count(velho)}x (esperava 1) em {nome}: {velho[:70]!r}")
                return 1
            txt = txt.replace(velho, novo)
            mudou = True
        try:
            compile(txt, nome, "exec")
        except SyntaxError as e:
            print(f"ERRO de sintaxe depois do patch em {nome}: {e}")
            return 1
        if mudou:
            prontos[nome] = (p, txt.replace("\n", "\r\n") if crlf else txt)
    for nome, (p, txt) in prontos.items():
        bk = p.with_name(p.name + ".antes_aprovados_26nov")
        if not bk.exists():
            shutil.copy2(p, bk)
        p.write_bytes(txt.encode("utf-8"))
        print(f"patch gravado: {nome} (backup {bk.name})")
    if not prontos:
        print("nada a fazer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
