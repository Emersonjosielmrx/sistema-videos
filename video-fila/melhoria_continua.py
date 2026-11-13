# -*- coding: utf-8 -*-
r"""melhoria_continua.py — MELHORIAS E CORREÇÕES SEM PARAR nos projetos de vídeo (pedido de 23/10/2026).

Pedido: "um sistema de melhorias contínuas e correções em que eu coloco o prompt dele ou aperto um botão, ele fica
procurando melhorias e correções pra fazer e faz; só as mais críticas me pergunta; eu vou recebendo no Telegram e
respondendo". Decisões (23/10): só os projetos de VÍDEO; sem parar, 1 por vez; crítico = gastar dinheiro/crédito pago.

Como funciona (reaproveita a IA do painel e o atendente dos bots; nada de agente novo):
  1. Ligado (config\melhoria_continua.json "ligado", ou no Telegram: "melhorias ligar"), com a fila da IA do painel
     livre e memória sobrando, pede à IA do painel (painel_ia.pedir "propor") UMA melhoria/correção no próximo projeto
     da roda. O pedido leva o "prompt" + o que já foi feito + o que outras sessões mudaram nas últimas 12 h.
  2. A IA investiga sem mexer e propõe. PROPOSTA normal = aplica sozinha (painel_ia.aplicar: backup de cada arquivo,
     "desfazer" pelo painel ou respondendo DESFAZER no Telegram). Vai pra dona com APLICAR/NÃO só: [PERGUNTA] (gasta
     dinheiro/crédito pago), arquivo protegido (config "protegidos") ou do NÚCLEO (o motor e o Telegram).
  3. Cada resultado chega no bot de produção, curto e em português simples (bots_conversa.py entrega com
     texto_entrega(); responder DESFAZER desfaz). Avisos sem resposta (modo reserva, desfiz sozinho) vão pelo portão.
  4. Terminou -> pausa curta -> a próxima. As regras fixas (nunca apagar, postar só agendado, sem API do Google, sem
     senha/conta...) vão em todo pedido (painel_ia.REGRAS).

Redes de segurança (2ª versão, 23/10 — histórico e motivos em MELHORIAS_CONTINUAS.md):
  - Modelo sem crédito/fora no meio da rodada (402/401/429...) não conta como feito: marca o modelo (ia_reserva) e
    refaz o MESMO projeto, com espera crescente (2, 4, 8... até 60 min) se continuar falhando.
  - MODO RESERVA (o principal, Kiro, sem crédito): proposta da IA reserva vira IDEIA ANOTADA (sem perguntar nada),
    rodadas a cada pausa_reserva_min; quando o principal volta, as ideias são conferidas primeiro. "melhorias reserva
    sim" deixa a reserva aplicar sozinha só conserto pequeno (até pequeno_max_linhas / pequeno_max_arquivos; maior =
    desfeito na hora e vira ideia).
  - Aplicação que parou no meio (erro/parado/modelo caiu) é DESFEITA sozinha; .py que não compila ou .json quebrado
    depois de aplicar = desfeito sozinho. Nunca desfaz por cima de mudança de outra sessão (sem "forçar").
  - Projeto que respondeu "nada a fazer" 2 vezes seguidas descansa descanso_ok_h.
  - Memória: só começa rodada com RAM e memória virtual livres (23/10 a virtual chegou a 0,5 GB: erro 1455).

Telegram (bot de produção): melhorias ligar | parar | status | ideias | reserva sim/não | prompt: <texto>
    python melhoria_continua.py --rodar 39     # motor vivo por 39 min (o vigia geral relança a cada 20)
    python melhoria_continua.py status
Estado: estado\melhoria_continua.json | log: logs\melhoria_continua.log | doc e histórico: MELHORIAS_CONTINUAS.md
"""
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
CONFIG = BASE / "config" / "melhoria_continua.json"
ESTADO = BASE / "estado" / "melhoria_continua.json"
TRAVA = BASE / "estado" / "melhoria_continua.lock"
LOG = BASE / "logs" / "melhoria_continua.log"
HISTORICO = BASE / "MELHORIAS_CONTINUAS.md"
LICOES = BASE / "config" / "melhoria_licoes.md"  # regras aprendidas nas revisões: entram em todo pedido
REVISAO = BASE / "REVISAO_MELHORIAS.md"  # pacote pra qualquer IA revisar o agente (refeito a cada rodada)
BACKLOG = BASE / "estado" / "melhoria_backlog.json"  # 23/10 multiagente: o que o buscador achou, por nota
ORIGEM = "melhoria"
AVISO_ORIGEM = "melhoria contínua"  # portão (avisos.py): bot de produção
PADRAO = {
    "ligado": False,
    "projetos": ["cortes", "voz", "postador", "hipercool", "manhwa-react", "veo", "geral"],
    "pausa_min": 5,
    "pausa_reserva_min": 30,
    "reserva_aplica_pequeno": False,
    "pequeno_max_linhas": 15,
    "pequeno_max_arquivos": 2,
    "descanso_ok_h": 6,
    "ram_min_gb": 2.5,
    # 23/10 (dona: "um pra procurar, outro pra fazer, outro pra revisar"): buscador (só lê, enche o backlog) ->
    # executor (propõe e aplica o melhor item) -> revisor (conversa nova, só lê o diff; REPROVADO = desfaz + lição)
    "multiagente": True,
    "backlog_max": 30,
    "backlog_validade_h": 48,
    # 24/10 (dona): dupla de modelos com visões diferentes — os 2 buscam, um vota na lista do outro (só entra o que
    # os 2 aprovarem) e os 2 revisam o conserto; reprovou = desfaz e refaz com a crítica, até tentativas_max
    "dupla": True,
    "modelo_segundo": "agy/gemini-3.8-flash-high",
    "tentativas_max": 3,
    "voltas_leitura": 40,  # passos dos pedidos só de leitura (o Gemini estourava as 15 padrão em todos, 24/10)
    # 24/10 (dona: "inteligência máxima no Kiro e no Gemini, várias camadas, só o Opus economizado"):
    "kiro_pensar": True,                 # marcas de raciocínio do Kiro (testado: sem elas errou o fuso; com elas acertou)
    "revisores": ["B", "C", "A"],        # B = Gemini; C = Kiro adversário (procura o defeito); A = Kiro do checklist
    "critica_plano": ["B", "A"],         # críticos do PLANO antes de aplicar (nada mexido ainda: barrar aqui é barato)
    "criticas_max": 2,                   # vezes que o plano é refeito com a crítica antes de desistir do item
    "revisao_obrigatoria": True,         # toda aplicação terminada passa pela revisão (com ou sem arquivo mudado)
    "licoes_por_papel": 2500,
    # 24/10: 3ª camada — o Opus 4.6 do Antigravity como juiz final (auditoria_final.py + camada_opus.py)
    "opus_camada": True,
    "opus_modelo": "antigravity/claude-opus-4-6-thinking",
    "opus_base_url": "http://157.173.207.22:20133",  # o Antigravity só funciona pelo mini-proxy da 20133
    "opus_exigir_modelo": "opus-4-6",
    "opus_contas_min": 3,                # "acima de duas contas" com crédito (monitor da dona)
    "opus_contas_min_dona_usando": 8,    # se a dona estiver usando o Opus no VS Code agora
    "opus_dona_janela_min": 20,
    "opus_frescor_min": 15,              # leitura do monitor com no máximo isso de idade
    "opus_prioridade_min": 2,            # 0 = só P0; 1 = P0 e P1; 2 = tudo
    "opus_lote_max": 4,
    "opus_lote_espera_min": 60,
    "opus_dossie_max_chars": 60000,
    "opus_max_tokens": 12000,
    "opus_primeiro_byte_s": 150,         # sem cota, a chamada TRAVA (o gateway varre as ~130 contas)
    "opus_tempo_max_min": 12,
    "opus_chamadas_dia_max": 8,
    "opus_chamadas_hora_max": 2,
    "opus_tokens_dia_max": 300000,
    "opus_fora_min": 30,
    "opus_validade_h": 72,               # P2 que espera mais que isso sai da fila sem gastar Opus
    "opus_tentativas_max": 2,
    "opus_espera_reserva_h": 12,         # P0 sem Opus por esse tempo: um Kiro pensando audita (só avisa a dona)
    "opus_ram_min_gb": 1.0,
    "prompt": ("Procure a melhoria ou correção que MAIS ajuda agora: primeiro erros reais nos logs das últimas 24 h e "
               "coisas que estão falhando ou travando a produção; depois pendências anotadas nos documentos do projeto "
               "(CONTINUAR_*, MELHORIAS_*, PENDENCIAS, relatórios); depois o que deixa os vídeos melhores ou mais vistos."),
}
PERGUNTA = re.compile(r"\[PERGUNTA\]", re.I)
# o próprio motor, a IA do painel e o Telegram: um conserto ruim aqui cala o canal com a dona -> nunca sozinho
NUCLEO = ("melhoria_continua.py", "painel_ia.py", "bots_conversa.py", "vigia_geral.py", "ia_reserva.py", "avisos.py",
          "notificar_telegram.py", "faxina.py", "telegram_bots.json", "telegram.json", "claude_proxy.json",
          "camada_opus.py", "auditoria_final.py", "monitor_opus.py", "melhoria_guarda.json")
CODIGO_SUB = ("", "bin", "mr", "scripts", "comum", "config", "beta", "producao/bin", "producao/config")
# botões fixos no bot de produção (o bots_conversa manda junto da resposta de qualquer comando "melhorias ...")
TECLADO = {"keyboard": [[{"text": "melhorias ligar"}, {"text": "melhorias parar"}],
                        [{"text": "melhorias status"}, {"text": "melhorias ideias"}],
                        [{"text": "melhorias revisão"}, {"text": "melhorias opus"}]],
           "resize_keyboard": True, "is_persistent": True}
RESUMO_TG = ("\nResuma para o dono em no máximo 4 linhas curtas: o que estava errado ou o que dava pra melhorar, o que "
             "muda (ou mudou) e como foi conferido. Sem termos técnicos, sem nomes de arquivo, sem código.")


def _protegidos(c):
    """Arquivos que outra sessão ainda está conferindo na produção (config "protegidos": {nome: "até AAAA-MM-DD"}) +
    o NÚCLEO: o motor não aplica sozinho proposta que mexe neles — vai pra dona como proposta."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    return [n for n, ate in (c.get("protegidos") or {}).items() if str(ate)[:10] >= hoje] + list(NUCLEO)


# 24/10: o painel corta o PEDIDO em 4.000 caracteres — antes as lições (variáveis) vinham no meio e empurravam o
# PROIBIDO pra fora. Agora o pedido só tem o fixo; item, lições e listas vão no CONTEXTO (até 6.000).
PEDIDO = """MELHORIA CONTÍNUA (rodada automática pedida pela dona; você trabalha sozinho, ela só recebe o resumo).
Projeto desta rodada: {projeto} ({pasta}). Pode olhar os outros projetos de vídeo pra entender, mas a mudança é neste.
O QUE A DONA QUER: «{prompt}»
No CONTEXTO: o ITEM desta rodada (se houver), as LIÇÕES (erros que este agente já cometeu: siga SEMPRE, valem mais
que o resto), os arquivos que NÃO pode mexer, o que mudou nas últimas 12 h e o que já foi feito (não repetir; o que
está "DESFEITO — NÃO REPROPOR" não volta). Se houver ITEM, faça ESSE; senão escolha UMA melhoria pequena, concreta e
testável hoje. Confira se o problema AINDA acontece (só conta erro de DEPOIS da última mudança do arquivo).
Se exigir GASTAR DINHEIRO ou crédito pago, proponha mesmo assim mas comece a última linha com
"STATUS: PROPOSTA - [PERGUNTA]" (a dona aprova antes). Se não achar nada que valha (ou o item não acontece mais),
STATUS: OK.
<<PROIBIDO>>
Escreva primeiro "ANÁLISE:" respondendo o CHECK (uma linha por número); depois o PLANO: o que muda, em que arquivo e
como conferir. Dois críticos leem o plano antes de aplicar; depois três revisores e uma auditoria final.
<<CHECK>>"""

# 24/10: revisão do que o agente fez em 23-24/10 (recortou e moveu 296 fotos da dona, religou postagem, rodou a rede
# que agenda upload, reinstalou Pillow por pip, copiou cookies, trocou modelo do Gemini sem testar, leu log sem data
# e UTC como hora local) — vale em TODOS os papéis
PROIBIDO = """PROIBIDO (nunca proponha nem faça, nem "só pra testar"):
- ligar teste novo de conteúdo que a dona não aprovou; mudar voz/formato/efeito/visual dos vídeos sem amostra aprovada;
- ALTERAR, RECORTAR, MOVER, RENOMEAR ou APAGAR mídia (fotos, vídeos, áudios, vozes, pastas de material) — só código
  e config; se achar mídia ruim, anote pra dona;
- postar/despublicar; rodar rotina que posta ou agenda (rede_hora_em_hora, fila ciclo, postar_*, parceiro_diario...);
  mudar config de postagem (postar_*, limites, horários, canais) — nem quando "a pausa já acabou";
