"""
====================================================================
 auto_producer.py — Produtor autonomo de videos de historias
====================================================================

O QUE FAZ (em 1 frase):
    Fica num loop gerando videos sozinho, escolhendo generos/temas ao acaso
    sem repetir, esperando a quota do Gemini quando ela acaba, e anotando tudo
    num log — sem depender do chat nem de ninguem olhando.

--------------------------------------------------------------------
 PRA QUEM VAI EDITAR (humano OU modelo de IA), LEIA ISTO:
--------------------------------------------------------------------
 Quase nada do que voce quer mudar esta NESTE arquivo. Veja onde mexer:

   * Trocar/adicionar GENEROS e TEMAS ....... config/temas.json
   * Mudar cenas, qualidade, timeout, backoff  config/settings.json
   * Ligar a producao ....................... rode LIGAR_PRODUCAO.bat
   * Desligar a producao .................... rode DESLIGAR_PRODUCAO.bat
   * Ver o que aconteceu .................... logs/auto-producer.md

 Este .py so ORQUESTRA: le os JSONs, escolhe o proximo video, chama o
 pipeline (bin/story_pipeline.py) e trata falha/quota. O codigo esta
 dividido em SECOES numeradas e comentadas abaixo. Se for editar a logica,
 edite a secao certa e rode `--dry-run` pra testar sem gastar quota.

 SEGURANCA: sempre existe um backup em _BACKUP_auto_producer_* na raiz.
 Se quebrar, e so restaurar de la.
--------------------------------------------------------------------

USO NA LINHA DE COMANDO:
    python auto_producer.py                 # loop infinito
    python auto_producer.py --max 10        # para apos 10 videos
    python auto_producer.py --generos terror,suspense
    python auto_producer.py --dry-run       # so mostra o plano, nao gera nada
"""

import os
import sys
import json
import time
import random
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


# ====================================================================
# SECAO 1 — CAMINHOS (paths).
# PROJECT_DIR e a pasta deste arquivo, resolvida sozinha. Assim a MESMA
# copia funciona em qualquer pista (prod/beta/teste) sem editar nada.
# ====================================================================
PROJECT_DIR = Path(__file__).resolve().parent          # raiz da pista atual
PIPELINE    = PROJECT_DIR / "bin" / "story_pipeline.py"  # o gerador de video real
WORKSPACE   = PROJECT_DIR / "workspace"
CONFIG_DIR  = PROJECT_DIR / "config"                   # onde ficam os JSONs editaveis

# Arquivos de configuracao editaveis (SEM mexer neste .py):
SETTINGS_FILE = CONFIG_DIR / "settings.json"           # parametros (cenas, quality...)
TEMAS_FILE    = CONFIG_DIR / "temas.json"              # generos + temas

# Arquivos de estado/controle (o script gerencia sozinho, nao edite a mao):
STATE_FILE    = WORKSPACE / ".auto_producer_state.json"  # progresso persistido
COOLDOWN_FILE = WORKSPACE / ".quota_cooldown.txt"        # criado pelo image_generator
MAX_RETOMADAS = 4             # vezes que a mesma historia e retomada apos cota/imagens
ESPERA_INCOMPLETO_SEG = 600   # imagens incompletas sem hora de volta: tenta de novo em 10min
LOCK_FILE     = WORKSPACE / ".auto_producer.lock"        # evita 2 daemons juntos
LOG_FILE      = PROJECT_DIR / "logs" / "auto-producer.md"


# ====================================================================
# SECAO 2 — DEFAULTS. So sao usados se os JSONs sumirem/estiverem quebrados.
#           O certo e editar os JSONs em config/, nao estes valores.
# ====================================================================
DEFAULT_SETTINGS = {
    "pista": "prod",              # nome da pista (prod/beta/teste) — separa a saida
    "cenas": 8,
    "quality": "high",
    "timeout_por_video_seg": 1800,
    "backoff_base_seg": 30,
    "backoff_max_seg": 600,
    "falhas_ate_pausa_longa": 5,
    "pausa_longa_seg": 1800,
    "generos_ativos": None,
    "videos_paralelo": 1,        # quantos videos gerar ao mesmo tempo (guardiao/config)
    "popup_ao_terminar": True,   # avisa no canto da tela quando cada video fica pronto
    "materiais_dir": r"D:\hipercool-materiais\historias-em-frames",  # saida compartilhada
}

