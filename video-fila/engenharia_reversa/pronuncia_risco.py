"""pronuncia_risco.py — Fable 29/10 (CORTES_03 tarefa 3): palavras com risco de erro do Edge pt-BR nos roteiros dos
últimos N dias (sem IA). Lê roteiro_falas.json / roteiro*.txt das pastas de Shorts e lista, por frequência:
  - homógrafos conhecidos (coco/cocô, sede, colher, seção, gosto, jogo, olho, governo, começo, acordo, sobre…)
  - siglas (2+ maiúsculas) e nomes estrangeiros (palavra com letras raras em pt: k, w, y, ou terminação -ng/-th/-ck)
  - números com unidade/colados (10k, 2x, 3º, 1.5)
Saída: tabela + `pronuncia_risco.json` (palavra → contagem, exemplos) para virar entradas em `anime_tts._pronuncia`.
    python D:\\video-fila\\engenharia_reversa\\pronuncia_risco.py [dias]
"""
import sys as _sys
_sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — regra da dona: nenhum processo filho abre janela na tela
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZES = [Path(r"D:\hipercool-materiais\animes recap\shorts"), Path(r"D:\recapd-ambientes\producao\workspace\anime")]
DIAS = int(sys.argv[1]) if len(sys.argv) > 1 else 7
# homógrafos/heterófonos que o Edge erra com frequência (ô/ó, é/ê) — a lista cresce com o que a dona ouvir
HOMOGRAFOS = {"coco", "sede", "colher", "secao", "seção", "gosto", "jogo", "olho", "governo", "começo", "acordo",
              "sobre", "forma", "molho", "corpo", "esforço", "torre", "posso", "ele", "este", "esse", "medo", "pelo",
              "pode", "para", "apoio", "almoço", "bolo", "soco", "troco", "choro", "logo", "poço", "fosso", "rosto",
              "piloto", "toco", "jogos", "olhos", "ovo", "ovos", "povo", "novo", "novos", "porto", "posto", "corte",
              "cortes", "copo", "copos", "lobo", "lobos", "osso", "ossos", "pelo", "pelos", "cerca", "sexta", "cobra"}
ESTRANGEIRA = re.compile(r"^[A-Za-zÀ-ÿ]{3,}$")
RARAS = re.compile(r"[kwy]|ng$|th|ck|sh|[^aeiouáéíóúâêôãõç]{3}$", re.I)


def textos():
    lim = time.time() - DIAS * 86400
    for raiz in RAIZES:
        if not raiz.is_dir():
            continue
        for pasta in raiz.iterdir():
            if not pasta.is_dir() or pasta.stat().st_mtime < lim:
                continue
            for arq in list(pasta.glob("roteiro*.txt")) + list(pasta.glob("roteiro_falas.json")):
                try:
                    t = arq.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if arq.suffix == ".json":
                    try:
                        d = json.loads(t)
                        t = " ".join(str(x.get("texto") or x.get("fala") or x.get("frase") or "") if isinstance(x, dict) else str(x)
                                     for x in (d if isinstance(d, list) else d.get("falas") or d.get("frases") or []))
                    except ValueError:
                        pass
                yield pasta.name, t


homo, siglas, estr, nums = Counter(), Counter(), Counter(), Counter()
ex = defaultdict(set)
n = 0
for nome, t in textos():
    n += 1
    for frase in re.split(r"[.!?\n]", t):
        for w in re.findall(r"[\wÀ-ÿ]+(?:[.,][\wÀ-ÿ]+)?", frase):
            wl = w.lower()
            if wl in HOMOGRAFOS:
                homo[wl] += 1
                ex[wl].add(frase.strip()[:90])
            elif re.fullmatch(r"[A-ZÀ-Ý]{2,6}", w):
                siglas[w] += 1
                ex[w].add(frase.strip()[:90])
            elif re.search(r"\d", w) and re.search(r"[A-Za-zº°ª]|[.,]\d", w):
                nums[wl] += 1
                ex[wl].add(frase.strip()[:90])
            elif ESTRANGEIRA.match(w) and w[0].isupper() and RARAS.search(w) and not w.isupper():
                estr[w] += 1
                ex[w].add(frase.strip()[:90])
print(f"roteiros lidos: {n} (últimos {DIAS} dias)")
for titulo, c in (("HOMÓGRAFOS (ô/ó, é/ê — conferir no _pronuncia)", homo), ("SIGLAS (o Edge soletra ou lê como palavra)", siglas),
                  ("NOMES/PALAVRAS ESTRANGEIRAS (pronúncia aportuguesada)", estr), ("NÚMEROS colados/unidades", nums)):
    print(f"\n{titulo}: {len(c)} distintas")
    for w, k in c.most_common(25):
        print(f"  {w:<22} {k:>3}  ex.: {next(iter(ex[w]))}")
saida = Path(__file__).with_name("pronuncia_risco.json")
saida.write_text(json.dumps({"dias": DIAS, "roteiros": n, "homografos": homo, "siglas": siglas, "estrangeiras": estr,
                             "numeros": nums, "exemplos": {k: sorted(v)[:3] for k, v in ex.items()}},
                            ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\njson: {saida}")
