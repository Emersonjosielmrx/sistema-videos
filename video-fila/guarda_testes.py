"""guarda_testes.py — teste e produção rodando JUNTOS sem a produção dar erro (dono, 22/10/2026).

Pedido do dono: "um sistema que detecte quando estamos fazendo teste (geração de áudio, vídeo de teste) pra manter os
dois rodando, ou pausar temporariamente se for dar erro, em último caso". Caso real: 22/10 05:28-05:36 o separador de
voz de um TESTE (dataset_v3) comeu a RAM e o clone da produção caiu 3x com MemoryError.

Três degraus, nesta ordem:
  1. DETECTA processo de teste pela linha de comando (scratch/tmp/amostras_voz/clone2/kaggle/separador/teste_*),
     sempre olhando os PAIS: filho da produção (ffmpeg de render, separador do intros_voz) é PRODUÇÃO, nunca teste.
  2. CONVIVE: teste vai pra prioridade baixa (com produção rodando: a mais baixa) — a produção ganha a CPU e
     ninguém para. Sem produção, o teste volta ao normal.
  3. ÚLTIMO CASO: RAM livre < RAM_CRITICA com produção rodando = o teste é SUSPENSO (congelado: não morre, não perde
     nada; o Windows tira a memória dele pro arquivo de paginação). Retoma sozinho quando a RAM volta (> RAM_OK), quando
     a produção acaba, ou no máximo em MAX_SUSPENSO_MIN (aí a produção é que espera: o clone já espera RAM até 45 min).

    python guarda_testes.py              # mostra o que é teste/produção agora (não mexe em nada)
    python guarda_testes.py --rodar 19   # guarda ativa por 19 min (o vigia geral relança a cada 20)
Estado: estado\\guarda_testes.json; log: logs\\guarda_testes.log. Nunca mexe em Chrome/Claude/OBS/sistema.
"""
import json
import re
import sys
import time
from pathlib import Path

import psutil

BASE = Path(__file__).resolve().parent
ESTADO = BASE / "estado" / "guarda_testes.json"
LOG = BASE / "logs" / "guarda_testes.log"
TRAVA = BASE / "estado" / "guarda_testes.lock"
RAM_CRITICA_GB = 2.5
RAM_OK_GB = 4.5
MAX_SUSPENSO_MIN = 40
INTERVALO_S = 20

PRODUCAO = re.compile(r"anime-pipeline|hiper-pipeline|hiper-longo|anime_auto|parceiro_diario|anime_worker_daemon|"
                      r"fila\.py|lancamento_pt|postar_|youtube_web_poster|rede\.py|manhwareact\.py|controlador\.py|"
                      r"gera_auto|cron_gerar|split-shorts|refazer_caps", re.I)
TESTE = re.compile(r"\\AppData\\Local\\Temp\\claude|\\scratchpad\\|D:\\tmp\\|amostras_voz|clone2\.py|kaggle|"
                   r"testar_vozes|tts-teste|\\teste[_s\\]|teste_[\w-]+\.py|amostra[s_]|audio-separator|reacoes_reais|"
                   r"colher_reacoes|dataset_v\d|_teste_religar|separador", re.I)
NOMES_ALVO = {"python.exe", "pythonw.exe", "ffmpeg.exe", "ffprobe.exe", "audio-separator.exe"}
# infraestrutura do próprio sistema: NUNCA é teste nem produção (nunca congela, nunca muda prioridade)
INFRA = re.compile(r"faxina\.py|guarda_testes\.py|vigia_geral\.py|maquinas\.py|status_videos\.py|avisos\.py|"
                   r"controle\.py|painel_controlador\.py|backup_drive\.py|notificar_telegram\.py", re.I)


def log(msg):
    linha = f"[{time.strftime('%d/%m %H:%M:%S')}] {msg}"
    print(linha, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def _cmd(p):
    try:
        return " ".join(p.cmdline())
    except (psutil.Error, OSError):
        return ""


def classificar():
    """(testes, producao): listas de psutil.Process. Produção = ele OU um pai bate PRODUCAO."""
    testes, producao = [], []
    for p in psutil.process_iter(["name"]):
        try:
            if (p.info["name"] or "").lower() not in NOMES_ALVO:
                continue
            proprio = _cmd(p)
            if INFRA.search(proprio):
                continue
            pais = p.parents()
            # produção: ele ou QUALQUER pai (inclui o .bat/.vbs da tarefa agendada que lançou)
            if PRODUCAO.search(proprio) or any(PRODUCAO.search(_cmd(x)) or "cron_" in _cmd(x).lower() for x in pais):
                producao.append(p)
                continue
            # teste: ele ou um pai PYTHON/ffmpeg — o terminal/sessão que abriu (caminho do Claude) não conta
            if TESTE.search(proprio) or any(TESTE.search(_cmd(x)) for x in pais
                                            if (x.name() or "").lower() in NOMES_ALVO and not INFRA.search(_cmd(x))):
                testes.append(p)
        except (psutil.Error, OSError):
            continue
    return testes, producao


def _ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"suspensos": {}}


