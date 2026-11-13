import json, collections
from datetime import datetime, timedelta
L = r"D:\video-fila\estado\avisos.jsonl"
corte = (datetime.now() - timedelta(days=7)).isoformat()
cont = collections.Counter(); env = collections.Counter(); ult = {}
for ln in open(L, encoding="utf-8"):
    try:
        d = json.loads(ln)
    except Exception:
        continue
    q = str(d.get("em") or "")
    if q < corte:
        continue
    o = d.get("origem") or "?"
    cont[o] += 1
    env[o] += d.get("situacao") == "enviado"
    ult[o] = (q[:16].replace("T", " "), (d.get("texto") or "").strip())
SUG = {  # o que eu sugiro para cada tipo (a dona decide)
 "inscritos": "JÁ MUDADO 09/11: agora só avisa meta de inscritos (degrau automático), não cada +1",
 "no ar": "CORTAR do Telegram (só painel): 1 msg por Short postado",
 "argon": "CORTAR: troca de conta do Argon é rotina interna",
 "sonnet-monitor": "CORTAR: rotina interna", "opus-monitor": "CORTAR: rotina interna", "troca-modelo": "CORTAR: rotina interna",
 "argon-monitor": "CORTAR: rotina interna", "sentinela-credito": "CORTAR: rotina interna", "sonnet-web": "CORTAR: rotina interna",
 "hipercool": "REDUZIR: só falhas", "aprendizado": "CORTAR: vai pro painel",
 "monitor do anime": "MANTER só falha que repete 3x", "telao": "CORTAR: like do telão é detalhe",
 "banimento": "MANTER só banimento real (rampa de tetos = painel)", "postagens": "MANTER: resumo 3x/dia",
 "filas de postagem": "MANTER no resumo", "vídeos": "MANTER só erro", "postador": "MANTER no resumo",
 "studio": "MANTER: Short parecido / restrição do YouTube", "ritmo de postagem": "CORTAR: informativo",
 "contas com problema": "MANTER só deslogado CONFIRMADO (pendência humana)", "nsn": "MANTER só deslogado confirmado",
 "painel ia": "CORTAR: vai pro painel", "guarda de testes": "CORTAR", "resumo": "MANTER",
 "no ar longo": "MANTER (poucos por dia)", "instagram login": "MANTER (pendência humana)",
 "vigia desktop": "MANTER só > 2 h fora", "melhorador central": "CORTAR: painel", "postagem": "MANTER no resumo",
 "freelas-99f": "MANTER (dinheiro)", "vigia-postagem": "MANTER só erro repetido", "longo": "MANTER",
 "recap-longo": "MANTER (defeito no vídeo)", "engenharia_reversa": "CORTAR", "mil views": "MANTER (metas)",
 "controlador": "MANTER", "veo": "CORTAR: créditos vão pro painel", "comentarios": "MANTER (responder)",
 "recapd": "CORTAR: voz aprovada é informativo", "vigia de melhorias": "CORTAR", "pendencias_humanas": "MANTER",
 "opus": "CORTAR", "tiktok notebooks": "MANTER (código por e-mail = humano)", "producao": "MANTER no resumo",
 "credenciais-kaggle": "MANTER", "instagram auto": "MANTER (suspensão)", "conferência do áudio": "MANTER",
 "produto-lead": "MANTER (cliente respondeu)", "checar_canais": "MANTER", "resumo dos notebooks": "CORTAR",
 "resumo_geral": "MANTER", "plantao": "MANTER", "rampa de canais": "CORTAR", "tiktok-views": "MANTER 1x/dia",
 "vigia mútuo": "JUNTAR com vigia desktop", "trechos_noite": "CORTAR", "solares": "MANTER",
 "maquinas-24h": "MANTER 1x/dia", "desktop-vigia": "JUNTAR com vigia desktop", "kaggle contas": "MANTER",
 "carrossel-marca": "MANTER só falha", "claude-code-video": "CORTAR", "bloqueios": "MANTER",
 "youtube-trava": "MANTER", "melhoria contínua": "MANTER (erro que não desfez)", "vigilancia": "CORTAR",
 "metricas": "MANTER no resumo", "msenergy-metricas": "MANTER 1x/semana",
}
out = ["# Catálogo dos avisos do Telegram — últimos 7 dias (gerado 09/11)", "",
       "Cada tipo: quantos registrou / quantos foram MESMO pro Telegram (o resto entrou em resumo, repetido ou mudo),",
       "o último exemplo e minha sugestão. Dona: marque [x] no que quer cortar e me diga 'aplica os avisos'.", "",
       "Fonte: D:\\video-fila\\estado\\avisos.jsonl (avisos.py).", ""]
for i, (o, n) in enumerate(cont.most_common(), 1):
    q, t = ult[o]
    t = t.replace("\n", " · ")[:300]
    out += [f"## {i}. {o}  —  {n} registrados / {env[o]} enviados", f"- Sugestão: {SUG.get(o, 'avaliar')}",
            f"- [ ] cortar", f"- Último ({q}): {t}", ""]
open(r"D:\video-fila\AVISOS_TELEGRAM_CATALOGO.md", "w", encoding="utf-8").write("\n".join(out))
print(len(cont), sum(cont.values()), sum(env.values()))
