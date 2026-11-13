# -*- coding: utf-8 -*-
"""fx_foley.py — SOM DO QUE ACONTECE NA CENA (foley contextual).

Parte do motor de efeitos (ver mapa completo em effects_engine.py).
Diferente do SFX de transição (toca no corte), o foley é o som do EVENTO da
cena: campainha, porta, passos, soco, beijo. Disparado por keyword da
descrição/fala (onde estão as onomatopeias: "DING DONG", "CLACK"...).

  FOLEY_MAP                 (situação, arquivo, [keywords]) — ordem importa,
                            mais específico primeiro.
  pick_foley(desc, text)    escolhe o foley da cena (sem repetir o último).
  prepare_foley_audio(...)  mixa o foley com a voz. FOLEY_GAP_MODE (env
                            HIPER_FOLEY_GAP) decide se o foley toca ANTES da
                            voz (gap) ou junto.

Não importa outro fx_*. Mexa aqui pra: novo som de cena, nova keyword de
foley, ou timing (gap) do foley.
"""
import random
import subprocess
import os
import re
from pathlib import Path


ASSETS_DIR = Path(__file__).parent.parent / "workspace" / "assets"


FOLEY_DIR = ASSETS_DIR / "sfx_foley"


SFX_MEMES_DIR = ASSETS_DIR / "sfx_memes"


FOLEY_GAP_MODE = os.environ.get("HIPER_FOLEY_GAP", "1").strip().lower() in ("1", "true", "yes", "on")


FOLEY_GAP_S = 0.8  # atraso aplicado à voz no modo gap (foley toca limpo nesse início)


# (situação, arquivo, [keywords]) — ordem importa: mais específico primeiro.
# Arquivos relativos a ASSETS_DIR.
FOLEY_MAP = [
    ("campainha", "sfx_memes/Campainha Ding Dong - Efeitos sonoros Nerzinho.mp3",
        ["ding dong", "ding-dong", "campainha", "interfone", "toca a campainha",
         "toca o interfone", "som da campainha"]),
    ("bate_porta", "sfx_memes/Batendo na Porta - Efeitos sonoros Nerzinho.mp3",
        ["bate na porta", "batida na porta", "batidas na porta", "bate à porta",
         "batem na porta", "knock"]),
    ("porta_abre", "sfx_memes/Minecraft Porta abrindo - Efeitos sonoros Nerzinho.mp3",
        ["porta se abre", "abre a porta", "abriu a porta", "abre uma porta",
         "porta desliza", "destranca", "\"open\"", "open\"", "porta abrindo"]),
    ("porta_fecha", "sfx_foley/door_close.wav",
        ["fecha a porta", "porta se fecha", "porta fechando", "bateu a porta",
         "porta bate"]),
    ("clack", "sfx_foley/door_close.wav",
        ["clack", "fechadura", "tranca", "destrava"]),
    ("passos", "sfx_memes/Minecraft som de passos - Efeitos sonoros Nerzinho.mp3",
        ["step step", "passos", "ponta dos pés", "caminha pelo corredor",
         "pés caminham", "anda pelo corredor", "step"]),
    ("telefone", "sfx_foley/phone_ring.wav",
        ["celular toca", "telefone toca", "ligação", "atende o telefone",
         "smartphone toca", "chamada"]),
    ("notificacao", "sfx_foley/notification.wav",
        ["notificação", "mensagem chega", "beep", "tu!", "bipe"]),
    ("beijo", "sfx_foley/kiss_smooch.wav",
        ["beijo", "smooch", "beijando", "chu", "lábios", "selinho"]),
    ("soco", "sfx/punch.wav",
        ["soco", "golpe", "bateu", "tapa", "punch", "murro", "esmurr",
         "golpe na cabeça", "leva um golpe"]),
    ("vidro", "sfx_foley/glass_break.wav",
        ["quebra o vidro", "vidro quebr", "estilha", "shatter", "vidro estilha",
         "copo quebr"]),
    ("tiro", "sfx_foley/gunshot.wav",
        ["tiro", "atira", "dispara a arma", "gunshot", "disparo"]),
    ("espada", "sfx_foley/sword_slash.wav",
        ["espada", "lâmina corta", "golpe de espada", "sword"]),
    ("coracao", "sfx_foley/heartbeat.wav",
        ["coração dispar", "coração bate", "palpita", "disparou", "batendo forte",
         "coração acelera", "heartbeat"]),
    ("comer", "sfx_foley/eating_crunch.wav",
        ["mastiga", "comendo", "crunch", "morde", "macarrão", "come "]),
    ("beber", "sfx_foley/drinking_gulp.wav",
        ["bebe", "gole", "gulp", "tomando", "bebida", "brinde"]),
    ("chuva", "sfx_foley/rain_loop.wav",
        ["chuva", "chovendo", "tempestade de chuva", "rain"]),
    ("chuveiro", "sfx_foley/rain_loop.wav",
        ["chuveiro", "banho", "água caindo", "tomar banho"]),
    ("mar", "sfx_foley/ocean_waves.wav",
        ["ondas", "mar", "praia", "oceano", "ocean"]),
    ("grito", "sfx_foley/crowd_gasp.wav",
        ["multidão grita", "todos ofegam", "plateia", "gasp coletivo"]),
    ("aplauso", "sfx_foley/crowd_cheer.wav",
        ["aplauso", "aplaudem", "clap clap", "torcida", "comemora"]),
    ("trovao", "sfx_foley/thunder.wav",
        ["trovão", "relâmpago", "raio cai", "thunder"]),
    ("vento", "sfx_foley/wind_blow.wav",
        ["vento forte", "vendaval", "rajada", "wind"]),
    ("manha", "sfx_foley/birds_morning.wav",
        ["amanhece", "sol nasce", "de manhã", "pássaros cantam", "manhã ensolarada"]),
]