def _gravar(est):
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = ESTADO.with_name(ESTADO.name + ".tmp")
    tmp.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ESTADO)


def _retomar_todos(est, motivo):
    for pid in list(est.get("suspensos", {})):
        try:
            psutil.Process(int(pid)).resume()
        except (psutil.Error, OSError, ValueError):
            pass
        est["suspensos"].pop(pid, None)
    log(f"testes RETOMADOS ({motivo})")


def ciclo(est):
    testes, producao = classificar()
    livre = psutil.virtual_memory().available / 1024 ** 3
    # degrau 2: prioridade — com produção, teste na mais baixa; sem, volta ao normal
    for p in testes:
        try:
            alvo = psutil.IDLE_PRIORITY_CLASS if producao else psutil.BELOW_NORMAL_PRIORITY_CLASS
            if p.nice() != alvo:
                p.nice(alvo)
        except (psutil.Error, OSError):
            pass
    susp = est.setdefault("suspensos", {})
    if susp:
        desde = min(v.get("desde", time.time()) for v in susp.values())
        if not producao:
            _retomar_todos(est, "a produção acabou")
        elif livre > RAM_OK_GB:
            _retomar_todos(est, f"RAM voltou ({livre:.1f} GB livres)")
        elif time.time() - desde > MAX_SUSPENSO_MIN * 60:
            _retomar_todos(est, f"limite de {MAX_SUSPENSO_MIN} min suspenso — agora a produção é que espera RAM")
            est["descanso_ate"] = time.time() + 15 * 60  # não re-suspende logo em seguida
    elif producao and testes and livre < RAM_CRITICA_GB and time.time() > est.get("descanso_ate", 0):
        # degrau 3: último caso
        for p in testes:
            try:
                p.suspend()
                susp[str(p.pid)] = {"desde": time.time(), "cmd": _cmd(p)[:160]}
            except (psutil.Error, OSError):
                pass
        if susp:
            log(f"RAM crítica ({livre:.1f} GB) com produção rodando: {len(susp)} processo(s) de TESTE suspensos "
                f"(congelados, nada se perde): " + "; ".join(v["cmd"][:70] for v in susp.values()))
            try:
                if r"D:\video-fila" not in sys.path:
                    sys.path.insert(0, r"D:\video-fila")
                import avisos
                avisos.enviar(f"Teste pausado pra proteger a produção: RAM {livre:.1f} GB. Retoma sozinho quando a "
                              f"RAM voltar (máx {MAX_SUSPENSO_MIN} min).", "guarda de testes", importante=False)
            except Exception:  # noqa: BLE001
                pass
    _gravar(est)
    return len(testes), len(producao), livre


def rodar(minutos):
    if TRAVA.exists() and time.time() - TRAVA.stat().st_mtime < 25 * 60:
        return  # já há uma guarda viva
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    TRAVA.write_text(str(time.time()), encoding="utf-8")
    est = _ler()
    fim = time.time() + minutos * 60
    try:
        while time.time() < fim:
            TRAVA.write_text(str(time.time()), encoding="utf-8")
            try:
                ciclo(est)
            except Exception as e:  # noqa: BLE001
                log(f"ciclo falhou ({type(e).__name__}: {e})")
            time.sleep(INTERVALO_S)
    finally:
        if est.get("suspensos"):
            _retomar_todos(est, "a guarda vai sair — nada fica congelado sem vigia")
            _gravar(est)
        TRAVA.unlink(missing_ok=True)


def main():
    if "--rodar" in sys.argv:
        i = sys.argv.index("--rodar")
        rodar(float(sys.argv[i + 1]) if len(sys.argv) > i + 1 else 19)
        return
    testes, producao = classificar()
    livre = psutil.virtual_memory().available / 1024 ** 3
    print(f"RAM livre: {livre:.1f} GB | produção: {len(producao)} | teste: {len(testes)}")
    for nome, lst in (("PRODUÇÃO", producao), ("TESTE", testes)):
        for p in lst[:12]:
            print(f"  {nome:8} pid {p.pid:6} {_cmd(p)[:110]}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
