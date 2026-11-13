"""persona_personagem.py — o PERSONAGEM narra do jeito dele, não "alguém com a voz dele" (dono, 22/10/2026).

Pedido do dono: "pra parar de ser alguém falando com a voz da personagem, no caso a Chiquinha narrando um vídeo, pra ser
a própria Chiquinha narrando do jeito dela — ela fala 'pois é, pois é, pois é', que é muito a cara dela".

Os guias linguagem_v2.json de personagem tinham bordões INVENTADOS genéricos (a Akali com "Foco na missão, zero vacilo")
e 8 vozes novas não tinham guia. Aqui o LLM devolve o que é REAL da dublagem/fala brasileira do personagem:
  bordoes_iconicos  frases que o público RECONHECE (só com certeza alta/média; nada inventado)
  maneirismos       jeitos de falar escritos COMO A VOZ DEVE LER (repetição por palavra inteira, nunca letra esticada)
  como_conta        como ESTE personagem contaria uma história em 1ª pessoa (de quem fala, com o que compara)
  referencias       pessoas/lugares do universo dele que ele citaria de passagem
  soaria_falso      o que ele NUNCA diria
Campos atuais do guia ficam; os novos entram por cima (backup <guia>.bkp_<data> antes). Voz SEM guia ganha o guia
completo. O monitor (recapd bin\\monitor_bordoes.py) tira depois o bordão que a voz fala estranho (`bordoes_estranhos`).

    python persona_personagem.py chiquinha           # uma voz
    python persona_personagem.py todos [--refazer]   # todas as de tipo personagem (pula as já feitas sem --refazer)
"""
import json
import shutil
import sys
import time
from pathlib import Path

VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
PULAR = {"lula"}  # dono 20/10: fora do rodízio
VERSAO = 2  # v2 (22/10): checagem cruzada (bordão de OUTRO personagem do mesmo programa sai) + sementes do dono
# o que o DONO sabe vale mais que o modelo: entra sempre, na frente; "remover" tira o que o modelo errou.
# Arquivo editável à mão (sem mexer em código): {voz: {"bordoes": [], "maneirismos": [], "remover": []}}
CORRECOES = Path(r"D:\hipercool-materiais\config\persona_correcoes.json")