# Fallback minimo de temas caso o temas.json nao carregue (o loop nao trava).
DEFAULT_TEMAS = {
    "terror": ["voz que sussurrava do ralo do banheiro"],
    "comedia": ["o gato que aprendeu a falar mas so pedia pizza"],
    "drama": ["pai descobre que a filha que criou por 20 anos nao era dele"],
}


# ====================================================================
# SECAO 3 — LOG. Grava em logs/auto-producer.md e imprime no console.
# ====================================================================
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"- [{ts}] {msg}\n")
    except Exception:
        pass


def notificar_video_pronto(settings, genero, tema, elapsed, n_na_run):
    """Popup no canto da tela quando um video fica pronto (best-effort).
    Identifica a PISTA no titulo pra voce saber qual delas produziu."""
    if not settings.get("popup_ao_terminar", True):
        return
    try:
        sys.path.insert(0, str(PROJECT_DIR / "bin"))
        from notifica import avisar_desktop
        pista = settings.get("pista", "prod").upper()
        titulo = f"[{pista}] Video pronto (#{n_na_run})"
        msg = f"{genero} — '{tema[:50]}' ({elapsed:.0f}s)"
        avisar_desktop(titulo, msg)
    except Exception:
        pass  # nunca deixa a notificacao derrubar o loop


# ====================================================================
# SECAO 4 — CARREGAR CONFIG. Le os JSONs a cada video, entao editar o
#           JSON tem efeito imediato (nao precisa reiniciar o daemon).
# ====================================================================
def load_settings():
    """Le config/settings.json; se faltar/quebrar, usa DEFAULT_SETTINGS."""
    cfg = dict(DEFAULT_SETTINGS)
    try:
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            # so aceita chaves conhecidas (ignora os campos "_help_*" e "_LEIA")
            for k in DEFAULT_SETTINGS:
                if k in data:
                    cfg[k] = data[k]
    except Exception as e:
        log(f"WARN: settings.json invalido ({e}) — usando defaults")
    return cfg


def load_temas():
    """Le config/temas.json e retorna {genero: [temas]}."""
    try:
        if TEMAS_FILE.exists():
            data = json.loads(TEMAS_FILE.read_text(encoding="utf-8"))
            generos = data.get("generos", {})
            # so mantem generos com pelo menos 1 tema valido
            limpo = {g: [t for t in temas if isinstance(t, str) and t.strip()]
                     for g, temas in generos.items() if temas}
            if limpo:
                return limpo
    except Exception as e:
        log(f"WARN: temas.json invalido ({e}) — usando defaults")
    return dict(DEFAULT_TEMAS)


# ====================================================================
# SECAO 5 — ESTADO. Guarda progresso (quantos videos, temas usados...)
#           pra retomar de onde parou apos restart. Escrita atomica.
# ====================================================================
def _novo_estado():
    return {
        "version": 1,
        "started_at": datetime.now().isoformat(),
        "last_updated": None,
        "total_produced": 0,
        "total_failed": 0,
        "used_temas": [],
        "consecutive_failures": 0,
        "last_video_path": None,
        "last_genero": None,
    }


def load_state():
    if not STATE_FILE.exists():
        return _novo_estado()
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        log("WARN: state file corrupto, recriando")
        return _novo_estado()


def save_state(state):
    state["last_updated"] = datetime.now().isoformat()
    tmp = STATE_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(STATE_FILE)  # replace e atomico: sobrevive a kill no meio
    except Exception as e:
        log(f"WARN: nao conseguiu salvar state: {e}")


