r"""melhorador.py — o MELHORADOR do Claude Code Video (27/10/2026, pedido do dono).

Faz sozinho o que a sessão do Claude fazia no chat: olha o vídeo pronto, acha o defeito que MAIS se repete, faz UMA
mudança no sistema, e julga nos próximos vídeos se a nota da 1ª versão subiu (fica) ou caiu (desfaz sozinho).
Diferença do melhoria_continua.py (D:\video-fila): lá a IA escolhe "uma melhoria qualquer" na roda de projetos e não
mede o resultado; aqui a escolha vem da EVIDÊNCIA (notas e defeitos do júri) e todo experimento é julgado pelos
vídeos seguintes. Copiado de lá: backup, desfazer sozinho, lições, não repropor o que foi desfeito.

Agentes (papéis) e modelos — cada papel tem uma ESCADA em config_melhorador.json["papeis"]; tenta do primeiro ao
último. "cc/..." só com cota do Claude Pro (cota_claude, reserva do dono); modelos em "bloqueados" (Kiro até dia 1)
são pulados; erro/429 = desce a escada. estado/melhorador_modelos.json conta, por papel e modelo, quantas vezes
respondeu, foi aprovado pelo crítico e o experimento ficou — é o dado para decidir se um modelo "de baixo" ajuda.
  ANALISTA    lê a evidência e ranqueia os defeitos que se repetem
  PROPOSITOR  escreve UMA mudança concreta (troca de trecho num manual, ou um valor de config na faixa)
  CRÍTICO     confere a proposta contra os limites fixos e as lições; veta o que é arriscado
O que ele PODE mudar (Gemini já quebrou o sistema antes — escopo fechado): só os manuais do editor
(remotion\EDITOR.md, remotion\EDITOR_ENTRETENIMENTO.md) e 3 valores do config (com faixa). Nunca código.

    python melhorador.py --simular      # roda tudo e mostra o que faria, sem aplicar
    python melhorador.py                # 1 ciclo (a tarefa ClaudeCodeVideo chama; só age se "ligado")
    python melhorador.py ligar|desligar|status
"""
import sem_janela  # noqa: F401 — nenhum filho abre janela
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
import cota_claude  # noqa: E402
import motor  # noqa: E402

CFG = RAIZ / "config_melhorador.json"
EST = RAIZ / "estado" / "melhorador.json"
STATS = RAIZ / "estado" / "melhorador_modelos.json"
LOG = RAIZ / "estado" / "melhorador.log"
BACKUP = RAIZ / "estado" / "melhorador_backup"
TRAB = RAIZ / "estado" / "melhorador_trab"
LICOES = RAIZ / "melhorador_LICOES.md"
# 27/10 (dona): pedidos dela em toda rodada; o que pede CÓDIGO vira ideia (não aplica sem o ok dela)
PEDIDOS = RAIZ / "PEDIDOS_DO_DONO.md"
IDEIAS = RAIZ / "IDEIAS_CODIGO.md"
LINHA = Path(r"D:\video-fila\linhas\CLAUDE-CODE-VIDEO")
EVOL = LINHA / "evolucao.jsonl"
DECISOES = LINHA / "DECISOES.md"
TRABALHOS = RAIZ / "trabalhos"
MANUAIS = {"remotion/EDITOR.md": ["## Zonas seguras", "## Regras duras", "## Como trabalhar", "## KIT DE CÂMERA"],
           "remotion/EDITOR_ENTRETENIMENTO.md": ["## Zonas seguras", "## Regras de verdade", "## Como trabalhar",
                                                 "## KIT DE CÂMERA"]}
