# -*- coding: utf-8 -*-
"""
========================================================================
validate.py  —  Smoke test (checagem rapida) do bot Veo/Flow
========================================================================

NAO gera video, NAO abre Chrome, NAO gasta credito/token. So confere que:
  1. Todos os modulos VIVOS importam sem erro (pega import quebrado/circular).
  2. A lista de contas e consistente (contas.py) e bate com o que o
     orquestrador e o worker enxergam (cron_gerar_video_llm / gera_auto).

Rode SEMPRE depois de mexer em contas.py ou nos imports:
    python validate.py

Saida: imprime a tabela de contas e um veredito no final.
Exit code 0 = tudo OK; 1 = achou problema.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Modulos vivos que devem SEMPRE importar limpo.
MODULOS_VIVOS = [
    "config", "contas", "creditos",
    "flow_bot", "gera_auto", "cron_gerar_video_llm",
    "agents", "llm_client", "metrics_client", "thumbnail_client",
    "vencedoras", "loop_cron",
    # 16/10 (BX-04): o que entrou na Onda 1/2 e roda em producao
    "validar_video", "conferir_fala", "dedupe_video", "trava_render", "sem_janela",
    "sonda_contas_veo", "seo_palavras_veo", "separar_fotos_marcadas",
]

problemas = []


def _check_imports():
    print("[1/3] Importando modulos vivos...")
    for m in MODULOS_VIVOS:
        try:
            __import__(m)
            print(f"      OK  {m}")
        except Exception as e:
            print(f"      ERRO {m}: {type(e).__name__}: {e}")
            problemas.append(f"import {m}: {e}")


def _check_contas():
    print("\n[2/3] Conferindo consistencia das contas...")
    import contas
    ok, probs = contas._consistente()
    if not ok:
        for p in probs:
            problemas.append(f"contas.py: {p}")

    sess_contas = sorted(c["session"] for c in contas.CONTAS)

    # o orquestrador tem que ver a MESMA lista (importa de contas.py)
    try:
        import cron_gerar_video_llm as cron
        sess_cron = sorted(s["session"] for s in cron.SESSOES)
        if sess_cron != sess_contas:
            problemas.append(f"cron.SESSOES {sess_cron} != contas {sess_contas}")
    except Exception as e:
        problemas.append(f"nao consegui checar cron.SESSOES: {e}")

    # o worker tem que ter profile pra cada conta (PROFILE_MAP vem de contas.py)
    try:
        import gera_auto
        faltando = [s for s in sess_contas if s not in gera_auto.PROFILE_MAP]
        if faltando:
            problemas.append(f"gera_auto.PROFILE_MAP sem profile p/: {faltando}")
    except Exception as e:
        problemas.append(f"nao consegui checar gera_auto.PROFILE_MAP: {e}")

    print(f"      {len(contas.CONTAS)} conta(s):")
    print(f"      {'SESSION':<16} {'PORT':<6} PROFILE")
    for c in contas.CONTAS:
        print(f"      {c['session']:<16} {c['port']:<6} {c['profile']}")


def _check_funcoes():
    """Comportamento que ja quebrou ou que protege a producao (16/10, BX-04). Sem Chrome, sem credito, sem rede."""
    print("\n[3/3] Conferindo comportamentos...")
    casos = []
    try:
        from agents import prompt_com_fala
        pr = prompt_com_fala("A man looks at the camera.", 'Diz "oi"')
        casos.append(("prompt pede sem texto na tela e 9:16", "on-screen text" in pr and "9:16" in pr and '"' in pr))
    except Exception as e:
        casos.append((f"prompt_com_fala: {e}", False))
    try:
        import cron_gerar_video_llm as C
        marc = C._fotos_com_marca()
        escolhas = [C.escolher_foto({"nome": n}) for n in ("Stand-up IA", "E Se...", "Motivacao IA", "Segredos do Oceano")]
        casos.append(("escolher_foto nunca devolve foto com marca de IA",
                      all(f is None or os.path.normcase(f) not in marc for f in escolhas)))
        casos.append(("sistema_pausado() responde sem erro", C.sistema_pausado() in (True, False)))
    except Exception as e:
        casos.append((f"escolha de foto/pausa: {e}", False))
    try:
        from trava_render import trava_render, TRAVA
        with trava_render("validate"):
            dentro = TRAVA.exists()
        casos.append(("trava_render cria e apaga a trava", dentro and not TRAVA.exists()))
    except Exception as e:
        casos.append((f"trava_render: {e}", False))
    try:
        import dedupe_video
        casos.append(("dedupe_video.parecido(x, x) == 1", dedupe_video.parecido([1, 2, 3], [1, 2, 3]) == 1.0))
    except Exception as e:
        casos.append((f"dedupe_video: {e}", False))
    for nome, ok in casos:
        print(f"      {'OK  ' if ok else 'ERRO'} {nome}")
        if not ok:
            problemas.append(f"comportamento: {nome}")


if __name__ == "__main__":
    _check_imports()
    _check_contas()
    _check_funcoes()
    print("\n" + "=" * 50)
    if problemas:
        print("FALHOU. Problemas encontrados:")
        for p in problemas:
            print(f"  - {p}")
        sys.exit(1)
    print("TUDO OK. Imports limpos e contas consistentes.")
    sys.exit(0)
