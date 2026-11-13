# -*- coding: utf-8 -*-
"""avisos_studio.py — vídeos BLOQUEADOS / com direitos autorais no Studio, pra todo canal (21/10).

Por quê: 21/10 ~6% dos Shorts recentes de 3 canais estavam "Bloqueado" (Dorama Noturno, hindi, CenaReact) e ninguém
lia isso — o parceiro contava como agendado e o dia ficava sem post. Aqui (4 canais por rodada, rodízio; mesma trava
do Chrome — youtube_studio_extras --avisos):
- vídeo com aviso novo -> config/bloqueados.json (o politica para de contar ele na vaga de publicação do dia; o
  parceiro marca a ficha como "bloqueado" e o canal volta a ser preenchido) + aviso pro dono pelo portão (avisos.py);
- a CAUSA vem da tabela "Reivindicações" do Studio (conteúdo/autor/tipo: Áudio, Melodia ou letra = música; Visual/
  Vídeo = imagem); trilhas do Short do parceiro vêm do log _parceiro_*.log ([TRILHA] antes de "[publish] alvo");
- anti-bloqueio (dono 21/10: "parar de usar o que causou, sozinho"): D:\\video-fila\\material_bloqueado.py tira de uso
  a trilha reivindicada (inclusive das prioritarias/, movida pra _bloqueadas/) e a fonte do parceiro com bloqueios
  repetidos por IMAGEM; o aviso diz o que saiu.

    python bin/avisos_studio.py [--canais "A,B"] [--ensaio]
"""
import argparse
import html
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
ROOT = BIN.parent
CONFIG = ROOT / "config"
BLOQ = CONFIG / "bloqueados.json"
ESTADO = CONFIG / "avisos_studio_estado.json"
DUPS = CONFIG / "avisos_studio_duplicados.json"  # vídeos "Duplicado" já avisados
LEDGER = ROOT / "logs" / "uploads_ledger.jsonl"
CURADORIA = Path(r"D:\hipercool-materiais\_curadoria")
SUSPEITAS = CURADORIA / "trilhas_suspeitas.json"
BLOCKLIST = CURADORIA / "copyright_blocklist.json"
PRIORITARIAS = Path(r"D:\hipercool-materiais\assets\trilhas\prioritarias")
LOGS_PARCEIRO = Path(r"D:\recapd-ambientes\producao\workspace\anime")
POR_RODADA = 4
MIN_BLOQUEIOS = 2


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(p).with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def canais():
    cad = _ler(CONFIG / "canais.json", {}).get("canais", {})
    return [v.get("nome") for v in cad.values() if v.get("nome") and v.get("navegador", True) is not False]


def _ledger():
    out = {}
    for ln in LEDGER.read_text(encoding="utf-8").splitlines() if LEDGER.exists() else []:
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("video_id"):
            out[r["video_id"]] = r
    return out


def trilhas_do_short(pasta):
    """Trilhas que o log do parceiro mostra pro Short publicado em `pasta` (as linhas [TRILHA] do bloco dele)."""
    alvo = f"[publish] alvo: {pasta}"
    for log in sorted(LOGS_PARCEIRO.glob("_parceiro_*.log"), reverse=True)[:6]:
        try:
            linhas = log.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for i, ln in enumerate(linhas):
            if ln.strip() == alvo:
                faixas = []
                for x in reversed(linhas[max(0, i - 400):i]):
                    if "publish OK" in x:
                        break
                    m = re.search(r"\[TRILHA\] Trecho \d+/\d+: .*?→ (.+)$", x)
                    if m:
                        faixas.append(m.group(1).strip())
                return list(reversed(faixas))
    return []


def _cred_do_canal(nome):
    """canais.json tem nome próprio ("Inovare Manga ind") e o leitor acha o canal pelo nome do cred ("YouTube
    inovaremanhwaverseind") — 21/10 dava "canal não encontrado". Liga pelo channel_id no mapa do navegador."""
    cid = next((v.get("channel_id") for v in _ler(CONFIG / "canais.json", {}).get("canais", {}).values()
                if v.get("nome") == nome), None)
    for e in _ler(CONFIG / "youtube_navegador.json", {}).get("canais", {}).values():
        if cid and e.get("channel_id") == cid and e.get("creds"):
            return e["creds"][0]
    return nome