- parar/iniciar tarefa agendada, matar processo, reiniciar serviço; pip install/uninstall, mexer em venv;
- login/senha/conta/cookies/perfis do Chrome (nem copiar cookies de um projeto pro outro); Hermes Call; trader;
- trocar modelo/API/chave sem uma chamada real de teste que funcionou HOJE;
- gravar arquivo de estado compartilhado (ex.: sessoes_status.json) num caminho que antes só lia.
DATAS: confira a DATA de toda linha de log que usar como prova (linha sem data não prova nada) e lembre que horário
com "Z"/UTC é 3 h na frente de Brasília. Falso alarme ou nada mudado = STATUS: OK, nunca CONSERTEI."""

# 24/10 (dona: "um thinking simulado que obrigue a pensar"): todo papel que decide responde isto por escrito antes
CHECK = """CHECK (em "ANÁLISE:", uma linha por número: "ok" ou o problema, com a prova):
1 DATA: a prova é de hoje e de depois da última mudança do arquivo? 2 FORA DE ARQUIVO: roda algo que muda o mundo
fora do código (pip, mídia, postar, tarefa, processo, cookies)? 3 PROTEÇÃO: tira/afrouxa trava, checagem, pausa,
limite ou regra comentada? 4 REGRA DA DONA: postagem, conta/login, mídia/voz/formato, dinheiro? 5 MODELO/API: troca
sem chamada real de hoje? 6 REPETIÇÃO: laço/retry que cria processo ou gasta crédito; limite/aborto sem medir o
normal? 7 CAMINHO: o código chega no caminho do problema e trata a causa? 8 OUTROS PROGRAMAS: mexe em estado que
outro programa lê/escreve?"""

LIMITE = ("LIMITE: você tem no máximo uns 30 passos. Não releia o mesmo arquivo nem repita a mesma busca; leia só a "
          "parte que precisa (fim do log, a função). Com uns 20 passos usados, PARE de procurar e entregue a resposta "
          "no formato com o que já conferiu — resposta sem o formato final não vale nada.")

PEDIDO_BUSCADOR = """MELHORIA CONTÍNUA — você é o BUSCADOR: só LÊ e anota, não muda nada. Projeto: {projeto} ({pasta}).
O QUE A DONA QUER (o prompt dela): «{prompt}»
Ache até 5 melhorias ou correções concretas e pequenas NESTE projeto, cada uma com PROVA (linha de log com data e hora,
trecho de código, número do painel). Confira se ainda acontece: erro no log de ANTES da última mudança do arquivo
(lista "MUDADOS" no CONTEXTO) provavelmente já foi consertado. Não repita o que já está no backlog, já foi feito ou
outra sessão acabou de mexer (listas no CONTEXTO). Siga as LIÇÕES do CONTEXTO.
<<PROIBIDO>>
Antes do bloco, "ANÁLISE:" com uma linha por item: a DATA da prova e se cai em algo PROIBIDO (se cair, tire o item).
Notas: impacto 1 a 5 (5 = produção parada ou vídeo se perdendo); risco 1 a 5 (5 = pode quebrar postagem, censura ou
apagar algo). Termine com o bloco abaixo (JSON válido; lista vazia [] se não achar nada que valha) e STATUS: OK.
<<<BACKLOG
[{{"titulo": "...", "evidencia": "...", "arquivos": ["..."], "impacto": 3, "risco": 2, "como_conferir": "..."}}]
BACKLOG>>>
<<LIMITE>>"""

PEDIDO_CRITICO = """MELHORIA CONTÍNUA — você é o CRÍTICO DO PLANO: só LÊ e confere, não muda nada. Outra IA propôs a mudança
do CONTEXTO em {projeto} ({pasta}); NADA foi aplicado ainda. Se você aprovar, ela é aplicada sozinha logo depois.
Confira você mesmo, abrindo os arquivos e logs citados: a premissa é verdadeira HOJE (veja a data das linhas)? O plano
resolve a causa? Mexe só no necessário? Respeita as regras abaixo e as LIÇÕES do CONTEXTO?
<<PROIBIDO>>
Escreva "ANÁLISE:" respondendo o CHECK (uma linha por número, com a prova) e termine com UMA linha e, depois dela,
STATUS: OK
VEREDITO: APROVADO - <motivo curto>
VEREDITO: REPROVADO - <o que está errado e como deveria ser, escrito pro outro agente refazer>
VEREDITO: DÚVIDA - <o que a dona precisa decidir, em palavras simples>
Aprovação sem a ANÁLISE não vale. Só reprove por problema real que você confirmou; estilo e gosto não contam.
<<CHECK>>
<<LIMITE>>"""

PEDIDO_REVISOR = """MELHORIA CONTÍNUA — você é o REVISOR: só LÊ e confere, não muda nada. Outra IA acabou de aplicar
sozinha uma melhoria em {projeto} ({pasta}). O QUE ELA DIZ QUE FEZ: {feito}
No CONTEXTO: o item que era pra fazer, os comandos que ela rodou, o que a guarda viu, as lições e o diff (cortado se
for grande; o arquivo de ANTES está no caminho "backup" e o de agora no caminho original: leia os dois se precisar).
Confira: 1) censura, postagem (sempre agendada, só pelo navegador), "nunca apagar, mover pro Drive", contas/login:
iguais? 2) o caminho normal ficou igual, ou a parte nova tem volta pro jeito antigo se falhar? 3) compila e o teste
do arquivo (se houver) passa? Rode python -m py_compile / o teste. 4) não mexeu em arquivo protegido (lista no
CONTEXTO)? 5) os COMANDOS mostram algo proibido (pip, mídia, postar/rede, tarefa, processo, cookie, config de postagem)? Se sim:
REPROVADO.
<<PROIBIDO>>
Escreva "ANÁLISE:" respondendo o CHECK (uma linha por número, com a prova) e termine com UMA linha e, depois dela,
STATUS: OK
VEREDITO: APROVADO - <motivo curto>
VEREDITO: REPROVADO - <o que está errado, escrito como lição pro outro agente: "não faça X; faça Y">
VEREDITO: DÚVIDA - <o que a dona precisa decidir, em palavras simples>
Aprovação sem a ANÁLISE não vale. Só reprove por problema real que você confirmou; estilo e gosto não contam.
<<CHECK>>
<<LIMITE>>"""

# 24/10 (dona: "um agente revisor só dele"): o Kiro adversário parte do princípio de que tem defeito
ADVERSARIO = ("\nVOCÊ É O REVISOR ADVERSÁRIO: parta do princípio de que esta mudança tem um defeito e procure-o de "
              "verdade (abra o arquivo inteiro na parte mudada, rode o py_compile, procure no log a linha com data). "
              "Só aprove se, depois de conferir o CHECK com prova, não achar nenhum.")

PEDIDO_VOTO = """MELHORIA CONTÍNUA — você é o SEGUNDO PAR DE OLHOS: só LÊ, não muda nada. Outra IA procurou melhorias em
{projeto} ({pasta}) e achou a lista do CONTEXTO. Confira cada item você mesmo: a prova existe e o problema ainda
acontece (erro de antes da última mudança do arquivo provavelmente já foi consertado)? Vale a pena fazer? O risco está
certo? A prova é de HOJE (veja a data da linha)? Não cai em nada proibido abaixo?
<<PROIBIDO>>
Antes do bloco, "ANÁLISE:" com uma linha por item (DATA da prova, PROIBIDO, CAMINHO). Concorde só com o que você
conferiu e acha que deve ser feito. Termine com o bloco abaixo (um voto por item, JSON válido) e STATUS: OK.
<<<VOTOS
[{{"n": 1, "concordo": true, "motivo": "..."}}]
VOTOS>>>
<<LIMITE>>"""


def _montar(t):
    return t.replace("<<PROIBIDO>>", PROIBIDO).replace("<<CHECK>>", CHECK).replace("<<LIMITE>>", LIMITE)


PEDIDO, PEDIDO_BUSCADOR, PEDIDO_CRITICO, PEDIDO_REVISOR, PEDIDO_VOTO = (
    _montar(PEDIDO), _montar(PEDIDO_BUSCADOR), _montar(PEDIDO_CRITICO), _montar(PEDIDO_REVISOR), _montar(PEDIDO_VOTO))
VEREDITO = re.compile(r"VEREDITO:?\**\s*\**\s*(APROVADO|REPROVADO|D[UÚ]VIDA)\**\s*[-—:]?\s*(.*)", re.I)
ANALISE = re.compile(r"AN[AÁ]LISE\s*\**\s*:", re.I)
LADOS = {"A": "o revisor principal (Kiro)", "B": "o 2º modelo (Gemini)", "C": "o revisor adversário (Kiro)"}


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(p)


def cfg():
    c = dict(PADRAO)
    c.update(_ler(CONFIG, {}))
    return c


def _salvar_cfg(**mudar):
    c = _ler(CONFIG, {}) or dict(PADRAO)
    c.update(mudar)
    _gravar(CONFIG, c)


def _estado():
    e = _ler(ESTADO, {})
    e.setdefault("feitos", [])        # [{"quando", "projeto", "resumo", "job", "status"}]
    e.setdefault("vez", 0)            # índice da roda de projetos
    e.setdefault("atual", None)       # job do painel em andamento (propor ou aplicar)
    e.setdefault("entregar", [])      # jobs que o bots_conversa ainda não pegou pra mandar no Telegram
    e.setdefault("proxima_em", 0)
    e.setdefault("ideias", [])        # propostas da IA reserva, conferidas quando o principal voltar
    e.setdefault("falhas", [])        # rodadas perdidas por erro do modelo/gateway (não contam como feitas)
    e.setdefault("falhas_seguidas", 0)
    e.setdefault("repetir", None)     # projeto a refazer (a rodada caiu por erro do modelo)
    e.setdefault("motivos", {})       # job -> por que foi pra dona
    e.setdefault("pequenos", [])      # aplicações da reserva que precisam caber no "pequeno"
    e.setdefault("ok_seguidos", {})   # projeto -> quantos "nada a fazer" seguidos
    e.setdefault("descanso", {})      # projeto -> até quando fica fora da roda
    e.setdefault("modo_avisado", None)
    e.setdefault("vigiar", [])        # melhorias aplicadas sendo vigiadas na produção (VIGIADA_H)
    e.setdefault("sem_memoria_desde", None)
    e.setdefault("registrados", [])   # aplicações aprovadas pela dona no Telegram que já entraram no histórico
    e.setdefault("papeis", {})        # job -> {"papel": "buscador"|"revisor", ...} (pedidos só de leitura)
    e.setdefault("item_atual", None)  # item do backlog que o executor está fazendo (o revisor confere contra ele)
    e.setdefault("livre", None)       # projeto cujo buscador não respondeu no formato: a próxima rodada é a antiga
    e.setdefault("duvidas", {})       # aplicação -> dúvida do revisor (vai junto no Telegram)
    e.setdefault("busca", None)       # busca em dupla em andamento: {"projeto", "A", "B", "ok"}
    e.setdefault("revisao", None)     # revisão em dupla em andamento: {"aplicado", "vereditos": {lado: [v, motivo]}}
    e.setdefault("refazer", None)     # item reprovado na revisão, refeito com a crítica antes do resto do backlog
    e.setdefault("critica", None)     # crítica do plano em andamento: {"proposta", "vereditos", "fila"}
    return e


def _ram_gb():
    """Memória que dá pra usar agora: a menor entre a RAM livre e o que sobra da memória virtual (23/10: a virtual chegou
    a 0,5 GB livre e programas falharam com erro 1455, mesmo com RAM sobrando de vez em quando)."""
    livres = []
    try:
        import psutil
        livres.append(psutil.virtual_memory().available)
    except ImportError:
        pass
    try:
        import ctypes

        class _Mem(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = _Mem()
        m.dwLength = ctypes.sizeof(_Mem)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            livres += [m.ullAvailPhys, m.ullAvailPageFile]
    except Exception:  # noqa: BLE001
        pass
    return min(livres) / 1024 ** 3 if livres else 99


def _historico(linha):
    try:
        novo = not HISTORICO.exists()
        with open(HISTORICO, "a", encoding="utf-8") as f:
            if novo:
                f.write("# Melhorias contínuas (automáticas)\n\n## Histórico (1 linha por rodada)\n\n")
            f.write(linha + "\n")
    except OSError:
        pass


def _texto(job):
    return f"{job.get('detalhe') or ''}\n{job.get('resposta') or ''}"


def _resumo(job):
    """1 linha do que a rodada achou/fez: o detalhe do STATUS; sem ele, o erro ou o começo da resposta
    (23/10: rodada que morreu sem crédito virava "success" no histórico)."""
    det = " ".join(str(job.get("detalhe") or "").split())
    if det and not re.fullmatch(r"success|error_\w+|erro do agente", det):
        return det[:200]
    resp = re.sub(r"\n?STATUS:.*$", "", str(job.get("resposta") or ""), flags=re.S | re.I).strip()
    m = re.search(r"API Error[^\n]*", resp)
    linha = m.group(0) if m else (resp.splitlines()[0] if resp else (det or str(job.get("status") or "")))
    return " ".join(linha.split())[:200]


def _quando(job):
    return (job.get("fim") or job.get("criado") or "")[:16].replace("T", " ")


def _avisar(texto):
    """Aviso que não espera resposta (modo reserva, desfiz sozinho...) — pelo portão, bot de produção."""
    try:
        import avisos
        avisos.enviar(texto, AVISO_ORIGEM, importante=True, html_ok=False)
    except Exception as ex:  # noqa: BLE001
        log(f"aviso não saiu ({type(ex).__name__}: {ex})")


def _desfazer(job, motivo, quem="melhorias contínuas (motor)"):
    """Desfaz o que a aplicação mudou. Nunca força: se outra sessão mexeu depois, deixa e conta no log.
    quem (24/10, achado 9): fica gravado em desfeito_por (antes saía 'pelo dono no painel')."""
    import inspect
    import painel_ia
    if not job.get("manifesto") or job.get("desfeito_em"):
        return False
    try:
        if "quem" in inspect.signature(painel_ia.desfazer).parameters:
            painel_ia.desfazer(job["id"], quem=f"{quem}: {motivo}"[:200])
        else:
            painel_ia.desfazer(job["id"])
        log(f"{job['id']}: DESFEITO sozinho ({motivo})")
        return True
    except Exception as ex:  # noqa: BLE001
        log(f"{job['id']}: não desfiz ({motivo}): {ex}")
        return False


def _quebrados(job):
    """Depois de aplicar: cada .py ainda compila e cada .json ainda abre? Devolve o que quebrou."""
    ruins = []
    for orig in (job.get("manifesto") or {}):
        p = Path(orig)
        if not p.is_file() or p.suffix.lower() not in (".py", ".json"):
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            if p.suffix.lower() == ".py":
                compile(txt, str(p), "exec")
            else:
                json.loads(txt)
        except (SyntaxError, ValueError) as ex:
            ruins.append(f"{p.name}: {type(ex).__name__}: {str(ex)[:120]}")
    return ruins


def _tamanho(jid):
    """(arquivos, linhas mudadas) de uma aplicação, pelo diff backup x agora."""
    import painel_ia
    try:
        ms = painel_ia.mudancas(jid)
    except Exception:  # noqa: BLE001
        return 0, 0
    linhas = sum(1 for m in ms for ln in m["diff"].splitlines()
                 if ln[:1] in "+-" and not ln.startswith(("+++", "---")))
    return len(ms), linhas


VIGIADA_H = 6  # depois de aplicada, a melhoria é vigiada na produção por esse tempo
TRACEBACK = re.compile(r"Traceback \(most recent call last\):\n(?:[ \t]+[^\n]*\n)+[^\n]+")


def _logs_do_projeto(pasta):
    saida = []
    for d in {Path(pasta) / "logs", BASE / "logs"}:
        if d.is_dir():
            saida += [p for p in d.glob("*.log") if p.is_file()]
    return saida


def _comecar_vigia(e, job):
    """Guarda onde cada log do projeto está agora: depois só o que for escrito DEPOIS da mudança conta."""
    import painel_ia
    arqs = [o for o in (job.get("manifesto") or {}) if o.lower().endswith(".py")]
    if not arqs:
        return
    pasta = painel_ia.PROJETOS.get(job["projeto"], ("", str(BASE)))[1]
    tamanhos = {}
    for p in _logs_do_projeto(pasta):
        try:
            tamanhos[str(p)] = p.stat().st_size
        except OSError:
            continue
    e["vigiar"].append({"job": job["id"], "projeto": job["projeto"], "arquivos": arqs, "desde": time.time(),
                        "logs": tamanhos})


def _vigiar_producao(e):
    """Revisar na produção real (regra da dona): até VIGIADA_H depois de aplicada, um Traceback NOVO num log do projeto
    que passe por um arquivo que a melhoria mudou = desfaz sozinho e avisa. Olha no máximo a cada 10 min."""
    import painel_ia
    if not e["vigiar"] or time.time() - float(e.get("vigia_ultimo", 0)) < 600:
        return False
    e["vigia_ultimo"] = time.time()
    manter = []
    for v in e["vigiar"]:
        if time.time() - v["desde"] > VIGIADA_H * 3600:
            continue
        pasta = painel_ia.PROJETOS.get(v["projeto"], ("", str(BASE)))[1]
        nomes = [Path(a).name.lower() for a in v["arquivos"]]
        achado = None
        for p in _logs_do_projeto(pasta):
            try:
                tam, ini = p.stat().st_size, int(v["logs"].get(str(p), 0))  # log que nasceu depois: lê do começo
                if tam <= ini:
                    continue
                with open(p, "rb") as f:
                    f.seek(max(ini, tam - 400_000))
                    novo = f.read().decode("utf-8", "replace").replace("\r\n", "\n")
            except OSError:
                continue
            for bloco in TRACEBACK.findall(novo):
                if any(f'{n}"' in bloco.lower() for n in nomes):
                    achado = (p.name, bloco.strip().splitlines()[-1][:160])
                    break
            if achado:
                break
        if not achado:
            manter.append(v)
            continue
        job = painel_ia.ler(v["job"]) or {}
        motivo = f"erro novo na produção depois dela ({achado[0]}: {achado[1]})"
        desfeito = _desfazer(job, motivo) if job else False
        _historico(f"- {datetime.now():%Y-%m-%d %H:%M} | {v['projeto']} | {'DESFEITO' if desfeito else 'NÃO DESFEITO'} "
                   f"na produção: {motivo} | {v['job']}")
        nome = painel_ia.PROJETOS.get(v["projeto"], (v["projeto"],))[0]
        _avisar(f"Uma melhoria automática em {nome} "
                + ("foi desfeita sozinha: depois dela o programa começou a dar erro na produção. Tudo voltou como estava."
                   if desfeito else
                   "pode ter causado erro na produção e NÃO consegui desfazer sozinho (o arquivo mudou depois). "
                   f"Se precisar, desfaça no painel (aba IA, pedido {v['job']})."))
    e["vigiar"] = manter
    return True


def _recentes(pasta, horas=12, limite=25):
    """Código e configs mudados nas últimas `horas` no projeto e no D:\\video-fila (o que outras sessões já mexeram)."""
    corte, achados = time.time() - horas * 3600, {}
    for base in {Path(pasta), BASE}:
        for sub in CODIGO_SUB:
            pasta_sub = base / sub
            if not pasta_sub.is_dir():
                continue
            for p in pasta_sub.glob("*"):
                if p.suffix.lower() not in (".py", ".bat", ".ps1", ".json", ".md") or not p.is_file():
                    continue
                if re.search(r"\.(bak|bkp|antes|orig|tmp)|_bak_|_bkp_", p.name, re.I) or p.name == HISTORICO.name:
                    continue
                try:
                    mt = p.stat().st_mtime
                except OSError:
                    continue
                if mt >= corte:
                    achados[str(p)] = mt
    linhas = [f"- {datetime.fromtimestamp(mt):%d/%m %H:%M} {p}"
              for p, mt in sorted(achados.items(), key=lambda x: -x[1])[:limite]]
    return "\n".join(linhas) or f"- (nada nas últimas {horas} h)"


def _consertos_recentes(limite=12):
    linhas = []
    try:
        linhas += [ln.strip() for ln in (BASE / "consertos_ia" / "INDICE.md").read_text(
            encoding="utf-8", errors="replace").splitlines() if ln.startswith("- ")][-limite:]
    except OSError:
        pass
    for diario in (BASE / "VIGIA_DIARIO.md", Path(r"D:\hipercool-videos\docs\VIGIA_DIARIO.md")):
        try:
            linhas += [ln.strip() for ln in diario.read_text(encoding="utf-8", errors="replace").splitlines()
                       if ln.startswith("## ")][-6:]
        except OSError:
            pass
    return "\n".join(x[:220] for x in linhas) or "- (nada)"


def _licoes(limite=6000):
    """As lições (linhas "- " do config\\melhoria_licoes.md, com as continuações) que vão em todo pedido."""
    try:
        linhas = LICOES.read_text(encoding="utf-8").splitlines()
    except OSError:
        return "- (nenhuma ainda)"
    itens = []
    for ln in linhas:
        if ln.startswith("- "):
            itens.append(ln)
        elif itens and ln.startswith("  ") and ln.strip():
            itens[-1] += " " + ln.strip()
    # 24/10: as marcadas [FIXA] entram sempre (as da revisão de 23-24/10); o resto, as mais novas primeiro
    fixas = [i for i in itens if "[FIXA]" in i]
    texto, saida = sum(len(i) for i in fixas), []
    for item in reversed([i for i in itens if "[FIXA]" not in i]):
        if texto + len(item) > limite:
            break
        saida.insert(0, item)
        texto += len(item)
    return "\n".join(fixas + saida) or "- (nenhuma ainda)"


def _pedir(tipo, pedido, **kw):
    """painel_ia.pedir passando só o que ele aceita (pensar/voltas/modelo podem não existir numa versão antiga)."""
    import inspect
    import painel_ia
    aceitos = inspect.signature(painel_ia.pedir).parameters
    if _ATUAL:  # 24/10: modo ASSUMIR do Opus 5.5 (botão) — com cota, o pedido vai pro Opus 5.5 em esforço máximo
        try:
            import opus55
            kw = opus55.ajustar(kw, *_ATUAL)
        except Exception as ex:  # noqa: BLE001 — na dúvida, fluxo normal
            log(f"opus55 não ajustou o pedido ({type(ex).__name__}: {ex})")
    return painel_ia.pedir(tipo, pedido, **{k: v for k, v in kw.items() if k in aceitos})


_ATUAL = None  # (c, e) da volta atual do motor (o _pedir é chamado de muitos lugares sem o estado)


def _sem_segredo(txt):
    """24/10 (achado 16): o que vai pra revisor/Opus/dona sai sem chave nem linha de cookie (Netscape: 7 campos com
    TAB, ou domínio TRUE/FALSE caminho ...)."""
    s = "\n".join(ln for ln in str(txt or "").splitlines()
                  if not re.match(r"^#?\s*\.?[\w.-]+\.\w+\s+(?:TRUE|FALSE)\s+\S+\s+(?:TRUE|FALSE)\s+\d+\s", ln))
    try:
        import camada_opus
        return camada_opus._limpar(s, 10 ** 7)
    except Exception:  # noqa: BLE001
        s = re.sub(r"(?i)(bearer\s+)[^\s\"',;]+", r"\1<chave>", s)
        s = re.sub(r"\b(?:sk|pk|rk)-[A-Za-z0-9_\-]{8,}", "<chave>", s)
        return " ".join(re.sub(r"[A-Za-z0-9_\-+=]{32,}", "<...>", s).split())


def _comandos(jid, limite=3000, so_lista=False):
    """Os comandos de terminal que o pedido rodou, com o começo da saída (24/10: os revisores só viam o fim do texto
    final — o pip, a rede rodada à mão e o mv das fotos passavam)."""
    import painel_ia
    if not jid:
        return [] if so_lista else ""
    conv = painel_ia.conversa(jid, limite=800)
    cmds = []
    for i, x in enumerate(conv):
        if x.get("quem") == "ferramenta" and str(x.get("texto", "")).startswith("rodando"):
            prox = conv[i + 1] if i + 1 < len(conv) and conv[i + 1].get("quem") == "resultado" else {}
            cmds.append((str(x.get("detalhe") or x["texto"]), str(prox.get("texto") or ""), bool(prox.get("erro"))))
    if so_lista:
        return cmds
    linhas = [f"$ {_sem_segredo(cmd)[:400]}\n  -> {_sem_segredo(saida)[:300]}{' (ERRO/BLOQUEADO)' if erro else ''}"
              for cmd, saida, erro in cmds]
    return _corta("\n".join(linhas), limite) if linhas else ""


def _nova_licao(texto, origem):
    texto = " ".join(str(texto).split())[:600]
    novo = not LICOES.exists()
    with open(LICOES, "a", encoding="utf-8") as f:
        if novo:
            f.write("# Lições do agente de melhorias contínuas\n\n")
        f.write(f"- [{datetime.now():%Y-%m-%d}, {origem}] {texto}\n")


PROMPT_REVISAO = (
    "Revise o trabalho do agente de IA que faz melhorias contínuas sozinho no meu sistema de vídeos: conserte o que ele "
    "fez de errado, liste o que ele fez de certo e melhore o próprio agente (lições do tipo \"não faça isso\" / \"faça "
    "assim\" e mudanças no jeito dele trabalhar, coisas que não enxergamos quando o criamos).\n"
    "- Se você consegue abrir arquivos e rodar comandos no meu computador: leia D:\\video-fila\\REVISAO_MELHORIAS.md "
    "e faça tudo o que ele pede (julgar cada mudança, desfazer/consertar as erradas, gravar as lições, anotar a revisão).\n"
    "- Se não consegue: o arquivo REVISAO_MELHORIAS.md está anexado (ou colado abaixo). Faça o que ele pede e me devolva "
    "os consertos prontos num bloco \"PARA COLAR NO CLAUDE CODE\" e as lições em linhas que começam com "
    "\"melhorias regra: \".\n"
    "No fim, me responda em português simples, sem termos técnicos: 1) o que ele fez certo; 2) o que fez errado e o que "
    "foi (ou precisa ser) consertado; 3) dúvidas; 4) o que responder nas perguntas pendentes dele (APLICAR ou NÃO); "
    "5) lições novas pro agente; 6) o que mudar no jeito dele trabalhar.")

INSTRUCOES_REVISAO = r"""# REVISÃO DO AGENTE DE MELHORIAS CONTÍNUAS — leia e faça o que está aqui

