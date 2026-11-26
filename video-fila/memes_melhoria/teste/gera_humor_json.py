# -*- coding: utf-8 -*-
# PC1: gera D:\recapd-ambientes\producao\bin\humor_narradores.json (vai junto do codigo pro Kaggle).
import glob, json, os, random, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PAL = re.compile(r"\b(caralh\w*|porras?|put[ao]s?|puta\w*|merda\w*|fod[aeiô]\w*|cacete|bucet\w*|arrombad\w*|"
                 r"viad[oa]s?|desgraçad\w*|desgraç\w*|fdp|cuz[aã]o|carai)\b", re.I)
VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
PED = Path(r"C:\Users\Haylla\Desktop\coleta_narradores\_pedacos")
REACAO = re.compile(r"(?i)\?|\b(eu|até eu|nem eu|comigo)\b|^(nossa|eita|rapaz|caramba|caraca|pô|ih|ai ai|meu deus|ué|vixe|ixi|olha)\b")
def limpa_lista(v, n=8):
    out = []
    for x in v or []:
        s = str(x).strip()
        if s and not PAL.search(s) and len(s) <= 60 and s not in out:
            out.append(s)
    return out[:n]
dados = {"_leia": ("26/11: perfil de HUMOR por narrador para a passada de reações do roteiro longo (humor_narrador.py). "
                   "Gerado de models/rvc/vozes/<voz>/linguagem_v2.json + exemplos REAIS curtos de reação das "
                   "transcrições da coleta (coleta_narradores/_pedacos). Sem palavrão (a postagem reprova). "
                   "Regerar: memes_melhoria/teste/gera_humor_json.py"), "_generico": {
    "interjeicoes": ["Nossa", "Eita", "Rapaz", "Caramba", "Olha só", "Pô"],
    "fala_com_publico": ["galera", "meu povo", "vocês"], "bordoes": [], "apelidos": ["o cara", "o moleque"],
    "exemplos": ["Nossa, eu jamais faria isso!", "Pera aí, ele fez o quê?", "Eita, agora complicou!",
                 "Até eu fiquei com medo agora...", "Rapaz, isso não é possível não!", "Cadê o cérebro desse cara?"]}}
for p in sorted(VOZES.glob("*/linguagem_v2.json")):
    voz = p.parent.name
    try: g = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError): continue
    d = {"interjeicoes": limpa_lista(g.get("interjeicoes")), "fala_com_publico": limpa_lista(g.get("fala_com_publico"), 6),
         "bordoes": limpa_lista(g.get("bordoes"), 10), "apelidos": limpa_lista(g.get("apelidos_protagonista"), 6)}
    ex = []
    for f in sorted(glob.glob(str(PED / voz / "*" / "*.json"))):
        try: segs = json.load(open(f, encoding="utf-8"))
        except Exception: continue
        for s in segs:
            t = re.sub(r"\s+", " ", s.get("text", "")).strip()
            n = len(t.split())
            if 4 <= n <= 13 and s.get("avg_logprob", -9) > -0.45 and s.get("no_speech_prob", 1) < 0.5 \
                    and REACAO.search(t) and not PAL.search(t):
                ex.append(t)
    random.seed(voz)
    ex = list(dict.fromkeys(ex))
    d["exemplos"] = random.sample(ex, min(25, len(ex)))
    if any(d.values()):
        dados[voz] = d
out = Path(r"D:\recapd-ambientes\producao\bin\humor_narradores.json")
out.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
print("vozes:", len(dados) - 2, "| arquivo:", out, out.stat().st_size // 1024, "KB")
for v in ("kkvirjao", "momo", "mike"):
    print(v, "exemplos:", len(dados.get(v, {}).get("exemplos", [])))
    for e in dados.get(v, {}).get("exemplos", [])[:8]: print("    ", e)
