"""anime_revisao.py — trava "análise do vídeo pronto" do recap de anime (copiada do hipercool, 16/10).

Por quê: em 16/10 o canal pt do hipercool levou advertência do YouTube ("Nudez e conteúdo sexual") por vídeo que
ninguém assistiu pronto. Recap de anime também pode ter fan service. Regra do hipercool: nada sobe sem veredito "ok"
daquele MESMO arquivo.

Usa o D:\\hipercool-videos\\bin\\revisao_video.py SEM copiar: roda num processo à parte com o Python do hipercool
(importar aqui poria o bin do hipercool na frente do sys.path e o recapd passaria a carregar os módulos de mesmo nome
de lá — foi assim que 2 pipelines quebraram em 16/10). O veredito fica em <video>.revisao.json (formato do hipercool).

Passo entre quadros: 0,5 s no Short (igual ao hipercool); 3 s no vídeo longo (40 min a 0,5 s = ~4.800 quadros x até
3 perguntas ao Gemini). ANIME_REVISAO_PASSO muda os dois.

  aplicar(postar_json)   revisa o vídeo do postar.json e grava "revisao" + "pronto" (só True com "ok").
  python bin/anime_revisao.py --pendentes   refaz os que ficaram sem "ok" (gateway fora, cota...).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HIPER_BIN = Path(r"D:\hipercool-videos\bin")
HIPER_PY = Path(r"D:\hipercool-videos\venv\Scripts\python.exe")
ANIMES_RECAP = Path(r"D:\hipercool-materiais\animes recap")

_SCRIPT = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import revisao_video as R
R.PASSO_S = float(sys.argv[3])
v = R.revisar(sys.argv[2])
print("VEREDITO " + json.dumps({"status": v.get("status"), "problemas": len(v.get("problemas") or []),
                                "quadros": v.get("quadros")}))
"""


def _duracao(mp4):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                           capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip())
    except (ValueError, OSError, subprocess.SubprocessError):
        return 0.0


def revisar(mp4, timeout=3600):
    """{"status": ok|reprovado|incompleto|erro, ...}. Nunca aprova no escuro."""
    mp4 = Path(mp4)
    passo = os.environ.get("ANIME_REVISAO_PASSO") or ("0.5" if _duracao(mp4) <= 180 else "3.0")
    py = str(HIPER_PY if HIPER_PY.exists() else sys.executable)
    try:
        r = subprocess.run([py, "-c", _SCRIPT, str(HIPER_BIN), str(mp4), passo], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, cwd=str(HIPER_BIN.parent))
        for linha in reversed((r.stdout or "").splitlines()):
            if linha.startswith("VEREDITO "):
                return json.loads(linha[len("VEREDITO "):])
        return {"status": "erro", "detalhe": (r.stderr or r.stdout or "")[-300:]}
    except subprocess.TimeoutExpired:
        return {"status": "erro", "detalhe": f"passou de {timeout} s"}
    except OSError as e:
        return {"status": "erro", "detalhe": str(e)}


def _avisar(texto):
    """Aviso pelo portão único do Telegram (D:\\video-fila\\avisos.py, regra de 19/10: nunca direto na API)."""
    try:
        import sys as _sys
        if r"D:\video-fila" not in _sys.path:
            _sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, "revisão do anime", importante=True)
    except Exception:  # noqa: BLE001 — aviso nunca derruba a revisão
        pass


_OFENSA = None
WORK = Path(r"D:\recapd-ambientes\producao\workspace\anime")