CONFIG_FAIXA = {"rodadas": (1, 4), "alvo": (7.0, 9.5), "prazo_correcao_s": (900, 3600)}  # dentro de "lapidar"
PADRAO = {
    "ligado": False,
    "videos_para_julgar": 2,       # experimento é julgado depois de N vídeos do mesmo tipo
    "piora_maxima": 0.4,           # nota média da 1ª versão caiu mais que isso = desfaz
    "crescimento_max": 0.25,       # o manual não pode crescer mais que 25% numa mudança
    "bloqueados": {"kr/": "2026-11-01"},  # prefixo: até quando (Kiro sem crédito até dia 1)
    "papeis": {
        "analista": ["agy/gemini-3.8-flash-high", "antigravity/gemini-3.8-flash-tiered"],
        "propositor": ["agy/gemini-3.8-flash-high", "antigravity/gemini-3.8-flash-tiered"],
        "critico": ["agy/gemini-3.8-flash-high", "antigravity/gemini-3.8-flash-tiered"],
        "implementador": ["agy/gemini-3.8-flash-high"],
    },
    "pode_codigo": True,           # 27/10 (dona): também muda código (ARQ_CODIGO), testado na caixa e com desfazer
    "_papeis": "escada de modelos por papel (1º que responder). Argon entra quando o dono avisar "
               "(gemini/gemini-4-argon). cc/ só com cota de certeza do Claude Pro.",
}


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text("utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=1), "utf-8")


FORCAR = []  # --modelo X: X em todos os papéis (teste)
# MODO SOMBRA (27/10, dono): o melhorador roda numa CAIXA SEPARADA (cópia dos manuais e do config); a sessão do
# Claude faz a análise/melhoria real, compara com a dele em estado\sombra\COMPARACOES.md e ajusta prompts/lições.
SOMBRA = RAIZ / "estado" / "sombra"
EM_SOMBRA = []


def base():
    """Onde ficam os arquivos que ele lê e muda: o sistema real, ou a cópia da caixa de areia no modo sombra."""
    return SOMBRA / "caixa" if EM_SOMBRA else RAIZ


def preparar_sombra():
    """Caixa nova a cada rodada: cópia fresca dos manuais e do config reais (o que ele mudar fica só aqui)."""
    caixa = SOMBRA / "caixa"
    shutil.rmtree(caixa, ignore_errors=True)
    (caixa / "remotion").mkdir(parents=True)
    for m in MANUAIS:
        shutil.copy2(RAIZ / m, caixa / m)
    shutil.copy2(RAIZ / "config.json", caixa / "config.json")
    EM_SOMBRA.append(True)


def cfg():
    c = {**PADRAO, **_ler(CFG, {})}
    if FORCAR:
        c["papeis"] = {p: FORCAR[:] for p in c["papeis"]}
    return c


# ───────────────────────────── modelos (escada por papel) ─────────────────────────────

def _bloqueado(m, c):
    hoje = datetime.now().strftime("%Y-%m-%d")
    return any(m.startswith(pref) and hoje < ate for pref, ate in c["bloqueados"].items())


def _conta(papel, modelo, campo):
    s = _ler(STATS, {})
    d = s.setdefault(papel, {}).setdefault(modelo, {"tentou": 0, "respondeu": 0, "aprovado": 0, "ficou": 0,
                                                     "desfeito": 0})
    d[campo] = d.get(campo, 0) + 1
    _gravar(STATS, s)


def chamar(papel, prompt, c):
    """JSON do 1º modelo da escada do papel que responder. Devolve (resposta, modelo)."""
    TRAB.mkdir(parents=True, exist_ok=True)
    try:  # 29/10 (Fable, D14): pelo melhorador CENTRAL a escada do papel vem dele (botão Argon/Opus/ambos); nunca Kiro
        escada = [m for m in (json.loads(os.environ.get("CENTRAL_MODELOS") or "{}").get(papel) or [])
                  if not str(m).startswith(("kr/", "kiro"))] or c["papeis"][papel]
    except ValueError:
        escada = c["papeis"][papel]
    for m in escada:
        if _bloqueado(m, c):
            continue
        if m.startswith("cc/") and not cota_claude.decidir(3, certeza=True)["ligar"]:
            continue
        _conta(papel, m, "tentou")
        try:
            # 27/10: o Gemini abria arquivos em vez de responder e estourava 10 turnos ("None None")
            prompt = ("TUDO o que você precisa está neste texto: NÃO abra nem procure arquivos; responda direto.\n\n"
                      + prompt) if not prompt.startswith("TUDO") else prompt
            r = motor.chamar_json(prompt, TRAB, "melhorador", papel, timeout=900, max_turnos=20,
                                  modelo=None if m == motor_padrao() else m)
            _conta(papel, m, "respondeu")
            return r, m
        except (motor.MotorErro, motor.SemCota) as e:
            log(f"  [{papel}] {m} falhou: {str(e)[:150]}")
    raise motor.MotorErro(f"nenhum modelo respondeu no papel {papel}")


def motor_padrao():
    return json.loads((RAIZ / "config.json").read_text("utf-8"))["modelo"]


# ───────────────────────────── evidência ─────────────────────────────

def _videos():
    out = []
    for linha in EVOL.read_text("utf-8").splitlines() if EVOL.exists() else []:
        try:
            v = json.loads(linha)
        except ValueError:
            continue
        v.setdefault("tipo", "anuncio")
        out.append(v)
    return out


def _trabalho(vid):
    p = TRABALHOS / vid / "estado.json"
    return _ler(p, {}) if p.exists() else {}


def evidencia(tipo, n=4):
    """Notas e defeitos da 1ª versão dos últimos n vídeos do tipo (o que o editor entrega sem corretor)."""
    vids = [v for v in _videos() if v["tipo"] == tipo][-n:]
    blocos = []
    for v in vids:
        e = _trabalho(v["id"])
        r1 = (e.get("lapidar") or [{}])[0]
        probs = [f"   [{p.get('gravidade')}] ({vv['foco']}) {str(p.get('problema'))[:220]}"
                 for vv in r1.get("verificadores", []) for p in vv.get("problemas", [])]
        blocos.append(f"- {v['id']} ({v.get('produto')}): 1ª versão {v.get('nota_1a_versao')} final "
                      f"{v.get('nota_final')} | por foco {r1.get('notas')}\n" + "\n".join(probs[:18]))
    return "\n".join(blocos), vids


def _historico_txt(e):
    return "\n".join(f"- [{x['status']}] {x['titulo']} ({x.get('motivo', '')})" for x in e.get("historico", [])[-20:]) \
        or "- (nenhum ainda)"


def pedidos_abertos():
    if not PEDIDOS.exists():
        return []
    return [ln[6:].strip() for ln in PEDIDOS.read_text("utf-8").splitlines() if ln.startswith("- [ ] ")]


def _pedidos_txt():
    ps = pedidos_abertos()
    return ("\nPEDIDOS DA DONA (prioridade MÁXIMA, acima dos defeitos do júri):\n" + "\n".join(f"- {x}" for x in ps)
            + "\n") if ps else ""


def marcar_pedido(pedido, como):
    if not pedido or not PEDIDOS.exists() or EM_SOMBRA:
        return
    txt = PEDIDOS.read_text("utf-8")
    for ln in txt.splitlines():
        if ln.startswith("- [ ] ") and pedido.strip()[:40] in ln:
            PEDIDOS.write_text(txt.replace(ln, f"- [x] {ln[6:]}  → {datetime.now():%d/%m %H:%M} {como}"), "utf-8")
            return


# ───────────────────────────── agentes ─────────────────────────────

def analista(tipo, ev, e, c):
    prompt = f"""Você é o ANALISTA do sistema que faz vídeos verticais de {tipo} em Remotion (um editor de IA escreve o
código seguindo um manual; 4 verificadores dão nota 0-10 por foco). Abaixo, a 1ª versão dos últimos vídeos (antes
de qualquer correção) com a nota por foco e os defeitos que os verificadores viram.

{ev}
{_pedidos_txt()}
EXPERIMENTOS JÁ FEITOS (não repita o que foi DESFEITO):
{_historico_txt(e)}

LIÇÕES:
{LICOES.read_text('utf-8') if LICOES.exists() else ''}

Ranqueie os 3 defeitos que MAIS derrubam a nota e que se REPETEM em mais de um vídeo (não um caso isolado). Para
cada um: o foco, o defeito em 1 frase, em quantos vídeos aparece e a causa provável no jeito de editar.
Responda SÓ JSON: {{"defeitos": [{{"foco": "", "defeito": "", "videos": 0, "causa": ""}}]}}"""
    return chamar("analista", prompt, c)


def propositor(tipo, defeito, manual_nome, manual_txt, e, c):
    prompt = f"""Você é o PROPOSITOR. O defeito que mais se repete nos vídeos de {tipo}:
{json.dumps(defeito, ensure_ascii=False)}

O editor de IA segue este manual ({manual_nome}):
<<<
{manual_txt}
>>>

{('AVISO: ' + defeito['aviso']) if defeito.get('aviso') else ''}
{_pedidos_txt()}Se um pedido da dona cabe numa mudança do manual/config, atenda o pedido ANTES do defeito e diga qual em "pedido".
Se o pedido (ou o defeito) só se resolve mudando CÓDIGO (Python/TSX), responda {{"tipo": "codigo", "titulo": "",
"arquivo": "caminho provável", "descricao": "o que mudar e por quê", "pedido": "o pedido atendido ou vazio"}}
(vira ideia para a dona aprovar; não é aplicado).
Se a mudança certa agora é NENHUMA (a regra para esse defeito já existe e ainda não foi medida, ou a evidência é
fraca), responda {{"tipo": "esperar", "titulo": "esperar", "hipotese": "por quê"}}.
Senão, proponha UMA mudança, a menor que resolve, de um destes dois tipos:
(a) "editar": troque um trecho EXATO do manual por um novo (o trecho velho tem que existir igual, letra por letra,
    e aparecer uma vez só). Regra concreta e verificável (números: px, segundos, %), dita como ordem. Não apague as
    seções de zonas seguras, regras duras/verdade, como trabalhar e kit. Não afrouxe limites (zona y 150–1580,
    letra >= 32 px, só fatos do briefing).
(b) "config": mudar um valor de "lapidar" dentro da faixa: {json.dumps(CONFIG_FAIXA)}.
Não repita experimentos desfeitos:
{_historico_txt(e)}
Responda SÓ JSON: {{"tipo": "editar|config", "titulo": "curto", "trocar_de": "", "trocar_para": "", "chave": "",
"valor": null, "pedido": "o pedido da dona atendido ou vazio", "hipotese": "por que melhora", "foco_que_sobe": "legibilidade|movimento|roteiro_marca|diretor|historia|retencao"}}"""
    return chamar("propositor", prompt, c)


def critico(tipo, prop, manual_txt, e, c):
    prompt = f"""Você é o CRÍTICO. Uma IA quer mudar o sistema que faz vídeos de {tipo}. Proposta:
{json.dumps(prop, ensure_ascii=False, indent=1)}

Trecho do manual em volta (para ver contradição): {manual_txt[:6000]}

Vete (aprovado=false) se: contradiz outra regra do manual; afrouxa limite (zona segura, letra mínima, fatos);
é vaga ("melhore o ritmo") em vez de concreta; repete experimento desfeito; pode quebrar o render (pedir pacote que
não existe, efeito pesado em toda cena); ou não ataca o defeito. Senão aprove.
Desfeitos: {_historico_txt(e)}
Responda SÓ JSON: {{"aprovado": true, "motivo": "1 frase"}}"""
    return chamar("critico", prompt, c)


# ───────────────────────────── aplicar / validar / julgar ─────────────────────────────

def _gerar_rodando():
    trava = RAIZ / "estado" / "gerar.lock"
    try:
        pid = int(trava.read_text().strip() or 0)
    except (OSError, ValueError):
        return False
    return str(pid) in subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True,
                                      text=True).stdout


