r"""instalar_voz_aprovada.py — põe na produção uma voz RVC APROVADA pela dona, com o consentimento registrado.

Dona 18/11: "tem 32 novas vozes que aprovei... já consegui o consentimento de outras também que ainda não estão
treinadas, mas já deixe pronto pra colocar elas também". Regra de 16/11 (memória project-estrategia-vozes-views):
voz de pessoa/dublador real só entra em vídeo publicado com o consentimento REGISTRADO — este script grava o registro
em models\rvc\vozes\<voz>\consentimento.json e em amostras_voz\CONSENTIMENTOS.json.

O que faz, por voz (mesmo formato das 20 de 11/11, D:\tmp\instalar_vozes_novas.py):
  1. copia .index e, POR ÚLTIMO, o .pth para models\rvc\vozes\<voz> (sem o .pth a voz não conta como instalada);
  2. f0.txt (tom natural MEDIDO na amostra aprovada), personagem.json, linguagem_v2.json, consentimento.json;
  3. tom_*.txt das 4 bases (Kokoro, Francisca, Piper, Kitten) — tom_fixo do voz_clonada;
  4. nota por nicho em config\narradores_nichos.json (copia a de uma voz parecida que já está lá);
  5. sobe a voz para o cache do Kaggle (manhwa-drive:colab_recap/vozes/<voz>) pelo Drive central.
A voz entra no sorteio (anime_voz_clonada.proxima) sozinha: tem personagem.json + .pth.

    (ver acima)

VOZ NOVA (treinada depois): pôr a pasta com .pth e .index em amostras_voz\vozes_novas_1011\<voz> (ou em ORIGEM_EXTRA),
uma amostra aprovada em amostras_voz\vozes_novas_1011\falas\<voz>.wav e marcar "aprovado" no _vereditos.json.
Se a voz não estiver no VOZES_DICT, o script usa o nome do catálogo de treino (vozes_novas_treino.py) e escolhe a
voz parecida pelo tom natural mais próximo entre as que já estão na produção. Consentimento: registra que a dona deu o
consentimento (18/11).

    venv_vozes\Scripts\python.exe instalar_voz_aprovada.py --novas       # aprovadas no _vereditos que faltam instalar
    venv_vozes\Scripts\python.exe instalar_voz_aprovada.py todas         # as do dicionário VOZES abaixo
    venv_vozes\Scripts\python.exe instalar_voz_aprovada.py <voz> [...]   # só essas (aceita qualquer voz com .pth+amostra)
    venv_vozes\Scripts\python.exe instalar_voz_aprovada.py --listar      # estado de tudo (VOZES_DICT + pendentes)
"""
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voz_clonada as vc  # noqa: E402

ORIGEM = Path(r"D:\hipercool-materiais\amostras_voz\vozes_novas_1011")
VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
NICHOS = Path(r"D:\recapd-ambientes\producao\config\narradores_nichos.json")
REGISTRO = Path(r"D:\hipercool-materiais\amostras_voz\CONSENTIMENTOS.json")
RCLONE = r"D:\tools\rclone.exe"
BASES = ("1_kokoro", "2_edge_francisca", "3_piper", "4_kitten")

