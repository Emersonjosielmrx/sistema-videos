# -*- coding: utf-8 -*-
r"""tools/quero.py — quem comentar a palavra (padrão "QUERO") nos posts recentes recebe DM com o link e uma resposta no
comentário. Tudo por HTTP (services\instagram\postar.py). Cada comentário é atendido 1 vez só (logs\quero_<conta>.json).

    python tools\quero.py <conta> [--palavra QUERO] [--link URL] [--mensagem "texto com {link}"] [--posts 12]
                                  [--maximo 10] [--seco]
--seco: só mostra quem seria atendido. Sem --link usa o link da bio da conta (sem link nenhum: não roda).
Regra do Instagram (29/10): DM para quem não segue vira convite; até aceitar, só a 1ª mensagem passa.
30/10: no máximo --maximo atendimentos por rodada; a mesma pessoa recebe 1 DM por dia (comentou QUERO em 3 posts =
1 DM + 3 respostas); bloqueio de spam do Instagram (feedback_required) para a rodada na hora.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core.arquivo import gravar_json  # noqa: E402
from services.instagram.postar import InstagramPostar  # noqa: E402

MSG = "Oi! Aqui está o link que você pediu 👉 {link}"
RESPOSTA = "Te mandei no direct! 📩"
BLOQUEIO = ("feedback_required", "spam", "checkpoint", "login_required", "Limitamos", "try again later")


def _bloqueado(erro):
    return any(x.lower() in erro.lower() for x in BLOQUEIO)


def _dm_hoje(feitos, usuario):
    hoje = time.strftime("%Y-%m-%d")
    return any(r.get("usuario") == usuario and r.get("dm") and str(r.get("quando", "")).startswith(hoje)
               for r in feitos.values())


def _arg(a, nome, padrao=None):
    return a[a.index(nome) + 1] if nome in a else padrao


def main():
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    conta = a[0]
    from core.maquinas import ou_remoto  # 29/10 (D31): conta logada só numa máquina -> o robô roda LÁ (estado fica lá)
    if ou_remoto(f"ig_{conta}", "tools.quero") is not None:
        return
    palavra = _arg(a, "--palavra", "QUERO").casefold()
    seco = "--seco" in a
    maximo = int(_arg(a, "--maximo", 10))
    estado_arq = ROOT / "logs" / f"quero_{conta}.json"
    feitos = json.loads(estado_arq.read_text("utf-8")) if estado_arq.exists() else {}
    ig = InstagramPostar(conta)
    link = _arg(a, "--link") or ig.perfil_info().get("link") or ""
    if not link and not seco:  # DM "aqui está o link 👉 " sem link nenhum só queima a conta
        raise SystemExit(f"{conta}: sem --link e a bio não tem link — não mando DM vazia")
    msg = _arg(a, "--mensagem", MSG).format(link=link)
    atendidos = 0
    for p in ig.posts(int(_arg(a, "--posts", 12))):
        if not p["comentarios"]:
            continue
        media_id, cs = ig.comentarios(p["codigo"])
        for c in cs:
            cid = str(c["id"])  # 30/10: chave do JSON é texto; pk numérico nunca batia e a pessoa era atendida de novo
            if c["usuario"] == conta or cid in feitos or palavra not in (c["texto"] or "").casefold():
                continue
            print(f"{p['codigo']} @{c['usuario']}: {c['texto'][:60]!r}", "(seco)" if seco else "")
            if seco:
                continue
            if atendidos >= maximo:
                print(f"{conta}: limite de {maximo} por rodada; o resto fica para a próxima")
                return _fim(conta, atendidos, link)
            reg = {"post": p["codigo"], "usuario": c["usuario"], "quando": time.strftime("%Y-%m-%d %H:%M")}
            if _dm_hoje(feitos, c["usuario"]):
                reg["dm_pulada"] = "já recebeu DM hoje"
            else:
                try:
                    reg["dm"] = ig.mandar_dm(c["usuario_id"], msg)
                except Exception as e:  # noqa: BLE001 — convite pendente etc.: ainda responde no comentário
                    reg["dm_erro"] = str(e)[:200]
                time.sleep(20)
            try:
                reg["resposta"] = ig.comentar(media_id, RESPOSTA, responder_a=c)
            except Exception as e:  # noqa: BLE001
                reg["resposta_erro"] = str(e)[:200]
            feitos[cid] = reg
            gravar_json(estado_arq, feitos)
            atendidos += 1
            erros = " ".join(reg.get(k, "") for k in ("dm_erro", "resposta_erro"))
            if erros and _bloqueado(erros):  # insistir com a conta marcada piora o bloqueio
                print(f"{conta}: Instagram bloqueou ação ({erros[:120]}); parei a rodada")
                return _fim(conta, atendidos, link)
            time.sleep(40)  # sem rajada
    _fim(conta, atendidos, link)


def _fim(conta, atendidos, link):
    print(f"{conta}: {atendidos} atendido(s); link {link}")


if __name__ == "__main__":
    main()
