"""EDITOR Gemini em Remotion para o vídeo de produto (26/10; cópia adaptada do modo editor + lapidar do
D:\\claude-code-video — lá o Cardápio foi de 5,62 a 7,62 com editor + corretor).

Depois que o video.py monta a versão Python (o molde) e os verificadores dão nota, este módulo entrega o MESMO
material (voz pronta no tempo certo, cena do dono no Veo, instalações reais, imagens, conversa, cores) ao editor
Gemini, que escreve a edição em Remotion (remotion\\src\\videos\\<id>) e olha os quadros; os 4 verificadores dão nota
e o corretor conserta até `rodadas`. Fica a versão de MAIOR nota entre a do editor e a do molde.
Config: config\\produto_lapidar.json -> "editor".
"""
import json
import re
import shutil
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from produto import lapidar, motor

RAIZ = Path(__file__).resolve().parents[2]
REMOTION = RAIZ / "remotion"
GUARDADOS = Path(r"D:\video-fila\produto_tmp\editor_guardados")
FF = r"D:\hipercool-materiais\bin\ffmpeg.exe"
_feitos = []  # vídeos editados neste processo (limite por rodada do diário)


def _cfg():
    c = motor.cfg()
    return {"ligado": False, "rodadas": 4, "alvo": 9, "por_rodada": 2, "modelo": c["modelo"], **(c.get("editor") or {})}


def _cadeia(c, log):
    """Modelos do editor/corretor na ordem, só os que responderam ao ping (27/10: não esperar 30 min por um modelo)."""
    vivos = []
    for m in [c["modelo"], c.get("modelo_reserva"), c.get("modelo_reserva2")]:
        if m and m not in vivos:
            if motor.responde(m, 90 if "argon" in m else 60):
                vivos.append(m)
            else:
                log(f"  [editor] {m} não respondeu ao teste rápido — pulo")
    return vivos


def _prazo(c, modelo, padrao):
    """Dono 27/10: "Argon curto; se começar a demorar muito, troca pro Gemini" -> prazo menor só para o Argon."""
    if "argon" in str(modelo):
        return int(c.get("argon_prazo_min", 30) * 60)
    # 28/10: Gemini estourou 1 h em 4 de 5 tentativas (27–28/10) e a única edição pronta (92 min) perdeu do molde
    # (5,75 x 6,25) -> prazo da config; cada hora perdida aqui é 1 vídeo a menos na fila
    return int(c["gemini_prazo_min"] * 60) if c.get("gemini_prazo_min") else padrao