# voz: (nome, tipo "personagem"|"pessoa", parecida_com (nicho), resumo, tom, bordões, consentimento)
VOZES_DICT = {
    "julius": ("Julius (Todo Mundo Odeia o Chris)", "personagem", "seu_madruga",
               "Julius, o pai pão-duro: reclama de gasto, trabalha em dois empregos e calcula o preço de tudo.",
               ["pão-duro", "bravo", "cômico"],
               ["Isso aí custa dinheiro!", "Eu trabalho em dois empregos!", "Desliga essa luz!"]),
    "jack_sparrow": ("Capitão Jack Sparrow (Piratas do Caribe)", "personagem", "buggy",
                     "Jack Sparrow, o pirata malandro: excêntrico, cheio de lábia, sempre escapando no último segundo.",
                     ["malandro", "excêntrico", "aventureiro"],
                     ["Capitão! Capitão Jack Sparrow!", "Por que o rum acabou?", "Esse é o dia que você quase pegou o capitão Jack Sparrow."]),
    "sam_winchester": ("Sam Winchester (Supernatural)", "personagem", "loid_forger",
                       "Sam Winchester, o irmão estudioso: sério, racional e determinado, caça monstros com o irmão.",
                       ["sério", "racional", "determinado"], ["Dean, isso não é normal.", "A gente tem que salvar essas pessoas."]),
    "dean_winchester": ("Dean Winchester (Supernatural)", "personagem", "loid_forger",
                        "Dean Winchester, o irmão marrento: durão, sarcástico e protetor, ama rock e o carro dele.",
                        ["durão", "sarcástico", "protetor"], ["Salvar pessoas, caçar coisas. O negócio da família.", "Vamos nessa, Sammy."]),
    "magneto_santa_cruz": ("Magneto (X-Men)", "personagem", "muzan",
                           "Magneto, o mestre do magnetismo: imponente, frio e convicto, fala como um líder que não perdoa.",
                           ["imponente", "frio", "vilão"], ["Os humanos nunca vão nos aceitar.", "Eu sou Magneto."]),
    "jonah_jameson_santa_cruz": ("J. Jonah Jameson (Homem-Aranha)", "personagem", "buggy",
                                 "J. Jonah Jameson, o editor do Clarim Diário: escandaloso, grita o tempo todo e odeia o Homem-Aranha.",
                                 ["escandaloso", "cômico", "explosivo"],
                                 ["Me traga fotos do Homem-Aranha!", "Esse aracnídeo é uma ameaça!", "Parker!"]),
    "pedro_bial": ("Pedro Bial (apresentador)", "pessoa", "cid_moreira",
                   "Pedro Bial, o apresentador: voz de reflexão, pausada e poética, faz a crônica do que aconteceu.",
                   ["reflexivo", "poético", "pausado"], ["Boa noite.", "E a vida segue."]),
    "pato_donald_galvan": ("Pato Donald (Disney)", "personagem", "pato_donald",
                           "Pato Donald, o pato esquentado: fala embolado, perde a paciência à toa e se mete em confusão.",
                           ["esquentado", "cômico", "embolado"], ["Oh, me deixa!", "Ah é? Ah é?!"]),
    "sonic_manolo_rey": ("Sonic (filme)", "personagem", "goten_gohan_crianca",
                         "Sonic, o ouriço azul: rápido, convencido e brincalhão, fala acelerado e cheio de piada.",
                         ["rápido", "brincalhão", "convencido"], ["Vamos nessa!", "Sou rápido demais pra você!"]),
    "hinata_hyuga": ("Hinata Hyuga (Naruto)", "personagem", "rem",
                     "Hinata, a herdeira tímida do clã Hyuga: doce, gentil e corajosa quando precisa, apaixonada pelo Naruto.",
                     ["tímida", "doce", "corajosa"], ["Naruto-kun...", "Eu não vou desistir!"]),
    "anya_forger_e500": ("Anya Forger (Spy x Family)", "personagem", "anya_forger",
                         "Anya, a menina que lê mentes: fofa, travessa e animada, adora espiões e amendoim.",
                         ["fofa", "infantil", "travessa"], ["Anya gosta de amendoim!", "Waku waku!", "Heh."]),
}
CONSENTIMENTO_DE = {v: "dona registrou o consentimento do dono da voz em 18/11/2026" for v in VOZES_DICT}
VEREDITOS = ORIGEM / "_vereditos.json"
CATALOGO_TREINO = Path(r"D:\tmp\vozes_novas_treino.py")  # VOZES = {voz: (busca, tom, "Nome (Obra)")}


