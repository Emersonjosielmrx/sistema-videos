# -*- coding: utf-8 -*-
"""vo3_propaganda_rotator — gera clipes de PROPAGANDA no Veo 3 (um por produto)
e os rotaciona no montar_final, SEM tocar na pipeline que ja funciona.

IDEIA (pedido da dona):
  Hoje o short sai como:  INTRO -> VIDEO(criativo) -> TRANSICAO -> PROPAGANDA(card
  estatico + voz) -> OUTRO. A propaganda-card e um slide PNG.

  Aqui a gente adiciona um TERCEIRO tipo de bloco: um CLIPE VEO 3 curto (~8s) que
  e SO o anuncio do produto (cena cinematografica + fala PT-BR curta). A gente
  gera UMA vez, por produto, salva no pool e vai RODANDO eles (rotacao por hash)
  a cada video novo — igual o propaganda_pool_pre_gerada.py ja faz com mp4 fixos.

  Ordem alvo no video final (quando ligado):
     VIDEO(criativo)  ->  VO3-PROPAGANDA(clipe do produto)  ->  PROPAGANDA(card CTA)
  ou seja: entra o criativo (que ja tem os atrativos), depois o clipe-anuncio Veo,
  depois o card/voz que fecha com o WhatsApp na tela.

NAO-DESTRUTIVO:
  - Nada aqui e chamado pelo pipeline por padrao. montar_final so usa se a flag
    com_vo3_propaganda=True for passada (default False).
  - A GERACAO dos clipes e MANUAL/agendada (rode este arquivo direto). Ela usa as
    5 contas novas (conta5..9) via FLOW_PORT, uma por vez, respeitando o mesmo
    gera_auto.py / contas.py que o resto do sistema usa.

USO — gerar o pool (1 clipe por produto TOP, nas 5 contas):
    cd D:\\veo\\beta
    PYTHONUTF8=1 python pos_producao\\vo3_propaganda_rotator.py gerar --tops --n 1

USO — escolher um clipe pra um video (rotacao), no codigo:
    from vo3_propaganda_rotator import escolher_vo3_propaganda
    clip = escolher_vo3_propaganda(produto_id="hermes_call", stem="video123")
"""
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent            # D:\veo\beta
_POS = _BASE / "pos_producao"
_GERA_AUTO = _BASE / "gera_auto.py"
_PRODUTOS_JSON = _POS / "assets" / "produtos.json"
# 2026-08-01: pool de propaganda vo3 agora mora em D:\hipercool-materiais\veo\
# (junto do resto do material). Mantem subpastas vo3/ e vo3_lateral/ pra
# nao misturar orientacao. Aponta via centralizar_publicar pra nao hardcodar.
import sys as _sys
_sys.path.insert(0, str(_POS))
import centralizar_publicar as _cp
_POOL_VO3 = _cp.DIR_PROP_VEO3 / "vo3"
_POOL_VO3.mkdir(parents=True, exist_ok=True)
# Pool LATERAL (16:9) — pra recap de anime deitado. Separado do vertical
# pra rotacao nunca misturar orientacao.
_POOL_VO3_LAT = _cp.DIR_PROP_VEO3 / "vo3_lateral"
_POOL_VO3_LAT.mkdir(parents=True, exist_ok=True)


def _pool_dir(orientacao="9:16"):
    return _POOL_VO3_LAT if str(orientacao).replace(" ", "") == "16:9" else _POOL_VO3
_FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"

sys.path.insert(0, str(_BASE))

# Contas NOVAS dedicadas a propaganda (as 5 que a dona separou). session->port
# vem de contas.py (fonte unica); aqui so listamos QUAIS usar pra propaganda,
# pra nao concorrer com a geracao de conteudo das contas antigas.
# Contas NOVAS de 30/07 (as 5 que a dona cadastrou) — as antigas conta5..9
# esgotaram no Veo. Estas tem credito fresco. session->port vem de contas.py.
# 12/10/2026: emerson2029 (bloqueada por idade no Flow) saiu; inovaremanga virou inovaremanhwaverseesp (mesma conta).
# Nome que nao esta em contas.py cairia na porta 9250 da seebotsia (fallback de contas.porta_de).
# VO-06 (16/10): a lista fixa (emerson2030, inovaremanhwaverseesp, inovaremanhwabr, emersoncunha) nao existe mais no
# contas.py - todas cairiam na porta da seebotsia com o perfil errado. Fonte unica = contas.py: quem tiver
# "papel": "propaganda"; sem nenhuma marcada, as sessoes ativas do gerador.
def _contas_propaganda():
    try:
        import contas
        marcadas = [c["session"] for c in contas.CONTAS if c.get("papel") == "propaganda"]
        return marcadas or [s["session"] for s in contas.SESSOES]
    except Exception:
        return []