def validar(prop, c):
    """(ok, motivo, (arquivo, texto_novo) | ("config", chave, valor))."""
    if prop.get("tipo") == "config":
        ch, val = prop.get("chave"), prop.get("valor")
        if ch not in CONFIG_FAIXA or not isinstance(val, (int, float)):
            return False, f"config fora da lista: {ch}={val}", None
        lo, hi = CONFIG_FAIXA[ch]
        if not lo <= val <= hi:
            return False, f"{ch}={val} fora da faixa {lo}–{hi}", None
        return True, "", ("config", ch, val)
    arq = prop.get("arquivo")
    if arq not in MANUAIS:
        return False, f"arquivo não permitido: {arq}", None
    velho = (base() / arq).read_text("utf-8")
    de, para = prop.get("trocar_de") or "", prop.get("trocar_para") or ""
    if len(de) < 15 or velho.count(de) != 1:
        return False, f"trecho a trocar aparece {velho.count(de)} vez(es) (precisa 1, >= 15 letras)", None
    novo = velho.replace(de, para)
    falta = [s for s in MANUAIS[arq] if s not in novo]
    if falta:
        return False, f"apagaria seção obrigatória: {falta}", None
    if len(novo) > len(velho) * (1 + c["crescimento_max"]):
        return False, f"manual cresceria {len(novo) / len(velho) - 1:.0%}", None
    for proibido in (r"y\s*=?\s*1[6-9]\d\d", r"\b(2\d|1\d)\s*px\b.*(m[ií]nim|letra)"):
        if re.search(proibido, para, re.I) and not re.search(proibido, de, re.I):
            return False, f"parece afrouxar limite ({proibido})", None
    return True, "", (arq, novo)


