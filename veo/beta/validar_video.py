# -*- coding: utf-8 -*-
"""validar_video.py — o video gerado presta? (item AT-02 de docs\\PLANO_MELHORIAS_VEO.md)

Ate 15/10/2026 a unica conferencia depois do download era `validar_video()` dentro do
cron: largura, altura e codec de audio. Nao olhava duracao, proporcao, quadro preto,
quadro congelado nem volume — e, pior, quando o ffprobe falhava ela devolvia
`(None, "<mensagem de erro>")`, e quem chamava lia essa mensagem como "tem audio".
Video mudo, de 4 s ou no formato errado entrava no cache como SUCESSO.

Este modulo e autocontido (so ffmpeg/ffprobe, nada de importar o pacote do
manhwa-react) e devolve sempre um dicionario; nunca levanta excecao.

    from validar_video import validar
    r = validar("video.mp4")                  # bruto do Veo: 9:16, ~8 s, com audio
    if not r["ok"]:
        print(r["problemas"])

Espelha D:\\manhwa-react\\mr\\validate.py::validate_output, adaptado ao Short de 8 s:
la o alvo e um Short de react de 30-60 s ja masterizado; aqui e o clipe cru do Veo.
"""
import json
import re
import subprocess
from pathlib import Path

# o mesmo binario que o resto do projeto usa
_FFMPEG = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"
try:  # prefere a constante central, se o pacote estiver no path
    from pos_producao.config import FFMPEG as _FFMPEG_CFG  # type: ignore
    _FFMPEG = _FFMPEG_CFG or _FFMPEG
    _FFPROBE = str(Path(_FFMPEG).with_name("ffprobe.exe"))
except Exception:
    pass

PROPORCAO_ALVO = 9 / 16          # 0.5625
TOLERANCIA_PROPORCAO = 0.02
DURACAO_ESPERADA_S = 8.0
TOLERANCIA_DURACAO_S = 1.0
DURACAO_MINIMA_S = 5.0
TAMANHO_MINIMO_BYTES = 100_000   # abaixo disso nao e video (ver Nano Banana no GUIA)
# erros que o ffmpeg solta quando o arquivo abre mas nao da para decodificar
_RX_DECODE = re.compile(
    r"Invalid NAL unit size|Error splitting the input into NAL units|"
    r"missing picture in access unit|error while decoding|"
    r"Invalid data found when processing input|could not find codec parameters",
    re.I)


def _correr(cmd, timeout=120):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          encoding="utf-8", errors="replace")


def _sonda(mp4):
    """ffprobe -> dict. Levanta se nao der (quem chama trata como falha, nao como ok)."""
    r = _correr([_FFPROBE, "-v", "error", "-show_format", "-show_streams",
                 "-of", "json", str(mp4)], timeout=60)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "ffprobe falhou").strip()[:200])
    return json.loads(r.stdout)


