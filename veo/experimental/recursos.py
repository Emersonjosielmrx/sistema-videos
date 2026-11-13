# -*- coding: utf-8 -*-
"""
========================================================================
recursos.py  —  Mede RAM/CPU/disco e decide quantos Chromes abrir
========================================================================

O bot Veo/Flow trava quando a maquina fica sem RAM (o Chrome crasha a aba do
Flow). Este modulo e o "sensor" que permite o bot ser inteligente com os
recursos: mede a maquina AGORA e diz quantos workers (Chromes) e seguro abrir,
qual o nivel de carga, e quanto esticar os timeouts.

Usado pelo orquestrador (cron_gerar_video_llm.py) e pelo monitor noturno
(monitor_recursos.py). NAO abre navegador, NAO gasta credito — so le sensores.

Ajuste fino: as constantes vem de config.py quando existem (com fallback aqui).
"""
import psutil

try:
    import config as _cfg
except Exception:
    _cfg = None


def _c(nome, default):
    """Le a constante de config.py se existir; senao usa o default local."""
    return getattr(_cfg, nome, default) if _cfg else default


# ---- limiares (podem ser sobrescritos em config.py) ----
RAM_POR_CHROME_MB = lambda: _c("RAM_POR_CHROME_MB", 1500)  # RAM estimada por Chrome+worker
RAM_RESERVA_MB    = lambda: _c("RAM_RESERVA_MB", 2000)     # folga que nunca ocupamos
TETO_WORKERS      = lambda: _c("TETO_WORKERS", 4)          # maximo absoluto (subir p/ 10 c/ 50 contas)
CPU_ALTA_PCT      = lambda: _c("CPU_ALTA_PCT", 85)         # acima disso, corta 1 worker
DISCO_MIN_GB      = lambda: _c("DISCO_MIN_GB", 5)          # abaixo disso, nao gera video


def ram_livre_mb():
    return psutil.virtual_memory().available / (1024 * 1024)


def ram_livre_pct():
    return 100.0 - psutil.virtual_memory().percent


def cpu_pct(intervalo=0.5):
    """% de CPU. intervalo pequeno pra nao travar o loop."""
    return psutil.cpu_percent(interval=intervalo)


def disco_livre_gb(path="D:/"):
    try:
        return psutil.disk_usage(path).free / (1024 ** 3)
    except Exception:
        return 999.0


def slots_por_recurso():
    """Quantos Chromes/workers a maquina aguenta AGORA (>=0).

    Base: quanta RAM sobra depois de reservar uma folga, dividida pela RAM
    que cada Chrome consome. Corta 1 se a CPU ja esta alta. Nunca passa do teto.
    Retorna 0 quando nem 1 worker cabe (a maquina esta afogada).
    """
    livre = ram_livre_mb() - RAM_RESERVA_MB()
    if livre <= 0:
        return 0
    slots = int(livre // RAM_POR_CHROME_MB())
    if cpu_pct() >= CPU_ALTA_PCT():
        slots -= 1
    return max(0, min(slots, TETO_WORKERS()))


def nivel_carga():
    """Classifica a carga atual: folgado | medio | apertado | critico.

    Combina RAM livre e CPU. 'critico' = nao vale nem tentar abrir Chrome.
    """
    ram = ram_livre_pct()
    cpu = cpu_pct()
    if ram < 12 or cpu >= 95:
        return "critico"
    if ram < 22 or cpu >= 85:
        return "apertado"
    if ram < 40 or cpu >= 65:
        return "medio"
    return "folgado"


def timeout_dinamico(base_s):
    """Estica o timeout conforme a carga (maquina apertada rende mais devagar).

    folgado=base, medio=base*1.25, apertado=base*1.5, critico=base*2.
    """
    fator = {"folgado": 1.0, "medio": 1.25, "apertado": 1.5, "critico": 2.0}
    return int(base_s * fator.get(nivel_carga(), 1.0))


def disco_ok():
    """True se ha disco suficiente pra salvar video."""
    return disco_livre_gb() >= DISCO_MIN_GB()


def resumo():
    """String de 1 linha pro log/diagnostico."""
    return (f"RAM {ram_livre_mb():.0f}MB livre ({ram_livre_pct():.0f}%) | "
            f"CPU {cpu_pct():.0f}% | disco {disco_livre_gb():.0f}GB | "
            f"nivel={nivel_carga()} | slots={slots_por_recurso()}")


if __name__ == "__main__":
    print(resumo())