def _ff(args, timeout=900):
    r = subprocess.run([FF, "-y", "-v", "error", *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    if r.returncode:
        raise RuntimeError(f"ffmpeg: {r.stderr[-400:]}")


def _hexa(c):
    return "#%02X%02X%02X" % tuple(c)


def preparar(tid, k, ctx, log):
    """Pasta pública com narracao.mp3 (toda a voz já no tempo), trilha, fotos, vídeos das cenas e briefing.json."""
    pub = RAIZ / "remotion" / "trabalhos" / tid / "public"
    shutil.rmtree(pub.parent, ignore_errors=True)
    pub.mkdir(parents=True)
    total = ctx["total"]
    ent, fc, rotas = [], [], []
    for i, (wav, ofs) in enumerate(ctx["vozes"]):
        ent += ["-i", str(wav)]
        ms = int(ofs * 1000)
        fc.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[n{i}]")
        rotas.append(f"[n{i}]")
    fc.append(f"{''.join(rotas)}amix=inputs={len(rotas)}:duration=longest:normalize=0,apad,atrim=0:{total:.3f}[a]")
    _ff([*ent, "-filter_complex", ";".join(fc), "-map", "[a]", "-c:a", "libmp3lame", "-q:a", "2",
         str(pub / "narracao.mp3")])
    shutil.copy2(ctx["trilha"], pub / "trilha.mp3")
    cenas = []
    for c in ctx["cenas"]:
        c = dict(c)
        if c.get("img") is not None:
            nome = f"img_{c['n']}.jpg"
            c["img"].convert("RGB").resize((1080, 1920)).save(pub / nome, quality=92)
            c["foto"] = nome
        c.pop("img", None)
        if c.get("seg"):
            nome = f"{c['tipo'] if c['tipo'] in ('dono', 'real') else 'video'}_{c['n']}.mp4"
            shutil.copy2(c.pop("seg"), pub / nome)
            c["video"] = nome
        c.pop("seg", None)
        cenas.append(c)
    briefing = {"marca": k["marca"], "produto": k["nome_produto"], "publico": k["publico"], "fatos": k["fatos"],
                "cliente_real": bool(k.get("cliente")),
                "cores": {"marca": k["cor_hex"], "apoio": _hexa(k["apoio"]), "fundo_escuro": _hexa(k["escuro"]),
                          "destaque": _hexa(k["destaque"]), "texto_sobre_marca": _hexa(k["texto"])},
                "arroba": k["arroba"], "convite": k["convite"], "convite_voz": k["convite_voz"],
                "titulo": ctx["titulo"], "gancho_tela": ctx["gancho"], "duracao_s": round(total, 2),
                "cenas": cenas, "palavras": ctx["palavras"]}
    (pub / "briefing.json").write_text(json.dumps(briefing, ensure_ascii=False, indent=1), "utf-8")
    src = REMOTION / "src" / "videos" / tid
    shutil.rmtree(src, ignore_errors=True)
    src.mkdir(parents=True)
    (src / "index.ts").write_text("import {registerRoot} from 'remotion';\nimport {Raiz} from './Video';\n\n"
                                  "registerRoot(Raiz);\n", "utf-8")
    log(f"  [editor] material pronto ({total:.1f}s, {len(cenas)} cenas, {len(ctx['palavras'])} palavras)")
    return pub


@contextmanager
def _so_este_video(tid):
    """O editor de lá copiava a edição de outro vídeo da pasta ao lado: durante a sessão só a dele fica visível."""
    videos = REMOTION / "src" / "videos"
    GUARDADOS.mkdir(parents=True, exist_ok=True)
    for p in GUARDADOS.iterdir():  # sobra de sessão que caiu no meio
        if not (videos / p.name).exists():
            shutil.move(str(p), str(videos / p.name))
    outros = [p for p in videos.iterdir() if p.name != tid]
    for p in outros:
        shutil.move(str(p), str(GUARDADOS / p.name))
    try:
        yield
    finally:
        for p in outros:
            shutil.move(str(GUARDADOS / p.name), str(p))


def executar(cmd, cwd, timeout):
    """veio de claude-code-video/motor.py executar v1: saída em ARQUIVO e morte da ÁRVORE no prazo. Com
    capture_output o Chrome do Remotion travou lá, o timeout matou só o npx e os netos seguraram o pipe (2h20)."""
    import tempfile
    import psutil
    with tempfile.TemporaryFile() as saida:
        p = subprocess.Popen(cmd, cwd=str(cwd), stdout=saida, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                for x in psutil.Process(p.pid).children(recursive=True) + [psutil.Process(p.pid)]:
                    x.kill()
            except psutil.Error:
                pass
            return None, f"render passou de {timeout // 60} min (árvore encerrada)"
        saida.seek(0)
        return p.returncode, saida.read().decode("utf-8", "replace")


PC2_REMOTION = r"C:\produto-pc2\remotion"  # npm ci do MESMO package-lock (28/10)
TAR = r"C:\Windows\System32\tar.exe"  # o tar do Git lê "D:\..." como máquina remota


def _ssh_pc2(ps, timeout):
    import base64
    cod = base64.b64encode(ps.encode("utf-16-le")).decode()
    # entrada = pipe VAZIO (input=""): herdada, -n ou DEVNULL o canal não fecha (28/10: render pronto em 3,5 min e a
    # conexão presa 15 min; testado: só o pipe vazio sai sozinho)
    r = subprocess.run(["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "pc2",
                        f"powershell -NoProfile -NonInteractive -EncodedCommand {cod}"], capture_output=True,
                       input="", text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _render_pc2(tid, out, log):
    """28/10 (dona: "PC2 a mais produtiva"; o PC1 caiu por "Cannot allocate memory" renderizando): o render Remotion
    vai pro PC2 com o mesmo layout (src/lib, src/videos/<id>, trabalhos/<id>/public); o PC1 manda 1 tar e traz o mp4.
    3 conexões por render (sem rajada). Falhou/sem RAM lá = False e o render local segue."""
    import tempfile
    pacote = Path(tempfile.gettempdir()) / f"render_{tid}.tar"
    try:
        r = subprocess.run([TAR, "-cf", str(pacote), "-C", str(REMOTION), "src/lib", f"src/videos/{tid}",
                            f"trabalhos/{tid}/public"], capture_output=True, timeout=600)
        if r.returncode:
            raise RuntimeError(f"tar: {r.stderr[-200:]!r}")
        t0 = time.time()
        r = subprocess.run(["scp", "-q", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", str(pacote),
                            "pc2:C:/produto-pc2/pacotes/"], capture_output=True, input=b"", timeout=900)
        if r.returncode:
            raise RuntimeError(f"scp ida: {r.stderr[-200:]!r}")
        ps = f"""$ErrorActionPreference='Continue'
if (-not (Test-Path {PC2_REMOTION}\\node_modules\\.bin\\remotion.cmd)) {{ 'SEM_INSTALACAO'; exit 3 }}
Get-CimInstance Win32_Process -Filter "Name='node.exe' or Name='chrome-headless-shell.exe'" | Where-Object {{ $_.CommandLine -match 'produto-pc2' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }}
$m=[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)
if ($m -lt 2.5) {{ "SEM_RAM $m GB"; exit 4 }}
Set-Location {PC2_REMOTION}
Get-ChildItem trabalhos -Directory -EA SilentlyContinue | Where-Object {{ $_.LastWriteTime -lt (Get-Date).AddHours(-6) }} | Remove-Item -Recurse -Force -EA SilentlyContinue
Remove-Item src\\videos -Recurse -Force -EA SilentlyContinue
& {TAR} -xf C:\\produto-pc2\\pacotes\\render_{tid}.tar
Remove-Item C:\\produto-pc2\\pacotes\\render_{tid}.tar -Force
Remove-Item trabalhos\\{tid}\\video.mp4 -Force -EA SilentlyContinue
cmd /c "npx.cmd remotion render src/videos/{tid}/index.ts Main trabalhos\\{tid}\\video.mp4 --public-dir=trabalhos\\{tid}\\public --log=error --crf=18 --concurrency=2 2>&1"
"RC=$LASTEXITCODE"
if (Test-Path trabalhos\\{tid}\\video.mp4) {{ 'RENDER_OK' }}"""
        rc, txt = _ssh_pc2(ps, 2700)
        if "RENDER_OK" not in txt:
            raise RuntimeError(txt.strip()[-300:] or f"ssh rc={rc}")
        r = subprocess.run(["scp", "-q", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes",
                            f"pc2:C:/produto-pc2/remotion/trabalhos/{tid}/video.mp4", str(out)],
                           capture_output=True, input=b"", timeout=900)
        if r.returncode or not Path(out).exists():
            raise RuntimeError(f"scp volta: {r.stderr[-200:]!r}")
        log(f"  [editor] render no PC2 ({(time.time() - t0) / 60:.1f} min)")
        return True
    except Exception as e:  # noqa: BLE001
        log(f"  [editor] PC2 não renderizou ({type(e).__name__}: {str(e)[-200:]}) — render aqui")
        return False
    finally:
        pacote.unlink(missing_ok=True)


def _render(tid, pub, out, log=print):
    if _cfg().get("render_pc2", True) and _render_pc2(tid, out, log):
        return True, ""
    # v1 do ccv: --concurrency=2, prazo 20 min, 2ª tentativa
    texto = ""
    for _ in range(2):
        cod, texto = executar(["npx.cmd", "remotion", "render", f"src/videos/{tid}/index.ts", "Main", str(out),
                               f"--public-dir={pub}", "--log=error", "--crf=18", "--concurrency=2"], REMOTION, 1200)
        if cod == 0 and Path(out).exists():
            return True, ""
    return False, texto[-1200:]


_JSX_TEXTO = re.compile(r">([^<>{}]*[A-Za-zÀ-ú][^<>{}]*)<")
_LITERAL = re.compile(r"""(["'`])((?:(?!\1).){3,200})\1""")
_CSS = re.compile(r"\b(px|rgba?|deg|ease|cubic|translate|scale|solid|inset|blur|linear-gradient|staticFile|"
                  r"Montserrat|flex|center|absolute)\b|#[0-9a-fA-F]{3,8}\b|\.(png|jpe?g|mp4|mp3|tsx?)\b")
# 26/10 11:15: o editor escreveu "Envio ... em minutos" e selos "100% Automático/Livre" e os verificadores deram só
# "média" -> trava de texto própria (a regra "\d" do roteirista daria alarme em passos "1." e horário de conversa)
_PROIBIDO_TELA = [
    (r"\d+\s*%|\bpor\s*cento\b", "porcentagem inventada"),
    (r"r\$\s*\d|\d\s*reais\b", "preço"),  # 26/10 (mural ccv): "\breais\b" barrava "Fotos Reais dos Pratos"
    (r"\bem\s+(poucos\s+)?(minutos|segundos)\b|\b\d+\s*(min|minutos|segundos)\b|\bna\s+hora\b|instant[aâ]ne",
     "prazo/tempo que não é fato"),
    (r"(?<![\d:/])\b[1-9]\d{1,}(?:[.,]\d+)?\b(?![:h/])|\bmil\b", "número inventado (quantidade)"),
]


def _textos_tsx(src):
    textos = []
    for arq in Path(src).glob("*.tsx"):
        cod = arq.read_text("utf-8", errors="replace")
        textos += [m.group(1).strip() for m in _JSX_TEXTO.finditer(cod)]
        textos += [m.group(2).strip() for m in _LITERAL.finditer(cod)
                   if " " in m.group(2) and re.search(r"[A-Za-zÀ-ú]{3}", m.group(2)) and not _CSS.search(m.group(2))]
    # fora pedaços de código que o regex pega entre "<" e ">" de comparações (x >= 1 && y < 2) e templates ${...}
    # 28/10 (ccv): fora também pedaços de objeto entre duas strings ('", ini: 1.32, fim: 1.36, falante:"' da legenda
    # com `falante`) — deram 20 alarmes falsos de "número inventado" num vídeo só
    return [t for t in textos if t and not re.search(r"[=;&|(){}$]|\breturn\b|\bconst\b|(^|,)\s*[a-z_]\w*\s*:", t)]


def problemas_texto(src, k):
    """O que está ESCRITO na edição e quebra as regras de propaganda (lista de 'trecho: motivo')."""
    from produto import agentes
    fatos = " ".join(k.get("fatos") or []).lower()
    # 27/10: "quase dez anos" é fato do MS Energy e o editor escreveu "Quase 10 Anos" -> barrado à toa
    for palavra, num in (("dois", "2"), ("três", "3"), ("quatro", "4"), ("cinco", "5"), ("seis", "6"), ("sete", "7"),
                         ("oito", "8"), ("nove", "9"), ("dez", "10"), ("vinte", "20"), ("cem", "100")):
        fatos = re.sub(rf"\b{palavra}\b", f"{palavra} {num}", fatos)
    if re.search(r"\b\d{4,}\b|\b\d{1,3}\.\d{3}\b", fatos):
        fatos += " mil"  # 28/10 (ccv): fato "2500" falado por extenso ("dois mil e quinhentos") não é inventado
    erros = []
    for t in sorted(set(_textos_tsx(src))):
        tl = t.lower()
        for padrao, motivo in _PROIBIDO_TELA:
            m = re.search(padrao, tl)
            if m and m.group(0) not in fatos:
                erros.append(f"\"{t[:80]}\": {motivo}")
                break
        else:
            gerais = [e for e in agentes.problemas(t, k) if not e.startswith(("tem número", "contato/site"))]
            if gerais:
                erros.append(f"\"{t[:80]}\": {gerais[0][:120]}")
    return erros


def _nivelar(mp4, log):
    from produto import video
    video.nivelar(Path(mp4), log)


def melhorar(conta, k, ctx, side, mp4_molde, log):
    """Tenta a versão do editor. Devolve (mp4, lapidar_res) da versão do editor se ela tirou nota MAIOR que a do
    molde; senão None (o molde fica)."""
    c = _cfg()
    if not c["ligado"] or len(_feitos) >= c["por_rodada"]:
        return None
    _feitos.append(conta)
    tid = Path(mp4_molde).stem
    nota_molde = (side.get("lapidar") or {}).get("nota")
    pub = preparar(tid, k, ctx, log)
    trab = pub.parent
    quadros = trab / "quadros"
    quadros.mkdir(exist_ok=True)
    mp4 = trab / "video.mp4"
    src = REMOTION / "src" / "videos" / tid
    t0 = time.time()
    prompt = f"""Leia EDITOR.md (pasta atual) e siga à risca. Você vai editar o vídeo de ID `{tid}`.
- Pasta pública (material + briefing.json): {pub}
- Seu código: src/videos/{tid}/Video.tsx  (index.ts já existe)
- PROIBIDO abrir/ler/copiar outras pastas de src/videos/: crie a edição do zero.
- Pasta para os quadros de conferência: {quadros}
Produto: {k['nome_produto']} ({k['marca']}). Duração: {ctx['total']:.2f} s.
Faça um trabalho de agência: motion design de verdade, não slides."""
    erro = None
    for tentativa in range(2):  # render falhou = volta pro editor com o erro (1 vez)
        texto = None
        # 26/10 14:08: o gateway respondeu "unrecognized_model" no meio da edição (passageiro: 10 min depois os 3
        # modelos respondiam) -> 2ª tentativa com o modelo reserva, continuando o Video.tsx que já está no disco
        for modelo in _cadeia(c, log):
            try:
                ja = (src / "Video.tsx").exists()
                with _so_este_video(tid):
                    texto = motor.chamar(prompt + (f"\nO render FALHOU com este erro, conserte: {erro}" if erro else "")
                                         + ("\nO Video.tsx JÁ EXISTE de uma sessão interrompida: leia, continue e "
                                            "termine (não recomece)." if ja else ""),
                                         REMOTION, "produto_editar", timeout=_prazo(c, modelo, 3600), max_turnos=90,
                                         ferramentas=motor.EDITOR, modelo=modelo, aceitar_limite=True)
                break
            except (motor.MotorErro, motor.SemCota) as e:
                log(f"  [editor] {modelo} falhou: {str(e)[:160]}")
        if texto is None:
            log("  [editor] sem editor agora — fica o molde")
            return None
        log(f"  [editor] edição pronta ({(time.time() - t0) / 60:.0f} min): {texto[-160:]}")
        ok, erro = _render(tid, pub, mp4, log)
        if ok:
            break
        log(f"  [editor] render falhou: {erro[-200:]}")
    else:
        return None
    _nivelar(mp4, log)

    side_ed = {**side, "cenas": [{kk: v for kk, v in cc.items() if kk in ("n", "ini", "fim", "fala", "tipo")}
                                 for cc in ctx["cenas"]], "variante": f"{side.get('variante')}+editor"}
    melhor, melhor_res = -1.0, None
    melhor_mp4, melhor_src = trab / "melhor.mp4", trab / "melhor_src"
    notas, ant_graves = [], []
    for n in range(1, c["rodadas"] + 1):
        res = lapidar.verificar(mp4, side_ed, k, log)
        if not res:
            break
        notas.append(res["nota"])
        erros_txt = problemas_texto(src, k)
        log(f"  [editor] rodada {n}: nota {res['nota']} (molde {nota_molde})"
            + (f"; TEXTO PROIBIDO: {' | '.join(erros_txt)[:300]}" if erros_txt else ""))
        if erros_txt:
            res["verificadores"].append({"foco": "regras_texto", "nota": 0, "elogios": [], "problemas": [
                {"gravidade": "grave", "quadro": "-", "cena": "-", "problema": f"texto na tela quebra a regra: {e}",
                 "como_corrigir": "apague/troque esse texto (só os fatos permitidos, sem número/prazo/porcentagem)"}
                for e in erros_txt]})
        if res["nota"] > melhor and not res["reprovar"] and not erros_txt:
            melhor, melhor_res = res["nota"], res
            shutil.copy2(mp4, melhor_mp4)
            shutil.rmtree(melhor_src, ignore_errors=True)
            shutil.copytree(src, melhor_src)
        graves = [p for v in res["verificadores"] for p in v["problemas"] if p.get("gravidade") == "grave"]
        sem_melhora = len(notas) >= 3 and max(notas[-2:]) <= max(notas[:-2])
        if (res["nota"] >= c["alvo"] and not graves) or n == c["rodadas"] or sem_melhora:
            break
        ordem = {"grave": 0, "media": 1, "leve": 2}
        probs = sorted(((p, v["foco"]) for v in res["verificadores"] for p in v["problemas"]),
                       key=lambda x: ordem.get(x[0].get("gravidade"), 1))
        lista = "\n".join(f"- [{p.get('gravidade')}] ({f}) {p.get('quadro')} cena {p.get('cena')}: {p.get('problema')} "
                          f"-> {p.get('como_corrigir')}" for p, f in probs)
        elogios = "\n".join(f"- {e}" for v in res["verificadores"] for e in v["elogios"])
        antes = "\n".join(f"- {g}" for g in ant_graves)
        ant_graves = [p.get("problema") for p in graves]
        corr = f"""Leia EDITOR.md (pasta atual). Você é o CORRETOR da edição do vídeo `{tid}` (código em
src/videos/{tid}/). A edição já existe e foi renderizada; os verificadores deram nota {res['nota']}/10.
NÃO recomece do zero: corrija os problemas abaixo no código, do mais grave ao mais leve, sem estragar o que foi
elogiado. PROIBIDO abrir outras pastas de src/videos/.
Pasta pública (material + briefing.json): {pub}
Pasta para seus quadros de conferência: {quadros}

PROBLEMAS:
{lista}

MANTER (elogiado):
{elogios or '- (nada)'}
{('GRAVES DA RODADA ANTERIOR (se algum acima é o mesmo, a correção passada NÃO funcionou: mude a abordagem):'
  + chr(10) + antes) if antes else ''}

NÃO ESTRAGUE O QUE ESTÁ CERTO:
- Fatos permitidos, e SÓ eles: {'; '.join(k['fatos'])}. Não acrescente número, prazo, "24h", preço ou alegação.
- Tempo das cenas é fixo (a voz está pronta); rosto do dono sempre livre.
- Scroll de mockup para com itens inteiros; legenda ancorada pela base em y <= 1580; letra >= 32 px; margem 60 px.

Depois de corrigir, gere stills (npx remotion still) dos momentos mexidos, OLHE com Read e confirme. No fim
responda uma frase com o que mudou."""
        corrigiu = False
        for modelo in _cadeia(c, log):  # Argon demorou -> Gemini continua (27/10, dono)
            try:
                with _so_este_video(tid):
                    motor.chamar(corr, REMOTION, "produto_corrigir", timeout=_prazo(c, modelo, 2700), max_turnos=90,
                                 ferramentas=motor.EDITOR, modelo=modelo, aceitar_limite=True)
                corrigiu = True
                break
            except (motor.MotorErro, motor.SemCota) as e:
                log(f"  [editor] corretor {modelo} falhou: {str(e)[:160]}")
        if not corrigiu:
            break
        ok, erro = _render(tid, pub, mp4, log)
        if not ok:
            log(f"  [editor] render da correção falhou: {erro[-200:]}")
            break
        _nivelar(mp4, log)
    log(f"  [editor] melhor nota do editor {melhor} x molde {nota_molde} ({(time.time() - t0) / 60:.0f} min)")
    if melhor_res and (nota_molde is None or melhor > nota_molde):
        return melhor_mp4, melhor_res
    return None


def limpar(tid):
    """Depois de copiar o vídeo pra fila: a pasta de trabalho sai; o código da edição fica (remotion\\src\\videos)."""
    shutil.rmtree(RAIZ / "remotion" / "trabalhos" / tid, ignore_errors=True)
