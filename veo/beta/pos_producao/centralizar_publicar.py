# -*- coding: utf-8 -*-
"""centralizar_publicar.py — roteador de pastas centralizadas do projeto VEO.

PROPOSITO: o projeto veo tinha saidas espalhadas (D:\\veo\\beta\\videos\\cron_shorts,
D:\\veo\\beta\\videos_pos\\cron_shorts, D:\\hipercool-materiais\\_postados\\vo3).
Esse modulo e a FONTE UNICA da verdade do layout:

  D:\\hipercool-materiais\\veo\\
    ├─ cron_shorts/   <- espelho do que o cron_gerar_video_llm.py gera
    │                    (so espelhamos D:\\veo\\beta\\videos\\cron_shorts para o
    │                     lado do NAS, evita regerar)
    ├─ pos/           <- SAIDA DA POS-PRODUCAO (cta_builder + montagem)
    │                    e o que o postador_de_videos deve ler
    ├─ ja_feitos/     <- videos que ja viraram pos e estao prontos p/ postagem
    │                    (so moram aqui por um tempo; depois o postador move)
    ├─ ja_postados/   <- copia de backup do que o postador ja subiu
    │                    (espelho de D:\\hipercool-materiais\\_postados\\vo3)
    └─ logs/          <- logs do worker + health check de imagem

Compatibilidade: as funcoes antigas (cron_video_watcher, montar_final) continuam
funcionando; so adicionamos uma indirection por aqui pra nao duplicar paths.
"""

from pathlib import Path

# Raiz unica de tudo do veo que sai de /d/veo/beta
RAIZ_VEO = Path(r"D:\hipercool-materiais\veo")

# Pastas de origem (voo gera, cron do veo escreve)
ORIGEM_CRON_VEO = Path(r"D:\veo\beta\videos\cron_shorts")
ORIGEM_POSTADOS = Path(r"D:\hipercool-materiais\_postados\vo3")

# Pastas centrais (a saida oficial)
DIR_CRON = RAIZ_VEO / "cron_shorts"        # espelho central
# 2026-08-01: repositorio reorganizado pela dona.
#   - veo_videos_iniciais/  <- material cru que sai do Veo (era 'ja_feitos')
#   - pos_final/            <- a versão final dos shorts (foto + vo3 + card)
#   - propagandas_vo3/      <- clipes vo3 de propaganda (material reutilizavel)
# Pasta v1 antiga 'pos/' (so pos sem o clipe vo3) foi descontinuada — a "boa"
# é pos_final. O caminho v1 sumiu; quem importava DIR_POS foi atualizado.
DIR_INICIAIS = RAIZ_VEO / "veo_videos_iniciais"   # material cru Veo
DIR_POS_FINAL = RAIZ_VEO / "pos_final"            # saida FINAL (ex pos_v2)
DIR_PROP_VEO3 = RAIZ_VEO / "propagandas_vo3"      # clipes vo3 propaganda
DIR_POSTADOS = RAIZ_VEO / "ja_postados"    # backup do postador
DIR_LOGS = RAIZ_VEO / "logs"

# Aliases p/ nao quebrar callers antigos: DIR_FEITOS = DIR_INICIAIS, DIR_POS_V2 = DIR_POS_FINAL
DIR_FEITOS = DIR_INICIAIS
DIR_POS_V2 = DIR_POS_FINAL


def pos_v2_out_path(stem: str) -> Path:
    return DIR_POS_FINAL / f"{stem}.mp4"

# Alias da versao final
pos_final_out_path = pos_v2_out_path

# Pastas legadas (so p/ ler; nao escrevemos mais)
_DIR_LEGACY_VEOS = [
    Path(r"D:\veo\beta\videos\cron_shorts"),
    Path(r"D:\veo\beta\videos_pos\cron_shorts"),
]


def garantir_layout():
    """Cria a arvore central. Safe de chamar em loop."""
    for p in (RAIZ_VEO, DIR_CRON, DIR_INICIAIS, DIR_POS_FINAL, DIR_PROP_VEO3,
              DIR_POSTADOS, DIR_LOGS):
        p.mkdir(parents=True, exist_ok=True)


def pos_out_path(stem: str) -> Path:
    """Compat: alias p/ pos_final (a v1 'pos' foi descontinuada)."""
    return DIR_POS_FINAL / f"{stem}.mp4"


def pos_out_path_existente(stem: str) -> Path | None:
    """Retorna o path pos_final se ja existe, None c.c."""
    p = pos_out_path(stem)
    return p if p.exists() else None


def ja_feitos_path(stem: str) -> Path:
    """Alias p/ veo_videos_iniciais (material cru Veo)."""
    return DIR_INICIAIS / f"{stem}.mp4"


def log_path() -> Path:
    """Log do worker/centralizador."""
    return DIR_LOGS / "worker_noite.log"


def log(msg: str):
    """Loga com timestamp ao log do worker (e stdout)."""
    import time
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        garantir_layout()
        with open(log_path(), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    garantir_layout()
    print("layout centralizado em:", RAIZ_VEO)
    for p in [DIR_CRON, DIR_INICIAIS, DIR_POS_FINAL, DIR_PROP_VEO3, DIR_POSTADOS, DIR_LOGS]:
        print(f"  {p}  ->  existe={p.exists()}")
    # v1 antiga so p/ checagem
    v1 = RAIZ_VEO / "pos"
    print(f"  [v1 descontinuada] {v1}  ->  existe={v1.exists()}")
