# -*- coding: utf-8 -*-
r"""tools/saude.py — o "navegador sem navegador" está funcionando MESMO? (dona 29/10: "é invisível; hoje se um PC para
eu vejo porque ele não abre mais as janelas; esse aí não vai ter como — então quero ver os logs no painel").

Testa de verdade, por HTTP e SEM abrir Chrome nunca (cookie morto = marca "morto", não ressincroniza), 1 leitura leve
por conta:
  youtube   Studio: GET studio.youtube.com com os cookies de D:\gemini-argo\cookies_youtube\<slug>.json → tem CHANNEL_ID?
  tiktok    TikTok Studio: /tiktokstudio/api/web/user → userId? (cookie do cofre, proxy da conta)
  instagram GET instagram.com/<conta>/ com o cookie do cofre (TLS do Chrome) → DTSG e não "not-logged-in"?
  fotos     GET photos.google.com → SNlM0e?
  flow      GET flow.google.com com cookies/flow_<conta>.json → SNlM0e? (+ créditos quando dá). Esse arquivo é renovado
            a cada geração por HTTP (flow_gerar.FlowGerador.colher) ou por `flow_gerar <conta> colher`.
  flow@maq  (29/10, D30) o mesmo NAS máquinas (notebooks/PC2), com os cookies de lá: 1 ssh por máquina roda
            services/veo_flow/saude_flow.py e cada perfil vira "flow <perfil>@<maquina>" no painel.
Por hora: TODOS os canais do YouTube (é o nosso Studio, barato) e uma AMOSTRA rotativa de TikTok (6) e Instagram (3) —
nada de rajada. Resultado: relatorios\saida\saude.json (por serviço/conta: vivo, ms, erro, desde quando, última vez
vivo) + logs\saude.jsonl (1 linha por teste) + Telegram só quando MUDA (vivo→morto, morto→vivo) pelo avisos.py.
O painel (:8790, aba "Sem navegador") e o melhorador central leem o saude.json.

    python tools\saude.py              # rodada normal (amostra)
    python tools\saude.py --todos      # testa tudo (lento; 1 vez por dia basta)
    python tools\saude.py --mostrar    # imprime o estado
Tarefa: NSN_Saude (a cada 60 min).
"""
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401 — nenhum processo filho abre janela
import requests  # noqa: E402
from core.cofre_cookies import ler, sessao  # noqa: E402

SAIDA = ROOT / "relatorios" / "saida" / "saude.json"
LOG = ROOT / "logs" / "saude.jsonl"
COOKIES_YT = Path(r"D:\gemini-argo\cookies_youtube")
MAPA_YT = Path(r"D:\postador-de-videos\config\youtube_navegador.json")
REUSO = Path(r"D:\postador-de-videos\config\reuso_plataformas.json")
COOKIES_FLOW = ROOT / "cookies"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36")
AMOSTRA = {"tiktok": 6, "instagram": 3}
MORTA_H = 24  # 31/10: só depois disso a conta vai pro resumo de pendências humanas


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def _log(reg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")


# ───────── testes (nunca abrem Chrome) ─────────
def t_youtube(slug):
    arq = COOKIES_YT / f"{slug}.json"
    if not arq.exists():
        return False, "sem cookies (youtube_http.py sync)"
    s = requests.Session()
    s.headers["User-Agent"] = UA
    s.cookies.update(json.loads(arq.read_text("utf-8")))
    r = s.get("https://studio.youtube.com/", timeout=30)
    if '"CHANNEL_ID":"' in r.text:
        return True, ""
    return False, "login caiu (sem CHANNEL_ID)" + (" — accounts.google.com" if "accounts.google.com" in r.url else "")


def t_tiktok(conta):
    from services.tiktok.studio import TikTokStudio
    try:
        t = TikTokStudio(conta, navegador=False)
    except KeyError as e:
        return None, f"conta sem {e} no reuso_plataformas (não testável)"
    except RuntimeError as e:
        msg = str(e)
        return (None, "sem cookie salvo no nsn (cookies_todos)") if "sem_login" in msg and "ausente" in msg else (False, msg[:120])
    u = t._user()
    return (True, f"@{t.arroba}") if u.get("userId") else (False, "não reconheceu o login")


def t_instagram(conta):
    perfil = f"ig_{conta}"
    d = ler(perfil)
    if not d:
        return None, "sem cookie salvo no nsn (pegar) — não testável"
    if not any(c.get("name") == "sessionid" for c in d.get("cookies", [])):
        return False, "cookie salvo sem sessionid (deslogado)"
    s = sessao(perfil, ["instagram.com"], chrome_tls=True)
    r = s.get(f"https://www.instagram.com/{conta}/", timeout=30)
    if r.status_code == 429:
        return None, "429 (não conta como morto)"
    h = r.text
    if "not-logged-in" in h[:3000] or "/accounts/login" in str(r.url):
        return False, "deslogado"
    return (True, "") if re.search(r'"dtsg":\{"token":"|"DTSGInitialData"', h) else (False, f"sem DTSG (HTTP {r.status_code})")


def t_fotos(conta):
    d = ler(conta)
    if not d:
        return None, "sem cookies no nsn (pegar) — não testável"
    if not any(c.get("name") in ("SID", "__Secure-1PSID") and "google.com" in c.get("domain", "") for c in d.get("cookies", [])):
        return None, "cookie salvo só do TikTok (sem Google) — não testável"
    s = sessao(conta, ["google.com"])
    r = s.get("https://photos.google.com/", timeout=30)
    if "accounts.google.com" in str(r.url) or '"SNlM0e":"' not in r.text:
        return False, "pediu login"
    return True, ""


def t_flow(conta):
    arq = COOKIES_FLOW / f"flow_{conta}.json"
    if not arq.exists():
        return False, "sem cookies/flow_<conta>.json"
    from services.veo_flow.flow_http import FlowHTTP
    try:
        f = FlowHTTP(json.loads(arq.read_text("utf-8")))
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:120]
    try:
        cr = f.creditos()
    except Exception:  # noqa: BLE001
        cr = None
    return True, f"créditos {cr}" if cr is not None else "logado (créditos não lidos)"  # antes: "créditos None"


