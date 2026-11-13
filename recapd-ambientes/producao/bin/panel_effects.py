"""panel_effects.py — efeitos que MEXEM NO PAINEL (T15). Grupos A (zoom/câmera) e B (tempo/impacto).

Porte dos builders de _testes/COMANDOS_PROTOTIPOS.sh (validados/aprovados) pra Python. Cada
efeito é um filtro `zoompan`/etc aplicado ao painel gerando um clip 720x1280 com o ÁUDIO do
painel (não regera). Roteado por keyword/emoção da narração, igual elemental_transitions.
Flag PANEL_FX=1 no caller. Anti-repetição consecutiva.

ESCOPO desta versão: grupos A (11 efeitos "dentro do quadro") + B (8 tempo/impacto). Todos
single-image, SEM depender de depth/recorte/IMG2 (baratos, sem asset extra). Grupos C (transição
c/ IMG2), D (recorte/depth), E (word-strike HyperFrames), F (multi-painel) = EXTENSÃO futura
(builders no COMANDOS_PROTOTIPOS.sh; exigem cache de depth/rembg ou 2º painel).

NOTA build local: drawtext segfauta (texto só via HyperFrames); gblur eval=frame não anima
(usar sendcmd); imagem estática exige -loop 1 -t N. W/H do projeto = 720x1280 (edge).
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

W, H = 720, 1280
FPS = 25


def _ff():
    f = shutil.which("ffmpeg")
    if f:
        return f
    import glob as _g
    for pat in (str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/**/ffmpeg.exe"),
                "C:/Users/*/AppData/Local/Microsoft/WinGet/**/ffmpeg.exe"):
        h = _g.glob(pat, recursive=True)
        if h:
            return h[0]
    return "ffmpeg"


# Cada efeito = (vf_template, encaixe). vf recebe {W}{H}{FPS}{DUR}{FR} (FR=frames=DUR*FPS).
# Só single-image (grupos A/B). Os transição/depth ficam de fora desta versão.
PANEL_FX = {
    # GRUPO A — zoom/câmera (dentro do quadro)
    "facezoom":   "scale=2160:3840,setsar=1,zoompan=z='min(1+0.008*on,1.55)':x='iw/2-(iw/zoom/2)':y='ih*0.28-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "dollypush":  "scale=2160:3840,setsar=1,zoompan=z='min(1+0.005*on,1.35)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "pulsezoom":  "scale=1584:2816,setsar=1,zoompan=z='1.1+0.06*sin(on/3)':x='iw/2-(iw/zoom/2)':y='ih*0.4-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "dollyzoom":  "scale=2160:3840,setsar=1,zoompan=z='1.5-0.4*sin(on/63*1.57)':x='iw/2-(iw/zoom/2)':y='ih*0.4-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "orbit":      "scale=1584:2816,setsar=1,zoompan=z=1.25:x='iw/2-(iw/zoom/2)+120*sin(on/12)':y='ih/2-(ih/zoom/2)+120*cos(on/12)':d={FR}:s={W}x{H}:fps={FPS}",
    "panLR":      "scale=1584:2816,setsar=1,zoompan=z=1.3:x='(iw-iw/zoom)*on/{FR}':y='ih*0.3-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "panUP":      "scale=1584:2816,setsar=1,zoompan=z=1.3:x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(1-on/{FR})':d={FR}:s={W}x{H}:fps={FPS}",
    "handheld":   "scale=1584:2816,setsar=1,zoompan=z=1.25:x='iw/2-(iw/zoom/2)+18*sin(on*0.9)+10*sin(on*2.3)':y='ih*0.4-(ih/zoom/2)+15*cos(on*1.1)+8*sin(on*3.1)':d={FR}:s={W}x{H}:fps={FPS}",
    "breathing":  "scale=1584:2816,setsar=1,zoompan=z='1.15+0.05*sin(on/15)':x='iw/2-(iw/zoom/2)':y='ih*0.4-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "snapzoom":   "scale=2160:3840,setsar=1,zoompan=z='1+0.2*floor(on/15)':x='iw/2-(iw/zoom/2)':y='ih*0.35-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    # GRUPO B — tempo/impacto (dentro do quadro)
    "freezeimpact": "scale=2160:3840,setsar=1,zoompan=z='if(lte(on,8),1+0.06*on,1.5)':x='iw/2-(iw/zoom/2)':y='ih*0.3-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS},eq=brightness='if(lt(t,0.32),0.6,0)':eval=frame",
    "shockwave":  "scale=1584:2816,setsar=1,zoompan=z='1+0.35*exp(-on/4)*cos(on/2)':x='iw/2-(iw/zoom/2)':y='ih*0.35-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "speedlineszoom": "scale=2160:3840,setsar=1,zoompan=z='min(1+0.05*on,1.8)':x='iw/2-(iw/zoom/2)':y='ih*0.3-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "slowmoin":   "scale=2160:3840,setsar=1,zoompan=z='1+0.5*(1-pow(1-on/63,3))':x='iw/2-(iw/zoom/2)':y='ih*0.32-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "doubletake": "scale=2160:3840,setsar=1,zoompan=z='1.2+0.4*abs(sin(on/10))':x='iw/2-(iw/zoom/2)':y='ih*0.3-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "heartbeatzoom": "scale=1584:2816,setsar=1,zoompan=z='1.2+0.12*exp(-mod(on,18)/3)':x='iw/2-(iw/zoom/2)':y='ih*0.35-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    # FAMÍLIAS NOVAS L/N/O/P (single-image, sem .cmd/IMG2). As que usam sendcmd/2º painel
    # (bulge, cardflip, perspectiveswing, dooropen, pixeldissolve, graindissolve) = extensão futura.
    # GRUPO L — distorção óptica (usar leve; sutil, não enjoar)
    "ripple":     "scale={W}:{H},setsar=1,fps={FPS},geq=lum='p(X+8*sin((Y/20)+T*4),Y+8*sin((X/20)+T*4))':cb='p(X,Y)':cr='p(X,Y)'",
    "heathaze":   "scale={W}:{H},setsar=1,fps={FPS},geq=lum='p(X+4*sin(Y/8+T*6),Y)':cb='p(X,Y)':cr='p(X,Y)'",
    "underwater": "scale={W}:{H},setsar=1,fps={FPS},geq=lum='p(X+10*sin(Y/30+T*2),Y+6*cos(X/30+T*1.5))':cb='p(X,Y)':cr='p(X,Y)'",
    # GRUPO N — espelho/reflexo
    "waterreflection": "scale={W}:854,setsar=1[top];[top]split[t1][t2];[t2]vflip,crop={W}:426:0:0,geq=lum='p(X+6*sin(Y/10+T*3),Y)':cb='p(X,Y)':cr='p(X,Y)',eq=brightness=-0.1[refl];[t1][refl]vstack",
    "mirrorsplit": "scale={W}:{H},setsar=1,crop=360:{H}:0:0[l];[l]split[l1][l2];[l2]hflip[r];[l1][r]hstack",
    "kaleidoscope": "scale=360:640,setsar=1[q];[q]split[q1][q2];[q2]hflip[qr];[q1][qr]hstack[top];[top]split[tt][tb];[tb]vflip[bot];[tt][bot]vstack",
    # GRUPO O — perspectiva 3D (estático, sem swing animado)
    "perspectivetilt": "scale={W}:{H},setsar=1,fps={FPS},perspective=x0=100:y0=0:x1=620:y1=0:x2=0:y2={H}:x3={W}:y3={H}:interpolation=linear",
    # GRUPO P — dissolução/partícula
    "dispersion": "scale={W}:{H},setsar=1,fps={FPS},noise=alls=20:allf=t+u,fade=t=out:st=0.8:d=1.0",
    # ── LOTE ADITIVO 2026-07-03 (single-image, sem .cmd/IMG2/rembg — seguros de portar) ──
    # GRUPO A/B extra (zoom/câmera/tempo)
    "whipzoom":   "scale=2160:3840,setsar=1,zoompan=z='min(1+0.06*on,2.4)':x='iw*0.5-(iw/zoom/2)':y='ih*0.25-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS},tblend=all_mode=average",
    "kenburnsdiag": "scale=1584:2816,setsar=1,zoompan=z='1.1+0.003*on':x='(iw-iw/zoom)*on/{FR}':y='(ih-ih/zoom)*on/{FR}':d={FR}:s={W}x{H}:fps={FPS}",
    "stutter":    "scale=1584:2816,setsar=1,zoompan=z='1.2+0.05*floor(mod(on,10)/5)':x='iw/2-(iw/zoom/2)':y='ih*0.35-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS},fps=12",
    "pulsebeat":  "scale=1584:2816,setsar=1,zoompan=z='1.12+0.06*abs(sin(on/25*6.283))':x='iw/2-(iw/zoom/2)':y='ih*0.4-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    # GRUPO G — cinema/enquadramento
    "crashzoomout": "scale=2160:3840,setsar=1,zoompan=z='max(2.2-0.12*on,1.0)':x='iw/2-(iw/zoom/2)':y='ih*0.35-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    "tiltdutch":  "scale=864:1536,setsar=1,rotate='0.12*min(t,1.2)':c=black:ow={W}:oh={H}",
    # GRUPO U — rotação/roll
    "rollcw":     "scale=1080:1920,setsar=1,rotate='0.1*sin(t*1.2)':c=black:ow={W}:oh={H}",
    "spinin":     "scale=1440:2560,setsar=1,rotate='0.6*(1-min(t/1.2,1))':c=black:ow={W}:oh={H},zoompan=z='max(1.5-0.4*min(on/30,1),1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS}",
    # GRUPO T — echo/rastro
    "echotrail":  "scale=1440:2560,setsar=1,zoompan=z=1.2:x='iw/2-(iw/zoom/2)+200*sin(on/12)':y='ih/2-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS},tmix=frames=8:weights='1 1 1 1 1 1 1 1'",
    "motionsmear": "scale=1440:2560,setsar=1,zoompan=z=1.3:x='(iw-iw/zoom)*min(on/40,1)':y='ih*0.4-(ih/zoom/2)':d={FR}:s={W}x{H}:fps={FPS},tblend=all_mode=average,tblend=all_mode=average",
}

# Efeitos multi-label (têm ';' no filtro → geram cadeia própria, não entram como [0:v]{vf}[v]).
_MULTI = {"waterreflection", "mirrorsplit", "kaleidoscope"}

# keyword PT → efeito (roteamento, igual elemental_transitions). Emoção forte primeiro,
# depois cotidiano amplo. Fallback probabilístico no final do pick_effect pra que ~35%
# dos painéis sem keyword também ganhem efeito suave (breathing/handheld/dollypush).
import random as _rnd

FX_KEYWORDS = [
    # --- IMPACTO / AÇÃO ---
    ("freezeimpact", ["soco", "golpe", "impacto", "explos", "bateu", "atingiu",
                      "porrada", "chute", "tapa", "esmagou", "destrui", "arrebent",
                      "derrub", "acertou", "nocaute", "esbarr"]),
    ("shockwave",    ["onda", "estrondo", "detonou", "explodiu", "trovão", "trovao",
                      "terremo", "abalo", "tremeu", "estremec"]),
    ("speedlineszoom", ["corre", "veloz", "rápido", "disparou", "sprint", "fugiu",
                        "saiu correndo", "escapou", "persegu", "atrás del"]),
    # --- EMOÇÃO / REAÇÃO ---
    ("slowmoin",     ["câmera lenta", "camera lenta", "slow", "devagar", "em câmera",
                      "tempo parou", "congelou", "lentamente"]),
    ("heartbeatzoom", ["coração", "coracao", "nervos", "ansios", "batida", "palpita",
                       "medo", "assustou", "temor", "pavor", "apreens", "aflição",
                       "suou frio", "arrepiou", "tremendo"]),
    ("facezoom",     ["olhou", "encarou", "fitou", "observ", "rosto", "olhos",
                      "olhar", "fixo", "mirou", "viu", "notou", "percebeu",
                      "olhando", "olharam", "olhou pra", "olhava"]),
    ("dollyzoom",    ["chocad", "vertigem", "não acredito", "assombr", "incrédulo",
                      "incredulo", "estupefat", "sem palavras", "não pode ser"]),
    ("pulsezoom",    ["tensão", "tensao", "suspense", "aguarde", "silêncio",
                      "silencio", "pausa", "hesitou", "tenso", "apreensiv"]),
    ("dollypush",    ["revelaç", "descobr", "segredo", "verdade", "revelou",
                      "mostrou", "apareceu", "surgiu", "finalmente"]),
    ("doubletake",   ["surpres", "de repente", "inesperad", "do nada", "subitamente",
                      "repentin", "inesperado", "não esperava"]),
    # --- MOVIMENTO / CENA ---
    ("panLR",        ["cenário", "cenario", "paisagem", "lugar", "cidade", "lugar",
                      "ambiente", "local", "bar", "restaur", "escola", "prédio",
                      "predio", "rua", "sala", "escritório", "escritorio", "cozinha"]),
    ("panUP",        ["subiu", "levantou", "ergueu", "de pé", "alto", "torre",
                      "prédio", "olhou pra cima", "céu", "ceu"]),
    ("handheld",     ["caminhando", "andando", "seguiu", "foi até", "entrou",
                      "saiu", "passou", "voltou", "desceu", "foi embora"]),
    ("orbit",        ["girou", "rodeou", "ao redor", "cercou", "em volta"]),
    ("breathing",    ["pensou", "refletiu", "lembrou", "memória", "memoria",
                      "sozinho", "sozinha", "calmo", "calma", "tranquil",
                      "em paz", "relaxou", "descansou"]),
    ("snapzoom",     ["gritou", "berrou", "exclamou", "vociferou", "bradou",
                      "esbravejou", "ordenou", "mandou"]),
    # --- CONVERSA / DIÁLOGO (slice-of-life) ---
    ("dollypush",    ["falou", "disse", "respondeu", "explicou", "comentou",
                      "perguntou", "questionou"]),
    ("facezoom",     ["sorriu", "sorriso", "risada", "riu", "gargalh",
                      "chorou", "lágrima", "lagrima", "chorando"]),
    ("heartbeatzoom", ["confus", "embaraç", "embarac", "constrang",
                       "envergon", "sem graça", "sem graca", "corou"]),
    # --- ESPECIAIS (L/N/O/P) ---
    ("underwater",   ["água", "agua", "submerso", "afund", "mergulh", "no mar", "no fundo",
                      "chuva", "chuvoso", "encharcad", "molhado", "molhada"]),
    ("heathaze",     ["calor", "deserto", "quente demais", "sol escaldante", "suando",
                      "quente", "pegando fogo"]),
    ("ripple",       ["sonho", "sonhou", "ilusão", "ilusao", "miragem", "distorc",
                      "imaginação", "imaginacao", "fantasi", "alucinação"]),
    ("waterreflection", ["reflexo", "espelho d'água", "lago", "poça", "reflet na água"]),
    ("mirrorsplit",  ["espelho", "reflexão", "reflexao"]),
    ("kaleidoscope", ["caleidosc", "psicodél", "psicodel", "hipnó", "hipno"]),
    ("perspectivetilt", ["inclinou", "tombou a cena", "de lado", "torto", "caiu",
                         "desabou", "tombou", "desmoron"]),
    ("dispersion",   ["desintegr", "virou pó", "virou po", "sumindo", "se dissolv",
                      "desaparec", "sumiu", "evaporou"]),
    # --- LOTE ADITIVO 2026-07-03 (roteamento dos efeitos novos) ---
    ("whipzoom",     ["virou-se", "virou de repente", "num átimo", "num instante",
                      "rapidamente olhou", "de súbito", "num piscar"]),
    ("crashzoomout", ["afastou", "recuou", "distância", "distancia", "ao longe", "panorama",
                      "revelou o lugar", "toda a cena", "vista geral", "enorme", "imenso", "gigantesco"]),
    ("tiltdutch",    ["desequilíbr", "desequilibr", "vertiginos", "louco", "insano",
                      "delírio", "delirio", "atordoad", "zonzo", "cambale"]),
    ("rollcw",       ["rodopi", "rodou", "girando", "cambalhota", "capotou", "virou de cabeça"]),
    ("spinin",       ["chegou girando", "entrou triunf", "apareceu em grande", "irrompeu",
                      "surgiu de repente", "explodiu em cena"]),
    ("echotrail",    ["eco", "vibrou", "ecoou", "reverber", "vertigem", "zumbido", "atordoou"]),
    ("motionsmear",  ["disparou pra", "voou até", "arremessou", "lançou-se", "num borrão",
                      "veloz demais", "rasgou o ar"]),
    ("kenburnsdiag", ["contempl", "admirou", "vista", "horizonte", "amplo", "extenso",
                      "por toda parte", "estendia-se"]),
    ("stutter",      ["hesitou", "gaguejou", "travou", "congelou de vez", "paralisou",
                      "não conseguia se mexer", "engasgou"]),
    ("pulsebeat",    ["batida forte", "pulsando", "ritmo", "coração acelerou", "adrenalina",
                      "euforia", "empolg"]),
    # --- TRANSIÇÕES (Grupo C/F — usam o PRÓXIMO painel via img2) ---
    ("mangaslide",   ["enquanto isso", "mais tarde", "no dia seguinte", "horas depois",
                      "em outro lugar", "noutro lugar", "na manhã seguinte", "de volta a",
                      "mudança de cena", "cena seguinte", "logo depois", "naquela noite"]),
    ("splitreveal",  ["ao mesmo tempo", "simultaneamente", "por outro lado", "em paralelo"]),
    ("wipediag",     ["e então tudo mudou", "num corte seco", "de uma hora pra outra"]),
    # --- AVANÇADOS (depth/atmosfera/multi-personagem — inputs gerados) ---
    ("twocharface",  ["os dois", "se encararam", "encararam-se", "frente a frente", "cara a cara",
                      "confronto", "olharam-se", "um pro outro", "face a face"]),
    ("ganglineup",   ["o grupo", "a gangue", "todos eles", "em fila", "lado a lado", "o bando", "a turma"]),
    ("snowdepth",    ["nevando", "neve caía", "flocos de neve", "inverno gelado", "nevava"]),
    ("lightraysdepth", ["raios de sol", "luz divina", "feixe de luz", "sol atravessava", "luz dourada", "raio de luz"]),
    ("parallax3layer", ["profundidade", "ao longe se via", "camadas", "cenário vasto", "ao fundo"]),
    ("depthdolly",   ["mergulhou na cena", "adentrou", "avançou pela", "penetrou no"]),
]

# Efeitos suaves pra fallback probabilístico (não atrapalham, dão vida ao painel)
_SAFE_FALLBACKS = ["breathing", "handheld", "dollypush", "pulsezoom", "panLR", "facezoom"]
_FALLBACK_CHANCE = 0.35  # 35% dos painéis sem keyword ganham efeito suave

_last_fx = None
_fx_hist = {}   # histograma de uso por efeito (variedade por capítulo)

# Pool VISÍVEL preferido quando um efeito satura/repete — puxa pro RECORTE (o que a usuária
# mais quer) e pra efeitos de impacto, em vez de cair sempre no facezoom/dollypush sutil.
_VISIBLE_POOL = ["parallaxcut", "charfloat", "charslidein", "charsway", "bgblurfocus",
                 "freezeimpact", "shockwave", "slowmoin", "dollyzoom", "orbit", "snapzoom", "panLR",
                 "whipzoom", "crashzoomout", "spinin", "echotrail", "kenburnsdiag", "pulsebeat"]


def reset_fx_hist():
    """Zera o histograma de efeitos (chamar no início de cada capítulo)."""
    _fx_hist.clear()
    globals()['_last_fx'] = None


def fx_hist():
    """Retorna o histograma {efeito: contagem} — pra validar variedade."""
    return dict(_fx_hist)


def _record(fx):
    if fx:
        _fx_hist[fx] = _fx_hist.get(fx, 0) + 1
        globals()['_last_fx'] = fx
    return fx


def _saturado(fx):
    """True se o efeito já foi usado MUITO mais que a média (evita concentrar em 2-3)."""
    if not _fx_hist:
        return False
    med = sum(_fx_hist.values()) / max(1, len(_fx_hist))
    return _fx_hist.get(fx, 0) >= max(3, med * 1.5)


def _menos_usado(pool):
    cand = [f for f in pool if f != _last_fx]
    if not cand:
        return None
    return min(cand, key=lambda f: _fx_hist.get(f, 0))


def pick_effect(text, is_sensual=False, is_texto_plano=False, tem_balao=False, img_path=None):
    """Retorna o efeito de painel pela narração, ou None. FILOSOFIA: na dúvida, None.

    SALVAGUARDAS: is_sensual/is_texto_plano → None.
    VARIEDADE (2026-07-03): histograma penaliza efeito SATURADO e puxa pro _VISIBLE_POOL
    (recorte/impacto), pra parar de cair sempre em facezoom/dollypush em recap cheio de
    'olhou/viu/disse'. Recorte auto-gate: se o painel não tem personagem, o builder cai no fallback."""
    global _last_fx
    if is_sensual or is_texto_plano:
        return None
    _all = set(PANEL_FX) | set(CUTOUT_FX) | set(SENDCMD_FX) | set(FX2) | set(ADVFX)

    def _finaliza(fx):
        if not fx:
            return None
        # se saturou ou repetiria consecutivo → troca por um VISÍVEL menos usado
        if fx == _last_fx or _saturado(fx):
            alt = _menos_usado(list(CUTOUT_FX) + _VISIBLE_POOL)  # inclui TODOS os recortes portados
            if alt:
                fx = alt
        return _record(fx)

    # motion_director: decisão por visão pré-computada
    if img_path is not None:
        try:
            import motion_director as _md
            _dec = _md.decidir_efeito(img_path, text, is_sensual=is_sensual, use_ia=False)
            _fx = _dec.get("efeito") if _dec else None
            if _fx and _fx in _all:
                return _finaliza(_fx)
        except Exception:
            pass
    t = (text or "").lower()
    if not t.strip():
        return None
    for fx, kws in FX_KEYWORDS:
        if any(k in t for k in kws):
            return _finaliza(fx)
    # fallback: painel sem keyword → puxa efeito VISÍVEL menos usado (variedade real)
    if not tem_balao and _rnd.random() < _FALLBACK_CHANCE:
        return _finaliza(_menos_usado(list(CUTOUT_FX) + _VISIBLE_POOL + _SAFE_FALLBACKS))
    return None


def build_effect_clip(img_path, audio_path, out_path, fx_name, duration=None, img2=None):
    """Gera clip 720x1280 do painel com o efeito `fx_name` + áudio do painel. True/False.
    img2 = próximo painel (só usado por efeitos de transição do Grupo C/F)."""
    # duração vem do áudio (não regera; casa com a narração)
    if duration is None:
        try:
            fp = shutil.which("ffprobe") or _ff().replace("ffmpeg", "ffprobe")
            r = subprocess.run([fp, "-v", "quiet", "-show_entries", "format=duration",
                                "-of", "csv=p=0", str(audio_path)], capture_output=True, text=True, timeout=10)
            duration = float(r.stdout.strip())
        except Exception:
            duration = 3.0
    duration = max(duration, 1.0)
    # AVANÇADOS (depth/atmosfera/multi-personagem): geram depth/recorte/overlay/.cmd
    if fx_name in ADVFX:
        return build_advfx(img_path, out_path, fx_name, duration, img2=img2, audio_path=audio_path)
    # TRANSIÇÃO/MULTI (Grupo C/F): precisa do PRÓXIMO painel (img2); sem ele → fallback
    if fx_name in FX2:
        return build_fx2(img_path, img2, audio_path, out_path, fx_name, duration)
    # SENDCMD (gblur/lenscorrection/perspective animados via arquivo .cmd)
    if fx_name in SENDCMD_FX:
        return build_sendcmd_fx(img_path, audio_path, out_path, fx_name, duration)
    # RECORTE DE PERSONAGEM (Grupo D): efeito 2-input (painel + recorte rembg). Se o
    # painel não tem personagem recortável, build_cutout_clip retorna False → cai no fallback.
    if fx_name in CUTOUT_FX:
        return build_cutout_clip(img_path, audio_path, out_path, fx_name, duration)
    tpl = PANEL_FX.get(fx_name)
    if not tpl:
        return False
    fr = int(duration * FPS)
    vf = tpl.format(W=W, H=H, FPS=FPS, FR=fr, DUR=duration)
    # Simples e multi-label ambos começam em [0:v] e fecho com [v] (os multi já têm ; internos).
    fc = f"[0:v]{vf}[v]"
    cmd = [_ff(), "-y", "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
           "-i", str(audio_path),
           "-filter_complex", fc,
           "-map", "[v]", "-map", "1:a",
           "-t", f"{duration:.2f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
           str(out_path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return r.returncode == 0 and Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    except Exception:
        return False


# ─── RECORTE DE PERSONAGEM (Grupo D, rembg) — efeitos 2-input FIRST-CLASS ───────
# Fundo desfocado que cobre o frame + zoom lento; personagem recortado animado por
# cima (desliza/flutua/entra). É o "corta o personagem e ele se mexe" da usuária.
CUTOUT_FX = {
    # nome:        (scale_frac, x_expr, y_expr, blur, bg_zoom)
    "parallaxcut": (0.80, "(main_w-overlay_w)/2 + 55*sin(1.5*t)", "(main_h-overlay_h)/2 + 22*sin(0.9*t)", 18, 0.0012),
    "charfloat":   (0.80, "(main_w-overlay_w)/2",                 "(main_h-overlay_h)/2 + 28*sin(1.2*t)", 18, 0.0008),
    "charslidein": (0.82, "-overlay_w + ((main_w-overlay_w)/2 + overlay_w)*min(1,t/0.7)", "(main_h-overlay_h)/2", 20, 0.0010),
    "bgblurfocus": (0.86, "(main_w-overlay_w)/2",                 "(main_h-overlay_h)/2", 30, 0.0009),
    "charsway":    (0.80, "(main_w-overlay_w)/2 + 40*sin(1.1*t)", "(main_h-overlay_h)/2 + 12*sin(2.2*t)", 20, 0.0011),
}

_REMBG_CACHE = Path(__file__).resolve().parent.parent / "workspace" / "rembg_cache"
_rembg_session = None


def _rembg_cached(img_path):
    """Recorta o personagem (rembg) → PNG alpha, cacheado por md5 (rembg é ~3.8s).
    Retorna o caminho SÓ se o recorte parece um PERSONAGEM (10-80% da imagem) — assim
    NÃO aplica cutout em painel só-balão nem full-bleed. None caso contrário."""
    global _rembg_session
    try:
        import hashlib
        md5 = hashlib.md5(Path(img_path).read_bytes()).hexdigest()
    except Exception:
        return None
    _REMBG_CACHE.mkdir(parents=True, exist_ok=True)
    out = _REMBG_CACHE / f"{md5}.png"
    nochar = _REMBG_CACHE / f"{md5}.nochar"   # marcador: já tentei, não vale a pena
    if nochar.exists():
        return None
    if out.exists() and out.stat().st_size > 500:
        return out
    try:
        from rembg import remove, new_session
        from PIL import Image
        import numpy as np
        if _rembg_session is None:
            _rembg_session = new_session("u2net")
        im = Image.open(img_path).convert("RGBA")
        cut = remove(im, session=_rembg_session)
        frac = float((np.asarray(cut)[:, :, 3] > 40).mean())
        if not (0.10 < frac < 0.80):   # balão minúsculo ou imagem toda → não é personagem
            nochar.write_text("1")
            return None
        cut.save(out)
        return out if out.exists() else None
    except Exception:
        return None


def build_cutout_clip(img_path, audio_path, out_path, fx_name, duration):
    """Efeito de RECORTE: fundo desfocado + personagem recortado animado por cima."""
    spec = CUTOUT_FX.get(fx_name)
    if not spec:
        return False
    char = _rembg_cached(img_path)
    if not char:
        return False   # sem personagem recortável → o caller cai no fallback (Ken Burns)
    fr = int(max(duration, 1.0) * FPS)
    if isinstance(spec, str):
        # template CRU 2-input (do COMANDOS_PROTOTIPOS.sh): [0:v]=painel, [1:v]=recorte, saída [v]
        fc = spec.format(W=W, H=H, FPS=FPS, FR=fr, DUR=duration)
    else:
        sc, xexpr, yexpr, blur, bgzoom = spec
        fc = (
            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur={blur}:2,eq=brightness=-0.12:saturation=0.88,"
            f"zoompan=z='min(zoom+{bgzoom},1.14)':d={fr}:s={W}x{H}:fps={FPS},setsar=1[bg];"
            f"[1:v]scale={int(W*sc)}:-1,setsar=1[ch];"
            f"[bg][ch]overlay=x='{xexpr}':y='{yexpr}':eval=frame,format=yuv420p[v]"
        )
    cmd = [_ff(), "-y",
           "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
           "-loop", "1", "-t", f"{duration:.2f}", "-i", str(char),
           "-i", str(audio_path),
           "-filter_complex", fc,
           "-map", "[v]", "-map", "2:a", "-t", f"{duration:.2f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
           str(out_path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return r.returncode == 0 and Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    except Exception:
        return False


# ─── SENDCMD (Grupo A/L/P/J/O): filtro animado via arquivo .cmd (gblur/lens/perspective) ───
# name: (conteúdo do .cmd, template de filtro c/ {CMD} = caminho do .cmd escapado)
SENDCMD_FX = {
    "rackfocus":        ("0.0 gblur sigma 0;\n0.5 gblur sigma 2;\n0.7 gblur sigma 6;\n0.9 gblur sigma 12;\n1.3 gblur sigma 6;\n1.6 gblur sigma 0;\n",
                         "scale={W}:{H},setsar=1,sendcmd=filename={CMD},gblur=sigma=0"),
    "bulge":            ("0.0 lenscorrection k1 0;\n1.2 lenscorrection k1 0.3;\n2.4 lenscorrection k1 0;\n",
                         "scale={W}:{H},setsar=1,fps={FPS},sendcmd=filename={CMD},lenscorrection=cx=0.5:cy=0.4:k1=0:k2=0"),
    "graindissolve":    ("0.0 noise alls 80;\n1.5 noise alls 0;\n",
                         "scale={W}:{H},setsar=1,fps={FPS},sendcmd=filename={CMD},noise=alls=80:allf=t,fade=t=in:st=0:d=0.8"),
    "pixeldissolve":    ("0.0 gblur sigma 9;\n1.5 gblur sigma 0;\n",
                         "scale=120:213,setsar=1,fps={FPS},scale={W}:{H}:flags=neighbor,sendcmd=filename={CMD},gblur=sigma=9"),
    "pixelresolve":     ("0.0 gblur sigma 20;\n1.5 gblur sigma 0;\n",
                         "scale={W}:{H},setsar=1,sendcmd=filename={CMD},gblur=sigma=20"),
    "perspectiveswing": ("0.0 perspective x0 0;\n1.2 perspective x0 160;\n2.4 perspective x0 0;\n",
                         "scale={W}:{H},setsar=1,fps={FPS},sendcmd=filename={CMD},perspective=x0=0:y0=0:x1={W}:y1=0:x2=0:y2={H}:x3={W}:y3={H}"),
}


def build_sendcmd_fx(img_path, audio_path, out_path, fx_name, duration):
    """Efeito com filtro animado por arquivo .cmd (sendcmd). Escreve o .cmd temporário,
    roda o ffmpeg e apaga. O caminho do .cmd é escapado p/ o filtergraph (o ':' do Windows)."""
    spec = SENDCMD_FX.get(fx_name)
    if not spec:
        return False
    cmd_content, ftpl = spec
    fr = int(max(duration, 1.0) * FPS)
    cmdfile = Path(out_path).with_suffix(".cmd")
    try:
        cmdfile.write_text(cmd_content, encoding="utf-8")
        cmd_esc = str(cmdfile).replace("\\", "/").replace(":", "\\:")  # escapa p/ o filtergraph
        vf = ftpl.format(W=W, H=H, FPS=FPS, FR=fr, CMD=cmd_esc)
        fc = f"[0:v]{vf}[v]"
        cmd = [_ff(), "-y", "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
               "-i", str(audio_path), "-filter_complex", fc,
               "-map", "[v]", "-map", "1:a", "-t", f"{duration:.2f}",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
               "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
               str(out_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return r.returncode == 0 and Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    except Exception:
        return False
    finally:
        try:
            cmdfile.unlink(missing_ok=True)
        except Exception:
            pass


# ─── TRANSIÇÕES / MULTI-PAINEL (Grupo C/F): 2-input com o PRÓXIMO painel (IMG2) ──
FX2 = {}  # merge do ext no fim


def build_fx2(img_path, img2_path, audio_path, out_path, fx_name, duration):
    """Efeito 2-input com o PRÓXIMO painel (transição IMG->IMG2). [0:v]=atual, [1:v]=próximo.
    Sem img2 → False (o caller cai no fallback)."""
    spec = FX2.get(fx_name)
    if not spec or not img2_path:
        return False
    fr = int(max(duration, 1.0) * FPS)
    fc = spec.format(W=W, H=H, FPS=FPS, FR=fr, DUR=duration)
    cmd = [_ff(), "-y",
           "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img_path),
           "-loop", "1", "-t", f"{duration:.2f}", "-i", str(img2_path),
           "-i", str(audio_path),
           "-filter_complex", fc,
           "-map", "[v]", "-map", "2:a", "-t", f"{duration:.2f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
           str(out_path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        return r.returncode == 0 and Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    except Exception:
        return False


# ─── AVANÇADOS (Grupo D-depth/I-atmosfera/Dp-multichar): inputs gerados ─────────
ADVFX = {}  # {nome: {"tpl":..., "inputs":[IMG/IMG2/CUT/CUT2/FAR/MID/NEAR/EL:x.mov], "cmd":...}}
_EL_DIR = Path(__file__).resolve().parent.parent / "workspace" / "assets" / "overlays" / "elemental"
_DEPTH_LAYER_CACHE = Path(__file__).resolve().parent.parent / "workspace" / "depth_layers_cache"


def _depth_layers(img_path):
    """3 camadas (far/mid/near) PNG alpha por profundidade, cacheadas por md5.
    Reusa parallax_engine.get_depth. Retorna (far, mid, near) paths ou None."""
    try:
        import hashlib
        md5 = hashlib.md5(Path(img_path).read_bytes()).hexdigest()
    except Exception:
        return None
    _DEPTH_LAYER_CACHE.mkdir(parents=True, exist_ok=True)
    outs = [_DEPTH_LAYER_CACHE / f"{md5}_{n}.png" for n in ("far", "mid", "near")]
    if all(p.exists() and p.stat().st_size > 500 for p in outs):
        return tuple(outs)
    try:
        import parallax_engine as _pe
        from PIL import Image, ImageFilter
        import numpy as np
        depth = _pe.get_depth(img_path, (W, H))
        try:
            img = _pe._fit(img_path, W, H).convert("RGBA")
        except Exception:
            img = Image.open(img_path).convert("RGB").resize((W, H)).convert("RGBA")
        d = np.asarray(depth, dtype=np.float32) / 255.0
        for (name_lo_hi, outp) in zip([(0.0, 0.4), (0.4, 0.7), (0.7, 1.01)], outs):
            lo, hi = name_lo_hi
            mask = ((d >= lo) & (d < hi)).astype(np.uint8) * 255
            m = Image.fromarray(mask).filter(ImageFilter.GaussianBlur(6))
            rgba = img.copy()
            rgba.putalpha(m)
            rgba.save(outp)
        return tuple(outs)
    except Exception:
        return None


def _resolve_adv_input(spec, img_path, img2_path):
    """Resolve um spec de input → (kind, path). kind='still'|'video'. None se indisponível."""
    if spec == "IMG":
        return ("still", img_path)
    if spec == "IMG2":
        return ("still", img2_path) if img2_path else None
    if spec in ("CUT", "CUT2"):
        c = _rembg_cached(img_path)
        return ("still", c) if c else None
    if spec in ("FAR", "MID", "NEAR"):
        layers = _depth_layers(img_path)
        if not layers:
            return None
        return ("still", layers[{"FAR": 0, "MID": 1, "NEAR": 2}[spec]])
    if spec.startswith("EL:"):
        p = _EL_DIR / spec[3:]
        return ("video", p) if p.exists() else None
    return None


def build_advfx(img_path, out_path, fx_name, duration, img2=None, audio_path=None):
    """Efeitos avançados (depth/atmosfera/multi-personagem). Gera os inputs necessários
    (camadas de depth, recorte rembg, overlays .mov, .cmd) e monta o ffmpeg. False se
    algum input não puder ser gerado (ex.: painel sem personagem) → caller cai no fallback."""
    spec = ADVFX.get(fx_name)
    if not spec:
        return False
    fr = int(max(duration, 1.0) * FPS)
    resolved = []
    for s in spec["inputs"]:
        r = _resolve_adv_input(s, img_path, img2)
        if not r:
            return False
        resolved.append(r)
    cmdfile = None
    cmd_esc = ""
    if spec.get("cmd"):
        cmdfile = Path(out_path).with_suffix(".cmd")
        try:
            cmdfile.write_text(spec["cmd"], encoding="utf-8")
        except Exception:
            return False
        cmd_esc = str(cmdfile).replace("\\", "/").replace(":", "\\:")
    try:
        fc = spec["tpl"].format(W=W, H=H, FPS=FPS, FR=fr, DUR=duration, CMD=cmd_esc)
        cmd = [_ff(), "-y"]
        for kind, path in resolved:
            if kind == "video":
                cmd += ["-stream_loop", "-1", "-i", str(path)]
            else:
                cmd += ["-loop", "1", "-t", f"{duration:.2f}", "-i", str(path)]
        aidx = len(resolved)  # áudio é o último input
        cmd += ["-i", str(audio_path),
                "-filter_complex", fc,
                "-map", "[v]", "-map", f"{aidx}:a", "-t", f"{duration:.2f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "-pix_fmt", "yuv420p",
                str(out_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=200)
        return r.returncode == 0 and Path(out_path).exists() and Path(out_path).stat().st_size > 1000
    except Exception:
        return False
    finally:
        if cmdfile:
            try:
                cmdfile.unlink(missing_ok=True)
            except Exception:
                pass


# ─── Merge do LOTE EXTRA (arquivo separado p/ evitar conflito de edição) ────────
try:
    from panel_effects_ext import EXTRA_FX, EXTRA_CUTOUT, EXTRA_FX2, EXTRA_ADVFX
    PANEL_FX.update(EXTRA_FX)
    CUTOUT_FX.update(EXTRA_CUTOUT)
    FX2.update(EXTRA_FX2)
    ADVFX.update(EXTRA_ADVFX)
except Exception:
    pass