def aplicar(alvo, prop, tipo, linha_base, modelos, e):
    pasta_bk = SOMBRA / "backup" if EM_SOMBRA else BACKUP
    pasta_bk.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    if alvo[0] == "config":
        arq = base() / "config.json"
        copia = pasta_bk / f"{marca}_config.json"
        shutil.copy2(arq, copia)
        d = json.loads(arq.read_text("utf-8"))
        d.setdefault("lapidar", {})[alvo[1]] = alvo[2]
        arq.write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")
        alvo_arq = "config.json"
    else:
        arq = base() / alvo[0]
        copia = pasta_bk / f"{marca}_{arq.name}"
        shutil.copy2(arq, copia)
        arq.write_text(alvo[1], "utf-8")
        alvo_arq = alvo[0]
    e["aberto"] = {"titulo": prop.get("titulo"), "tipo": tipo, "arquivo": alvo_arq, "backup": str(copia),
                   "aplicado_em": datetime.now().isoformat(timespec="seconds"), "linha_base": linha_base,
                   "hipotese": prop.get("hipotese"), "foco": prop.get("foco_que_sobe"), "modelos": modelos}
    if EM_SOMBRA:
        return
    _decisao(f"[melhorador] APLICADO: {prop.get('titulo')} ({alvo_arq}) — hipótese: {prop.get('hipotese')}; "
             f"base 1ª versão {linha_base}; julga em {cfg()['videos_para_julgar']} vídeo(s) de {tipo}; desfazer: "
             f"copiar {copia.name} de volta. Modelos: {modelos}")


# ───────────────────────────── CÓDIGO (27/10, dona: "dê a ele o poder de fazer isso também") ─────────────────────────────
# Só estes arquivos (+ arquivo novo em remotion/src/lib/). Fora: motor.py (gateway/cadeia), melhorador.py, config.
ARQ_CODIGO = ["gerar.py", "remotion/src/lib/efeitos.tsx", "remotion/src/lib/karaoke.tsx"]
CAIXA_COD = RAIZ / "estado" / "melhorador_caixa_codigo"
REMOTION = RAIZ / "remotion"


def _ultimo_video_pronto():
    for v in reversed(_videos()):
        if (REMOTION / "src" / "videos" / v["id"] / "index.ts").exists() and (TRABALHOS / v["id"] / "public").exists():
            return v["id"]
    return None


