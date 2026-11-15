# Teste real da API da Comanda pelo webhook público (cria uma loja de teste e apaga no fim via SQL).
import json, time, urllib.request, base64, io, sys
BASE = "https://webhookn8n6.inovareinteligenciaartificial.com/webhook"


def api(acao, **d):
    t = time.time()
    req = urllib.request.Request(BASE + "/comanda-api", data=json.dumps({"acao": acao, **d}).encode(), headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    print(f"{acao:16} {time.time() - t:5.1f}s", json.dumps(r, ensure_ascii=False)[:230])
    return r


def get(caminho):
    t = time.time()
    r = urllib.request.urlopen(BASE + caminho, timeout=60)
    corpo = r.read()
    print(f"GET {caminho[:40]:40} {time.time() - t:5.1f}s {r.status} {r.headers.get('Content-Type')} {len(corpo)} bytes")
    return corpo


for p in ("/comanda", "/comanda-painel", "/comanda-mesa"):
    get(p)
c = api("cadastro", nome="Teste Aula Comanda", senha="<SEGREDO_REMOVIDO>", mesas=4, tipo="bar")
loja = c["loja"]
tok = api("login", loja=loja, login="dono", senha="<SEGREDO_REMOVIDO>")["token"]
api("eu", token=tok)
cat = api("prod_lista", token=tok)
# imagem: PNG 1x1 vermelho
png = base64.b64encode(bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de0000000c4944415408d763f8cfc000000301010018dd8db00000000049454e44ae426082")).decode()
im = api("img_salvar", token=tok, mime="image/png", b64=png)
get("/comanda-img?id=" + im["id"])
get("/comanda-img?id=00000000-0000-0000-0000-000000000000") if False else None
p0 = cat["produtos"][0]
api("prod_salvar", token=tok, id=p0["id"], nome=p0["nome"], categoria_id=p0["categoria_id"], preco=31.5, imagem=im["id"], adicionais=p0["adicionais"], descricao=p0["descricao"], destaque=True)
api("caixa_abrir", token=tok, troco=50)
api("comanda_add", token=tok, mesa=1, itens=[{"produto_id": p0["id"], "qtd": 1, "adicionais": ["Bacon"]}])
cfg = api("config_ver", token=tok)
t1 = cfg["qrs"][0]["t"]
api("cliente_menu", loja=loja, mesa=1, t=t1)
api("cliente_pedir", loja=loja, mesa=1, t=t1, itens=[{"produto_id": cat["produtos"][-1]["id"], "qtd": 2}])
api("cozinha", token=tok)
api("ia_descricao", token=tok, nome="Pastel de carne", categoria="Porções", ingredientes="carne moída, azeitona, ovo")
r = api("ia_importar", token=tok, texto="X-tudo 32,00\nmisto quente ... 14\ncoca lata 7 reais\nchopp 300ml 12,50\nporcao fritas 400g 24")
ana = api("ia_analise", token=tok)
v = api("comanda_ver", token=tok, mesa=1)["comanda"]["total"]
api("comanda_fechar", token=tok, mesa=1, pagamentos=[{"forma": "pix", "valor": float(v)}])
api("relatorio", token=tok)
print("LOJA", loja)
