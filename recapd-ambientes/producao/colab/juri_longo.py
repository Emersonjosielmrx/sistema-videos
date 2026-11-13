"""juri_longo.py — júri Gemini + movimento medido no recap LONGO, POR AMOSTRA (dona 26/10: "adicione estrategicamente
em trechos; o vídeo longo inteiro na IA seria muito consumo de tokens e demora").

Peças copiadas do sistema Claude Code Video (D:\\claude-code-video; não entra no sys.path):
  executar/chamar/chamar_json      # veio de claude-code-video/motor.py v1.1
  quadros_e_movimento, VERIFICADORES_ENTRETENIMENTO, verificar_generico   # veio de claude-code-video/gerar.py v1.1
Adaptado ao deitado (16:9) e ao longo: 1 trecho na abertura, 1 por capítulo (até 8) e o final. Movimento medido
em todo trecho (sem IA, < 4% = parado). 4 verificadores em paralelo (agy/gemini-3.8-flash-high, reserva tiered).
Saída: <pasta>/juri.json + 1 linha em D:\\video-fila\\linhas\\LONGOS\\evolucao.jsonl.

    python juri_longo.py <video.mp4> [--ficha <pasta na_nuvem>] [--so-movimento]
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

if sys.platform == "win32":  # rclone/ffmpeg/claude filhos sem janela (dona 26/10)
    for _p in (r"D:\hipercool-materiais\comum", r"C:\hipercool-materiais\comum"):
        if Path(_p, "sem_janela.py").exists():
            sys.path.append(_p)
            import sem_janela  # noqa: F401,E402
            break

AQUI = Path(__file__).resolve().parent
CCV_CONFIG = Path(r"D:\claude-code-video\config.json")  # só lê gateway/chave
EVOLUCAO = Path(r"D:\video-fila\linhas\LONGOS\evolucao.jsonl")
CONSUMO = AQUI / "juri_consumo.jsonl"
MODELO = "agy/gemini-3.8-flash-high"
MODELO_RESERVA = "antigravity/gemini-3.8-flash-tiered"
MOV_MIN = 4
EXT = Path.home() / ".vscode" / "extensions"


class MotorErro(Exception):
    pass


# ── veio de claude-code-video/motor.py v1.1 ──────────────────────────────────────────────────────────────────────
def executar(cmd, cwd, timeout, env=None, entrada=None):
    """Saída em ARQUIVO e morte da ÁRVORE de processos no tempo limite (26/10: 2h20 parado com capture_output)."""
    import psutil
    with tempfile.TemporaryFile() as out:
        p = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdin=subprocess.PIPE if entrada is not None else None,
                             stdout=out, stderr=subprocess.STDOUT)
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
    achados = sorted(EXT.glob("anthropic.claude-code-*/resources/native-binary/claude.exe"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
    if not achados:
        raise MotorErro("claude.exe não encontrado")
    return str(achados[0])


def chamar(prompt, pasta, etapa, timeout=900, max_turnos=30, modelo=MODELO):
    cfg = json.loads(CCV_CONFIG.read_text("utf-8"))
    env = dict(os.environ, ANTHROPIC_BASE_URL=cfg["gateway"], ANTHROPIC_AUTH_TOKEN=cfg["chave"],
               ANTHROPIC_MODEL=modelo, ANTHROPIC_DEFAULT_OPUS_MODEL=modelo, ANTHROPIC_DEFAULT_SONNET_MODEL=modelo,
               ANTHROPIC_DEFAULT_HAIKU_MODEL=modelo, ANTHROPIC_SMALL_FAST_MODEL=modelo,
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
    env.pop("ANTHROPIC_API_KEY", None)
    cmd = [_exe(), "-p", "--output-format", "json", "--max-turns", str(max_turnos), "--setting-sources", "project",
           "--allowedTools", "Read", "--disallowedTools", "Bash,Edit,Write,WebFetch,WebSearch,Agent"]
    ini = datetime.now()
    try:
        _, saida = executar(cmd, pasta, timeout, env=env, entrada=prompt.encode("utf-8"))
    except subprocess.TimeoutExpired:
        raise MotorErro(f"timeout {timeout}s")
    res = next((json.loads(l) for l in reversed(saida.strip().splitlines()) if l.startswith("{")), None)
    with CONSUMO.open("a", encoding="utf-8") as f:
        u = (res or {}).get("usage") or {}
        f.write(json.dumps({"em": ini.isoformat(timespec="seconds"), "etapa": etapa, "modelo": modelo,
                            "segundos": round((datetime.now() - ini).total_seconds()),
                            "entrada": u.get("input_tokens", 0), "saida": u.get("output_tokens", 0)}) + "\n")
    if res is None or res.get("is_error") or res.get("subtype") != "success":
        raise MotorErro(f"{(res or {}).get('subtype')} {str((res or {}).get('result') or saida[-300:])[:300]}")
    return (res.get("result") or "").strip()


def chamar_json(prompt, pasta, etapa, **kw):
    txt = ""
    for tentativa in range(2):
        txt = chamar(prompt if not tentativa else prompt + "\n\nIMPORTANTE: responda SÓ o JSON válido.", pasta, etapa, **kw)
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except ValueError:
                pass
    raise MotorErro(f"JSON inválido: {txt[:200]}")


# ── veio de claude-code-video/gerar.py v1.1 (adaptado ao deitado) ─────────────────────────────────────────────────
VERIFICADORES_ENTRETENIMENTO = {
    "legibilidade": """LEGIBILIDADE E ENQUADRAMENTO (vídeo DEITADO 16:9). Procure: texto/legenda cortado ou saindo da
