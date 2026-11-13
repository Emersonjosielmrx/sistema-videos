r"""reagendar_nobre.py — leva 1 Short JÁ AGENDADO de cada dia pro horário nobre do canal (13/11/2026).

Por quê: o 1º post das 21-22 h de Brasília rende muito mais no MESMO canal (INTELIGENCIA_SHORTS.md: Fio da Meada 3,1x,
CenaReact 2,9x, inovare manhwa br 5,1x, Bicho Noturno 106x, Curiosidades 197x). Mas 41 canal-dias dos próximos 7 dias
estavam agendados (regra antiga) SEM nenhum post nesse horário, e em 22 deles o dia já está no teto do canal — o
agendador não consegue pôr mais um. Não precisa subir nada: basta MUDAR O HORÁRIO do último Short do dia.

O que faz, por canal pt (do que mais rende pro que menos):
  - dia com post e sem nenhum às 21-22 h -> o ÚLTIMO Short do parceiro daquele dia vai pro horário nobre do cadastro
    (parceiro.json "horarios"), se nenhum outro vídeo do canal estiver a menos de 50 min dele;
  - muda por HTTP (o mesmo caminho do envio sem navegador: services/youtube/upload_http, metadata_update
    scheduledPublishing) e CONFERE relendo o Studio: tem de continuar PRIVADO e com o horário novo;
  - corrige o publish_at no registro de postagens (uploads_ledger.jsonl), no lugar, pra agenda continuar certa.
Nunca abre navegador nem colhe login: canal sem sessão HTTP viva é pulado. Só canal que JÁ enviou por HTTP deste PC
nas últimas 48 h (mesma saída de sempre). Conta do Kaggle nunca. Nunca publica: só troca a hora de um agendado.

    python reagendar_nobre.py            # ensaio: só mostra
    python reagendar_nobre.py --fazer    # faz (no máximo REAGENDAR_MAX por rodada, padrão 12)
Desligar: REAGENDAR_NOBRE=0 ou criar estado\reagendar_nobre.off. Log: logs\reagendar_nobre.log.
"""
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
LOG = BASE / "logs" / "reagendar_nobre.log"
DESLIGA = BASE / "estado" / "reagendar_nobre.off"
HTTP_LOG = Path(r"D:\postador-de-videos\logs\youtube_http.log")
MAXIMO = int(os.environ.get("REAGENDAR_MAX", "12"))
DIAS = 7
LONGE_S = 3000  # 50 min de qualquer outro vídeo do canal

sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")


def log(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")
    if sys.stdout:
        try:
            print(linha, flush=True)
        except (OSError, ValueError):
            pass


def _slugs_http(horas=48):
    """Canais que subiram por HTTP deste PC nas últimas `horas` (linha 'slug: subiu por HTTP' do youtube_http.log)."""
    out, corte = set(), datetime.now() - timedelta(hours=horas)
    try:
        for l in HTTP_LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-3000:]:
            m = re.match(r"\[(\d\d)/(\d\d) (\d\d):(\d\d):\d\d\] ([\w-]+): subiu por HTTP", l)
            if m and datetime(datetime.now().year, int(m.group(2)), int(m.group(1)), int(m.group(3)),
                              int(m.group(4))) >= corte:
                out.add(m.group(5))
    except (OSError, ValueError):
        pass
    return out


def candidatos():
    import parceiro_diario as p
    sys.path.insert(1, r"D:\postador-de-videos\bin")
    import politica as pol
    import youtube_web_poster as ywp
    c = p.cfg()
    rend = p._rendimento_canais()
    agora = datetime.now(p.FUSO_BR)
    dias = [agora.date() + timedelta(days=i) for i in range(0, DIAS + 1)]
    nobres = set(p.horas_nobres())
    if not nobres:
        return []
    bloq = set()
    try:
        bloq = set(pol.bloqueados())
    except Exception:  # noqa: BLE001
        pass
    posts = defaultdict(lambda: defaultdict(list))
    for l in p.LEDGER.read_text(encoding="utf-8").splitlines()[-9000:]:
        try:
            u = json.loads(l)
        except ValueError:
            continue
        q = p._dt(u.get("publish_at") or u.get("ts") or "")
        if q and q.astimezone(p.FUSO_BR).date() in dias and u.get("video_id") not in bloq:
            posts[u.get("canal_id")][q.astimezone(p.FUSO_BR).date()].append((q.astimezone(p.FUSO_BR), u))
    out = []
    for d in sorted(c["pt"], key=lambda d: -(rend.get(d["canal"]) or 0)):
        try:
            slug, _e = ywp.entrada_do_cred(d["canal"])
        except Exception:  # noqa: BLE001
            slug = None
        if not slug:
            continue
        tz = ZoneInfo(d["fuso"])
        slot = None
        for h in (d.get("horarios") or [d.get("horario")]):
            if not h:
                continue
            hh, mm = (int(v) for v in h.split(":"))
            if datetime(agora.year, agora.month, agora.day, hh, mm, tzinfo=tz).astimezone(p.FUSO_BR).hour in nobres:
                slot = (hh, mm)
                break
        if not slot:
            continue
        for dia in dias:
            ps = sorted(posts[d["canal"]][dia], key=lambda x: x[0])
            if not ps or any(q.hour in nobres for q, _u in ps):
                continue
            novo = datetime(dia.year, dia.month, dia.day, slot[0], slot[1], tzinfo=tz)
            if novo < agora + timedelta(minutes=90):
                continue
            meus = [(q, u) for q, u in ps if u.get("projeto") == p.PROJETO and u.get("video_id")
                    and (u.get("tipo") or "short") == "short" and q > agora + timedelta(minutes=45)]
            if not meus:
                continue
            q, u = meus[-1]
            if any(abs((novo - x).total_seconds()) < LONGE_S for x, uu in ps if uu is not u):
                continue
            out.append({"canal": d["nome"], "slug": slug, "rend": rend.get(d["canal"]) or 0, "video": u["video_id"],
                        "de": q, "para": novo.astimezone(p.FUSO_BR), "publish_at": u.get("publish_at")})
    return out


