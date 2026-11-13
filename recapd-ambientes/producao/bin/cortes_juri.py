# -*- coding: utf-8 -*-
"""cortes_juri.py — sistema Claude Code Video (júri Gemini + movimento medido + aprendiz) na linha CORTES.
# veio de claude-code-video v1.1 (gerar.py: quadros_e_movimento, VERIFICADORES_ENTRETENIMENTO, verificar_generico,
# _aprender; motor.py: executar, chamar, chamar_json) — adaptado: Shorts prontos de parceiro, sem camada editável.

Linha de muito volume (ATUALIZACAO_PARA_LINHAS "CORTES"): movimento medido em TODO Short (sem IA, barato); júri de
entretenimento (4 focos em paralelo, agy/gemini-3.8-flash-high, reserva automática) em 1 a cada JURI_CADA; o
APRENDIZ reescreve linhas\\CORTES\\APRENDIDO.md com o lote (+ opinião do dono, que vale mais) — quem transforma as
regras em mudança do pipeline é a sessão da linha (não se corrige Short por Short).
Saída: linhas\\CORTES\\juri\\<pasta do Short>\\ (q01.jpg..., folha.jpg, juri.json) e linhas\\CORTES\\evolucao.jsonl.

    python cortes_juri.py rodar        # tarefa Cortes_Juri (a cada 30 min, prioridade baixa)
    python cortes_juri.py um <pasta>   # força júri num Short
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

SHORTS = Path(r"D:\hipercool-materiais\animes recap\shorts")
LINHA = Path(r"D:\video-fila\linhas\CORTES")
JURI = LINHA / "juri"
EVOL = LINHA / "evolucao.jsonl"
APRENDIDO = LINHA / "APRENDIDO.md"
OPINIOES = Path(r"D:\hipercool-materiais\CORTES_ULTIMO_VIDEO\OPINIOES.txt")  # 27/10: pasta mudou (dono não achava)
OPINIOES_USADAS = Path(r"D:\hipercool-materiais\CORTES_ULTIMO_VIDEO\.opinioes_usadas.txt")
LOG = LINHA / "juri.log"
TRAVA = LINHA / ".juri.lock"
CFG_CCV = Path(r"D:\claude-code-video\config.json")  # só leitura: gateway e chave (não entra no sys.path)
MODELO = "agy/gemini-3.8-flash-high"
MODELO_RESERVA = "antigravity/gemini-3.8-flash-tiered"
MOV_MIN = 4          # % de mudança entre 20% e 80% da cena: abaixo = cena PARADA (calibrado no claude-code-video)
N_CENAS = 6          # o Short não guarda o roteiro com tempo: 6 pedaços iguais
JURI_CADA = 4        # júri em 1 a cada 4 Shorts (muito volume)
DESDE = datetime(2026, 10, 26, 19, 0).timestamp()  # Shorts anteriores à implantação não entram
FFMPEG = "ffmpeg"
# 28/10: o júri tirava ponto (e o aprendiz virou regra 19) do que a DONA decidiu: "narrar em 3ª pessoa" contra a 1ª
# pessoa de dorama/filme; o fim "..." do loop lido como corte; frase "truncada" que era o júri juntando pedaços de
# legenda de quadros diferentes. Decisões fixas do dono entram no júri e no aprendiz; o roteiro real vai junto.
DECISOES_DONO = """DECISÕES FIXAS DO DONO (não são defeito; nunca peça o contrário):
- Dorama, filme e histórias: narração em 1ª PESSOA do protagonista ('eu', 'meu') é de propósito. Narração com jeito
  de narrador brasileiro (gíria, 'francamente', bordão) é de propósito.
- O fim termina com frase aberta ('provando pra essa...') que EMENDA na 1ª frase do vídeo: é o LOOP, não corte.
- Cada quadro mostra só um PEDAÇO da legenda (palavra-a-palavra): NÃO junte pedaços de quadros diferentes e chame de
  frase quebrada. Para julgar o texto, use o ROTEIRO abaixo (é o que a voz fala).
