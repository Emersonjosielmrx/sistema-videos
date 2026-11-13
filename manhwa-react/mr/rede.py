"""Rede de canais: distribui os videos prontos entre os canais ativos da rede e agenda 1 por canal por dia.

Fonte unica dos canais: D:/postador-de-videos/config/rede_canais.json (nicho, persona, regras, horarios, credenciais).
Fontes de video: Shorts do manhwa-react (shorts/ e cortes/ em hipercool-materiais) + historias-em-frames (postar.json)
+ Veo LIMPO (D:/postador-de-videos/bin/limpar_veo.py, sem marca e sem o slide de propaganda/WhatsApp): so nos canais de
  canais_veo_limpo, com a nota minima (pega so a vaga que sobrar depois dos reacts do dono) - pedido do dono 15/10.

Por rodada (manhwareact.py rede):
  1. inventario: videos aprovados e ainda nao postados (publicados.json + postar.json)
  2. notas: o "diretor da rede" (LLM) da nota 0-10 de encaixe de cada video em cada canal (cache em work/rede_notas.json)
  3. distribuicao: cada canal com vaga no dia recebe o video de maior nota (>= nota_min), cada video vai para UM canal so
     (nunca o mesmo video em 2 canais - foi o padrao que derrubou a rede antiga)
  4. marca: se o video foi renderizado com o @ de outro canal (ou e historia com @InovareStories), o canto e coberto e o @ certo entra
  5. agente do canal (LLM com a persona/regras do canal) reescreve titulo, descricao, tags e o comentario do canal
  6. horario: um dos horarios do canal (rede_canais.json); o agendador explora todos e depois prefere o que rende mais views em 48 h
     (_analise/rede_horarios.json, gerado pelo painel)
  7. upload agendado (private + publishAt) via politica.postar_youtube: vale a politica inteira (parada, bloqueio, cota, aprovacao)
  8. depois que o video abre, o canal posta a pergunta como 1o comentario (rodada --comentarios, a cada 30 min)
"""
import hashlib
import json
import random
import re
import shutil
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from .common import log, load_json, save_json, ffmpeg, ffprobe_json
from . import publish as PB
from .llm import ask_json

REDE_PADRAO = {
    "historias_dir": "D:/hipercool-materiais/historias-em-frames",
    "postados_historias": "D:/hipercool-materiais/_postados/historias",
    "aprendizado": "D:/postador-de-videos/_analise/rede_aprendizado.json",
    "janela_upload_h": 3,
    "nota_min": 6,
    "bonus_canal_original": 1.5,
    "antecedencia_min": 30,
    "veo_limpos_dir": "D:/hipercool-materiais/veo/limpos",
    "canais_veo_limpo": ["inventoreact", "manhwareact"],
    # 16/10/2026 (itens DS-01 e DS-02 de D:\veo\docs\PLANO_MELHORIAS_VEO.md):
    # veo_max_fila     quantos limpos entram na disputa por rodada. Ha 227 aprovados;
    #                  mandar todos ao diretor seria ~12 chamadas de LLM numa rodada
    #                  so. Entram os mais novos — a fila e bem maior que as vagas.
    # veo_max_dia      teto de videos do Veo na REDE INTEIRA por dia (nao por canal).
    #                  Fica baixo de proposito ate haver medida de 48 h do veo limpo.
    # veo_pelo_diretor True = o veo concorre com nota do diretor, restrita aos canais
    #                  de canais_veo_limpo. False = volta ao de antes (nota fixa =
    #                  nota_min, que so pegava a vaga que sobrasse).
    "veo_max_fila": 40,
    "veo_max_dia": 2,
    "veo_pelo_diretor": True,
    # 16/10/2026 (dono: "publique apenas nos 2 canais ... 3 por dia e aumentando"): o Veo limpo tem VAGAS PROPRIAS nos
    # canais de canais_veo_limpo, ALEM da vaga do react (que segue 1/dia, max_dia do canal), e sai da disputa da vaga do
    # react (veo_max_dia/veo_pelo_diretor acima so valem com veo_rampa vazia, o jeito de antes).
    # veo_rampa        [desde, Veo por canal por dia]: vale o ultimo cuja data ja chegou (3 -> 4 -> 5, 1 a mais por semana).
    # veo_horarios     na ordem em que entram (3/dia = os 3 primeiros), longe dos horarios do react; horario de hoje que
    #                  ja passou publica a partir de agora (antecedencia_min), veo_intervalo_min longe de outro video.
    # veo_dias_frente  dias (hoje incluso) que o Veo ja fica agendado no YouTube; cada rodada completa o que faltar.
    "veo_rampa": [["2026-10-16", 3], ["2026-10-23", 4], ["2026-10-30", 5]],
    "veo_horarios": ["15:00", "21:45", "09:00", "13:40", "23:00"],
    "veo_dias_frente": 2,
    "veo_intervalo_min": 60,
    # veo_uploads_dia  teto de UPLOADS do Veo por canal por dia (contados no ledger pela hora do upload, nao pela de
    #                  publicar); 0 = o degrau do dia na veo_rampa. 16/10: sem ele o Veo dos 3 dias adiantados subiu 8
    #                  por canal num dia so, o YouTube cortou (uploadLimitExceeded) e o react do dono das 18:53 e o
    #                  completo das 20:40 do ManhwaReact nao subiram.
    "veo_uploads_dia": 0,
}


def _rc(cfg):
    out = dict(REDE_PADRAO)
    out.update(cfg.get("rede") or {})
    return out


def _num(R, chave, padrao, tipo=int):
    """Numero da config, tolerante a lixo. Um "veo_max_dia": "dois" no config.json
    derrubava a rodada inteira dos 12 canais com ValueError (nada era postado)."""
    v = R.get(chave, padrao)
    if v is None:
        return padrao
    try:
        return tipo(v)
    except (TypeError, ValueError):
        log(f"rede: config 'rede.{chave}' = {v!r} nao e numero; usando {padrao}")
        return padrao


def _seguro(iid):
    return re.sub(r"[^\w.-]", "_", iid)


def _work(cfg, *partes):
    p = Path(cfg["paths"]["work"]).joinpath(*partes)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


# ─────────────────────────── canais ─────────────────────────────────────────
def canais(cfg, politica):
    """Canais ATIVOS da rede, com a credencial principal e os campos do padrao preenchidos."""
    mapa = politica.rede()
    padrao = mapa.get("padrao", {})
    creds = {c["id"]: c for c in politica.carregar_creds()}
    out = []
    for rc in mapa.get("canais", []):
        if rc.get("status") != "ativo":
            continue
        cred = next((creds[i] for i in rc.get("creds", []) if i in creds), None)
        if not cred:
            log(f"rede: {rc['nome']} sem credencial em youtube_canais.json - pulado")
            continue
        c = dict(padrao)
        c.update(rc)
        c["cred"] = cred
        out.append(c)
    return out


# ─────────────────────────── inventario ─────────────────────────────────────
def _reabertos_path(cfg):
    return Path(cfg["publish"]["posted_dir"]) / "reabertos.json"


def _reabertos(cfg):
    p = _reabertos_path(cfg)
    return load_json(p) if p.exists() else {}


def reabrir(cfg, stem, video_antigo, motivo):
    """Video que foi postado no canal errado e ficou privado: volta a poder ser postado (no canal certo)."""
    reab = _reabertos(cfg)
    ent = reab.get(stem) or {}
    ent.update({"video_antigo": video_antigo, "motivo": motivo, "em": datetime.now().isoformat(timespec="seconds")})
    reg = PB._carregar_registro(cfg)
    if stem in reg and reg[stem].get("video_id") == video_antigo:
        ent["registro_antigo"] = reg.pop(stem)
        save_json(reg, PB._registro_path(cfg))
    reab[stem] = ent
    save_json(reab, _reabertos_path(cfg))


def _postados(cfg, politica):
    """Ids (stem/hist:pasta) ja postados: registro do projeto + ledger do postador (menos os reabertos)."""
    reg = PB._carregar_registro(cfg)
    reab = _reabertos(cfg)
    feitos = set(reg)
    for r in politica._ler_ledger():
        stem = Path(r.get("arquivo") or "").stem
        if stem in reab and r.get("video_id") == reab[stem].get("video_antigo"):
            continue
        feitos.add(stem)
    return reg, feitos


def _resumo_react(cfg, it):
    d = it["dados"]
    base = re.sub(r"_p\d+$", "", it["mp4"].stem)
    ed_p = Path(cfg["paths"]["work"]) / base / "editorial.json"
    topico, obra = "", ""
    if ed_p.exists():
        try:
            ed = load_json(ed_p)
            topico, obra = ed.get("topic") or "", ed.get("work") or ""
        except Exception:  # noqa: BLE001
            pass
    return {"titulo": d.get("titulo", ""), "tema": topico, "obra": obra, "tags": (d.get("tags") or [])[:10],
            "descricao": (d.get("descricao") or "")[:300]}


