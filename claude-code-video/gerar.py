"""Claude Code Video — Reels de propaganda dos NOSSOS produtos feitos do zero, com o Claude Code como diretor.

Etapas (cada uma gravada em trabalhos/<id>/estado.json; caiu no meio, continua de onde parou):
  1 roteiro   CLAUDE escreve gancho, 4 cenas (fala + texto grande + foto) só com fatos do produtos.json
  2 narracao  edge-tts por cena (tempo de cada palavra = legenda karaokê exata)
  3 imagens   Flow (Nano Banana, 0 crédito) conferido pelo Gemini; falhou -> banco aprovado da marca
  4 plano     CLAUDE OLHA as fotos e decide efeito (texto ATRÁS do assunto / zoom), posição, foco e tamanho;
              pode mandar refazer uma foto ruim
  5 render    cenas quadro a quadro + transições + karaokê + trilha com ducking + −14 LUFS
  6 revisao   CLAUDE OLHA 8 quadros do vídeo pronto; pede ajustes -> refaz só as cenas apontadas (até 2 rodadas)
  7 final     saida/<conta>/<id>.mp4 + .json; o postador posta no Instagram (postador/bin/produto/fila.itens_ccv)

Cota: só COMEÇA um vídeo com cota de certeza (cota_claude.decidir certeza=True). Faltou no meio (SemCota) -> o
trabalho fica "aguardando_cota" com a hora prevista da volta e a tarefa agendada retoma.

    python gerar.py --auto                 (tarefa ClaudeCodeVideo: retoma pendente ou começa um novo se der)
    python gerar.py --conta futebolcom.ia2 [--forcar]   (--forcar ignora a trava de cota; uso manual)
    python gerar.py --continuar <id>
"""
import sem_janela  # noqa: F401 — 28/10 (dona): nenhum filho abre janela na tela (ver CLAUDE.md)
import argparse
import json
import random
import re
import shutil
import subprocess
import sys
import time
import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
sys.path.append(r"D:\postador-de-videos\bin")
sys.path.append(r"D:\video-fila")
import cota_claude  # noqa: E402
import efeitos  # noqa: E402
import motor  # noqa: E402
from produto import kit as kit_mod  # noqa: E402
from produto import video as pv  # noqa: E402

TRABALHOS = RAIZ / "trabalhos"
SAIDA = RAIZ / "saida"
LOG = RAIZ / "estado" / "gerar.log"
TRAVA = RAIZ / "estado" / "gerar.lock"
PROJETO = "claude-code-video"
LEAD = 0.22
MAX_RODADAS = 2


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def cfg():
    return json.loads((RAIZ / "config.json").read_text("utf-8"))


# ───────────────────────────── estado do trabalho ─────────────────────────────

class Trabalho:
    def __init__(self, pasta):
        self.pasta = Path(pasta)
        self.arq = self.pasta / "estado.json"
        self.e = json.loads(self.arq.read_text("utf-8"))

    @classmethod
    def novo(cls, conta, tipo="anuncio"):
        tid = f"{conta.replace('.', '_')}_{datetime.now():%Y%m%d_%H%M%S}"
        pasta = TRABALHOS / tid
        pasta.mkdir(parents=True)
        (pasta / "estado.json").write_text(json.dumps(
            {"id": tid, "conta": conta, "tipo": tipo, "status": "em_andamento", "feitas": [],
             "criado": datetime.now().isoformat(timespec="seconds"), "rodada": 0, "erros": 0},
            ensure_ascii=False, indent=1), "utf-8")
        return cls(pasta)

    @property
    def entretenimento(self):
        return self.e.get("tipo") == "entretenimento"

    def salvar(self):
        tmp = self.arq.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.e, ensure_ascii=False, indent=1), "utf-8")
        tmp.replace(self.arq)

    def feita(self, etapa):
        return etapa in self.e["feitas"]

    def marcar(self, etapa, **dados):
        self.e.update(dados)
        if etapa not in self.e["feitas"]:
            self.e["feitas"].append(etapa)
        self.salvar()


def manual(t):
    """Manual do editor/corretor (em remotion/) de cada tipo de vídeo."""
    return "EDITOR_ENTRETENIMENTO.md" if t.entretenimento else "EDITOR.md"


def kit_trabalho(t):
    """Kit da conta; no ENTRETENIMENTO (26/10, dono: "comece a fazer de entretenimento para os temas dos canais") o
    convite final é seguir o perfil, não "chame no direct"."""
    k = kit_mod.kit(t.e["conta"])
    if t.entretenimento:
        k = {**k, "convite": "Segue pra mais", "convite_voz": f"Segue o perfil pra mais {k.get('tema') or 'histórias'}.",
             "nome_produto": k["marca"], "publico": f"quem curte {k.get('tema')}",
             "voz": "pt-BR-FranciscaNeural"}  # base do clone RVC (tom_base 2_edge_francisca)
    elif t.e.get("elenco"):  # anúncio com voz clonada: mesma base do clone
        k = {**k, "voz": "pt-BR-FranciscaNeural"}
    return k


def pendentes():
    return [Trabalho(p.parent) for p in sorted(TRABALHOS.glob("*/estado.json"))
            if (e := json.loads(p.read_text("utf-8"))).get("status") in ("em_andamento", "aguardando_cota")
            and not e.get("comparacao")]          # testes de modelo são do comparar_modelos.py, não da tarefa


# ───────────────────────────── 1 roteiro (Claude) ─────────────────────────────

REGRAS = """REGRAS DURAS (o vídeo é propaganda real da nossa empresa):
- Use SÓ os fatos listados. Nada inventado: nenhum número, preço, porcentagem, prazo, cliente ou prêmio.
- Nada de telefone, site ou @ na fala ou na tela. O convite final é fixo (já incluído pelo sistema).
- Português do Brasil falado, frases curtas, tom confiante e humano, sem cara de meme.
- As fotos não podem ter texto, letreiro, tela legível nem logotipo (o texto grande quem põe é a edição)."""


def modelo_etapa(etapa):
    """Modelo do OmniRoute para a etapa (config "modelos_etapa"); None = o padrão (Opus 5.5). 26/10: o dono quer
    misturar modelos conforme o desempenho de cada um em cada etapa (comparar_etapas.py mede)."""
    return (cfg().get("modelos_etapa") or {}).get(etapa) or None


def custo_zero():
    """Pontos do Claude Pro de um vídeo do zero: a edição (até 90 turnos) é o grosso; se ela roda em outro modelo
    (26/10: Gemini), o Claude só faz o roteiro."""
    c = cfg()
    edita_claude = (modelo_etapa("editar") or c["modelo"]).startswith("cc/")
    return c["custo_video_zero"] if edita_claude else c.get("custo_so_roteiro", 4)


def _escolher_elenco():
    """28/10 (dona): anúncio com voz clonada de quem adulto conhece; rodízio pelo elenco menos usado."""
    elencos = [e for e in (cfg().get("elencos_anuncio") or [])
               if all((VOZES_RVC / v / f"{v}.pth").exists() for v in e["vozes"].values())]
    if not elencos or not PY_VOZES.exists():
        return None
    usos = {}
    for p in TRABALHOS.glob("*/estado.json"):
        n = (json.loads(p.read_text("utf-8")).get("elenco") or {}).get("nome")
        if n:
            usos[n] = usos.get(n, 0) + 1
    return min(elencos, key=lambda e: (usos.get(e["nome"], 0), random.random()))


def _texto_elenco(el):
    import bordoes
    bs = "\n".join(f"  - {n}: \"{b['texto']}\" ({b['personagem']}, {b['clima']}, {b['duracao_s']} s)"
                   for n, b in bordoes.catalogo().items())
    quem = ", ".join(el["vozes"])
    return f"""
VOZES (elenco "{el['nome']}"): {quem}. Jeito: {el['jeito']}.
- Cada cena tem "quem": um destes nomes. Com 2 ou mais personagens faça DIÁLOGO entre as cenas (um fala, o outro
  responde, cada um no seu jeito); com 1 só, ele narra tudo. Engraçado, mas o PRODUTO e o benefício ficam claros.
- O personagem NÃO diz que usa/recomenda a marca na vida real; ele vive a cena (ex.: Seu Madruga fugindo do trabalho
  descobre que o robô atende o WhatsApp por ele).
- "bordao" (opcional, no máximo 2 no vídeo): o áudio ORIGINAL de um destes entra logo depois da fala da cena. Use só
  onde encaixa na piada; senão deixe "".
{bs}"""


# 01/11: empresas solares (clientes reais) no mesmo motor de animação dos produtos
SOLAR_REGRAS = """EMPRESA DE ENERGIA SOLAR (cliente real, não é software):
- Nada de valor de conta, economia em %, "zerar a conta", prazo de retorno ou garantia. Nada de chatbot/IA/app: as
  "telas" da animação são a conta de luz, o telhado com placas, o inversor, o orçamento pelo WhatsApp da empresa.
- O apresentador (fotos da pessoa que representa a empresa) é o rosto da marca; as fotos geradas mostram casas,
  comércios, sítios e telhados do interior do Pará (sol forte, casas simples ou de alvenaria), nunca paisagem estrangeira.
- Nunca chame o apresentador de "dono" nem de "proprietário": use só o cargo que estiver nos fatos da empresa (na
  Advance, o Luiz é o RESPONSÁVEL). Sem cargo nos fatos = só o nome."""


def prompt_roteiro(k, elenco=None):
    fatos = "\n".join(f"- {f}" for f in k["fatos"])
    extra = _texto_elenco(elenco) if elenco else ""
    campos = '"quem": "", "bordao": "", ' if elenco else ""
    return f"""Você é o diretor de um anúncio em vídeo vertical (Reels, 20 a 30 segundos) do produto abaixo.

PRODUTO: {k['nome_produto']} (marca {k['marca']})
PARA QUEM: {k['publico']}
FATOS PERMITIDOS:
{fatos}
{('EXEMPLO REAL: ' + k['exemplo_real']) if k.get('exemplo_real') else ''}

{REGRAS}
{SOLAR_REGRAS if k.get('solar') else ''}
{extra}
Monte 4 cenas. A cena 1 é o GANCHO (uma dor ou desejo do público, em pergunta ou afirmação forte). As cenas 2 e 3
mostram como o produto resolve. A cena 4 fecha com o benefício principal. Depois do vídeo entra um cartão da marca
com a narração "{k['convite_voz']}" (não escreva isso).

Para cada cena:
- "fala": o que a narradora diz (1 ou 2 frases, no máximo 22 palavras)
- "texto_tela": 2 a 4 palavras FORTES que aparecem enormes na tela (não repita a fala inteira)
- "prompt_en": foto realista em inglês, vertical, com UM assunto principal claro no centro (pessoa do público,
  prato, celular na mão...) e fundo com profundidade; sem texto/letreiro/tela legível
- "efeito": "texto_atras" se o assunto principal é alto e central (o texto vai passar atrás dele), senão "kenburns"

Responda SÓ JSON:
{{"titulo": "título do post (até 60 caracteres, sem nome de concorrente)",
  "cenas": [{{{campos}"fala": "", "texto_tela": "", "prompt_en": "", "efeito": ""}}, ...4],
  "legenda_post": "texto do post com 2 a 4 linhas e convite para o link no perfil",
  "hashtags": ["#..."]}}"""