def validar(mp4, duracao_esperada=DURACAO_ESPERADA_S, exigir_audio=True,
            lufs_alvo=None, checar_imagem=True):
    """Devolve {ok, problemas[], duracao, largura, altura, tem_audio, lufs, ...}.

    duracao_esperada=None nao confere duracao (util para o video ja montado).
    lufs_alvo=None nao confere volume (o bruto do Veo ainda nao foi nivelado).
    checar_imagem=False pula a passada de quadro preto/congelado (mais rapido).
    """
    rel = {"ok": False, "problemas": [], "arquivo": str(mp4)}
    p = Path(mp4)
    if not p.is_file():
        rel["problemas"].append("arquivo nao existe")
        return rel
    tam = p.stat().st_size
    rel["bytes"] = tam
    if tam < TAMANHO_MINIMO_BYTES:
        # 1,8 KB mjpeg 512x512 = o Flow caiu no modo imagem (Nano Banana)
        rel["problemas"].append(f"arquivo pequeno demais ({tam} bytes): pode ser imagem, nao video")
        return rel

    try:
        info = _sonda(p)
    except Exception as e:
        rel["problemas"].append(f"ffprobe falhou: {e}")
        return rel

    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    dur = float(info.get("format", {}).get("duration") or 0)
    rel["duracao"] = round(dur, 2)
    rel["tem_audio"] = bool(a)
    rel["codec_video"] = (v or {}).get("codec_name")
    rel["codec_audio"] = (a or {}).get("codec_name")

    if not v:
        rel["problemas"].append("sem faixa de video")
        return rel
    larg, alt = int(v.get("width") or 0), int(v.get("height") or 0)
    rel["largura"], rel["altura"] = larg, alt
    if not larg or not alt:
        rel["problemas"].append("sem dimensoes")
        return rel

    # proporcao (nao a dimensao exata: o bruto sai 720x1280 e o montado 1080x1920)
    prop = larg / alt
    rel["proporcao"] = round(prop, 4)
    if abs(prop - PROPORCAO_ALVO) > TOLERANCIA_PROPORCAO:
        rel["problemas"].append(f"nao esta em 9:16 ({larg}x{alt})")
    if (v.get("codec_name") or "").lower() in ("mjpeg", "png", "bmp"):
        rel["problemas"].append(f"codec {v.get('codec_name')}: isso e imagem, nao video")

    if exigir_audio and not a:
        rel["problemas"].append("sem audio")
    if duracao_esperada and abs(dur - duracao_esperada) > TOLERANCIA_DURACAO_S:
        rel["problemas"].append(f"duracao {dur:.1f}s (esperado ~{duracao_esperada:.0f}s)")
    if dur < DURACAO_MINIMA_S:
        rel["problemas"].append(f"curto demais ({dur:.1f}s)")

    # A decodificacao completa roda SEMPRE (16/10, 3.3 do CONTINUAR_DAQUI): antes ela so acontecia dentro de
    # checar_imagem, e quem desligava preto/congelado para ganhar tempo desligava junto o pega-arquivo-quebrado.
    if True:
        filtros = "blackdetect=d=0.5:pix_th=0.10,freezedetect=n=-60dB:d=2" if checar_imagem else None
        cmd = [_FFMPEG, "-hide_banner", "-i", str(p)] + (["-vf", filtros] if filtros else [])
        if a and lufs_alvo is not None:
            cmd += ["-af", "ebur128"]
        cmd += ["-f", "null", "-"]
        try:
            r = _correr(cmd, timeout=180)
            saida = r.stderr or ""
            # O ffprobe le o cabecalho e diz que esta tudo bem mesmo quando o
            # BITSTREAM esta quebrado: o container fica intacto e so a decodificacao
            # falha. Sem olhar o codigo de saida aqui, este modulo aprovava arquivo
            # ilegivel — na varredura de 16/10, 27 dos 240 mp4 de
            # D:\hipercool-materiais\veo\limpos (11%, a pasta que vai ao ar) nao
            # decodificam, e todos passavam.
            if r.returncode != 0 or _RX_DECODE.search(saida):
                achado = _RX_DECODE.search(saida)
                rel["problemas"].append(
                    "video nao decodifica (bitstream corrompido"
                    + (f": {achado.group(0)}" if achado else f", ffmpeg saiu {r.returncode}") + ")")
        except Exception as e:
            saida = ""
            rel["problemas"].append(f"analise de imagem falhou: {str(e)[:60]}")
        pretos = re.findall(r"black_start:(\S+) black_end:(\S+)", saida)
        if pretos:
            rel["trechos_pretos"] = len(pretos)
            rel["problemas"].append(f"{len(pretos)} trecho(s) preto(s)")
        congelado = re.findall(r"freeze_start", saida)
        if congelado:
            rel["trechos_congelados"] = len(congelado)
            rel["problemas"].append(f"{len(congelado)} trecho(s) congelado(s)")
        if lufs_alvo is not None:
            medidas = re.findall(r"I:\s+(-?[\d.]+) LUFS", saida)
            if medidas:
                lufs = float(medidas[-1])
                rel["lufs"] = lufs
                if abs(lufs - lufs_alvo) > 2.0:
                    rel["problemas"].append(f"volume {lufs} LUFS (alvo {lufs_alvo})")

    rel["ok"] = not rel["problemas"]
    return rel


def resumo(rel: dict) -> str:
    """Uma linha para o log."""
    if rel.get("ok"):
        return (f"OK {rel.get('largura')}x{rel.get('altura')} {rel.get('duracao')}s "
                f"{'com audio' if rel.get('tem_audio') else 'SEM AUDIO'}")
    return "REPROVADO: " + "; ".join(rel.get("problemas", []))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("uso: validar_video.py <video.mp4> [mais videos...]")
        sys.exit(1)
    ruins = 0
    for arq in sys.argv[1:]:
        r = validar(arq)
        print(f"{Path(arq).name}: {resumo(r)}")
        ruins += 0 if r["ok"] else 1
    sys.exit(1 if ruins else 0)
