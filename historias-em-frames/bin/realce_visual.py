# COMUM — fonte única: D:\hipercool-materiais\comum\realce_visual.py. Mudou esta cópia? python D:\hipercool-materiais\bin\recursos.py subir realce_visual.py --de <projeto>
"""realce_visual.py — recursos visuais vindos do GitHub (testados pela dona em 02/11/2026).

  parallax(img, saida, dur, w, h)            2.5D por profundidade com o DepthFlow (shader OpenGL)
  transicao_inicio(clip, anterior)           transição gl-transitions do último quadro do clip anterior
                                             para o começo deste (só o vídeo; áudio e duração intactos)
  igualar_cor(clip, referencia)              puxa a cor do começo do clip para a do quadro de referência
                                             (Reinhard em LAB, o mesmo método do color-matcher), soltando aos poucos
  ampliar(img, saida, escala=2)              Real-CUGAN (ncnn-vulkan) para painel/capa/imagem pequena
  morph(q0, q1, saida_dir, n=6)              RIFE (ncnn-vulkan): quadros intermediários entre dois quadros

Tudo devolve False/None quando falta a biblioteca, a ferramenta ou a GPU: quem chama segue no caminho antigo.
Cada recurso desliga por env: REALCE_PARALLAX=0, REALCE_TRANSICAO=0, REALCE_COR=0, REALCE_AMPLIAR=0, REALCE_MORPH=0.
Ferramentas em D:\\hipercool-materiais\\tools (rife-ncnn-vulkan, realcugan-ncnn-vulkan, gl-transitions).
Cuidados medidos: o rife no Windows pt-BR lê o passo com vírgula; o DepthFlow não fecha o processo sozinho
(roda num subprocesso que termina com os._exit).
"""
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def _achar_tools():
    """REALCE_TOOLS > D:\\hipercool-materiais\\tools > <projeto>\\tools (PC2: C:\\recapd-e-animes\\tools, sem mexer no
    ambiente do daemon). Fica a primeira que tem os shaders."""
    cands = [os.environ.get("REALCE_TOOLS"), r"D:\hipercool-materiais\tools", Path(__file__).resolve().parent.parent / "tools"]
    for c in cands:
        if c and (Path(c) / "gl-transitions").is_dir():
            return Path(c)
    return Path(r"D:\hipercool-materiais\tools")


TOOLS = _achar_tools()
SHADERS = TOOLS / "gl-transitions"
RIFE = TOOLS / "rife-ncnn-vulkan"
CUGAN = TOOLS / "realcugan-ncnn-vulkan"
_SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
# shaders que combinam com manhwa/anime/Shorts (os 7 aprovados no teste 04)
TRANSICOES = ("CrossZoom", "Dreamy", "GlitchDisplace", "GlitchMemories", "InvertedPageCurl", "WaterDrop", "ZoomInCircles")


def ligado(nome):
    return os.environ.get(f"REALCE_{nome.upper()}", "1") != "0"


def disponivel(nome):
    """Ligado E com o que precisa nesta máquina (lib/ferramenta). Quem troca um efeito antigo pelo novo pergunta
    isto antes, pra não ficar sem nenhum dos dois numa máquina que não tem a lib."""
    import importlib.util
    if not ligado(nome):
        return False
    precisa = {"transicao": ("moderngl", SHADERS), "parallax": ("depthflow", None), "cor": ("cv2", None),
               "ampliar": (None, CUGAN / "realcugan-ncnn-vulkan.exe"), "morph": (None, RIFE / "rife-ncnn-vulkan.exe")}
    lib, arq = precisa.get(nome, (None, None))
    ok = (lib is None or importlib.util.find_spec(lib) is not None) and (arq is None or Path(arq).exists())
    return ok and (nome != "transicao" or _gl_abre())


_gl_ok = None


