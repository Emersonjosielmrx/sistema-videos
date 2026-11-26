# -*- coding: utf-8 -*-
# Roda no PC1. Implanta nos longos os memes que a dona aprovou em 26/11 (Desktop\memes_pt).
#   python implantar_aprovados.py preparar  -> corta/copia para a pasta de teste e confere as fichas (NAO mexe na producao)
#   python implantar_aprovados.py aplicar   -> copia para memes_novos e atualiza memes.json e fichas.json (com backup)
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import memes_visuais as mv  # noqa: E402

FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
FP = r"D:\hipercool-materiais\bin\ffprobe.exe"
BASE = Path(r"C:\Users\Haylla\Desktop\memes_pt")
NOVOS = Path(r"D:\hipercool-materiais\assets\memes_img\memes_novos")
STAGE = Path(r"D:\video-fila\memes_melhoria\teste\aprovados_stage")
PASTAS_OK = ("apropvados", "aprovado")  # nomes das pastas onde a dona separou os aprovados
NUNCA = ["morreu", "morre", "morte", "luto", "funeral", "chorando"]
TETO = mv.INTERROMPE_DUR[1]


def item(origem, nome, frase, emo, cabe, corte=None, resumo=True, palavrao=False, som=False):
    return dict(origem=origem, nome=nome, frase=frase, emo=emo, cabe=cabe, corte=corte, resumo=resumo,
                palavrao=palavrao, som=som)


ITENS = [
    item("101_", "21_ai_que_delicia_cara", "ai que delicia cara", "alegria",
         ["se deliciou", "que delícia", "saboreou cada", "aproveitou cada momento", "comeu com gosto"], corte=(4.5, 7.9)),
    item("02_", "22_ai_ai_ai_nada_eu_curto", "ai ai ai nada eu curto", "deboche",
         ["gostou de apanhar", "apanhou e gostou", "curtiu a surra", "adorou apanhar"]),
    item("103_", "23_xaropinho_rapaz", "rapaz", "choque",
         ["rapaz do céu", "não é que ele", "olha só o que", "ficou de boca aberta"]),
    item("111_", "24_que_deselegante", "que deselegante", "deboche",
         ["foi mal-educado", "falta de educação", "sem educação", "foi grosseiro", "tratou mal", "atitude feia"]),
    item("114_", "25_receba", "receba", "deboche",
         ["recebeu o troco", "levou o que merecia", "na mesma moeda", "toma essa", "pega essa"]),
    item("130_", "26_que_ota", "que ota", "deboche",
         ["que trouxa", "caiu feito patinho", "foi enganado fácil", "se deixou enganar", "caiu na conversa"]),
    item("132_", "27_meu_deus_do_ceu_nao_sobrou_nada", "meu deus do ceu nao sobrou nada", "choque",
         ["destruiu tudo", "não restou nada", "deixou só escombros", "arrasou a cidade", "tudo virou cinzas"]),
    item("133_", "28_socorro", "socorro", "choque",
         ["pediu socorro", "pediu ajuda desesperado", "entrou em pânico", "se viu encurralado", "gritou por socorro"]),
    item("134_", "29_ta_tranquilo_ta_favoravel", "ta tranquilo ta favoravel", "deboche",
         ["tudo sob controle", "o plano está funcionando", "dominando a luta", "ganhando de lavada", "tudo correndo bem"],
         corte=(0.0, 3.3)),
    item("138_", "30_nao_entendi_foi_nada", "nao entendi foi nada", "confusão",
         ["não entendeu nada", "ficou sem entender", "ninguém explicou nada", "sem entender a situação",
          "não entendeu foi nada"]),
    item("125_", "31_mas_que_porra_e_essa", "mas que porra e essa", "choque",
         ["que poder é esse", "que força é essa", "que monstro é esse", "que absurdo é esse", "que diabos é isso"],
         resumo=False, palavrao=True),
    item("135_", "32_e_o_pix_nada", "e o pix nada", "raiva",
         ["cadê o pagamento", "levou calote", "ficou sem a recompensa", "foi enganado no preço",
          "esperando o pagamento"], resumo=False, palavrao=True),
    item("116_", "33_ai_papai_devagar_pai", "oh meu deus nao faca isso", "choque",
         ["não faça isso", "pediu para ele parar", "ficou pedindo para parar"],
         corte=(0.0, 5.7)),
    item("129_", "34_meu_deus_so_besteira", "meu deus so besteira", "deboche",
         ["só besteira", "falou besteira", "só falou besteira", "falando besteira", "que besteira"]),
    item("141_", "35_som_boom_dramatico", "boom dramatico", "choque",
         ["e foi aí que tudo mudou", "tudo mudou naquele momento", "a verdade veio à tona", "o plano veio abaixo"],
         resumo=False, som=True),
    item("143_", "36_som_explosao", "explosao", "choque",
         ["uma explosão", "tudo explodiu", "a bomba explodiu", "o prédio explodiu"], resumo=False, som=True),
    item("150_", "37_som_game_over", "game over", "deboche",
         ["game over", "fim de jogo", "acabou para ele", "levou a pior"], resumo=False, som=True),
]


