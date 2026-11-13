# -*- coding: utf-8 -*-
"""anime_testes.py — TESTE GRADUAL de formatos e vozes nos Shorts reais (dona 23/10/2026).

Pedido: "cria um sistema de testes, vamos testando nos vídeos reais devagar e põe o vigia pra ir avaliando; conforme tal
personagem for se saindo bem podemos colocar aquele personagem ou modelo mais vezes". Config: config\\testes_voz.json.

Só entra Short de parceiro que já sairia com voz clonada (os outros são o CONTROLE "solo"):
  1. sortear(nicho): FRACAO dos Shorts vira teste. Itens: "formato:<chave>" (formatos_voz.json aprovados com uso
     producao/padrao_faustao) e "voz:<nome>" (personagem aprovado que quase nunca sai no rodízio: encaixe 1 no nicho;
     pessoa real fica fora). Quem vai em teste sai por Thompson no placar de 48 h (placar_testes_voz.json, o mesmo
     "venceu = views acima da mediana do canal" do funil): quem rende mais sai mais, os outros continuam tendo vez.
     PROMOVIDO (>= MIN_MEDIDAS e taxa >= solo + MARGEM) ganha FRACAO_PROMOVIDOS a mais (= "mais vezes").
     PAUSADO: taxa <= solo - MARGEM, soou mal RUINS_PAUSA vezes (metade ou mais) ou a dona/vigia pôs em "pausados".
  2. aplicar_formato(work, formato): a IA reescreve o roteiro como diálogo (anime_formatos); falhou = segue solo.
  3. conferir(work, video): transcreve o Short pronto e compara com o que devia ser dito. "circunflexo", erro da IA
     narrado ou fala comida (< MIN_SEMELHANCA das palavras) = ruim: o formato é refeito no SOLO (desfazer_formato) e a
     voz em teste é segurada (não sobe). Calibrado 23/10: amostras aprovadas 0,90-1,00; xaropinho com "circunflexo" 0,40.
  4. campos(teste, clone): vai no postar.json — teste_voz ("solo" | item), elenco, sintetico (pessoa real no elenco de
     um Short EM TESTE = marca "conteúdo alterado ou sintético" no YouTube; no solo só com marcar_sintetico_solo). O
     medidor de 48 h (notificar_telegram._placar_titulos) conta o teste_voz no placar. Pipeline/IA que quebra conta
     em falhas (contar_falha): FALHAS_PAUSA vezes = pausado.
  5. O vigia (D:\\video-fila\\avaliar_testes_voz.py, subvigia do vigia_geral) lê o registro (logs\\testes_voz.jsonl), a
     qualidade e o placar, escreve D:\\video-fila\\TESTES_VOZ_RELATORIO.md e avisa quando alguém é promovido/pausado.

  python anime_testes.py situacao          # placar de cada item (o que o vigia vê)
  python anime_testes.py sortear [nicho]   # 20 sorteios de exemplo (não grava nada)
"""
import difflib
import json
import logging
import os
import random
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
CONFIG = BIN.parent / "config" / "testes_voz.json"
FORMATOS = BIN.parent / "config" / "formatos_voz.json"
REGISTRO = BIN.parent / "logs" / "testes_voz.jsonl"
QUALIDADE = BIN.parent / "logs" / "testes_voz_qualidade.json"
VOZES = Path(r"D:\hipercool-materiais\models\rvc\vozes")
PLACAR, GRUPO = "testes_voz", "parceiro"
FALHAS_VALE_H = 48
USOS_FORMATO = ("producao", "padrao_faustao")
PADRAO = {"ligado": True, "fracao": 0.15, "parte_formatos": 0.67, "fracao_promovidos": 0.15, "min_medidas": 5,
          "margem": 0.1, "min_semelhanca": 0.6, "ruins_pausa": 2, "falhas_pausa": 3, "pausados": {}, "pessoas_reais": [],
          "marcar_sintetico_solo": False}