def _gl_abre():
    """O OpenGL abre MESMO nesta sessão? (processo de serviço/sessão 0 pode ter a lib e não ter a placa). 1 teste só."""
    global _ctx, _gl_ok
    if _gl_ok is None:
        try:
            import moderngl
            try:
                _ctx = _ctx or moderngl.create_standalone_context()
            except Exception:  # noqa: BLE001 — 02/11: Linux sem tela (Kaggle T4) só abre por EGL; antes desligava aqui
                _ctx = moderngl.create_standalone_context(backend="egl")
            _gl_ok = True
        except Exception as e:  # noqa: BLE001
            _log(f"OpenGL não abre aqui ({str(e)[:100]}): transições gl desligadas")
            _gl_ok = False
    return _gl_ok


def _ffmpeg():
    return shutil.which("ffmpeg") or r"D:\hipercool-materiais\bin\ffmpeg.exe"


def _ffprobe():
    return shutil.which("ffprobe") or r"D:\hipercool-materiais\bin\ffprobe.exe"


def _log(m):
    print(f"[realce] {m}", file=sys.stderr, flush=True)


def _info(video):
    """(w, h, fps, duração) do vídeo."""
    r = subprocess.run([_ffprobe(), "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(video)],
                       capture_output=True, text=True, creationflags=_SEM_JANELA, timeout=60)
    j = json.loads(r.stdout or "{}")
    s = (j.get("streams") or [{}])[0]
    num, _, den = str(s.get("r_frame_rate", "30/1")).partition("/")
    fps = float(num) / float(den or 1)
    return int(s["width"]), int(s["height"]), fps, float(j.get("format", {}).get("duration", 0))


def _tem_audio(video):
    r = subprocess.run([_ffprobe(), "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True, creationflags=_SEM_JANELA)
    return bool(r.stdout.strip())


def _ultimo_quadro(video, w, h):
    import numpy as np
    r = subprocess.run([_ffmpeg(), "-v", "error", "-sseof", "-0.5", "-i", str(video), "-vf", f"scale={w}:{h}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, creationflags=_SEM_JANELA,
                       timeout=120)
    n = w * h * 3
    if len(r.stdout) < n:
        return None
    return np.frombuffer(r.stdout[-n:], dtype=np.uint8).reshape(h, w, 3)


def _reescrever(clip, w, h, fps, trocar, crf=20):
    """Lê o clip quadro a quadro (RGB) e regrava passando cada quadro por trocar(i, quadro) -> quadro.
    Áudio copiado sem mexer e mesma quantidade de quadros: a duração não muda. Grava por cima só no fim."""
    import numpy as np
    clip = Path(clip)
    tmp = clip.with_name(clip.stem + "_realce.mp4")
    ler = subprocess.Popen([_ffmpeg(), "-v", "error", "-i", str(clip), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE, creationflags=_SEM_JANELA)
    audio = ["-i", str(clip), "-map", "0:v", "-map", "1:a", "-c:a", "copy"] if _tem_audio(clip) else ["-map", "0:v"]
    gravar = subprocess.Popen([_ffmpeg(), "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                               "-r", f"{fps:.5f}", "-i", "-", *audio, "-c:v", "libx264", "-preset", "fast",
                               "-crf", str(crf), "-g", "30", "-pix_fmt", "yuv420p", str(tmp)],
                              stdin=subprocess.PIPE, creationflags=_SEM_JANELA)
    n = w * h * 3
    i = 0
    try:
        while True:
            buf = ler.stdout.read(n)
            if len(buf) < n:
                break
            q = np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 3)
            gravar.stdin.write(np.ascontiguousarray(trocar(i, q)).tobytes())
            i += 1
    finally:
        ler.stdout.close()
        ler.wait()
        gravar.stdin.close()
        gravar.wait()
    if gravar.returncode != 0 or i == 0 or not tmp.exists():
        tmp.unlink(missing_ok=True)
        return False
    os.replace(tmp, clip)
    return True


# ── transições gl-transitions ───────────────────────────────────────────────

_VERT = """#version 330
in vec2 pos; out vec2 uv;
void main(){ uv = pos*0.5+0.5; gl_Position = vec4(pos,0.0,1.0); }"""
_FRAG = """#version 330
uniform sampler2D from_tex; uniform sampler2D to_tex;
uniform float progress; uniform float ratio;
in vec2 uv; out vec4 cor;
vec4 getFromColor(vec2 p){ return texture(from_tex, p); }
vec4 getToColor(vec2 p){ return texture(to_tex, p); }
%s
void main(){ cor = transition(uv); }"""
_ctx = None


def _padroes(codigo):
    """Valores padrão no formato do gl-transitions: 'uniform float x; // = 0.4'."""
    import re
    vals = {}
    for tipo, nome, v in re.findall(r"uniform\s+(\w+)\s+(\w+)\s*;\s*//\s*=\s*([^\n]+)", codigo):
        v = v.strip().rstrip(";")
        nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", v)]
        if tipo in ("float", "int") and nums:
            vals[nome] = nums[0]
        elif tipo == "bool":
            vals[nome] = v.startswith("true")
        elif nums:
            vals[nome] = tuple(nums)
    return vals


def transicao_inicio(clip, anterior, nome=None, dur=0.4, semente=None):
    """Troca os primeiros `dur` s do clip por uma transição do último quadro de `anterior` para o clip.
    Mesma duração e áudio intacto (o clip só é regravado). True se aplicou."""
    global _ctx
    if not ligado("transicao") or not anterior or not Path(anterior).exists():
        return False
    try:
        import moderngl
        import numpy as np
        nome = nome or random.Random(semente).choice(TRANSICOES)
        codigo = (SHADERS / f"{nome}.glsl").read_text(encoding="utf-8")
        w, h, fps, _ = _info(clip)
        de = _ultimo_quadro(anterior, w, h)
        if de is None:
            return False
        if _ctx is None:
            try:
                _ctx = moderngl.create_standalone_context()
            except Exception:  # noqa: BLE001 — Linux sem tela (Kaggle): contexto pelo EGL
                if os.name == "nt":
                    raise
                _ctx = moderngl.create_standalone_context(backend="egl")
        ctx = _ctx
        fbo = ctx.simple_framebuffer((w, h))
        prog = ctx.program(vertex_shader=_VERT, fragment_shader=_FRAG % codigo)
        vbo = ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype="f4").tobytes())
        vao = ctx.vertex_array(prog, [(vbo, "2f", "pos")])
        for k, v in _padroes(codigo).items():
            if k in prog:
                prog[k].value = v
        prog["from_tex"].value = 0
        prog["to_tex"].value = 1
        if "ratio" in prog:
            prog["ratio"].value = w / h
        t_de = ctx.texture((w, h), 3, np.ascontiguousarray(de[::-1]).tobytes())
        t_para = ctx.texture((w, h), 3)
        n = max(2, int(round(dur * fps)))

        def trocar(i, q):
            if i >= n:
                return q
            p = i / (n - 1)
            p = p * p * (3 - 2 * p)
            t_para.write(np.ascontiguousarray(q[::-1]).tobytes())
            t_de.use(0)
            t_para.use(1)
            if "progress" in prog:
                prog["progress"].value = p
            fbo.use()
            fbo.clear()
            vao.render(moderngl.TRIANGLE_STRIP)
            return np.frombuffer(fbo.read(components=3), dtype=np.uint8).reshape(h, w, 3)[::-1]

        try:
            return _reescrever(clip, w, h, fps, trocar)
        finally:
            for o in (vao, vbo, prog, t_de, t_para, fbo):
                o.release()
    except Exception as e:  # noqa: BLE001
        _log(f"transição falhou ({str(e)[:160]}): segue sem")
        return False


# ── cor igual entre clipes (emenda) ─────────────────────────────────────────

def igualar_cor(clip, referencia, seg=1.5):
    """Puxa a cor do começo de `clip` para a do último quadro de `referencia` (vídeo) ou da imagem `referencia`;
    o peso cai de 1 a 0 em `seg` segundos (a cor volta à do próprio clip sem 'piscar'). True se aplicou."""
    if not ligado("cor"):
        return False
    try:
        import cv2
        import numpy as np
        w, h, fps, _ = _info(clip)
        ref = Path(referencia)
        if ref.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            r = cv2.cvtColor(cv2.resize(cv2.imread(str(ref)), (w, h)), cv2.COLOR_BGR2RGB)
        else:
            r = _ultimo_quadro(ref, w, h)
        if r is None:
            return False
        lab_r = cv2.cvtColor(r, cv2.COLOR_RGB2LAB).astype(np.float32)
        mu_r, sd_r = lab_r.reshape(-1, 3).mean(0), lab_r.reshape(-1, 3).std(0) + 1e-3
        n = max(2, int(round(seg * fps)))
        est = {}

        def trocar(i, q):
            if i >= n:
                return q
            lab = cv2.cvtColor(q, cv2.COLOR_RGB2LAB).astype(np.float32)
            if "mu" not in est:  # estatística do 1º quadro do clip: a mesma conta em todos (sem tremer)
                est["mu"], est["sd"] = lab.reshape(-1, 3).mean(0), lab.reshape(-1, 3).std(0) + 1e-3
            casado = (lab - est["mu"]) / est["sd"] * sd_r + mu_r
            peso = 1.0 - i / (n - 1)
            mist = np.clip(peso * casado + (1 - peso) * lab, 0, 255).astype(np.uint8)
            return cv2.cvtColor(mist, cv2.COLOR_LAB2RGB)

        return _reescrever(clip, w, h, fps, trocar)
    except Exception as e:  # noqa: BLE001
        _log(f"cor falhou ({str(e)[:160]}): segue sem")
        return False


# ── parallax DepthFlow ──────────────────────────────────────────────────────

MOVIMENTOS = ("aproximar", "lateral", "orbital", "dolly")


def parallax(img, saida, dur, w, h, fps=30, profundidade=None, movimento=None, semente=0, parados=(),
             intensidade=1.0, timeout=None):
    """Clip 2.5D do DepthFlow a partir de uma imagem. profundidade: array 0..1 do tamanho da imagem (None = o
    DepthFlow estima). parados: caixas (x, y, w, h) em px da imagem que não podem mexer (balões/texto).
    True se o vídeo saiu com a duração pedida."""
    if not ligado("parallax"):
        return False
    try:
        import importlib.util
        if importlib.util.find_spec("depthflow") is None:
            return False
        import cv2
        import numpy as np
        tmpd = Path(tempfile.mkdtemp(prefix="realce_df_"))
        try:
            dep = None
            if profundidade is not None:
                d = np.clip(np.asarray(profundidade, dtype=np.float32), 0, 1)
                steady = 0.30
                if parados:
                    livre = np.ones_like(d)
                    for x, y, bw, bh in parados:
                        livre[max(0, int(y) - 12):int(y + bh) + 12, max(0, int(x) - 12):int(x + bw) + 12] = 0
                    livre = cv2.GaussianBlur(livre, (0, 0), 10)
                    d = d * livre + steady * (1 - livre)  # no plano 'steady' o DepthFlow não desloca
                dep = tmpd / "depth.png"
                cv2.imwrite(str(dep), (d * 255).astype(np.uint8))
            mov = movimento or random.Random(semente).choice(MOVIMENTOS)
            args = {"img": str(img), "depth": str(dep) if dep else None, "saida": str(saida), "dur": float(dur),
                    "w": int(w), "h": int(h), "fps": float(fps), "mov": mov, "sinal": random.Random(semente).choice([-1, 1]),
                    "k": float(intensidade)}
            env = dict(os.environ)
            env["PATH"] = str(Path(_ffmpeg()).parent) + os.pathsep + env.get("PATH", "")
            env["PYTHONUTF8"] = "1"
            try:
                subprocess.run([sys.executable, str(Path(__file__).resolve()), "_depthflow", json.dumps(args)],
                               capture_output=True, timeout=timeout or max(120, dur * 40), env=env,
                               creationflags=_SEM_JANELA)
            except subprocess.TimeoutExpired:
                pass  # o arquivo pode ter saído mesmo assim; a conferência abaixo decide
            if not Path(saida).exists():
                return False
            ok = abs(_info(saida)[3] - dur) < 0.25
            if not ok:
                Path(saida).unlink(missing_ok=True)
            return ok
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
    except Exception as e:  # noqa: BLE001
        _log(f"parallax falhou ({str(e)[:160]}): segue sem")
        return False


def _depthflow_filho(a):
    """Roda dentro do subprocesso: renderiza e sai com os._exit (o DepthFlow deixa thread viva)."""
    from attrs import define
    from depthflow.scene import DepthScene

    @define
    class Cena(DepthScene):
        def update(self):
            s = self.state
            t = min(1.0, max(0.0, self.time / max(1e-3, a["dur"])))
            e = t * t * (3 - 2 * t)
            k, sinal = a["k"], a["sinal"]
            s.steady = 0.30
            # amplitudes medidas no painel de teste: menos que isso a câmera parece parada
            if a["mov"] == "aproximar":
                s.isometric = 0.5
                s.height = k * (0.15 + 0.45 * e)
                s.offset = (0.0, -0.15 * k * e)
            elif a["mov"] == "lateral":
                s.isometric = 0.6
                s.height = 0.20 * k
                s.offset = (sinal * k * 0.70 * (e - 0.5), 0.0)
            elif a["mov"] == "orbital":
                s.focus = 0.30
                s.zoom = 0.97
                s.height = 0.15 * k
                s.isometric = 0.45 + 0.30 * math.cos(math.pi * e)
                s.offset = (sinal * k * 0.60 * math.sin(math.pi * (e - 0.5)), 0.0)
            else:  # dolly
                s.height = 0.35 * k
                s.focus = 0.35
                s.zoom = 0.95
                s.isometric = 0.7 * e

    cena = Cena(backend="headless")
    cena.ffmpeg.h264(preset="veryfast")
    cena.input(image=a["img"], depth=a["depth"])
    cena.main(output=a["saida"], width=a["w"], height=a["h"], fps=a["fps"], time=a["dur"], ssaa=1.25, quality=70)
    os._exit(0)


# ── Real-CUGAN e RIFE (ncnn-vulkan) ─────────────────────────────────────────

def ampliar(img, saida, escala=2, ruido=1, timeout=600):
    """Real-CUGAN: amplia imagem de anime/manhwa. ~67 s por 720x1280 na Intel UHD 620. True se saiu."""
    exe = CUGAN / "realcugan-ncnn-vulkan.exe"
    if not ligado("ampliar") or not exe.exists():
        return False
    try:
        subprocess.run([str(exe), "-i", str(img), "-o", str(saida), "-s", str(escala), "-n", str(ruido)],
                       cwd=CUGAN, capture_output=True, timeout=timeout, creationflags=_SEM_JANELA, check=True)
        return Path(saida).exists()
    except Exception as e:  # noqa: BLE001
        _log(f"ampliar falhou ({str(e)[:160]}): segue sem")
        return False


def morph(q0, q1, saida_dir, n=6, timeout=1200):
    """RIFE v4.6: n quadros entre as imagens q0 e q1 (lista de caminhos, em ordem). ~60 s por quadro
    1080x1920 na Intel UHD 620: usar em GPU ou em emendas curtas. [] se não deu."""
    exe = RIFE / "rife-ncnn-vulkan.exe"
    if not ligado("morph") or not exe.exists():
        return []
    saida_dir = Path(saida_dir)
    saida_dir.mkdir(parents=True, exist_ok=True)
    feitos = []
    try:
        for k in range(1, n + 1):
            out = saida_dir / f"morph_{k:02d}.png"
            # o exe lê o número com o locale do Windows (pt-BR = vírgula)
            passo = f"{k / (n + 1):.4f}".replace(".", ",")
            subprocess.run([str(exe), "-0", str(q0), "-1", str(q1), "-o", str(out), "-m", str(RIFE / "rife-v4.6"),
                            "-s", passo], cwd=RIFE, capture_output=True, timeout=timeout / n,
                           creationflags=_SEM_JANELA, check=True)
            feitos.append(out)
        return feitos
    except Exception as e:  # noqa: BLE001
        _log(f"morph falhou ({str(e)[:160]}): segue sem")
        return []


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "_depthflow":
        _depthflow_filho(json.loads(sys.argv[2]))
    else:
        print(__doc__)