- Tarja branca só quando a fonte tem legenda queimada; zona segura y 150–1580; letra mínima 32 px."""


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


# ─── motor (veio de claude-code-video/motor.py v1.1) ─────────────────────────────────────────────────────────────
class MotorErro(Exception):
    pass


def executar(cmd, cwd, timeout, env=None, entrada=None):
    """subprocess com saída em ARQUIVO e morte da árvore inteira no tempo limite (26/10: um travamento segurou o
    pipe 2h20). Devolve (código, saída) ou levanta subprocess.TimeoutExpired."""
    import psutil
    with tempfile.TemporaryFile() as out:
        p = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdin=subprocess.PIPE if entrada is not None else None,
                             stdout=out, stderr=subprocess.STDOUT,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))  # 27/10: pythonw abria 1 janela cmd por jurado
        try:
            if entrada is not None:
                p.stdin.write(entrada)
                p.stdin.close()
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                for x in psutil.Process(p.pid).children(recursive=True) + [psutil.Process(p.pid)]:
                    x.kill()
            except psutil.Error:
                pass
            raise
        out.seek(0)
        return p.returncode, out.read().decode("utf-8", "replace")


def _exe():
    achados = sorted((Path.home() / ".vscode" / "extensions").glob(
        "anthropic.claude-code-*/resources/native-binary/claude.exe"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not achados:
        raise MotorErro("claude.exe não encontrado nas extensões do VS Code")
    return str(achados[0])


def chamar_json(prompt, pasta, modelo, timeout=900, max_turnos=30):
    """Gemini pelo claude.exe -p (só Read: ele OLHA os quadros da pasta). Devolve o 1º objeto JSON da resposta."""
    cfg = json.loads(CFG_CCV.read_text("utf-8"))
    env = dict(os.environ, ANTHROPIC_BASE_URL=cfg["gateway"], ANTHROPIC_AUTH_TOKEN=cfg["chave"],
               ANTHROPIC_MODEL=modelo, ANTHROPIC_DEFAULT_OPUS_MODEL=modelo, ANTHROPIC_DEFAULT_SONNET_MODEL=modelo,
               ANTHROPIC_DEFAULT_HAIKU_MODEL=modelo, ANTHROPIC_SMALL_FAST_MODEL=modelo,
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
    env.pop("ANTHROPIC_API_KEY", None)
    cmd = [_exe(), "-p", "--output-format", "json", "--max-turns", str(max_turnos), "--setting-sources", "project",
           "--allowedTools", "Read", "--disallowedTools", "Bash,Edit,Write,WebFetch,WebSearch,Agent"]
    for tentativa in range(2):
        p = prompt if not tentativa else prompt + "\n\nIMPORTANTE: responda SÓ o JSON válido, nada mais."
        try:
            _, saida = executar(cmd, pasta, timeout, env=env, entrada=p.encode("utf-8"))
        except subprocess.TimeoutExpired:
            raise MotorErro(f"timeout {timeout}s")
        res = None
        for linha in reversed(saida.strip().splitlines()):
            if linha.startswith("{"):
                try:
                    res = json.loads(linha)
                    break
                except ValueError:
                    pass
        if not res or res.get("is_error") or res.get("subtype") != "success":
            raise MotorErro(f"{(res or {}).get('subtype')} {str((res or {}).get('result') or saida[-300:])[:300]}")
        m = re.search(r"\{.*\}", res.get("result") or "", re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except ValueError:
                pass
    raise MotorErro("JSON inválido")


# ─── quadros + movimento (veio de claude-code-video/gerar.py v1.1) ──────────────────────────────────────────────
def _dur(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return float((r.stdout or "0").strip() or 0)


def quadros_e_movimento(mp4, pasta, cenas):
    """3 quadros por cena (20/50/80%) + folha.jpg; devolve (itens para o júri, [% de movimento por cena])."""
    from PIL import Image, ImageChops, ImageStat
    pasta.mkdir(parents=True, exist_ok=True)
    itens, ims, mov, pcts = [], [], [], []
    # 12/11: as cenas do roteiro passavam do fim do vídeo (sem-obra-afc76d: vídeo 17,0 s, último quadro em ~17,x s) — o
    # ffmpeg não gera o quadro, o Image.open dava FileNotFoundError e o júri morria SEMPRE no mesmo Short (tarefa
    # Cortes_Juri "código 1" desde 11/11 21:23, nenhum Short julgado). Agora o tempo fica dentro do vídeo e quadro que
    # não sai é pulado.
    dur = _dur(mp4)
    for c in cenas:
        da_cena = []
        for frac in (0.2, 0.5, 0.8):
            seg = round(c["ini"] + (c["fim"] - c["ini"]) * frac, 2)
            if dur > 0.5:
                seg = round(min(seg, dur - 0.25), 2)
            nome = f"q{len(itens) + 1:02d}.jpg"
            subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{seg}", "-i", str(mp4),
                            "-frames:v", "1", "-vf", "scale='min(960,iw)':-2", "-q:v", "3", str(pasta / nome)],
                           capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            if not (pasta / nome).exists():
                continue
            itens.append(f"{nome}: cena {c['n']}, {seg}s, fala da cena: \"{c.get('fala', '')}\"")
            im = Image.open(pasta / nome).convert("RGB")
            larg = 270 if im.height > im.width else 480
            ims.append(im.resize((larg, round(larg * im.height / im.width))))
            da_cena.append(ims[-1])
        if len(da_cena) < 2:
            continue  # cena sem 2 quadros (fora do vídeo): não dá pra medir movimento
        dif = sum(ImageStat.Stat(ImageChops.difference(da_cena[0].convert("L"), da_cena[-1].convert("L"))).mean) / 2.55
        pcts.append(round(dif, 1))
        mov.append(f"cena {c['n']}: mudança de imagem entre 20% e 80% da cena = {dif:.1f}%"
                   + (" -> PARADA (medido)" if dif < MOV_MIN else ""))
    itens.append(f"MOVIMENTO MEDIDO POR CENA (abaixo de {MOV_MIN}% = cena parada):\n" + "\n".join(mov))
    if not ims:
        raise RuntimeError(f"nenhum quadro saiu de {Path(mp4).name} (vídeo de {dur:.1f} s)")
    w, h = ims[0].size
    folha = Image.new("RGB", (w * 3, h * ((len(ims) + 2) // 3)))
    for i, im in enumerate(ims):
        folha.paste(im.resize((w, h)), ((i % 3) * w, (i // 3) * h))
    folha.save(pasta / "folha.jpg", quality=88)
    return itens, pcts


# ─── júri de entretenimento (veio de claude-code-video/gerar.py v1.1) ───────────────────────────────────────────
VERIFICADORES = {
    "legibilidade": """LEGIBILIDADE E ENQUADRAMENTO. Procure: texto cortado ou saindo da tela; texto/elemento importante
