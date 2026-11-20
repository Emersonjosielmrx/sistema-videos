# -*- coding: utf-8 -*-
r"""services/facebook/reel.py — postar Reel numa Página do Facebook por HTTP (sem Chrome). EM CONSTRUÇÃO (20/11).

O que já está provado (sessao.py): login por cookie, agir como a Página (i_user), GraphQL com fb_dtsg/lsd/av.
O que falta e SÓ entra depois de capturado de uma postagem REAL (regra do projeto: nada de endpoint inventado;
regra da dona: nada de post de teste em Página real):
  1. upload do arquivo de vídeo  -> endpoint, cabeçalhos (offset/tamanho), o que devolve (video_id / handle)
  2. publicar o Reel             -> doc_id + variables do GraphQL do composer do Business Suite
  3. confirmação                 -> o que a resposta traz quando publicou (id do post/reel)
Capturas: capturas\passivo_facebook_20261120.jsonl (postagens reais das 15:20 e 21–22 h de 20/11).

Enquanto não estiver pronto, `postar()` levanta NaoPronto e quem chama segue pelo Chrome (fb_reel_bs.py).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


class NaoPronto(RuntimeError):
    """O postador HTTP ainda não foi completado a partir de uma captura real: use o caminho com Chrome."""


def postar(conta, page_id, video, texto):
    raise NaoPronto("postar Reel por HTTP ainda não capturado (ver docs\\FACEBOOK_SEM_NAVEGADOR.md)")
