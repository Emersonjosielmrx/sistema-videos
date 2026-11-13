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
]

# Efeitos suaves pra fallback probabilístico (não atrapalham, dão vida ao painel)
_SAFE_FALLBACKS = ["breathing", "handheld", "dollypush", "pulsezoom", "panLR", "facezoom"]
_FALLBACK_CHANCE = 0.35  # 35% dos painéis sem keyword ganham efeito suave

_last_fx = None


def pick_effect(text, is_sensual=False, is_texto_plano=False, tem_balao=False, img_path=None):
    """Retorna o efeito de painel pela narração, ou None. FILOSOFIA: na dúvida, None
    (efeito errado no painel errado fica horrível; melhor não aplicar).

    SALVAGUARDAS (regras da usuária — nunca violar):
      is_sensual=True   → None (painel +18 vai ser censurado, não gastar efeito)
      is_texto_plano=True → None (painel só texto/onomatopeia não ganha com movimento)
      tem_balao=True + efeito de transição → None (transição atrapalha leitura do balão)
    Anti-repetição consecutiva embutida.

    img_path: se dado e há decisão PRÉ-COMPUTADA do motion_director (por visão, cache md5),
    ela tem PRIORIDADE sobre o keyword (decisão de mais qualidade, feita adiantada)."""
    global _last_fx
    if is_sensual or is_texto_plano:
        return None
    # motion_director: decisão por visão pré-computada (se existe no cache p/ este painel)
    if img_path is not None:
        try:
            import motion_director as _md
            _dec = _md.decidir_efeito(img_path, text, is_sensual=is_sensual, use_ia=False)
            _fx = _dec.get("efeito") if _dec else None
            if _fx and _fx in PANEL_FX and _fx != _last_fx:
                _last_fx = _fx
                return _fx
        except Exception:
            pass
    t = (text or "").lower()
    if not t.strip():
        return None
    for fx, kws in FX_KEYWORDS:
        if any(k in t for k in kws):
            if fx == _last_fx:
                continue  # evita repetir consecutivo
            _last_fx = fx
            return fx
    # fallback: efeito suave aleatório (~35% dos painéis sem keyword, pra dar vida)
    if not tem_balao and _rnd.random() < _FALLBACK_CHANCE:
        candidates = [f for f in _SAFE_FALLBACKS if f != _last_fx]
        if candidates:
            fx = _rnd.choice(candidates)
            _last_fx = fx
            return fx
    return None


def build_effect_clip(img_path, audio_path, out_path, fx_name, duration=None):
    """Gera clip 720x1280 do painel com o efeito `fx_name` + áudio do painel. True/False."""
    tpl = PANEL_FX.get(fx_name)
    if not tpl:
        return False
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