_CONTAS_PROPAGANDA = _contas_propaganda()


def _carregar_produtos() -> list[dict]:
    cat = json.loads(_PRODUTOS_JSON.read_text(encoding="utf-8"))
    return cat.get("produtos", [])


def _produtos_top() -> list[dict]:
    return [p for p in _carregar_produtos() if p.get("prioridade") == "top"]


# ---------------------------------------------------------------------------
# PROMPT do anuncio Veo por produto.
# Padrao PROMPTS_NICHOS_PT.md: cena cinematografica + fala LITERAL entre aspas +
# "spoken in Brazilian Portuguese" + 9:16. Fala CURTA (1 linha) senao o Veo
# embola / cai pro ingles. A fala sai do cta_curto (curto e ja pensado pra voz).
# ---------------------------------------------------------------------------
# cenas por "tag" do produto (visual que combina com o que ele faz).
_CENAS = {
    "hermes":   "A sleek smartphone on a desk glowing with a green WhatsApp call ringing by itself, holographic soundwaves of a human voice rising from it, modern office at blue hour, cinematic product shot",
    "avatar":   "A glowing digital human avatar forming from particles in front of a ring light, phone recording it posting to social media, futuristic creator studio, warm cinematic light",
    "followup": "A phone screen showing WhatsApp chats lighting up one by one as an AI reactivates cold leads, coins turning into a rising sales graph, clean fintech cinematic look",
    "superchat": "A single dashboard screen merging WhatsApp, Telegram and Instagram chat bubbles into one AI hub, calm control-room lighting, sleek SaaS cinematic product shot",
    "agenda":   "A calendar filling itself with confirmed appointments automatically, a phone sending confirmation messages on WhatsApp, clean clinic reception, soft cinematic light",
    "vitrine":  "A friendly AI shopping assistant floating in a bright online store, product cards appearing and being recommended to a customer on WhatsApp, cinematic e-commerce look",
    "conteudo": "A content machine turning one idea into a blog post, a podcast waveform and social posts flying out automatically, creative studio, energetic cinematic light",
    "carrinho": "An abandoned shopping cart on a phone screen, an AI message arriving on WhatsApp and the customer returning to finish the purchase, warm cinematic e-commerce look",
    "agente":   "A calm AI personal agent working on multiple floating screens doing research, scheduling and follow-ups for a relaxed person, futuristic cinematic home office",
}
_CENA_DEFAULT = "A modern cinematic product commercial with a glowing AI theme, sleek gradient background, professional lighting, vertical 9:16"


def montar_prompt(produto: dict, orientacao: str = "9:16") -> str:
    """Monta o prompt Veo do anuncio. Usa o multi-agente de comerciais
    (comercial_agents) pra garantir PESSOA FALANDO (lip-sync) — resolve o bug
    do 'so telefone tocando'. Cai no prompt fixo antigo se o multi-agente falhar.
    orientacao: '9:16' (shorts, default) ou '16:9' (lateral/deitado do recap)."""
    _lat = str(orientacao).replace(" ", "") == "16:9"
    _fmt = "horizontal 16:9" if _lat else "vertical 9:16"

    def _garante_fmt(p: str) -> str:
        """O LLM as vezes ignora o pedido de aspecto. Crava no fim do prompt
        pra o Veo enquadrar certo (o FLOW_ASPECT ja forca no Flow, isto reforca).
        VO-02 (16/10): e nada escrito na tela - o Veo erra texto; nome do produto entra depois, pelo card."""
        if "16:9" not in p and "9:16" not in p:
            p = f"{p.rstrip('. ')}. {_fmt}, 8 seconds."
        if "on-screen text" not in p:
            p = f"{p.rstrip('. ')}. No subtitles, no captions, no on-screen text."
        return p

    # 1) tentativa PRINCIPAL: multi-agente projeta o comercial (fala falada)
    try:
        from comercial_agents import projetar_comercial
        r = projetar_comercial(produto, orientacao=orientacao)
        if r and r.get("prompt"):
            return _garante_fmt(r["prompt"])
    except Exception as e:
        print(f"[vo3-prop] multi-agente falhou, usando prompt fixo: {str(e)[:80]}",
              flush=True)

    # 2) FALLBACK: prompt fixo (com pessoa falando, nao 'narrator' off)
    tag = (produto.get("tag") or "").lower()
    cena = _CENAS.get(tag, _CENA_DEFAULT)
    fala = (produto.get("cta_curto") or produto.get("nome") or "").strip().rstrip(".")
    # numero de whatsapp NAO vai na fala (o Veo erra numero); fica no card depois.
    return _garante_fmt(
        f"A person looks directly at the camera and says out loud in Brazilian "
        f"Portuguese: \"{fala}.\", lips moving naturally, clear voice. {cena}. "
        f"Upbeat modern advertising music, {_fmt}, 8 seconds."
    )