def prompt_roteiro_entretenimento(k, ja_feitos):
    feitos = "\n".join(f"- {x}" for x in ja_feitos[-30:]) or "- (nenhum ainda)"
    return f"""Você é o roteirista de um canal de ENTRETENIMENTO no Reels/Shorts/TikTok: "{k['marca']}", tema
"{k.get('tema')}". Escreva UM vídeo vertical de 35 a 45 segundos, narrado, que prende do primeiro ao último segundo.

ESCOLHA DA PAUTA: um assunto do tema com curiosidade forte e que dá pra contar em 40 s. NÃO repita estes já feitos:
{feitos}

REGRAS:
- VERDADE: só fatos amplamente documentados (enciclopédia, história conhecida). Nada inventado; se não tem certeza
  de um número/data, não use. Lenda/mistério é contado COMO lenda ("dizem que", "a lenda conta"). Liste as fontes.
- Português do Brasil falado, frases curtas, tom de quem conta um segredo para um amigo. Sem palavrão.
- Gancho na cena 1 que abre uma pergunta SEM entregar a resposta (nada de spoiler do final no começo). A 1ª frase
  começa pelo ABSURDO/conflito, NUNCA por data, ano ou contexto ("Em 1932..." derrubou a retenção em 27/10).
- Cada cena pede uma imagem DIFERENTE e que mostra a ação daquele momento (a virada e o clímax têm imagem própria
  de ação, nunca a mesma pessoa parada).
- Cena 3 ou 4 tem uma VIRADA (o detalhe que ninguém espera). Cena 5 fecha a história e termina com uma pergunta
  curta para o público comentar. Depois entra o cartão com a narração "{k['convite_voz']}" (não escreva isso).
- Nada de marca, logo, pessoa famosa viva retratada de forma ofensiva, violência gráfica ou tema sexual.

JEITO DE NARRAR (aprendido com os canais parceiros da dona, 28/10 — use 1 ou 2 por vídeo, sem forçar):
- Julgue a cena como amigo, não só descreva: "o coitado", "o gênio", "a figura", "o espertinho".
- Um adjetivo inesperado de outro assunto pra descrever o fato ("uma humilhação minimalista", "vingança gourmet").
- Falsa seriedade: conta sério e a virada é absurda/cômica (ou 3 casos que dão certo + 1 que dá errado de um jeito
  ridículo). Só quando o tema permite rir.
- Pergunta final que pega o espectador NELE mesmo quando couber ("você reparou que acabou de prender a respiração?").

Para cada uma das 5 cenas:
- "fala": o que a narradora diz (1 a 3 frases, no máximo 28 palavras)
- "texto_tela": 1 a 4 palavras FORTES que aparecem enormes (não repita a fala inteira)
- "prompt_en": imagem em inglês, vertical, cinematográfica (fotografia realista ou pintura digital realista), UM
  assunto principal claro, luz dramática; sem texto, letreiro, logo ou rosto de pessoa famosa
- "efeito": "kenburns"

Responda SÓ JSON:
{{"titulo": "título do post com provocação (até 60 caracteres)",
  "cenas": [{{"fala": "", "texto_tela": "", "prompt_en": "", "efeito": "kenburns"}}, ...5],
  "fontes": ["onde isso é documentado"],
  "legenda_post": "2 a 4 linhas, termina com a pergunta para comentar",
  "hashtags": ["#..."]}}"""


def _titulos_feitos(conta):
    out = []
    for p in sorted(TRABALHOS.glob(f"{conta.replace('.', '_')}_*/estado.json")):
        r = json.loads(p.read_text("utf-8")).get("roteiro") or {}
        if r.get("titulo"):
            out.append(r["titulo"])
    return out


def etapa_roteiro(t, k):
    if t.entretenimento:
        return etapa_roteiro_entretenimento(t, k)
    modelo = modelo_etapa("roteiro")
    reserva = cfg().get("roteiro_reserva")
    # sem cota do Claude Pro o roteiro vai pro Gemini e a produção não para (26/10, dono); só vale se o roteirista
    # é o Claude (27/10: argon-gemini no roteiro dos anúncios não usa a cota do Claude)
    if reserva and (modelo or cfg()["modelo"]).startswith("cc/") and not cota_claude.decidir(
            cfg().get("custo_so_roteiro", 4), certeza=False)["ligar"]:
        modelo = reserva
    # 01/11: empresa cliente (solar) não usa voz de personagem famoso (Chaves, Silvio...) — narrador clonado
    elenco = t.e.get("elenco") or (None if k.get("cliente") else _escolher_elenco())
    t.e["elenco"] = elenco
    try:
        r = motor.chamar_json(prompt_roteiro(k, elenco), t.pasta, PROJETO, "roteiro", max_turnos=8, modelo=modelo,
                               timeout=cfg().get("prazo_roteiro_s", 600))
    except motor.SemCota:
        if not reserva or modelo == reserva:
            raise
        modelo = reserva
        r = motor.chamar_json(prompt_roteiro(k, elenco), t.pasta, PROJETO, "roteiro", max_turnos=8, modelo=modelo,
                               timeout=cfg().get("prazo_roteiro_s", 600))
    t.e["modelo_roteiro"] = modelo or cfg()["modelo"]
    cenas = r.get("cenas") or []
    if len(cenas) != 4 or not all(c.get("fala") and c.get("texto_tela") and c.get("prompt_en") for c in cenas):
        raise motor.MotorErro(f"roteiro incompleto: {json.dumps(r, ensure_ascii=False)[:300]}")
    if elenco:  # quem fora do elenco = o 1º; bordão que não existe sai; no máximo 2
        import bordoes
        cat, nomes, usados = bordoes.catalogo(), list(elenco["vozes"]), 0
        for c in cenas:
            if c.get("quem") not in elenco["vozes"]:
                c["quem"] = nomes[0]
            if c.get("bordao") not in cat or usados >= 2:
                c["bordao"] = ""
            usados += bool(c["bordao"])
    t.marcar("roteiro", roteiro=r)
    log(f"  [roteiro] {r['titulo']} | " + " / ".join(
        (f"{c['quem']}: " if c.get("quem") else "") + c["texto_tela"] + (f" +{c['bordao']}" if c.get("bordao") else "")
        for c in cenas) + (f" | elenco {elenco['nome']}" if elenco else ""))


def etapa_roteiro_entretenimento(t, k):
    # Gemini direto: não gasta cota do Claude Pro e já provou roteiro válido com 8 turnos
    modelo = cfg().get("roteiro_reserva") or modelo_etapa("roteiro")
    r = motor.chamar_json(prompt_roteiro_entretenimento(k, _titulos_feitos(t.e["conta"])), t.pasta, PROJETO,
                          "roteiro_entretenimento", max_turnos=8, modelo=modelo,
                          timeout=cfg().get("prazo_roteiro_s", 600))
    cenas = r.get("cenas") or []
    if not 4 <= len(cenas) <= 6 or not all(c.get("fala") and c.get("texto_tela") and c.get("prompt_en") for c in cenas):
        raise motor.MotorErro(f"roteiro incompleto: {json.dumps(r, ensure_ascii=False)[:300]}")
    t.e["modelo_roteiro"] = modelo
    t.marcar("roteiro", roteiro=r)
    log(f"  [roteiro entretenimento] {r['titulo']} | " + " / ".join(c["texto_tela"] for c in cenas)
        + f" | fontes: {'; '.join(r.get('fontes') or [])[:150]}")


# ───────────────────────────── 2 narração ─────────────────────────────

def etapa_narracao(t, k):
    falas = [c["fala"] for c in t.e["roteiro"]["cenas"]] + [k["convite_voz"]]
    audio = []
    for i, fala in enumerate(falas):
        mp3, palavras, dur = pv.narrar(fala, t.pasta / f"voz_{i}.mp3", k, log)
        audio.append({"mp3": str(mp3), "palavras": palavras, "dur": dur})
    if t.e.get("elenco") and not t.entretenimento:
        el = t.e["elenco"]
        quem = [c.get("quem") for c in t.e["roteiro"]["cenas"]] + [list(el["vozes"])[0]]
        vozes = [el["vozes"].get(q) or list(el["vozes"].values())[0] for q in quem]
        voz = "+".join(dict.fromkeys(vozes)) if _rodar_clone(t, audio, vozes) else None
    else:
        voz = _clonar(t, k, audio)
    if not voz:
        # dona 28/10: edge puro (Francisca/Thalita/Antonio sem clone) NUNCA vai ao ar; o erro faz a etapa repetir
        raise RuntimeError("clone falhou — voz edge pura é proibida")
    t.marcar("narracao", audio=audio, voz_clonada=voz)
    log(f"  [voz] {sum(a['dur'] for a in audio):.1f}s de narração ({voz or k['voz']})")


NICHO_DO_TEMA = {"curiosidades": "curiosidades", "histórias e mistérios": "historia_mitologia",
                 "filmes e séries": "filme_sem_voz", "finanças": "financas", "humor": "geral"}
VOZES_RVC = Path(r"D:\hipercool-materiais\models\rvc\vozes")
PY_VOZES = Path(r"D:\hipercool-materiais\python\venv_vozes\Scripts\python.exe")


def _escolher_narrador(nicho):
    """Narrador clonado que mais ENCAIXA no nicho (tabela dos Cortes: narradores_nichos.json, só leitura), menos o
    uso AQUI (não grava no rodízio/histórico dos Cortes, que medem views deles)."""
    tabela = json.loads(Path(r"D:\recapd-ambientes\producao\config\narradores_nichos.json").read_text("utf-8"))
    vozes = [p.parent.name for p in VOZES_RVC.glob("*/personagem.json")
             if (p.parent / f"{p.parent.name}.pth").exists() and p.parent.name not in ("lula", "bolsonaro")]
    usos = {}
    for p in TRABALHOS.glob("*/estado.json"):
        v = json.loads(p.read_text("utf-8")).get("voz_clonada")
        if v:
            usos[v] = usos.get(v, 0) + 1
    cands = [(int((tabela.get(v) or {}).get(nicho, (tabela.get(v) or {}).get("geral", 1))) - 0.6 * usos.get(v, 0), v)
             for v in vozes]
    return max(cands)[1] if cands else None


def _clonar(t, k, audio):
    """26/10 (dono): entretenimento com VOZ CLONADA de personagem, como nos Cortes. Base edge Francisca (o RVC mantém
    a duração, então os tempos das palavras do karaokê continuam valendo). Falhou = None (edge puro é proibido)."""
    nicho = NICHO_DO_TEMA.get(str(k.get("tema")), "geral")
    voz = _escolher_narrador(nicho)
    if not voz or not PY_VOZES.exists():
        log("  [clone] sem narrador clonado disponível")
        return None
    if not _rodar_clone(t, audio, [voz] * len(audio)):
        return None
    log(f"  [clone] narrador {voz} (nicho {nicho})")
    return voz


def _rodar_clone(t, audio, vozes):
    """RVC de cada fala com a voz dela (28/10: anúncio com diálogo = 1 voz por cena; 1 lote por voz). Tudo ou nada:
    falhou uma voz = False e a narração repete (edge puro é proibido; misturar clone com edge soaria pior)."""
    pasta = t.pasta / "clone"
    pasta.mkdir(exist_ok=True)
    itens = []
    for i, a in enumerate(audio):
        wav = pasta / f"base_{i}.wav"
        pv._ff(["-i", a["mp3"], "-ar", "48000", "-ac", "1", str(wav)])
        itens.append({"saida": str(pasta / f"clone_{i}.wav"), "tom_base": "2_edge_francisca", "entrada": str(wav)})
    import psutil
    for voz in dict.fromkeys(vozes):
        meus = [it for it, v in zip(itens, vozes) if v == voz]
        lista = pasta / f"lista_{voz}.json"
        lista.write_text(json.dumps(meus, ensure_ascii=False), "utf-8")
        ini = time.time()
        while psutil.virtual_memory().available < 2.5 * 2 ** 30 and time.time() - ini < 1800:
            time.sleep(60)  # o Applio pesa: espera a RAM (até 30 min) em vez de derrubar o PC
        try:
            rc, saida = motor.executar([str(PY_VOZES), r"D:\hipercool-materiais\bin\voz_clonada.py", "lote", voz,
                                        str(lista)], pasta, 3600, baixa=True)
        except subprocess.TimeoutExpired:
            rc, saida = -1, "timeout 60 min"
        if rc or not all(Path(it["saida"]).exists() for it in meus):
            log(f"  [clone] {voz} falhou (rc={rc}): {saida[-200:]}")
            return False
    for it, a in zip(itens, audio):
        pv._ff(["-i", it["saida"], "-c:a", "libmp3lame", "-q:a", "2", a["mp3"]])
    if len(set(vozes)) > 1:
        log(f"  [clone] diálogo: " + ", ".join(dict.fromkeys(vozes)))
    return True


# ───────────────────────────── 3 imagens ─────────────────────────────

FLOW_PRAZO_S = 360


def _flow_com_prazo(k, prompt_en, destino):
    """pv.imagem com prazo: o Flow é fila COMUM (Produto_Videos, MS Energy, Veo) e a espera por notebook livre não
    tem fim (25/10: 28 min parado sem 1 foto). Estourou -> (None, tarefa que segue sozinha)."""
    import concurrent.futures as cf
    ex = cf.ThreadPoolExecutor(max_workers=1)
    fut = ex.submit(pv.imagem, k, prompt_en, destino, log)
    try:
        return fut.result(timeout=FLOW_PRAZO_S), None
    except cf.TimeoutError:
        log(f"    [imagem] Flow ocupado por mais de {FLOW_PRAZO_S // 60} min — uso o banco da marca")
        return None, fut
    finally:
        ex.shutdown(wait=False)


def _salvar_cena(t, i, im):
    im.save(t.pasta / f"img_{i}.png")
    # cópia leve para o Claude olhar (gasta menos que a de 1080x1920)
    im.convert("RGB").resize((540, 960)).save(t.pasta / f"cena_{i + 1}.jpg", quality=85)