def inventario(cfg, politica, so_aprovados=True):
    reg, feitos = _postados(cfg, politica)
    aprov = politica.ler_json(politica.APROV_FILE, {})
    itens, esperando = [], []
    # 1. Shorts do manhwa-react
    for it in PB.prontos(cfg):
        iid = it["mp4"].stem
        if iid in feitos:
            continue
        item = {"id": iid, "fonte": "react", "mp4": it["mp4"], "json": it["json"], "dados": it["dados"],
                "slug_origem": it["slug"], "sintetico": False, "pb": it, "resumo": _resumo_react(cfg, it)}
        (itens if (not so_aprovados or politica.aprovado(it["mp4"], aprov)) else esperando).append(item)
    # 2. historias-em-frames (Shorts narrados feitos com IA, marca @InovareStories no canto)
    hdir = Path(_rc(cfg)["historias_dir"])
    if hdir.exists():
        for pj in sorted(hdir.rglob("postar.json")):
            try:
                d = load_json(pj)
            except Exception:  # noqa: BLE001
                continue
            mp4 = pj.parent / d.get("arquivo", "")
            iid = f"hist:{pj.parent.name}"
            if d.get("categoria") != "historias" or d.get("pronto") is False or not mp4.is_file():
                continue
            if iid in feitos or d.get("posted_url"):
                continue
            item = {"id": iid, "fonte": "historias", "mp4": mp4, "json": pj, "dados": d, "slug_origem": None,
                    "sintetico": True, "resumo": {"titulo": d.get("titulo", ""), "tema": d.get("tema", ""),
                                                  "genero": d.get("genero", ""), "tags": (d.get("tags") or [])[:8]}}
            (itens if (not so_aprovados or politica.aprovado(mp4, aprov)) else esperando).append(item)
    # 3. Veo LIMPO (sem a marca @InovareStories e sem o slide de propaganda/WhatsApp que derrubou os canais antigos):
    #    so nos canais de canais_veo_limpo; o limpar_veo.py ja aprova os de estrutura padrao (os outros ficam em 'esperando')
    R = _rc(cfg)
    vdir = Path(R["veo_limpos_dir"])
    if vdir.exists() and R.get("canais_veo_limpo"):
        # Os mais NOVOS primeiro: a fila de limpos (241 em 16/10) e muito maior que
        # as vagas do dia, e mandar todos ao diretor custaria ~12 chamadas de LLM
        # numa rodada so (veo_max_fila corta isso).
        # A data esta no NOME (tema_AAAAMMDD_HHMMSS.json), entao ordenar a string
        # inteira ordena por TEMA, nao por data: assim os 6 limpos mais novos caiam
        # na posicao ~200 e nunca entravam. Ordena pela data do nome; quem nao tem
        # data no nome (v1, teste1, stand-up_20260706) vai pelo mtime.
        def _quando(p):
            """Data de GERACAO do clipe, tirada do nome (tema_AAAAMMDD_HHMMSS).

            Sem data no nome (v1, teste1, v2_916: sobras de teste) conta como o
            mais antigo possivel, para ir ao fim da fila. Nao use o mtime aqui: o
            limpar_veo reescreve o json e todo arquivo antigo pareceria novinho —
            foi o que aconteceu no 1o teste, com os 'teste*' encabecando a fila.
            """
            m = re.search(r"(\d{8}_\d{6})", p.name)
            return m.group(1) if m else "00000000_000000"

        # O corte vale so para a DISPUTA (quem vai ao diretor). A fila de aprovacao
        # humana ('esperando') continua vendo TUDO: com o corte aplicado aos dois,
        # um limpo novo podia nunca aparecer no 'manhwareact.py rede --aprovar'.
        # Percorrer os 241 jsons e barato; caro e so a chamada de LLM.
        veo_max_fila = _num(R, "veo_max_fila", 40)
        veo_itens, veo_esperando = [], []
        for jp in sorted(vdir.glob("*.json"), key=_quando, reverse=True):
            try:
                d = load_json(jp)
            except Exception:  # noqa: BLE001
                continue
            mp4 = jp.with_suffix(".mp4")
            iid = f"veo:{mp4.stem}"
            # marca do TikTok e arquivo que nao decodifica (detectores do limpar_veo, 16/10: 28 dos 240) nunca vao pro
            # YouTube: nem entram na fila de aprovacao
            rev = str(d.get("revisar") or "")
            if (not mp4.is_file() or iid in feitos or d.get("posted_url")
                    or any(x in rev for x in ("TikTok", "quebrado", "marca d'agua", "moldura", "clipe repetido"))):
                continue  # + marca d'agua de IA (Grok/Veo/Sora), bruto montado com moldura/legenda e clipe repetido (16/10)
            fala = (d.get("fala") or "").strip()
            tema = (d.get("tema") or "").replace("_", " ").strip()
            titulo = (re.split(r"[.!?]", fala)[0].strip() or tema)[:80]  # reserva se o agente do canal falhar
            item = {"id": iid, "fonte": "veo", "mp4": mp4, "json": jp, "slug_origem": None, "sintetico": True,
                    "so_canais": list(R["canais_veo_limpo"]),
                    "dados": {"titulo": titulo, "descricao": fala, "tags": [tema] if tema else []},
                    # o diretor da nota por isto: quanto mais concreto o assunto, melhor
                    # ele encaixa o video no nicho certo (antes o veo nem passava por ele).
                    "resumo": {"formato": "Short curto feito com IA (Veo): uma cena gerada por IA com a fala abaixo; NAO e react",
                               "tema": tema, "fala": fala, "duracao_s": d.get("duracao"),
                               "assunto": (fala or tema)[:200]}}
            if not so_aprovados or politica.aprovado(mp4, aprov):
                if len(veo_itens) < veo_max_fila:   # so o que disputa e limitado
                    veo_itens.append(item)
            else:
                veo_esperando.append(item)          # a dona ve todos no --aprovar
        itens += veo_itens
        esperando += veo_esperando
    return itens, esperando


# ─────────────────────────── notas de encaixe (diretor da rede) ─────────────
NOTAS_INSTR = """Voce e o diretor de uma rede de canais de YouTube Shorts em portugues do Brasil. Para cada VIDEO, de uma nota de 0 a 10
para o quanto ele combina com o PUBLICO de cada CANAL (10 = e exatamente o que esse publico procura; 6 = combina bem com um angulo
honesto; 3 = estranho no canal; 0 = nada a ver). Considere o assunto real do video (tema/obra), nao palavras soltas.
Anime/manhwa nao combina com canal de financas, games ou forja, a menos que o assunto do video seja exatamente o do canal
(ex.: anime sobre trader pode ir para investimento). Historia narrada com licao de dinheiro combina com canal de financas.
Varios canais sao de anime com ANGULOS diferentes (romance, luta, isekai/ranking, plot twist, comedia, sombrio, donghua...):
de a nota pelo angulo que o video realmente tem, para cada canal receber o que combina com ele.
Responda SOMENTE JSON: {"<id do video>": {"<slug do canal>": nota, ... (as 6 maiores notas)}, ...}"""


def _hash_canais(chans):
    return hashlib.md5(json.dumps([(c["slug"], c.get("nicho")) for c in chans], ensure_ascii=False).encode()).hexdigest()[:10]


def notas(cfg, itens, chans):
    cache_p = _work(cfg, "rede_notas.json")
    cache = load_json(cache_p) if cache_p.exists() else {}
    h = _hash_canais(chans)
    falta = [it for it in itens if (cache.get(it["id"]) or {}).get("canais") != h]
    ch_txt = "\n".join(f"- {c['slug']}: {c.get('nicho', '')}" for c in chans)
    for i in range(0, len(falta), 20):
        lote = falta[i:i + 20]
        payload = "CANAIS:\n" + ch_txt + "\n\nVIDEOS:\n" + "\n".join(
            f"- id={it['id']} | origem={it['fonte']} | " + json.dumps(it["resumo"], ensure_ascii=False) for it in lote)
        data = ask_json(cfg, NOTAS_INSTR, payload) or {}
        for it in lote:
            n = data.get(it["id"]) or {}
            notas_ok = {}
            for s, v in n.items():
                try:
                    notas_ok[s] = float(v)
                except (TypeError, ValueError):
                    continue
            if not notas_ok and it.get("slug_origem"):
                notas_ok = {it["slug_origem"]: 7.0}  # LLM fora: fica no canal em que foi renderizado
            cache[it["id"]] = {"canais": h, "notas": notas_ok}
        save_json(cache, cache_p)
    return {it["id"]: (cache.get(it["id"]) or {}).get("notas", {}) for it in itens}


def _serie(item):
    """Partes em sequencia (PARTE 1/2, 'parte 2 no perfil') ficam no canal em que foram renderizadas."""
    try:
        return int(item["dados"].get("total_partes") or 1) > 1
    except (TypeError, ValueError):
        return False


def distribuir(cfg, itens, chans, vagas, fome=None, excluir=()):
    """vagas: {slug: n}. Guloso pela maior nota; bonus para o canal em que o video ja foi renderizado e para o canal
    que esta ha mais tempo sem video (fome: {slug: bonus}), para ninguem ficar de fora enquanto outro recebe 2.
    excluir: pares (id, slug) que nao podem (ex.: revisor ja barrou) - a vaga do canal vai para o proximo video."""
    R = _rc(cfg)
    fixos = {it["id"]: it["dados"].get("canal_fixo") for it in itens if it.get("dados", {}).get("canal_fixo")}
    restritos = {it["id"]: it["so_canais"] for it in itens if it.get("so_canais")}
    # 16/10/2026 (item DS-01): o Veo limpo passa a ser avaliado pelo DIRETOR como
    # as outras fontes, em vez de receber nota fixa = nota_min. Com nota fixa ele
    # so pegava a vaga que sobrasse depois de qualquer react, e ficava parado: em
    # 16/10 havia 227 limpos aprovados, 8 canais sem video bom e 1 unico Veo
    # postado desde sempre. A nota do diretor continua RESTRITA aos canais de
    # canais_veo_limpo — quem decide onde o veo pode entrar e a config, nao o LLM.
    pelo_diretor = bool(R.get("veo_pelo_diretor", True))
    avaliar = [it for it in itens if it["id"] not in fixos and (pelo_diretor or it["id"] not in restritos)]
    nt = notas(cfg, avaliar, chans)
    nota_min = _num(R, "nota_min", 6.0, float)
    preferidos = {}  # o que o diretor escolheria se a config deixasse
    for iid, permitidos in restritos.items():
        permitidos = set(permitidos)
        dadas = nt.get(iid) or {}
        so_permitidos = {s: v for s, v in dadas.items() if s in permitidos}
        if so_permitidos:
            # o diretor julgou um canal permitido: vale o que ele disse, inclusive
            # nota baixa (ai o video fica de fora, que e o certo).
            nt[iid] = so_permitidos
        else:
            # O diretor so indicou canais que a config NAO permite. Isso nao e
            # rejeicao do video, e um descompasso entre o que ele acha e o que a
            # dona liberou — entao mantem o comportamento de antes (nota_min) e
            # REGISTRA a preferencia, que e o dado para decidir liberar canal.
            nt[iid] = {s: nota_min for s in permitidos}
            melhor = sorted(dadas.items(), key=lambda x: -x[1])[:1]
            if melhor and melhor[0][1] >= nota_min:
                preferidos[iid] = melhor[0]
    if preferidos:
        # agrupa por canal para o log nao virar uma lista enorme
        por_canal = {}
        for iid, (slug, v) in preferidos.items():
            por_canal.setdefault(slug, []).append(v)
        resumo = ", ".join(f"{s} ({len(vs)} video(s), nota ate {max(vs):.0f})"
                           for s, vs in sorted(por_canal.items(), key=lambda x: -len(x[1])))
        log(f"rede: o diretor encaixaria {len(preferidos)} video(s) do Veo em canais fora de "
            f"canais_veo_limpo: {resumo}. Eles entraram com a nota minima nos canais liberados.")
    validos = {c["slug"] for c in chans}
    fome = fome or {}
    pares = []
    for iid, s in fixos.items():  # canal fixo (ex.: aula do dono): so esse canal, na frente da fila dele
        if s in validos and (iid, s) not in excluir:
            pares.append((99 + fome.get(s, 0), 10, iid, s))
    for it in itens:
        if it["id"] in fixos:
            continue
        for s, v in nt.get(it["id"], {}).items():
            if s not in validos or (it["id"], s) in excluir:
                continue
            if _serie(it) and s != it.get("slug_origem"):
                continue
            bonus = (R["bonus_canal_original"] if s == it.get("slug_origem") else 0) + fome.get(s, 0)
            pares.append((v + bonus, v, it["id"], s))
    pares.sort(key=lambda x: (-x[0], -fome.get(x[3], 0), x[2]))
    por_id = {it["id"]: it for it in itens}
    usados, plano = set(), []
    vagas = dict(vagas)
    # Teto de Veo por rodada de planejamento (item DS-01). Com 2 canais em
    # canais_veo_limpo e max_dia=1 o limite natural ja e 2; isto passa a valer de
    # verdade quando a dona ampliar os canais.
    # ATENCAO: e por RODADA, nao por dia — a tarefa roda de hora em hora e este
    # contador zera a cada chamada. Com mais canais permitidos que o teto, some
    # aqui a contagem do que ja foi agendado hoje (publicados.json).
    # veo_max_dia = 0 PROIBE o veo (era o contrario: o 'or 0' tornava 0 ilimitado,
    # entao quem escrevesse 0 para parar o veo liberava tudo).
    veo_teto = _num(R, "veo_max_dia", 2)
    veo_no_plano = 0
    for _, nota, iid, s in pares:
        if iid in usados or vagas.get(s, 0) <= 0 or nota < nota_min:
            continue
        item = por_id[iid]
        if item.get("fonte") == "veo":
            if veo_no_plano >= veo_teto:
                continue  # a vaga fica para um react/historia
            veo_no_plano += 1
        usados.add(iid)
        vagas[s] -= 1
        plano.append((item, s, nota))
    return plano, vagas


# ─────────────────────────── marca do canal (@ no canto) ────────────────────
def _png_handle(cfg, handle, dst):
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(str(Path(cfg["paths"]["assets"]) / "fonts" / "Montserrat-ExtraBold.ttf"), 34)
    tmp = Image.new("RGBA", (10, 10))
    l, t, r, b = ImageDraw.Draw(tmp).textbbox((0, 0), handle, font=font, stroke_width=2)
    img = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((4 - l, 4 - t), handle, font=font, fill=(255, 255, 255, 170),
                             stroke_width=2, stroke_fill=(0, 0, 0, 170))
    img.save(dst)
    return img.size


