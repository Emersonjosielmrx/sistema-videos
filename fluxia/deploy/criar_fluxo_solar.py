"""Cria (ou atualiza) o fluxo de menu com botões de uma empresa de energia solar no FluxIA, com o login da loja.
Rodar dentro do contêiner:
    python /app/criar_fluxo_solar.py globo              -> mostra o que vai gravar
    python /app/criar_fluxo_solar.py globo --gravar     -> grava o fluxo (LIGADO; responde assim que a loja ler o QR)
    python /app/criar_fluxo_solar.py advance --gravar
Login e senha da loja pedidos pelo dono (01/11): globo/globo e luiz/luiz. Tela: /cliente.
Dados das empresas: D:\\ms-energy\\docs\\GLOBO.md e ADVANCE.md. Sem preço nem "% de economia": valores não confirmados.
Só vai no texto o que a empresa diz no Instagram (ex.: "Financiamos e parcelamos" é da bio da Globo; da Advance não)."""

import json
import sqlite3
import sys

sys.path.insert(0, "/app")
from backend.flow_config import new_config  # noqa: E402

EMPRESAS = {
    "globo": {
        "fluxo": "Globo Solar (menu)",
        "login": "globo", "senha": "globo", "nome_login": "Globo Solar",
        "admin": "91 98246-9729, 6451208650994",  # dono da Globo (número e LID): ensina e simula pelo WhatsApp só nesta linha (04/11)
        "loja": "Globo Solar | Energia Global",
        "cidade": "Concórdia do Pará",
        "endereco": "Av. Deodoro da Fonseca, 695, Pinheiro, Concórdia do Pará",
        "boas_vindas": "Energia solar pra você economizar na conta de luz. *Financiamos e parcelamos!*",
        "pagamento": "💳 Financiamos e parcelamos (o consultor simula as parcelas pelo valor da sua conta de luz).",
    },
    "advance": {
        "fluxo": "Advance Solar (menu)",
        "login": "luiz", "senha": "luiz", "nome_login": "Advance Solar (Luiz)",
        "loja": "Advance Energia Solar",
        "cidade": "Castanhal (PA)",
        "endereco": "",  # não está no Instagram; a IA diz que o consultor informa
        "boas_vindas": "Energia solar pra você economizar na conta de luz, com instalação bem feita. ☀️",
        "pagamento": "💳 Formas de pagamento e financiamento: o consultor apresenta junto com o orçamento.",
    },
}

PROMPT = """Você é o atendente virtual da {{loja}} no WhatsApp, empresa de energia solar de {{cidade}}. Seja simpático e objetivo: no máximo 2 frases curtas e 2 emojis.

COMO FUNCIONA O ATENDIMENTO:
- O orçamento é feito pelo MENU DE OPÇÕES (botões no WhatsApp): o cliente escolhe a opção e o sistema faz as perguntas (cidade, valor da conta de luz, foto da conta, telhado) e passa para um consultor.
- Você só entra quando o cliente escreve ou fala (áudio) algo que não é uma opção: responda a dúvida usando SÓ as informações abaixo.
- Você NÃO faz orçamento, NÃO diz preço de kit, NÃO promete porcentagem de economia nem valor de parcela: diga que o consultor calcula pelo consumo da conta de luz e coloque [BOTOES] no fim para ele escolher no menu.
- Use o CONTEXTO DO MENU (opções que o cliente tocou, respostas dadas) para entender a mensagem.
- Nunca invente preço, prazo, endereço, horário ou condição de financiamento. Se não souber, diga que o consultor confirma.
- Use [ATENDENTE] só se o cliente pedir para falar com uma pessoa/consultor.

INFORMAÇÕES:
- Cidade: {{cidade}}
- Endereço: {{endereco}}
- Horário: {{horario}}

SOBRE A EMPRESA:
{{informacoes}}"""