def _correcoes():
    try:
        return json.loads(CORRECOES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

PROMPT_CHECAGEM = """Personagem: "{nome}". Abaixo, frases candidatas a bordão dele/dela (dublagem brasileira).
Para CADA uma responda se é dita pelo PRÓPRIO {nome} — e não por OUTRO personagem do mesmo programa/obra (erro comum:
misturar bordões de personagens do mesmo elenco). Devolva SÓ um JSON: {{"dele": [frases que são MESMO dele], "de_outro":
[{{"frase": "...", "de_quem": "..."}}]}}
Candidatas:
{lista}"""

PROMPT = """Você conhece a fundo a DUBLAGEM/FALA BRASILEIRA do personagem "{nome}".
Um vídeo de resumo de anime/manhwa/filme vai ser NARRADO PELO PRÓPRIO {nome}, em 1ª pessoa, do jeito dele. Devolva SÓ um JSON:
{{
 "bordoes_iconicos": [até 8 frases que o personagem REALMENTE diz na versão brasileira e que o público reconhece na hora; só com certeza; cada uma com "frase" e "certeza" ("alta"|"media")],
 "maneirismos": [até 6 falas CURTAS e LITERAIS (o TEXTO exato que ele diz, de 1 a 6 palavras) que são mania dele — repetição, interjeição, risada, choro escrito como palavra; é o que a voz vai LER em voz alta, então NUNCA descrição ("choro falso batendo o pé" é ERRADO; "pipipipipi" é certo) e NUNCA letra esticada ("nããão", "faaala")],
 "como_conta": "2 frases: como ESTE personagem contaria uma história — de que ponto de vista, com quem ele compara as cenas, que tipo de comentário ele solta",
 "referencias": [até 5 pessoas/lugares/coisas do universo dele que ele citaria de passagem (ex.: outro personagem, o lugar onde mora)],
 "soaria_falso": [até 5 coisas que ele NUNCA diria / jeitos que denunciam que não é ele],
 "resumo": "1 frase: quem ele é e como narraria",
 "tom": [3-4 adjetivos],
 "abertura": "como ELE abriria um vídeo (1 frase curta, com o jeito dele)",
 "contracoes": [até 6 formas faladas que ele usa: "tá", "pra"...],
 "interjeicoes": [até 6]
}}
Se você NÃO tiver certeza de bordões reais deste personagem, devolva "bordoes_iconicos": [] (é melhor vazio que inventado).
Nada de palavrão pesado nem piada de orientação sexual."""


def falavel(t):
    """A voz sintética lê isto sem soletrar? Letra esticada ("Eeeh", "nããão") e sílaba picada com hífen
    ("U-ur-ru-ru") viram "a-a-a" na voz (dono 22/10). Repetição de SÍLABA inteira ("pipipipipi") e de palavra passa."""
    import re as _re
    return not (_re.search(r"([a-zà-ü])\1\1", t.lower()) or _re.search(r"\w-\w", t))


def _guia(voz):
    p = VOZES / voz / "linguagem_v2.json"
    try:
        return p, json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return p, {}


def _nome(voz):
    pj = next(iter((VOZES / voz).glob("personagem*.json")), None)
    try:
        return json.loads(pj.read_text(encoding="utf-8")).get("nome") or voz
    except (OSError, ValueError, AttributeError):
        return voz.replace("_", " ").title()


def gerar(voz, refazer=False):
    import claude_client
    caminho, guia = _guia(voz)
    if guia.get("persona_v") == VERSAO and not refazer:
        print(f"{voz}: já tem persona v{VERSAO} — pulado")
        return guia
    nome = _nome(voz)
    resp = None
    for tentativa in range(3):
        try:
            txt = claude_client.generate_text(PROMPT.format(nome=nome), max_tokens=2500, temperature=0.2,
                                              model=claude_client.strong_model(), timeout=180)
            resp = claude_client._extract_json(txt)
            if isinstance(resp, dict) and "maneirismos" in resp:
                break
        except Exception as e:  # noqa: BLE001
            print(f"{voz}: tentativa {tentativa + 1} falhou ({type(e).__name__}: {str(e)[:80]})")
        time.sleep(3)
    if not isinstance(resp, dict):
        print(f"{voz}: LLM não devolveu JSON — guia fica como estava")
        return guia
    if caminho.exists():
        shutil.copy2(caminho, caminho.with_name(f"linguagem_v2.json.bkp_{time.strftime('%Y%m%d')}"))
    bi = [b for b in resp.get("bordoes_iconicos") or [] if isinstance(b, dict) and b.get("frase")
          and b.get("certeza") in ("alta", "media")]
    candidatos = [b["frase"] for b in sorted(bi, key=lambda b: b["certeza"] != "alta")]
    # maneirismo = texto falável curto; descrição ("choro falso batendo o pé") cai fora
    man = [str(m).strip() for m in (resp.get("maneirismos") or []) if 0 < len(str(m).split()) <= 7
           and falavel(str(m))]
    # 2ª passada: bordão/maneirismo de OUTRO personagem do mesmo elenco sai (22/10: "foi sem querer querendo" do
    # Chaves tinha ido pra Chiquinha)
    de_outro = []
    try:
        lista = "\n".join(f"- {x}" for x in candidatos + man)
        chk = claude_client._extract_json(claude_client.generate_text(
            PROMPT_CHECAGEM.format(nome=nome, lista=lista), max_tokens=1500, temperature=0.0,
            model=claude_client.strong_model(), timeout=180)) if lista else {}
        if isinstance(chk, dict) and isinstance(chk.get("dele"), list):
            dele = {str(x).strip().lower() for x in chk["dele"]}
            de_outro = chk.get("de_outro") or []
            candidatos = [c for c in candidatos if c.strip().lower() in dele]
            man = [m for m in man if m.strip().lower() in dele]
    except Exception as e:  # noqa: BLE001
        print(f"{voz}: checagem cruzada falhou ({type(e).__name__}) — fica só o que tinha certeza alta")
        candidatos = [b["frase"] for b in bi if b["certeza"] == "alta"]
    semente = _correcoes().get(voz, {})
    fora = {str(x).strip().lower() for x in semente.get("remover", [])}
    candidatos = [c for c in dict.fromkeys(semente.get("bordoes", []) + candidatos) if c.strip().lower() not in fora]
    man = [m for m in dict.fromkeys(semente.get("maneirismos", []) + man) if m.strip().lower() not in fora]
    novo = dict(guia)
    novo.update({
        "tipo": "personagem", "canal": guia.get("canal") or nome,
        "bordoes_iconicos": candidatos,
        "maneirismos": man[:6],
        "barrados_de_outro": de_outro,
        "como_conta": resp.get("como_conta", ""), "referencias": resp.get("referencias") or [],
        "soaria_falso": resp.get("soaria_falso") or [], "persona_v": VERSAO,
        "persona_em": time.strftime("%Y-%m-%d %H:%M"),
    })
    for k in ("resumo", "tom", "abertura", "contracoes", "interjeicoes"):  # só preenche o que faltava
        if not novo.get(k) and resp.get(k):
            novo[k] = resp[k]
    if novo["bordoes_iconicos"]:  # os reais passam a ser os bordões que o roteiro usa
        novo.setdefault("bordoes_inventados_antigos", guia.get("bordoes") or [])
        novo["bordoes"] = novo["bordoes_iconicos"][:6]
    caminho.write_text(json.dumps(novo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{voz} ({nome}): {len(novo['bordoes_iconicos'])} bordões reais | maneirismos: "
          f"{' / '.join(novo['maneirismos'][:3])}")
    return novo


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    refazer = "--refazer" in sys.argv
    if not args:
        print(__doc__)
        return
    if args[0] == "todos":
        vozes = sorted(d.name for d in VOZES.iterdir() if d.is_dir() and any(d.glob("personagem*.json"))
                       and d.name not in PULAR)
    else:
        vozes = args
    for v in vozes:
        gerar(v, refazer)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