tela; letra pequena demais para ler no celular; pouco contraste; legenda/tarja/elemento cobrindo rosto ou balão
importante; legenda quebrando palavra; legenda queimada da fonte aparecendo junto com a nossa; borrão fixo sem motivo.
PRECISÃO: antes de dizer que palavras "grudaram", amplie o quadro e diga se o espaço está AUSENTE ou só ESTREITO.""",
    "movimento": """RITMO E MOVIMENTO. Procure: imagem/painel parado com a narração andando (veja o MOVIMENTO MEDIDO);
cena que dura demais para o que conta; corte seco sem intenção; zoom/pan que não segue o foco da ação; troca de
cena que não bate com a mudança da narração; final parado ou cortado no meio da frase.""",
    "historia": """HISTÓRIA E SINCRONIA. Procure: imagem que não mostra o que a narração diz NAQUELE momento
(personagem errado, cena de outro momento); legenda diferente da fala; nome de personagem trocado; erro de
português; gancho que só entende quem já conhece a obra; spoiler do final logo no começo sem intenção; marca d'água
de site/scan ou legenda queimada da fonte visível.""",
    "retencao": """DIRETOR DE RETENÇÃO (YouTube, vídeo longo). O gancho dos primeiros segundos faz a pessoa ficar?
Há um motivo para continuar assistindo a cada trecho (pergunta aberta, virada, revelação)? A tarja de capítulo, o
CTA e o nome do narrador (quando há revezamento) ajudam ou atrapalham? Há sangue/gore em excesso (risco de
desmonetização)? Aparece a mascote/CTA no meio? Diga as 3 mudanças de MAIOR impacto na retenção (concretas: o quê,
em qual trecho, como).""",
}


def _ff(args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True, capture_output=True, timeout=120)


def quadros_e_movimento(mp4, pasta, cenas):
    """3 quadros por cena (20/50/80%) + folha.jpg; devolve (itens para o júri, % de movimento por cena)."""
    from PIL import Image, ImageChops, ImageStat
    pasta.mkdir(parents=True, exist_ok=True)
    itens, ims, mov, pcts = [], [], [], []
    for c in cenas:
        for frac in (0.2, 0.5, 0.8):
            seg = round(c["ini"] + (c["fim"] - c["ini"]) * frac, 2)
            nome = f"q{len(itens) + 1:02d}.jpg"
            _ff(["-ss", f"{seg}", "-i", str(mp4), "-frames:v", "1", "-vf", "scale='min(960,iw)':-2", "-q:v", "3",
                 str(pasta / nome)])
            itens.append(f"{nome}: trecho {c['n']} ({c.get('rotulo', '')}), {seg}s, fala/capítulo: \"{c.get('fala', '')}\"")
            im = Image.open(pasta / nome).convert("RGB")
            ims.append(im.resize((480, round(480 * im.height / im.width))))
        dif = sum(ImageStat.Stat(ImageChops.difference(ims[-3].convert("L"), ims[-1].convert("L"))).mean) / 2.55
        pcts.append(round(dif, 1))
        mov.append(f"trecho {c['n']}: mudança de imagem entre 20% e 80% = {dif:.1f}%"
                   + (" -> PARADA (medido)" if dif < MOV_MIN else ""))
    itens.append(f"MOVIMENTO MEDIDO POR TRECHO (abaixo de {MOV_MIN}% = parado):\n" + "\n".join(mov))
    w, h = ims[0].size
    folha = Image.new("RGB", (w * 3, h * len(cenas)))
    for i, im in enumerate(ims):
        folha.paste(im.resize((w, h)), ((i % 3) * w, (i // 3) * h))
    folha.save(pasta / "folha.jpg", quality=88)
    return itens, pcts


def verificar_generico(pasta, itens, foco, texto_foco, descricao, regras_extra="", modelos=None):
    prompt = f"""Você é um VERIFICADOR exigente de {descricao}. Seu foco único: {texto_foco}

Use Read para OLHAR folha.jpg (visão geral, cada linha = um trecho) e depois abra os quadros que precisar em tamanho
maior. Quadros:
{chr(10).join(itens)}
{regras_extra}

