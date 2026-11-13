# -*- coding: utf-8 -*-
"""hp_paineis.py — QUAIS painéis de um capítulo entram no vídeo, e onde fica a narração deles.

Usado pelo hiper-pipeline (vídeo vertical) e pelo hiper-longo (vídeo 16:9): os dois PRECISAM escolher
os mesmos painéis na mesma ordem, senão a narração em cache (uma locução por painel) desalinha.

  selecionar_paineis(pasta, max_panels, skip_credits, skip_final, start_panel) -> (paineis, capa_original)
  arquivo_narracao(pasta, n, skip_credits, skip_final, start_panel, fusao) -> Path do cache da narração
  pasta_video(pasta, idioma) -> workspace/videos/<obra>/capNN/<idioma>/ (subpastas normal/ e censurado/)
"""
import json
import re
import os
from pathlib import Path

from PIL import Image, ImageStat

from hp_common import PROJECT_DIR, VIDEOS_DIR, log

EXTS = {".jpg", ".jpeg", ".png"}
MIN_ALTURA = 300


def _em_branco(path):
    return ImageStat.Stat(Image.open(path).convert("L")).mean[0] > 248  # quase branco puro


def selecionar_paineis(panels_dir, max_panels, skip_credits=1, skip_final=0, start_panel=0, verbose=True):
    """(paineis, capa_original). capa_original = 1ª imagem (créditos/capa), só pra fundo borrado."""
    say = log if verbose else (lambda *_a, **_k: None)
    panel_files = sorted(f for f in Path(panels_dir).iterdir()
                         if f.suffix.lower() in EXTS and not f.name.startswith("_"))
    if not panel_files:
        return [], None
    cover_panel = panel_files[0]
    # Pular painéis de créditos/capa (geralmente os primeiros são avisos 18+, logos, etc)
    if skip_credits and len(panel_files) > skip_credits + max_panels:
        say(f"  Pulando {skip_credits} painéis iniciais (créditos/capa)")
        panel_files = panel_files[skip_credits:]
    # Filtrar painéis muito pequenos (provavelmente headers/ads/créditos)
    panel_files = [f for f in panel_files if Image.open(f).height >= MIN_ALTURA]
    # Filtrar painéis em branco (cortes errados do splitter)
    before = len(panel_files)
    panel_files = [f for f in panel_files if not _em_branco(f)]
    if len(panel_files) < before:
        say(f"  Removidos {before - len(panel_files)} painéis em branco")
    # Pular painéis finais (propaganda/créditos do grupo de scan no fim do capítulo)
    if skip_final and len(panel_files) > skip_final:
        say(f"  Pulando {skip_final} painéis finais (propaganda/créditos)")
        panel_files = panel_files[:-skip_final]
    # Offset de início (pra gerar partes seguintes do mesmo capítulo)
    if start_panel > 0:
        total_disp = len(panel_files)
        panel_files = panel_files[start_panel:]
        say(f"  Começando do painel {start_panel} (parte seguinte) — {len(panel_files)} de {total_disp} restantes")
    if len(panel_files) > max_panels:
        say(f"  {len(panel_files)} painéis -> limitando a {max_panels}")
        panel_files = panel_files[:max_panels]
    return panel_files, cover_panel


def pasta_video(panels_dir, idioma=None):
    """Onde o vídeo do capítulo fica: workspace/videos/<obra>/capNN/<idioma>/ quando a pasta dos painéis
    se chama '<obra>-capNN' (padrão da fila); senão a raiz de workspace/videos (jeito antigo)."""
    m = re.match(r"^(.+)-cap(\d+)$", Path(panels_dir).name)
    if not m:
        return VIDEOS_DIR
    return VIDEOS_DIR / m.group(1) / f"cap{int(m.group(2)):02d}" / (idioma or "pt")


def _versao_narracao():
    """Versão do roteiro, de config/fila.json ("narracao_v"), com HIPER_NARRACAO_V como atalho.

    Aposenta os roteiros guardados sem apagar nada — serve pra quando o jeito de LER os painéis muda
    e o roteiro velho deixa de servir (16/10: a leitura passou a transcrever caixa de narração e
    balão de pensamento; antes sumiam, e no cap 1 as caixas "HAN SIHYUN... / AQUELA MULHER FOI / O
    MEU PRIMEIRO AMOR." nunca foram ditas no vídeo).

    Fica na CONFIG, não só no ambiente, porque quem lê o roteiro são cinco pontos de entrada em
    processos diferentes: o render, a postagem (título, descrição e tags), a capa, o 16:9 e a
    tradução das línguas. Com a versão só no ambiente do render, os outros liam o roteiro antigo
    sem dar erro nenhum, e o vídeo sairia narrado de um jeito e anunciado de outro."""
    v = os.environ.get("HIPER_NARRACAO_V", "").strip()
    if v:
        return v
    try:
        cfg = json.loads((PROJECT_DIR / "config" / "fila.json").read_text(encoding="utf-8"))
        return str(cfg.get("narracao_v") or "").strip()
    except (OSError, ValueError):
        return ""


def arquivo_narracao(panels_dir, n, skip_credits=1, skip_final=0, start_panel=0, fusao=False):
    """Cache da narração. A chave SEMPRE inclui skip_credits: senão runs com skips diferentes (mas
    mesmo n de painéis) colidem no mesmo arquivo e reusam narração desalinhada."""
    part_tag = f"_s{start_panel}" if start_panel > 0 else ""
    part_tag += f"_sk{skip_credits}"
    if skip_final:
        part_tag += f"_sf{skip_final}"
    if fusao:
        part_tag += "_fusao"
    versao = _versao_narracao()
    if versao:
        part_tag += f"_{versao}"
    return PROJECT_DIR / "workspace" / "narration_cache" / f"{Path(panels_dir).name}{part_tag}_{n}panels.json"