def _imagem_cena(t, k, i, prompt_en, evitar):
    destino = t.pasta / f"img_{i}.png"
    im, atrasada = _flow_com_prazo(k, prompt_en, t.pasta / f"flow_{i}.png")
    origem = "flow"
    if im is None:
        im, nome = pv.do_banco(k, evitar)
        origem = f"banco:{nome}" if im is not None else "marca"
        if im is None:
            im = pv.fundo_marca(k)
    _salvar_cena(t, i, im)
    return str(destino), origem, atrasada


def etapa_imagens(t, k):
    imgs, origens, atrasadas = [], [], {}
    for i, c in enumerate(t.e["roteiro"]["cenas"]):
        arq, origem, fut = _imagem_cena(t, k, i, c["prompt_en"],
                                        [o.split(":", 1)[1] for o in origens if o.startswith("banco:")])
        imgs.append(arq)
        origens.append(origem)
        if fut:
            atrasadas[i] = fut
        log(f"  [imagem] cena {i + 1}: {origem}")
    # 27/10: o pedido atrasado do Flow segue e termina minutos depois (o da cena seguinte espera atrás dele e também
    # estoura): a tumba de Qin saiu com 2 cenas de COR LISA e as fotos certas chegaram 6 min depois. Espera as
    # atrasadas (até 15 min no total) e troca a reserva pela do Flow já conferida pela visão.
    import concurrent.futures as cf
    fim = time.time() + 900
    for i, fut in atrasadas.items():
        try:
            im = fut.result(timeout=max(1, fim - time.time()))
        except cf.TimeoutError:
            log(f"  [imagem] cena {i + 1}: a do Flow não chegou em 15 min — fica {origens[i]}")
            continue
        except Exception as e:  # noqa: BLE001
            log(f"  [imagem] cena {i + 1}: a do Flow atrasada falhou ({str(e)[:100]})")
            continue
        if im is None:
            continue
        _salvar_cena(t, i, im)
        log(f"  [imagem] cena {i + 1}: a do Flow chegou atrasada — troquei ({origens[i]} -> flow)")
        origens[i] = "flow"
    t.marcar("imagens", imgs=imgs, origens_img=origens)


# ───────────────────────────── 4 plano (Claude olha as fotos) ─────────────────────────────

def etapa_plano(t, k):
    cenas = t.e["roteiro"]["cenas"]
    lista = "\n".join(f"- cena_{i + 1}.jpg: texto grande \"{c['texto_tela']}\" (efeito sugerido: {c['efeito']})"
                      for i, c in enumerate(cenas))
    prompt = f"""Você é o editor de um Reels vertical 1080x1920. Use a ferramenta Read para OLHAR estas imagens da
pasta atual (uma por cena):
{lista}

Para cada cena decida a edição:
- "efeito": "texto_atras" = o assunto principal é recortado e o texto grande passa ATRÁS dele (fica lindo quando a
  cabeça/topo do assunto invade a faixa do texto); "kenburns" = texto na frente com caixa escura
- "posicao": faixa do texto. "topo" = de 18% a 36% da altura; "meio" = de 33% a 52%. A faixa de 66% a 82% é da
  legenda e NUNCA recebe texto. No texto_atras escolha a faixa onde o assunto encosta por cima do texto, mas sem
  esconder mais da metade das letras
- "foco": [x, y] de 0 a 1, para onde o zoom lento caminha (o rosto ou o produto)
- "tamanho": 0.8 a 1.2 (menor se o fundo é muito poluído)
- "cor": "marca" ({k['cor_hex']}) ou "branco" — o que tiver mais contraste com o fundo daquela faixa
- "refazer": null, ou um novo prompt em inglês SE a foto tem defeito (mão/rosto deformado, texto legível, não
  combina com a cena). Só use se for ruim de verdade.

Responda SÓ JSON: {{"cenas": [{{"efeito": "", "posicao": "", "foco": [0.5, 0.5], "tamanho": 1.0, "cor": "", "refazer": null}}, ...{len(cenas)}]}}"""
    r = motor.chamar_json(prompt, t.pasta, PROJETO, "plano", max_turnos=len(cenas) + 3, modelo=modelo_etapa("plano"))
    plano = r.get("cenas") or []
    if len(plano) != len(cenas):
        raise motor.MotorErro(f"plano com {len(plano)} cenas")
    imgs, origens = list(t.e["imgs"]), list(t.e["origens_img"])
    for i, p in enumerate(plano):
        if p.get("refazer") and not t.e.get(f"refeita_{i}"):
            log(f"  [plano] Claude pediu nova foto na cena {i + 1}")
            imgs[i], origens[i], _ = _imagem_cena(t, k, i, p["refazer"], [])
            t.e[f"refeita_{i}"] = True
    t.marcar("plano", plano=[_normalizar(p) for p in plano], imgs=imgs, origens_img=origens)
    log("  [plano] " + " | ".join(f"{p['efeito']}/{p['posicao']}" for p in t.e["plano"]))


def _normalizar(p):
    foco = p.get("foco") or [0.5, 0.5]
    return {"efeito": p.get("efeito") if p.get("efeito") in ("texto_atras", "kenburns") else "kenburns",
            "posicao": p.get("posicao") if p.get("posicao") in efeitos.POSICOES else "topo",
            "foco": [min(max(float(foco[0]), 0), 1), min(max(float(foco[1]), 0), 1)],
            "tamanho": min(max(float(p.get("tamanho") or 1.0), 0.7), 1.25),
            "cor": "branco" if p.get("cor") == "branco" else "marca"}


# ───────────────────────────── 5 render ─────────────────────────────

def _durs(t):
    a = t.e["audio"]
    durs = [LEAD + x["dur"] + pv.FOLGA + pv.XF for x in a[:-1]]
    durs[0] = max(durs[0], 2.6)
    durs.append(max(3.2, LEAD + a[-1]["dur"] + 1.3))
    return durs


def render_cena(t, k, i, durs):
    p, c = t.e["plano"][i], t.e["roteiro"]["cenas"][i]
    cor = (255, 255, 255) if p["cor"] == "branco" else k["destaque"]
    saida = t.pasta / f"s{i}.mp4"
    usado = efeitos.cena(Image.open(t.e["imgs"][i]), durs[i], saida, c["texto_tela"], cor, p["efeito"],
                         p["posicao"], tuple(p["foco"]), p["tamanho"], log=log)
    if usado != p["efeito"]:
        t.e["plano"][i]["efeito"] = usado
        t.salvar()
    return saida


def _com_pontuacao(palavras, fala):
    """Devolve a pontuação da fala às palavras do edge (que vêm sem ela), para a legenda quebrar no ponto/vírgula
    também DENTRO da fala (25/10: 'cozinha O pedido' grudou duas frases).
    28/10: alinhamento monotônico M:N (ideia do narrative-speech-alignment do Hypit) no lugar da busca de 3 em 3:
    o edge junta número + palavra numa marca só ("199 reais", "24 horas", "Em 1932" — 5 de 94 falas) e aí a
    pontuação e o tempo de cada palavra se perdiam. Cada palavra do roteiro sai com o próprio tempo."""
    import re
    import unicodedata
    from difflib import SequenceMatcher

    def limpo(s):
        s = unicodedata.normalize("NFKD", s)
        return re.sub(r"\W", "", "".join(c for c in s if not unicodedata.combining(c))).lower()

    tokens = fala.split()
    if not palavras or not tokens:
        return list(palavras)
    A = [limpo(x) for x in tokens]
    B = [limpo(w) for w, _, _ in palavras]
    n, m = len(A), len(B)
    INF = float("inf")
    custo = [[INF] * (m + 1) for _ in range(n + 1)]
    volta = [[None] * (m + 1) for _ in range(n + 1)]
    custo[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            c0 = custo[i][j]
            if c0 == INF:
                continue
            passos = []
            if i < n and j < m:
                igual = A[i] == B[j]
                passos.append((1, 1, 0.0 if igual else 0.3 + 0.7 * (1 - SequenceMatcher(None, A[i], B[j]).ratio())))
            for k in (2, 3):  # k palavras do roteiro numa marca do edge ("199 reais")
                if i + k <= n and j < m and "".join(A[i:i + k]) == B[j]:
                    passos.append((k, 1, 0.05))
                if j + k <= m and i < n and A[i] == "".join(B[j:j + k]):  # 1 do roteiro lida em k marcas
                    passos.append((1, k, 0.05))
            if i < n:
                passos.append((1, 0, 0.0 if not A[i] else 0.8))  # não falada (travessão, emoji, sigla pulada)
            if j < m:
                passos.append((0, 1, 0.0 if not B[j] else 0.8))  # falada e não escrita
            for di, dj, c in passos:
                if c0 + c < custo[i + di][j + dj]:
                    custo[i + di][j + dj] = c0 + c
                    volta[i + di][j + dj] = (di, dj)
    grupos, i, j = [], n, m
    while i or j:
        di, dj = volta[i][j]
        grupos.append((i - di, di, j - dj, dj))
        i, j = i - di, j - dj
    saida, antes = [], ""  # antes = palavra escrita e não falada no começo (vai grudada na 1ª falada)
    for i, di, j, dj in reversed(grupos):
        if di and dj:
            s, e = palavras[j][1], palavras[j + dj - 1][2]
            if antes:
                tokens[i], antes = f"{antes} {tokens[i]}", ""
            if di == 1:
                saida.append((tokens[i], s, e))
            else:  # divide o tempo da marca pelas letras de cada palavra
                letras = [max(1, len(A[i + q])) for q in range(di)]
                acc = s
                for q in range(di):
                    fim = e if q == di - 1 else acc + (e - s) * letras[q] / sum(letras)
                    saida.append((tokens[i + q], round(acc, 3), round(fim, 3)))
                    acc = fim
        elif di:  # escrita e não falada: vai junto com a vizinha (não ganha tempo inventado)
            if saida:
                w, s, e = saida[-1]
                saida[-1] = (f"{w} {tokens[i]}", s, e)
            else:
                antes = f"{antes} {tokens[i]}".strip()
        elif saida:  # falada e não escrita: o tempo dela fica com a palavra anterior
            w, s, _ = saida[-1]
            saida[-1] = (w, s, palavras[j][2])
    return [x for x in saida if x[2] > x[1]] or list(palavras)


def gravar_legenda(camada, total, saida):
    n = int(total * pv.FPS) + 1
    p = subprocess.Popen([pv.FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s",
                          f"{pv.W}x{camada.LEG_H}", "-r", str(pv.FPS), "-i", "-", "-c:v", "qtrle", "-pix_fmt", "argb",
                          str(saida)], stdin=subprocess.PIPE)
    try:
        for q in range(n):
            p.stdin.write(camada.quadro_legenda(q / pv.FPS).tobytes())
    finally:
        p.stdin.close()
        p.wait(timeout=600)
    if p.returncode:
        raise RuntimeError("ffmpeg da legenda falhou")


def etapa_render(t, k, so_cenas=None):
    durs = _durs(t)
    segs = []
    for i in range(len(t.e["roteiro"]["cenas"])):
        s = t.pasta / f"s{i}.mp4"
        if so_cenas is None or i in so_cenas or not s.exists():
            render_cena(t, k, i, durs)
        segs.append(s)
    cartao = t.pasta / "s_cartao.mp4"
    if not cartao.exists():
        pv.seg_imagem(pv.card_final(k, Image.open(t.e["imgs"][-1]).convert("RGB")), durs[-1], cartao)
    segs.append(cartao)
    base = t.pasta / "base.mp4"
    inicios, total = pv.emendar(segs, durs, base)

    # legenda agrupada POR FALA: o edge entrega as palavras sem pontuação, então juntando tudo o fim de uma fala
    # grudava no começo da próxima ("WhatsApp Com o", visto na folha de revisão de 25/10)
    falas = [c["fala"] for c in t.e["roteiro"]["cenas"]] + [k["convite_voz"]]
    grupos, ofs = [], []
    for idx, a in enumerate(t.e["audio"]):
        o = inicios[idx] + LEAD + (pv.XF * 0.5 if idx else 0)
        ofs.append(o)
        palavras = _com_pontuacao(a["palavras"], falas[idx])
        grupos += pv._blocos_legenda([(w, s + o, e + o) for w, s, e in palavras])
    camada = pv.Camada(k, t.e["roteiro"]["titulo"], [], grupos, {"gancho": 0, "card": total}, total)
    leg = t.pasta / "legenda.mov"
    gravar_legenda(camada, total, leg)

    trilha = random.choice([x for x in pv.TRILHAS if Path(x).exists()])
    ent = ["-i", str(base), "-i", str(leg)]
    fc = [f"[0:v][1:v]overlay=0:{pv.LEGENDA_Y}[v]"]
    rotas = []
    for idx, a in enumerate(t.e["audio"]):
        ent += ["-i", a["mp3"]]
        ms_ = int(ofs[idx] * 1000)
        fc.append(f"[{2 + idx}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms_}|{ms_}[n{idx}]")
        rotas.append(f"[n{idx}]")
    ni = 2 + len(t.e["audio"])
    ent += ["-stream_loop", "-1", "-i", trilha]
    fc.append(f"{''.join(rotas)}amix=inputs={len(rotas)}:duration=longest:normalize=0,apad,atrim=0:{total:.3f}[voz]")
    fc.append("[voz]asplit=2[voz1][voz2]")
    fc.append(f"[{ni}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
              f"volume={pv.VOL_TRILHA * 2:.3f},afade=t=in:d=0.8,afade=t=out:st={max(total - 1.5, 0):.2f}:d=1.5[mu]")
    fc.append("[mu][voz1]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=400[mud]")
    fc.append("[voz2][mud]amix=inputs=2:duration=first:normalize=0[a]")
    out = t.pasta / "video.mp4"
    pv._ff([*ent, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}", "-c:v",
            "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(pv.FPS), "-c:a", "aac",
            "-b:a", "192k", "-movflags", "+faststart", str(out)], timeout=1800)
    pv.nivelar(out, log)
    t.marcar("render", total=round(total, 2), inicios=inicios, durs=durs, trilha=Path(trilha).name)
    log(f"  [render] {total:.1f}s")