# ====================================================================
# SECAO 6 — QUOTA. O bin/image_generator.py grava .quota_cooldown.txt
#           (um timestamp unix) quando a quota do Gemini esgota. Aqui a
#           gente respeita esse cooldown antes de tentar o proximo video.
# ====================================================================
def quota_cooldown_active():
    """Retorna segundos restantes do cooldown, ou 0 se inativo."""
    if not COOLDOWN_FILE.exists():
        return 0
    try:
        v = float(COOLDOWN_FILE.read_text(encoding="utf-8").strip())
        # o arquivo guarda a HORA DE VOLTA da cota. Valor no passado = formato antigo
        # (hora em que acabou) -> +1h. Antes isto lia o formato antigo como hora de volta
        # e o cooldown dava sempre 0: o produtor nunca esperava a cota.
        expires_at = v if v > time.time() else v + 3600
        return max(0, int(expires_at - time.time()))
    except Exception:
        return 0


def wait_for_quota_cooldown():
    remaining = quota_cooldown_active()
    if remaining <= 0:
        return
    log(f"QUOTA cooldown ativo — aguardando {remaining // 60}min {remaining % 60}s")
    sleep_until = time.time() + remaining + 5
    while time.time() < sleep_until:
        time.sleep(min(30, sleep_until - time.time()))
    log("RESUMED apos cooldown")


# ====================================================================
# SECAO 7 — ESCOLHA DO PROXIMO VIDEO (genero + tema, sem repetir).
# ====================================================================
def pick_tema(genero, temas_por_genero, used_set, cycle=0):
    """Escolhe um tema ainda nao usado. Se acabaram, gera uma variacao numerada
    pra nunca travar o loop."""
    pool = temas_por_genero.get(genero, [])
    disponiveis = [t for t in pool if t not in used_set]
    if disponiveis:
        return random.choice(disponiveis)
    seed = random.choice(pool) if pool else f"tema {genero}"
    return f"{seed} (variacao #{cycle + 1})"


# ====================================================================
# SECAO 8 — RODAR O PIPELINE. Chama bin/story_pipeline.py num subprocesso.
#           Aqui NAO se gera video; so se dispara o gerador de verdade.
# ====================================================================
def videos_out_dir(settings):
    """Pasta de saida desta pista, DENTRO de hipercool-materiais (compartilhado).
    Ex.: D:\\hipercool-materiais\\historias-em-frames\\videos\\prod
    Se materiais_dir nao existir/nao setado, cai no workspace local (nunca trava)."""
    mat = settings.get("materiais_dir")
    pista = settings.get("pista", "prod")
    if mat:
        base = Path(mat) / "videos" / pista
        try:
            base.mkdir(parents=True, exist_ok=True)
            return base
        except Exception:
            pass
    return WORKSPACE / "videos"