_last_foley_used = None  # anti-repetição consecutiva


def _foley_path(rel):
    p = ASSETS_DIR / rel
    if not p.exists():
        return None
    # Defesa: alguns assets baixados falharam e ficaram como XML de erro de ~111B
    # (header "<?xml" em vez de RIFF/ID3). Rejeita arquivos pequenos/inválidos.
    try:
        if p.stat().st_size < 1000:
            return None
        with open(p, "rb") as fh:
            head = fh.read(4)
        if head[:1] == b"<":
            return None
    except Exception:
        return None
    return p


def _kw_match(blob, kw):
    """Casa keyword com limite de palavra (evita 'mar' casar 'tomarmos').

    Keywords multi-palavra ou com pontuação (ex: "ding dong", "tu!", "\"open\"")
    usam substring direto. Tokens simples usam fronteira de palavra.
    """
    if " " in kw or any(c in kw for c in '"!?-'):
        return kw in blob
    return re.search(r'(?<![a-zà-ú])' + re.escape(kw) + r'(?![a-zà-ú])', blob) is not None


def pick_foley(desc, text=""):
    """Escolhe o foley contextual do painel pela situação detectada nas keywords.

    Retorna (caminho_do_arquivo, nome_da_situacao) ou (None, None).
    Evita repetir o mesmo foley em painéis consecutivos.
    """
    global _last_foley_used
    blob = f"{desc} {text}".lower()
    for situacao, rel, kws in FOLEY_MAP:
        if any(_kw_match(blob, kw) for kw in kws):
            path = _foley_path(rel)
            if not path:
                continue
            if str(path) == _last_foley_used:
                # mesmo som consecutivo -> pula (deixa respirar)
                continue
            _last_foley_used = str(path)
            return path, situacao
    return None, None


def prepare_foley_audio(voice_audio, foley_file, out_audio, gap_mode=None,
                        foley_vol_gap=1.1, foley_vol_together=0.5):
    """Mixa o foley contextual com o áudio da voz, gerando um novo wav.

    build_clip deriva a duração do clip do áudio (ffprobe), então o áudio
    estendido pelo gap é absorvido automaticamente — sem conflito com o
    mix de SFX de transição (que roda depois, em apply_effects_to_cmd).

    Modos:
      - gap (True): a voz é ATRASADA FOLEY_GAP_S; o foley toca limpo nesse
        início (volume cheio), depois entra a fala. O clip fica ~FOLEY_GAP_S
        mais longo. Igual à "pausa antes" das transições — não atropela a voz.
      - junto (False): o foley é mixado SOBRE a voz desde t=0, em volume baixo
        (fica de fundo sob a fala).

    Retorna o caminho do áudio gerado, ou o áudio original se algo falhar.
    """
    if gap_mode is None:
        gap_mode = FOLEY_GAP_MODE
    if not foley_file or not Path(foley_file).exists():
        return str(voice_audio)
    if not Path(voice_audio).exists():
        return str(voice_audio)

    delay_ms = int(FOLEY_GAP_S * 1000)
    if gap_mode:
        # voz atrasada; foley toca no início em volume cheio; soma das durações.
        # Foley é CORTADO (gap + ~1.5s) com fade-out: cobre a pausa e um pouco da
        # fala, depois some. Sem isso, um foley longo (ex: gulp de 12s) domina a
        # abertura e estica o clip — soava como "chuva" no começo do vídeo.
        foley_cap = FOLEY_GAP_S + 1.5
        fade_st = max(0.1, foley_cap - 0.4)
        fc = (
            f"[0:a]adelay={delay_ms}|{delay_ms},apad=pad_dur=0.15[v];"
            f"[1:a]volume={foley_vol_gap},atrim=0:{foley_cap:.2f},"
            f"afade=t=out:st={fade_st:.2f}:d=0.4[f];"
            f"[f][v]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[a]"
        )
    else:
        # foley de fundo, mixado sobre a voz desde t=0; duração = voz
        fc = (
            f"[1:a]volume={foley_vol_together}[f];"
            f"[0:a][f]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
        )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(voice_audio),
        "-i", str(foley_file),
        "-filter_complex", fc,
        "-map", "[a]",
        "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(out_audio),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        return str(out_audio) if Path(out_audio).exists() else str(voice_audio)
    except Exception:
        return str(voice_audio)

