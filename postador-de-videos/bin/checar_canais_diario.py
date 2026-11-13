#!/usr/bin/env python3
"""checar_canais_diario.py — P04/HC-07 (22/10): todo dia de madrugada confere se cada canal que posta pelo navegador
(config\\youtube_navegador.json usar=true, canal ATIVO no cadastro) abre o Studio LOGADO e no canal certo — antes do
pico, e não na hora de subir (até aqui conta deslogada só aparecia quando o upload falhava).

1 Chrome por vez, pela trava do postador (youtube_studio_extras.sessao: não briga com upload). Resultado em
logs\\checar_canais.json (o painel lê); aviso pelo portão D:\\video-fila\\avisos.py: problema de login/permissão ou
aviso de direitos autorais parado no Studio = importante (o dono resolve: python D:\\logins-google\\cofre.py logar
<conta>); tudo ok = só no resumo. Roda 1x por dia, entre 04:00 e 08:59: o VigiaVideos chama de hora em hora e fora
da janela (ou já feito hoje) sai na hora.

    python checar_canais_diario.py                          respeita a janela e o "já feito hoje"
    python checar_canais_diario.py --agora [--canal SLUG]   na mão: ignora a janela; --canal = só esse
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
ROOT = BIN.parent
sys.path.insert(0, str(BIN))
RESULTADO = ROOT / "logs" / "checar_canais.json"
LOG = ROOT / "logs" / "checar_canais.log"
JANELA = (4, 8)  # horas (inclusive) em que a rodada automática pode começar


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    tmp = Path(p).with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def _alvos(so=None):
    """[(slug, entrada do mapa)] dos canais pelo navegador que estão ATIVOS (parado de propósito não é conferido)."""
    import politica
    import youtube_web_poster as yw
    creds = {c["id"]: c for c in politica.carregar_creds()}
    parados = set()
    for x in (_ler(ROOT / "config" / "canais.json", {}).get("canais") or {}).values():
        if politica.estado_do_cadastro(x, creds) != "ativo":
            parados |= set(x.get("creds") or [])
    out = []
    for slug, e in (yw.ler_mapa().get("canais") or {}).items():
        if not e.get("usar") or (so and slug != so):
            continue
        if not so and e.get("creds") and all(c in parados for c in e["creds"]):
            continue
        out.append((slug, e))
    return out


def checar_um(slug, e):
    """(status, detalhe): ok | login | direitos | erro."""
    import youtube_studio_extras as yx
    import youtube_web_poster as yw
    if not e.get("channel_id"):
        return "erro", "sem channel_id no mapa (rode youtube_web_poster.py --montar-mapa)"
    try:
        with yx.sessao(e) as pg:
            try:
                yw._abrir_studio(pg, e["channel_id"])
                return "ok", f"abre o canal '{yw._nome_canal(pg) or '?'}'"
            except yw.Falha as f:
                yw._shot(pg, f"checar_{slug}")
                if f.status == "morto":
                    return "login", str(f)
                if "direitos autorais" in str(f):
                    return "direitos", str(f)
                return "erro", str(f)
    except yw.Falha as f:  # a conta nem abriu (cofre sem login, Chrome não subiu)
        return ("login" if f.status == "morto" else "erro"), str(f)
    except Exception as ex:  # noqa: BLE001
        return "erro", f"{type(ex).__name__}: {str(ex)[:160]}"


def rodada(agora_forcado=False, so=None):
    hoje = datetime.now().date().isoformat()
    res = _ler(RESULTADO, {})
    if not agora_forcado:
        if res.get("dia") == hoje and res.get("completa"):
            return None
        if not JANELA[0] <= datetime.now().hour <= JANELA[1]:
            return None
    alvos = _alvos(so)
    log(f"checagem diária de login: {len(alvos)} canal(is)" + (f" (só {so})" if so else ""))
    canais = dict(res.get("canais") or {}) if so else {}
    for slug, e in alvos:
        t0 = time.time()
        st, det = checar_um(slug, e)
        if st == "erro":  # Chrome/página lenta acontece: 1 nova tentativa antes de acusar
            st, det = checar_um(slug, e)
        canais[slug] = {"status": st, "detalhe": det[:300], "quando": datetime.now().isoformat(timespec="minutes"),
                        "conta": e.get("email"), "s": round(time.time() - t0)}
        log(f"  {slug:24} {st.upper():8} {det[:140]}")
    res = {"dia": hoje, "completa": not so, "canais": canais, "fim": datetime.now().isoformat(timespec="minutes")}
    _gravar(RESULTADO, res)
    ruins = {k: v for k, v in canais.items() if v["status"] != "ok"}
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        if ruins:
            linhas = [f"- {k}: {v['status']} — {v['detalhe'][:150]}" + (
                f" (python D:\\logins-google\\cofre.py logar {str(v.get('conta') or '').split('@')[0]})"
                if v["status"] == "login" else "") for k, v in sorted(ruins.items())]
            avisos.enviar(f"Checagem de login dos canais: {len(ruins)} de {len(canais)} com problema\n" + "\n".join(linhas),
                          "checar_canais", importante=True, html_ok=False,
                          chave=f"checar_canais:{hoje}:{','.join(sorted(ruins))}")
        elif not so:
            avisos.enviar(f"Checagem de login dos canais: os {len(canais)} abrem o Studio logados no canal certo.",
                          "checar_canais", importante=False, html_ok=False, chave=f"checar_canais:{hoje}:ok")
    except Exception as ex:  # noqa: BLE001
        log(f"aviso não foi: {ex}")
    log(f"fim: {len(canais) - len(ruins)} ok, {len(ruins)} com problema")
    return res


def main():
    if sys.stdout:  # pythonw não tem console
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--agora", action="store_true", help="ignora a janela de 04-08 h e o 'já feito hoje'")
    ap.add_argument("--canal", help="só esse slug (do youtube_navegador.json)")
    a = ap.parse_args()
    rodada(a.agora, a.canal)


if __name__ == "__main__":
    main()