def rebrand(cfg, item, canal):
    """Cobre o @ antigo do canto superior direito (desfoque) e escreve o @ do canal de destino. Cache por (video, canal)."""
    dst = _work(cfg, "rede_marca", f"{_seguro(item['id'])}__{canal['slug']}.mp4")
    if dst.exists() and dst.stat().st_mtime >= item["mp4"].stat().st_mtime:
        return dst
    info = ffprobe_json(cfg, item["mp4"])
    vs = next(s for s in info["streams"] if s["codec_type"] == "video")
    W, H = int(vs["width"]), int(vs["height"])
    bw, bh = int(W * 0.5), int(H * 0.055)
    png = dst.with_suffix(".png")
    pw, _ = _png_handle(cfg, canal["handle"], png)
    fc = (f"[0:v]crop={bw}:{bh}:{W - bw}:0,boxblur=22:3[bl];[0:v][bl]overlay={W - bw}:0[v1];"
          f"[v1][1:v]overlay={W - 30 - pw}:26[v]")
    ffmpeg(cfg, ["-y", "-i", str(item["mp4"]), "-i", str(png), "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-threads", "2", "-c:a", "copy",
                 "-movflags", "+faststart", str(dst)])
    log(f"marca: {item['mp4'].name} -> {canal['handle']}")
    return dst


def precisa_marca(item, canal):
    if item["fonte"] in ("historias", "veo"):
        return True
    return item.get("slug_origem") != canal["slug"]


# ─────────────────────────── estrategias (cada canal explora e aprende) ─────
# Cada upload escolhe 1 braco por dimensao (titulo, gancho, comentario, horario). O painel (bin/painel_canais.py) mede o
# video em ~48 h e grava a nota em _analise/rede_aprendizado.json; o canal passa a preferir o que rende, mas continua
# testando (explorar). Pouca amostra no canal -> usa a media da rede inteira como ponto de partida (aprende mais rapido).
ESTRATEGIAS = {
    "titulo": {
        "pergunta": "titulo em forma de PERGUNTA que o publico quer responder (ex.: 'Quem ganha essa luta?')",
        "choque": "titulo de CHOQUE/surpresa, com a palavra mais forte em CAIXA ALTA",
        "curiosidade": "titulo de CURIOSIDADE que abre um misterio sem entregar o final ('ninguem reparou nesse detalhe...')",
        "opiniao": "titulo com OPINIAO forte e pessoal do canal ('essa e a cena mais triste de...')",
        # 15/10: era "nome_obra" (titulo comecando pelo nome da obra); regra do dono (LEIA_MELHORIAS_HIPERCOOL.md):
        # nunca o nome da obra (da reivindicacao de direitos) -> palavras que o publico busca
        "busca": "titulo com as PALAVRAS QUE O PUBLICO BUSCA sobre o assunto (o que acontece + 2-3 palavras-chave em CAIXA ALTA), sem o nome da obra",
    },
    "gancho": {
        "pergunta_direta": "1a linha da descricao = pergunta direta ao publico",
        "contexto": "1a linha da descricao = contexto rapido (quem, onde, o que esta em jogo)",
        "spoiler_parcial": "1a linha da descricao = metade da revelacao, sem contar o final",
    },
    "comentario": {
        "opiniao": "comentario pedindo a opiniao sincera sobre a cena",
        "a_ou_b": "comentario em formato enquete 'A ou B?' com duas opcoes claras",
        "previsao": "comentario pedindo um palpite do que acontece depois",
    },
}


def _aprend_path(cfg):
    return Path(_rc(cfg)["aprendizado"])


def aprendizado(cfg):
    try:
        p = _aprend_path(cfg)
        return load_json(p) if p.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _bracos(canal, dim):
    if dim == "horario":
        return list(canal.get("horarios") or ["12:00", "19:00"])
    permitidos = (canal.get("estrategias") or {}).get(dim)
    return [b for b in ESTRATEGIAS[dim] if not permitidos or b in permitidos]


def ordem_bracos(cfg, canal, dim, semente, apr=None):
    """Ordem de preferencia dos bracos de uma dimensao para este canal.
    1) braco com menos de 2 amostras no canal vai primeiro (exploracao inicial);
    2) depois, nota = media do canal puxada para a media da rede (K=2 amostras virtuais);
    3) com probabilidade 'explorar' (padrao 25%) testa outro braco que nao o melhor."""
    apr = apr if apr is not None else aprendizado(cfg)
    bracos = _bracos(canal, dim)
    do_canal = ((apr.get("canais") or {}).get(canal["slug"]) or {}).get(dim) or {}
    rede = {}
    for por_dim in (apr.get("canais") or {}).values():
        for b, v in (por_dim.get(dim) or {}).items():
            rede.setdefault(b, []).extend(v)
    rnd = random.Random(f"{semente}|{dim}")
    poucas = [b for b in bracos if len(do_canal.get(b, [])) < 2]
    if poucas:
        rnd.shuffle(poucas)
        poucas.sort(key=lambda b: len(do_canal.get(b, [])))
        return poucas + [b for b in bracos if b not in poucas]

    def nota(b):
        vc, vr = do_canal.get(b, []), rede.get(b, [])
        base = sum(vr) / len(vr) if vr else 1.0
        return (sum(vc) + 2 * base) / (len(vc) + 2)
    melhor = sorted(bracos, key=nota, reverse=True)
    if rnd.random() < float(canal.get("explorar", 0.25)) and len(melhor) > 1:
        outro = rnd.choice(melhor[1:])
        melhor.remove(outro)
        melhor.insert(0, outro)
    return melhor


def escolher_estrategia(cfg, canal, semente):
    apr = aprendizado(cfg)
    return {dim: ordem_bracos(cfg, canal, dim, semente, apr)[0] for dim in ESTRATEGIAS}


def memoria_canal(cfg, canal, n=3):
    """Titulos que mais e menos renderam no canal (views em 48 h relativas a mediana do canal)."""
    hist = ((aprendizado(cfg).get("historico") or {}).get(canal["slug"]) or [])
    if len(hist) < 4:
        return ""
    hs = sorted(hist, key=lambda h: h.get("nota", 0), reverse=True)
    bons = "; ".join(f"'{h['titulo'][:70]}' ({h.get('nota', 0):.1f}x)" for h in hs[:n])
    ruins = "; ".join(f"'{h['titulo'][:70]}' ({h.get('nota', 0):.1f}x)" for h in hs[-n:])
    return (f"MEMORIA DO CANAL (views em 48 h vs mediana do canal) - renderam MAIS: {bons}. Renderam MENOS: {ruins}. "
            "Use o que funcionou (estilo, tamanho, palavras), sem copiar titulo.")


def memoria_rede(cfg, canal, n=4):
    """Aprendizado ENTRE projetos (15/10): titulos que mais/menos renderam em 48 h nos OUTROS canais, de todos os projetos
    (react, recap do hipercool, historias, Veo). Medido pelo postador (bin/notificar_telegram.py -> aprendizado_global.json)."""
    p = Path(_rc(cfg)["aprendizado"]).with_name("aprendizado_global.json")
    try:
        g = load_json(p) if p.exists() else {}
    except Exception:  # noqa: BLE001
        return ""
    top = [t for t in g.get("top") or [] if t.get("canal") != canal["slug"]][:n]
    if len(top) < 2:
        return ""
    bons = "; ".join(f"'{t['titulo'][:70]}' ({t['views']} views, {t.get('origem', '')})" for t in top)
    ruins = "; ".join(f"'{t['titulo'][:70]}' ({t['views']})" for t in (g.get("piores") or [])[:2])
    return (f"MEMORIA DA REDE (outros canais e projetos, views em 48 h) - renderam MAIS: {bons}. Renderam MENOS: {ruins}. "
            "Inspire-se no gancho e nas palavras do que funcionou, sem copiar e sem sair do nicho deste canal.")


# ─────────────────────────── agente do canal (metadados) ────────────────────
AGENTE_INSTR = """Voce e o agente do canal de YouTube Shorts "{nome}" ({handle}). Publico/nicho: {nicho}.
Voz do canal: {persona}.
{regras}
Recebe os dados de um video que vai ao ar neste canal e escreve os metadados NA VOZ DO CANAL, em portugues do Brasil.
ESTRATEGIA DESTE VIDEO (e um teste do canal - siga): {estrategia}
{memoria}
{memoria_rede}
Responda SOMENTE JSON:
{{"titulo": "...", "descricao": "...", "tags": ["..."], "comentario": "..."}}
Regras:
- titulo: ate 70 caracteres, gancho forte e verdadeiro (nada que o video nao mostre), no maximo 2 emojis, termina com #shorts e 1 hashtag do tema.
  Se o video nao e exatamente do nicho do canal, use o angulo que conecta o video ao publico deste canal (sem mentir sobre o conteudo).
- descricao: 1a linha = gancho curto (aparece no Shorts); depois 2 a 3 linhas sobre o que acontece; 1 pergunta para o publico comentar;
  1 chamada para seguir o canal no estilo do canal; linha em branco; 3 a 5 hashtags (a 1a e #shorts). Primeira pessoa do canal
  ("reagi", "olha isso"), NUNCA "o criador". Sem links. Sem listas enormes de hashtags. Sem #fyp/#viral.
{sintetico}- tags: 10 a 15 tags sem #, do mais especifico (obra, personagem, assunto) ao mais amplo; inclua 2 a 4 destas tags do canal: {tags_base}.
- comentario: 1 frase curta e especifica sobre o video, que o canal posta como 1o comentario (gera conversa).
- Seguranca de anuncios: evite matar, morte, morrer, sexo, nu, droga, arma, suicidio, sangue no titulo/descricao/tags (use eufemismos).
- NUNCA o nome da obra original (anime, manhwa, filme, serie, novela, jogo) no titulo, descricao, tags ou hashtags: da
  reivindicacao de direitos autorais. Use as palavras que o publico busca sobre o assunto; nome de personagem so na descricao.
- Nao invente fatos que nao estao nos dados."""

# revisor: o que nunca pode sair (vale para todo canal; canais com 'regras' tem a lista do dono)
PROIBIDO_TITULO = re.compile(r"\b(matar|matou|morte|morrer|morreu|sexo|nua?s?|drogas?|armas?|suic[ií]dio|sangue)\b", re.I)
# playlist dos completos (18/10): criada no 1o upload pelo navegador; o extras_rede.py poe a tela final "1 video + esta
# playlist" quando o completo abre. Nome fixo (a playlist e achada pelo nome) e sem nome de obra.
PLAYLIST_COMPLETOS = "REACT COMPLETO | reagindo do começo ao fim"

# anti-ban (copiado do historias-em-frames/bin/viralizador.py, 18/10): troca direta em titulo, descricao, tags e comentario.
# So palavra inteira e so troca que mantem o genero ("a morte" -> "a partida"). Ambiguas (droga = interjeicao, arma secreta,
# sangue frio) ficam fora: o revisor acima pega no titulo e o LLM reescreve com contexto.
ANTI_BAN = {
    "matar": "eliminar", "matou": "eliminou", "mataram": "eliminaram",
    "morrer": "partir", "morreu": "partiu", "morreram": "partiram",
    "morte": "partida", "mortes": "partidas",
    "assassino": "vilão", "assassina": "vilã", "assassinos": "vilões", "assassinas": "vilãs", "assassinato": "crime",
    "suicídio": "desespero", "suicidio": "desespero",
    "sexo": "romance", "nu": "sem roupa", "nua": "sem roupa", "nus": "sem roupa", "nuas": "sem roupa",
    "drogas": "substâncias", "estupro": "crime", "terrorista": "extremista", "terroristas": "extremistas",
}
_ANTI_BAN_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in sorted(ANTI_BAN, key=len, reverse=True)) + r")\b", re.I)


