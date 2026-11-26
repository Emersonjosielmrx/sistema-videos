# D:\hipercool-materiais\fluxos-n8n\novos\insta_integra\testa.py
# Teste de ponta a ponta: 1) gera diagnóstico novo  2) cria um calendário usando o diagnóstico  3) confere o resultado.
# Não publica nada (publicação automática fica desligada).
import json, sys, time, urllib.request, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
W = "https://webhookn8n6.inovareinteligenciaartificial.com/webhook"
def get(u, t=60):
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "teste-fluxo"}), timeout=t) as r: return r.read().decode("utf-8", "replace")
def post(u, d, t=60):
    req = urllib.request.Request(u, data=json.dumps(d).encode(), method="POST", headers={"Content-Type": "text/plain", "User-Agent": "teste-fluxo"})
    with urllib.request.urlopen(req, timeout=t) as r: return json.loads(r.read())
etapa = sys.argv[1] if len(sys.argv) > 1 else "tudo"
if etapa in ("tudo", "diag"):
    print("1) pedindo diagnóstico novo…"); h = get(f"{W}/insta-relatorio?senha=publica-5b514a&atualizar=1"); print("   resposta:", "analisando" if "Analisando" in h else h[:150])
    # a página mostra o relatório guardado enquanto o novo é feito: espera a hora do relatório mudar
    antes = time.strftime("%H:%M")
    for i in range(30):
        time.sleep(10); h = get(f"{W}/insta-relatorio?senha=publica-5b514a")
        m = re.search(r"relatório de \d\d/\d\d,? (\d\d:\d\d)", h)
        if m and m.group(1) >= antes: break
    print("   hora do relatório:", m.group(1) if m else "?", "(pedido às", antes + ")")
    print("   relatório pronto:", "Análise da IA" in h, "| cartão do plano:", "Plano para o próximo mês" in h, "| IA respondeu:", "não respondeu" not in h)
    m = re.search(r'<div class="mix">(.*?)</div>', h); print("   plano:", re.sub("<[^>]+>", "", m.group(1)) if m else "-")
if etapa in ("tudo", "p30"):
    print("2) criando calendário com diagnóstico…")
    r = post(f"{W}/posts30", {"nome": "Teste integração (apagar)", "nicho": "cursos de automação com IA", "vende": "Curso de n8n com IA R$ 297, mentoria em grupo R$ 97/mês, fluxos prontos para pequenos negócios",
        "publico": "donos de pequenos negócios que querem automatizar o atendimento", "objetivo": "Vender mais", "tom": "Descontraído", "ofertas": "", "perfil": "", "estilo": "escuro", "hora": "11:00", "diag": True, "hora_diag": True})
    print("   ", r); link = r.get("link", ""); q = link.split("?")[1]
    for i in range(60):
        time.sleep(10); c = json.loads(get(f"{W}/posts30-dados?{q}"))["cal"]
        if i % 3 == 0: print(f"   {i*10:>3}s status={c['status']} escritos={c['escritos']} diag={(c.get('diagnostico') or {}).get('status')}")
        if c["status"] == "pronto": break
    dg = c.get("diagnostico") or {}
    cont = {}
    for d in c["dias"]: cont[d["formato"]] = cont.get(d["formato"], 0) + 1
    print("   status:", c["status"], "| diag:", dg.get("status"), dg.get("usuario"), "| mix pedido:", dg.get("mix_formatos"), "| mix feito:", cont, "| hora:", c["hora"])
    print("   o que melhorar:", dg.get("o_que_melhorar")); print("   aviso:", dg.get("aviso"))
    print("   dias com motivo:", sum(1 for d in c["dias"] if d.get("motivo")), "de 30 | com erro:", sum(1 for d in c["dias"] if d["estado"] == "erro"))
    for d in c["dias"][:5]: print(f"   dia {d['dia']} {d['formato']:9} {d['tema'][:60]} | 🎯 {d.get('motivo','')[:90]}")
    print("   LINK:", link)