acima de y=150 ou abaixo de y=1580 (de 1920 — lá ficam os botões do Reels) ou a menos de 60 px da lateral; letra
pequena demais para ler no celular (corpo < ~34 px no vídeo 1080x1920); pouco contraste; elemento cobrindo rosto ou
outro texto; legenda/karaokê quebrando palavra; tarja branca cobrindo imagem sem legenda da fonte embaixo.""",
    "movimento": """RITMO E MOVIMENTO. Procure: imagem/painel parado com a narração andando (veja o MOVIMENTO MEDIDO);
cena que dura demais para o que conta; corte seco sem intenção; zoom/pan que não segue o foco da ação; troca de
cena que não bate com a mudança da narração; trecho escuro/quase preto; final parado ou cortado no meio da frase.""",
    "historia": """HISTÓRIA E SINCRONIA. Procure: imagem que não mostra o que a narração diz NAQUELE momento
(personagem errado, cena de outro momento); legenda diferente da fala; nome/gênero de personagem trocado (ex.: "ELE"
numa protagonista mulher); erro de português; gancho que só entende quem já conhece a obra; spoiler do final logo
no começo (inclusive no título da tarja); marca d'água ou legenda queimada da fonte visível.""",
    "retencao": """DIRETOR DE RETENÇÃO (YouTube Shorts/TikTok). O gancho dos 2 primeiros segundos faz a pessoa ficar?
Há um motivo para continuar assistindo a cada ~5 s (pergunta aberta, virada, revelação)? O título/tarja/CTA no
meio ajuda ou atrapalha? Diga as 3 mudanças de MAIOR impacto na retenção (concretas: o quê, em qual cena, como).""",
}


