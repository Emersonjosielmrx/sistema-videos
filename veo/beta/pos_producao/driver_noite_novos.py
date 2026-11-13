# -*- coding: utf-8 -*-
"""driver_noite_novos.py — PRODUCAO NOTURNA AUTONOMA.

A noite toda, SEM PERGUNTAR:
  1. Gera um video NOVO no Flow usando as CONTAS NOVAS (rotacao) + foto da Haylla.
  2. Assim que baixa o cru, monta na receita COMPLETA (pos_v2): efeitos +
     clipe-propaganda vo3 (pool) + card Gemini alta-res + voz do banco.
  3. Salva em veo/pos_v2 com sidecar rastreavel — mesmo formato do lote v2.
  4. Repete ate a hora limite (default 08:00) ou ate esgotar tentativas.

Contas: usa APENAS as novas (perfis chrome_gen_nova_*). Se uma falha
(sessao expirada / creditos / sem Flow liberado), marca cooldown e vai pra
proxima. Nunca trava — pula e continua.

Uso:
    python driver_noite_novos.py                 (roda ate 08:00)
    python driver_noite_novos.py --ate 07:30
    python driver_noite_novos.py --max 50        (no maximo 50 videos)
"""
import argparse
import datetime as dt
import os
import random
import subprocess
import sys
import time
from pathlib import Path

_BASE = Path(__file__).resolve().parent            # D:\veo\beta\pos_producao
_RAIZ = _BASE.parent                                # D:\veo\beta

# IMPORTANTE: existem DOIS config.py (beta e pos_producao). flow_bot precisa
# do config do BETA (tem SESSIONS_DIR). Carregamos ele explicitamente e o
# fixamos em sys.modules ANTES de importar flow_bot, senao o config de
# pos_producao (sem SESSIONS_DIR) vence quando rodamos de dentro da pasta.
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("config", str(_RAIZ / "config.py"))
_cfg = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_cfg)
sys.modules["config"] = _cfg

sys.path.insert(0, str(_RAIZ))
sys.path.insert(0, str(_BASE))

import centralizar_publicar as cp
from centralizar_publicar import log
from worker_noite import _escolher_metadados, _gravar_sidecar
import contas as _contas
import flow_bot

# --- Contas NOVAS (a dona pediu explicitamente pra usar SO essas) -----------
# Sao as que tem perfil chrome_gen_nova_* em contas.py.
_NOVAS = [c for c in _contas.CONTAS
          if "nova_" in c.get("profile", "") or c["session"] in {
              "emerson2029", "emerson2030", "inovaremanga",
              "inovaremanhwabr", "emersoncunha"}]

# Fotos da Haylla (protagonista). VEO_FOTOS aponta pra <raiz-do-veo>\fotos.
_FOTOS_DIR = _RAIZ.parent / "fotos"

# Prompts de cena (variados) — a foto entra como protagonista falando.
_CENAS = [
    ("Curiosidades IA", "A confident Brazilian woman entrepreneur talking directly "
     "to camera about AI automation for business, modern bright office, cinematic "
     "vertical 9:16, natural warm lighting, she speaks with energy"),
    ("Motivacao IA", "A woman speaking to camera with motivational energy about "
     "success and discipline, soft cinematic background, vertical 9:16, golden hour"),
    ("Dicas de Negocio", "A woman entrepreneur explaining a business tip to camera, "
     "clean studio, vertical 9:16, professional lighting, confident tone"),
    ("Tech News", "A woman presenter announcing exciting AI tech news to camera, "
     "futuristic subtle background, vertical 9:16, dynamic lighting"),
    ("Produtividade", "A woman talking to camera about productivity and automation, "
     "cozy home office, vertical 9:16, natural light, friendly and clear"),
    ("Vendas com IA", "A woman explaining how AI closes sales on WhatsApp, talking "
     "to camera, modern office, vertical 9:16, cinematic, engaging"),
]

_COOLDOWN = {}            # session -> timestamp ate quando pular
_COOLDOWN_SEG = 3 * 3600  # 3h de castigo pra conta que falhou feio


def _foto_aleatoria():
    fotos = []
    for pat in ("*.jpg", "*.jpeg", "*.png"):
        fotos += list(_FOTOS_DIR.glob(pat))
    return str(random.choice(fotos)) if fotos else None


def _conta_disponivel():
    """Proxima conta nova fora de cooldown (round-robin embaralhado)."""
    agora = time.time()
    livres = [c for c in _NOVAS if _COOLDOWN.get(c["session"], 0) < agora]
    if not livres:
        return None
    return random.choice(livres)


def _castigar(session, seg=_COOLDOWN_SEG):
    _COOLDOWN[session] = time.time() + seg
    log(f"    [cooldown] {session} pausada por {seg//3600}h")