def dur(p):
    r = subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)
    return float(r.stdout.strip())


def cortar(src, dst, a, b):
    d = b - a
    cmd = [FF, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a:.2f}", "-i", str(src),
           "-t", f"{d:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k",
           "-af", f"afade=t=in:d=0.05,afade=t=out:st={max(d - 0.15, 0):.2f}:d=0.15",
           "-movflags", "+faststart", str(dst)]
    subprocess.run(cmd, stdin=subprocess.DEVNULL, timeout=120, check=True,
                   creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS)


def achar(origem):
    ach = []
    for p in BASE.rglob("*.mp4"):
        if p.parent.name in PASTAS_OK and p.name.replace("[PALAVRAO] ", "").startswith(origem):
            ach.append(p)
    return ach


def preparar():
    STAGE.mkdir(parents=True, exist_ok=True)
    plano, erros = [], 0
    for it in ITENS:
        ach = achar(it["origem"])
        if len(ach) != 1:
            print(f"ERRO {it['origem']}: achei {len(ach)} arquivo(s) nas pastas de aprovados")
            erros += 1
            continue
        src, dst = ach[0], STAGE / (it["nome"] + ".mp4")
        if it["corte"]:
            cortar(src, dst, *it["corte"])
        else:
            shutil.copy2(src, dst)
        d = dur(dst)
        cabe_ok = [e for e in it["cabe"] if not mv.triste(e)]
        tirados = [e for e in it["cabe"] if mv.triste(e)]
        ficha = {"emocao": it["emo"], "interrompe": True, "cabe": cabe_ok, "nunca": list(NUNCA)}
        if not it["resumo"]:
            ficha["resumo"] = False
        if it["palavrao"]:
            ficha["palavrao"] = True
        if it["som"]:
            ficha["so_som"] = True
        aviso = "  <-- PASSA DO TETO" if d > TETO else ""
        erros += 1 if d > TETO else 0
        print(f"{it['nome']:42} {d:5.1f}s {'cortado' if it['corte'] else 'inteiro':8} cabe={len(cabe_ok)}"
              f"{' tirados=' + str(tirados) if tirados else ''}{aviso}")
        plano.append({"arquivo": dst.name, "frase": it["frase"], "dur": round(d, 2), "ficha": ficha,
                      "origem": src.name})
    (STAGE / "plano.json").write_text(json.dumps(plano, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"preparados: {len(plano)} de {len(ITENS)} | erros: {erros}")
    return 1 if erros else 0


def _grava(arq, dados):
    tmp = arq.with_name(arq.name + ".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(arq)


def aplicar():
    plano = json.loads((STAGE / "plano.json").read_text(encoding="utf-8"))
    memes_json, fichas_json = NOVOS / "memes.json", NOVOS / "fichas.json"
    for arq in (memes_json, fichas_json):
        bk = arq.with_name(arq.name + ".antes_aprovados_26nov")
        if not bk.exists():
            shutil.copy2(arq, bk)
    lista = json.loads(memes_json.read_text(encoding="utf-8"))
    fichas = json.loads(fichas_json.read_text(encoding="utf-8"))
    ja = {m["arquivo"] for m in lista}
    novos = 0
    for p in plano:
        src, dst = STAGE / p["arquivo"], NOVOS / p["arquivo"]
        if not src.exists():
            print("FALTA no stage:", p["arquivo"])
            return 1
        if p["arquivo"] in ja or dst.exists() or p["arquivo"] in fichas:
            print("ja existe, pulei:", p["arquivo"])
            continue
        shutil.copy2(src, dst)
        lista.append({"arquivo": p["arquivo"], "frase": p["frase"], "dur": p["dur"]})
        fichas[p["arquivo"]] = p["ficha"]
        novos += 1
    fichas["_26_11"] = ("26/11 (dona aprovou 17 memes novos, numeros 21 a 37): ficha com resumo=false = nao entra no "
                        "resumo do comeco (palavrao ou so som); palavrao=true / so_som=true so informam. "
                        "Backup: memes.json.antes_aprovados_26nov e fichas.json.antes_aprovados_26nov")
    _grava(memes_json, lista)
    _grava(fichas_json, fichas)
    print(f"aplicados: {novos} | memes.json agora com {len(lista)} | fichas com {len([k for k in fichas if not k.startswith('_')])}")
    return 0


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit(preparar() if modo == "preparar" else aplicar() if modo == "aplicar" else print(__doc__) or 2)