def run_pipeline(genero, tema, settings):
    """Retorna (ok, output, tem_marca_de_quota, returncode)."""
    cmd = [
        sys.executable,
        str(PIPELINE),
        "--genero", genero,
        "--tema", tema,
        "--cenas", str(settings["cenas"]),
        "--quality", str(settings["quality"]),
        "--skip-notify",
    ]
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"       # console Windows quebra sem isso
    env["FORCE_DIRECT_TTS"] = "1" # usa edge-tts direto
    # roteia a saida do pipeline pra pasta desta pista em hipercool-materiais
    env["HEF_VIDEOS_DIR"] = str(videos_out_dir(settings))

    log(f"SPAWN: {genero} / '{tema[:60]}' -> {env['HEF_VIDEOS_DIR']}")
    try:
        proc = subprocess.run(
            cmd, cwd=str(PROJECT_DIR), env=env,
            capture_output=True, text=True,
            timeout=settings["timeout_por_video_seg"],
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        ok = proc.returncode == 0 and "OK:" in output
        quota_marker = "QUOTA_COOLDOWN" in output or "API_QUOTA_EXHAUSTED" in output
        return ok, output, quota_marker, proc.returncode
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT", False, -1
    except Exception as e:
        return False, f"EXCEPTION: {e}", False, -1


def rodar_metricas():
    """1x por dia (a trava de 20 h fica no proprio script): le no Studio o que as historias postadas renderam e
    alimenta o rodizio de capas (bin/metricas_historias.py). Falhar aqui nunca para a producao."""
    py = Path(sys.executable).with_name("python.exe")  # o daemon roda em pythonw
    try:
        proc = subprocess.run(
            [str(py if py.exists() else sys.executable), str(PROJECT_DIR / "bin" / "metricas_historias.py")],
            cwd=str(PROJECT_DIR), env={**os.environ, "PYTHONUTF8": "1"}, capture_output=True, text=True,
            timeout=3600, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        linhas = ((proc.stdout or "") + (proc.stderr or "")).strip().splitlines()
        if linhas:
            log(f"METRICAS: {linhas[-1][:200]}")
    except Exception as e:
        log(f"METRICAS falhou: {e}")


def find_latest_video(genero, settings):
    """Acha o mp4 final mais recente do genero, pra registrar no state/log.
    Procura na pasta de saida da pista (materiais); se nao achar, tenta o local."""
    for base in (videos_out_dir(settings) / genero, WORKSPACE / "videos" / genero):
        if base.exists():
            cands = sorted(base.glob("*/v*_FINAL.mp4"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
            if cands:
                return str(cands[0])
    return None


# ====================================================================
# SECAO 9 — LOCK. Garante que so 1 daemon roda por vez (2 competiriam
#           pela mesma quota e derrubariam os dois).
# ====================================================================
def _pid_alive(pid):
    try:
        out = subprocess.run(["tasklist", "/fi", f"PID eq {pid}", "/nh"],
                             capture_output=True, text=True, timeout=15)
        return str(pid) in (out.stdout or "")
    except Exception:
        return False


def acquire_lock():
    """True = consegui o lock. False = ja tem outro daemon vivo."""
    if LOCK_FILE.exists():
        try:
            old_pid = int(LOCK_FILE.read_text(encoding="utf-8").strip())
            if _pid_alive(old_pid):
                log(f"JA EXISTE daemon rodando (PID {old_pid}) — abortando esta instancia")
                return False
            log(f"lock orfao de PID {old_pid} (morto) — assumindo")
        except Exception:
            pass
    try:
        LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
        return True
    except Exception as e:
        log(f"WARN: nao conseguiu criar lock: {e}")
        return True


def release_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass


# ====================================================================
# SECAO 10 — LOOP PRINCIPAL. Junta tudo: escolhe -> gera -> trata falha.
# ====================================================================
def main():
    parser = argparse.ArgumentParser(description="Auto Producer — loop autonomo")
    parser.add_argument("--max", type=int, default=None, help="Para apos N videos")
    parser.add_argument("--generos", default=None, help="Subset de generos (csv)")
    parser.add_argument("--dry-run", action="store_true", help="So imprime o plano")
    args = parser.parse_args()

    settings = load_settings()
    temas_por_genero = load_temas()

    # Ordem de prioridade dos generos: --generos (CLI) > settings.json > todos
    if args.generos:
        generos = [g.strip() for g in args.generos.split(",") if g.strip()]
    elif settings.get("generos_ativos"):
        generos = list(settings["generos_ativos"])
    else:
        generos = list(temas_por_genero.keys())
    # so mantem generos que existem no temas.json
    generos = [g for g in generos if g in temas_por_genero] or list(temas_por_genero.keys())

    if not args.dry_run and not acquire_lock():
        return

    state = load_state()
    used = set(state.get("used_temas", []))
    consecutive_failures = state.get("consecutive_failures", 0)
    cycle = len(used)

    log(f"STARTED (max={args.max or 'inf'}, generos={generos})")
    log(f"STATE: produced={state['total_produced']}, failed={state['total_failed']}, "
        f"used_temas={len(used)}")

    # --- modo dry-run: so mostra o que faria, nao gera nada ---
    if args.dry_run:
        log("DRY RUN — proximos 5 jobs:")
        for i in range(5):
            g = random.choice(generos)
            t = pick_tema(g, temas_por_genero, used, cycle + i)
            log(f"  {i+1}. {g} / '{t[:60]}'")
        return

    produced_this_run = 0
    pendente = None   # (genero, tema, tentativa) interrompida por cota -> retomar
    try:
        while True:
            if args.max and produced_this_run >= args.max:
                log(f"MAX atingido ({args.max}), saindo")
                break

            # recarrega config a cada volta (edicoes no JSON valem na hora)
            settings = load_settings()
            temas_por_genero = load_temas()

            wait_for_quota_cooldown()
            rodar_metricas()

            if pendente:
                # retoma a MESMA historia: roteiro e imagens que ja sairam vem do cache
                genero, tema, tentativa = pendente
                log(f"RETOMANDO {genero} / '{tema[:50]}' (tentativa {tentativa + 1})")
            else:
                genero = random.choice(generos)
                tema = pick_tema(genero, temas_por_genero, used, cycle)
                cycle += 1
                tentativa = 0

            t0 = time.time()
            ok, output, quota_marker, rc = run_pipeline(genero, tema, settings)
            elapsed = time.time() - t0
            incompleto = "IMAGENS_INCOMPLETAS" in output

            # --- caso 1: cota de imagem / imagens incompletas -> NAO faz o video, espera e
            #     retoma a mesma historia (nao conta como falha). Antes sorteava outra
            #     historia e jogava fora roteiro + imagens ja gerados. ---
            if quota_marker or incompleto:
                consecutive_failures = 0
                state["esperas_cota"] = state.get("esperas_cota", 0) + 1
                save_state(state)
                if tentativa + 1 >= MAX_RETOMADAS:
                    log(f"DESISTIU de {genero} / '{tema[:50]}' apos {MAX_RETOMADAS} retomadas")
                    pendente = None
                else:
                    pendente = (genero, tema, tentativa + 1)
                if quota_marker:
                    log(f"COTA de imagem esgotada ({elapsed:.0f}s) — video NAO feito; "
                        f"esperando a cota voltar pra retomar")
                    wait_for_quota_cooldown()
                else:
                    log(f"IMAGENS INCOMPLETAS ({elapsed:.0f}s) — video NAO feito; "
                        f"tentando de novo em {ESPERA_INCOMPLETO_SEG // 60}min")
                    time.sleep(ESPERA_INCOMPLETO_SEG)
                continue
            pendente = None

            # --- caso 2: sucesso ---
            if ok:
                produced_this_run += 1
                state["total_produced"] += 1
                state["consecutive_failures"] = 0
                state["used_temas"].append(tema)
                state["last_genero"] = genero
                vpath = find_latest_video(genero, settings)
                state["last_video_path"] = vpath
                used.add(tema)
                save_state(state)
                log(f"OK {genero} / '{tema[:50]}' ({elapsed:.0f}s) -> {vpath}")
                notificar_video_pronto(settings, genero, tema, elapsed, produced_this_run)
                continue

            # --- caso 3: falha comum -> backoff exponencial ---
            state["total_failed"] += 1
            state["consecutive_failures"] = consecutive_failures + 1
            save_state(state)
            consecutive_failures = state["consecutive_failures"]

            if consecutive_failures >= settings["falhas_ate_pausa_longa"]:
                pausa = settings["pausa_longa_seg"]
                log(f"FALHOU {genero} / '{tema[:50]}' (rc={rc}) — "
                    f"{consecutive_failures} falhas seguidas, PAUSA LONGA {pausa // 60}min")
                time.sleep(pausa)
                consecutive_failures = 0
                state["consecutive_failures"] = 0
                save_state(state)
            else:
                backoff = min(
                    settings["backoff_base_seg"] * (2 ** min(consecutive_failures - 1, 5)),
                    settings["backoff_max_seg"],
                )
                tail = output.strip().splitlines()[-3:] if output else ["<sem output>"]
                log(f"FALHOU {genero} / '{tema[:50]}' (rc={rc}, {elapsed:.0f}s) — "
                    f"backoff {backoff}s. Tail: {tail}")
                time.sleep(backoff)

    except KeyboardInterrupt:
        log("INTERRUPTED pelo usuario — salvando state e saindo")
        save_state(state)
    finally:
        release_lock()

    log(f"FINISHED: +{produced_this_run} nesta run, "
        f"total={state['total_produced']} OK, {state['total_failed']} falhas")


if __name__ == "__main__":
    main()
