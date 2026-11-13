"""Botões ajustáveis do vídeo de produto (27/10): o que o MELHORADOR automático (produto\\melhorador.py) pode mexer
sozinho, sempre dentro de LIMITES. O código lê daqui; sem o arquivo, vale o padrão (= como o vídeo é hoje).
config\\produto_ajustes.json  ->  {"nome": valor}
"""
import json
from pathlib import Path

ARQ = Path(__file__).resolve().parents[2] / "config" / "produto_ajustes.json"

# nome: (padrão, mínimo, máximo, o que é) — números; o melhorador nunca sai da faixa
BOTOES = {
    "kenburns_zoom": (0.16, 0.06, 0.30, "quanto a foto aproxima/afasta na cena (0,16 = 16%)"),
    "kenburns_pan": (1.2, 0.0, 3.0, "deslize lateral da foto por quadro (px)"),
    "chat_fonte_msg": (52, 40, 64, "tamanho da letra das mensagens da conversa animada"),
    "legenda_fonte": (74, 60, 92, "tamanho da letra da legenda karaokê"),
    "vol_trilha": (0.13, 0.06, 0.22, "volume da trilha de fundo (antes do ducking)"),
    "folga_fala": (0.28, 0.15, 0.5, "respiro depois de cada fala (s)"),
    "pulso_botao": (0.06, 0.0, 0.12, "quanto o botão do cartão final cresce no pulso (0,06 = 6%)"),
    "punchin_video": (0.06, 0.0, 0.12, "aproximação lenta nas cenas de vídeo (dono/Veo) ao longo da cena"),
    "conversa_zoom": (0.12, 0.0, 0.25, "zoom lento do fundo borrado na cena de conversa (0,12 = 12% na cena)"),
    "conversa_subida": (50, 0, 120, "quantos px o cartão da conversa sobe devagar ao longo da cena"),
    "efeitos_transicao": (1, 0, 1, "1 = faixa elétrica/fogo/glitch atravessa a tela em cada troca de cena (impacto)"),
    "folga_dono": (0.45, 0.2, 1.2, "quanto a cena do dono continua depois da última palavra dele (s)"),
    "brilho_botao": (1, 0, 1, "1 = brilho atravessa o botão do cartão final a cada 1,5 s (e o botão entra crescendo)"),
    "destaques_tela": (1, 0, 1, "1 = trechos da fala entram na tela (cartão com ✓) na cena de imagem quando ditos"),
}
# listas/textos que o melhorador também pode mexer (validados no melhorador)
LISTAS = {"variantes_desligadas": [], "pesos_variantes": {}}


def _ler():
    try:
        return json.loads(ARQ.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def valor(nome):
    """Valor do botão já preso entre o mínimo e o máximo."""
    if nome in LISTAS:
        return _ler().get(nome, LISTAS[nome])
    padrao, mn, mx, _ = BOTOES[nome]
    try:
        v = float(_ler().get(nome, padrao))
    except (TypeError, ValueError):
        v = padrao
    v = min(max(v, mn), mx)
    return int(round(v)) if isinstance(padrao, int) else v


def todos():
    return {n: valor(n) for n in list(BOTOES) + list(LISTAS)}