def _roteiro(pj_meta_dir):
    """Texto que a voz fala (roteiro.txt da pasta de trabalho apontada no metadata.json), ou ""."""
    try:
        meta = json.loads((pj_meta_dir / "metadata.json").read_text("utf-8"))
        return (Path(meta["video"]["path"]).parent / "roteiro.txt").read_text("utf-8").strip()[:3000]
    except (OSError, ValueError, KeyError, TypeError):
        return ""


def verificar(pasta, itens, foco, descricao, roteiro=""):
    prompt = f"""Você é um VERIFICADOR exigente de {descricao}. Seu foco único: {VERIFICADORES[foco]}

{DECISOES_DONO}

ROTEIRO (o que a voz fala, na ordem):
{roteiro or "(não achado — julgue o texto só pelo que der pra ver com certeza)"}

Use Read para OLHAR folha.jpg (visão geral, cada linha = uma cena) e depois abra os quadros que precisar em tamanho
maior. Quadros:
{chr(10).join(itens)}

É um Short de RECAP narrado por cima de um vídeo de canal parceiro: a tarja branca com título cobre a legenda queimada
da fonte (só deve existir se a fonte tiver legenda); a legenda amarela/branca palavra-a-palavra é a NOSSA narração; o
@ é a marca do nosso canal.
Pense com calma e a fundo antes de responder. Seja duro: nota 10 = nível profissional top, sem nenhum defeito do
seu foco. Aponte só problemas reais que você VIU, com o quadro.
Responda SÓ JSON: {{"nota": 0-10, "problemas": [{{"quadro": "q03.jpg", "cena": 1, "gravidade": "grave|media|leve",
"problema": "...", "como_corrigir": "instrução concreta"}}], "elogios": ["o que está bom e deve ficar"]}}"""
    for m, turnos in ((MODELO, 30), (MODELO_RESERVA, 40)):
        try:
            r = chamar_json(prompt, pasta, m, max_turnos=turnos)
            return {"foco": foco, "nota": float(r.get("nota") or 0), "problemas": r.get("problemas") or [],
                    "elogios": r.get("elogios") or [], "modelo": m}
        except MotorErro as e:
            log(f"  [verificador {foco}] {m} falhou: {str(e)[:150]}")
    return None


def _opiniao_nova():
    try:
        txt = OPINIOES.read_text("utf-8")
        usado = OPINIOES_USADAS.read_text("utf-8") if OPINIOES_USADAS.exists() else ""
    except OSError:
        return ""
    linhas = [l for l in txt.splitlines()[2:] if l.strip() and l.strip() not in usado]
    return "\n".join(linhas)