def cfg():
    c = dict(PADRAO)
    try:
        c.update(json.loads(CONFIG.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return c


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def _voz_ok(v, especial=False):
    """Aprovada pela dona (personagem.json; no formato vale também a só-especial) e com o modelo."""
    marcas = ("personagem.json", "personagem_especial.json") if especial else ("personagem.json",)
    return (VOZES / v / f"{v}.pth").exists() and any((VOZES / v / m).exists() for m in marcas)


def formatos():
    """{chave: formato} dos formatos que podem ir pra teste (aprovados, uso de produção, elenco todo aprovado)."""
    fs = _ler(FORMATOS, {}).get("formatos", {})
    return {k: f for k, f in fs.items() if f.get("aprovado_dono") and f.get("uso") in USOS_FORMATO
            and f.get("elenco") and all(_voz_ok(v, especial=True) for v in f["elenco"])}


def _bases_ok(v):
    """Bases da voz sem 2 falhas nas últimas 24 h (a mesma trava do rodízio normal, anime_voz_clonada._falhou)."""
    import anime_voz_clonada as avc
    est = avc._ler()
    rodada = est.get("rodada", 1)
    return [b for b in avc._bases_da(v) if not avc._falhou(est, f"{v}:{b}:r{rodada}")]


def vozes_em_teste(nicho=None, c=None):
    """Personagens aprovados que quase nunca saem no rodízio normal (encaixe 1 no nicho: o anime_voz_clonada só pega os
    de nota >= 2). Nota 0 = a dona/tabela disse que não encaixa: fica fora. Pessoa real fica fora (risco legal). Voz com
    todas as bases falhando nas últimas 24 h fica fora até passar."""
    import anime_voz_clonada as avc
    c = c or cfg()
    tabela = _ler(avc.ENCAIXE, {})
    fora = set(c.get("pessoas_reais") or []) | set(avc.FORA)
    out = []
    for v in avc._personagens():
        n = tabela.get(v) or {}
        fit = int(n.get(nicho, n.get("geral", 1)) if nicho else n.get("geral", 1))
        if v not in fora and fit == 1 and _bases_ok(v):
            out.append(v)
    return out


def situacao(itens=None, c=None):
    """{item: {testes, vitorias, taxa, ok, ruins, estado}} + "solo". estado: novo | testando | promovido | pausado."""
    import placar_titulos
    c = c or cfg()
    t = placar_titulos.taxas(PLACAR, GRUPO)
    q = _ler(QUALIDADE, {})
    st, sv = t.get("solo", (0, 0))
    solo = (sv + 1) / (st + 2)
    out = {"solo": {"testes": st, "vitorias": sv, "taxa": round(solo, 3), "estado": "controle"}}
    mm, mg = int(c["min_medidas"]), float(c["margem"])
    for item in itens if itens is not None else [k for k in t if k != "solo"]:
        tt, vv = t.get(item, (0, 0))
        taxa = (vv + 1) / (tt + 2)
        d = q.get(item, {})
        ok, ruins, falhas = d.get("ok", 0), d.get("ruins", 0), _falhas_recentes(d)
        if item in (c.get("pausados") or {}):
            estado = "pausado"
        elif ruins >= int(c["ruins_pausa"]) and ruins >= ok:
            estado = "pausado"
        elif falhas >= int(c["falhas_pausa"]) and falhas >= ok:  # quebra o pipeline/IA toda vez: não insiste
            estado = "pausado"
        elif tt >= mm and st >= mm and taxa <= solo - mg:
            estado = "pausado"
        elif tt >= mm and st >= mm and taxa >= solo + mg:
            estado = "promovido"
        else:
            estado = "testando" if tt or ok or ruins or falhas else "novo"
        out[item] = {"testes": tt, "vitorias": vv, "taxa": round(taxa, 3), "ok": ok, "ruins": ruins, "falhas": falhas,
                     "estado": estado}
    return out


FONTE_MIN_FORMATO_S = 35  # 23/10: fonte mais curta que isso = diálogo maior que o vídeo (imagem repete)


def sortear(nicho=None, canal=None, dur=None):
    """None (Short normal) ou o teste deste Short: {"item", "estado", "elenco", e "formato"/"nome" ou "voz"/"base"}."""
    c = cfg()
    forcar = os.environ.get("TESTE_VOZ_FORCAR", "").strip()  # ensaio: "formato:chaves_quico" / "voz:bulma"
    if not c.get("ligado") and not forcar:
        return None
    fs = formatos() if not dur or dur >= FONTE_MIN_FORMATO_S else {}  # fonte curta: só voz nova sozinha
    vs = vozes_em_teste(nicho, c)
    itens = [f"formato:{k}" for k in fs] + [f"voz:{v}" for v in vs]
    sit = situacao(itens, c)
    vivos = [i for i in itens if sit[i]["estado"] != "pausado"]
    promovidos = [i for i in vivos if sit[i]["estado"] == "promovido"]
    extra = float(c["fracao_promovidos"]) if promovidos else 0.0
    r = random.random()
    if forcar:
        if forcar not in itens:
            logging.warning(f"[testes] TESTE_VOZ_FORCAR={forcar} não é item válido — ignorado")
            return None
        pool = [forcar]
    elif r < extra:
        pool = promovidos
    elif r < extra + float(c["fracao"]):
        f_viv = [i for i in vivos if i.startswith("formato:")]
        v_viv = [i for i in vivos if i.startswith("voz:")]
        pool = f_viv if f_viv and (not v_viv or random.random() < float(c["parte_formatos"])) else v_viv
    else:
        return None
    if not pool:
        return None
    item = max(pool, key=lambda i: random.betavariate(sit[i]["vitorias"] + 1, sit[i]["testes"] - sit[i]["vitorias"] + 1))
    tipo, nome = item.split(":", 1)
    teste = {"item": item, "estado": sit[item]["estado"], "nicho": nicho, "canal": canal}
    if tipo == "formato":
        teste.update(formato=nome, nome=fs[nome]["nome"], elenco=list(fs[nome]["elenco"]))
    else:
        teste.update(voz=nome, base=(_bases_ok(nome) or [None])[0], elenco=[nome])
        if not teste["base"]:
            return None
    return teste


def aplicar_formato(work, formato):
    """Roteiro solo -> diálogo do formato (anime_formatos). True se deu; False = segue solo com o roteiro como estava."""
    import anime_formatos
    work = Path(work)
    try:
        falas = anime_formatos.reescrever_roteiro(work / "roteiro.txt", formato)
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[testes] formato {formato} não saiu ({type(e).__name__}: {str(e)[:120]}) — Short segue solo")
        return False
    tempos = work / "roteiro_tempos.json"
    if tempos.exists():  # os tempos eram das frases do solo
        tempos.replace(work / "roteiro_tempos_solo.json")
        # 26/10 (dono: fala nunca depois da cena): cada fala do diálogo herda o segundo da frase do solo que conta a
        # mesma parte (antes caía no corte "espalhado")
        try:
            solo = [l for l in (work / "roteiro_narrador.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
            dial = [l for l in (work / "roteiro.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
            t_solo = json.loads((work / "roteiro_tempos_solo.json").read_text(encoding="utf-8"))
            novos = alinhar_tempos(solo, t_solo, dial)
            if novos:
                tempos.write_text(json.dumps(novos), encoding="utf-8")
                logging.info(f"[testes] tempos do solo -> {len(novos)} falas do diálogo ({novos[0]:.0f}s..{novos[-1]:.0f}s)")
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[testes] não alinhei os tempos ({type(e).__name__}: {e}) — corte espalhado")
    logging.info(f"[testes] Short em teste no formato {formato}: {len(falas)} falas")
    return True


def alinhar_tempos(solo, t_solo, dial):
    """[segundo por fala do diálogo] ou None. Cada fala vai pra frase do solo com mais palavras em comum, sem voltar
    na história (até 3 frases à frente; sem palavra em comum = a posição proporcional); falas na mesma frase dividem o
    trecho até a frase seguinte."""
    if not solo or not dial or len(t_solo) < len(solo):
        return None
    sets = [set(w for w in _palavras(s) if len(w) > 3) for s in solo]
    idx, j = [], 0
    for i, f in enumerate(dial):
        pf = set(w for w in _palavras(f) if len(w) > 3)
        cand = range(j, min(len(solo), j + 4))
        k = max(cand, key=lambda c: (len(pf & sets[c]), -c))
        if not pf & sets[k]:
            k = max(j, min(len(solo) - 1, round(i * (len(solo) - 1) / max(1, len(dial) - 1))))
        idx.append(k)
        j = k
    out, i = [], 0
    while i < len(idx):
        k, g = idx[i], 1
        while i + g < len(idx) and idx[i + g] == k:
            g += 1
        ini = float(t_solo[k])
        fim = float(t_solo[k + 1]) if k + 1 < len(solo) else ini + 3.0 * g
        out += [round(ini + (fim - ini) * r / g, 2) for r in range(g)]
        i += g
    return out


def desfazer_formato(work):
    """Volta o Short pro solo: roteiro do narrador, tempos, e apaga o áudio/clipes do formato (senão seriam reusados)."""
    work = Path(work)
    for de, para in (("roteiro_narrador.txt", "roteiro.txt"), ("roteiro_tempos_solo.json", "roteiro_tempos.json"),
                     ("roteiro_falas.json", "roteiro_falas_desfeito.json")):
        if (work / de).exists():
            (work / de).replace(work / para)
    for p in [work / "audio_cache", work / "final_anime_short.mp4", *work.glob("clipes_*"), *work.glob("_semlegenda*"),
              *work.glob("_master_*")]:
        try:
            shutil.rmtree(p) if p.is_dir() else p.unlink(missing_ok=True)
        except OSError as e:
            logging.warning(f"[testes] não apaguei {p.name} ({e})")


def _palavras(t):
    t = unicodedata.normalize("NFKD", str(t or "").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", t).split()


def conferir(work, video, falas=None):
    """Transcreve o Short pronto e compara com o que devia ser dito. {"ok": True|False|None, "sem", "motivo", "ouvido"}.
    sem = parte das palavras do roteiro que se ouve, na ordem (palavra a mais, ex. o áudio do original, não pesa).
    ok=None = não deu pra conferir (Groq fora): não segura nada."""
    work, video = Path(work), Path(video)
    if falas is None:
        import anime_formatos
        falas = [x["fala"] for x in (anime_formatos.falas_do_video(work) or [])] or \
            [ln for ln in (work / "roteiro.txt").read_text(encoding="utf-8").splitlines() if ln.strip()]
    esperado = " ".join(falas)
    mp3 = work / "_conferir_teste.mp3"
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k",
                        str(mp3)], check=True, timeout=180, creationflags=0x08000000)
        import monitor_bordoes
        ouvido = monitor_bordoes._transcrever(mp3)
    except Exception as e:  # noqa: BLE001
        return {"ok": None, "motivo": f"não conferi ({type(e).__name__}: {str(e)[:80]})"}
    finally:
        mp3.unlink(missing_ok=True)
    if not ouvido.strip():
        return {"ok": None, "motivo": "transcrição vazia (Groq fora?)"}
    a, b = _palavras(esperado), _palavras(ouvido)
    sem = sum(m.size for m in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks()) / max(1, len(a))
    motivos = []
    if re.search(r"circunflex", ouvido, re.I) and not re.search(r"circunflex", esperado, re.I):
        motivos.append("falou 'circunflexo'")
    try:
        import anime_script
        if anime_script.resposta_de_erro(ouvido) and not anime_script.resposta_de_erro(esperado):
            motivos.append("erro/recusa da IA narrado")
    except Exception:  # noqa: BLE001
        pass
    if sem < float(cfg()["min_semelhanca"]):
        motivos.append(f"só {sem:.0%} do roteiro se entende")
    return {"ok": not motivos, "sem": round(sem, 2), "motivo": "; ".join(motivos), "ouvido": ouvido[:400]}


def contar_qualidade(item, q):
    """Placar de qualidade por item (o 'soou mal 2x = pausa'). q = resultado do conferir; ok=None não conta."""
    if not item or q.get("ok") is None:
        return
    d = _ler(QUALIDADE, {})
    x = d.setdefault(item, {"ok": 0, "ruins": 0})
    x["ok" if q["ok"] else "ruins"] += 1
    x["ultima"] = {"em": datetime.now().isoformat(timespec="seconds"), "sem": q.get("sem"), "motivo": q.get("motivo")}
    _gravar(QUALIDADE, d)


def contar_falha(item, motivo):
    """Pipeline ou IA do formato quebrou com este item (não é áudio ruim, é não sair): FALHAS_PAUSA vezes = pausado."""
    if not item:
        return
    d = _ler(QUALIDADE, {})
    x = d.setdefault(item, {"ok": 0, "ruins": 0})
    agora = datetime.now()
    # revisão 23/10: só valem as das últimas FALHAS_VALE_H (travas passageiras da máquina não pausam pra sempre)
    x["falhas_em"] = [t for t in x.get("falhas_em", []) if (agora - datetime.fromisoformat(t)).total_seconds()
                      < FALHAS_VALE_H * 3600] + [agora.isoformat(timespec="seconds")]
    x["falhas"] = len(x["falhas_em"])
    x["ultima_falha"] = {"em": agora.isoformat(timespec="seconds"), "motivo": str(motivo)[:200]}
    _gravar(QUALIDADE, d)


def _falhas_recentes(d):
    agora = datetime.now()
    return sum(1 for t in d.get("falhas_em", []) if (agora - datetime.fromisoformat(t)).total_seconds()
               < FALHAS_VALE_H * 3600)


def segurar(pasta, motivo):
    """Short em teste que soou mal NÃO sobe: pronto=False + revisao "reprovado (segurado)" (o parceiro_diario relê o
    postar.json antes de cada upload, L879). Já postado = só registra. True se segurou."""
    pj = Path(pasta) / "postar.json"
    d = _ler(pj, None)
    if not d or d.get("posted_url"):
        return False
    d.update(pronto=False, revisao=f"reprovado (segurado): teste de voz — {motivo}"[:300])
    _gravar(pj, d)
    logging.warning(f"[testes] {Path(pasta).name} SEGURADO: {motivo}")
    return True


def marcar_conferido(pasta, q):
    """Áudio já aprovado aqui: grava "conferido_audio" no postar.json pra conferência antes do upload
    (bin\\conferir_audio.py, da outra sessão) não transcrever o mesmo Short de novo. Só o ok=True."""
    if not q or q.get("ok") is not True:
        return
    pj = Path(pasta) / "postar.json"
    d = _ler(pj, None)
    if d is None or (d.get("conferido_audio") or {}).get("ok") is not None:
        return
    d["conferido_audio"] = {"ok": True, "sem": q.get("sem"), "por": "anime_testes",
                            "em": datetime.now().isoformat(timespec="seconds")}
    _gravar(pj, d)


def guardar_roteiro(work, pasta):
    """Copia o que devia ser dito pra pasta do Short (o work é apagado): o vigia confere de novo se a Groq falhou."""
    work, pasta = Path(work), Path(pasta)
    for nome, dest in (("roteiro_falas.json", "roteiro_falas.json"), ("roteiro.txt", "roteiro_teste.txt")):
        if (work / nome).exists():
            try:
                shutil.copy2(work / nome, pasta / dest)
            except OSError as e:
                logging.warning(f"[testes] não copiei {nome} ({e})")


def falas_da_pasta(pasta):
    """O que devia ser dito num Short em teste já publicado (roteiro_falas.json ou roteiro_teste.txt), ou None."""
    pasta = Path(pasta)
    f = _ler(pasta / "roteiro_falas.json", {}).get("falas")
    if f:
        return [x["fala"] for x in f]
    t = pasta / "roteiro_teste.txt"
    return [ln for ln in t.read_text(encoding="utf-8").splitlines() if ln.strip()] if t.exists() else None


def campos(teste, clone=None):
    """Campos do postar.json: teste_voz ("solo" = controle; anotado mesmo com ligado=false, só registra), elenco e
    sintetico (pessoa real no elenco). Revisão 23/10: no Short normal (solo) o sintetico só vale com
    marcar_sintetico_solo=true — mudar o upload de todo Short com voz de pessoa real é decisão da dona."""
    c = cfg()
    if teste:
        item, elenco = teste["item"], list(teste["elenco"])
    elif clone:
        item, elenco = "solo", [clone[0]]
    else:
        return {}
    reais = set(c.get("pessoas_reais") or [])
    marca = bool(teste) or bool(c.get("marcar_sintetico_solo"))
    return {"teste_voz": item, "elenco": elenco, "sintetico": marca and any(v in reais for v in elenco)}


def registrar(teste, pasta=None, qualidade=None, refeito_solo=False, falhou=None):
    """1 linha por Short em teste em logs\\testes_voz.jsonl (o vigia lê): item, pasta do postar.json, qualidade."""
    if not teste:
        return
    linha = {"quando": datetime.now().isoformat(timespec="seconds"), "item": teste["item"],
             "estado": teste.get("estado"), "nicho": teste.get("nicho"), "canal": teste.get("canal"),
             "pasta": str(pasta) if pasta else None, "qualidade": qualidade, "refeito_solo": refeito_solo,
             "falhou": falhou}
    try:
        REGISTRO.parent.mkdir(parents=True, exist_ok=True)
        with open(REGISTRO, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(linha, ensure_ascii=False) + "\n")
    except OSError as e:
        logging.warning(f"[testes] registro não gravou ({e})")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.path.insert(0, str(BIN))
    acao = sys.argv[1] if len(sys.argv) > 1 else "situacao"
    if acao == "situacao":
        itens = [f"formato:{k}" for k in formatos()] + [f"voz:{v}" for v in vozes_em_teste(None)]
        for k, s in situacao(itens).items():
            print(f"{k:42s} {s['estado']:10s} {s['vitorias']}/{s['testes']} (taxa {s['taxa']:.2f})"
                  + (f"  qualidade {s['ok']} ok / {s['ruins']} ruins" if "ok" in s else ""))
    elif acao == "sortear":
        nicho = sys.argv[2] if len(sys.argv) > 2 else None
        for _ in range(20):
            t = sortear(nicho)
            print(t["item"] if t else "-")