def _troca_anti_ban(m):
    w, novo = m.group(0), ANTI_BAN[m.group(0).casefold()]
    if len(w) > 1 and w.isupper():
        return novo.upper()
    return novo[0].upper() + novo[1:] if w[0].isupper() else novo


def anuncio_seguro(texto):
    return _ANTI_BAN_RE.sub(_troca_anti_ban, texto or "")
PROIBIDO_DONO = re.compile(r"\b(rob[oô]s?|bots?|garantid[oa]s?|fique rico|ficar rico|enriquecer r[aá]pido|prev[eê] o mercado|"
                           r"lucro certo|ganho certo|aumentou meu (resultado|lucro))\b", re.I)
# 16/10/2026 (item DS-02 de D:\veo\docs\PLANO_MELHORIAS_VEO.md): contato e convite
# a sair do YouTube. Ate agora "Sem links" existia so como INSTRUCAO ao LLM, sem
# ninguem conferir depois — e foi justamente o slide de WhatsApp que derrubou os
# canais antigos do Veo em 04/09/2026. A politica de spam do YouTube trata o
# redirecionamento tambem quando aparece em descricao, comentario ou fala.
# A palavra "WhatsApp" sozinha NAO entra: um produto da dona se chama "Ligacoes
# WhatsApp com IA", e descrever o produto e legitimo; o que nao pode e mandar ir.
# Link para o PROPRIO YouTube nao entra: apontar para outro video ou canal e
# normal e nao e "sair da plataforma" (foi pego como falso positivo na simulacao
# de 16/10, num react que citava https://www.youtube.com/watch?v=...).
_YOUTUBE_OK = re.compile(r"^(?:https?://)?(?:www\.|m\.)?(?:youtube\.com|youtu\.be)\b", re.I)
# 16/10 (casos em testes/teste_filtro_contato.py): o telefone antigo (qualquer 9+ caracteres de digito/espaco/ponto/
# traco) barrava "Capitulo 120 - 125", "1.000.000", "2025-2026"; e o convite exigia o verbo colado no "no" ("fala comigo
# no WhatsApp", "me chama no whats", "siga no tiktok" passavam). Telefone agora = formato BR: celular 9XXXX-XXXX, ou
# DDD + 8/9 digitos, com +55 opcional.
PROIBIDO_CONTATO = re.compile(
    r"(?:(?<![\d/])(?:\+?55[\s.-]?)?(?:\(?\d{2}\)?[\s.-]?\d{4,5}|9\d{4})[\s.-]?\d{4}(?![\d/]))"  # telefone
    r"|(?:(?:https?://|www\.)\S+)"                      # url
    r"|(?:\b[\w-]+\.(?:com|com\.br|net|br|io|app|me|ly|link|site|org|info|gg)\b\S*)"  # dominio solto
    r"|(?:\b(?:chama|chame|chamar|fala|fale|manda|mande|segue|siga|entra|entre|vem|venha|clica|clique)\b"
    r"(?:\s+\w+){0,3}?\s+(?:no|na|pelo|pela|meu|minha)\s+"
    r"(?:whats?(?:app)?|wpp|zap(?:zap)?|dire?c?t|dm|pv|privado|insta\w*|telegram|tiktok|kwai)\b)"  # "chama no zap"
    r"|(?:\bno\s+zap\b|\bclique?\s+no\s+link\b|\blink\s+na\s+bio\b|\blink\s+na\s+descri\w+\b)",
    re.I)


def _acha_contato(texto):
    """Primeiro contato/convite a sair do YouTube no texto, ou None.

    Link do proprio YouTube e ignorado (ver _YOUTUBE_OK).
    """
    for m in PROIBIDO_CONTATO.finditer(texto or ""):
        achado = m.group(0).strip()
        if _YOUTUBE_OK.match(achado):
            continue
        return achado
    return None


def revisar(meta, canal, obra=None):
    """Lista de problemas (vazia = ok). obra: nome da obra do editorial (nunca pode aparecer - direitos autorais)."""
    prob = []
    if obra and len(obra.strip()) >= 4:
        txt = " ".join([meta["titulo"], meta["descricao"], " ".join(meta["tags"])]).casefold()
        if obra.strip().casefold() in txt:
            prob.append(f"cita o nome da obra '{obra.strip()}' (proibido: da reivindicacao de direitos); use palavras de busca")
    if PROIBIDO_TITULO.search(meta["titulo"]):
        prob.append(f"titulo com palavra que derruba anuncio: '{PROIBIDO_TITULO.search(meta['titulo']).group(0)}'")
    if canal.get("regras"):
        txt = " ".join([meta["titulo"], meta["descricao"], meta["comentario"], " ".join(meta["tags"])])
        m = PROIBIDO_DONO.search(txt)
        if m:
            prob.append(f"fere a regra do dono: '{m.group(0)}'")
    if re.search(r"\bo criador\b", meta["descricao"], re.I):
        prob.append("descricao fala 'o criador' (tem que ser primeira pessoa do canal)")
    # contato/link em QUALQUER campo que vai ao ar (titulo, descricao, comentario, tags)
    for campo in ("titulo", "descricao", "comentario"):
        achado = _acha_contato(meta.get(campo) or "")
        if achado:
            prob.append(f"{campo} manda a pessoa para fora do YouTube ou mostra contato: '{achado}'")
    achado = _acha_contato(" ".join(meta.get("tags") or []))
    if achado:
        prob.append(f"tags com contato/link: '{achado}'")
    return prob


def _barrado(cfg, item, canal):
    """O revisor ja barrou este video neste canal com a estrategia de hoje? O veredito fica no cache do adaptar e
    se repetiria toda hora, ocupando a vaga do canal (p1 do financeiro segurou o Assist-IA de 10 a 11/10)."""
    est = escolher_estrategia(cfg, canal, f"{item['id']}|{canal['slug']}")
    chave = "_".join(est[d] for d in ESTRATEGIAS)
    p = _work(cfg, "rede_meta", f"{_seguro(item['id'])}__{canal['slug']}__{chave}.json")
    return p.exists() and bool((load_json(p) or {}).get("bloqueado"))


def adaptar(cfg, item, canal, estrategia=None):
    estrategia = estrategia or escolher_estrategia(cfg, canal, item["id"])
    chave = "_".join(estrategia[d] for d in ESTRATEGIAS)
    cache_p = _work(cfg, "rede_meta", f"{_seguro(item['id'])}__{canal['slug']}__{chave}.json")
    if cache_p.exists():
        return load_json(cache_p)
    d = item["dados"]
    if d.get("manter_texto"):  # conteudo do dono com canal fixo (ex.: aula): o texto do editorial vai como esta
        meta = _validar_meta({}, d, dict(canal, tags_base=[]), item)
        prob = revisar(meta, canal)
        meta.update({"estrategia": estrategia, "bloqueado": "; ".join(prob) if prob else None})
        save_json(meta, cache_p)
        return meta
    sint = ("- descricao: termine com a linha 'Historia e imagens criadas com inteligencia artificial.' (o video e sintetico).\n"
            if item["sintetico"] else "")
    est_txt = "; ".join(f"{dim} = {ESTRATEGIAS[dim][estrategia[dim]]}" for dim in ESTRATEGIAS)
    instr = AGENTE_INSTR.format(nome=canal["nome"], handle=canal.get("handle", ""), nicho=canal.get("nicho", ""),
                                persona=canal.get("persona", "direta e sincera"),
                                regras=("REGRAS DO DONO (obrigatorio): " + canal["regras"]) if canal.get("regras") else "",
                                estrategia=est_txt, memoria=memoria_canal(cfg, canal),
                                memoria_rede=memoria_rede(cfg, canal),
                                sintetico=sint, tags_base=", ".join(canal.get("tags_base", [])))
    corpo = {"origem": item["fonte"], "resumo": item["resumo"], "titulo_original": d.get("titulo"),
             "descricao_original": (d.get("descricao") or "")[:900], "tags_originais": d.get("tags"),
             "comentario_original": d.get("comentario_fixado")}
    buscadas = _palavras_buscadas_veo(item) if item["fonte"] == "veo" else (
        _palavras_buscadas_react(item) if item["fonte"] == "react" else [])
    if buscadas:  # DS-03 (16/10): o que o publico digita na busca do YouTube no tema do clipe
        corpo["palavras_buscadas"] = buscadas
        instr += ("\n- palavras_buscadas: o que o publico DIGITA na busca do YouTube neste tema. Use 1 ou 2 que combinem "
                  "DE VERDADE com o video no titulo e nas tags (nunca uma que nao tenha a ver; nada de nome de musica, "
                  "jogo ou serie que nao aparece no video).")
    payload = json.dumps(corpo, ensure_ascii=False)
    obra = (item.get("resumo") or {}).get("obra")
    meta = _validar_meta(ask_json(cfg, instr, payload) or {}, d, canal, item)
    prob = revisar(meta, canal, obra)
    if prob:  # revisor: 1 nova tentativa dizendo o que corrigir
        log(f"revisor ({canal['slug']}): {'; '.join(prob)} - pedindo correcao")
        meta = _validar_meta(ask_json(cfg, instr + "\nCORRIJA OBRIGATORIAMENTE: " + "; ".join(prob), payload) or {},
                             d, canal, item)
        prob = revisar(meta, canal, obra)
    meta["estrategia"] = estrategia
    meta["bloqueado"] = "; ".join(prob) if prob else None
    save_json(meta, cache_p)
    return meta


SEO_VEO = Path(r"D:\veo\beta\logs\seo_palavras_veo.json")
PLACAR_PALAVRAS = Path(r"D:\postador-de-videos\_analise\placar_palavras.json")
# palavra de contato nunca e empurrada pro titulo, mesmo vencendo (o WhatsApp na tela derrubou os canais em 04/09)
_PALAVRA_CONTATO = re.compile(r"whats|zap|telefone|celular|contato|link|chama|direct|insta|perfil|site|\d", re.I)
SEO_HIPERCOOL = Path(r"D:\hipercool-videos\config\seo_palavras.json")


def _palavras_buscadas_veo(item):
    """Palavras do autocompletar do YouTube para o tema do clipe do Veo (D:\\veo\\beta\\seo_palavras_veo.py)."""
    try:
        temas = json.loads(SEO_VEO.read_text(encoding="utf-8")).get("temas") or {}
    except (OSError, ValueError):
        return []
    stem = item["id"].split(":", 1)[-1]
    tema = re.split(r"_20\d{6}", stem)[0]
    # 24/10 (funil, como o seo_generator.quentes do recapd): palavras de TITULO de Veo que passaram da mediana do canal
    # em 48 h NO MESMO TEMA (placar palavras, grupo veo:<tema>; min. 2 testes, taxa > 50%, sem palavra de contato)
    # entram primeiro
    vencedoras = []
    try:
        g = json.loads(PLACAR_PALAVRAS.read_text(encoding="utf-8")).get("grupos", {}).get(f"veo:{tema[:15]}", {})
        vencedoras = [p for _t, _r, p in sorted(((x.get("vitorias", 0) / x["testes"], x["testes"], p)
                                                  for p, x in g.items() if x.get("testes", 0) >= 2
                                                  and x.get("vitorias", 0) / x["testes"] > 0.5
                                                  and not _PALAVRA_CONTATO.search(p)), reverse=True)][:5]
    except (OSError, ValueError, KeyError, ZeroDivisionError):
        pass
    busca = temas.get(tema) or []
    return (vencedoras + [p for p in busca if p not in vencedoras])[:12]