def _testar_codigo(mud):
    """(ok, motivo). Python: compila e importa o gerar da caixa. TSX: renderiza 2 quadros do último vídeo com a lib
    da caixa (cópia isolada em src/_teste_mel; a produção não vê)."""
    py = RAIZ.parent / "veo" / "venv" / "Scripts" / "python.exe"
    py = str(py) if py.exists() else sys.executable
    for rel in mud:
        if rel.endswith(".py"):
            r = subprocess.run([py, "-c", "import sys; sys.path[:0]=[r'%s', r'%s']; import gerar" % (CAIXA_COD, RAIZ)],
                               cwd=str(RAIZ), capture_output=True, text=True, timeout=120)
            if r.returncode:
                return False, f"{rel} não importa: {(r.stderr or r.stdout)[-300:]}"
    if not any(r.startswith("remotion/src/lib/") for r in mud):
        return True, ""
    vid = _ultimo_video_pronto()
    if not vid:
        return False, "sem vídeo pronto para testar a lib"
    teste = REMOTION / "src" / "_teste_mel"
    shutil.rmtree(teste, ignore_errors=True)
    try:
        shutil.copytree(REMOTION / "src" / "lib", teste / "lib")
        for f in (CAIXA_COD / "remotion" / "src" / "lib").glob("*.tsx"):
            shutil.copy2(f, teste / "lib" / f.name)
        shutil.copytree(REMOTION / "src" / "videos" / vid, teste / "videos" / vid)
        for quadro in (30, 300):
            saida = CAIXA_COD / f"teste_{quadro}.png"
            try:
                rc, out = motor.executar(["npx.cmd", "remotion", "still", f"src/_teste_mel/videos/{vid}/index.ts", "Main",
                                          str(saida), f"--frame={quadro}", f"--public-dir={TRABALHOS / vid / 'public'}",
                                          "--log=error"], REMOTION, timeout=600, baixa=True)
            except subprocess.TimeoutExpired:
                return False, f"quadro {quadro} travou 10 min"
            if rc or not saida.exists():
                return False, f"quadro {quadro} não renderizou: {out[-300:]}"
    finally:
        shutil.rmtree(teste, ignore_errors=True)
    return True, ""