# 04/11 (dono): sem botões, conversa curta e o mais humana possível. O menu fica guardado em config.menu
# (menu_enabled=False) para voltar se quiser.
PROMPT_CONVERSA = """Você atende o WhatsApp da {{loja}}, empresa de energia solar de {{cidade}}. Escreva como uma atendente de verdade da empresa conversando pelo celular.

JEITO DE ESCREVER:
- Mensagens CURTAS: 1 ou 2 frases, como no WhatsApp. Nada de listas, tópicos, negrito ou textos longos.
- Português do dia a dia do Pará, simpático e direto. No máximo 1 emoji, e não em toda mensagem.
- UMA pergunta por vez. Use o nome da pessoa quando souber. Não repita cumprimento nem se apresente de novo.
- Se a pessoa mandar áudio, responda normalmente ao que ela falou.
- Se perguntarem se você é robô/IA, diga com naturalidade que é a assistente virtual da {{loja}} e que um consultor de verdade continua o atendimento.

O QUE FAZER:
- Entenda o que a pessoa quer (energia solar em casa, comércio, área rural, financiamento, limpeza/manutenção) e tire dúvidas usando só as informações abaixo.
- Para o orçamento, vá pegando aos poucos, na conversa: nome, cidade/bairro e quanto vem a conta de luz por mês. Depois peça uma foto da conta de luz (se não tiver agora, tudo bem).
- Quando já tiver nome, cidade e o valor da conta (ou a pessoa pedir para falar com alguém), avise que um consultor vai chamar ali mesmo no WhatsApp para passar o orçamento, e coloque [ATENDENTE] no fim.
- Nunca invente preço, valor de kit, parcela, porcentagem de economia, prazo, endereço ou horário. Se perguntarem, diga que o consultor calcula pela conta de luz.
- Se a mensagem não for sobre energia solar (fornecedor, vaga de emprego, assunto pessoal), responda curto e educado e coloque [ATENDENTE] para a equipe ver.

INFORMAÇÕES:
- Cidade: {{cidade}}
- Endereço: {{endereco}}
- Horário: {{horario}}

SOBRE A EMPRESA:
{{informacoes}}"""


def info(e: dict) -> str:
    linhas = ["☀️ Energia solar para casa, comércio e área rural.",
              "🔧 Fazemos projeto, instalação e a homologação junto à concessionária de energia.",
              e["pagamento"],
              "📝 Orçamento sem compromisso: só precisamos da cidade e de uma foto da sua conta de luz."]
    linhas.append(f"📍 {e['endereco']}." if e["endereco"] else f"📍 Atendemos {e['cidade']} e região.")
    return "\n".join(linhas)


CONTA = {"key": "conta", "label": "Conta de luz/mês", "q": "Quanto vem, em média, sua conta de luz por mês? 💡",
         "options": ["Até R$ 200", "R$ 200 a R$ 500", "Mais de R$ 500"]}
FOTO_CONTA = {"key": "foto", "label": "Foto da conta", "type": "file",
              "q": "Se puder, mande uma foto da sua conta de luz 📸\n(Se não tiver agora, escreva *depois*)"}
NOME_Q = {"key": "nome", "label": "Nome", "q": "Para começar, qual o seu nome? 😊"}
CIDADE = {"key": "cidade", "label": "Cidade/bairro", "q": "Em qual cidade e bairro fica o imóvel? 📍"}


def menu(e: dict) -> dict:
    return {
        "welcome": f"Olá! 👋 Bem-vindo à *{e['loja']}* ☀️\n{e['boas_vindas']}",
        "done_text": f"Recebemos seus dados! ✅\n\nUm consultor da *{e['loja']}* vai te chamar aqui no WhatsApp em breve "
                     "com o seu orçamento. ☀️\nSe quiser, pode mandar outras fotos ou dúvidas por aqui.",
        "table_text": f"Como funciona com a {e['loja']} 👇\n\n{{{{informacoes}}}}\n\n"
                      "Para pedir seu orçamento, toque em *☀️ Orçamento solar* no menu acima ou digite *menu*.",
        "menus": {
            # Rótulos de até 20 letras: aparecem como botões do WhatsApp em blocos de 3.
            "inicio": {"title": "Como posso te ajudar? Toque numa opção 👇", "options": [
                {"label": "☀️ Orçamento solar", "service": "orcamento"},
                {"label": "💳 Financiamento", "service": "financiamento"},
                {"label": "🏭 Empresa ou rural", "service": "empresa"},
                {"label": "🧽 Limpeza/manutenção", "service": "manutencao"},
                {"label": "❓ Como funciona", "action": "table"},
                {"label": "🙋 Falar c/ consultor", "action": "human"},
            ]},
        },
        "services": {
            "orcamento": {"label": "Orçamento de energia solar (residencial)", "price": "orçamento sem compromisso", "questions": [
                NOME_Q, CIDADE, CONTA, FOTO_CONTA,
                {"key": "telhado", "label": "Telhado", "q": "Qual o tipo de telhado da casa?",
                 "options": ["Telha de barro", "Fibrocimento", "Laje ou outro"]},
                {"key": "pagamento", "label": "Pagamento", "q": "Como prefere pagar?",
                 "options": ["💳 Financiado", "💰 À vista", "🤔 Ainda não sei"]},
            ]},
            "financiamento": {"label": "Simulação de financiamento solar", "price": "simulação sem compromisso", "questions": [
                NOME_Q, CIDADE, CONTA, FOTO_CONTA,
                {"key": "parcela", "label": "Parcela desejada", "q": "Mais ou menos quanto gostaria de pagar por mês na parcela?"},
            ]},
            "empresa": {"label": "Energia solar para empresa, comércio ou área rural", "price": "orçamento sem compromisso", "questions": [
                NOME_Q,
                {"key": "tipo", "label": "Tipo de lugar", "q": "Que tipo de lugar é? (comércio, fazenda, sítio, indústria...)"},
                CIDADE,
                {"key": "conta", "label": "Conta de luz/mês", "q": "Quanto vem a conta de luz por mês, mais ou menos? 💡"},
                FOTO_CONTA,
            ]},
            "manutencao": {"label": "Limpeza ou manutenção de sistema solar", "price": "valor a combinar", "questions": [
                NOME_Q, CIDADE,
                {"key": "placas", "label": "Placas", "q": "Quantas placas tem o sistema, mais ou menos?"},
                {"key": "problema", "label": "O que precisa", "q": "O que está acontecendo? (limpeza, geração caiu, inversor com erro...)"},
            ]},
        },
    }