# ───────────────────────────── 6 revisão (Claude olha o vídeo pronto) ─────────────────────────────

def folha_revisao(t):
    """8 quadros (2 por cena) numa folha 4x2 com o número da cena em cada quadro."""
    from PIL import ImageDraw
    out = t.pasta / "video.mp4"
    quadros = []
    for i, (ini, d) in enumerate(zip(t.e["inicios"][:4], t.e["durs"][:4])):
        for f in (0.45, 0.85):
            jpg = subprocess.run([pv.FF, "-v", "error", "-ss", f"{ini + d * f:.2f}", "-i", str(out), "-frames:v", "1",
                                  "-vf", "scale=360:640", "-f", "image2", "-vcodec", "png", "-"], capture_output=True).stdout
            im = Image.open(__import__("io").BytesIO(jpg)).convert("RGB")
            ImageDraw.Draw(im).text((10, 8), f"CENA {i + 1}", fill=(255, 255, 0), font=efeitos._fonte(30),
                                    stroke_width=3, stroke_fill=(0, 0, 0))
            quadros.append(im)
    folha = Image.new("RGB", (360 * 4, 640 * 2))
    for j, im in enumerate(quadros):
        folha.paste(im, ((j // 2) * 360, (j % 2) * 640))
    nome = f"revisao_{t.e['rodada'] + 1}.jpg"
    folha.save(t.pasta / nome, quality=88)
    return nome


def etapa_revisao(t, k):
    nome = folha_revisao(t)
    resumo = "\n".join(f"- cena {i + 1}: texto \"{c['texto_tela']}\", efeito {p['efeito']}, posição {p['posicao']}, "
                       f"cor {p['cor']}, tamanho {p['tamanho']}"
                       for i, (c, p) in enumerate(zip(t.e["roteiro"]["cenas"], t.e["plano"])))
    r = motor.chamar_json(prompt_revisao(nome, resumo), t.pasta, PROJETO, "revisao", max_turnos=4,
                          modelo=modelo_etapa("revisao"))
    _aplicar_revisao(t, k, r)


def prompt_revisao(nome, resumo):
    return f"""Você é o editor-chefe revisando um anúncio vertical antes de ir ao ar. Use Read para OLHAR {nome}
(pasta atual): 8 quadros do vídeo pronto, 2 por cena (coluna = cena; em cima meio da cena, embaixo fim).
Fazem parte do desenho: texto enorme por cena (no efeito texto_atras ele passa de propósito ATRÁS da pessoa/objeto),
legenda karaokê embaixo com uma palavra acesa, cartão final (não mostrado).
Edição atual:
{resumo}

Procure: texto ilegível (pouco contraste), texto escondido demais pelo assunto (mais da metade das letras), texto
cortado na borda, texto em cima de rosto, foto deformada/feia/com letreiro legível, cena que não combina com o texto.

Responda SÓ JSON:
{{"aprovado": true/false, "nota": 1-10, "comentario": "uma frase",
  "ajustes": [{{"cena": 1, "posicao": "topo|meio", "efeito": "texto_atras|kenburns", "cor": "marca|branco",
               "tamanho": 0.9, "foco": [x, y], "refazer": "novo prompt em inglês ou null"}}]}}
Em "ajustes" ponha só as cenas que precisam mudar e só os campos que mudam. Aprovado = nota >= 7 e nada grave."""


def _aplicar_revisao(t, k, r):
    t.e["rodada"] += 1
    t.e.setdefault("revisoes", []).append(r)
    log(f"  [revisão {t.e['rodada']}] nota {r.get('nota')} — {r.get('comentario', '')[:120]}")
    ajustes = [a for a in (r.get("ajustes") or []) if isinstance(a.get("cena"), int) and 1 <= a["cena"] <= 4]
    if r.get("aprovado") or not ajustes or t.e["rodada"] >= MAX_RODADAS + 1:
        t.marcar("revisao")
        return
    mexer = set()
    for a in ajustes:
        i = a["cena"] - 1
        novo = dict(t.e["plano"][i])
        novo.update({c: a[c] for c in ("posicao", "efeito", "cor", "tamanho", "foco") if a.get(c) is not None})
        t.e["plano"][i] = _normalizar(novo)
        if a.get("refazer"):
            t.e["imgs"][i], t.e["origens_img"][i], _ = _imagem_cena(t, k, i, a["refazer"], [])
        mexer.add(i)
    t.salvar()
    log(f"  [revisão] refazendo cenas {sorted(x + 1 for x in mexer)}")
    etapa_render(t, k, so_cenas=mexer)


# ───────────────────── MODO EDITOR: o Claude Code edita em código (Remotion) ─────────────────────
# 25/10 (dono): "não é isso que vejo nos vídeos" — o Claude tem que EDITAR (motion design, texto cinético, telas,
# b-roll), não escolher opção de molde. Referências: Tiago Lemos (nD-niqynHKY) e Marcos de Castro (3eOwboVaX-0).

REMOTION = RAIZ / "remotion"
PAUSA_FALAS = 0.35


def _pub(t):
    return t.pasta / "public"


def _fotos_dono(t, pub, quantas=2):
    """26/10, dono: "não tem nenhuma foto eu como personagem". Fotos dele JÁ APROVADAS pelo revisor de rosto do
    foto_na_hora (as do pipeline de produto; não disputa o Flow): primeiro as desta conta, depois as de outros
    produtos. Grava dono_N.jpg (1080x1920) e dono_N_recorte.png (sem fundo, p/ parallax). [] se não há."""
    try:
        sys.path.append(r"D:\veo\beta")
        import foto_na_hora as fnh
        # 01/11: empresa solar (cliente) = SÓ as fotos aprovadas do dono DELA (kit dono_tag), nunca as do Emerson
        tag_cli = kit_mod.kit(t.e["conta"]).get("dono_tag")
        regs = [r for r in fnh._registros() if r.get("aprovada") and r.get("arquivo") and Path(r["arquivo"]).exists()
                and (r.get("tag") == tag_cli if tag_cli else str(r.get("tag") or "").startswith("produto_"))]
    except Exception as e:  # noqa: BLE001
        log(f"  [dono] fotos indisponíveis: {e}")
        return []
    regs.sort(key=lambda r: (r.get("tag") == f"produto_{t.e['conta']}", r.get("em", "")), reverse=True)
    out = []
    for i, r in enumerate(regs[:quantas], 1):
        im = Image.open(r["arquivo"]).convert("RGB")
        esc = max(pv.W / im.width, pv.H / im.height)
        im = im.resize((round(im.width * esc), round(im.height * esc)))
        x, y = (im.width - pv.W) // 2, max(0, (im.height - pv.H) // 3)
        im = im.crop((x, y, x + pv.W, y + pv.H))
        im.save(pub / f"dono_{i}.jpg", quality=92)
        item = {"foto": f"dono_{i}.jpg", "cenario": r.get("cenario")}
        # 27/10: o rembg travou 20 min com CPU 0 (com os Chromes do Flow abertos) -> prazo; estourou = sem recorte
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as Prazo
        ex = ThreadPoolExecutor(1)
        try:
            mascara, _ = ex.submit(efeitos.recorte, im).result(timeout=120)
        except Prazo:
            log(f"  [dono] recorte da foto {i} passou de 2 min — sigo com a foto inteira")
            mascara = None
        ex.shutdown(wait=False)
        if mascara is not None:
            rec = im.convert("RGBA")
            rec.putalpha(mascara)
            rec.crop(mascara.getbbox()).save(pub / f"dono_{i}_recorte.png")
            item["recorte"] = f"dono_{i}_recorte.png"
        out.append(item)
    log(f"  [dono] {len(out)} foto(s) do dono aprovadas: " + ", ".join(Path(r['arquivo']).name for r in regs[:quantas]))
    return out


def etapa_preparar_editor(t, k):
    """Junta a narração num mp3 só (com pausas), tempos ABSOLUTOS das palavras, fotos, trilha e briefing.json."""
    pub = _pub(t)
    pub.mkdir(exist_ok=True)
    falas = [c["fala"] for c in t.e["roteiro"]["cenas"]] + [k["convite_voz"]]
    lista, palavras, cenas, cursor = [], [], [], 0.4
    silencio = t.pasta / "silencio.mp3"
    pv._ff(["-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{PAUSA_FALAS}", "-c:a", "libmp3lame",
            str(silencio)])
    inicio = t.pasta / "inicio.mp3"
    pv._ff(["-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.4", "-c:a", "libmp3lame", str(inicio)])
    pv._ff(["-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.15", "-c:a", "libmp3lame",
            str(t.pasta / "respiro.mp3")])
    lista.append(inicio)
    rc_cenas = t.e["roteiro"]["cenas"]
    for i, a in enumerate(t.e["audio"]):
        ini = cursor
        quem = rc_cenas[i].get("quem") if i < len(rc_cenas) else None
        for w, s, e in _com_pontuacao(a["palavras"], falas[i]):
            palavras.append({"p": w, "ini": round(ini + s, 3), "fim": round(ini + e, 3), "cena": i + 1,
                             **({"falante": quem} if quem else {})})
        cursor += a["dur"]
        lista.append(Path(a["mp3"]))
        extra = {}
        nome_b = rc_cenas[i].get("bordao") if i < len(rc_cenas) else None
        if nome_b:  # 28/10: bordão GRAVADO (não clonado) logo depois da fala, no mesmo formato da narração
            import bordoes
            b = bordoes.catalogo().get(nome_b)
            if b:
                arq = t.pasta / f"bordao_{i}.mp3"
                r = subprocess.run([pv.FFPROBE, "-v", "error", "-select_streams", "a:0", "-show_entries",
                                    "stream=sample_rate,channels", "-of", "csv=p=0", a["mp3"]],
                                   capture_output=True, text=True)
                sr, ch = (r.stdout.strip().split(",") + ["24000", "1"])[:2]
                pv._ff(["-i", str(bordoes.PASTA / b["arquivo"]), "-ar", sr, "-ac", ch, "-c:a", "libmp3lame",
                        "-q:a", "2", str(arq)])
                cursor += 0.15
                lista += [t.pasta / "respiro.mp3", arq]
                # 29/10: bordão sem fala ("(risada do Pica-Pau)") ia escrito na tela como descrição -> onomatopeia
                tela = b["texto"] if not b["texto"].startswith("(") else ONOMATOPEIA.get(b["personagem"], "")
                extra["bordao"] = {"nome": nome_b, "texto": tela, "personagem": b["personagem"],
                                   "ini": round(cursor, 2), "fim": round(cursor + b["duracao_s"], 2)}
                cursor += b["duracao_s"]
        cursor += PAUSA_FALAS
        cenas.append({"n": i + 1, "ini": round(ini, 2), "fim": round(cursor, 2), "fala": falas[i],
                      **({"quem": quem} if quem else {}), **extra,
                      **({"texto_forte": rc_cenas[i]["texto_tela"], "foto": f"img_{i + 1}.jpg"}
                         if i < len(rc_cenas) else {"cartao_final": True})})
        lista.append(silencio)
    duracao = round(cursor + 1.2, 2)
    txt = t.pasta / "concat.txt"
    txt.write_text("".join(f"file '{p.as_posix()}'\n" for p in lista), "utf-8")
    pv._ff(["-f", "concat", "-safe", "0", "-i", str(txt), "-ar", "48000", "-ac", "2", "-c:a", "libmp3lame", "-q:a", "2",
            str(pub / "narracao.mp3")])
    shutil.copy2(random.choice([x for x in pv.TRILHAS if Path(x).exists()]), pub / "trilha.mp3")
    for i, arq in enumerate(t.e["imgs"]):
        Image.open(arq).convert("RGB").resize((pv.W, pv.H)).save(pub / f"img_{i + 1}.jpg", quality=92)
    if cfg().get("vivo", True):  # 28/10: profundidade, camadas, recorte e fundo limpo (do historias-em-frames)
        import camadas
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as Prazo
        feitos = []
        for c in cenas:
            if not c.get("foto"):
                continue
            ex = ThreadPoolExecutor(1)
            try:
                c["vivo"] = ex.submit(camadas.preparar, pub / c["foto"], pub, c["n"], efeitos.recorte, log).result(
                    timeout=180)
                feitos.append(f"{c['n']}:{'+'.join(k for k in ('profundidade', 'recorte') if c['vivo'].get(k))}")
            except Prazo:
                log(f"  [vivo] cena {c['n']} passou de 3 min — sigo sem as camadas dela")
            ex.shutdown(wait=False)
        log(f"  [vivo] {' '.join(feitos)}")
    hexa = lambda c: "#%02X%02X%02X" % tuple(c)  # noqa: E731
    briefing = {"marca": k["marca"], "produto": k["nome_produto"], "publico": k["publico"], "fatos": k["fatos"],
                "cores": {"marca": k["cor_hex"], "apoio": hexa(k["apoio"]), "fundo_escuro": hexa(k["escuro"]),
                          "destaque": hexa(k["destaque"]), "texto_sobre_marca": hexa(k["texto"])},
                "arroba": k["arroba"], "convite": k["convite"], "titulo": t.e["roteiro"]["titulo"],
                "duracao_s": duracao, "cenas": cenas, "palavras": palavras}
    if k.get("solar"):  # 01/11: o editor também lê as regras da empresa solar
        briefing["regras_empresa"] = SOLAR_REGRAS
    if not t.entretenimento:
        briefing["dono"] = _fotos_dono(t, pub)
    # 29/10: profundidade + recorte ficavam presos no processo (medido: 2,2 GB -> 0,66 GB ao soltar) durante as 2 h de
    # render e júri; com a memória virtual do PC esgotada o Chrome do render parava ("travou 20 min")
    import gc
    import camadas
    camadas._sess = None
    efeitos._sessao_rembg = None
    gc.collect()
    if (cfg().get("referencias") or {}).get("ligado"):  # 28/10: estudo de um vídeo que deu certo (referencia.py)
        try:
            import referencia
            ref = referencia.para_video("entretenimento" if t.entretenimento else "anuncio", pub, t.e["id"])
        except Exception as e:  # noqa: BLE001 — sem referência o vídeo segue como antes
            ref = None
            log(f"  [referência] falhou: {e}")
        if ref:
            briefing["referencia"] = ref
            t.e["referencia"] = ref["nome"]
            log(f"  [referência] {ref['nome']} (estudo em public/referencia/)")
    (pub / "briefing.json").write_text(json.dumps(briefing, ensure_ascii=False, indent=1), "utf-8")
    pasta_src = REMOTION / "src" / "videos" / t.e["id"]
    pasta_src.mkdir(parents=True, exist_ok=True)
    (pasta_src / "index.ts").write_text("import {registerRoot} from 'remotion';\nimport {Raiz} from './Video';\n\n"
                                        "registerRoot(Raiz);\n", "utf-8")
    t.marcar("preparar_editor", duracao_editor=duracao)
    log(f"  [editor] material pronto ({duracao}s, {len(palavras)} palavras)")


def etapa_editar(t, k):
    tid = t.e["id"]
    quadros = t.pasta / "quadros"
    quadros.mkdir(exist_ok=True)
    ja = (REMOTION / "src" / "videos" / tid / "Video.tsx").exists()
    erro_render = t.e.get("erro_render")
    prompt = f"""Leia {manual(t)} (pasta atual) e siga à risca. Você vai editar o vídeo de ID `{tid}`.
- Pasta pública (material + briefing.json): {_pub(t)}
- Seu código: src/videos/{tid}/Video.tsx  (index.ts já existe)
- PROIBIDO abrir/ler/copiar as outras pastas de src/videos/ (são vídeos de outros trabalhos): crie a edição do zero.
- Pasta para os quadros de conferência: {quadros}
{('Canal de entretenimento: ' + k['marca'] + ' (tema ' + str(k.get('tema')) + ')') if t.entretenimento else
 ('Produto: ' + k['nome_produto'] + ' (' + k['marca'] + ')')}. Duração: {t.e['duracao_editor']} s.
{'O Video.tsx JÁ EXISTE de uma sessão anterior que foi interrompida: leia, continue e termine (não recomece do zero).' if ja else ''}
{('O render final FALHOU com este erro, conserte: ' + erro_render) if erro_render else ''}
Faça um trabalho de agência: motion design de verdade, não slides."""
    modelo = t.e.get("modelo_editor") or modelo_etapa("editar")
    with _so_este_video(tid):
        # Argon (27/10): ~200 s por passo contra ~56 s do Gemini 3.8 -> prazo na config
        texto = motor.chamar(prompt, REMOTION, PROJETO, "editar", timeout=cfg().get("prazo_editor_s", 5400), max_turnos=90,
                             ferramentas=motor.EDITOR, modelo=modelo, aceitar_limite=True)
    t.marcar("editar", resumo_editor=texto[-600:], erro_render=None)
    log(f"  [editor] {modelo or 'Opus 5.5'} terminou a edição: {texto[-200:]}")


@contextmanager
def _so_este_video(tid):
    """O editor copiava a edição de outro vídeo da pasta ao lado (26/10): durante a sessão só a dele fica visível."""
    videos, guardados = REMOTION / "src" / "videos", RAIZ / "estado" / "videos_guardados"
    guardados.mkdir(exist_ok=True)
    for p in guardados.iterdir():           # sobra de sessão que caiu no meio
        if not (videos / p.name).exists():
            shutil.move(str(p), str(videos / p.name))
    outros = [p for p in videos.iterdir() if p.name != tid]
    for p in outros:
        shutil.move(str(p), str(guardados / p.name))
    try:
        yield
    finally:
        for p in outros:
            shutil.move(str(guardados / p.name), str(p))


# erro do Chrome/máquina, não do código (27/10: CPU a 100% -> "Timed out evaluating page function" em 30 s)
_RENDER_PASSAGEIRO = re.compile(r"Timed out evaluating page function|Target closed|Session closed|"
                                r"Navigation timeout|ECONNRESET|Cannot allocate memory|browser has disconnected|"
                                r"write EOF|EPIPE|render travou", re.I)  # 27/10: write EOF = filho do Remotion morreu (o código rendia)
# 28/10: "render travou 20 min" (máquina sem RAM) ia para o corretor como se fosse erro de código (15 min perdidos)


def _virtual_livre_gb():
    """Memória VIRTUAL livre (commit) do Windows — é ela que acaba (29/10: 0,07 GB), não a RAM física."""
    import ctypes

    class M(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [
            (n, ctypes.c_ulonglong) for n in ("tf", "af", "tp", "ap", "tv", "av", "ae")]
    m = M()
    m.dwLength = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ap / 2 ** 30


def _render(t, out):
    cmd = ["npx.cmd", "remotion", "render", f"src/videos/{t.e['id']}/index.ts", "Main", str(out),
           f"--public-dir={_pub(t)}", "--log=error", "--crf=18", "--concurrency=2", "--timeout=120000"]
    saida = ""
    for tentativa in (1, 2):           # o Chrome do Remotion às vezes trava (26/10: 2h20 parado); 2ª tentativa limpa
        ini = time.time()
        while _virtual_livre_gb() < 3 and time.time() - ini < 900:
            time.sleep(60)  # 29/10: render começado sem memória virtual ficava parado até o limite de 20 min
        try:
            rc, saida = motor.executar(cmd, REMOTION, timeout=1200, baixa=True)
        except subprocess.TimeoutExpired:
            log(f"  [render] travou 20 min (tentativa {tentativa}), processos mortos")
            saida = "render travou 20 min"
            continue
        if not rc and out.exists():
            return True, ""
        (t.pasta / "erro_render.txt").write_text(saida, "utf-8")
        if not _RENDER_PASSAGEIRO.search(saida):
            break
        log(f"  [render] erro passageiro do Chrome (tentativa {tentativa}), tento de novo")
        time.sleep(60)
    return False, saida[-2500:]


ONOMATOPEIA = {"pica_pau": "HA-HA-HA-HA-HA!", "quico": "HUA HUA HUA!"}  # sem chave (plateia) = sem texto na tela


class RenderPassageiro(RuntimeError):
    """Chrome/máquina (sem RAM, disco cheio, CPU a 100%), não o código: não gasta as 3 tentativas do trabalho."""


def etapa_render_remotion(t, k):
    out = t.pasta / "video.mp4"
    ok, erro = _render(t, out)
    if not ok:
        if _RENDER_PASSAGEIRO.search(erro):
            # máquina/Chrome, não código: a edição fica e a próxima rodada da tarefa só renderiza de novo
            raise RenderPassageiro(f"render do Remotion falhou (Chrome/máquina): {erro[-300:]}")
        # volta para o Claude consertar (1 vez por falha; o contador de erros do trabalho limita)
        t.e["feitas"].remove("editar")
        t.e["erro_render"] = erro
        t.salvar()
        raise RuntimeError(f"render do Remotion falhou: {t.e['erro_render'][-300:]}")
    pv.nivelar(out, log)
    t.marcar("render_remotion", total=round(pv._dur(out), 2), rodada=0,
             revisoes=[{"nota": None, "comentario": t.e.get("resumo_editor", "")[:200]}])
    log(f"  [render] Remotion {t.e['total']}s")


# ───────────────────── lapidar: verificadores em paralelo + corretor (26/10) ─────────────────────
# O dono: "quantos corretores e verificadores precisar pra subir a nota", Gemini com raciocínio no máximo.

VERIFICADORES = {
    "legibilidade": """LEGIBILIDADE E ENQUADRAMENTO. Procure: texto cortado ou saindo da tela; texto/elemento importante
acima de y=150 ou abaixo de y=1580 (de 1920 — lá ficam os botões do Reels) ou a menos de 60 px da lateral; letra
pequena demais para ler no celular (corpo < ~34 px no vídeo 1080x1920); pouco contraste; elemento cobrindo rosto ou
outro texto; legenda/karaokê quebrando palavra.
Trabalhe pela folha.jpg e abra em tamanho grande NO MÁXIMO 8 quadros (os suspeitos que a folha mostra) — 29/10: abrir
quadro por quadro levava 20–24 turnos e estourava o prazo em 10 de 61 vezes (o vídeo ficava sem esta nota).""",
    "movimento": """MOTION DESIGN. Procure: cena vazia (só foto + legenda, sem elemento gráfico vivo); quadros da mesma
cena praticamente iguais (nada se move/entra/sai); entrada de elemento sem animação; ritmo arrastado; transição
seca entre cenas; tudo com o mesmo molde repetido em todas as cenas (falta variedade de layout).""",
    "roteiro_marca": """ROTEIRO, SINCRONIA E MARCA. Procure: o que está na tela não combina com a fala daquele momento;
informação inventada (número, preço, prazo, cliente que não está nos fatos); erro de português; cores fora da
paleta da marca; cartão final sem nome do produto, sem convite ou sem o @; mockup com texto genérico/placeholder
("Prato 1", "Lorem", "Descrição").""",
    "diretor": """DIRETOR DE CRIAÇÃO DE AGÊNCIA. Julgue o todo: o gancho prende nos 2 primeiros segundos? Parece anúncio
profissional ou slide? Diga as 3 mudanças de MAIOR impacto para este vídeo subir de nível (seja concreto: o quê,
em qual cena, como).""",
}


MOV_MIN = 4


def _quadros_lapidar(t, pasta):
    """3 quadros por cena (20/50/80% dela) em tamanho meio-HD + folha geral; devolve a legenda de cada quadro."""
    br = json.loads((_pub(t) / "briefing.json").read_text("utf-8"))
    return quadros_e_movimento(t.pasta / "video.mp4", pasta, br["cenas"])[0]


def quadros_e_movimento(mp4, pasta, cenas):
    """Para QUALQUER vídeo (vertical ou deitado) de qualquer linha. cenas = [{"n", "ini", "fim", "fala"}] (tempos em
    s). Grava q01.jpg... (3 por cena: 20/50/80%) e folha.jpg (1 linha por cena) em `pasta`.
    Devolve (itens para o júri, [% de movimento por cena]). < MOV_MIN = cena PARADA."""
    from PIL import ImageChops, ImageStat
    pasta.mkdir(parents=True, exist_ok=True)
    itens, ims, mov, pcts = [], [], [], []
    for c in cenas:
        for frac in (0.2, 0.5, 0.8):
            seg = round(c["ini"] + (c["fim"] - c["ini"]) * frac, 2)
            nome = f"q{len(itens) + 1:02d}.jpg"
            pv._ff(["-ss", f"{seg}", "-i", str(mp4), "-frames:v", "1", "-vf", "scale='min(960,iw)':-2",
                    "-q:v", "3", str(pasta / nome)])
            itens.append(f"{nome}: cena {c['n']}, {seg}s, fala da cena: \"{c.get('fala', '')}\"")
            im = Image.open(pasta / nome).convert("RGB")
            larg = 270 if im.height > im.width else 480
            ims.append(im.resize((larg, round(larg * im.height / im.width))))
        # 26/10: os verificadores viam "cena congelada" e o editor (que só olha stills) não percebia: medida objetiva
        dif = sum(ImageStat.Stat(ImageChops.difference(ims[-3].convert("L"), ims[-1].convert("L"))).mean) / 2.55
        pcts.append(round(dif, 1))
        mov.append(f"cena {c['n']}: mudança de imagem entre 20% e 80% da cena = {dif:.1f}%"
                   + (" -> PARADA (medido)" if dif < MOV_MIN else ""))
    itens.append("MOVIMENTO MEDIDO POR CENA (abaixo de " + f"{MOV_MIN}% = cena parada):\n" + "\n".join(mov))
    w, h = ims[0].size
    folha = Image.new("RGB", (w * 3, h * len(cenas)))
    for i, im in enumerate(ims):
        folha.paste(im.resize((w, h)), ((i % 3) * w, (i // 3) * h))
    folha.save(pasta / "folha.jpg", quality=88)
    return itens, pcts


# Júri para vídeo de ENTRETENIMENTO (recap de manhwa/anime, doramas, curiosidades, cortes) — 26/10, dono: "o seu
# sistema não é só pra propaganda, a maioria dos outros é entretenimento". Mesma função, outros focos.
VERIFICADORES_ENTRETENIMENTO = {
    "legibilidade": VERIFICADORES["legibilidade"],
    "movimento": """RITMO E MOVIMENTO. Procure: imagem/painel parado com a narração andando (veja o MOVIMENTO MEDIDO);
cena que dura demais para o que conta; corte seco sem intenção; zoom/pan que não segue o foco da ação; troca de
cena que não bate com a mudança da narração; final parado ou cortado no meio da frase.""",
    "historia": """HISTÓRIA E SINCRONIA. Procure: imagem que não mostra o que a narração diz NAQUELE momento
(personagem errado, cena de outro momento); legenda diferente da fala; nome de personagem trocado; erro de
português; gancho que só entende quem já conhece a obra; informação que contradiz a obra; spoiler do final logo
no começo sem intenção; marca d'água de site/scan ou legenda queimada da fonte visível.""",
    "retencao": """DIRETOR DE RETENÇÃO (YouTube/Shorts/TikTok). O gancho dos 2 primeiros segundos faz a pessoa ficar?
Há um motivo para continuar assistindo a cada ~5 s (pergunta aberta, virada, revelação)? O título/tarja/CTA no
meio ajuda ou atrapalha? Diga as 3 mudanças de MAIOR impacto na retenção (concretas: o quê, em qual cena, como).""",
}
# HIPERCOOL/manhwa com censura: some este foco (reprovado continua travando o vídeo no pipeline da linha)
FOCO_CENSURA = """CENSURA E SEGURANÇA. Procure: nudez ou parte íntima visível (mesmo parcial, mesmo por 1 quadro);
mosaico/borrão fora do lugar, pequeno demais ou cobrindo a tela inteira (censura é SÓ na parte); conteúdo sexual
explícito; violência gráfica que derruba monetização."""


MODELO_RESERVA = "antigravity/gemini-3.8-flash-tiered"


def verificar_generico(pasta, itens, foco, texto_foco, descricao, regras_extra, modelo, projeto=PROJETO):
    """1 verificador do júri, para QUALQUER linha. `pasta` tem folha.jpg + quadros; `itens` = legenda de cada quadro
    (+ o bloco de movimento medido). Devolve {foco, nota, problemas[], elogios[]} ou None."""
    prompt = f"""Você é um VERIFICADOR exigente de {descricao}. Seu foco único: {texto_foco}

Use Read para OLHAR folha.jpg (visão geral, cada linha = uma cena) e depois abra os quadros que precisar em tamanho
maior. Quadros:
{chr(10).join(itens)}
{regras_extra}

Pense com calma e a fundo antes de responder. Seja duro: nota 10 = nível profissional top, sem nenhum defeito do
seu foco. Aponte só problemas reais que você VIU, com o quadro.
Responda SÓ JSON: {{"nota": 0-10, "problemas": [{{"quadro": "q03.jpg", "cena": 1, "gravidade": "grave|media|leve",
"problema": "...", "como_corrigir": "instrução concreta"}}], "elogios": ["o que está bom e deve ficar"]}}"""
    # 26/10: o gateway às vezes responde "unrecognized_model" para o -high e 18 quadros estouram 20 turnos -> 2ª
    # tentativa com o modelo reserva e mais turnos (o júri de entretenimento perdeu 2 de 4 verificadores assim)
    for tentativa, (m, turnos) in enumerate(((modelo, 30), (MODELO_RESERVA, 40))):
        try:
            r = motor.chamar_json(prompt, pasta, projeto, f"verificar_{foco}", timeout=900, max_turnos=turnos, modelo=m)
            return {"foco": foco, "nota": float(r.get("nota") or 0), "problemas": r.get("problemas") or [],
                    "elogios": r.get("elogios") or [], "modelo": m}
        except motor.MotorErro as e:
            log(f"    [verificador {foco}] {m} falhou: {str(e)[:150]}")
    return None


def _verificar(t, k, pasta, itens, foco, texto_foco, modelo):
    if t.entretenimento:
        r = t.e["roteiro"]
        return verificar_generico(
            pasta, itens, foco, texto_foco,
            f"um vídeo vertical de entretenimento do canal \"{k['marca']}\" (tema {k.get('tema')}), título "
            f"\"{r['titulo']}\"",
            f"Fontes que o roteirista citou: {'; '.join(r.get('fontes') or []) or '(nenhuma)'}. Afirmação falsa ou "
            f"lenda contada como fato = grave. O @ {k['arroba']} no cartão final é a conta oficial (obrigatório).",
            modelo)
    return verificar_generico(
        pasta, itens, foco, texto_foco,
        f"um anúncio Reels (1080x1920) do produto {k['nome_produto']} ({k['marca']})",
        f"Fatos permitidos do produto: {'; '.join(k['fatos'])}\nO perfil {k['arroba']} é a conta oficial que posta o "
        f"anúncio: o @ dele no final é OBRIGATÓRIO, não é erro." + (
            f"\nO anúncio é FALADO POR PERSONAGEM conhecido ({t.e['elenco']['nome']}, voz clonada) de propósito: o "
            f"selo pequeno com o nome de quem fala e o BORDÃO dele escrito grande na hora em que o áudio do bordão "
            f"toca (ex.: \"AI, EU NÃO DIGO!\", \"HA-HA-HA!\") são a PIADA do anúncio, não texto irrelevante. Defeito é "
            f"só: descrição técnica vazando como texto (\"(risada de...)\", nome de arquivo), bordão ilegível ou "
            f"cobrindo rosto/produto." if t.e.get("elenco") else ""), modelo)


def _copiar_src(de, para):
    shutil.rmtree(para, ignore_errors=True)
    shutil.copytree(de, para)


def etapa_lapidar(t, k):
    from concurrent.futures import ThreadPoolExecutor
    c = {"ligado": True, "modelo": "agy/gemini-3.8-flash-high", "alvo": 9, "rodadas": 4, **(cfg().get("lapidar") or {})}
    if not c["ligado"]:
        t.marcar("lapidar")
        return
    tid, modelo = t.e["id"], c["modelo"]
    # 27/10 (dona): o Argon CRIA (corretor/aprendiz) e o júri continua no mesmo modelo, para a nota ser comparável
    criador = c.get("modelo_corretor") or modelo
    src = REMOTION / "src" / "videos" / tid
    base = t.pasta / "lapidar"
    melhor_src, melhor_mp4 = base / "melhor_src", base / "melhor.mp4"
    rodadas = t.e.setdefault("lapidar", [])
    melhor = max((r["nota"] for r in rodadas), default=-1)
    quebrou = False
    mp4 = t.pasta / "video.mp4"
    if max(p.stat().st_mtime for p in src.glob("*.tsx")) > mp4.stat().st_mtime:
        # retomada: o corretor mexeu no código e o processo caiu antes do render
        ok, erro = _render(t, mp4)
        if ok:
            pv.nivelar(mp4, log)
        elif melhor_src.exists():
            log(f"  [lapidar] render da retomada falhou, volto para a melhor versão: {erro[-200:]}")
            _copiar_src(melhor_src, src)
            shutil.copy2(melhor_mp4, mp4)
    while True:
        n = len(rodadas) + 1
        pasta = base / f"r{n}"
        itens = _quadros_lapidar(t, pasta)
        juri = VERIFICADORES_ENTRETENIMENTO if t.entretenimento else VERIFICADORES
        with ThreadPoolExecutor(len(juri)) as ex:
            vs = [v for v in ex.map(lambda f: _verificar(t, k, pasta, itens, f, juri[f], modelo), juri) if v]
        if not vs:
            raise motor.MotorErro("nenhum verificador respondeu")
        nota = round(sum(v["nota"] for v in vs) / len(vs), 2)
        texto_ruim = []
        if not t.entretenimento:
            # trava de texto do postador (26/10: barrou vídeos daqui por "Entrega: 99.4%", "998 contatos", "#142")
            from produto import editor as editor_produto
            texto_ruim = editor_produto.problemas_texto(src, k)
        graves = [p for v in vs for p in v["problemas"] if p.get("gravidade") == "grave"] + [
            {"gravidade": "grave", "problema": f"texto na tela fora dos fatos: {x}"} for x in texto_ruim]
        rodadas.append({"rodada": n, "nota": nota, "graves": len(graves), "trava_texto": texto_ruim,
                        "notas": {v["foco"]: v["nota"] for v in vs}, "verificadores": vs})
        t.salvar()
        log(f"  [lapidar] rodada {n}: nota {nota} ({', '.join(f'{v['foco']} {v['nota']:g}' for v in vs)}), "
            f"{len(graves)} grave(s), trava de texto {len(texto_ruim)}")
        if nota > melhor:
            melhor = nota
            _copiar_src(src, melhor_src)
            shutil.copy2(t.pasta / "video.mp4", melhor_mp4)
        sem_melhora = len(rodadas) >= 3 and max(r["nota"] for r in rodadas[-2:]) <= max(
            r["nota"] for r in rodadas[:-2])
        if (nota >= c["alvo"] and not graves) or n >= c["rodadas"] or sem_melhora:
            if sem_melhora:
                log("  [lapidar] 2 rodadas sem superar a melhor nota: paro aqui")
            break
        # corretor: junta tudo dos verificadores, do mais grave ao mais leve
        ordem = {"grave": 0, "media": 1, "leve": 2}
        probs = sorted(((p, v["foco"]) for v in vs for p in v["problemas"]),
                       key=lambda x: ordem.get(x[0].get("gravidade"), 1))
        lista = "\n".join([f"- [grave] (trava de texto) {x} -> troque por texto SEM número/prazo/porcentagem/preço "
                           f"inventado (só o que está nos fatos)" for x in texto_ruim] +
                          [f"- [{p.get('gravidade')}] ({foco}) {p.get('quadro')} cena {p.get('cena')}: "
                           f"{p.get('problema')} -> {p.get('como_corrigir')}" for p, foco in probs])
        elogios = "\n".join(f"- {e}" for v in vs for e in v["elogios"])
        antes = "\n".join(f"- {p.get('problema')}" for v in (rodadas[-2]["verificadores"] if len(rodadas) > 1 else [])
                          for p in v["problemas"] if p.get("gravidade") == "grave")
        prompt = f"""Leia {manual(t)} (pasta atual). Você é o CORRETOR da edição do vídeo `{tid}` (código em
src/videos/{tid}/). A edição já existe e foi renderizada; {len(vs)} verificadores deram nota média {nota}/10.
NÃO recomece do zero: corrija os problemas abaixo no código, do mais grave ao mais leve, sem estragar o que foi
elogiado. PROIBIDO abrir outras pastas de src/videos/.
Pasta pública (material + briefing.json): {_pub(t)}
Os quadros que os verificadores viram estão em {pasta} (q01.jpg...). Pasta para seus quadros de conferência:
{t.pasta / 'quadros'}

PROBLEMAS:
{lista}

{itens[-1]}
(cena PARADA = ponha movimento visível que dure a cena toda: câmera, entrada/saída de elementos, progresso.)

MANTER (elogiado):
{elogios or '- (nada)'}
{('GRAVES DA RODADA ANTERIOR (se algum dos problemas acima é o mesmo, a correção passada NÃO funcionou: mude a '
  'abordagem, não repita):' + chr(10) + antes) if antes else ''}

NÃO ESTRAGUE O QUE ESTÁ CERTO (as correções passadas criaram defeitos novos):
- {('Texto na tela só com o que a NARRAÇÃO diz: não acrescente fato, data ou número que ela não fala.')
   if t.entretenimento else
   ('Fatos permitidos, e SÓ eles: ' + '; '.join(k['fatos']) + '. Não acrescente número, prazo, tempo de resposta, '
    '"24h", preço ou qualquer alegação que não esteja aqui — nem em selo/pílula de enfeite.')}
- Rolagem/scroll de mockup: pare sempre com itens INTEIROS visíveis, nunca cortando texto ou foto ao meio.
- Legenda: ancorada pela BASE (bottom fixo) com a base em y <= 1580 mesmo com 2 linhas.
{('- NUNCA troque a imagem de uma cena pela imagem de OUTRA cena (27/10: o corretor repetiu a mesma foto 4 vezes e a '
  'retenção caiu de 6 para 5). Cada img_N é da cena N; varie com recorte, zoom, pan ou parallax da PRÓPRIA imagem.'
  + chr(10) + '- NENHUM texto novo na tela que não seja palavra da narração daquela cena (27/10 o corretor escreveu '
  '"ESPÉCIE INVASORA", falso) e nada que entregue a resposta antes de a narração revelar (nem o título).'
  + chr(10) + '- Problema de ROTEIRO (o que a narração fala, gancho falado, ordem da história) NÃO se conserta na '
  'edição: ignore esses e conserte só o visual.') if t.entretenimento else ''}
- Texto novo que você criar segue letra >= 32 px, zona segura e margem de 60 px.

Pense a fundo em cada correção. Depois de corrigir, gere stills (npx remotion still) dos momentos mexidos, OLHE
com Read e confirme que ficou certo. No fim responda uma frase com o que mudou."""
        with _so_este_video(tid):
            motor.chamar(prompt, REMOTION, PROJETO, "corrigir", timeout=c.get("prazo_correcao_s", 2700), max_turnos=90,
                         ferramentas=motor.EDITOR, modelo=criador, aceitar_limite=True)
        ok, erro = _render(t, t.pasta / "video.mp4")
        if not ok and _RENDER_PASSAGEIRO.search(erro):
            # 28/10: máquina (RAM/Chrome), não código: espera RAM (até 15 min) e renderiza de novo, sem jogar fora
            # a correção nem chamar o corretor à toa
            import psutil
            ini = time.time()
            while psutil.virtual_memory().available < 2.5 * 2 ** 30 and time.time() - ini < 900:
                time.sleep(30)
            log(f"  [lapidar] render da correção caiu por máquina ({erro[-80:].strip()}); renderizo de novo")
            ok, erro = _render(t, t.pasta / "video.mp4")
        if not ok and not _RENDER_PASSAGEIRO.search(erro):
            # 27/10: a correção de 40 min (VPS) foi jogada fora por um erro de código que o corretor conserta
            log(f"  [lapidar] render da correção falhou; o corretor conserta o erro: {erro[-300:]}")
            with _so_este_video(tid):
                motor.chamar(f"""O render do vídeo `{tid}` (código em src/videos/{tid}/) FALHOU depois da sua correção.
Erro do Remotion:
{erro[-2500:]}

Conserte SÓ o que causa esse erro, sem mudar mais nada da edição. Confirme com
`npx remotion still src/videos/{tid}/index.ts Main {t.pasta / 'quadros' / 'conserto.jpg'} --frame=60
--public-dir={_pub(t)}` e responda uma frase.""", REMOTION, PROJETO, "consertar_render", timeout=900,
                             max_turnos=30, ferramentas=motor.EDITOR, modelo=criador, aceitar_limite=True)
            ok, erro = _render(t, t.pasta / "video.mp4")
        if not ok:
            log(f"  [lapidar] render da correção falhou, volto para a melhor versão: {erro[-300:]}")
            quebrou = True
            break
        pv.nivelar(t.pasta / "video.mp4", log)
    if melhor_src.exists() and (quebrou or melhor > rodadas[-1]["nota"]):
        _copiar_src(melhor_src, src)
        shutil.copy2(melhor_mp4, t.pasta / "video.mp4")
        log(f"  [lapidar] fica a versão de nota {melhor}")
    t.marcar("lapidar", total=round(pv._dur(t.pasta / "video.mp4"), 2), nota_lapidar=melhor,
             revisoes=[{"nota": melhor, "comentario": f"{len(rodadas)} rodada(s) de verificação"}],
             rodada=len(rodadas))
    with Path(r"D:\video-fila\linhas\CLAUDE-CODE-VIDEO\evolucao.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"em": datetime.now().isoformat(timespec="minutes"), "id": tid, "tipo": t.e.get("tipo", "anuncio"),
                            "produto": k["nome_produto"],
                            "editor": t.e.get("modelo_editor") or modelo_etapa("editar"),
                            "roteirista": t.e.get("modelo_roteiro"), "corretor": criador, "juri": modelo,
                            "referencia": t.e.get("referencia"),
                            "nota_1a_versao": rodadas[0]["nota"],
                            "graves_1a_versao": rodadas[0]["graves"], "nota_final": melhor,
                            "rodadas": len(rodadas)}, ensure_ascii=False) + "\n")
    _aprender(t, k, rodadas[0], criador)


APRENDIDO = REMOTION / "APRENDIDO.md"


def _aprender(t, k, primeira, modelo):
    """Cada vídeo ensina o próximo (26/10, dono: "ir melhorando a cada vídeo feito"): os defeitos da 1ª versão do
    editor viram regras gerais em remotion/APRENDIDO.md, que o editor lê antes de começar."""
    arq = REMOTION / "APRENDIDO_ENTRETENIMENTO.md" if t.entretenimento else APRENDIDO
    genero = "vídeos de ENTRETENIMENTO (curiosidades, histórias, filmes)" if t.entretenimento else "anúncios"
    atuais = arq.read_text("utf-8") if arq.exists() else "(vazio)"
    probs = "\n".join(f"- [{p.get('gravidade')}] ({v['foco']}) {p.get('problema')}"
                      for v in primeira["verificadores"] for p in v["problemas"])
    dono = opiniao_do_dono(t.e.get("tipo", "anuncio"))
    if dono:
        probs = (f"OPINIÃO DO DONO (vale MAIS que os verificadores; vire regra, com prioridade máxima):\n{dono}\n\n"
                 + probs)
    prompt = f"""Você mantém o caderno de regras de um EDITOR de {genero} verticais em Remotion. A cada vídeo,
verificadores apontam defeitos da 1ª versão que o editor entregou. Seu trabalho: transformar defeitos em REGRAS
GERAIS curtas e acionáveis (valem para qualquer vídeo deste tipo), para o editor não repetir.

REGRAS ATUAIS:
{atuais}

DEFEITOS DA 1ª VERSÃO DO ÚLTIMO VÍDEO ({k['nome_produto']}, nota {primeira['nota']}):
{probs}

Pense a fundo. Reescreva o caderno: mantenha as regras que continuam valendo, junte as repetidas, acrescente as
novas que esses defeitos ensinam, dê prioridade (primeiro) ao que mais derruba nota; no máximo 25 regras, cada uma
em 1–2 linhas, imperativa e concreta (números quando houver: px, segundos). Nada específico de um produto.
LIMITES FIXOS do manual (nunca afrouxe nem contradiga): zona segura y 150–1580 e 60 px nas laterais; letra
mínima 32 px em qualquer texto; só os fatos do briefing (nada de número/prazo/preço inventado).
Responda SÓ JSON: {{"regras": ["...", "..."]}}"""
    try:
        r = motor.chamar_json(prompt, t.pasta, PROJETO, "aprender", timeout=900, max_turnos=6, modelo=modelo)
        regras = [x for x in r.get("regras") or [] if isinstance(x, str) and x.strip()]
        if regras:
            arq.write_text(f"# Regras aprendidas (atualizado {datetime.now():%d/%m %H:%M}, depois de {t.e['id']})\n"
                                 + "".join(f"{i}. {x.strip()}\n" for i, x in enumerate(regras, 1)), "utf-8")
            log(f"  [aprender] {len(regras)} regras em APRENDIDO.md")
            if dono:
                with (ULTIMO / "opinioes_ja_usadas.txt").open("a", encoding="utf-8") as f:
                    f.write(f"\n=== {datetime.now():%d/%m %H:%M} (virou regra depois de {t.e['id']})\n{dono}\n")
                OPINIAO.write_text(OPINIAO.read_text("utf-8").split(_MARCA_OPINIAO, 1)[0] + _MARCA_OPINIAO + "\n",
                                   "utf-8")
                log("  [aprender] opinião do dono usada")
    except (motor.MotorErro, motor.SemCota) as e:
        log(f"  [aprender] não atualizou: {str(e)[:150]}")


# ───────────────────────────── 7 final ─────────────────────────────

def etapa_final(t, k):
    if not t.e.get("voz_clonada"):
        t.marcar("final", status="voz_proibida")
        log("  [TRAVA] vídeo com voz edge pura (sem clone) — não vai pra saída nem pro Telegram")
        return
    r = t.e["roteiro"]
    destino = SAIDA / t.e["conta"]
    destino.mkdir(parents=True, exist_ok=True)
    mp4 = destino / f"{t.e['id']}.mp4"
    shutil.copy2(t.pasta / "video.mp4", mp4)
    ult = (t.e.get("revisoes") or [{}])[-1]
    lado = {"conta": t.e["conta"], "produto": k["produto_id"], "marca": k["marca"], "titulo": r["titulo"],
            "legenda": r.get("legenda_post", "") + "\n\n" + " ".join((r.get("hashtags") or k["hashtags"])[:5]),
            "roteiro": r, "plano": t.e.get("plano"), "modo": t.e.get("modo", "molde"),
            "editor_resumo": t.e.get("resumo_editor"), "imagens": t.e["origens_img"], "duracao_s": t.e["total"],
            "revisao_claude": {"rodadas": t.e["rodada"], "nota": ult.get("nota"), "comentario": ult.get("comentario")},
            "motor": "claude-code", "gerado_em": datetime.now().isoformat(timespec="seconds")}
    mp4.with_suffix(".json").write_text(json.dumps(lado, ensure_ascii=False, indent=1), "utf-8")
    if k.get("pasta_reels"):  # 01/11: empresa solar -> fila do postador dela (reel_advance/reel_globo/postar_ms_energy)
        try:
            fila = Path(k["pasta_reels"])
            fila.mkdir(parents=True, exist_ok=True)
            alvo = fila / f"ccv_{t.e['id']}.mp4"
            shutil.copy2(mp4, alvo)
            alvo.with_suffix(".json").write_text(json.dumps({
                "titulo": r["titulo"], "legenda_insta": lado["legenda"], "descricao": lado["legenda"],
                "legenda_tiktok": lado["legenda"], "hashtags": k["hashtags"], "pipeline": "claude_code_video",
                "tipo": "ccv", "tipo_video": "animacao", "estilo": "animacao", "cenas": len(r.get("cenas") or []),
                "legenda_estilo": "remotion", "layout": "animacao", "fala": " ".join(
                    c.get("fala", "") for c in (r.get("cenas") or [])), "origem": str(mp4),
                "duracao_s": t.e["total"], "gerado_em": lado["gerado_em"]}, ensure_ascii=False, indent=2), "utf-8")
            log(f"  [solar] na fila de postagem: {alvo}")
        except Exception as e:  # noqa: BLE001
            log(f"  [solar] não copiei para a fila da empresa: {e}")
    enviado = None
    if cfg().get("mandar_telegram"):
        try:
            import avisos
            enviado = avisos.enviar_arquivo(
                mp4, (f"🎬 Claude Code Video — {k['nome_produto']} (EDITADO em Remotion por "
                      f"{t.e.get('modelo_editor') or modelo_etapa('editar') or 'Opus 5.5'})\n{r['titulo']}"
                      + (f"\nNota dos verificadores: {t.e['nota_lapidar']}/10 em {t.e['rodada']} rodada(s)"
                         if t.e.get("nota_lapidar") is not None else "")
                      if t.e.get("modo") == "editor" else
                      f"🎬 Claude Code Video — {k['nome_produto']}\n{r['titulo']}\nNota do Claude: {ult.get('nota')}/10 "
                      f"({t.e['rodada']} revisão(ões))") + f"\nVai para o Instagram na próxima rodada do postador: {mp4}", PROJETO)
        except Exception as e:  # noqa: BLE001
            log(f"  [telegram] não saiu: {e}")
    t.marcar("final", status="pronto", saida=str(mp4), telegram=enviado,
             terminado=datetime.now().isoformat(timespec="seconds"))
    log(f"  [OK] {mp4} ({t.e['total']}s) — telegram {'enviado' if enviado else 'NÃO'}")
    publicar_ultimo(t, k, mp4)


ULTIMO = Path(r"D:\hipercool-materiais\claude-code-video\ULTIMO_VIDEO")
OPINIAO = ULTIMO / "SUA_OPINIAO.txt"
_MARCA_OPINIAO = "--- escreva abaixo desta linha ---"


def publicar_ultimo(t, k, mp4):
    """26/10, dono: "deixe uma pasta sempre com o último vídeo feito aberta pra eu ver e dar minhas opiniões".
    Só o último fica (o anterior sai daqui; o original continua em saida/). Opinião escrita é lida pelo aprendiz."""
    ULTIMO.mkdir(parents=True, exist_ok=True)
    for velho in ULTIMO.glob("*.mp4"):
        velho.unlink()
    shutil.copy2(mp4, ULTIMO / mp4.name)
    rods = t.e.get("lapidar") or []
    notas = "\n".join(f"  rodada {r['rodada']}: {r['nota']} " + str(r.get("notas")) for r in rods)
    (ULTIMO / "LEIA.txt").write_text(
        f"Último vídeo do Claude Code Video: {k['nome_produto']} ({t.e['conta']}) — {datetime.now():%d/%m %H:%M}\n"
        f"Título: {t.e['roteiro']['titulo']}\nArquivo original: {mp4}\n"
        f"Nota dos verificadores (melhor versão): {t.e.get('nota_lapidar')}\n{notas}\n\n"
        f"Quer opinar? Escreva em SUA_OPINIAO.txt (abaixo da linha). O próximo vídeo já usa a sua opinião como "
        f"regra mais forte que a dos verificadores.\n", "utf-8")
    if not OPINIAO.exists():
        OPINIAO.write_text(f"Sua opinião sobre os vídeos (vale para os próximos; pode escrever informal).\n"
                           f"{_MARCA_OPINIAO}\n", "utf-8")
    if not opiniao_do_dono(None):  # a opinião que vier é sobre ESTE vídeo (27/10: a de um anúncio caiu no entretenimento)
        (ULTIMO / ".tipo").write_text(t.e.get("tipo", "anuncio"), "utf-8")


def opiniao_do_dono(tipo):
    """Texto que o dono escreveu em SUA_OPINIAO.txt (vazio se nada). tipo: só devolve se a opinião é sobre um vídeo
    desse tipo (anuncio/entretenimento); None = qualquer."""
    if not OPINIAO.exists():
        return ""
    texto = OPINIAO.read_text("utf-8").split(_MARCA_OPINIAO, 1)[-1].strip()
    marca = ULTIMO / ".tipo"
    if tipo and texto and marca.exists() and marca.read_text("utf-8").strip() != tipo:
        return ""
    return texto


# ───────────────────────────── condutor ─────────────────────────────

ETAPAS = [("roteiro", etapa_roteiro), ("narracao", etapa_narracao), ("imagens", etapa_imagens),
          ("plano", etapa_plano), ("render", etapa_render), ("revisao", etapa_revisao), ("final", etapa_final)]
ETAPAS_EDITOR = [("roteiro", etapa_roteiro), ("narracao", etapa_narracao), ("imagens", etapa_imagens),
                 ("preparar_editor", etapa_preparar_editor), ("editar", etapa_editar),
                 ("render_remotion", etapa_render_remotion), ("lapidar", etapa_lapidar), ("final", etapa_final)]


def rodar(t):
    k = kit_trabalho(t)
    t.e.setdefault("modo", cfg().get("modo", "molde"))
    log(f"=== {t.e['id']} ({k['nome_produto']}, modo {t.e['modo']}) — etapas feitas: {t.e['feitas'] or 'nenhuma'} ===")
    t.e["status"] = "em_andamento"
    t.salvar()
    try:
        for nome, fn in (ETAPAS_EDITOR if t.e["modo"] == "editor" else ETAPAS):
            while not t.feita(nome):
                fn(t, k)
                if nome != "revisao":
                    break
        return True
    except motor.SemCota as e:
        d = cota_claude.decidir(custo_zero() / 2, certeza=False, forcar=True)
        t.e.update(status="aguardando_cota", retomar_apos=d["volta"], ultimo_erro=str(e)[:200])
        t.salvar()
        log(f"  [PAUSA] cota acabou no meio ({str(e)[:100]}); retoma {d['volta'] or 'quando a cota voltar'}")
    except Exception as e:  # noqa: BLE001
        if isinstance(e, motor.MotorErro) and re.search(r"high demand|\b503\b|UNAVAILABLE", str(e), re.I):
            # sobrecarga passageira do Gemini (28/10: 2 vídeos perderam tentativa): espera a próxima rodada sem contar
            t.e["ultimo_erro"] = f"passageiro: {str(e)[:200]}"
            t.salvar()
            log("  [ESPERA] Gemini sobrecarregado — retoma na próxima rodada (não conta como erro)")
            return False
        if isinstance(e, RenderPassageiro) and t.e.get("esperas_render", 0) < 4:
            # 29/10: o render travou com o disco a 1,7 GB e gastou a 2ª de 3 tentativas do Fato ou Fake
            t.e["esperas_render"] = t.e.get("esperas_render", 0) + 1
            t.e["ultimo_erro"] = f"passageiro: {str(e)[:200]}"
            t.salvar()
            log(f"  [ESPERA] render falhou pela máquina ({t.e['esperas_render']}/4) — renderiza de novo na próxima rodada")
            return False
        t.e["erros"] = t.e.get("erros", 0) + 1
        t.e["ultimo_erro"] = f"{type(e).__name__}: {str(e)[:300]}"
        if t.e["erros"] >= 3:
            t.e["status"] = "falhou"
        t.salvar()
        log(f"  [ERRO {t.e['erros']}/3] {t.e['ultimo_erro']}\n{traceback.format_exc()[-800:]}")
    return False


def feitos_hoje():
    hoje = datetime.now().strftime("%Y%m%d")
    return sum(1 for p in TRABALHOS.glob(f"*_{hoje}_*/estado.json")
               if not json.loads(p.read_text("utf-8")).get("comparacao"))


def proximo_tipo():
    """26/10 (dono): entretenimento nos temas dos canais, alternando com os anúncios."""
    if not (cfg().get("entretenimento") or {}).get("contas"):
        return "anuncio"
    trabs = sorted((json.loads(p.read_text("utf-8")) for p in TRABALHOS.glob("*/estado.json")),
                   key=lambda e: e.get("criado", ""))
    ultimo = next((e.get("tipo", "anuncio") for e in reversed(trabs) if not e.get("comparacao")), "anuncio")
    return "anuncio" if ultimo == "entretenimento" else "entretenimento"


def proxima_conta(contas=None):
    contas = contas or cfg()["contas"]
    ultimos = [json.loads(p.read_text("utf-8"))["conta"] for p in sorted(TRABALHOS.glob("*/estado.json"),
                                                                          key=lambda p: p.stat().st_mtime)]
    for c in contas:          # quem nunca teve vídeo primeiro; depois quem teve há mais tempo
        if c not in ultimos:
            return c
    return min(contas, key=lambda c: max(i for i, x in enumerate(ultimos) if x == c))


def escolher_proximo():
    """01/11 (dona: "dê prioridade só de energia solar, depois aos de produtos, e depois aos de entretenimento"):
    (tipo, conta). 1º as solares até `solar_por_conta_dia` cada (a que tem menos hoje); 2º produto que ainda não teve
    vídeo hoje; 3º entretenimento; sem entretenimento, o produto de vez mais antiga."""
    c = cfg()
    hoje = datetime.now().strftime("%Y-%m-%d")
    cont = {}
    for p in TRABALHOS.glob("*/estado.json"):
        e = json.loads(p.read_text("utf-8"))
        if not e.get("comparacao") and str(e.get("criado", "")).startswith(hoje):
            cont[e["conta"]] = cont.get(e["conta"], 0) + 1
    solares = [x for x in c["contas"] if x in kit_mod.SOLARES]
    falta = [x for x in solares if cont.get(x, 0) < c.get("solar_por_conta_dia", 2)]
    if falta:
        menor = min(cont.get(x, 0) for x in falta)
        return "anuncio", proxima_conta([x for x in falta if cont.get(x, 0) == menor])
    produtos = [x for x in c["contas"] if x not in kit_mod.SOLARES]
    sem_hoje = [x for x in produtos if not cont.get(x)]
    if sem_hoje:
        return "anuncio", proxima_conta(sem_hoje)
    ent = (c.get("entretenimento") or {}).get("contas")
    if ent:
        return "entretenimento", proxima_conta(ent)
    return "anuncio", proxima_conta(produtos)


def auto():
    c = cfg()
    if not c.get("ligado"):
        log("desligado na config")
        return
    agora = datetime.now().astimezone()
    for t in pendentes():
        quando = t.e.get("retomar_apos")
        if t.e["status"] == "aguardando_cota" and quando and datetime.fromisoformat(quando) > agora:
            log(f"{t.e['id']}: aguardando cota até {quando}")
            return
        d = cota_claude.decidir(custo_zero() / 2, certeza=False)
        if not d["ligar"] and _precisa_claude(t):
            log(f"{t.e['id']}: pendente, sem cota para retomar ({d['motivo']})")
            return
        rodar(t)
        return
    if feitos_hoje() >= c["videos_por_dia"]:
        return
    import psutil
    livre = psutil.virtual_memory().available / 2 ** 30
    if livre < c.get("ram_livre_min_gb", 3):
        # 26/10, dono: "sem atrapalhar os outros" — vídeo novo só com o PC folgado
        log(f"novo vídeo espera: RAM livre {livre:.1f} GB < {c.get('ram_livre_min_gb', 3)} GB")
        return
    d = cota_claude.decidir(custo_zero(), certeza=True, forcar=True)
    tipo, conta = escolher_proximo()  # 01/11: solar > produto > entretenimento (antes alternava anúncio/entretenimento)
    if tipo == "entretenimento":       # roteiro e edição no Gemini: não depende da cota do Claude Pro
        rodar(Trabalho.novo(conta, tipo))
        return
    if not d["ligar"] and _precisa_claude():
        log(f"novo vídeo não começa: {d['motivo']}")
        return
    rodar(Trabalho.novo(conta))


def _precisa_claude(t=None):
    """Falta alguma etapa que só o Claude Pro faz? (edição no Claude, ou roteiro sem a reserva Gemini.) 26/10: o
    vídeo esperou 1 h por cota do Claude com o roteiro já pronto e o resto todo no Gemini."""
    if (modelo_etapa("editar") or cfg()["modelo"]).startswith("cc/"):
        return True
    return not (t and t.feita("roteiro")) and not cfg().get("roteiro_reserva")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--conta")
    ap.add_argument("--continuar")
    ap.add_argument("--forcar", action="store_true", help="ignora a trava de cota (uso manual)")
    a = ap.parse_args()
    # prioridade baixa só nas etapas pesadas (render, clone, editor com stills — motor.executar(baixa=True)); o
    # processo inteiro em baixa travou um ffmpeg de 1 s por 15 min com a CPU a 100% (27/10)
    TRAVA.parent.mkdir(exist_ok=True)
    try:
        trava = open(TRAVA, "x")
    except FileExistsError:
        # 25/10: processo morto (matado no meio) deixava a trava e bloqueava tudo -> vale só se o PID dela vive
        try:
            pid = int(TRAVA.read_text().strip() or 0)
        except (ValueError, OSError):
            pid = 0
        vivo = pid and str(pid) in subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True,
                                                  text=True).stdout
        if vivo:
            log(f"já tem um rodando (PID {pid})")
            return
        log(f"trava velha (PID {pid or '?'} não existe) — apagando")
        TRAVA.unlink(missing_ok=True)
        trava = open(TRAVA, "x")
    trava.write(str(__import__("os").getpid()))
    trava.flush()
    try:
        if a.auto:
            auto()
        elif a.continuar:
            rodar(Trabalho(TRABALHOS / a.continuar))
        elif a.conta:
            if not a.forcar:
                d = cota_claude.decidir(custo_zero(), certeza=True, forcar=True)
                if not d["ligar"]:
                    print("sem cota de certeza:", d["motivo"], "(use --forcar para ignorar)")
                    return
            rodar(Trabalho.novo(a.conta))
    finally:
        trava.close()
        TRAVA.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