def _palavras_buscadas_react(item):
    """Palavras do autocompletar do YouTube para o react, pelo gênero/tema do editorial."""
    try:
        banco = json.loads(SEO_HIPERCOOL.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    resumo = item.get("resumo") or {}
    tags = [t.casefold() for t in resumo.get("tags", [])]
    tema = (resumo.get("tema") or "").casefold()
    generos = banco.get("generos") or {}
    out = list(banco.get("sempre") or [])
    for g, palavras in generos.items():
        if g in tags or g in tema or any(g in t for t in tags):
            out += palavras
    if not [w for w in out if w not in (banco.get("sempre") or [])]:
        out += generos.get("drama", [])
    return out[:15]


def _validar_meta(m, d, canal, item):
    titulo = anuncio_seguro(str(m.get("titulo") or d.get("titulo") or "").strip())
    if len(titulo) > 100:
        titulo = titulo[:97].rsplit(" ", 1)[0] + "..."
    desc = anuncio_seguro(str(m.get("descricao") or d.get("descricao") or "").strip())
    hashtags = re.findall(r"#\w+", desc)
    if len(hashtags) > 8:  # acima de 15 o YouTube ignora todas; mantem as 5 primeiras
        for h in hashtags[5:]:
            desc = desc.replace(" " + h, "").replace(h, "")
        desc = desc.rstrip()
    if item["sintetico"] and "inteligencia artificial" not in desc.lower() and "inteligência artificial" not in desc.lower():
        desc += "\n\nHistoria e imagens criadas com inteligencia artificial."
    tags, total, vistos = [], 0, set()
    for t in list(m.get("tags") or []) + list(d.get("tags") or []) + list(canal.get("tags_base") or []):
        t = anuncio_seguro(str(t).replace("#", "").strip())
        k = t.casefold()
        if not t or k in vistos or len(t) > 60:
            continue
        if total + len(t) + 1 > 450 or len(tags) >= 15:
            break
        vistos.add(k)
        tags.append(t)
        total += len(t) + 1
    com = anuncio_seguro(str(m.get("comentario") or d.get("comentario_fixado") or "").strip())[:300]
    return {"titulo": titulo, "descricao": desc[:4900], "tags": tags, "comentario": com, "llm": bool(m)}


# ─────────────────────────── horario ────────────────────────────────────────
def _hhmm_dt(dia, hhmm, tz):
    hh, mm = (int(x) for x in hhmm.split(":"))
    return datetime(dia.year, dia.month, dia.day, hh, mm, tzinfo=tz)


def escolher_horario(cfg, politica, canal, dia, item_id, ocupados, recuperar_de=None, ja=False):
    """Horario = mais uma dimensao da estrategia (explora os horarios do canal e aprende o que rende).
    recuperar_de (botao LIGAR): se os horarios do canal hoje ja passaram, publica a partir desse instante e devolve
    horario None (pendente recuperada nao conta como braco da estrategia no aprendizado).
    ja (botao LIGAR): nem espera o horario do canal - o video de hoje publica a partir de recuperar_de."""
    agora = politica.agora()
    intervalo = timedelta(hours=politica.politica().get("intervalo_min_horas_mesmo_canal") or 0)
    j = int(canal.get("jitter_min", 15))
    jit = timedelta(minutes=(int(hashlib.md5(item_id.encode()).hexdigest(), 16) % (2 * j + 1)) - j) if j else timedelta()
    for h in ([] if ja and recuperar_de else ordem_bracos(cfg, canal, "horario", f"{item_id}{dia}")):
        alvo = _hhmm_dt(dia, h, agora.tzinfo) + jit
        if alvo < agora + timedelta(minutes=_rc(cfg)["antecedencia_min"]):
            continue
        if any(abs(alvo - o) < intervalo for o in ocupados):
            continue
        return alvo, h
    if recuperar_de and recuperar_de.date() == dia:
        alvo = recuperar_de
        while any(abs(alvo - o) < intervalo for o in ocupados):
            alvo += timedelta(minutes=15)
        if alvo.date() == dia:
            return alvo, None
    return None, None


# ─────────────────────────── API (privar, editar, comentar) ─────────────────
def _req(yp, cred, url, metodo="GET", corpo=None):
    tok = yp.refresh_access_token(cred)
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo,
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode() or "{}")


def video_info(yp, cred, vid):
    d = _req(yp, cred, f"https://www.googleapis.com/youtube/v3/videos?part=snippet,status&id={vid}")
    return (d.get("items") or [None])[0]


def privar(yp, cred, vid):
    v = video_info(yp, cred, vid)
    if not v:
        return "nao achado"
    st = v["status"]
    if st.get("privacyStatus") == "private" and not st.get("publishAt"):
        return "ja privado"
    novo = {k: st[k] for k in ("embeddable", "license", "publicStatsViewable", "selfDeclaredMadeForKids",
                               "containsSyntheticMedia") if k in st}
    novo["privacyStatus"] = "private"
    _req(yp, cred, "https://www.googleapis.com/youtube/v3/videos?part=status", "PUT", {"id": vid, "status": novo})
    return "privado"


def editar_meta(yp, cred, vid, meta, categoria=None, idioma="pt-BR"):
    v = video_info(yp, cred, vid)
    if not v:
        return "nao achado"
    sn = v["snippet"]
    novo = {"title": meta["titulo"][:100], "description": meta["descricao"][:5000], "tags": meta["tags"],
            "categoryId": str(categoria or sn.get("categoryId") or "24")}
    if idioma:
        novo["defaultLanguage"] = idioma
        novo["defaultAudioLanguage"] = idioma
    _req(yp, cred, "https://www.googleapis.com/youtube/v3/videos?part=snippet", "PUT", {"id": vid, "snippet": novo})
    return "editado"


# ─────────────────────────── rodada de agendamento ──────────────────────────
def _arquivar_historia(cfg, item, extra):
    d = dict(item["dados"], posted_url=extra["url"], postado=extra)
    save_json(d, item["json"])
    dst = Path(_rc(cfg)["postados_historias"]) / (item["dados"].get("genero") or "outros") / item["json"].parent.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(item["json"].parent), str(dst))


def _arquivar_veo(item, extra):
    """Veo limpo: so marca o json (a pasta limpos/ e de todos os videos Veo e fica onde esta)."""
    d = load_json(item["json"])
    d.update(posted_url=extra["url"], postado=extra)
    save_json(d, item["json"])


APREND_GLOBAL = Path(r"D:\postador-de-videos\_analise\aprendizado_global.json")