TESTES = {"youtube": t_youtube, "tiktok": t_tiktok, "instagram": t_instagram, "fotos": t_fotos, "flow": t_flow}


def flow_maquinas(est):
    """29/10 (D30): o Flow por HTTP roda NOS notebooks/PC2 com os cookies DE LÁ (nunca saem). A saúde pergunta a cada
    máquina (1 ssh, saude_flow.py lá) e registra como flow "<perfil>@<maquina>" — a aba do painel mostra por máquina.
    Máquina fora do ar: mantém o último estado dela (não vira "morto": é a máquina, não o login)."""
    sys.path.insert(0, r"D:\postador-de-videos\bin")
    try:
        import maquina_remota as mr
    except ImportError:
        return []
    mudancas = []
    for nome in mr.MAQUINAS:
        r = mr.Remoto(nome)
        try:
            if not r.vivo() or not r.nsn_flow_pronto():
                continue
            itens = r.nsn_flow_saude()
        except Exception as e:  # noqa: BLE001
            print(f"flow@{nome}: {type(e).__name__}", flush=True)
            continue
        for it in itens:
            servico = it.get("servico") or "flow"  # D31: o worker também testa o Instagram da máquina
            perfil = it["perfil"][3:] if servico == "instagram" and it["perfil"].startswith("ig_") else it["perfil"]
            conta = f"{perfil}@{nome}"
            vivo, obs, ms = it.get("vivo"), it.get("obs", ""), it.get("ms", 0)
            if it.get("colhido"):
                obs = f"{obs} (cookie colhido {it['colhido']})"
            ant = (est.get(servico) or {}).get(conta) or {}
            reg = {"em": datetime.now().isoformat(timespec="seconds"), "vivo": vivo, "ms": ms, "obs": obs,
                   "ultimo_vivo": ant.get("ultimo_vivo"), "desde": ant.get("desde"), "maquina": nome}
            if vivo:
                reg["ultimo_vivo"] = reg["em"]
            _mudanca(servico, conta, vivo, obs, ant, reg, mudancas)
            est.setdefault(servico, {})[conta] = reg
            _log({"servico": servico, "conta": conta, **reg})
            print(f"{servico:<9} {conta:<28} {'vivo' if vivo else ('?' if vivo is None else 'MORTO'):<6} {ms:>6} ms {obs}", flush=True)
    return mudancas


def alvos():
    yt = sorted((_ler(MAPA_YT, {}).get("canais") or {}).keys())
    reuso = _ler(REUSO, {})
    tk = sorted((reuso.get("tiktok", {}).get("contas") or {}).keys())
    ig = sorted((reuso.get("instagram", {}).get("contas") or {}).keys())
    fl = sorted(p.stem[5:] for p in COOKIES_FLOW.glob("flow_*.json")) if COOKIES_FLOW.is_dir() else []
    # 29/10 (Fable): Fotos só nas contas que o fotos_http/catalogo_visao usam de fato (antes: as 3 primeiras cofre_*,
    # que não eram as usadas e apareciam "mortas" no painel sem significar nada)
    fo = [c for c in FOTOS_CONTAS if (COOKIES_FLOW / f"cofre_{c}.json").exists()]
    return {"youtube": yt, "tiktok": tk, "instagram": ig, "flow": fl, "fotos": fo}