def implementar_codigo(prop, c):
    """O IMPLEMENTADOR muda a cópia (caixa); código confere arquivos, compila/importa e renderiza; devolve
    (ok, motivo, {rel: texto_novo|None-se-novo}, diff)."""
    import difflib
    shutil.rmtree(CAIXA_COD, ignore_errors=True)
    for rel in ARQ_CODIGO:
        (CAIXA_COD / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(RAIZ / rel, CAIXA_COD / rel)
    antes = {p.relative_to(CAIXA_COD).as_posix(): p.read_text("utf-8") for p in CAIXA_COD.rglob("*") if p.is_file()}
    prompt = f"""Você é o IMPLEMENTADOR do sistema que faz vídeos verticais em Remotion. Implemente NESTA PASTA (é uma cópia;
nada aqui vai para a produção sem passar nos testes) a mudança abaixo, a MENOR que resolve:
{json.dumps(prop, ensure_ascii=False, indent=1)}

Arquivos que você pode editar (só estes): {', '.join(ARQ_CODIGO)}. Pode criar arquivo novo só em remotion/src/lib/.
Não mude prazos, travas de texto/fatos, zonas seguras, modelos nem a ordem das etapas. Não reescreva o arquivo
inteiro: use Edit. Comente só o porquê não óbvio, em 1 linha. No fim responda 1 frase com o que mudou."""
    try:  # 29/10 (dona: os 3 modelos escolhidos em todas as linhas, sem Gemini puro): o central manda o implementador
        cm = [m for m in (json.loads(os.environ.get("CENTRAL_MODELOS") or "{}").get("implementador") or [])
              if not str(m).startswith(("kr/", "kiro"))]
    except ValueError:
        cm = []
    modelo = (cm or c["papeis"].get("implementador") or c["papeis"]["propositor"])[0]
    motor.chamar(prompt, CAIXA_COD, "melhorador", "implementar", timeout=1800, max_turnos=40, ferramentas=motor.EDITOR,
                 modelo=None if modelo == motor_padrao() else modelo, aceitar_limite=True)
    depois = {p.relative_to(CAIXA_COD).as_posix(): p.read_text("utf-8") for p in CAIXA_COD.rglob("*")
              if p.is_file() and p.suffix in (".py", ".tsx", ".ts")}
    mud = {rel: txt for rel, txt in depois.items() if antes.get(rel) != txt}
    fora = [rel for rel in mud if rel not in ARQ_CODIGO and not (rel.startswith("remotion/src/lib/")
                                                                  and rel.endswith(".tsx"))]
    if fora:
        return False, f"mexeu fora do permitido: {fora}", {}, ""
    if not mud:
        return False, "não mudou nada", {}, ""
    ok, motivo = _testar_codigo(mud)
    diff = "".join("".join(difflib.unified_diff((antes.get(rel) or "").splitlines(True), txt.splitlines(True),
                                                rel, rel, n=2)) for rel, txt in mud.items())
    return ok, motivo, mud, diff[:12000]


def critico_codigo(prop, diff, c):
    prompt = f"""Você é o CRÍTICO de uma mudança de CÓDIGO no sistema de vídeos. Ideia:
{json.dumps(prop, ensure_ascii=False, indent=1)}

Diferença (diff) já testada (compila, importa e renderiza):
{diff}

Vete (aprovado=false) se: faz mais do que a ideia pede; afrouxa trava de texto/fatos, zona segura, prazo ou tentativa;
troca modelo; apaga tratamento de erro; reescreve trecho grande sem necessidade; pode quebrar outro tipo de vídeo
(anúncio x entretenimento); ou não resolve a ideia. Senão aprove.
Responda SÓ JSON: {{"aprovado": true, "motivo": "1 frase"}}"""
    return chamar("critico", prompt, c)


def aplicar_codigo(mud, prop, tipo, linha_base, modelos, e):
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_bk = BACKUP / f"{marca}_codigo"
    arquivos = {}
    for rel, txt in mud.items():
        alvo = RAIZ / rel
        if alvo.exists():
            (pasta_bk / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(alvo, pasta_bk / rel)
            arquivos[rel] = str(pasta_bk / rel)
        else:
            arquivos[rel] = None  # arquivo novo: desfazer = apagar
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(txt, "utf-8")
    e["aberto"] = {"titulo": prop.get("titulo"), "tipo": tipo, "arquivo": ", ".join(mud), "arquivos": arquivos,
                   "codigo": True, "aplicado_em": datetime.now().isoformat(timespec="seconds"),
                   "linha_base": linha_base, "hipotese": prop.get("descricao"), "foco": prop.get("foco_que_sobe"),
                   "modelos": modelos}
    _decisao(f"[melhorador] CÓDIGO APLICADO: {prop.get('titulo')} ({', '.join(mud)}) — {prop.get('descricao')}; base "
             f"1ª versão {linha_base}; julga em {cfg()['videos_para_julgar']} vídeo(s); erro na produção = desfaz na "
             f"hora; backup em {pasta_bk}. Modelos: {modelos}")


def _desfazer(ab):
    if ab.get("arquivos"):
        for rel, bk in ab["arquivos"].items():
            if bk:
                shutil.copy2(bk, RAIZ / rel)
            else:
                (RAIZ / rel).unlink(missing_ok=True)
    else:
        shutil.copy2(ab["backup"], RAIZ / ab["arquivo"])


def _erro_depois(desde_iso):
    """1ª linha [ERRO] do gerar.log depois da mudança (código novo quebrando a produção)."""
    log_g = RAIZ / "estado" / "gerar.log"
    if not log_g.exists():
        return ""
    desde = datetime.fromisoformat(desde_iso)
    for ln in log_g.read_text("utf-8", errors="replace").splitlines()[-400:]:
        m = re.match(r"\[(\d\d)/(\d\d) (\d\d:\d\d:\d\d)\]\s+\[ERRO", ln)
        if m and datetime.fromisoformat(f"{desde.year}-{m[2]}-{m[1]}T{m[3]}") > desde:
            return ln[:200]
    return ""


def julgar(e, c):
    ab = e.get("aberto")
    if not ab:
        return
    erro = _erro_depois(ab["aplicado_em"]) if ab.get("codigo") else ""
    if erro:
        _desfazer(ab)
        e.setdefault("historico", []).append({**ab, "status": "DESFEITO — NÃO REPROPOR",
                                              "motivo": f"a produção deu erro depois do código: {erro}",
                                              "julgado_em": datetime.now().isoformat(timespec="seconds")})
        e["aberto"] = None
        _decisao(f"[melhorador] DESFEITO NA HORA (erro na produção): {ab['titulo']} — {erro}")
        return
    depois = [v for v in _videos() if v["tipo"] == ab["tipo"] and v.get("em", "") >= ab["aplicado_em"][:16]]
    if len(depois) < c["videos_para_julgar"]:
        return
    media = round(sum(v["nota_1a_versao"] for v in depois) / len(depois), 2)
    if media < ab["linha_base"] - c["piora_maxima"]:
        _desfazer(ab)
        status, motivo = "DESFEITO — NÃO REPROPOR", f"1ª versão caiu {ab['linha_base']} → {media}"
    else:
        status, motivo = "ficou", f"1ª versão {ab['linha_base']} → {media}"
    for papel, m in (ab.get("modelos") or {}).items():
        _conta(papel, m, "ficou" if status == "ficou" else "desfeito")
    e.setdefault("historico", []).append({**ab, "status": status, "motivo": motivo,
                                          "julgado_em": datetime.now().isoformat(timespec="seconds")})
    e["aberto"] = None
    _decisao(f"[melhorador] {status}: {ab['titulo']} — {motivo}")
    log(f"julgado: {ab['titulo']} -> {status} ({motivo})")


def _decisao(texto):
    log(texto)
    if not DECISOES.exists():
        return
    linhas = DECISOES.read_text("utf-8").splitlines(keepends=True)
    linhas.insert(2, f"- {datetime.now():%d/%m %H:%M} {texto}\n")
    DECISOES.write_text("".join(linhas), "utf-8")


# ───────────────────────────── ciclo ─────────────────────────────

def _nao_medido(tipo, manual_nome, vids):
    """Texto de aviso se o manual mudou DEPOIS do último vídeo deste tipo (a mudança ainda não foi medida)."""
    ult = [v for v in vids if v["tipo"] == tipo]
    mt = datetime.fromtimestamp((RAIZ / manual_nome).stat().st_mtime)
    if ult and mt.isoformat(timespec="minutes") > ult[-1].get("em", ""):
        return (f"ATENÇÃO: o manual foi mudado em {mt:%d/%m %H:%M}, DEPOIS do último vídeo de {tipo} "
                f"({ult[-1].get('em')}). Essas mudanças ainda NÃO foram medidas em nenhum vídeo. Mexer de novo agora "
                f"contamina o teste: se o defeito já tem regra nova não medida, a resposta certa é ESPERAR.")
    return ""


def ciclo(simular=False, sombra=False):
    c = cfg()
    if not c["ligado"] and not (simular or sombra):
        return
    if sombra:
        preparar_sombra()
    arq_est = SOMBRA / "estado.json" if sombra else EST
    e = _ler(arq_est, {})
    if not (simular or sombra):
        # 28/10 (dona): o melhorador também busca vídeo de referência a cada rodada (fundo; trava própria)
        # 12/11: o cron_auto.bat já roda "referencia.py rodada >> estado\referencia.log" em fundo; com ele escrevendo,
        # o open(..., "a") daqui dava PermissionError (Windows) e o ciclo INTEIRO morria antes do julgar (253 vezes no
        # log; tarefa ClaudeCodeVideo "falhou código 1"). A busca de referência é extra: log ocupado = vai pra outro
        # arquivo; falha ao disparar = segue o ciclo.
        try:
            try:
                saida_ref = open(RAIZ / "estado" / "referencia.log", "a", encoding="utf-8")
            except PermissionError:
                saida_ref = open(RAIZ / "estado" / "referencia_melhorador.log", "a", encoding="utf-8")
            subprocess.Popen([sys.executable, str(RAIZ / "referencia.py"), "rodada"], cwd=str(RAIZ),
                             stdout=saida_ref, stderr=subprocess.STDOUT,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except OSError as erro_ref:
            log(f"referência não disparou ({type(erro_ref).__name__}: {erro_ref}) — segue o ciclo")
        julgar(e, c)
        _gravar(EST, e)
        if e.get("aberto"):
            return  # 1 experimento por vez
    vids = _videos()
    novos = [v for v in vids if v["id"] not in e.get("analisados", [])]
    if not novos and not pedidos_abertos() and not (simular or sombra):
        return
    tipo = (novos or vids)[-1]["tipo"]
    manual_nome = "remotion/EDITOR_ENTRETENIMENTO.md" if tipo == "entretenimento" else "remotion/EDITOR.md"
    aviso = _nao_medido(tipo, manual_nome, vids)
    if aviso and not (simular or sombra):
        log(f"esperando: {aviso}")  # 27/10 (1ª comparação da sombra): o Gemini reforçava regra ainda não testada
        return
    ev, base_vids = evidencia(tipo)
    if len(base_vids) < 2:
        log(f"poucos vídeos de {tipo} ainda ({len(base_vids)}) — espero mais evidência")
        return
    linha_base = round(sum(v["nota_1a_versao"] for v in base_vids[-3:]) / len(base_vids[-3:]), 2)
    modo = "SOMBRA" if sombra else "SIMULAÇÃO" if simular else "valendo"
    log(f"=== ciclo ({modo}) — {tipo}, base 1ª versão {linha_base} ===")
    reg = {"em": datetime.now().isoformat(timespec="seconds"), "tipo": tipo, "base": linha_base, "aviso": aviso,
           "videos": [v["id"] for v in base_vids]}
    ana, m_a = analista(tipo, ev + ("\n\n" + aviso if aviso else ""), e, c)
    defeitos = ana.get("defeitos") or []
    reg.update(analista=m_a, defeitos=defeitos)
    log(f"analista ({m_a}): " + " | ".join(f"{d.get('foco')}: {d.get('defeito')} ({d.get('videos')}v)"
                                          for d in defeitos))
    manual_txt = (base() / manual_nome).read_text("utf-8")
    for d in defeitos[:2]:  # o 1º defeito; se a proposta for vetada, tenta o 2º
        prop, m_p = propositor(tipo, {**d, "aviso": aviso}, manual_nome, manual_txt, e, c)
        reg.setdefault("propostas", []).append({"modelo": m_p, **prop})
        if prop.get("tipo") == "codigo" and c.get("pode_codigo") and not (sombra or simular):
            if _gerar_rodando():
                log("ideia de código: vídeo em produção agora — implemento no próximo ciclo")
                return
            ok, motivo, mud, diff = implementar_codigo(prop, c)
            crit = critico_codigo(prop, diff, c)[0] if ok else {"aprovado": False, "motivo": motivo}
            log(f"código ({m_p}): {prop.get('titulo')} — teste: {'ok' if ok else motivo} — crítico: "
                f"{'APROVADO' if crit.get('aprovado') else 'VETADO'} ({crit.get('motivo')})")
            if ok and crit.get("aprovado"):
                aplicar_codigo(mud, prop, tipo, linha_base, {"analista": m_a, "propositor": m_p}, e)
                marcar_pedido(prop.get("pedido"), f"código aplicado: {prop.get('titulo')} (julgado nos próximos vídeos)")
                reg["decisao"] = f"código aplicado: {prop.get('titulo')}"
                break
            prop = {**prop, "descricao": f"{prop.get('descricao')} [tentativa automática: {crit.get('motivo')}]"}
        if prop.get("tipo") == "codigo":
            if not sombra:
                with IDEIAS.open("a", encoding="utf-8") as f:
                    f.write(f"\n## {datetime.now():%d/%m %H:%M} — {prop.get('titulo')} ({m_p})\n"
                            f"- arquivo: {prop.get('arquivo')}\n- pedido: {prop.get('pedido') or '(defeito do júri)'}\n"
                            f"- {prop.get('descricao')}\n- estado: ESPERANDO A DONA\n")
                marcar_pedido(prop.get("pedido"), "virou ideia de código (IDEIAS_CODIGO.md), espera o seu ok")
            log(f"propositor ({m_p}): CÓDIGO (ideia, não aplicada) — {prop.get('titulo')}")
            reg["decisao"] = "ideia de código"
            break
        if prop.get("tipo") == "esperar":
            log(f"propositor ({m_p}): ESPERAR — {prop.get('hipotese')}")
            reg["decisao"] = "esperar"
            break
        prop.setdefault("arquivo", manual_nome)
        ok, motivo, alvo = validar(prop, c)
        log(f"propositor ({m_p}): {prop.get('titulo')} [{prop.get('tipo')}] — validação: {'ok' if ok else motivo}")
        if not ok:
            reg["propostas"][-1]["validacao"] = motivo
            continue
        crit, m_c = critico(tipo, {**prop, "aviso": aviso}, manual_txt, e, c)
        reg["propostas"][-1]["critico"] = {"modelo": m_c, **crit}
        log(f"crítico ({m_c}): {'APROVADO' if crit.get('aprovado') else 'VETADO'} — {crit.get('motivo')}")
        if not crit.get("aprovado"):
            continue
        _conta("propositor", m_p, "aprovado")
        if simular:
            log("SIMULAÇÃO: aplicaria → " + json.dumps(prop, ensure_ascii=False)[:1500])
            return prop
        if not sombra and _gerar_rodando():
            log("vídeo em produção agora — aplico no próximo ciclo")
            return
        aplicar(alvo, prop, tipo, linha_base, {"analista": m_a, "propositor": m_p, "critico": m_c}, e)
        reg["decisao"] = f"aplicado na {'caixa' if sombra else 'produção'}: {prop.get('titulo')}"
        marcar_pedido(prop.get("pedido"), f"aplicado: {prop.get('titulo')} (julgado nos próximos vídeos)")
        break
    if sombra:
        with (SOMBRA / "rodadas.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
        log(f"SOMBRA: registrado em {SOMBRA / 'rodadas.jsonl'} — decisão: {reg.get('decisao', 'nenhuma')}")
    e["analisados"] = (e.get("analisados", []) + [v["id"] for v in novos])[-200:]
    _gravar(arq_est, e)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg in ("ligar", "desligar"):
        d = _ler(CFG, {})
        d["ligado"] = arg == "ligar"
        _gravar(CFG, {**PADRAO, **d})
        log(f"melhorador {'LIGADO' if d['ligado'] else 'DESLIGADO'}")
    elif arg == "status":
        print(json.dumps({"config": cfg(), "estado": _ler(EST, {}), "modelos": _ler(STATS, {})}, ensure_ascii=False,
                         indent=1))
    else:
        if "--modelo" in sys.argv:  # teste: um modelo só em todos os papéis (ex.: só o Gemini)
            FORCAR.append(sys.argv[sys.argv.index("--modelo") + 1])
        try:
            ciclo(simular=arg == "--simular", sombra=arg == "--sombra")
        except motor.MotorErro as e:
            log(f"ciclo parou: {e} — tento no próximo")


if __name__ == "__main__":
    main()