def _ler_canal(nome, ja_lidos=()):
    try:
        p = subprocess.run([sys.executable, str(BIN / "youtube_studio_extras.py"), "--canal", _cred_do_canal(nome), "--avisos",
                            "--ja-lidos", ",".join(ja_lidos)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    except subprocess.TimeoutExpired:
        return {"erro": "timeout 1800 s"}
    m = re.search(r"^RESULTADO: (\{.*\})\s*$", p.stdout or "", re.M)
    return json.loads(m.group(1)) if m else {"erro": ((p.stderr or p.stdout or "")[-200:]).strip()}


def _avisar(texto, chave, importante=True):
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(texto, "studio", importante=importante, chave=chave)
    except Exception as e:  # noqa: BLE001
        print("aviso não saiu:", e)


AUDIO = ("Áudio", "Audio", "Melodia")
IMAGEM = ("Vídeo", "Video", "Visual")


def _causa(reivs):
    """Tabela de reivindicações do Studio -> {"tipo": musica|video|ambos, "conteudo", "reivindicacoes"} ou None."""
    if not reivs:
        return None
    tipos = {str(r.get("tipo")) for r in reivs}
    # "Melodia ou letra" (composição) também é música (21/10: Dorama/hindi/Filme Noturno)
    som = any(k in x.lower() for x in tipos for k in ("udio", "elodia", "letra", "música", "musica", "composi",
                                                      "melody", "lyric", "music"))
    img = bool(tipos & set(IMAGEM)) or "Audiovisual" in tipos
    return {"tipo": "ambos" if som and img else ("musica" if som else ("video" if img else "?")),
            "conteudo": "; ".join(f"{r.get('conteudo', '')} — {r.get('autor', '')} ({r.get('tipo')})" for r in reivs),
            "reivindicacoes": reivs}


def _material(vid, fonte, faixas, causa):
    try:
        if r"D:\video-fila" not in sys.path:
            sys.path.append(r"D:\video-fila")
        import material_bloqueado
        tirados = material_bloqueado.registrar(vid, fonte=fonte, trilhas=faixas, causa=causa)
        fora = bool(fonte) and material_bloqueado.bloqueios_da_fonte(fonte) >= material_bloqueado.FONTE_LIMITE
        return tirados, fora
    except Exception as e:  # noqa: BLE001
        print("material_bloqueado falhou:", e)
        return [], False


def processar(nome, achados, ensaio=False):
    bloq, susp, led = _ler(BLOQ, {}), _ler(SUSPEITAS, {}), _ledger()
    prio = {f.name.lower() for f in PRIORITARIAS.glob("*") if f.is_file()}
    novos = 0
    dups, dups_avisados = [], _ler(DUPS, [])
    for a in achados:
        vid = a.get("video")
        if a.get("aviso") == "Duplicado":  # só avisa: é upload repetido, não bloqueio (não libera vaga)
            if vid and vid not in dups_avisados:
                dups.append(a)
            continue
        causa = _causa(a.get("reivindicacoes"))
        if vid and vid in bloq:
            if causa and not bloq[vid].get("causa") and not ensaio:
                bloq[vid]["causa"] = causa
                tirados, fonte_fora = _material(vid, bloq[vid].get("fonte"), bloq[vid].get("trilhas") or [], causa)
                print(f"{nome}: causa de {vid} = {causa['conteudo']}")
                _avisar(f"🔎 Causa do bloqueio em {html.escape(nome)} ({html.escape(bloq[vid].get('titulo') or '')}): "
                        f"{html.escape(causa['conteudo'])}"
                        + "".join(f"\n🚫 saiu de uso: {html.escape(n)} — {html.escape(m)}" for _t, n, m in tirados),
                        "studio:causa:" + vid)
            continue
        if not vid:
            continue
        novos += 1
        r = led.get(vid, {})
        pasta = str(Path(r["caminho"]).parent) if r.get("caminho") else ""
        faixas = trilhas_do_short(pasta) if pasta and r.get("projeto") == "parceiro" else []
        bloq[vid] = {"canal": nome, "titulo": a.get("titulo"), "aviso": a.get("aviso"), "projeto": r.get("projeto"),
                     "pasta": pasta, "trilhas": faixas, "visto_em": datetime.now().isoformat(timespec="seconds")}
        print(f"{nome}: {a.get('aviso')} {vid} {a.get('titulo', '')[:60]} | trilhas {faixas}")
        if ensaio:
            continue
        fonte = None
        if pasta:
            pj = Path(pasta) / "postar.json"
            d = _ler(pj, None)
            if isinstance(d, dict):
                fonte = d.get("parceiro")
                d["bloqueado_studio"] = {"aviso": a.get("aviso"), "video_id": vid,
                                         "em": datetime.now().isoformat(timespec="seconds")}
                _gravar(pj, d)
        for f in faixas:
            susp.setdefault(f, [])
            if vid not in susp[f]:
                susp[f].append(vid)
        # anti-bloqueio (dono 21/10): o que causou sai de uso SOZINHO — fonte do parceiro e trilha (causa = tabela de
        # reivindicações lida acima)
        bloq[vid]["fonte"], bloq[vid]["causa"] = fonte, causa
        tirados, fonte_fora = _material(vid, fonte, faixas, causa)
        _avisar(f"⛔ <b>{html.escape(a.get('aviso', ''))}</b> no Studio — {html.escape(nome)}\n"
                f"{html.escape(a.get('titulo', ''))}\nhttps://studio.youtube.com/video/{vid}/copyright"
                + (f"\nCausa: {html.escape(str(causa.get('conteudo', '')))} ({causa.get('tipo')})" if causa else "")
                + (f"\nTrilhas: {html.escape(', '.join(faixas))}" if faixas else "")
                + "".join(f"\n🚫 saiu de uso: {html.escape(n)} — {html.escape(m)}" for _t, n, m in tirados)
                + (f"\n🚫 fonte {html.escape(fonte)} fora do rodízio do parceiro (bloqueios repetidos)" if fonte_fora else "")
                + "\n(a vaga do dia foi liberada pro próximo vídeo)", "studio:" + vid)
    if ensaio:
        return novos
    if dups:  # 23/10 (dono): 1 mensagem por canal, e cada vídeo só 1 vez (antes: 1 por vídeo, de novo a cada 12 h)
        _avisar(f"♊ <b>O YouTube achou {len(dups)} Short(s) parecido(s) com outros já postados</b>\n"
                f"Canal: {html.escape(nome)}\nO que significa: eles podem aparecer menos para as pessoas.\n"
                + "\n".join(f"- {html.escape(a.get('titulo', ''))}\n  https://studio.youtube.com/video/{a['video']}/edit"
                            for a in dups),
                "studio:dup:" + ",".join(sorted(a["video"] for a in dups)), importante=False)
        _gravar(DUPS, (dups_avisados + [a["video"] for a in dups])[-3000:])
    _gravar(BLOQ, bloq)
    _gravar(SUSPEITAS, susp)
    return novos


def rodada(lista=None, ensaio=False):
    est = _ler(ESTADO, {})
    alvo = lista or sorted(canais(), key=lambda n: est.get(n, ""))[:POR_RODADA]
    for nome in alvo:
        r = _ler_canal(nome, [v for v, x in _ler(BLOQ, {}).items() if x.get("causa")])
        if "erro" in r or not isinstance(r.get("avisos"), list):
            print(f"{nome}: {r}")
            if not ensaio:
                est[nome] = datetime.now().isoformat(timespec="seconds")  # canal com defeito não trava o rodízio
            continue
        n = processar(nome, r["avisos"], ensaio)
        print(f"{nome}: {len(r['avisos'])} com aviso, {n} novo(s)")
        if not ensaio:
            est[nome] = datetime.now().isoformat(timespec="seconds")
    if not ensaio:
        _gravar(ESTADO, est)


if __name__ == "__main__":
    if sys.stdout is not None and hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--canais", help="lista separada por vírgula (sem: rodízio de POR_RODADA)")
    ap.add_argument("--ensaio", action="store_true")
    a = ap.parse_args()
    rodada([x.strip() for x in a.canais.split(",")] if a.canais else None, a.ensaio)
