"""vigia_desktop.py — monitoramento de erros do DESKTOP (dona 28/10: "considere que os perfis estão funcionando e
coloque um monitoramento de erros lá"). Roda a cada 30 min (tarefa VigiaDesktop, escondida).

1. ssh do PC1 -> desktop (1 conexão só). "Connection reset" com o PC2 entrando = o sshd castigou o PC1
   (PerSourcePenalties); 2 checagens seguidas com erro = avisa (aviso só com prova real).
2. Lê o que entrou nos logs desde a última vez (maquina_remota.log, produto_videos.log): Chrome/túnel que não abre,
   "não respondeu", perfil que caiu do login (Google/TikTok) no desktop.
3. Perfil deslogado ou ssh bloqueado = aviso na hora pelo portão (D:\\video-fila\\avisos.py, sem repetir em 12 h);
   o resto vai no resumo. Estado e contagem em estado\\vigia_desktop.json (painel/sessões leem).

    python vigia_desktop.py            # uma checagem
"""
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\comum")
import sem_janela  # noqa: E402,F401

BASE = Path(__file__).resolve().parent
EST = BASE / "estado" / "vigia_desktop.json"
LOGS = [Path(r"D:\postador-de-videos\logs\maquina_remota.log"), Path(r"D:\postador-de-videos\logs\produto_videos.log")]
ERRO = re.compile(r"não respondeu|FALHOU|túnel até o Chrome não abriu|Connection reset|NÃO está logado|"
                  r"NÃO logado|deslogad|login caiu|erro", re.I)
DESLOGADO = re.compile(r"(?:conferir \w+|tiktok(?: lote)?) (\S+) no desktop: (?:NÃO está logado|erro: .*login)", re.I)


def _ssh():
    try:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", "desktop", "hostname"],
                           input=b"", capture_output=True, timeout=60)  # input vazio: senão o ssh não fecha
        err = r.stderr.decode(errors="replace")
        if r.returncode == 0:
            return "ok", ""
        return ("bloqueado" if "reset" in err.lower() else "erro"), err.strip()[:160]
    except subprocess.TimeoutExpired:
        return "erro", "sem resposta em 60 s"


def _novas(est):
    pos, linhas = est.setdefault("pos", {}), []
    for arq in LOGS:
        try:
            tam = arq.stat().st_size
            ini = pos.get(str(arq), tam)  # 1ª vez: só daqui pra frente
            if ini > tam:  # log rodou
                ini = 0
            with arq.open("rb") as f:
                f.seek(ini)
                linhas += f.read().decode("utf-8", errors="replace").splitlines()
            pos[str(arq)] = tam
        except OSError:
            pass
    return [l for l in linhas if "desktop" in l.lower()]


def _avisar(texto, chave, importante=True):
    try:
        sys.path.insert(0, str(BASE))
        import avisos
        avisos.enviar(texto, "vigia desktop", importante=importante, chave=chave, html_ok=False, janela_h=12)
    except Exception as e:  # noqa: BLE001
        print("aviso não saiu:", e)


def main():
    try:
        est = json.loads(EST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = {}
    ssh, det = _ssh()
    seguidas = est.get("ssh_erros_seguidos", 0) + 1 if ssh != "ok" else 0
    # 31/10 (dona: "chega muito aviso de desconexão de PC que logo volta; só avisar se passar mais de 1 h e não
    # voltar"): conta o tempo desde a 1ª falha, não o nº de checagens
    agora = datetime.now()
    fora_desde = est.get("ssh_fora_desde") if ssh != "ok" else None
    fora_desde = fora_desde or (agora.isoformat(timespec="seconds") if ssh != "ok" else None)
    fora_min = (agora - datetime.fromisoformat(fora_desde)).total_seconds() / 60 if fora_desde else 0
    if ssh == "ok" and est.get("ssh_avisado"):
        _avisar(f"✅ Desktop voltou: o ssh do PC1 entrou de novo (estava fora desde {est.get('ssh_fora_desde', '?')[11:16]}).",
                "desktop_ssh_voltou")
    avisado = est.get("ssh_avisado") if ssh != "ok" else False
    est["ssh_fora_desde"] = fora_desde
    linhas = _novas(est)
    erros = [l for l in linhas if ERRO.search(l)]
    tipos = Counter()
    for l in erros:
        m = ERRO.search(l)
        tipos[m.group(0).lower()] += 1
    deslog = sorted({m.group(1) for l in erros for m in [DESLOGADO.search(l)] if m})
    est.update({"em": datetime.now().isoformat(timespec="seconds"), "ssh": ssh, "ssh_detalhe": det,
                "ssh_erros_seguidos": seguidas, "erros_desde_ultima": dict(tipos), "deslogados_novos": deslog,
                "exemplos": [l[:200] for l in erros[-5:]]})
    hist = est.setdefault("deslogados", {})
    for p in deslog:
        hist[p] = est["em"]
    EST.parent.mkdir(parents=True, exist_ok=True)
    EST.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")

    if ssh != "ok" and fora_min >= 60 and not avisado:
        if ssh == "bloqueado":
            _avisar(f"Desktop: o ssh está RECUSANDO o PC1 há {fora_min / 60:.1f} h (Connection reset). Veo, TikTok e "
                    "conferência não entram nele. Conserto: no desktop, PowerShell como administrador, isentar a "
                    "Tailscale no sshd_config (PerSourcePenaltyExemptList 100.64.0.0/10) e Restart-Service sshd.",
                    "desktop_ssh_bloqueado")
        else:
            _avisar(f"Desktop fora há {fora_min / 60:.1f} h sem voltar ({det}). Está ligado e na Tailscale?",
                    "desktop_ssh_fora")
        est["ssh_avisado"] = True
    elif ssh == "ok":
        est["ssh_avisado"] = False
    EST.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    if deslog:
        _avisar("Desktop: perfil(is) que caíram do login: " + ", ".join(deslog) +
                ". Precisa logar de novo nesses (Google/TikTok) no desktop.", "desktop_deslogados_" + ",".join(deslog))
    if len(erros) >= 10:
        _avisar(f"Desktop: {len(erros)} erros na última meia hora ({', '.join(f'{k} {v}' for k, v in tipos.most_common(4))}).",
                "desktop_muitos_erros", importante=False)
    print(f"ssh={ssh} ({seguidas} seguidas) | erros novos={len(erros)} {dict(tipos)} | deslogados={deslog}")


if __name__ == "__main__":
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