def _roteiro_ofende_publico(d):
    """11/11 (dona: o Patolino chamou de 'plateia insignificante'; 54 roteiros em 7 dias xingavam quem assiste):
    trecho do roteiro que deprecia a PLATEIA (não os personagens), ou None. Acha o roteiro pelo id da fonte.
    REVISAO_PUBLICO=0 desliga."""
    global _OFENSA
    if os.environ.get("REVISAO_PUBLICO", "1") == "0":
        return None
    import re
    if _OFENSA is None:
        _OFENSA = re.compile(
            r"(?i)plateia (insignificante|de (desocupados|infelizes|man[eé]s))|seus? (idiota|ignorante|infeliz|"
            r"desocupados|imprest[aá]veis|incompetentes|man[eé]|humanos)\b|povo ign[oó]bil|seres ignorantes|"
            r"\b(mortais|infeliz mortal)\b|\bvermes?\b[,!.]|gentalha|bando de (imprest[aá]veis|moscas)|"
            r"turminha sem cultura|queridos pentelhos|recrutas de meia-pataca|ser humaninho")
    import re as _re
    m = _re.search(r"(?:shorts/|v=|youtu\.be/)([\w-]{11})", str(d.get("fonte") or ""))
    if not m:
        return None
    for rot in WORK.glob(f"{m.group(1)}_*/roteiro.txt"):
        try:
            achou = _OFENSA.search(rot.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        if achou:
            return achou.group(0)
    return None


def aplicar(postar_json):
    """Revisa o vídeo do postar.json e grava o resultado nele. Devolve o status.

    22/10 (regra do dono de 18/10, igual ao hipercool postar_hipercool.py:421): SÓ nudez confirmada
    ("reprovado") segura o vídeo; erro/incompleto da análise AVISAM e o vídeo sobe mesmo assim —
    antes qualquer gateway fora deixava pronto=False pra sempre e o canal ficava sem post."""
    pj = Path(postar_json)
    d = json.loads(pj.read_text(encoding="utf-8"))
    mp4 = pj.parent / d["arquivo"]
    ofensa = _roteiro_ofende_publico(d)
    if ofensa:  # 11/11 dona: "plateia insignificante" não pode — segura sem gastar a análise de nudez
        d["revisao"], d["pronto"] = f"segurado (narrador deprecia a plateia — '{ofensa}')", False
        pj.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[revisao] {pj.parent.name}: {d['revisao']}")
        return d["revisao"]
    v = revisar(mp4)
    d["revisao"] = v.get("status")
    d["pronto"] = v.get("status") != "reprovado"
    pj.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[revisao] {mp4.name}: {v.get('status')} ({v.get('problemas', '?')} trecho(s) com nudez, "
          f"{v.get('quadros', '?')} quadros){' — ' + v['detalhe'] if v.get('detalhe') else ''}")
    if v.get("status") == "reprovado":
        _avisar(f"Análise REPROVOU {mp4.name} (nudez): segurado. Folha: {mp4.with_suffix('.revisao.jpg')}")
    elif v.get("status") != "ok":
        _avisar(f"Análise do {mp4.name} saiu '{v.get('status')}' ({str(v.get('detalhe', ''))[:120]}) — "
                "o vídeo SOBE mesmo assim (regra 18/10); conferir depois")
    return v.get("status")


def herdar(postar_json, pt_postar_json):
    """Versão em outra língua (anime_idiomas): a imagem é a MESMA da versão pt — só muda o texto por cima (legenda,
    gancho, @) — então herda o veredito dela em vez de perguntar de novo ao Gemini (~150 perguntas por versão)."""
    pj = Path(postar_json)
    d = json.loads(pj.read_text(encoding="utf-8"))
    try:
        st = json.loads(Path(pt_postar_json).read_text(encoding="utf-8")).get("revisao")
    except (OSError, ValueError):
        st = None
    d["revisao_de"] = str(pt_postar_json)
    d["revisao"] = f"{st} (herdada do pt)" if st else "pendente_pt"
    # 22/10: como no aplicar() — só "reprovado" (nudez) segura; erro/incompleto herdados sobem. Sem análise
    # do pt ainda (pendente_pt), continua segurando até o pt ser analisado.
    d["pronto"] = bool(st) and not str(st).startswith("reprovado")
    pj.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[revisao] {pj.parent.name}: {d['revisao']}")
    return d["revisao"]


def _herdeiros(pt_postar_json):
    """postar.json das versões em outra língua que herdam a análise deste."""
    alvo = Path(pt_postar_json).resolve()  # Path do Windows compara sem diferenciar maiúscula/barra
    for pj in ANIMES_RECAP.rglob("postar.json"):
        try:
            de = json.loads(pj.read_text(encoding="utf-8")).get("revisao_de")
            if de and Path(de).resolve() == alvo:
                yield pj
        except (OSError, ValueError):
            continue


def aprovar_manual(postar_json, quem):
    """Libera um vídeo REPROVADO depois que alguém olhou a folha <video>.revisao.jpg e viu que é alarme falso
    (16/10: um close de rosto suado e uma garota vestida foram marcados — a trava erra pro lado seguro)."""
    pj = Path(postar_json)
    d = json.loads(pj.read_text(encoding="utf-8"))
    mp4 = pj.parent / d["arquivo"]
    try:
        v = json.loads(mp4.with_suffix(".revisao.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print("[revisao] sem análise gravada — rode a análise antes de aprovar")
        return False
    from datetime import datetime
    d["revisao"], d["pronto"] = "ok_manual", True
    d["revisao_manual"] = {"por": quem, "em": datetime.now().isoformat(timespec="seconds"),
                           "quadros_marcados_s": [p.get("t") for p in v.get("problemas") or []]}
    pj.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[revisao] {mp4.name}: liberado à mão por {quem}")
    for h in _herdeiros(pj):  # as versões nas outras línguas têm a mesma imagem
        herdar(h, pj)
    return True


def main():
    if "--aprovar" in sys.argv:  # python bin/anime_revisao.py --aprovar <postar.json> <quem olhou a folha>
        i = sys.argv.index("--aprovar")
        aprovar_manual(sys.argv[i + 1], sys.argv[i + 2] if len(sys.argv) > i + 2 else "dono")
    elif "--pendentes" in sys.argv:
        for pj in sorted(ANIMES_RECAP.rglob("postar.json")):
            try:
                d = json.loads(pj.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            # 22/10 (R4): vídeo SEGURADO à mão (ex.: voz do Lula, 21/10) tem anotação livre na revisao;
            # a reanálise só olha nudez e NÃO sabe do motivo — então --pendentes não toca nele.
            if "segurado" in str(d.get("revisao") or "").lower():
                print(f"[revisao] {pj.parent.name}: segurado à mão — não reanaliso ({d.get('revisao')})")
                continue
            if d.get("revisao_de"):  # versão em outra língua: só reconfere o pt
                if not d.get("pronto") and not d.get("posted_url"):
                    herdar(pj, d["revisao_de"])
            elif d.get("revisao") not in (None, "ok", "ok_manual") and not d.get("posted_url"):
                aplicar(pj)
    elif len(sys.argv) > 1:
        aplicar(sys.argv[1])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
