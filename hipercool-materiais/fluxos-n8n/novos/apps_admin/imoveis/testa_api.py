# Teste real da Vitrine: cria vitrine, sobe as 5 fotos de exemplo da oficina, IA escreve o anúncio, publica e gera o vídeo.
import base64, io, json, sys, time, urllib.request
from PIL import Image
BASE = "https://webhookn8n6.inovareinteligenciaartificial.com"


def api(acao, **d):
    t = time.time()
    req = urllib.request.Request(BASE + "/webhook/imoveis-api", data=json.dumps({"acao": acao, **d}).encode(), headers={"Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=200).read())
    print(f"{acao:14} {time.time() - t:5.1f}s", json.dumps(r, ensure_ascii=False)[:260])
    return r


def get(c):
    t = time.time(); r = urllib.request.urlopen(BASE + c, timeout=60); b = r.read()
    print(f"GET {c[:50]:50} {time.time() - t:4.1f}s {r.status} {len(b)}"); return b


for c in ("/webhook/imoveis-criar", "/webhook/imoveis-painel", "/webhook/imoveis", "/webhook/imovel"):
    get(c)
loja = api("cadastro", nome="Ana Teste Imóveis", senha="<SEGREDO_REMOVIDO>", whatsapp="51999990000", cidade="Porto Alegre", creci="12345-F")["loja"]
tok = api("login", loja=loja, login="admin", senha="<SEGREDO_REMOVIDO>")["token"]
ids, minis = [], []
for n in range(1, 6):
    jpg = get(f"/videos/arquivo/exemplos/fotos/apartamento/{n}.jpg") if False else None
    break
# as fotos de exemplo não são públicas: busca pela ssh
import subprocess
for n in range(1, 6):
    b = subprocess.run(["ssh", "hermes-bloqueio", f"base64 -w0 /opt/video-oficina/dados/exemplos/fotos/apartamento/{n}.jpg"], capture_output=True, text=True, timeout=60).stdout.strip()
    img = Image.open(io.BytesIO(base64.b64decode(b))).convert("RGB")
    g = img.copy(); g.thumbnail((1800, 1800)); bf = io.BytesIO(); g.save(bf, "JPEG", quality=84)
    p = img.copy(); p.thumbnail((512, 512)); bp = io.BytesIO(); p.save(bp, "JPEG", quality=70)
    ids.append(api("img_salvar", token=tok, mime="image/jpeg", b64=base64.b64encode(bf.getvalue()).decode())["id"])
    minis.append(base64.b64encode(bp.getvalue()).decode())
get("/webhook/imoveis-img?id=" + ids[0])
a = api("ia_anuncio", token=tok, miniaturas=minis, notas="Apartamento reformado, condomínio com portaria 24h, perto do parque", dados={"finalidade": "venda", "bairro": "Moinhos de Vento", "cidade": "Porto Alegre"})
an = json.loads(a["resultado"].strip().removeprefix("```json").removesuffix("```"))
print(json.dumps(an, ensure_ascii=False, indent=1)[:2500])
ordem = [ids[i] for i in an.get("ordem_fotos", []) if i < len(ids)] or ids
s = api("salvar", token=tok, titulo=an["titulo"], descricao=an["descricao"], destaques=an["destaques"], caracteristicas=an["caracteristicas"], tipo=an.get("tipo", "apartamento"),
        preco=890000, quartos=an.get("quartos") or 2, banheiros=an.get("banheiros") or 2, vagas=1, area=95, bairro="Moinhos de Vento", cidade="Porto Alegre",
        fotos=ordem + [i for i in ids if i not in ordem], status="publicado", destaque=True)
cod = s["codigo"]
get(f"/webhook/imovel?l={loja}&c={cod}")
api("imovel", loja=loja, codigo=cod)
api("lead", loja=loja, codigo=cod, nome="Carlos", telefone="51988887777", interesse="visita", mensagem="Posso visitar sábado?")
v = api("video_gerar", token=tok, id=s["id"], formato="vertical", duracao=15, voz="pt-BR-ThalitaMultilingualNeural")
job = v.get("job")
print("LOJA", loja, "ID", s["id"], "JOB", job)
if not job:
    sys.exit(1)
for k in range(80):
    st = json.loads(urllib.request.urlopen(f"{BASE}/webhook/anuncio-video-status?job={job}", timeout=30).read())
    print(f"  {k*6:4d}s etapa={st.get('etapa')} {str(st.get('detalhe', ''))[:70]} {st.get('progresso', '')}")
    if st.get("etapa") in ("pronto", "erro"):
        print(json.dumps({k2: st.get(k2) for k2 in ("video", "video_musica", "capa", "pagina", "erro", "duracao")}, ensure_ascii=False))
        break
    time.sleep(6)
time.sleep(1)
api("video_guardar", token=tok, id=s["id"], job=job, pagina=st.get("pagina", ""), erro=st.get("erro", "") if st.get("etapa") == "erro" else "")
r = api("ver", token=tok, id=s["id"])
print("VIDEO", r["imovel"]["video"])