FOTOS_CONTAS = ["fabricadeautomacoesia"]


def _mudanca(servico, conta, vivo, obs, ant, reg, mudancas):
    """31/10 (dona: "chega muito aviso de desconexão que logo volta"; "a lista de contas só vai pra pendências humanas
    em último caso; se voltarem, não precisa notificar"): CAIU/VOLTOU a cada teste virava 41 avisos em 4 dias
    (internet piscou = todas "caíram" e "voltaram"). Agora só a conta morta há mais de MORTA_H horas (o login
    automático do manter_cookies já tentou) entra no resumo, 1 vez; voltar não avisa."""
    if vivo is not None and ant.get("vivo") is not None and bool(vivo) != bool(ant.get("vivo")):
        reg["desde"] = reg["em"]
    elif ant.get("desde") is None and vivo is not None:
        reg["desde"] = reg["em"]
    reg["avisado"] = bool(ant.get("avisado")) and vivo is False
    if (vivo is False and not reg["avisado"] and reg.get("desde")
            and datetime.now() - datetime.fromisoformat(reg["desde"]) >= timedelta(hours=MORTA_H)):
        mudancas.append(f"{servico} {conta}: sem login há mais de {MORTA_H} h ({obs})")
        reg["avisado"] = True


def _amostra(est, servico, lista, n):
    """Os n que foram testados há mais tempo (rodízio) — nunca rajada."""
    quando = {c: ((est.get(servico) or {}).get(c) or {}).get("em") or "" for c in lista}
    return sorted(lista, key=lambda c: quando[c])[:n]


def rodar(todos=False):
    est = _ler(SAIDA, {})
    mudancas = []
    for servico, lista in alvos().items():
        if not lista:
            continue
        escolhidos = lista if (todos or servico not in AMOSTRA) else _amostra(est, servico, lista, AMOSTRA[servico])
        for conta in escolhidos:
            t0 = time.time()
            try:
                vivo, obs = TESTES[servico](conta)
            except Exception as e:  # noqa: BLE001
                vivo, obs = False, f"{type(e).__name__}: {str(e)[:100]}"
            ms = round((time.time() - t0) * 1000)
            ant = (est.get(servico) or {}).get(conta) or {}
            reg = {"em": datetime.now().isoformat(timespec="seconds"), "vivo": vivo, "ms": ms, "obs": obs,
                   "ultimo_vivo": ant.get("ultimo_vivo"), "desde": ant.get("desde")}
            if vivo:
                reg["ultimo_vivo"] = reg["em"]
            _mudanca(servico, conta, vivo, obs, ant, reg, mudancas)
            est.setdefault(servico, {})[conta] = reg
            _log({"servico": servico, "conta": conta, **reg})
            print(f"{servico:<9} {conta:<28} {'vivo' if vivo else ('?' if vivo is None else 'MORTO'):<6} {ms:>6} ms {obs}", flush=True)
            time.sleep(1.5 if servico in ("tiktok", "instagram") else 0.3)
    try:
        mudancas += flow_maquinas(est)
    except Exception as e:  # noqa: BLE001
        print(f"flow nas máquinas: {type(e).__name__}: {str(e)[:100]}")
    est["_resumo"] = resumo(est)
    est["_em"] = datetime.now().isoformat(timespec="seconds")
    _gravar(SAIDA, est)
    if mudancas:
        try:
            sys.path.insert(0, r"D:\video-fila")
            import avisos
            avisos.enviar("Contas sem login há mais de um dia (o login automático não resolveu):\n- "
                          + "\n- ".join(mudancas), origem="nsn", importante=False, html_ok=False,
                          chave="nsn:" + ";".join(mudancas)[:80])
        except Exception as e:  # noqa: BLE001
            print(f"aviso não saiu ({type(e).__name__})")
    return est


def resumo(est):
    out = {}
    for servico, contas in est.items():
        if servico.startswith("_"):
            continue
        vivos = sum(1 for r in contas.values() if r.get("vivo"))
        mortos = sum(1 for r in contas.values() if r.get("vivo") is False)
        out[servico] = {"vivos": vivos, "mortos": mortos, "total": len(contas)}
    return out


def mostrar():
    est = _ler(SAIDA, {})
    print(json.dumps(est.get("_resumo"), ensure_ascii=False), "em", est.get("_em"))
    for servico, contas in est.items():
        if servico.startswith("_"):
            continue
        for conta, r in sorted(contas.items()):
            print(f"{servico:<9} {conta:<28} {'vivo' if r.get('vivo') else ('?' if r.get('vivo') is None else 'MORTO'):<6} "
                  f"{r.get('em', '')[5:16]} {r.get('obs', '')[:60]}")


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--mostrar" in sys.argv:
        mostrar()
    else:
        rodar("--todos" in sys.argv)
