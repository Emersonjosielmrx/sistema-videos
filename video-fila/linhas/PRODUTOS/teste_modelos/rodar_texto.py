"""Teste do MELHORADOR em versão SÓ TEXTO (dona 29/10): o Sonnet web (cw/claude-sonnet-5-5) não recebe imagem nem
arquivo, então todos os modelos fazem analista + decisor + revisor do mesmo vídeo SEM a folha de quadros e com o
dados.json colado no prompt. Ferramentas bloqueadas para todos (ninguém vê a imagem). Ensaio: nada aplicado, nada
escrito no DECISOES nem no estado do melhorador. Resultado em <video>__<modelo>_texto.json.

    D:\\veo\\venv\\Scripts\\python.exe rodar_texto.py <video.json> [modelo ...]
"""
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, r"D:\postador-de-videos\bin")
from produto import melhorador as mel  # noqa: E402

MODELOS = ["cw/claude-sonnet-5-5", "gweb/gemini-3.1-pro", "argon-pro", "argon-flash", "argon-gemini",
           "agy/gemini-3.8-flash-high"]
SEM_FERRAMENTAS = ("Read", "Read,Bash,Edit,Write,Glob,Grep,WebFetch,WebSearch,Agent,NotebookEdit,TodoWrite")
AVISO = ("VERSÃO SÓ TEXTO DO TESTE: não há imagem nem arquivos para abrir e as ferramentas estão bloqueadas. "
         "Tudo o que você tem está neste texto; não peça nem cite quadros da folha.\n\n")

_cfg_original = mel.cfg


def _cfg_teste():
    c = _cfg_original()
    c["modelos_desligados"] = []
    return c


mel.cfg = _cfg_teste
mel._decisoes = lambda linhas: None
_gravar_original = mel._gravar
mel._gravar = lambda p, d: None if Path(p) == Path(mel.ESTADO) else _gravar_original(p, d)

_chamar_json_original = mel.motor.chamar_json


def _chamar_json_sem_ferramentas(prompt, pasta, etapa, **kw):
    kw["ferramentas"] = SEM_FERRAMENTAS
    return _chamar_json_original(prompt, pasta, etapa, **kw)


mel.motor.chamar_json = _chamar_json_sem_ferramentas

_chamar_original = mel._chamar


def _chamar_texto(papel, prompt, pasta, c, e, evitar=None):
    if papel == "analista":
        dados = (Path(pasta) / "dados.json").read_text("utf-8")
        prompt = re.sub(r"Abra com Read a imagem.*?ajustes atuais\)\.",
                        "Leia os DADOS abaixo (o júri de 4 verificadores com movimento por cena, opinião do dono, "
                        "histórico de notas, ajustes atuais). Não há imagem do vídeo neste teste.",
                        prompt, count=1, flags=re.S)
        prompt = prompt.replace("Cada achado com a PROVA (quadro da folha ou campo do dados.json).",
                                "Cada achado com a PROVA (campo dos DADOS abaixo).")
        prompt += "\n\nDADOS:\n" + dados
    else:
        prompt = prompt.replace("DADOS (também em dados.json nesta pasta):", "DADOS:")
    return _chamar_original(papel, AVISO + prompt, pasta, c, e, evitar)


mel._chamar = _chamar_texto


def main():
    js = Path(sys.argv[1])
    for m in sys.argv[2:] or MODELOS:
        t0 = time.time()
        try:
            r = mel.ciclo(True, js, so_modelo=m)
            erro = None
        except Exception as ex:  # noqa: BLE001
            r, erro = None, f"{type(ex).__name__}: {str(ex)[:300]}"
        out = {"modelo": m, "video": js.name, "versao": "so_texto",
               "quando": datetime.now().isoformat(timespec="seconds"),
               "segundos": round(time.time() - t0), "erro": erro, "resultado": r}
        nome = m.replace("/", "_") + "_texto"
        (AQUI / f"{js.stem}__{nome}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str),
                                                     "utf-8")
        print(f"== {m}: {out['segundos']} s, "
              + (f"ERRO {erro}" if erro else f"{len((r or {}).get('achados') or [])} achados, "
                 f"{len((r or {}).get('mudancas') or [])} mudanças, {(r or {}).get('aprovadas')} aprovadas"),
              flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    os.chdir(AQUI)
    main()