def _aprovadas_pendentes():
    """Vozes com veredito "aprovado..." no _vereditos.json que já têm .pth em vozes_novas_1011 e ainda não estão na
    produção. Motores ("aprovado (motor)") ficam de fora."""
    try:
        ver = json.loads(VEREDITOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for v, txt in ver.items():
        t = str(txt).lower()
        if not t.startswith("aprovad") or "motor" in t:
            continue
        if list((ORIGEM / v).glob("*.pth")) and not (VOZES / v / f"{v}.pth").exists():
            out.append(v)
    return out


def _catalogo():
    try:
        src = CATALOGO_TREINO.read_text(encoding="utf-8")
        i = src.index("VOZES = {")
        ns = {}
        exec(src[i:src.index("\n}\n", i) + 2], ns)  # noqa: S102 — arquivo nosso (catálogo do treino)
        return ns["VOZES"]
    except (OSError, ValueError, KeyError, SyntaxError):
        return {}


def _parecida_pelo_tom(f0):
    """Voz da produção com nota por nicho e tom natural mais perto (nicho da voz nova = o dela)."""
    try:
        tab = json.loads(NICHOS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    melhor = None
    for v, d in tab.items():
        if v.startswith("_") or not isinstance(d, dict) or d.get("fora"):
            continue
        try:
            f = float((VOZES / v / "f0.txt").read_text().strip())
        except (OSError, ValueError):
            continue
        dist = abs(12 * __import__("math").log2(f / f0))
        if melhor is None or dist < melhor[0]:
            melhor = (dist, v)
    return melhor[1] if melhor else None


def _entrada_automatica(voz):
    """Para voz aprovada que não está no VOZES_DICT: nome do catálogo do treino, resumo genérico, voz parecida
    escolhida pelo tom (feita em instalar() depois de medir o f0)."""
    nome = (_catalogo().get(voz) or (None, None, None))[2] or voz.replace("_", " ").title()
    pessoa = "(" not in nome  # "Nome (Obra)" = personagem; sem obra = pessoa real (apresentador, dublador...)
    resumo = (f"{nome}: fala com o jeito marcante dele(a) — usar nas falas e na narração do nicho em que encaixa."
              if not pessoa else f"{nome}: a voz real conhecida, narrando com o jeito dele(a).")
    return (nome, "pessoa" if pessoa else "personagem", None, resumo, ["marcante"], [])


def _amostra(voz):
    for p in (ORIGEM / "falas" / f"{voz}.wav", ORIGEM / "chatterbox" / f"{voz}.wav", ORIGEM / "falas_desktop" / f"{voz}.wav"):
        if p.exists():
            return p
    return None


def instalar(voz):
    nome, tipo, parecida, resumo, tom, bordoes = VOZES_DICT.get(voz) or _entrada_automatica(voz)
    CONSENTIMENTO_DE.setdefault(voz, "dona registrou o consentimento do dono da voz (aprovada no _vereditos.json)")
    src, dst = ORIGEM / voz, VOZES / voz
    pths, idxs = sorted(src.glob("*.pth")), sorted(src.glob("*.index"))
    if not pths:
        return f"{voz}: SEM .pth em {src} (ainda não treinada?) — pulada"
    amostra = _amostra(voz)
    if not amostra:
        return f"{voz}: SEM amostra aprovada (falas\\{voz}.wav) — pulada"
    f0 = vc.tom_medio(amostra)
    if not parecida:
        parecida = _parecida_pelo_tom(f0)
    dst.mkdir(parents=True, exist_ok=True)
    if idxs:
        shutil.copyfile(idxs[0], dst / f"{voz}.index")
    (dst / "f0.txt").write_text(f"{f0:.1f}\n", encoding="utf-8")
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    (dst / "personagem.json").write_text(json.dumps({
        "nome": nome, "tipo": tipo, "amostra_aprovada": str(amostra), "f0": round(f0, 1),
        "fonte_tom": "medido na amostra aprovada", "tem_index": bool(idxs), "bases": ["kokoro"],
        "aprovada_em": "16-18/11/2026 (_vereditos.json)", "instalada_em": agora}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (dst / "linguagem_v2.json").write_text(json.dumps({
        "resumo": resumo, "tom": tom, "bordoes": bordoes, "bordoes_iconicos": bordoes[:2]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    (dst / "consentimento.json").write_text(json.dumps({
        "voz": voz, "nome": nome, "consentimento": CONSENTIMENTO_DE[voz], "registrado_em": agora},
        ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.copyfile(pths[0], dst / f"{voz}.pth")  # por último: só agora a voz conta como instalada
    for b in BASES:
        (dst / f"tom_{b}.txt").unlink(missing_ok=True)  # recalcula com o f0 medido agora
        vc.tom_fixo(voz, b)
    # nota por nicho: a mesma da voz parecida (sem ela, a voz fica com nota 1 em tudo)
    try:
        tab = json.loads(NICHOS.read_text(encoding="utf-8"))
        if voz not in tab and parecida in tab:
            tab[voz] = dict(tab[parecida])
            tab[voz].pop("fora", None)
            NICHOS.write_text(json.dumps(tab, ensure_ascii=False, indent=1), encoding="utf-8")
    except (OSError, ValueError) as e:
        print(f"{voz}: nota por nicho não gravada ({e})", flush=True)
    # registro geral dos consentimentos
    try:
        reg = json.loads(REGISTRO.read_text(encoding="utf-8")) if REGISTRO.exists() else {}
    except ValueError:
        reg = {}
    reg[voz] = {"nome": nome, "consentimento": CONSENTIMENTO_DE[voz], "registrado_em": agora}
    REGISTRO.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    # cache do Kaggle (Drive central)
    r = subprocess.run([RCLONE, "copy", str(dst), f"manhwa-drive:colab_recap/vozes/{voz}", "--exclude", "_NO_DRIVE.md"],
                       capture_output=True, text=True, timeout=900)
    tons = " ".join(f"{b.split('_', 1)[1]}{int((dst / f'tom_{b}.txt').read_text()):+d}" for b in BASES)
    return f"{voz}: instalada (f0 {f0:.0f} Hz; tons {tons}; nicho como {parecida}; Kaggle {'ok' if r.returncode == 0 else 'FALHOU'})"


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:] or ["--listar"]
    if args == ["--listar"]:
        print("=== VOZES_DICT (11 do lote 18/11) ===")
        for v in VOZES_DICT:
            print(f"  {v:28} origem {'ok' if list((ORIGEM / v).glob('*.pth')) else 'SEM .pth'} | amostra "
                  f"{'ok' if _amostra(v) else 'falta'} | produção {'sim' if (VOZES / v / f'{v}.pth').exists() else 'não'}")
        pend = _aprovadas_pendentes()
        if pend:
            print(f"\n=== APROVADAS PENDENTES (_vereditos.json → falta instalar): {len(pend)} ===")
            for v in pend:
                print(f"  {v:28} amostra {'ok' if _amostra(v) else 'FALTA'}")
        else:
            print("\n(nenhuma aprovada pendente de instalação)")
        # Vozes com amostra sem veredito (prontas pra dona aprovar)
        try:
            ver = json.loads(VEREDITOS.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            ver = {}
        sem_veredito = []
        for f in sorted((ORIGEM / "falas").glob("*.wav")):
            v = f.stem
            if v not in ver and not (VOZES / v / f"{v}.pth").exists():
                sem_veredito.append(v)
        if sem_veredito:
            print(f"\n=== COM AMOSTRA, SEM VEREDITO (esperando a dona ouvir): {len(sem_veredito)} ===")
            for v in sem_veredito:
                tem_pth = "tem .pth" if list((ORIGEM / v).glob("*.pth")) else "SEM .pth"
                print(f"  {v:28} {tem_pth}")
        return
    if args == ["--novas"]:
        # 18/11: todas as aprovadas no _vereditos.json que já têm modelo e ainda não estão na produção (o vigia do
        # treino baixa o modelo; a dona aprova ouvindo; isto põe em produção). Para rodar sozinho depois de cada lote.
        alvo = _aprovadas_pendentes()
        print(f"aprovadas pendentes: {len(alvo)} {alvo}", flush=True)
    else:
        alvo = list(VOZES_DICT) if args == ["todas"] else args
    for v in alvo:
        print(instalar(v), flush=True)


if __name__ == "__main__":
    main()