Pense com calma e a fundo antes de responder. Seja duro: nota 10 = nível profissional top, sem nenhum defeito do
seu foco. Aponte só problemas reais que você VIU, com o quadro.
Responda SÓ JSON: {{"nota": 0-10, "problemas": [{{"quadro": "q03.jpg", "cena": 1, "gravidade": "grave|media|leve",
"problema": "...", "como_corrigir": "instrução concreta"}}], "elogios": ["o que está bom e deve ficar"]}}"""
    for m, turnos in (modelos or ((MODELO, 30), (MODELO_RESERVA, 40))):
        try:
            r = chamar_json(prompt, pasta, f"verificar_{foco}", max_turnos=turnos, modelo=m)
            return {"foco": foco, "nota": float(r.get("nota") or 0), "problemas": r.get("problemas") or [],
                    "elogios": r.get("elogios") or [], "modelo": m}
        except MotorErro as e:
            print(f"[juri] {foco} com {m} falhou: {str(e)[:150]}", flush=True)
    return None


# ── amostra do longo ──────────────────────────────────────────────────────────────────────────────────────────────
def _dur(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def amostra(mp4, ficha=None, max_caps=8, janela=15.0):
    """Trechos: abertura (0–8 s), 1 por capítulo (30 s depois do começo dele) e o final (últimos 12 s)."""
    dur = _dur(mp4)
    caps = []
    if ficha and (Path(ficha) / "capitulos.json").exists():
        caps = json.loads((Path(ficha) / "capitulos.json").read_text(encoding="utf-8"))
    if len(caps) < 2:  # sem capítulos: divide em 6 partes iguais
        caps = [[dur * i / 7, f"parte {i}"] for i in range(1, 7)]
    passo = max(1, -(-len(caps) // max_caps))
    cenas = [{"n": 1, "ini": 0.5, "fim": 8.0, "rotulo": "abertura", "fala": "gancho de abertura"}]
    for t, titulo in caps[::passo][:max_caps]:
        ini = min(float(t) + 30, dur - janela - 15)
        if ini > cenas[-1]["fim"]:
            cenas.append({"n": len(cenas) + 1, "ini": ini, "fim": ini + janela, "rotulo": "capítulo", "fala": titulo})
    cenas.append({"n": len(cenas) + 1, "ini": dur - 12, "fim": dur - 0.5, "rotulo": "final", "fala": "fim do vídeo"})
    return cenas, dur


def julgar(mp4, ficha=None, so_movimento=False, modelos=None):
    """modelos = [(id, max_turnos), ...] em ordem (melhorador_longo passa o Argon primeiro); padrão = 3.8 high + reserva."""
    mp4 = Path(mp4)
    pasta = Path(tempfile.mkdtemp(prefix="juri_longo_", dir=str(AQUI)))
    cenas, dur = amostra(mp4, ficha)
    itens, pcts = quadros_e_movimento(mp4, pasta, cenas)
    res = {"video": mp4.name, "em": datetime.now().isoformat(timespec="seconds"), "duracao_s": round(dur),
           "trechos": len(cenas), "movimento": pcts, "parados": sum(1 for p in pcts if p < MOV_MIN), "pasta": str(pasta)}
    if not so_movimento:
        render = {}
        if ficha and (Path(ficha) / "render.json").exists():
            render = json.loads((Path(ficha) / "render.json").read_text(encoding="utf-8"))
        extra = (f"Contexto: recap LONGO de manhwa em português ({dur / 60:.0f} min), narrado com voz clonada"
                 + (f"; revezamento de narradores: {render.get('vozes_lista')}" if render.get("vozes_lista") else "")
                 + ". Os quadros são uma AMOSTRA (abertura, 1 trecho por capítulo e o final), não o vídeo inteiro.")
        with ThreadPoolExecutor(4) as ex:
            votos = list(ex.map(lambda kv: verificar_generico(pasta, itens, kv[0], kv[1],
                                                              "um recap LONGO de manhwa no YouTube (16:9)", extra,
                                                              modelos),
                                VERIFICADORES_ENTRETENIMENTO.items()))
        votos = [v for v in votos if v]
        res["juri"] = votos
        res["nota"] = round(sum(v["nota"] for v in votos) / len(votos), 2) if votos else None
    destino = (Path(ficha) if ficha else pasta) / "juri.json"
    destino.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    EVOLUCAO.parent.mkdir(parents=True, exist_ok=True)
    with EVOLUCAO.open("a", encoding="utf-8") as f:
        f.write(json.dumps({k: res.get(k) for k in ("video", "em", "duracao_s", "nota", "parados", "movimento")}
                           | {"notas": {v["foco"]: v["nota"] for v in res.get("juri", [])}}, ensure_ascii=False) + "\n")
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(1)
    ficha = a[a.index("--ficha") + 1] if "--ficha" in a else None
    r = julgar(a[0], ficha, so_movimento="--so-movimento" in a)
    print(json.dumps({k: r.get(k) for k in ("video", "duracao_s", "nota", "parados", "movimento", "pasta")},
                     ensure_ascii=False))
    for v in r.get("juri", []):
        print(f"- {v['foco']}: {v['nota']}  " + " | ".join(p.get("problema", "")[:90] for p in v["problemas"][:3]))