Você vai revisar o trabalho de um agente de IA que melhora SOZINHO, sem parar, um sistema de produção e postagem
automática de vídeos (YouTube, TikTok, Instagram) num computador Windows (pastas D:\...). A cada rodada ele escolhe um
projeto, investiga, propõe UMA mudança pequena e aplica sozinho (com cópia de cada arquivo antes); só pergunta à dona
quando gasta dinheiro ou mexe em parte sensível. Este arquivo foi gerado automaticamente em {quando} e traz tudo o que
ele mudou desde a última revisão ({desde}): o motivo que ele deu, o código antes/depois (diff) e o relato dele.

## Suas 3 tarefas

1. JULGAR cada mudança: CERTA, ERRADA ou DUVIDOSA, com o motivo em 1 linha. Confira:
   a) a premissa é verdadeira (o problema existia, e ainda existia quando ele mexeu)?
   b) ele tirou alguma proteção que o código explicava em comentário?
   c) a afirmação técnica dele está certa?
   d) fere alguma regra da dona (lista abaixo)?
   e) o código está correto (lógica, caso esquecido, laço sem fim, efeito em outra parte do sistema)?
2. CONSERTAR as erradas:
   - Se você consegue ler e mudar arquivos neste computador: desfaça pelo sistema (volta a cópia de antes):
     D:\veo\venv\Scripts\python.exe -c "import sys; sys.path.insert(0, r'D:\video-fila'); import painel_ia; print(painel_ia.desfazer('<código>'))"
     Se recusar porque "o arquivo mudou depois", NÃO force: conserte à mão só a parte errada e teste. Depois anote no fim
     de D:\video-fila\MELHORIAS_CONTINUAS.md: "- AAAA-MM-DD HH:MM | projeto | DESFEITO na revisão de <você>: motivo | código".
   - Se você NÃO consegue mexer no computador: escreva o conserto pronto num bloco "PARA COLAR NO CLAUDE CODE"
     (ex.: "desfaça o pedido <código> com painel_ia.desfazer" ou "no arquivo X troque o trecho A pelo B"); a dona cola
     num chat que tem acesso ao computador.
3. MELHORAR O PRÓPRIO AGENTE (o mais importante a longo prazo). Olhe o conjunto: que tipo de erro ele repete? o que ele
   não enxergou? que regra teria evitado? como ele deveria trabalhar diferente?
   - LIÇÕES: regras curtas pra ele seguir daqui em diante, no formato "NÃO faça X / FAÇA Y (caso: ...)".
     Com acesso ao computador: acrescente cada uma como uma linha "- [AAAA-MM-DD, revisão <você>] ..." no fim de
     D:\video-fila\config\melhoria_licoes.md (entra em todo pedido dele a partir da próxima rodada).
     Sem acesso: escreva cada uma numa linha começando com "melhorias regra: " — a dona manda essas linhas no bot de
     produção do Telegram e o agente aprende.
   - LIÇÕES ATUAIS (mais abaixo): alguma está errada, repetida ou atrapalhando? Diga qual apagar (com acesso, apague).
   - MUDANÇAS NO FUNCIONAMENTO: o que mudar no jeito dele trabalhar (o que olhar antes de propor, como escolher o que
     fazer, quando perguntar à dona, o que nunca tocar, como conferir depois). O funcionamento está resumido abaixo.
     Descreva a mudança e por quê; com acesso ao computador, anote em "Ideias pra depois" do MELHORIAS_CONTINUAS.md
     (o código do agente é D:\video-fila\melhoria_continua.py; só mude ele se for pequeno, testado e anotado).

## Resposta para a dona (português simples, sem termos técnicos)