def _ledger_trocar(video_id, antigo, novo_dt):
    """Troca o publish_at da linha do vídeo NO LUGAR (mesmo número de bytes): não reescreve o arquivo, então quem está
    acrescentando linha ao mesmo tempo não perde nada. True = trocou."""
    import parceiro_diario as p
    novo = novo_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    if not antigo or len(antigo.encode()) != len(novo.encode()):
        return False
    chave, de = f'"video_id": "{video_id}"'.encode(), f'"publish_at": "{antigo}"'.encode()
    para = f'"publish_at": "{novo}"'.encode()
    with open(p.LEDGER, "r+b") as f:
        dados = f.read()
        i = dados.rfind(chave)
        if i < 0:
            return False
        ini = dados.rfind(b"\n", 0, i) + 1
        fim = dados.find(b"\n", i)
        fim = len(dados) if fim < 0 else fim
        j = dados.find(de, ini, fim)
        if j < 0:
            return False
        f.seek(j)
        f.write(para)
    return True


def _enviador(slug):
    """Sessão HTTP viva do canal, SEM abrir navegador (Enviador() colheria o login pelo Chrome do cofre)."""
    sys.path.insert(0, r"D:\gemini-argo")
    if r"D:\projeto-navegador-sem-navegador" not in sys.path:
        sys.path.append(r"D:\projeto-navegador-sem-navegador")
    from services.youtube import upload_http
    en = upload_http.Enviador.__new__(upload_http.Enviador)
    en.slug = slug
    en.st = upload_http._studio(slug)
    en.token = upload_http.token_sessao(slug)
    return en


def _kaggle(slug):
    try:
        sys.path.insert(0, r"D:\gemini-argo")
        import youtube_http
        sys.path.insert(1, r"D:\postador-de-videos\bin")
        import maquina_remota
        return bool(maquina_remota.conta_kaggle_viva(youtube_http._email(slug).split("@")[0]))
    except Exception:  # noqa: BLE001 — na dúvida, não mexe
        return True


def main():
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    fazer = "--fazer" in sys.argv
    if os.environ.get("REAGENDAR_NOBRE") == "0" or DESLIGA.exists():
        return 0
    cands = candidatos()
    vivos = _slugs_http()
    feitos = pulados = 0
    sessoes, falhou = {}, set()
    for o in cands:
        rot = f"{o['canal']}: {o['video']} {o['de']:%d/%m %H:%M} -> {o['para']:%d/%m %H:%M}"
        if o["slug"] not in vivos:
            pulados += 1
            if not fazer:
                log(f"[ensaio] {rot} — PULA (canal não envia por HTTP deste PC)")
            continue
        if not fazer:
            log(f"[ensaio] {rot}")
            continue
        if feitos >= MAXIMO:
            break
        if o["slug"] in falhou:
            continue
        if _kaggle(o["slug"]):
            log(f"{rot} — pulado (conta do Kaggle ou não consegui conferir)")
            continue
        try:
            en = sessoes.get(o["slug"]) or _enviador(o["slug"])
            sessoes[o["slug"]] = en
            v = next((x for x in en.st.videos(80) if x["id"] == o["video"]), None)
            novo = int(o["para"].timestamp())
            if not v or v["privacidade"] != "private" or not v["agendado_para"]:
                log(f"{rot} — pulado (no Studio não está privado+agendado: {v and v['privacidade']})")
                continue
            if v["agendado_para"] != novo:
                if abs(v["agendado_para"] - int(o["de"].timestamp())) > 1200:
                    log(f"{rot} — pulado (o Studio mostra outro horário: "
                        f"{datetime.fromtimestamp(v['agendado_para']):%d/%m %H:%M})")
                    continue
                en._metadados(o["video"], flowType="MDE_FLOW_TYPE_EDIT",
                              scheduledPublishing={"set": {"timeSec": str(novo), "privacy": "PUBLIC"}})
                ok = False
                for espera in (2, 4, 6):
                    time.sleep(espera)
                    d = next((x for x in en.st.videos(80) if x["id"] == o["video"]), None)
                    if d and d["privacidade"] == "public":
                        en._metadados(o["video"], flowType="MDE_FLOW_TYPE_EDIT", privacyState={"newPrivacy": "PRIVATE"})
                        log(f"[!] {rot} — ficou PÚBLICO, voltei pra privado. PAREI.")
                        DESLIGA.write_text("vídeo ficou público ao reagendar — conferir", encoding="utf-8")
                        return 2
                    if d and d["agendado_para"] == novo and d["privacidade"] == "private":
                        ok = True
                        break
                if not ok:
                    log(f"[!] {rot} — o Studio não confirmou o horário novo; registro não mexido")
                    continue
            led = _ledger_trocar(o["video"], o["publish_at"], o["para"])
            feitos += 1
            log(f"OK {rot} (rend {o['rend']:.0f}){'' if led else ' — [!] registro de postagens NÃO atualizado'}")
            time.sleep(8)
        except Exception as e:  # noqa: BLE001
            log(f"{rot} — falhou ({type(e).__name__}: {str(e)[:140]}) — não tento os outros deste canal nesta rodada")
            falhou.add(o["slug"])
    log(f"{'feitos' if fazer else 'ensaio'}: {feitos if fazer else len(cands) - pulados} | sem HTTP neste PC: {pulados} "
        f"| candidatos: {len(cands)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