def aprender(juris):
    """Os defeitos do lote viram REGRAS do pipeline dos Cortes (APRENDIDO.md; a sessão da linha aplica)."""
    atuais = APRENDIDO.read_text("utf-8") if APRENDIDO.exists() else "(vazio)"
    probs = "\n".join(f"- [{p.get('gravidade')}] ({v['foco']}) {j['pasta']}: {p.get('problema')} -> {p.get('como_corrigir')}"
                      for j in juris for v in j["verificadores"] for p in v["problemas"])
    dono = _opiniao_nova()
    if dono:
        probs = f"OPINIÃO DO DONO (vale MAIS que os verificadores; vire regra com prioridade máxima):\n{dono}\n\n" + probs
    prompt = f"""Você mantém o caderno de regras do PIPELINE AUTOMÁTICO de Shorts de recap (cortes de canais
parceiros narrados com voz clonada, tarja branca com título sobre a legenda da fonte, legenda palavra-a-palavra).
Verificadores apontaram defeitos nos últimos Shorts. Transforme em REGRAS GERAIS curtas e acionáveis para o pipeline
(o que o código deve passar a fazer), para não repetir.

REGRAS ATUAIS:
{atuais}

DEFEITOS DO LOTE:
{probs}

Mantenha as que continuam valendo, junte as repetidas, acrescente as novas, prioridade primeiro ao que mais derruba
nota; no máximo 25 regras, 1–2 linhas cada, imperativas e concretas (números quando houver). Nada específico de um
vídeo. Regra atual que contrarie as decisões abaixo SAI do caderno.
{DECISOES_DONO}
Responda SÓ JSON: {{"regras": ["...", "..."]}}"""
    try:
        r = chamar_json(prompt, LINHA, MODELO, max_turnos=6)
    except MotorErro as e:
        log(f"  [aprender] não atualizou: {str(e)[:150]}")
        return
    regras = [x for x in r.get("regras") or [] if isinstance(x, str) and x.strip()]
    if regras:
        APRENDIDO.write_text(f"# Regras aprendidas — CORTES (atualizado {datetime.now():%d/%m %H:%M}; a sessão da linha "
                             "aplica no pipeline)\n" + "".join(f"{i}. {x.strip()}\n" for i, x in enumerate(regras, 1)),
                             "utf-8")
        log(f"  [aprender] {len(regras)} regras em APRENDIDO.md")
        if dono:
            with OPINIOES_USADAS.open("a", encoding="utf-8") as f:
                f.write(dono + "\n")


def _feitos():
    out = {}
    if EVOL.exists():
        for l in EVOL.read_text("utf-8").splitlines():
            try:
                d = json.loads(l)
                out[d["id"]] = d
            except (ValueError, KeyError):
                pass
    return out


# 28/10: o júri viu "[EMPTY RESPONSE]" queimado no topo 9 vezes (desde 27/10 20:42) e o Short foi pra fila assim
# mesmo. Texto de erro de IA/sistema na TELA é certeza (não gosto): o júri segura o Short que ainda não foi agendado.
_TEXTO_ERRO = re.compile(r"\[?EMPTY RESPONSE\]?|\bundefined\b|\bNaN\b|texto de erro|erro de (sistema|api)|"
                         r"string de erro|placeholder", re.IGNORECASE)


def _trava_texto_erro(pasta_short, pj, vs, lin):
    achou = [p.get("problema", "") for v in vs for p in v["problemas"]
             if p.get("gravidade") == "grave" and _TEXTO_ERRO.search(p.get("problema", ""))]
    if not achou or not pj or pj.get("publish_at") or not pj.get("pronto"):
        return
    pj.update(pronto=False, revisao=f"reprovado (segurado): júri viu texto de erro na tela — {achou[0][:200]}")
    (pasta_short / "postar.json").write_text(json.dumps(pj, ensure_ascii=False, indent=2), encoding="utf-8")
    lin["segurado"] = "texto de erro"
    log(f"  [TRAVA] {pasta_short.name} segurado: texto de erro na tela ({achou[0][:80]})")