_FOTOS_DIR = os.environ.get("VEO_FOTOS", str(_BASE.parent / "fotos"))


def _escolher_foto(stem: str = "") -> str | None:
    """Escolhe UMA foto da dona (image-to-video) de forma estavel por stem.
    Respeita as fotos bloqueadas por direitos (reusa a checagem do gerador).
    Retorna caminho absoluto ou None se nao houver fotos."""
    try:
        fotos = []
        # raiz + subpastas por tema (16/10: 299 das 305 da raiz tem a marca do Grok, que passa para o clipe)
        for pasta in [Path(_FOTOS_DIR)] + [p for p in Path(_FOTOS_DIR).iterdir() if p.is_dir() and not p.name.startswith("_")]:
            for ext in ("*.jpg", "*.jpeg", "*.png"):
                fotos.extend(pasta.glob(ext))
        # tira as bloqueadas e as com marca de IA (mesmas fontes que o cron_gerar usa)
        try:
            from cron_gerar_video_llm import _listar_fotos_bloqueadas, _fotos_com_marca
            bloq = {os.path.normcase(f) for f in _listar_fotos_bloqueadas()} | _fotos_com_marca()
            fotos = [f for f in fotos if os.path.normcase(str(f)) not in bloq]
        except Exception:
            return None  # sem como saber quais tem marca: melhor nao gerar (o clipe sairia com "Grok")
        if not fotos:
            return None
        fotos = sorted(fotos)
        h = int(hashlib.md5((stem or "x").encode("utf-8")).hexdigest(), 16)
        return str(fotos[h % len(fotos)])
    except Exception:
        return None


def _porta_da_conta(session: str) -> str:
    try:
        from contas import porta_de
        return porta_de(session)
    except Exception:
        return "9290"


def _ja_tem(produto_id: str, idx: int, orientacao: str = "9:16") -> Path | None:
    p = _pool_dir(orientacao) / f"{produto_id}_{idx}.mp4"
    return p if p.exists() and p.stat().st_size > 10_000 else None