1. O que ele fez CERTO (lista curta: o que melhorou pra ela).
2. O que ele fez ERRADO e o que você fez (ou o que precisa ser feito).
3. O que ficou em DÚVIDA.
4. Perguntas pendentes dele: responder APLICAR ou NÃO, e por quê.
5. Lições novas pro agente (sem acesso ao computador: as linhas "melhorias regra: ...").
6. Mudanças sugeridas no funcionamento do agente.
Com acesso ao computador, termine anotando no fim do MELHORIAS_CONTINUAS.md:
"- AAAA-MM-DD HH:MM | geral | revisão de <você>: N conferidas, N desfeitas, N lições | -" (a próxima revisão começa daí).
"""


def _ultima_revisao():
    """Quando foi a última revisão anotada no histórico (linha "| geral | revisão de ..."); sem ela, 3 dias atrás."""
    ultima = None
    try:
        for ln in HISTORICO.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^- (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) \| [^|]+ \| revis[aã]o\b", ln)
            if m:
                ultima = m.group(1)
    except OSError:
        pass
    return ultima or datetime.fromtimestamp(time.time() - 3 * 86400).strftime("%Y-%m-%d %H:%M")


def _diffs_do_documento(jid):
    """Os diffs gravados no documento do conserto logo depois de aplicar (consertos_ia\\<id>.md)."""
    try:
        doc = (BASE / "consertos_ia" / f"{jid}.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return re.findall(r"### diff (.+?)\n\n```diff\n(.*?)```", doc, re.S)


def _corta(texto, n):
    texto = str(texto or "").strip()
    return texto if len(texto) <= n else texto[:n] + f"\n[... cortado: mais {len(texto) - n} caracteres]"


def _citar(texto):
    """Texto do agente como citação ("> "): os títulos dele (## CAUSA...) não se misturam com as seções do pacote."""
    return "\n".join("> " + ln for ln in str(texto or "").splitlines()) if texto else ""


def pacote_revisao(e=None):
    """Gera REVISAO_MELHORIAS.md: instruções + funcionamento + regras + lições + cada mudança desde a última revisão
    (motivo, diff, relato), perguntas pendentes e rodadas sem mudança. Serve pra QUALQUER IA (com ou sem acesso ao PC)."""
    import painel_ia
    e = e or _estado()
    desde = _ultima_revisao()
    novo = lambda q: (q or "").replace("T", " ")[:16] >= desde  # noqa: E731
    partes = [INSTRUCOES_REVISAO.replace("{quando}", datetime.now().strftime("%Y-%m-%d %H:%M")).replace("{desde}", desde)]
    try:
        doc = HISTORICO.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\n## O que ele faz sozinho.*?(?=\n## Peças)", doc, re.S)
        if m:
            partes += ["## Como o agente funciona (resumo)", m.group(0).strip()]
    except OSError:
        pass
    partes += ["## Regras fixas da dona (valem sempre)", painel_ia.REGRAS,
               "## Lições atuais do agente (config\\melhoria_licoes.md)", _licoes()]
    mudancas, outras = [], []
    for f in e["feitos"]:
        if not novo(f.get("quando")):
            continue
        job = painel_ia.ler(f["job"]) or {}
        (mudancas if job.get("tipo") == "aplicar" else outras).append((f, job))
    falhas = [x for x in e["falhas"] if novo(x.get("quando"))]
    pendentes = []
    for jid, motivo in e["motivos"].items():
        pai = painel_ia.ler(jid) or {}
        if pai and not pai.get("aplicado_em") and novo(pai.get("fim") or pai.get("criado")):
            pendentes.append((pai, motivo))
    partes.append("## Números desde a última revisão")
    partes.append(f"- {len(mudancas)} mudança(s) aplicada(s), "
                  f"{sum(1 for _f, j in mudancas if j.get('desfeito_em'))} já desfeita(s); "
                  f"{len(outras)} rodada(s) sem mudança; {len(falhas)} rodada(s) perdida(s) por falha da IA; "
                  f"{len(pendentes)} pergunta(s) pendente(s) pra dona.")
    partes.append("## Mudanças aplicadas (uma por uma)")
    if not mudancas:
        partes.append("(nenhuma desde a última revisão)")
    if len(mudancas) > 25:
        partes.append(f"(mostrando as 25 mais novas; {len(mudancas) - 25} mais antigas ficaram de fora)")
    for i, (f, job) in enumerate(mudancas[-25:], 1):
        pai = painel_ia.ler(job.get("pai") or "") or {}
        situacao = ("JÁ DESFEITA em " + str(job["desfeito_em"])[:16]) if job.get("desfeito_em") else "aplicada (valendo)"
        partes += [f"### {i}. {f['quando'][:16].replace('T', ' ')} — {f['projeto']} — {f['resumo']}",
                   f"Código do pedido: {job.get('id')} | situação: {situacao} | IA: {job.get('modelo') or '?'}"
                   + (f" | proposta: {pai.get('id')}" if pai else ""),
                   "Arquivos: " + (", ".join(job.get("manifesto") or {}) or "(nenhum)"),
                   "**Por que ele fez (a proposta dele):**", _citar(_corta(pai.get("resposta"), 2500)) or "(sem proposta)"]
        diffs = _diffs_do_documento(job.get("id"))
        if not diffs:
            try:
                diffs = [(Path(m["arquivo"]).name, m["diff"]) for m in painel_ia.mudancas(job.get("id"))]
            except Exception:  # noqa: BLE001
                diffs = []
        for nome, d in diffs:
            partes += [f"**O que mudou em {nome}:**", "```diff\n" + _corta(d, 3500) + "\n```"]
        partes += ["**Relato dele depois de aplicar:**", _citar(_corta(job.get("resposta"), 1200)) or "(sem relato)"]
    partes.append("## Perguntas pendentes pra dona (ele não aplicou; esperam APLICAR ou NÃO)")
    if not pendentes:
        partes.append("(nenhuma)")
    for pai, motivo in pendentes:
        partes += [f"### {(pai.get('fim') or pai.get('criado') or '')[:16].replace('T', ' ')} — {pai.get('projeto')} — "
                   f"{_resumo(pai)}", f"Código: {pai.get('id')} | por que perguntou: {motivo}",
                   _citar(_corta(pai.get("resposta"), 2000))]
    partes.append("## Rodadas sem mudança e falhas (contexto)")
    partes += [f"- {f['quando'][:16].replace('T', ' ')} | {f['projeto']} | {f['status']} | {f['resumo']}" for f, _j in outras]
    partes += [f"- {x['quando']} | {x['projeto']} | FALHA ({x.get('modelo')}) | {x['erro']}" for x in falhas]
    if not outras and not falhas:
        partes.append("(nenhuma)")
    texto = "\n\n".join(partes) + "\n"
    tmp = REVISAO.with_name(REVISAO.name + ".tmp")
    tmp.write_text(texto, encoding="utf-8")
    tmp.replace(REVISAO)
    return len(mudancas)


def _modo():
    """("principal" | "reserva", modelo principal). Usa a mesma ordem que a IA do painel vai usar (ia_reserva)."""
    import ia_reserva
    import painel_ia
    try:
        principal = json.loads(painel_ia.PROXY.read_text(encoding="utf-8"))["modelo"]
    except (OSError, ValueError, KeyError):
        return "principal", "?"
    ordem = ia_reserva.modelos(principal)
    return ("principal" if ordem and ordem[0] == principal else "reserva"), principal


def _fim_de_rodada(e, c, pausa_min=None):
    e["feitos"] = e["feitos"][-200:]
    e["falhas"] = e["falhas"][-50:]
    e["ideias"] = e["ideias"][-60:]
    e["motivos"] = dict(list(e["motivos"].items())[-80:])
    e["proxima_em"] = time.time() + float(pausa_min if pausa_min is not None else c["pausa_min"]) * 60
    try:  # o pacote de revisão (REVISAO_MELHORIAS.md) fica sempre em dia pra qualquer IA revisar
        pacote_revisao(e)
    except Exception as ex:  # noqa: BLE001
        log(f"pacote de revisão não saiu ({type(ex).__name__}: {ex})")


def _falhou_modelo(e, c, job):
    """A rodada caiu por erro do modelo/gateway: não conta, marca o modelo e refaz o mesmo projeto mais tarde."""
    import ia_reserva
    texto = _texto(job)
    if job.get("modelo"):
        ia_reserva.marcar(job["modelo"], texto)
    e["falhas_seguidas"] += 1
    e["falhas"].append({"quando": _quando(job), "projeto": job["projeto"], "modelo": job.get("modelo"),
                        "erro": _resumo(job), "job": job["id"]})
    if job["tipo"] == "propor":
        e["repetir"] = job["projeto"]
    espera = min(60, 2 ** e["falhas_seguidas"])
    _historico(f"- {_quando(job)} | {job['projeto']} | FALHA DO MODELO ({job.get('modelo')}): {_resumo(job)} — "
               f"refaz em {espera} min | {job['id']}")
    log(f"{job['id']}: falha do modelo {job.get('modelo')} ({_resumo(job)}) — refaz {job['projeto']} em {espera} min")
    if e["falhas_seguidas"] == 3:
        _avisar("As melhorias contínuas estão travadas: os modelos de IA estão falhando (sem crédito ou fora do ar). "
                "Sigo tentando sozinho, cada vez mais espaçado (até 1 vez por hora). Não precisa fazer nada.")
    _fim_de_rodada(e, c, espera)


# ─── multiagente (23/10): buscador -> backlog -> executor -> revisor ─────────────────────────────────────────────
def _chave(titulo):
    return re.sub(r"\W+", " ", str(titulo).lower()).strip()[:60]


def _nota(item):
    return int(item.get("impacto", 3)) * 2 - int(item.get("risco", 3))


def _backlog(c=None):
    """Itens ainda válidos (vencem em backlog_validade_h: o que o buscador viu pode já ter mudado)."""
    c = c or cfg()
    limite = time.time() - float(c["backlog_validade_h"]) * 3600
    return [i for i in _ler(BACKLOG, []) if float(i.get("ts", 0)) >= limite]


def _da_vez(e, projetos):
    agora = time.time()
    livres = [p for p in projetos if float(e["descanso"].get(p, 0)) <= agora] or projetos
    proj = livres[e["vez"] % len(livres)]
    e["vez"] += 1
    return proj


def _pegar_item(e, c, projetos):
    """Tira do backlog o item de melhor nota (impacto alto, risco baixo; empate = o mais antigo)."""
    agora = time.time()
    lst = _backlog(c)
    boas = [i for i in lst if i["projeto"] in projetos
            and (i.get("opus") or float(e["descanso"].get(i["projeto"], 0)) <= agora)]
    if not boas:
        _gravar(BACKLOG, lst)
        return None
    # 24/10: o que a auditoria final (Opus) mandou refazer passa na frente
    item = max(boas, key=lambda i: (bool(i.get("opus")), _nota(i), -float(i["ts"])))
    lst.remove(item)
    _gravar(BACKLOG, lst)
    return item


def _itens_da_resposta(texto):
    """Lista do bloco <<<BACKLOG ... BACKLOG>>> do buscador; None se ele não respondeu no formato."""
    # 24/10: o ÚLTIMO bloco (o Kiro com raciocínio às vezes repete o formato de exemplo antes)
    blocos = re.findall(r"<<<BACKLOG\s*(.*?)\s*BACKLOG>>>", str(texto or ""), re.S)
    if not blocos:
        return None
    bruto = re.sub(r"^```(?:json)?\s*|\s*```$", "", blocos[-1].strip())
    try:
        lst = json.loads(bruto)
    except ValueError:
        return None
    if not isinstance(lst, list):
        return None
    itens = []
    for i in lst:
        if not isinstance(i, dict) or not str(i.get("titulo") or "").strip():
            continue
        nota = {}
        for k in ("impacto", "risco"):
            try:
                nota[k] = min(5, max(1, int(i.get(k, 3))))
            except (TypeError, ValueError):
                nota[k] = 3
        itens.append({"titulo": str(i["titulo"]).strip()[:200], "evidencia": str(i.get("evidencia") or "")[:600],
                      "arquivos": [str(a)[:200] for a in (i.get("arquivos") or [])][:6] if isinstance(
                          i.get("arquivos"), list) else [], "como_conferir": str(i.get("como_conferir") or "")[:300],
                      **nota})
    return itens


def _segundo(c):
    """2º modelo da dupla (24/10, dona: "os 2 buscam, um fala com o outro e só faz se os 2 concordarem")."""
    return c.get("modelo_segundo") if c.get("dupla") else None


def _feitos_txt(e, n=40):
    """O que as melhorias já fizeram; o que foi desfeito (pela dona, pela revisão ou pelo motor) vai marcado pra não
    ser reproposto (23/10: repropôs em 2 min o que a dona tinha acabado de desfazer)."""
    import painel_ia
    linhas = []
    for f in e["feitos"][-n:]:
        j = painel_ia.ler(f.get("job") or "") or {}
        marca = " [DESFEITO — NÃO REPROPOR]" if j.get("desfeito_em") or f.get("status") == "REPROVADO" else ""
        linhas.append(f"- {f['quando'][:10]} [{f['projeto']}] {f['resumo'][:150]}{marca}")
    return "\n".join(linhas) or "- (nada ainda)"


def _texto_item(item):
    if not item:
        return "(sem item do backlog: rodada livre)"
    txt = (f"«{item['titulo']}» (impacto {item['impacto']}, risco {item['risco']})\nProva: {item['evidencia']}\n"
           f"Arquivos: {', '.join(item['arquivos']) or '?'}\nComo conferir: {item['como_conferir'] or '?'}")
    if item.get("criticas"):
        txt += (f"\nTENTATIVA {item.get('tentativa', 2)}: a(s) anterior(es) foram DESFEITAS porque a revisão reprovou:\n"
                + "\n".join(f"- {k}" for k in item["criticas"]) + "\nFaça de novo resolvendo essas críticas.")
    return txt


def _pedir_busca(e, c, proj, lado="A"):
    import painel_ia
    nome, pasta = painel_ia.PROJETOS[proj]
    no_backlog = "\n".join(f"- [{i['projeto']}] {i['titulo']}" for i in _backlog(c)) or "- (vazio)"
    feitos = _feitos_txt(e, 25)
    ctx = (f"LIÇÕES (siga sempre):\n{_licoes(int(c['licoes_por_papel']))}\n\nNÃO MEXER: {', '.join(_protegidos(c))}\n\n"
           f"JÁ NO BACKLOG:\n{_corta(no_backlog, 600)}\n\nJÁ FEITO:\n{_corta(feitos, 1000)}\n\n"
           f"MUDADOS NAS ÚLTIMAS 12 H:\n{_corta(_recentes(pasta), 700)}\n\nCONSERTOS RECENTES:\n{_consertos_recentes()}")
    job = _pedir("pergunta", PEDIDO_BUSCADOR.format(projeto=nome, pasta=pasta, prompt=c["prompt"]),
                 projeto=proj, contexto=ctx[:6000], origem=ORIGEM, modelo=_segundo(c) if lado == "B" else None,
                 voltas=c["voltas_leitura"], pensar=lado != "B" and bool(c.get("kiro_pensar")))
    e["papeis"][job["id"]] = {"papel": "buscador", "projeto": proj, "lado": lado}
    e["atual"] = job["id"]
    log(f"buscador {lado} em {proj}: {job['id']}")


def _pedir_voto(e, c, proj, lado, itens):
    """lado = quem vota (na lista que o OUTRO achou)."""
    import painel_ia
    nome, pasta = painel_ia.PROJETOS[proj]
    ctx = "\n\n".join(f"ITEM {n}. {_texto_item(i)}" for n, i in enumerate(itens, 1))
    ctx = _corta(ctx, 4200) + f"\n\nLIÇÕES (siga sempre):\n{_licoes(1500)}"
    job = _pedir("pergunta", PEDIDO_VOTO.format(projeto=nome, pasta=pasta), projeto=proj, contexto=ctx[:6000],
                 origem=ORIGEM, modelo=_segundo(c) if lado == "B" else None, voltas=c["voltas_leitura"],
                 pensar=lado != "B" and bool(c.get("kiro_pensar")))
    e["papeis"][job["id"]] = {"papel": "votante", "projeto": proj, "lado": lado}
    e["atual"] = job["id"]
    log(f"votante {lado} em {proj} conferindo {len(itens)} item(ns) do outro: {job['id']}")


def _votos_da_resposta(texto):
    """{n: (concordo, motivo)} do bloco <<<VOTOS ... VOTOS>>>; None se não veio no formato."""
    blocos = re.findall(r"<<<VOTOS\s*(.*?)\s*VOTOS>>>", str(texto or ""), re.S)  # 24/10: o último bloco
    if not blocos:
        return None
    try:
        lst = json.loads(re.sub(r"^```(?:json)?\s*|\s*```$", "", blocos[-1].strip()))
    except ValueError:
        return None
    if not isinstance(lst, list):
        return None
    votos = {}
    for v in lst:
        try:
            votos[int(v["n"])] = (v.get("concordo") is True, str(v.get("motivo") or "")[:200])
        except (TypeError, ValueError, KeyError):
            continue
    return votos


def _novos(e, c, itens, proj, jid, ja=()):
    """Itens que ainda não estão no backlog, nos feitos nem em `ja` (o que o outro lado achou)."""
    vistas = ({_chave(i["titulo"]) for i in _backlog(c)} | {_chave(f["resumo"]) for f in e["feitos"][-80:]}
              | {_chave(i["titulo"]) for i in ja})
    novos = []
    for i in itens:
        if _chave(i["titulo"]) in vistas:
            continue
        vistas.add(_chave(i["titulo"]))
        novos.append(dict(i, projeto=proj, ts=time.time(), achado=jid, criado=datetime.now().strftime("%Y-%m-%d %H:%M")))
    return novos


def _guardar_no_backlog(e, c, proj, novos, resumo, jid):
    lst = sorted(_backlog(c) + novos, key=lambda i: (-_nota(i), float(i["ts"])))[:int(c["backlog_max"])]
    _gravar(BACKLOG, lst)
    if not novos:  # nada novo que valha: o projeto descansa, a roda gasta o crédito onde tem o que fazer
        e["descanso"][proj] = time.time() + float(c["descanso_ok_h"]) * 3600
    _historico(f"- {datetime.now():%Y-%m-%d %H:%M} | {proj} | {resumo}"
               + (": " + "; ".join(i["titulo"][:60] for i in novos) if novos else "") + f" | {jid}")
    log(f"{jid}: {proj}: {resumo}; backlog com {len(lst)}")
    e["busca"] = None
    _fim_de_rodada(e, c, 0)


def _fechar_busca(e, c, jid):
    b = e["busca"]
    _guardar_no_backlog(e, c, b["projeto"], b["ok"],
                        f"BUSCA EM DUPLA: A achou {len(b['A'])}, B achou {len(b['B'] or [])}, as duas concordaram em "
                        f"{len(b['ok'])}" + (f" ({b['nota']})" if b.get("nota") else ""), jid)


def _fila_revisores(c):
    return [x for x in c.get("revisores") or ["B", "A"] if x != "B" or _segundo(c)] or ["A"]


def _pedir_revisao(e, c, ap, lado="A"):
    """Um revisor (só lê; conversa nova). A fila de revisores (config "revisores") anda em _terminou_papel."""
    import painel_ia
    nome, pasta = painel_ia.PROJETOS.get(ap["projeto"], painel_ia.PROJETOS["geral"])
    partes = []
    for d in painel_ia.mudancas(ap["id"]):
        backup = (ap.get("manifesto") or {}).get(d["arquivo"], {}).get("backup") or "(arquivo novo)"
        partes.append(f"### {d['arquivo']} (backup de antes: {backup})\n{d['diff']}")
    pedido = PEDIDO_REVISOR.format(projeto=nome, pasta=pasta, feito=_resumo(ap)[:200]) + (ADVERSARIO if lado == "C" else "")
    guarda = json.dumps({"bloqueados": ap.get("bloqueios") or [], "suspeitos": ap.get("suspeitos") or []},
                        ensure_ascii=False)[:600]
    # 24/10 (achado 25): o DIFF vem logo depois do item, com cota fixa; LIÇÕES e NÃO MEXER no fim (é ali que o
    # ctx[:6000] corta). Antes as [FIXA] passavam do limite e o revisor via só ~840 caracteres do diff
    nomes = [d["arquivo"] for d in painel_ia.mudancas(ap["id"])]
    ctx = (f"O QUE ERA PRA FAZER (item):\n{_corta(_texto_item(e.get('item_atual')), 900)}\n\n"
           f"ARQUIVOS MUDADOS ({len(nomes)}): {', '.join(nomes) or '(nenhum)'}\n\nDIFF:\n"
           f"{_corta(chr(10).join(partes) or '(nenhum arquivo mudou)', 2500)}\n\n"
           f"COMANDOS QUE A APLICAÇÃO RODOU:\n{_comandos(ap['id'], 1100) or '(nenhum)'}\n"
           f"COMANDOS DA PROPOSTA:\n{_comandos(ap.get('pai'), 400) or '(nenhum)'}\nGUARDA: {guarda}\n\n"
           f"NÃO MEXER: {', '.join(_protegidos(c))}\n\nLIÇÕES (siga sempre):\n{_licoes(900)}")
    job = _pedir("pergunta", pedido, projeto=ap["projeto"], contexto=ctx[:6000], origem=ORIGEM,
                 modelo=_segundo(c) if lado == "B" else None, voltas=c["voltas_leitura"],
                 pensar=lado != "B" and bool(c.get("kiro_pensar")))
    e["papeis"][job["id"]] = {"papel": "revisor", "aplicado": ap["id"], "lado": lado}
    e["atual"] = job["id"]
    if not e.get("revisao") or e["revisao"].get("aplicado") != ap["id"]:
        e["revisao"] = {"aplicado": ap["id"], "vereditos": {}, "fila": [x for x in _fila_revisores(c) if x != lado]}
    log(f"{ap['id']}: revisor {lado} conferindo -> {job['id']}")


def _pedir_critica(e, c, prop, lado):
    """Crítico do PLANO (24/10): lê a proposta antes de qualquer arquivo mudar. A fila anda em _terminou_papel."""
    import painel_ia
    nome, pasta = painel_ia.PROJETOS.get(prop["projeto"], painel_ia.PROJETOS["geral"])
    plano = re.sub(r"\n?STATUS:.*$", "", str(prop.get("resposta") or ""), flags=re.S | re.I).strip()
    ctx = (f"O QUE ERA PRA FAZER (item):\n{_corta(_texto_item(e.get('item_atual')), 900)}\n\n"
           f"PROPOSTA DO EXECUTOR (análise e plano):\n{_corta(plano[-3200:], 3200)}\n\n"
           f"NÃO MEXER: {', '.join(_protegidos(c))}\n\nLIÇÕES (siga sempre):\n{_licoes(1000)}")
    job = _pedir("pergunta", PEDIDO_CRITICO.format(projeto=nome, pasta=pasta) + (ADVERSARIO if lado == "C" else ""),
                 projeto=prop["projeto"], contexto=ctx[:6000], origem=ORIGEM,
                 modelo=_segundo(c) if lado == "B" else None, voltas=c["voltas_leitura"],
                 pensar=lado != "B" and bool(c.get("kiro_pensar")))
    e["papeis"][job["id"]] = {"papel": "critico", "proposta": prop["id"], "lado": lado}
    e["atual"] = job["id"]
    if not e.get("critica") or e["critica"].get("proposta") != prop["id"]:
        e["critica"] = {"proposta": prop["id"], "vereditos": {},
                        "fila": [x for x in c.get("critica_plano") or [] if (x != "B" or _segundo(c)) and x != lado]}
    log(f"{prop['id']}: crítico do plano {lado} -> {job['id']}")


def _aplicar_proposta(e, c, prop, nota=""):
    """Manda aplicar a proposta (depois dos críticos). True se disparou."""
    import ia_reserva
    import painel_ia
    try:
        novo = painel_ia.aplicar(prop["id"])
    except Exception as ex:  # noqa: BLE001
        log(f"{prop['id']}: não deu pra aplicar ({ex})")
        return False
    e["atual"] = novo["id"]
    e["critica"] = None
    if ia_reserva.eh_reserva(prop.get("modelo") or ""):
        e["pequenos"].append(novo["id"])
    log(f"{prop['id']}: aplicando sozinho -> {novo['id']}{' (' + nota + ')' if nota else ''}: {_resumo(prop)}")
    return True


def _aceitar(e, c, atual, nota=""):
    """Aplicação que passou por todas as redes: vai pro Telegram (com DESFAZER) e é vigiada na produção."""
    jid, st = atual["id"], atual.get("status_ia")
    rev = e.get("revisao") if (e.get("revisao") or {}).get("aplicado") == jid else {}
    try:  # 24/10: 3ª camada — toda aplicação aceita entra na fila da auditoria final (Opus), com os vereditos
        import auditoria_final
        auditoria_final.enfileirar(e, c, atual, nota, (rev or {}).get("vereditos") or {}, e.get("item_atual"))
    except Exception as ex:  # noqa: BLE001 — a auditoria nunca trava o motor
        log(f"{jid}: não entrou na fila da auditoria ({type(ex).__name__}: {ex})")
    e["revisao"] = None
    e["entregar"].append(jid)  # resultado (CONSERTEI/REVISAR) vai pro Telegram, com DESFAZER
    e["feitos"].append({"quando": atual.get("fim") or atual["criado"], "projeto": atual["projeto"],
                        "resumo": _resumo(atual), "job": jid, "status": st or atual.get("status")})
    if st == "CONSERTEI":
        _comecar_vigia(e, atual)
    _historico(f"- {_quando(atual)} | {atual['projeto']} | {st or atual.get('status')} | {_resumo(atual)}"
               + (f" | {nota[:200]}" if nota else "") + f" | {jid}")
    log(f"{jid}: aplicado ({st}){' — ' + nota[:120] if nota else ''}: {_resumo(atual)}")
    _fim_de_rodada(e, c)


def _reprovado(e, c, ap, lado, motivo, jid):
    """Uma das revisoras reprovou: desfaz; se ainda tem tentativa, refaz o mesmo item com a crítica (até as duas
    concordarem); senão vira lição."""
    import painel_ia
    quem = LADOS.get(lado, "o revisor")
    desfeito = _desfazer(ap, f"{quem} reprovou: {motivo}")
    cmds = _comandos(ap["id"], 600)
    if not ap.get("manifesto") and cmds:  # 24/10: rodou comandos que o desfazer não volta: a dona precisa saber
        _avisar(f"Uma melhoria automática em {painel_ia.PROJETOS.get(ap['projeto'], (ap['projeto'],))[0]} foi "
                f"reprovada na revisão ({motivo[:200]}). Ela não mudou arquivo, mas rodou comandos que o desfazer não "
                f"volta — confira se precisa voltar algo:\n{cmds}")
    item = e.get("item_atual")
    tent = int((item or {}).get("tentativa", 1))
    e["revisao"] = None
    if item and desfeito and tent < int(c["tentativas_max"]):
        e["refazer"] = dict(item, tentativa=tent + 1, criticas=(item.get("criticas") or []) + [f"{quem}: {motivo[:300]}"])
        _historico(f"- {_quando(ap)} | {ap['projeto']} | REPROVADO ({quem}) (tentativa {tent}) e DESFEITO: "
                   f"{motivo[:200]} — refaz com a crítica | {ap['id']} ({jid})")
        log(f"{ap['id']}: {quem} REPROVOU ({motivo[:120]}); desfeito; refaz (tentativa {tent + 1})")
        _fim_de_rodada(e, c, 0)
        return
    _nova_licao(f"A revisão ({quem}) reprovou «{_resumo(ap)[:150]}»: {motivo}", "revisor")
    e["feitos"].append({"quando": ap.get("fim") or ap["criado"], "projeto": ap["projeto"], "resumo": _resumo(ap),
                        "job": ap["id"], "status": "REPROVADO"})
    _historico(f"- {_quando(ap)} | {ap['projeto']} | REPROVADO ({quem})"
               + (f" na tentativa {tent} (desisti)" if item else "")
               + f" e {'DESFEITO' if desfeito else 'NÃO DESFEITO'}: {motivo[:200]} | {_resumo(ap)} | {ap['id']} ({jid})")
    log(f"{ap['id']}: {quem} REPROVOU ({motivo[:120]}); {'desfeito' if desfeito else 'NÃO desfeito'}; sem nova tentativa")
    if not desfeito and ap.get("manifesto"):
        _avisar(f"Uma melhoria automática em {painel_ia.PROJETOS.get(ap['projeto'], (ap['projeto'],))[0]} foi "
                f"reprovada na revisão ({motivo[:200]}) e NÃO consegui desfazer sozinho, porque outra sessão mexeu "
                f"no mesmo arquivo depois. Se precisar, desfaça no painel (aba IA, pedido {ap['id']}).")
    _fim_de_rodada(e, c)


def _veredito(atual):
    """(veredito, motivo) da resposta; APROVADO sem a seção ANÁLISE não vale (24/10: raciocínio obrigatório)."""
    texto = str(atual.get("resposta") or "")
    m = VEREDITO.findall(texto)
    if not m:
        return None, ""
    v, motivo = m[-1][0].upper().replace("Ú", "U"), " ".join(m[-1][1].split())
    if v == "APROVADO" and not ANALISE.search(texto):
        return None, "aprovou sem a ANÁLISE (não vale)"
    return v, motivo


def _item_da_proposta(e, prop):
    item = dict(e.get("item_atual") or {})
    item.setdefault("titulo", _resumo(prop)[:200])
    item.setdefault("evidencia", "")
    item.setdefault("arquivos", [])
    item.setdefault("impacto", 3)
    item.setdefault("risco", 3)
    item.setdefault("como_conferir", "")
    item.setdefault("projeto", prop["projeto"])
    return item


def _terminou_critica(e, c, atual, papel):
    """Fim de um crítico do plano. Devolve True se já disparou o próximo (outro crítico ou o aplicar)."""
    import ia_reserva
    import painel_ia
    prop = painel_ia.ler(papel["proposta"])
    lado = papel.get("lado", "A")
    if not prop:
        e["critica"] = None
        _fim_de_rodada(e, c)
        return False
    cr = e.get("critica") if (e.get("critica") or {}).get("proposta") == prop["id"] else {
        "proposta": prop["id"], "vereditos": {}, "fila": []}
    e["critica"] = cr
    v, motivo = _veredito(atual)
    if v is None and ia_reserva.falha_de_modelo(_texto(atual)) and atual.get("modelo"):
        ia_reserva.marcar(atual["modelo"], _texto(atual))
    cr["vereditos"][lado] = [v, motivo]
    quem = {"A": "o crítico principal (Kiro)", "B": "o crítico 2º modelo (Gemini)",
            "C": "o crítico adversário (Kiro)"}.get(lado, "o crítico")
    if v == "REPROVADO":  # nada foi aplicado: refaz o PLANO com a crítica (barato) ou desiste do item
        e["critica"] = None
        item = _item_da_proposta(e, prop)
        n = int(item.get("planos", 1))
        if n <= int(c["criticas_max"]):
            e["refazer"] = dict(item, planos=n + 1,
                                criticas=(item.get("criticas") or []) + [f"{quem} reprovou o plano: {motivo[:300]}"])
            _historico(f"- {_quando(atual)} | {prop['projeto']} | PLANO REPROVADO ({quem}), nada aplicado: "
                       f"{motivo[:200]} — refaz o plano | {prop['id']} ({atual['id']})")
            log(f"{prop['id']}: {quem} reprovou o plano ({motivo[:120]}); refaz o plano ({n + 1})")
            _fim_de_rodada(e, c, 0)
        else:
            _nova_licao(f"O crítico do plano reprovou «{_resumo(prop)[:150]}»: {motivo}", "crítico do plano")
            e["feitos"].append({"quando": _quando(atual), "projeto": prop["projeto"], "resumo": _resumo(prop),
                                "job": prop["id"], "status": "REPROVADO"})
            _historico(f"- {_quando(atual)} | {prop['projeto']} | PLANO REPROVADO ({quem}) {n}x, desisti do item: "
                       f"{motivo[:200]} | {prop['id']} ({atual['id']})")
            log(f"{prop['id']}: plano reprovado {n}x; desisti do item")
            _fim_de_rodada(e, c)
        return False
    if v == "DUVIDA":  # vira pergunta pra dona (APLICAR/NÃO no Telegram), como as que gastam dinheiro
        e["critica"] = None
        e["entregar"].append(prop["id"])
        e["motivos"][prop["id"]] = f"{quem} ficou em dúvida: {motivo[:200]}"
        _historico(f"- {_quando(atual)} | {prop['projeto']} | PERGUNTA pra dona ({quem} em dúvida no plano) | "
                   f"{_resumo(prop)} | {prop['id']}")
        _fim_de_rodada(e, c)
        return False
    if cr.get("fila"):
        prox = cr["fila"].pop(0)
        _pedir_critica(e, c, prop, prox)
        return True
    aprov = [k for k, (vv, _mo) in cr["vereditos"].items() if vv == "APROVADO"]
    if not aprov:  # 24/10 (achado 6): ninguém respondeu no formato não é aprovação
        if "C" not in cr["vereditos"] and not cr.get("c_chamado"):
            cr["c_chamado"] = True
            log(f"{prop['id']}: nenhum crítico respondeu no formato; chamo o crítico C (Kiro adversário)")
            try:
                _pedir_critica(e, c, prop, "C")
                return True
            except Exception as ex:  # noqa: BLE001
                log(f"{prop['id']}: crítico C não começou ({type(ex).__name__}: {ex})")
        e["critica"] = None
        e["entregar"].append(prop["id"])
        e["motivos"][prop["id"]] = "nenhum crítico do plano respondeu no formato"
        _historico(f"- {_quando(atual)} | {prop['projeto']} | PERGUNTA pra dona (nenhum crítico respondeu no formato) | "
                   f"{_resumo(prop)} | {prop['id']}")
        _fim_de_rodada(e, c)
        return False
    nota = f"plano aprovado por {len(aprov)} de {len(cr['vereditos'])} crítico(s)"
    if _aplicar_proposta(e, c, prop, nota):
        return True
    _fim_de_rodada(e, c)
    return False


def _terminou_papel(e, c, atual, papel):
    """Fim de um pedido só de leitura (buscador, votante, crítico, revisor ou auditor reserva). Devolve True se já
    disparou o próximo."""
    import ia_reserva
    import painel_ia
    jid, lado = atual["id"], papel.get("lado", "A")
    e["atual"] = None
    e["papeis"].pop(jid, None)
    texto = _texto(atual)
    proj = papel.get("projeto")
    if papel["papel"] == "auditor_reserva":  # 24/10: só avisa a dona; o Opus reaudita quando voltar
        try:
            import auditoria_final
            auditoria_final.terminou_reserva(e, c, atual, papel)
        except Exception as ex:  # noqa: BLE001
            log(f"{jid}: auditor reserva falhou ({type(ex).__name__}: {ex})")
        # 24/10 (achado 7): não zera a pausa/espera do motor (a reserva roda até com as melhorias esperando)
        _fim_de_rodada(e, c, max(0.0, (float(e.get("proxima_em") or 0) - time.time()) / 60))
        return False
    if papel["papel"] == "critico":
        return _terminou_critica(e, c, atual, papel)
    if papel["papel"] == "buscador" and lado == "A":
        itens = _itens_da_resposta(atual.get("resposta"))
        if itens is None:
            if ia_reserva.falha_de_modelo(texto):
                _falhou_modelo(e, c, atual)
                return False
            if atual.get("status") in ("erro", "parado"):
                log(f"{jid}: buscador em {proj} parou ({_resumo(atual)})")
                _fim_de_rodada(e, c)
                return False
            e["livre"] = proj  # não veio no formato: a próxima rodada deste projeto é a do jeito antigo
            log(f"{jid}: buscador não devolveu o backlog no formato; próxima rodada em {proj} sem buscador")
            _fim_de_rodada(e, c, 0)
            return False
        e["falhas_seguidas"] = 0
        novos = _novos(e, c, itens, proj, jid)
        if not _segundo(c):
            _guardar_no_backlog(e, c, proj, novos, f"BUSCADOR: {len(novos)} item(ns) novo(s)", jid)
            return False
        e["busca"] = {"projeto": proj, "A": novos, "B": None, "ok": []}
        _pedir_busca(e, c, proj, "B")
        return True
    b = e.get("busca")
    if papel["papel"] in ("buscador", "votante") and (not b or b.get("projeto") != proj):
        log(f"{jid}: {papel['papel']} {lado} sem busca em andamento; ignorado")
        _fim_de_rodada(e, c, 0)
        return False
    if papel["papel"] == "buscador":  # lado B
        itens = _itens_da_resposta(atual.get("resposta"))
        if itens is None:
            b["nota"] = "o 2º modelo não respondeu"
            log(f"{jid}: buscador B não respondeu no formato ({_resumo(atual)})")
        b["B"] = _novos(e, c, itens or [], proj, jid, ja=b["A"])
        if b["A"]:
            _pedir_voto(e, c, proj, "B", b["A"])
            return True
        if b["B"]:
            _pedir_voto(e, c, proj, "A", b["B"])
            return True
        _fechar_busca(e, c, jid)
        return False
    if papel["papel"] == "votante":
        votos = _votos_da_resposta(atual.get("resposta"))
        lista = b["A"] if lado in ("B", "C") else b["B"]
        if votos is None and lado == "B" and "C" in (c.get("revisores") or []) and not b.get("c_votou"):
            b["c_votou"] = True  # 24/10: o Gemini não votou: o Kiro adversário (pensando) vota no lugar dele
            log(f"{jid}: votante B não respondeu; o votante C (Kiro adversário) vota no lugar")
            _pedir_voto(e, c, proj, "C", b["A"])
            return True
        if votos is None and lado in ("B", "C"):  # ninguém do outro lado votou: vale o principal sozinho
            b["ok"] += lista
            b["nota"] = "o 2º voto não veio; entrou o que o principal achou"
            log(f"{jid}: votante {lado} não respondeu; itens do A entram sem voto")
        else:
            for n, i in enumerate(lista, 1):
                concordo, motivo = (votos or {}).get(n, (False, "sem voto"))
                if concordo:
                    b["ok"].append(i)
                else:
                    log(f"{jid}: {lado} discordou de «{i['titulo'][:60]}»: {motivo[:100]}")
        if lado in ("B", "C") and b["B"]:
            _pedir_voto(e, c, proj, "A", b["B"])
            return True
        _fechar_busca(e, c, jid)
        return False
    # revisor
    ap = painel_ia.ler(papel["aplicado"])
    if not ap:
        log(f"{jid}: a aplicação {papel['aplicado']} sumiu; nada a revisar")
        e["revisao"] = None
        _fim_de_rodada(e, c)
        return False
    rev = e.get("revisao") if (e.get("revisao") or {}).get("aplicado") == ap["id"] else {
        "aplicado": ap["id"], "vereditos": {}, "fila": []}
    e["revisao"] = rev
    veredito, motivo = _veredito(atual)
    if veredito is None and ia_reserva.falha_de_modelo(texto) and atual.get("modelo"):
        ia_reserva.marcar(atual["modelo"], texto)
    rev["vereditos"][lado] = [veredito, motivo]
    if veredito == "REPROVADO":
        _reprovado(e, c, ap, lado, motivo, jid)
        return False
    if rev.get("fila"):  # o próximo revisor da fila (conversa nova)
        _pedir_revisao(e, c, ap, rev["fila"].pop(0))
        return True
    vs = rev["vereditos"]
    duvidas = [f"{LADOS.get(l, l)}: {mo}" for l, (v, mo) in vs.items() if v == "DUVIDA"]
    aprov = [l for l, (v, _mo) in vs.items() if v == "APROVADO"]
    if duvidas:  # fica aplicada e a dona decide no Telegram (DESFAZER)
        e["duvidas"][ap["id"]] = "; ".join(duvidas)[:300]
        e["duvidas"] = dict(list(e["duvidas"].items())[-40:])
        _aceitar(e, c, ap, "revisão em dúvida: " + "; ".join(duvidas))
    elif aprov:
        _aceitar(e, c, ap, f"{len(aprov)} de {len(vs)} revisor(es) aprovaram"
                 + ("" if len(aprov) == len(vs) else " (os outros não responderam no formato)"))
    else:  # 24/10 (achado 6): sem nenhum veredito válido vira DÚVIDA (P0 na auditoria e 🤔 pra dona)
        e["duvidas"][ap["id"]] = "nenhum revisor respondeu no formato"
        e["duvidas"] = dict(list(e["duvidas"].items())[-40:])
        _aceitar(e, c, ap, "revisão em dúvida: nenhum revisor respondeu no formato")
    return False


def _terminou(e, c, atual):
    """Decide o que fazer com o pedido que acabou de terminar. Devolve True se já disparou o próximo (aplicar)."""
    import ia_reserva
    import painel_ia
    jid, tipo, st = atual["id"], atual["tipo"], atual.get("status_ia")
    e["atual"] = None
    texto = _texto(atual)
    if not st and ia_reserva.falha_de_modelo(texto):
        if tipo == "aplicar":
            _desfazer(atual, "o modelo caiu no meio da aplicação")
        _falhou_modelo(e, c, atual)
        return False
    e["falhas_seguidas"] = 0
    reserva = ia_reserva.eh_reserva(atual.get("modelo") or "")
    if tipo == "propor" and st == "PROPOSTA":
        e["ok_seguidos"][atual["projeto"]] = 0
        tocados = [n for n in _protegidos(c) if n.lower() in texto.lower()]
        motivo = ("gasta dinheiro ou crédito pago" if PERGUNTA.search(texto) else
                  f"mexe em parte sensível do sistema ({', '.join(tocados[:3])})" if tocados else "")
        if motivo:
            e["entregar"].append(jid)
            e["motivos"][jid] = motivo
            log(f"{jid}: proposta pra dona ({motivo}): {_resumo(atual)}")
            _historico(f"- {_quando(atual)} | {atual['projeto']} | PERGUNTA pra dona ({motivo}) | {_resumo(atual)} | {jid}")
        elif reserva and not c.get("reserva_aplica_pequeno"):
            e["ideias"].append({"quando": _quando(atual), "projeto": atual["projeto"], "resumo": _resumo(atual), "job": jid})
            log(f"{jid}: ideia anotada (IA reserva, aplica quando o principal voltar): {_resumo(atual)}")
            _historico(f"- {_quando(atual)} | {atual['projeto']} | IDEIA (IA reserva; confere quando o principal voltar) "
                       f"| {_resumo(atual)} | {jid}")
        else:
            fila = [x for x in c.get("critica_plano") or [] if x != "B" or _segundo(c)] if c.get("multiagente") else []
            try:
                if fila:  # 24/10: críticos do PLANO antes de qualquer arquivo mudar (barrar aqui não precisa desfazer)
                    e["critica"] = None
                    _pedir_critica(e, c, atual, fila[0])
                    _gravar(ESTADO, e)
                    return True
            except Exception as ex:  # noqa: BLE001 — sem crítico, aplica como antes
                log(f"{jid}: crítico do plano não começou ({type(ex).__name__}: {ex})")
            if _aplicar_proposta(e, c, atual):
                _gravar(ESTADO, e)
                return True
        _fim_de_rodada(e, c, c["pausa_reserva_min"] if reserva and not c.get("reserva_aplica_pequeno") else None)
        return False
    if tipo == "aplicar":
        ruins = _quebrados(atual) if st == "CONSERTEI" else []
        pequeno_estourou = None
        if st == "CONSERTEI" and jid in e["pequenos"]:
            n_arq, n_lin = _tamanho(jid)
            if n_arq > int(c["pequeno_max_arquivos"]) or n_lin > int(c["pequeno_max_linhas"]):
                pequeno_estourou = f"{n_arq} arquivo(s), {n_lin} linhas"
        if atual.get("status") in ("erro", "parado") or ruins or pequeno_estourou:
            motivo, simples = ((f"o código ficou quebrado ({'; '.join(ruins)[:200]})", "o código ficou com erro")
                               if ruins else
                               (f"a IA reserva mudou mais que um conserto pequeno ({pequeno_estourou})",
                                "a IA reserva mexeu mais do que o combinado pra um conserto pequeno")
                               if pequeno_estourou else ("a aplicação parou no meio", "ela parou no meio"))
            desfeito = _desfazer(atual, motivo)
            if pequeno_estourou:
                e["ideias"].append({"quando": _quando(atual), "projeto": atual["projeto"], "resumo": _resumo(atual),
                                    "job": jid})
            situacao = ("DESFEITO sozinho" if desfeito else "NÃO DESFEITO sozinho" if atual.get("manifesto")
                        else "nada a desfazer (nenhum arquivo tinha mudado)")
            _historico(f"- {_quando(atual)} | {atual['projeto']} | {situacao}: {motivo} | {_resumo(atual)} | {jid}")
            cmds = "" if atual.get("manifesto") else _comandos(jid, 600)
            if cmds:  # 24/10 (achado 28): sem arquivo mudado, mas rodou comandos que o desfazer não volta
                _avisar(f"Uma melhoria automática em {painel_ia.PROJETOS.get(atual['projeto'], (atual['projeto'],))[0]} "
                        f"parou ({simples}). Ela não mudou arquivo, mas rodou comandos que o desfazer não volta — "
                        f"confira se precisa voltar algo:\n{cmds}")
            if atual.get("manifesto") or cmds:
                try:  # entra como P0 na auditoria final
                    import auditoria_final
                    auditoria_final.enfileirar(e, c, atual, f"parou no meio: {motivo}"[:200])
                except Exception as ex:  # noqa: BLE001
                    log(f"{jid}: não entrou na auditoria ({type(ex).__name__}: {ex})")
            if atual.get("manifesto"):
                _avisar(f"Uma melhoria automática em {painel_ia.PROJETOS.get(atual['projeto'], (atual['projeto'],))[0]} "
                        + (f"foi desfeita sozinha porque {simples}. Tudo voltou como estava." if desfeito else
                           f"deu problema ({simples}) e NÃO consegui desfazer sozinho, porque outra pessoa ou sessão "
                           f"mexeu no mesmo arquivo depois. Se precisar, desfaça no painel (aba IA, pedido {jid})."))
        else:
            if jid in e["pequenos"]:
                e["pequenos"].remove(jid)
            # 24/10: revisão obrigatória pra TODA aplicação terminada (antes, sem arquivo mudado ou sem CONSERTEI
            # passava direto: o pip e a rede rodada à mão de 24/10 foram aceitos assim)
            if c.get("multiagente") and (c.get("revisao_obrigatoria") or (st == "CONSERTEI" and atual.get("manifesto"))):
                try:  # passou nas redes automáticas: agora os revisores (conversa nova, só leem) conferem
                    e["revisao"] = None
                    _pedir_revisao(e, c, atual, _fila_revisores(c)[0])  # Gemini, Kiro adversário, Kiro do checklist
                    _gravar(ESTADO, e)
                    return True
                except Exception as ex:  # noqa: BLE001 — sem revisor, segue como antes
                    log(f"{jid}: revisor não começou ({type(ex).__name__}: {ex})")
            _aceitar(e, c, atual)
            return False
        if jid in e["pequenos"]:
            e["pequenos"].remove(jid)
        _fim_de_rodada(e, c)
        return False
    # proposta que voltou OK (nada a fazer), REVISAR ou erro do agente que não foi do modelo
    if not st and atual.get("status") in ("erro", "parado"):  # 23/10: "passou de 30 min" não é melhoria feita
        e["falhas"].append({"quando": _quando(atual), "projeto": atual["projeto"], "modelo": atual.get("modelo"),
                            "erro": _resumo(atual), "job": jid})
        # 23/10: a reserva estourou 30 min e depois as 40 voltas, seguidas — espaça (dobra) pra não gastar cota à toa
        e["erros_agente_seguidos"] = int(e.get("erros_agente_seguidos", 0)) + 1
        base = float(c["pausa_reserva_min"] if reserva and not c.get("reserva_aplica_pequeno") else c["pausa_min"])
        pausa = min(480 if reserva else 60, base * 2 ** (e["erros_agente_seguidos"] - 1))
        e["espera_reserva"] = bool(reserva)
        _historico(f"- {_quando(atual)} | {atual['projeto']} | ERRO DO AGENTE ({atual.get('modelo')}): {_resumo(atual)} "
                   f"— próxima em {pausa:.0f} min | {jid}")
        log(f"{jid}: erro do agente: {_resumo(atual)} (próxima em {pausa:.0f} min)")
        _fim_de_rodada(e, c, pausa)
        return False
    e["erros_agente_seguidos"], e["espera_reserva"] = 0, False
    if st == "OK":
        n = e["ok_seguidos"].get(atual["projeto"], 0) + 1
        e["ok_seguidos"][atual["projeto"]] = n
        if n >= 2:  # 2 "nada a fazer" seguidos: o projeto descansa e a roda gasta o crédito onde tem o que fazer
            e["descanso"][atual["projeto"]] = time.time() + float(c["descanso_ok_h"]) * 3600
            e["ok_seguidos"][atual["projeto"]] = 0
    e["feitos"].append({"quando": atual.get("fim") or atual["criado"], "projeto": atual["projeto"],
                        "resumo": _resumo(atual), "job": jid, "status": st or atual.get("status")})
    if st == "REVISAR":
        e["entregar"].append(jid)
    _historico(f"- {_quando(atual)} | {atual['projeto']} | {st or atual.get('status')} | {_resumo(atual)} | {jid}")
    log(f"{jid}: {st or atual.get('status')}: {_resumo(atual)}")
    _fim_de_rodada(e, c)
    return False


def _sem_memoria(e, ram):
    """Parado por falta de memória há mais de 2 h: 1 aviso por dia (a falta de memória também derruba a produção)."""
    if not e.get("sem_memoria_desde"):
        e["sem_memoria_desde"] = time.time()
        return
    hoje = datetime.now().strftime("%Y-%m-%d")
    if time.time() - e["sem_memoria_desde"] < 2 * 3600 or e.get("memoria_avisada") == hoje:
        return
    e["memoria_avisada"] = hoje
    _avisar(f"As melhorias contínuas estão paradas há mais de 2 horas porque o computador está sem memória livre "
            f"(sobram {str(round(ram, 1)).replace('.', ',')} GB). Isso também pode travar a produção. O que costuma ajudar: fechar janelas do VS Code "
            f"e sessões do Claude que não estão em uso. Eu volto sozinho quando a memória liberar.")


def _por_que_espera(c):
    import painel_ia
    motivos = []
    if [j for j in painel_ia.todos() if j.get("status") in ("fila", "rodando")]:
        motivos.append("a IA do painel está ocupada com outro pedido")
    if painel_ia._travas_ocupadas():
        motivos.append("um vigia está consertando algo")
    ram = _ram_gb()
    if ram < float(c["ram_min_gb"]):
        motivos.append(f"o computador está sem memória livre ({str(round(ram, 1)).replace('.', ',')} GB; preciso de {str(c['ram_min_gb']).replace('.', ',')})")
    return "; ".join(motivos) or "a próxima rodada já vai começar"


def _aprovadas_pela_dona(e):
    """Pergunta que a dona aprovou no Telegram (APLICAR): o atendente aplica sem passar por aqui. Quando terminar, entra
    no histórico e passa pelas mesmas redes: .py/.json quebrado = desfaz; certo = vigiado na produção."""
    import painel_ia
    if not e["motivos"] or time.time() - float(e.get("aprovadas_ultimo", 0)) < 120:
        return False
    e["aprovadas_ultimo"] = time.time()
    mudou = False
    for j in painel_ia.todos():
        if (j.get("tipo") != "aplicar" or j.get("pai") not in e["motivos"] or j["id"] in e["registrados"]
                or j.get("status") in ("fila", "rodando")):
            continue
        e["registrados"].append(j["id"])
        mudou = True
        st = j.get("status_ia")
        ruins = _quebrados(j) if st == "CONSERTEI" else []
        if ruins or (j.get("status") in ("erro", "parado") and j.get("manifesto")):
            motivo = (f"o código ficou quebrado ({'; '.join(ruins)[:200]})" if ruins else "a aplicação parou no meio")
            desfeito = _desfazer(j, motivo)
            _historico(f"- {_quando(j)} | {j['projeto']} | APROVADA PELA DONA, mas {'DESFEITA' if desfeito else 'NÃO DESFEITA'}"
                       f" sozinha: {motivo} | {_resumo(j)} | {j['id']}")
            _avisar(f"A melhoria que você aprovou em {painel_ia.PROJETOS.get(j['projeto'], (j['projeto'],))[0]} "
                    + ("deu erro e foi desfeita sozinha. Tudo voltou como estava." if desfeito else
                       "deu erro e NÃO consegui desfazer sozinho (o arquivo mudou depois). Se precisar, desfaça no "
                       f"painel (aba IA, pedido {j['id']})."))
            continue
        e["feitos"].append({"quando": j.get("fim") or j["criado"], "projeto": j["projeto"], "resumo": _resumo(j),
                            "job": j["id"], "status": st or j.get("status")})
        _historico(f"- {_quando(j)} | {j['projeto']} | APROVADA PELA DONA -> {st or j.get('status')} | {_resumo(j)} | {j['id']}")
        if st == "CONSERTEI":
            _comecar_vigia(e, j)
        try:  # 24/10: também passa pela auditoria final (que nunca desfaz sozinha o que a dona aprovou)
            import auditoria_final
            auditoria_final.enfileirar(e, cfg(), j, "aprovada pela dona", {}, None, dona=True)
        except Exception as ex:  # noqa: BLE001
            log(f"{j['id']}: não entrou na fila da auditoria ({type(ex).__name__}: {ex})")
    e["registrados"] = e["registrados"][-200:]
    return mudou


def _avisar_modo(e, c, modo):
    if modo == e.get("modo_avisado"):
        return
    anterior, e["modo_avisado"] = e.get("modo_avisado"), modo
    if modo == "reserva" and c.get("reserva_aplica_pequeno"):
        _avisar("As melhorias contínuas estão no MODO RESERVA: a IA principal (Kiro) ficou sem crédito e deve voltar só "
                "na virada do mês (dia 1). Até lá uma IA mais simples continua, mas só faz sozinha consertos bem "
                f"pequenos (até {c['pequeno_max_linhas']} linhas); o que passar disso eu desfaço e anoto pra depois.")
    elif modo == "reserva":
        _avisar("As melhorias contínuas estão no MODO RESERVA: a IA principal (Kiro) ficou sem crédito e deve voltar só "
                "na virada do mês (dia 1). Nesse modo uma IA mais simples procura melhorias, mas eu só ANOTO as ideias e "
                "não mudo nada sozinho; quando a principal voltar, confiro e aplico as boas. Não precisa fazer nada. "
                "Se quiser que a reserva já faça consertos bem pequenos sozinha (com desfazer automático), mande "
                "\"melhorias reserva sim\".")
    elif anterior == "reserva":
        _avisar(f"A IA principal voltou: as melhorias contínuas voltaram a aplicar sozinhas. "
                f"Tenho {len(e['ideias'])} ideia(s) anotada(s) no modo reserva pra conferir primeiro.")


def passo():
    """Uma volta do motor: acompanha o pedido atual e, livre, dispara o próximo."""
    global _ATUAL
    import painel_ia
    c, e = cfg(), _estado()
    _ATUAL = (c, e)
    try:  # 24/10: avisa (1x por dia) se tem cota do Opus 5.5 quase vencendo
        import opus55
        opus55.aviso_quase_vencendo(c, e, _avisar)
    except Exception as ex:  # noqa: BLE001
        log(f"aviso do Opus 5.5 falhou ({type(ex).__name__}: {ex})")
    try:
        vigiou = _vigiar_producao(e)
    except Exception as ex:  # noqa: BLE001 — a vigia da produção nunca para o motor
        vigiou = False
        log(f"vigia da produção falhou ({type(ex).__name__}: {ex})")
    try:
        vigiou = _aprovadas_pela_dona(e) or vigiou
    except Exception as ex:  # noqa: BLE001
        log(f"registro das aprovadas pela dona falhou ({type(ex).__name__}: {ex})")
    try:  # 24/10: 3ª camada (auditoria final pelo Opus) — só lê arquivos e dispara processo; nunca espera o Opus
        import auditoria_final
        auditoria_final.ciclo(e, c)
        _gravar(ESTADO, e)  # 24/10 (achado 13): o lote disparado não some se o resto do passo cair
        vigiou = True
    except Exception as ex:  # noqa: BLE001 — a auditoria nunca para o motor
        log(f"auditoria final falhou ({type(ex).__name__}: {ex})")
    atual = painel_ia.ler(e["atual"]) if e.get("atual") else None
    if atual and atual.get("status") in ("fila", "rodando"):
        if vigiou:
            _gravar(ESTADO, e)
        return e
    if atual and atual["id"] in e["papeis"]:
        if _terminou_papel(e, c, atual, e["papeis"][atual["id"]]):
            _gravar(ESTADO, e)
            return e
    elif atual and _terminou(e, c, atual):
        return e
    if (c.get("ligado") and time.time() < e.get("proxima_em", 0) and e.get("espera_reserva")
            and time.time() - float(e.get("modo_teste", 0)) > 600):
        # a espera longa foi por erro da IA reserva: se a principal voltou, não espera mais (testa a cada 10 min)
        e["modo_teste"] = time.time()
        if _modo()[0] == "principal":
            e.update(proxima_em=0, erros_agente_seguidos=0, espera_reserva=False)
            log("a IA principal voltou: cancelei a espera longa dos erros da reserva")
    if not c.get("ligado") or time.time() < e.get("proxima_em", 0):
        _gravar(ESTADO, e)
        return e
    ocupado = [j for j in painel_ia.todos() if j.get("status") in ("fila", "rodando")]
    ram = _ram_gb()
    if ram < float(c["ram_min_gb"]):
        _sem_memoria(e, ram)
    else:
        e["sem_memoria_desde"] = None
    if ocupado or painel_ia._travas_ocupadas() or ram < float(c["ram_min_gb"]):
        _gravar(ESTADO, e)  # a dona (ou um vigia) está usando a IA, ou o PC está sem memória: espera
        return e
    modo, _principal = _modo()
    _avisar_modo(e, c, modo)
    projetos = [p for p in c["projetos"] if p in painel_ia.PROJETOS] or ["geral"]
    ideia_txt, ideia, item = "", None, None
    if e.get("repetir") in projetos:
        proj = e["repetir"]
        if (e.get("item_atual") or {}).get("projeto") == proj:
            item = e["item_atual"]  # a rodada caiu por erro do modelo: refaz o mesmo item
    elif modo == "principal" and e["ideias"]:
        ideia = e["ideias"].pop(0)
        proj = ideia["projeto"] if ideia["projeto"] in projetos else projetos[0]
        ideia_txt = (f"\nIDEIA ANOTADA pela IA reserva em {ideia['quando']}: «{ideia['resumo']}» (proposta completa no "
                     f"painel, pedido {ideia['job']}). Confira se ainda vale e se ainda acontece; se valer, proponha do "
                     f"seu jeito; se não, STATUS: OK.\n")
    elif c.get("multiagente") and (e.get("refazer") or {}).get("projeto") in projetos:
        item, e["refazer"] = e["refazer"], None  # reprovado na revisão: refaz com a crítica até as duas concordarem
        proj = item["projeto"]
    elif c.get("multiagente") and e.get("livre") in projetos:
        proj, e["livre"] = e["livre"], None  # o buscador não respondeu no formato: rodada do jeito antigo
    elif c.get("multiagente"):
        item = _pegar_item(e, c, projetos)
        if item:
            proj = item["projeto"]
        else:  # backlog vazio: o buscador (só lê) procura antes de alguém mexer
            _pedir_busca(e, c, _da_vez(e, projetos))
            e["repetir"] = None
            _gravar(ESTADO, e)
            return e
    else:
        proj = _da_vez(e, projetos)
    e["repetir"] = None
    e["item_atual"] = item
    if item:
        ideia_txt = (f"ITEM DO BACKLOG (achado em {item.get('criado', '?')}; faça ESTE):\n{_corta(_texto_item(item), 1500)}\n"
                     "Confira se ainda acontece. Se sim, proponha este item (pode ajustar o jeito). Se não acontece "
                     "mais ou não vale, responda STATUS: OK.")
    nome, pasta = painel_ia.PROJETOS[proj]
    pedido = PEDIDO.format(projeto=nome, pasta=pasta, prompt=c["prompt"])
    # 24/10: o variável vai no CONTEXTO (o pedido é cortado em 4.000 e as lições empurravam o PROIBIDO pra fora)
    ctx = (f"{ideia_txt.strip() or '(sem item: rodada livre)'}\n\n"
           f"LIÇÕES (siga SEMPRE, valem mais que o resto):\n{_licoes(int(c['licoes_por_papel']))}\n\n"
           f"NÃO MEXA (outra sessão está conferindo, ou são o motor/Telegram): {', '.join(_protegidos(c)) or '(nenhum)'}\n\n"
           f"MUDADOS NAS ÚLTIMAS 12 H (outras sessões, vigias e a dona — não reconserte):\n{_corta(_recentes(pasta), 600)}\n\n"
           f"CONSERTOS RECENTES DA IA DO PAINEL E DOS VIGIAS:\n{_corta(_consertos_recentes(), 400)}\n\n"
           f"JÁ FEITO PELAS MELHORIAS (não repetir):\n")
    ctx += _corta(_feitos_txt(e, 40), max(300, 5950 - len(ctx)))
    job = _pedir("propor", pedido, projeto=proj, contexto=ctx[:6000], origem=ORIGEM,
                 pensar=bool(c.get("kiro_pensar")))
    e["atual"] = job["id"]
    log(f"nova rodada em {proj} (modo {modo}{', conferindo ideia ' + ideia['job'] if ideia else ''}"
        f"{', item: ' + item['titulo'][:80] if item else ''}): {job['id']}")
    _gravar(ESTADO, e)
    return e


def para_entregar():
    """O bots_conversa pega aqui o que mandar no Telegram (e esvazia a lista)."""
    e = _estado()
    lista, e["entregar"] = e["entregar"], []
    if lista:
        _gravar(ESTADO, e)
    return lista


def eh_melhoria(job):
    """O pedido nasceu das melhorias contínuas (a proposta, ou a aplicação que a dona aprovou pelo Telegram)?"""
    import painel_ia
    if not job:
        return False
    return job.get("origem") == ORIGEM or (painel_ia.ler(job.get("pai") or "") or {}).get("origem") == ORIGEM


def texto_entrega(job):
    """Mensagem curta e simples pro Telegram (o bots_conversa manda; responder APLICAR/NÃO/DESFAZER continua valendo).
    23/10: antes ia a resposta inteira do agente (até 3.500 caracteres técnicos)."""
    import painel_ia
    try:  # 24/10: a auditoria final quer que a dona decida esta aplicação
        import auditoria_final
        t = auditoria_final.texto_dona(job)
        if t:
            return t
    except Exception:  # noqa: BLE001
        pass
    proj = painel_ia.PROJETOS.get(job.get("projeto"), (job.get("projeto"),))[0]
    bruto = re.sub(r"\n?STATUS:.*$", "", str(job.get("resposta") or job.get("detalhe") or ""), flags=re.S | re.I).strip()
    simples = None
    try:
        import avisos
        simples = avisos.simplificar(bruto[-6000:], RESUMO_TG) if bruto else None
    except Exception:  # noqa: BLE001
        pass
    simples = simples or _resumo(job)
    st = job.get("status_ia")
    if job.get("tipo") == "propor" and st == "PROPOSTA":
        motivo = _estado()["motivos"].get(job["id"], "")
        return (f"❓ Melhoria esperando sua decisão — {proj}\n{simples}\n"
                + (f"Por que pergunto: {motivo}.\n" if motivo else "")
                + "➡️ Responda esta mensagem com APLICAR pra eu fazer, ou NÃO pra descartar.")
    if job.get("tipo") == "aplicar" and st == "CONSERTEI":
        duvida = _estado()["duvidas"].get(job["id"])
        if duvida:  # o revisor não teve certeza: a dona decide
            return (f"🤔 Melhoria feita, mas o revisor ficou em dúvida — {proj}\n{simples}\nDúvida: {duvida}\n"
                    "➡️ Se achar melhor voltar como estava, responda esta mensagem com DESFAZER.")
        return f"✅ Melhoria feita — {proj}\n{simples}\nSe não gostou, responda esta mensagem com DESFAZER."
    if st == "REVISAR":
        return (f"⚠️ Melhoria precisa de você — {proj}\n{simples}"
                + ("\nSe quiser voltar como estava, responda esta mensagem com DESFAZER." if job.get("tipo") == "aplicar"
                   else ""))
    return f"ℹ️ Melhoria — {proj}: {simples}"


def comando(texto):
    """Texto do bot de produção que começa com "melhoria(s)". Devolve a resposta pra dona."""
    t = texto.strip()
    m = re.match(r"^\s*melhorias?\s*(.*)$", t, re.I | re.S)
    resto = (m.group(1) if m else "").strip()
    if re.match(r"^(ligar|liga|come[cç]a|iniciar|on)\b", resto, re.I):
        _salvar_cfg(ligado=True)
        return "Melhorias contínuas LIGADAS. Vou fazendo uma por vez e te mando cada resultado aqui."
    if re.match(r"^(parar|para|desligar|desliga|pausa|off)\b", resto, re.I):
        _salvar_cfg(ligado=False)
        return "Melhorias contínuas PARADAS. A que estiver no meio termina; nenhuma nova começa."
    rm = re.match(r"^reserva\s*(sim|s|n[aã]o|nao|n)?\b", resto, re.I)
    if rm:
        if not rm.group(1):
            return ("Reserva " + ("APLICA" if cfg().get("reserva_aplica_pequeno") else "só ANOTA")
                    + " consertos. Mande \"melhorias reserva sim\" ou \"melhorias reserva não\".")
        sim = rm.group(1).lower().startswith("s")
        _salvar_cfg(reserva_aplica_pequeno=sim)
        return ("Combinado: quando a IA principal estiver sem crédito, a reserva faz sozinha só consertos pequenos (até "
                f"{cfg()['pequeno_max_linhas']} linhas); se mexer mais que isso, eu desfaço na hora e anoto como ideia."
                if sim else "Combinado: no modo reserva eu só anoto as ideias; aplico quando a IA principal voltar.")
    if re.match(r"^ideias?\b", resto, re.I):
        ideias = _estado()["ideias"]
        if not ideias:
            return "Nenhuma ideia anotada no modo reserva."
        return (f"{len(ideias)} ideia(s) anotada(s) (confiro quando a IA principal voltar):\n"
                + "\n".join(f"- [{i['projeto']}] {i['resumo'][:140]}" for i in ideias[-10:]))
    if re.match(r"^revis", resto, re.I):  # o bots_conversa manda junto o arquivo REVISAO_MELHORIAS.md
        n = pacote_revisao()
        return (f"Pacote de revisão com {n} mudança(s) desde a última revisão: o arquivo vem na próxima mensagem. "
                "Pra revisar em qualquer chat de IA: copie o texto abaixo, cole no chat e anexe o arquivo.\n\n"
                + PROMPT_REVISAO)
    lm = re.match(r"^regras?\s*:\s*(.+)$", resto, re.I | re.S)
    if lm:  # lição pro agente (vinda de uma revisão feita em qualquer chat de IA)
        _nova_licao(lm.group(1), "Telegram")
        return "Lição anotada. O agente segue ela a partir da próxima rodada."
    if re.match(r"^regras?\s*$", resto, re.I):
        return "Lições que o agente segue (as mais novas embaixo):\n" + _licoes(3000)
    pm = re.match(r"^prompt\s*:?\s*(.+)$", resto, re.I | re.S)
    if pm:
        # 24/10 (achado 10): o pedido do painel tem 4.000 caracteres; prompt grande empurrava a regra [PERGUNTA]
        # (gastar dinheiro) e o CHECK pra fora
        novo = pm.group(1).strip()
        _salvar_cfg(prompt=novo[:700])
        return ("Prompt das melhorias trocado. Vale a partir da próxima rodada."
                + (f" Cortei em 700 caracteres (o seu tinha {len(novo)}): o resto empurrava as regras pra fora."
                   if len(novo) > 700 else ""))
    om = re.match(r"^opus\s*(ligar|liga|on|desligar|desliga|off|status)?\b", resto, re.I)
    if om:  # 24/10: a 3ª camada (mesmo efeito do botão da área de trabalho)
        import auditoria_final
        import camada_opus
        acao = (om.group(1) or "status").lower()
        if acao in ("ligar", "liga", "on"):
            return camada_opus.ligar()
        if acao in ("desligar", "desliga", "off"):
            return camada_opus.desligar()
        return auditoria_final.status_txt(_estado(), cfg())
    return status()


def _papel_txt(e, job):
    p = e["papeis"].get(job["id"]) or {}
    if p:
        return p["papel"] + {"B": " (Gemini)", "C": " (Kiro adversário)"}.get(p.get("lado"), "")
    return {"propor": "executor (propondo)", "aplicar": "executor (aplicando)"}.get(job["tipo"], job["tipo"])


def status():
    import ia_reserva
    import painel_ia
    c, e = cfg(), _estado()
    atual = painel_ia.ler(e["atual"]) if e.get("atual") else None
    hoje_d = datetime.now().strftime("%Y-%m-%d")
    hoje = [f for f in e["feitos"] if f["quando"][:10] == hoje_d]
    falhas = [f for f in e["falhas"] if f["quando"][:10] == hoje_d]
    try:  # a mesma decisão do motor (ia_reserva.modelos: testa o principal no gateway no máximo a cada 10 min)
        sem_credito = _modo()[0] == "reserva"
    except Exception:  # noqa: BLE001
        sem_credito = False
    proxima = e.get("proxima_em", 0)
    linhas = [f"Melhorias contínuas: {'LIGADAS' if c.get('ligado') else 'PARADAS'}"
              + (" — MODO RESERVA (IA principal sem crédito: só anoto ideias)" if sem_credito
                 and not c.get("reserva_aplica_pequeno") else " — modo reserva (consertos pequenos)" if sem_credito
                 else ""),
              f"Agora: {_papel_txt(e, atual)} em {atual['projeto']} ({atual['status']}, IA {atual.get('modelo') or '?'})"
              if atual else ("Agora: esperando " + (f"a pausa entre rodadas (até {datetime.fromtimestamp(proxima):%H:%M})"
                                                    if proxima > time.time() else "— " + _por_que_espera(c))),
              f"Hoje: {len(hoje)} rodada(s), {sum(1 for f in hoje if f['status'] == 'CONSERTEI')} melhoria(s) aplicada(s)"
              + (f", {len(falhas)} perdida(s) por falha da IA" if falhas else "")
              + (f" | ideias anotadas: {len(e['ideias'])}" if e["ideias"] else "")]
    linhas += [f"- [{f['projeto']}] {f['status']}: {f['resumo'][:120]}" for f in hoje[-5:]]
    if c.get("multiagente"):
        bl = _backlog(c)
        reprov = sum(1 for f in hoje if f["status"] == "REPROVADO")
        linhas.append(f"Backlog (achado pelo buscador): {len(bl)} item(ns)"
                      + (f" | reprovadas e desfeitas pelo revisor hoje: {reprov}" if reprov else ""))
        linhas += [f"- [{i['projeto']}] {i['titulo'][:100]}" for i in sorted(bl, key=lambda i: -_nota(i))[:3]]
    desc = [p for p, ate in e["descanso"].items() if float(ate) > time.time()]
    if desc:
        linhas.append("Descansando (nada a fazer agora): " + ", ".join(desc))
    try:  # 24/10: a 3ª camada
        import auditoria_final
        linhas.append(auditoria_final.status_txt(e, c))
        import opus55
        linhas.append(opus55.status_txt(c, e))
    except Exception as ex:  # noqa: BLE001
        linhas.append(f"Auditoria final (Opus): sem status ({type(ex).__name__})")
    linhas.append("Comandos: melhorias ligar | parar | ideias | regras | regra: <lição> | reserva sim/não | prompt: <texto>"
                  " | opus ligar/desligar")
    return "\n".join(linhas)


def rodar(minutos):
    if TRAVA.exists() and time.time() - TRAVA.stat().st_mtime < 180:
        return  # já tem um motor vivo
    TRAVA.parent.mkdir(parents=True, exist_ok=True)
    fim = time.time() + minutos * 60
    try:
        while time.time() < fim:
            TRAVA.write_text(str(time.time()), encoding="utf-8")
            try:
                passo()
            except Exception as ex:  # noqa: BLE001
                log(f"volta falhou ({type(ex).__name__}: {ex})")
            time.sleep(30)
    finally:
        TRAVA.unlink(missing_ok=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--rodar" in sys.argv:
        rodar(float(sys.argv[sys.argv.index("--rodar") + 1]))
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        print(status())
    elif len(sys.argv) > 1 and sys.argv[1] == "pacote":
        print(f"{pacote_revisao()} mudança(s) no pacote: {REVISAO}")
    elif len(sys.argv) > 1 and sys.argv[1] in ("ligar", "parar"):
        print(comando("melhorias " + sys.argv[1]))