def avaliar(pasta_short, com_juri):
    mp4 = pasta_short / "video.mp4"
    dur = _dur(mp4)
    if dur <= 3:
        return None
    cenas = [{"n": i + 1, "ini": dur * i / N_CENAS, "fim": dur * (i + 1) / N_CENAS, "fala": ""} for i in range(N_CENAS)]
    pasta = JURI / pasta_short.name
    itens, pcts = quadros_e_movimento(mp4, pasta, cenas)
    try:
        pj = json.loads((pasta_short / "postar.json").read_text("utf-8"))
    except (OSError, ValueError):
        pj = {}
    lin = {"id": pasta_short.name, "data": datetime.now().isoformat(timespec="seconds"), "canal": pj.get("canal"),
           "nicho": pj.get("midia"), "dur": round(dur, 1), "mov": pcts, "paradas": sum(p < MOV_MIN for p in pcts)}
    juri = None
    if com_juri:
        desc = (f"um Short vertical de recap ({pj.get('midia', '?')}) do canal {pj.get('canal', '?')}, título "
                f"\"{pj.get('titulo', '')}\"")
        rot = _roteiro(pasta_short)
        with ThreadPoolExecutor(max_workers=4) as ex:
            vs = [v for v in ex.map(lambda f: verificar(pasta, itens, f, desc, rot), VERIFICADORES) if v]
        if vs:
            nota = round(sum(v["nota"] for v in vs) / len(vs), 2)
            juri = {"pasta": pasta_short.name, "nota": nota, "verificadores": vs}
            (pasta / "juri.json").write_text(json.dumps(juri, ensure_ascii=False, indent=1), "utf-8")
            lin.update(nota=nota, notas={v["foco"]: v["nota"] for v in vs},
                       graves=sum(p.get("gravidade") == "grave" for v in vs for p in v["problemas"]))
            _trava_texto_erro(pasta_short, pj, vs, lin)
    with EVOL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(lin, ensure_ascii=False) + "\n")
    log(f"{pasta_short.name}: movimento {pcts} ({lin['paradas']} parada(s))"
        + (f" | júri {lin.get('nota')} {lin.get('notas')}" if juri else ""))
    return juri


def rodar(max_videos=6):
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:  # noqa: BLE001
        pass
    feitos = _feitos()
    novos = sorted((p.parent for p in SHORTS.glob("*/video.mp4")
                    if p.stat().st_mtime >= DESDE and p.parent.name not in feitos and not p.parent.name.startswith("_")),
                   key=lambda p: (p / "video.mp4").stat().st_mtime)[:max_videos]
    n_total = len(feitos)
    juris = []
    for p in novos:
        lingua = bool(re.search(r"_[a-z]{2}$", p.name))  # versão em outra língua (_vi, _th): júri lê em pt, só movimento
        if not lingua:
            n_total += 1
        try:  # 27/10: Short com texto do Argon = júri sempre (medir Argon x Gemini rápido)
            argon = bool(json.loads((p / "postar.json").read_text(encoding="utf-8")).get("texto_modelo"))
        except (OSError, ValueError):
            argon = False
        # 12/11: um Short com erro derrubava a rodada inteira e voltava em 1º na próxima (preso pra sempre). Agora o
        # erro fica nele: registra no evolucao.jsonl com "erro" (não é tentado de novo) e segue pros outros.
        try:
            j = avaliar(p, com_juri=(not lingua and (argon or n_total % JURI_CADA == 1)))
        except Exception as e:  # noqa: BLE001
            log(f"{p.name}: júri falhou ({type(e).__name__}: {str(e)[:150]}) — marcado e segue pro próximo")
            with EVOL.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"id": p.name, "em": datetime.now().isoformat(timespec="seconds"),
                                    "erro": f"{type(e).__name__}: {str(e)[:200]}"}, ensure_ascii=False) + "\n")
            continue
        if j:
            juris.append(j)
    if juris:
        aprender(juris)


def main():
    LINHA.mkdir(parents=True, exist_ok=True)
    if TRAVA.exists() and datetime.now().timestamp() - TRAVA.stat().st_mtime < 3 * 3600:
        return  # outra rodada em andamento
    TRAVA.write_text(str(os.getpid()))
    try:
        if len(sys.argv) > 2 and sys.argv[1] == "um":
            j = avaliar(SHORTS / sys.argv[2], com_juri=True)
            if j:
                aprender([j])
        else:
            rodar()
    finally:
        TRAVA.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