def _veo_rende(R):
    """O Veo limpo esta rendendo? (Onda 3.2, 16/10: "escalar so com dado", item AB-11 do plano do veo.) Mediana de views em
    48 h dos Veo (aprendizado_global.json, origem "veo limpo", >= 5 videos) >= mediana dos canais que recebem o Veo."""
    try:
        d = json.loads(APREND_GLOBAL.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    veo = (d.get("por_origem") or {}).get("veo limpo") or {}
    canais = [(d.get("por_canal") or {}).get(s, {}).get("mediana") for s in (R.get("canais_veo_limpo") or [])]
    canais = [c for c in canais if c is not None]
    return bool(veo.get("n", 0) >= 5 and canais and veo.get("mediana", 0) >= sorted(canais)[len(canais) // 2])


def _veo_por_dia(R, dia):
    """Veo por canal no dia pela veo_rampa (vale o ultimo degrau cuja data ja chegou; 0 = sem vagas proprias).
    Subir alem do 1o degrau exige dado (_veo_rende); sem dado, fica no 1o (Onda 3.2, 16/10)."""
    n, primeiro = 0, None
    for degrau in R.get("veo_rampa") or []:
        try:
            desde, qtd = degrau
            if datetime.strptime(str(desde), "%Y-%m-%d").date() <= dia:
                n = int(qtd)
                primeiro = n if primeiro is None else primeiro
        except (TypeError, ValueError):
            log(f"rede: veo_rampa com degrau invalido {degrau!r} - ignorado")
    if primeiro is not None and n > primeiro and not _veo_rende(R):
        return primeiro
    return n


def _retirados(cfg):
    """{video_id: motivo} tirado do ar depois de agendado (work/rede_retirados.json): a vaga dele volta a ficar livre."""
    p = _work(cfg, "rede_retirados.json")
    return load_json(p) if p.exists() else {}


def _ocupados_rede(cfg, politica, cred, so_veo=False):
    """Horarios ja usados no canal (ledger do postador), menos os retirados; so_veo: so o Veo, que sobe com o arquivo
    da marca trocada, veo_<clipe>__<canal>.mp4 (rebrand)."""
    fora = _retirados(cfg)
    return [politica._dt(r.get("publish_at")) or politica._dt(r["ts"]) for r in politica._ler_ledger()
            if politica._do_canal(r, cred) and r.get("video_id") not in fora
            and (not so_veo or Path(str(r.get("arquivo") or "")).name.startswith("veo_"))]


def _extra_rampa_canal(politica, c):
    """Degraus extras do canal na rampa_canais do postador (0 se a politica nao tem a rampa ou deu erro)."""
    try:
        return int(politica._extra_rampa(c["cred"]))
    except Exception:  # noqa: BLE001
        return 0


def _teto_canal(politica, c, padrao):
    try:
        return int(politica.teto_canal(c["cred"]))
    except Exception:  # noqa: BLE001
        return padrao


PLACAR_VEO_TEMAS = Path(r"D:\postador-de-videos\_analise\placar_veo_temas.json")


def _bonus_viral_veo():
    """24/10 (funil): {tema: amostra Thompson 0-1} do placar veo_temas (postador notificar_telegram._placar_veo: vitoria
    = views em 48 h acima da mediana do canal). Tema sem dado = Beta(1,1), ainda testado."""
    try:
        g = json.loads(PLACAR_VEO_TEMAS.read_text(encoding="utf-8")).get("grupos", {}).get("veo", {})
    except (OSError, ValueError):
        g = {}
    return lambda tema: random.betavariate(g.get(tema, {}).get("vitorias", 0) + 1,
                                           g.get(tema, {}).get("testes", 0) - g.get(tema, {}).get("vitorias", 0) + 1)


def _plano_veo(cfg, chans, itens, dia, ocup, ocup_veo, excluir, agora, falas_rodada=None, extra=None):
    """[(item, slug, nota, horario)] das vagas proprias do Veo no dia: _veo_por_dia em cada canal de canais_veo_limpo,
    nos veo_horarios (com o jitter do canal); horario de hoje que ja passou vira 'a partir de agora'. O clipe de cada
    vaga: a maior nota do diretor para aquele canal (sem nota dele = nota_min; nota dele abaixo de nota_min = nao combina
    com o canal), o mais novo no empate."""
    R = _rc(cfg)
    n = _veo_por_dia(R, dia)
    permitidos = set(R.get("canais_veo_limpo") or [])
    vchans = [c for c in chans if c["slug"] in permitidos]
    if not n or not vchans or not itens:
        return []
    gap = timedelta(minutes=_num(R, "veo_intervalo_min", 60))
    cedo = agora + timedelta(minutes=_num(R, "antecedencia_min", 30))
    vagas = []  # (horario, slug)
    for c in vchans:
        s = c["slug"]
        nc = n + int((extra or {}).get(s, 0))  # 24/10: degrau extra da rampa_canais vale pro Veo do canal
        ja = [o for o in ocup_veo[s] if o.astimezone().date() == dia]
        j = int(c.get("jitter_min", 15))
        livres = []
        for h in (R.get("veo_horarios") or [])[:nc]:
            semente = int(hashlib.md5(f"{s}{dia}{h}".encode()).hexdigest(), 16)
            alvo = _hhmm_dt(dia, h, agora.tzinfo) + (timedelta(minutes=semente % (2 * j + 1) - j) if j else timedelta())
            if not any(abs(alvo - o) < gap for o in ja):  # esse horario ainda nao tem Veo
                livres.append(max(alvo, cedo))
        tomados = list(ocup[s])
        for alvo in sorted(livres)[:max(0, nc - len(ja))]:
            while any(abs(alvo - o) < gap for o in tomados):
                alvo += timedelta(minutes=15)
            if alvo.astimezone().date() != dia:
                continue
            tomados.append(alvo)
            vagas.append((alvo, s))
    if not vagas:
        return []
    nota_min = _num(R, "nota_min", 6.0, float)
    nt = notas(cfg, itens, chans)

    def fala(texto):
        return re.sub(r"[^a-z0-9]", "", (texto or "").lower())

    # o Veo gerou o mesmo roteiro mais de uma vez (16/10: 7 falas repetidas em 202 limpos): fala que ja saiu, em qualquer
    # dos canais, ou que ja esta no plano desta rodada (falas_rodada: os outros dias) nao sai de novo
    falas = falas_rodada if falas_rodada is not None else set()
    for jp in Path(R["veo_limpos_dir"]).glob("*.json"):
        try:
            d = load_json(jp)
        except Exception:  # noqa: BLE001
            continue
        if d.get("posted_url") and fala(d.get("fala")):
            falas.add(fala(d.get("fala")))
    usados, plano = set(), []
    viral = _bonus_viral_veo()
    peso_viral = _num(R, "veo_peso_viral", 3.0, float)  # 24/10: ate +3 na nota pro tema que viraliza (0 = desliga)
    for alvo, s in sorted(vagas):
        cands = []
        for i, it in enumerate(itens):  # inventario: os limpos mais novos primeiro
            v = (nt.get(it["id"]) or {}).get(s)
            v = nota_min if v is None else v
            f = fala(it["dados"].get("descricao"))
            if it["id"] not in usados and (it["id"], s) not in excluir and v >= nota_min and not (f and f in falas):
                # o id e "veo:<tema>_<AAAAMMDD_HHMMSS>": sem tirar o "veo:" o tema nunca casava com o placar
                tema = re.match(r"(.+?)_\d{8}_\d{6}", str(it["id"]).split(":", 1)[-1])
                cands.append((-(v + peso_viral * viral(tema.group(1) if tema else "")), i, v))
        if not cands:
            log(f"rede: Veo sem clipe que combine com {s} ({dia:%d/%m} {alvo:%H:%M})")
            continue
        _ordem, i, v = min(cands)
        usados.add(itens[i]["id"])
        falas.add(fala(itens[i]["dados"].get("descricao")) or itens[i]["id"])
        plano.append((itens[i], s, v, alvo))
    return plano


def _fome(ocup, dia):
    """Bonus de distribuicao para quem publicou pouco nos 3 dias ate `dia` (ninguem fica de fora enquanto outro recebe 2)."""
    out = {}
    for slug, lst in ocup.items():
        n = sum(1 for o in lst if 0 <= (dia - o.astimezone().date()).days <= 2)
        out[slug] = 1.5 if n == 0 else (0.75 if n == 1 else 0.0)
    return out


def _series_fora_de_ordem(itens, esperando):
    """Parte N de uma serie so entra depois que a parte N-1 saiu da fila (foi postada)."""
    na_fila = {it["id"] for it in itens + esperando}
    fora = set()
    for it in itens:
        if _serie(it):
            try:
                n = int(it["dados"].get("parte") or 1)
            except (TypeError, ValueError):
                continue
            base = re.sub(r"_p\d+$", "", it["id"])
            if n > 1 and f"{base}_p{n - 1}" in na_fila:
                fora.add(it["id"])
    return fora


class Trava:
    """Uma rodada da rede por vez (tarefa de hora em hora, ciclo das 06:40 e comentarios usam o mesmo registro).
    Trava com mais de 90 min e considerada abandonada (processo morto)."""

    def __init__(self, cfg):
        self.p = _work(cfg, "rede.lock")
        self.ok = False

    def __enter__(self):
        import os
        import time
        if self.p.exists() and time.time() - self.p.stat().st_mtime < 90 * 60:
            log(f"rede: outra rodada em andamento ({self.p.read_text(encoding='utf-8', errors='replace')}) - saindo")
            return self
        self.p.write_text(f"pid {os.getpid()} desde {datetime.now():%H:%M}", encoding="utf-8")
        self.ok = True
        return self

    def __exit__(self, *a):
        if self.ok:
            self.p.unlink(missing_ok=True)


# ─────────────────────────── videos completos (grandes/, react deitado) ─────
def inventario_longos(cfg, politica, so_aprovados=True):
    """Videos completos em grandes/<canal>/ (react deitado, 1 por tema) prontos e ainda nao postados."""
    _, feitos = _postados(cfg, politica)
    aprov = politica.ler_json(politica.APROV_FILE, {})
    pasta = Path(cfg["paths"].get("ready_grandes") or Path(cfg["paths"]["ready"]).parent / "grandes")
    itens, esperando = [], []
    for pj in sorted(pasta.glob("*/*.postar.json")):
        try:
            d = load_json(pj)
        except Exception:  # noqa: BLE001
            continue
        mp4 = pj.parent / d.get("arquivo", "")
        if d.get("pronto") is False or not mp4.is_file() or mp4.stem in feitos:
            continue
        item = {"id": mp4.stem, "fonte": "completo", "mp4": mp4, "json": pj, "dados": d,
                "slug_origem": d.get("canal_slug") or pj.parent.name, "sintetico": False}
        (itens if (not so_aprovados or politica.aprovado(mp4, aprov)) else esperando).append(item)
    return itens, esperando


def _agendar_longos(cfg, politica, yp, chans, reg, agora, simular, dias, janela_h, ja, rec_prox):
    """1 video completo por canal por dia, num horario do canal (longe do Short pelo intervalo da politica), no canal que o
    editorial do grande escolheu. Titulo/descricao/capitulos/thumb vem prontos do grande.empacotar; o revisor confere.
    Sobe na janela como os Shorts (LIGAR: publica ja). Nao entra no aprendizado de horario dos Shorts."""
    itens, esperando = inventario_longos(cfg, politica)
    if not itens and not esperando:
        return 0, rec_prox
    log(f"rede: videos completos: {len(itens)} aprovado(s) na fila | {len(esperando)} esperando aprovacao")
    by = {c["slug"]: c for c in chans}
    dias_com_longo = {}
    for r in reg.values():
        if r.get("tipo") == "completo" and politica._dt(r.get("publish_at")):
            dias_com_longo.setdefault(r.get("canal_slug"), set()).add(politica._dt(r["publish_at"]).astimezone().date())
    total, planejados = 0, {}
    for item in itens:
        canal = by.get(item["slug_origem"])
        if not canal:
            log(f"rede: completo {item['id']}: canal {item['slug_origem']} nao esta ativo - esperando")
            continue
        # canal sem a verificacao por telefone so aceita ate 15 min: o completo wKiGkUQ6bBc do InventoReact (13/10) foi
        # "removido por ser muito longo" (pagina do video, 16/10). verificado: false no rede_canais.json -> espera.
        if canal.get("verificado") is False:
            try:
                dur = float(ffprobe_json(cfg, item["mp4"]).get("format", {}).get("duration") or 0)
            except Exception:  # noqa: BLE001
                dur = 0
            if not dur or dur > 15 * 60:
                log(f"rede: completo {item['id']} ({dur / 60:.0f} min) esperando: {canal['nome']} sem a verificacao por "
                    "telefone (limite de 15 min) - o dono faz em Configuracoes do canal")
                continue
        d = item["dados"]
        meta = {"titulo": anuncio_seguro(d.get("titulo")), "descricao": anuncio_seguro(d.get("descricao")),
                "comentario": anuncio_seguro(d.get("comentario_fixado")),
                "tags": [anuncio_seguro(t) for t in d.get("tags") or []]}
        prob = revisar(meta, canal)
        if prob:
            log(f"rede: completo {item['id']} BARRADO pelo revisor em {canal['nome']}: {'; '.join(prob)}")
            continue
        slug = canal["slug"]
        ocup = [o for o in PB._ocupados(politica, canal["cred"]) if o] + planejados.get(slug, [])
        alvo = hh = None
        for k in range(dias):
            dia = (agora + timedelta(days=k)).date()
            if dia in dias_com_longo.get(slug, set()):
                continue
            alvo, hh = escolher_horario(cfg, politica, canal, dia, item["id"], ocup,
                                        recuperar_de=rec_prox if k == 0 else None, ja=ja)
            if alvo:
                break
        if not alvo:
            continue
        if hh is None:
            rec_prox = alvo + timedelta(minutes=20)
        dias_com_longo.setdefault(slug, set()).add(alvo.date())
        planejados.setdefault(slug, []).append(alvo)
        if simular:
            log(f"[simulacao] {canal['nome']:24} {alvo:%d/%m %H:%M} COMPLETO <- {item['id']} | {meta['titulo'][:60]}")
            total += 1
            continue
        if janela_h and hh and alvo > agora + timedelta(hours=janela_h):
            log(f"rede: completo {item['id']} reservado: {canal['nome']} {alvo:%d/%m %H:%M}")
            continue
        if desligada(politica):
            log("rede: postagem DESLIGADA no meio da rodada - parando antes do proximo upload")
            break
        # a capa vai NO upload pelo navegador (16/10, dono: nada pela API; antes subia depois pela thumbnails.set)
        thumb = item["json"].parent / (d.get("thumb") or "")
        capa = thumb if d.get("thumb") and thumb.exists() else None
        status, info = politica.postar_youtube(
            canal["cred"]["id"], item["mp4"], meta["titulo"], meta["descricao"], meta["tags"], privacy="private",
            publish_at=politica.rfc3339(alvo), projeto=politica.PROJETO_REDE, categoria=canal.get("categoria"),
            idioma=canal.get("idioma", "pt-BR"), thumbnail=capa, playlist=PLAYLIST_COMPLETOS, tipo="completo")
        if status in ("parado", "suspenso"):
            log(f"rede: {canal['nome']}: {status} - {info}. PAROU TUDO")
            if status == "suspenso":
                from . import notificar
                notificar.aviso(f"Canal SUSPENSO: {canal['nome']}", f"{info} - a postagem da rede parou toda", nivel="erro")
            break
        if status != "ok":
            log(f"rede: completo {item['id']} nao subiu em {canal['nome']} ({status}: {info})")
            continue
        vid = info.rsplit("/", 1)[-1]
        rec = next((r for r in reversed(politica._ler_ledger()) if r.get("video_id") == vid), {})
        publica = rec.get("publish_at") or politica.rfc3339(alvo)
        thumb_st = "navegador" if capa else "sem"
        extra = {"video_id": vid, "url": info, "canal": canal["nome"], "canal_id": canal["cred"]["id"], "canal_slug": slug,
                 "publish_at": publica, "horario": None, "horario_canal": hh, "postado_em": politica.agora().isoformat(timespec="seconds"),
                 "thumb": thumb_st, "comentario": "pendente" if meta["comentario"] else "sem", "comentario_texto": meta["comentario"],
                 "titulo": meta["titulo"], "fonte": "completo", "tipo": "completo", "script": "rede",
                 "playlist": PLAYLIST_COMPLETOS}
        arquivo = Path(cfg["publish"]["posted_dir"]) / item["json"].parent.name  # PB._arquivar move as capas pra la
        ab = [str(arquivo / n) for n in d.get("thumbs_ab") or [] if (item["json"].parent / n).exists()]
        if len(ab) >= 2:  # capas A/B/C (mr/capa.py): o extras_rede.py liga o "Testar e comparar" quando o video abrir
            extra["thumbs_ab"] = ab
        reg[item["id"]] = extra
        save_json(reg, PB._registro_path(cfg))
        PB._arquivar(cfg, item, extra)
        total += 1
        log(f"rede: {canal['nome']}: COMPLETO AGENDADO {info} -> {publica} ({hh or 'agora'}) | {meta['titulo'][:60]}")
    return total, rec_prox


# ─────────────────────────── liga/desliga (botoes do desktop) ───────────────
def _arq_desligada(politica):
    return politica.CONFIG_DIR / "POSTAGEM_DESLIGADA.json"


def desligada(politica):
    """Botao DESLIGAR: enquanto este arquivo existir, nenhuma rodada automatica sobe video, comenta ou abre navegador.
    A rede checa aqui; o ciclo das 06:40 (postar_tudo_auto.bat) e o agendar_vo3_auto.bat checam o mesmo arquivo."""
    p = _arq_desligada(politica)
    if not p.exists():
        return None
    try:
        return load_json(p) or {"desde": "?"}
    except Exception:  # noqa: BLE001
        return {"desde": "?"}


def desligar(cfg):
    politica, _ = PB._postador(cfg)
    d = desligada(politica)
    if not d:
        d = {"desde": politica.agora().isoformat(timespec="minutes"), "por": "botao DESLIGAR do desktop"}
        save_json(d, _arq_desligada(politica))
    log(f"postagem automatica DESLIGADA desde {d.get('desde')}: nada sobe, nada e comentado e nenhum navegador abre "
        "ate apertar LIGAR (os videos continuam na fila)")


def ligar(cfg):
    """Botao LIGAR: volta a postagem automatica e ja faz as pendentes de hoje: todo canal com vaga hoje e video
    aprovado publica agora (sem esperar o horario do canal, 20 min entre canais); depois a tarefa de hora em hora segue
    a agenda normal nos proximos dias."""
    politica, _ = PB._postador(cfg)
    d = desligada(politica)
    _arq_desligada(politica).unlink(missing_ok=True)
    log("postagem automatica LIGADA" + (f" (estava desligada desde {d.get('desde')})" if d else ""))
    return agendar(cfg, recuperar=True, ja=True)


def agendar(cfg, simular=False, dias=1, limite=None, janela_h=None, recuperar=False, ja=False):
    politica, _ = PB._postador(cfg)
    d = desligada(politica)
    if simular:
        if d:
            log(f"rede: postagem automatica DESLIGADA desde {d.get('desde')}: nada deste plano sobe ate apertar LIGAR")
        return _agendar(cfg, True, dias, limite, janela_h)
    if d:
        log(f"rede: postagem automatica DESLIGADA (botao) desde {d.get('desde')} - nada sobe; aperte LIGAR para voltar")
        return 0
    with Trava(cfg) as t:
        return _agendar(cfg, False, dias, limite, janela_h, recuperar, ja) if t.ok else 0


def _agendar(cfg, simular=False, dias=1, limite=None, janela_h=None, recuperar=False, ja=False):
    """Preenche as vagas dos proximos `dias` (hoje incluso): 1 video por canal por dia (max_dia do canal).
    janela_h: so faz o UPLOAD do que publica nas proximas N horas (padrao rede.janela_upload_h = 3). A tarefa
    ManhwaReact-Rede roda de hora em hora, entao cada video sobe 1-3 h antes de abrir - sem rajada de uploads.
    recuperar (botao LIGAR): canal com vaga hoje e horarios ja passados publica agora, 1 canal a cada 20 min, e o upload
    sai nesta rodada (as rodadas de hora em hora nao recuperam). ja: idem para TODO canal com vaga hoje, mesmo com
    horario ainda por vir."""
    janela_h = _rc(cfg)["janela_upload_h"] if janela_h is None else janela_h
    politica, yp = PB._postador(cfg)
    parada = politica.parada_ativa()
    if parada:
        log(f"rede: PARADA GERAL desde {parada.get('desde')}: {parada.get('motivo')} - nada sobe")
        return 0
    chans = canais(cfg, politica)
    itens, esperando = inventario(cfg, politica)
    log(f"rede: {len(chans)} canais ativos | {len(itens)} video(s) aprovado(s) na fila | {len(esperando)} esperando aprovacao")
    if esperando:
        log("rede: aprovar -> python manhwareact.py rede --aprovar")
    fora = _series_fora_de_ordem(itens, esperando)
    itens = [it for it in itens if it["id"] not in fora]
    reg = PB._carregar_registro(cfg)
    agora = politica.agora()
    total, sem_video, esperando_janela = 0, [], []
    itens_falhos = []  # 22/10: itens que estouraram excecao na rodada (MR-01) - pulados, avisados no fim
    rec_prox = agora + timedelta(minutes=_rc(cfg)["antecedencia_min"]) if recuperar else None
    barrados ={(it["id"], c["slug"]) for it in itens for c in chans if _barrado(cfg, it, c)}
    if barrados:
        log("rede: fora da distribuicao (revisor ja barrou neste canal): "
            + ", ".join(f"{i} em {s}" for i, s in sorted(barrados)))
    # Veo com vagas proprias (veo_rampa, 16/10): sai da disputa da vaga do react e ganha as suas (_plano_veo)
    R = _rc(cfg)
    veo_proprio = bool(R.get("veo_rampa"))
    veo_itens = [it for it in itens if it["fonte"] == "veo"] if veo_proprio else []
    if veo_proprio:
        itens = [it for it in itens if it["fonte"] != "veo"]
    veo_usados, veo_falas, cheios, veo_adiantado = set(), set(), set(), set()
    veo_teto = _num(R, "veo_uploads_dia", 0) or _veo_por_dia(R, agora.date())
    hoje_ledger = [r for r in politica._ler_ledger() if (politica._dt(r.get("ts")) or agora).date() == agora.date()
                   and Path(str(r.get("arquivo") or "")).name.startswith("veo_")]  # mesmo criterio de _ocupados_rede
    veo_subidos = {c["slug"]: sum(1 for r in hoje_ledger if politica._do_canal(r, c["cred"])) for c in chans}
    # dentro do teto da politica (piso de 16/10: 4 por canal/dia) o react do dono (max_dia) e o completo (se o canal tem
    # pasta em grandes/) tem lugar garantido: o Veo fica com o que sobra
    pol_max = int(politica.politica().get("max_uploads_por_canal_dia") or 4)
    grandes = Path(cfg["paths"].get("ready_grandes") or Path(cfg["paths"]["ready"]).parent / "grandes")
    # 24/10 (dono: "o Veo tem que passar pela rampa de melhorias do YouTube"): canal que a rampa_canais subiu (rende e
    # nao pegou limite diario) da os degraus extras tambem ao Veo; o teto do canal vem do politica.teto_canal (rampa)
    veo_extra = {c["slug"]: _extra_rampa_canal(politica, c) for c in chans}
    veo_teto_canal = {c["slug"]: max(0, min(veo_teto + veo_extra[c["slug"]],
                                            _teto_canal(politica, c, pol_max) - int(c.get("max_dia", 1))
                                            - (1 if (grandes / c["slug"]).is_dir() else 0))) for c in chans}
    for k in range(max(dias, _num(R, "veo_dias_frente", 2) if veo_proprio else 0)):
        dia = (agora + timedelta(days=k)).date()
        vagas, ocup, ocup_veo = {}, {}, {}
        for c in chans:
            ocup[c["slug"]] = [o for o in _ocupados_rede(cfg, politica, c["cred"]) if o]
            ocup_veo[c["slug"]] = [o for o in _ocupados_rede(cfg, politica, c["cred"], so_veo=True) if o] if veo_proprio else []
            # o Veo das vagas proprias nao gasta a vaga do react (max_dia do canal)
            no_dia = sum(1 for o in ocup[c["slug"]] if o.astimezone().date() == dia) \
                - sum(1 for o in ocup_veo[c["slug"]] if o.astimezone().date() == dia)
            vagas[c["slug"]] = max(0, int(c.get("max_dia", 1)) - no_dia) if k < dias else 0
        plano = []
        if any(vagas.values()):
            sem_veo = {s: [o for o in os_ if o not in ocup_veo[s]] for s, os_ in ocup.items()}
            plano, sobra = distribuir(cfg, itens, chans, vagas, fome=_fome(sem_veo, dia), excluir=barrados)
            sem_video += [f"{s} ({dia:%d/%m})" for s, n in sobra.items() if n > 0]
        plano = [(item, slug, nota, None) for item, slug, nota in plano]
        if veo_proprio:
            pv = _plano_veo(cfg, chans, [it for it in veo_itens if it["id"] not in veo_usados], dia, ocup, ocup_veo,
                            barrados, agora, veo_falas, extra=veo_extra)
            veo_usados |= {it["id"] for it, _, _, _ in pv}
            plano += pv
        by = {c["slug"]: c for c in chans}
        for item, slug, nota, fixo in plano:
            if limite and total >= limite:
                break
            if slug in cheios:
                continue
            # 22/10 (MR-01): try por ITEM - em 21/10 um ImportError no rebrand (PIL meio-instalado) matou as
            # rodadas de 00:17/01:17/02:17 INTEIRAS (12 canais sem post). Um item quebrado custa 1 vaga, nao a rodada.
            try:
                canal = by[slug]
                if fixo:  # vaga propria do Veo: fica agendada no YouTube com antecedencia, mas sem rajada (16/10: 12
                    alvo, hh = fixo, None  # uploads em 20 min e o padrao do banimento) - fora da janela, 1 por canal por rodada
                    if veo_subidos.get(slug, 0) >= veo_teto_canal[slug]:  # e no maximo o teto do canal no dia
                        esperando_janela.append(f"{canal['nome']} {alvo:%d/%m %H:%M} "
                                                f"(Veo: teto de {veo_teto_canal[slug]} uploads hoje)")
                        continue
                    if not simular and janela_h and alvo > agora + timedelta(hours=janela_h):
                        if slug in veo_adiantado:
                            esperando_janela.append(f"{canal['nome']} {alvo:%d/%m %H:%M} (Veo)")
                            continue
                        veo_adiantado.add(slug)
                else:
                    alvo, hh = escolher_horario(cfg, politica, canal, dia, item["id"], ocup[slug],
                                                recuperar_de=rec_prox if k == 0 else None, ja=ja)
                    if not alvo:
                        sem_video.append(f"{slug} ({dia:%d/%m}: sem horario livre)")
                        continue
                    if hh is None:  # pendente recuperada pelo LIGAR: o proximo canal publica 20 min depois
                        rec_prox = alvo + timedelta(minutes=20)
                    if not simular and janela_h and hh and alvo > agora + timedelta(hours=janela_h):
                        esperando_janela.append(f"{canal['nome']} {alvo:%d/%m %H:%M}")
                        itens.remove(item)  # reservado para este canal nesta rodada; sobe na rodada da hora certa
                        continue
                estrategia = escolher_estrategia(cfg, canal, f"{item['id']}|{canal['slug']}")
                meta = adaptar(cfg, item, canal, estrategia)
                if meta.get("bloqueado"):
                    log(f"rede: {canal['nome']}: {item['id']} BARRADO pelo revisor ({meta['bloqueado']})")
                    continue
                marca = precisa_marca(item, canal)
                if simular:
                    est = "/".join(estrategia[d] for d in ESTRATEGIAS)
                    log(f"[simulacao] {canal['nome']:24} {alvo:%d/%m %H:%M} nota {nota:.0f} {'(troca @) ' if marca else ''}"
                        f"[{est}] <- {item['id']} | {meta['titulo'][:60]}")
                    if item in itens:  # o Veo das vagas proprias nao esta em itens
                        itens.remove(item)
                    ocup[slug].append(alvo)
                    if fixo:
                        veo_subidos[slug] = veo_subidos.get(slug, 0) + 1
                    total += 1
                    continue
                if desligada(politica):
                    log("rede: postagem DESLIGADA no meio da rodada - parando antes do proximo upload")
                    return total
                arquivo = item["mp4"]
                if marca:
                    arquivo = rebrand(cfg, item, canal)
                    # o arquivo com o @ trocado e outro arquivo: herda a aprovacao do original
                    politica.marcar_aprovacao(arquivo, "aprovado", f"herdada de {item['mp4']}")
                # a capa vai NO upload pelo navegador (16/10, dono: nada pela API; antes subia depois pela thumbnails.set).
                # historias: capa IA 9:16 do historias-em-frames ("thumb" no postar.json) — sem @ de canal, vale mesmo com
                # a marca trocada no video
                capa = None
                if ((item["fonte"] == "react" and not marca) or (item["fonte"] == "historias" and item["dados"].get("thumb"))) \
                        and cfg["publish"].get("thumbnail"):
                    thumb = item["json"].parent / (item["dados"].get("thumb") or f"{item['mp4'].stem}_thumb.jpg")
                    capa = thumb if thumb.exists() else None
                status, info = politica.postar_youtube(
                    canal["cred"]["id"], arquivo, meta["titulo"], meta["descricao"], meta["tags"], privacy="private",
                    publish_at=politica.rfc3339(alvo), projeto=politica.PROJETO_REDE, categoria=canal.get("categoria"),
                    idioma=canal.get("idioma", "pt-BR"), sintetico=item["sintetico"], thumbnail=capa, tipo=item["fonte"])
                if status in ("parado", "suspenso"):
                    log(f"rede: {canal['nome']}: {status} - {info}. PAROU TUDO")
                    if status == "suspenso":  # "parado" se repete a cada rodada enquanto o PARADO.json existir
                        from . import notificar
                        notificar.aviso(f"Canal SUSPENSO: {canal['nome']}", f"{info} - a postagem da rede parou toda", nivel="erro")
                    save_json(reg, PB._registro_path(cfg))
                    return total
                if status != "ok":
                    log(f"rede: {canal['nome']}: {item['id']} nao subiu ({status}: {info})")
                    if status in ("cota", "limite", "morto", "reservado"):
                        vagas[slug] = 0
                        cheios.add(slug)  # o resto da rodada (inclusive o Veo dos proximos dias) nao insiste nele
                    continue
                vid = info.rsplit("/", 1)[-1]
                rec = next((r for r in reversed(politica._ler_ledger()) if r.get("video_id") == vid), {})
                publica = rec.get("publish_at") or politica.rfc3339(alvo)
                ocup[slug].append(politica._dt(publica))
                if fixo:
                    veo_subidos[slug] = veo_subidos.get(slug, 0) + 1
                if item in itens:
                    itens.remove(item)
                total += 1
                thumb_st = "navegador" if capa else "sem"
                extra = {"video_id": vid, "url": info, "canal": canal["nome"], "canal_id": canal["cred"]["id"], "canal_slug": slug,
                         "publish_at": publica, "horario": hh, "postado_em": politica.agora().isoformat(timespec="seconds"),
                         "thumb": thumb_st, "comentario": "pendente" if meta["comentario"] else "sem",
                         "comentario_texto": meta["comentario"], "titulo": meta["titulo"], "fonte": item["fonte"],
                         "slug_origem": item.get("slug_origem"), "nota": nota, "marca_trocada": marca, "script": "rede",
                         "estrategia": estrategia}
                reg[item["id"]] = extra
                save_json(reg, PB._registro_path(cfg))
                if item["fonte"] == "react":
                    PB._arquivar(cfg, item["pb"], extra)
                elif item["fonte"] == "veo":
                    _arquivar_veo(item, extra)
                else:
                    _arquivar_historia(cfg, item, extra)
                log(f"rede: {canal['nome']}: AGENDADO {info} -> {publica} ({hh or ('vaga do Veo' if fixo else 'pendente recuperada')}) | {meta['titulo'][:60]}")
            except Exception as e:
                import traceback
                log(f"rede: {slug}: {item.get('id', '?')} FALHOU ({type(e).__name__}: {e}) - pulando o item")
                log("rede: traceback do item:\n" + traceback.format_exc())
                itens_falhos.append(f"{slug}: {item.get('id', '?')} ({type(e).__name__})")
                continue
    n_longos, rec_prox = _agendar_longos(cfg, politica, yp, chans, reg, agora, simular, dias, janela_h, ja, rec_prox)
    total += n_longos
    if itens_falhos and not simular:  # 22/10 (MR-01): avisa 1x por rodada, pelo portao unico do Telegram
        from . import notificar
        notificar.aviso("Rede: item(ns) com erro na rodada",
                        f"{len(itens_falhos)} item(ns) pulados (a rodada seguiu): " + "; ".join(itens_falhos[:6]),
                        nivel="erro")
    if esperando_janela:
        log(f"rede: {len(esperando_janela)} video(s) reservados sobem mais perto do horario: " + ", ".join(esperando_janela))
    if not simular:
        falta = {}
        for x in sem_video:
            falta.setdefault(x.split(" ", 1)[0], []).append(x.split(" ", 1)[1].strip("()"))
        nichos = {c["slug"]: c.get("nicho", "") for c in chans}
        save_json({"em": agora.isoformat(timespec="minutes"),
                   "canais": {s_: {"dias": d_, "nicho": nichos.get(s_, "")} for s_, d_ in falta.items()}},
                  Path(_rc(cfg)["aprendizado"]).with_name("rede_sem_video.json"))
    if sem_video:
        log("rede: SEM VIDEO BOM para: " + ", ".join(sem_video) + " (grave/produza mais desse tema ou aprove os pendentes)")
    if not simular:
        _comentarios(cfg)
    log(f"rede: {total} video(s) {'simulado(s)' if simular else 'agendado(s)'}")
    return total


def comentarios(cfg):
    politica, _ = PB._postador(cfg)
    if desligada(politica):
        return 0
    with Trava(cfg) as t:
        return _comentarios(cfg) if t.ok else 0


def _comentarios(cfg):
    politica, yp = PB._postador(cfg)
    reg = PB._carregar_registro(cfg)
    n = PB.comentarios_pendentes(cfg, politica, yp, reg)
    save_json(reg, PB._registro_path(cfg))
    _extras_studio(cfg, politica, reg)
    return n


def _extras_studio(cfg, politica, reg):
    """Roda extras do Studio (comentário fixado) para vídeos que já abriram (publish_at no passado).
    Máximo 3 por rodada e só vídeos dos últimos 7 dias (antigos ficam sem extras)."""
    extras_py = Path(r"D:\postador-de-videos\bin\youtube_studio_extras.py")
    if not extras_py.exists():
        return
    import subprocess as sp
    agora = politica.agora()
    limite = agora - timedelta(days=7)
    feitos, mudou = 0, False
    for iid, r in reg.items():
        if feitos >= 3:
            break
        if r.get("extras_studio") or r.get("script") != "rede":
            continue
        pub = politica._dt(r.get("publish_at"))
        if not pub or pub > agora:
            continue
        if pub < limite:
            r["extras_studio"] = {"pulado": "antigo"}
            mudou = True
            continue
        vid = r.get("video_id")
        canal_id = r.get("canal_id")
        comentario = r.get("comentario_texto")
        if not vid or not canal_id or not comentario:
            r["extras_studio"] = {"feito": True, "sem_comentario": True}
            continue
        try:
            import sys as _sys
            cmd = [_sys.executable, str(extras_py),
                   "--canal", canal_id, "--video", vid, "--comentario", comentario]
            res = sp.run(cmd, capture_output=True, text=True, timeout=300,
                         encoding="utf-8", errors="replace")
            m = re.search(r"^RESULTADO: (\{.*\})\s*$", res.stdout or "", re.M)
            resultado = json.loads(m.group(1)) if m else {"saida": (res.stderr or res.stdout or "")[-200:].strip()}
            r["extras_studio"] = resultado
            save_json(reg, PB._registro_path(cfg))
            log(f"extras studio: {r.get('canal', '')} {vid} -> {list(resultado.keys())}")
            feitos += 1
        except sp.TimeoutExpired:
            r["extras_studio"] = {"erro": "timeout 300s"}
            save_json(reg, PB._registro_path(cfg))
            feitos += 1
        except Exception as e:  # noqa: BLE001
            log(f"extras studio: {vid} falhou ({e})")
            r["extras_studio"] = {"erro": str(e)[:200]}
            save_json(reg, PB._registro_path(cfg))
    if mudou:
        save_json(reg, PB._registro_path(cfg))


def aprovar(cfg, tudo=False, abrir=True):
    """Revisao humana de TUDO que a rede pode postar (react + historias)."""
    import os
    politica, _ = PB._postador(cfg)
    _, esperando = inventario(cfg, politica)
    esperando += inventario_longos(cfg, politica)[1]
    print(f"{len(esperando)} video(s) esperando aprovacao.\n")
    if tudo:  # sem olhar: só sobe o que a análise de nudez passou (dono 20/10; advertência do hipercool 16/10)
        from . import revisao_nudez
        for it in esperando:
            st, nota = revisao_nudez.portao(it["mp4"])
            if st:
                politica.marcar_aprovacao(it["mp4"], st, nota)
            print(f"  {st or 'fica pendente'}: {it['id']} ({nota})")
        return
    # AB-09 (16/10): folhas de quadros do LOTE (5 quadros x 3 videos, numerados como abaixo) - aprovar olhando, nao no
    # escuro; abre a 1a folha. testes/folhas_quadros.py ja existia, mas ninguem chamava.
    if esperando and abrir:
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "testes"))
            import folhas_quadros as FQ
            pasta = _work(cfg, "folhas_aprovar", datetime.now().strftime("%Y%m%d_%H%M"))
            lista_p = pasta / "lista.json"
            pasta.mkdir(parents=True, exist_ok=True)
            save_json([{"id": it["id"], "mp4": str(it["mp4"]), "titulo": it["dados"].get("titulo", "")} for it in esperando],
                      lista_p)
            sys.argv = ["folhas_quadros.py", str(lista_p), str(pasta)]
            FQ.main()
            primeira = sorted(pasta.glob("folha_*.jpg"))
            print(f"Folhas de quadros em {pasta} ({len(primeira)} folha(s), 3 videos cada, mesma numeracao)\n")
            if primeira:
                os.startfile(str(primeira[0]))
        except Exception as e:  # noqa: BLE001
            print(f"(folhas de quadros nao saíram: {e})\n")
    print("Para cada video: [a]provar  [r]ejeitar  [p]ular  [s]air\n")
    for n, it in enumerate(esperando, 1):
        d = it["dados"]
        print(f"-- {n}/{len(esperando)} -- {it['fonte']} {it.get('slug_origem') or ''} -- {it['mp4'].stat().st_size / 1e6:.0f} MB")
        print(f"   titulo: {d.get('titulo', '')}")
        try:
            from . import revisao_nudez
            v = revisao_nudez.ja_tem(it["mp4"])
            print("   analise de nudez: " + (f"{v['status'].upper()} ({v.get('problemas', 0)} trecho(s))" if v else
                                             "ainda nao feita (o --tudo faz)"))
        except Exception:  # noqa: BLE001
            pass
        if abrir:
            try:
                os.startfile(str(it["mp4"]))
            except Exception as e:  # noqa: BLE001
                print(f"   (nao abriu o player: {e})")
        r = ""
        while r not in ("a", "r", "p", "s"):
            r = input("   > ").strip().lower()[:1]
        if r == "s":
            break
        if r == "p":
            continue
        politica.marcar_aprovacao(it["mp4"], "aprovado" if r == "a" else "rejeitado",
                                  input("   motivo (opcional): ").strip() if r == "r" else "")