def gerar_um(produto: dict, conta: str, idx: int = 1,
             timeout_s: int = 900, forcar: bool = False,
             orientacao: str = "9:16") -> Path | None:
    """Gera UM clipe de propaganda Veo do produto na conta dada.
    Retorna o Path do mp4, ou None se falhou/pausado/sem credito.
    Idempotente: se ja existe e nao forcar, reusa.
    orientacao: '9:16' (shorts, default) ou '16:9' (lateral/deitado)."""
    _lat = str(orientacao).replace(" ", "") == "16:9"
    pid = produto.get("id", "generico")
    saida = _pool_dir(orientacao) / f"{pid}_{idx}.mp4"
    if not forcar:
        existente = _ja_tem(pid, idx, orientacao)
        if existente:
            print(f"[vo3-prop] ja existe, reuso: {existente.name}", flush=True)
            return existente

    prompt = montar_prompt(produto, orientacao=orientacao)
    porta = _porta_da_conta(conta)
    env = dict(os.environ)
    env["FLOW_PORT"] = str(porta)
    # CRITICO: passar a SESSAO e o PERFIL da conta. Sem isso o gera_auto abre
    # o perfil default (seebotsia) na porta da conta nova -> Chrome sem login
    # -> "Target page closed". FLOW_SESSION liga o profile certo via PROFILE_MAP.
    env["FLOW_SESSION"] = conta
    try:
        from contas import profile_de
        env["FLOW_PROFILE"] = profile_de(conta)
    except Exception:
        pass
    env["FLOW_ASPECT"] = "16:9" if _lat else "9:16"
    env["FLOW_DURATION"] = "8S"
    env.setdefault("PYTHONUTF8", "1")

    # FOTO da dona como primeiro frame (image-to-video): o comercial usa a
    # PESSOA REAL dela, nao um ator generico. gera_auto recebe em argv[3].
    foto = _escolher_foto(stem=f"{pid}_{idx}")

    print(f"[vo3-prop] gerando {pid}_{idx} em '{conta}' (porta {porta})", flush=True)
    print(f"           prompt: {prompt[:120]}...", flush=True)
    if foto:
        print(f"           foto (image-to-video): {Path(foto).name}", flush=True)
    try:
        cmd = [sys.executable, "-u", str(_GERA_AUTO), prompt, str(saida)]
        if foto:
            cmd.append(str(foto))
        r = subprocess.run(
            cmd, env=env, capture_output=True, text=True, timeout=timeout_s,
            cwd=str(_BASE))
    except subprocess.TimeoutExpired:
        print(f"[vo3-prop] TIMEOUT {pid}_{idx} (conta {conta})", flush=True)
        return None

    # exit codes do gera_auto: 2=creditos, 3=sessao, 4=direitos, 5=pausado
    if r.returncode == 5:
        print("[vo3-prop] SISTEMA_PAUSADO — abortando geracao", flush=True)
        return None
    if r.returncode == 2:
        print(f"[vo3-prop] CREDITOS_ESGOTADOS na conta {conta}", flush=True)
        return None
    if r.returncode == 3:
        print(f"[vo3-prop] SESSAO_EXPIRADA na conta {conta} — precisa relogin", flush=True)
        return None
    if r.returncode != 0 or not saida.exists():
        tail = (r.stderr or r.stdout or "")[-300:]
        print(f"[vo3-prop] FALHOU {pid}_{idx} rc={r.returncode}: {tail}", flush=True)
        return None
    # VO-03 (16/10): o clipe so entra no pool se presta - o mesmo porteiro dos videos (arquivo inteiro e fala pedida,
    # em pt). A fala pedida e o texto entre aspas duplas do prompt.
    try:
        import re as _re
        sys.path.insert(0, str(_BASE))
        from validar_video import validar, resumo
        v = validar(saida, duracao_esperada=8)
        motivo = None if v.get("ok") else resumo(v)
        m = _re.search(r'"([^"]{6,})"', prompt)
        if not motivo and m:
            from conferir_fala import conferir
            c = conferir(saida, m.group(1).strip().rstrip("."))
            if c.get("ok") is False:
                motivo = c.get("motivo")
        if motivo:
            print(f"[vo3-prop] REPROVADO {pid}_{idx}: {motivo} - fora do pool", flush=True)
            saida.unlink(missing_ok=True)
            return None
    except Exception as e:  # a conferencia nunca derruba a geracao; so fica no log
        print(f"[vo3-prop] conferencia nao rodou ({str(e)[:80]}) - entrando assim mesmo", flush=True)
    print(f"[vo3-prop] OK -> {saida}", flush=True)
    return saida


def gerar_pool(produtos: list[dict], n_por_produto: int = 1,
               forcar: bool = False, orientacao: str = "9:16") -> dict:
    """Gera n clipes por produto, distribuindo pelas 5 contas de propaganda.
    Serial (uma conta por vez) porque o Flow serializa o Chrome mesmo.
    orientacao: '9:16' (shorts) ou '16:9' (lateral/deitado).
    Retorna {produto_id: [Path, ...]}."""
    feitos = {}
    ci = 0
    for prod in produtos:
        pid = prod.get("id", "generico")
        feitos[pid] = []
        for idx in range(1, n_por_produto + 1):
            conta = _CONTAS_PROPAGANDA[ci % len(_CONTAS_PROPAGANDA)]
            ci += 1
            clip = gerar_um(prod, conta, idx=idx, forcar=forcar,
                            orientacao=orientacao)
            if clip:
                feitos[pid].append(clip)
            # respiro entre renders pra nao martelar o Flow
            time.sleep(3)
    return feitos