def _gerar_cru(conta, prompt, foto, stem):
    """Gera 1 video cru via gera_auto.py (subprocess) — ele CRIA o projeto
    'Novo projeto' se a conta nao tiver um, faz login-check e credit-check
    com exit codes. flow_bot nao cria projeto (por isso as contas novas
    travavam na pagina sem caixa de prompt). Retorna Path do cru ou None."""
    import os
    crus_dir = cp.DIR_FEITOS
    crus_dir.mkdir(parents=True, exist_ok=True)
    out = crus_dir / f"{stem}.mp4"
    env = dict(os.environ)
    env["FLOW_SESSION"] = conta["session"]
    env["FLOW_PROFILE"] = conta["profile"]
    env["FLOW_PORT"] = str(conta["port"])
    env["FLOW_ASPECT"] = "9:16"
    env["FLOW_DURATION"] = "8S"
    env["PYTHONUTF8"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    args = [sys.executable, str(_RAIZ / "gera_auto.py"), prompt, str(out)]
    if foto:
        args.append(foto)
    try:
        r = subprocess.run(args, env=env, cwd=str(_RAIZ),
                           capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        log(f"    ! timeout 900s ({conta['session']})")
        return None
    # exit codes do gera_auto: 0 ok | 2 creditos | 3 sessao | 4 direitos | 5 pausa
    rc = r.returncode
    tail = (r.stdout or "")[-200:].replace("\n", " ")
    if rc in (2, 3):
        _castigar(conta["session"])   # creditos/sessao -> cooldown longo
        log(f"    ! rc={rc} ({conta['session']}): {tail}")
        return None
    if rc != 0:
        log(f"    ! rc={rc} ({conta['session']}): {tail}")
        return None
    if out.exists() and out.stat().st_size > 50_000:
        return out
    log(f"    ! saida vazia/pequena ({conta['session']}): {tail}")
    return None


def _montar_v2(cru: Path) -> bool:
    """Monta o cru nas 3 receitas (limpo/vo3/estatica) -> pos_v2 + sidecar."""
    from montar_final import montar
    stem = cru.stem
    canal, tema, fala = _escolher_metadados(stem)

    variantes = [
        ("_LIMPO",    False, False),
        ("_VO3",      False, True),
        ("_ESTATICA", True,  False),
    ]
    ok_count = 0
    for sufixo, com_prop, com_vo3 in variantes:
        var_stem = f"{stem}{sufixo}"
        out = cp.pos_v2_out_path(var_stem)
        if out.exists() and out.stat().st_size > 50_000:
            ok_count += 1
            continue
        t0 = time.time()
        try:
            meta = montar(str(cru), str(out), canal, tema, fala,
                          voz="auto", formato_cta="slide",
                          com_propaganda=com_prop, com_vo3_propaganda=com_vo3)
            dt_ = time.time() - t0
            ok = meta.get("ok") if isinstance(meta, dict) else bool(meta)
            if ok:
                pp = meta.get("propaganda", {})
                log(f"    OK {sufixo} {stem} ({dt_:.0f}s) "
                    f"voz={pp.get('voz_usada')} var={pp.get('card_variante')}")
                try:
                    _gravar_sidecar(cru, out, meta if isinstance(meta, dict) else {}, dt_)
                except Exception as e:
                    log(f"    aviso sidecar: {str(e)[:60]}")
                ok_count += 1
            else:
                log(f"    FALHOU {sufixo} {stem}")
        except Exception as e:
            log(f"    ERRO {sufixo} {stem}: {str(e)[:100]}")
    return ok_count > 0


def rodar(ate="08:00", maximo=0):
    cp.garantir_layout()
    hoje = dt.date.today()
    hh, mm = [int(x) for x in ate.split(":")]
    limite_dt = dt.datetime.combine(hoje, dt.time(hh, mm))
    if limite_dt <= dt.datetime.now():          # se ja passou hoje, e amanha
        limite_dt += dt.timedelta(days=1)

    log("=" * 60)
    log(f"DRIVER NOITE (contas novas): ate {limite_dt:%Y-%m-%d %H:%M} "
        f"| max={maximo or 'sem limite'}")
    log(f"contas novas: {[c['session'] for c in _NOVAS]}")
    log("=" * 60)

    feitos = tentativas = 0
    while dt.datetime.now() < limite_dt:
        if maximo and feitos >= maximo:
            log(f"max {maximo} atingido.")
            break
        conta = _conta_disponivel()
        if not conta:
            log("todas as contas novas em cooldown; aguardando 15min...")
            time.sleep(900)
            continue

        tentativas += 1
        cena = random.choice(_CENAS)
        canal_slug = cena[0].lower().replace(" ", "_")
        stem = f"{canal_slug}_{dt.datetime.now():%Y%m%d_%H%M%S}"
        foto = _foto_aleatoria()
        log(f"[{feitos+1}] conta={conta['session']} cena='{cena[0]}' "
            f"foto={Path(foto).name if foto else '-'}")

        cru = _gerar_cru(conta, cena[1], foto, stem)
        if not cru:
            time.sleep(10)
            continue
        if _montar_v2(cru):
            feitos += 1
        time.sleep(5)

    log("=" * 60)
    log(f"DRIVER NOITE CONCLUIDO: novos={feitos} tentativas={tentativas}")
    log(f"saida: {cp.DIR_POS_V2}")
    log("=" * 60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ate", default="08:00", help="hora limite HH:MM")
    ap.add_argument("--max", type=int, default=0)
    a = ap.parse_args()
    rodar(ate=a.ate, maximo=a.max)