def config(e: dict) -> dict:
    m = menu(e)
    for o in m["menus"]["inicio"]["options"]:
        assert len(o["label"]) <= 20, o["label"]
    for svc in m["services"].values():
        for q in svc["questions"]:
            for o in q.get("options", []):
                assert len(o) <= 20, o
    return new_config("servicos_menu", {
        "store_name": e["loja"],
        "store_city": e["cidade"],
        "store_address": e["endereco"],
        "business_info": info(e),
        "prompt": PROMPT_CONVERSA,
        "menu": m,
        "menu_enabled": False,
        "buttons_enabled": False,
        "greeting_text": "",
        "reply_length": "curta",
        "typing": True,
        "split_messages": True,
        "pause_minutes": 1440,
        "owner_off_two_messages": False,
        "admin_phones": e.get("admin", ""),
        "audio_reply": "Oi! Não consegui ouvir seu áudio agora. Pode mandar de novo ou escrever? 🙏",
        "image_action": "vision",
        "document_action": "file",
    })


PRESERVAR = ("notify_phone", "admin_phones", "hours", "hours_enabled", "store_hours", "learned_rules",
             "closed_message", "closed_action", "delivery_info")


def gravar(e: dict, cfg: dict):
    from backend.auth import hash_password
    db = sqlite3.connect("/data/fluxia.db")
    admin = db.execute("SELECT id FROM accounts WHERE role = 'admin' ORDER BY id LIMIT 1").fetchone()[0]
    row = db.execute("SELECT id FROM flows WHERE name = ?", (e["fluxo"],)).fetchone()
    data = json.dumps(cfg, ensure_ascii=False)
    if row:
        flow_id = row[0]
        # o que a loja ou o admin já ajustou (avisos, horário, regras ensinadas, admins) não se perde
        antigo = json.loads(db.execute("SELECT config FROM flows WHERE id = ?", (flow_id,)).fetchone()[0] or "{}")
        for k in PRESERVAR:
            if antigo.get(k) not in (None, "", [], {}):
                cfg[k] = antigo[k]
        data = json.dumps(cfg, ensure_ascii=False)
        db.execute("UPDATE flows SET config = ? WHERE id = ?", (data, flow_id))
        note = f"menu da {e['loja']} atualizado"
    else:
        flow_id = db.execute("INSERT INTO flows (account_id, connection_id, name, type, config, active) VALUES (?, NULL, ?, 'servicos_menu', ?, 1)",
                             (admin, e["fluxo"], data)).lastrowid
        note = f"fluxo da {e['loja']} criado (menu com botões, Gemini 3.8, áudio transcrito)"
    db.execute("INSERT INTO flow_versions (flow_id, config, source, note) VALUES (?, ?, 'painel', ?)", (flow_id, data, note))
    acc = db.execute("SELECT id FROM accounts WHERE email = ?", (e["login"],)).fetchone()
    if acc:
        account_id = acc[0]
    else:
        account_id = db.execute("INSERT INTO accounts (email, password_hash, name, role) VALUES (?, ?, ?, 'client')",
                                (e["login"], hash_password(e["senha"]), e["nome_login"])).lastrowid
    db.execute("INSERT OR IGNORE INTO client_flows (account_id, flow_id) VALUES (?, ?)", (account_id, flow_id))
    db.commit()
    print(f"gravado: fluxo {flow_id}, login {e['login']} (conta {account_id})")


def main():
    nome = next((a for a in sys.argv[1:] if not a.startswith("--")), "")
    if nome not in EMPRESAS:
        sys.exit(f"uso: criar_fluxo_solar.py {'|'.join(EMPRESAS)} [--gravar]")
    e = EMPRESAS[nome]
    cfg = config(e)
    print(json.dumps({k: cfg[k] for k in ("store_name", "model", "menu_enabled", "button_style", "audio_action", "pause_minutes")}, ensure_ascii=False))
    if "--gravar" in sys.argv:
        gravar(e, cfg)


if __name__ == "__main__":
    main()