# ---------------------------------------------------------------------------
# ROTACAO — escolhe um clipe do pool pra um video (por produto, ou geral).
# ---------------------------------------------------------------------------
def _orientacao_ok(p: Path, orientacao: str) -> bool:
    """O clipe esta mesmo na orientacao pedida? (VO-01, 16/10: hermes_call_1.mp4 era 1280x720 dentro da pasta 9:16 -
    movido para vo3_lateral; daqui para frente, deitado na pasta vertical e ignorado.)"""
    import subprocess
    try:
        r = subprocess.run([r"D:\hipercool-materiais\bin\ffprobe.exe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0", str(p)],
                           capture_output=True, text=True, timeout=20)
        w, h = (int(x) for x in r.stdout.strip().split(",")[:2])
    except Exception:
        return False
    return h > w if orientacao == "9:16" else w > h


def _clipes_do_produto(produto_id: str, orientacao: str = "9:16") -> list[Path]:
    return sorted(p for p in _pool_dir(orientacao).glob(f"{produto_id}_*.mp4") if _orientacao_ok(p, orientacao))


def escolher_vo3_propaganda(produto_id: str | None = None,
                            stem: str = "", orientacao: str = "9:16") -> Path | None:
    """Escolhe (rotaciona) um clipe de propaganda Veo.
    - Se produto_id dado e tem clipes dele -> rotaciona entre os dele.
    - Senao -> rotaciona entre TODOS os clipes do pool da orientacao.
    orientacao: '9:16' (shorts, default) ou '16:9' (lateral/deitado).
    Rotacao estavel por hash do stem (mesmo video -> mesmo clipe)."""
    pool = _clipes_do_produto(produto_id, orientacao) if produto_id else []
    if not pool:
        pool = sorted(p for p in _pool_dir(orientacao).glob("*.mp4") if _orientacao_ok(p, orientacao))
    if not pool:
        return None
    h = int(hashlib.md5((stem or produto_id or "x").encode("utf-8")).hexdigest(), 16)
    return pool[h % len(pool)]


def _cli():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        print("\nComandos (use --lateral pra 16:9 do recap deitado):")
        print("  gerar --tops [--n N] [--forcar] [--lateral]   pool p/ produtos TOP")
        print("  gerar --todos [--n N] [--forcar] [--lateral]  pool p/ TODOS")
        print("  gerar --produto <id> [--n N] [--lateral]      pool de 1 produto")
        print("  listar [--lateral]                            mostra o pool")
        return

    cmd = args[0]
    orient = "16:9" if "--lateral" in args else "9:16"

    if cmd == "listar":
        pool = _pool_dir(orient)
        clips = sorted(pool.glob("*.mp4"))
        print(f"{len(clips)} clipe(s) no pool {orient} ({pool}):")
        for c in clips:
            print(f"  {c.name:40} {c.stat().st_size//1024:>6} KB")
        return

    if cmd == "gerar":
        n = 1
        if "--n" in args:
            try:
                n = int(args[args.index("--n") + 1])
            except Exception:
                n = 1
        forcar = "--forcar" in args
        if "--produto" in args:
            pid = args[args.index("--produto") + 1]
            prods = [p for p in _carregar_produtos() if p.get("id") == pid]
        elif "--todos" in args:
            prods = _carregar_produtos()
        else:  # default: tops
            prods = _produtos_top()
        print(f"[vo3-prop] gerando pool {orient}: {len(prods)} produto(s) x {n} "
              f"clipe(s) nas contas {_CONTAS_PROPAGANDA}")
        feitos = gerar_pool(prods, n_por_produto=n, forcar=forcar, orientacao=orient)
        ok = sum(len(v) for v in feitos.values())
        print(f"\n[vo3-prop] concluido: {ok} clipe(s) gerado(s)/reusado(s).")
        for pid, lst in feitos.items():
            print(f"  {pid:20} {len(lst)} clipe(s)")
        return

    print(f"comando desconhecido: {cmd}. use --help.")


if __name__ == "__main__":
    _cli()
