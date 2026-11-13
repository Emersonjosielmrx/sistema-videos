"""Teste de ponta a ponta de uma versão: manda o pedido pelo webhook (como a página) e acompanha o status até o fim.
Uso: python teste_fluxo.py <sufixo> [exemplo] [extra_json]   ex.: python teste_fluxo.py j2v apartamento '{"duracao":15}'"""
import json, sys, time, urllib.request, urllib.error

SUF = sys.argv[1]
EX = sys.argv[2] if len(sys.argv) > 2 else "apartamento"
EXTRA = json.loads(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].startswith("{") else {}
BASE = "https://webhookn8n6.inovareinteligenciaartificial.com/webhook"
CAMPOS = {
    "apartamento": dict(fotos=[f"exemplo-apartamento-{n}" for n in range(1, 6)], tipo="imovel", marca="Vista Alta Imóveis",
                        titulo="Apartamento 3 quartos com varanda gourmet e vista", preco="R$ 890 mil", oferta="Entrada facilitada em até 36 vezes",
                        detalhes="98 m² no 12º andar, 3 quartos sendo 1 suíte master, sala ampla com janelas do chão ao teto, cozinha planejada com ilha, varanda gourmet com churrasqueira e vista para a cidade, 2 vagas, prédio com portaria 24 horas, piscina e academia.",
                        whatsapp="11988887777", instagram="@vistaalta.imoveis", endereco="Rua das Palmeiras, 450 - Centro, São Paulo - SP"),
    "hamburguer": dict(fotos=[f"exemplo-hamburguer-{n}" for n in range(1, 5)], tipo="comida", marca="Brasa Burger",
                       titulo="Combo Brasa: burger artesanal + fritas + milkshake", preco="R$ 49,90", oferta="Toda terça o milkshake sai pela metade do preço",
                       detalhes="Hambúrguer artesanal de 180 g na brasa, cheddar derretido e bacon crocante no pão brioche; fritas rústicas com molho de cheddar; milkshake de chocolate com brownie. Delivery no bairro e salão aberto de terça a domingo, das 18h às 23h.",
                       whatsapp="11977776666", instagram="@brasaburger", endereco="Av. Brasil, 1200 - Jardins, São Paulo - SP"),
}
if "--enviar" in sys.argv:  # sobe as fotos de exemplo pela rota da página, como um aluno faria
    import subprocess
    ids = []
    for n in range(1, len(CAMPOS[EX]["fotos"]) + 1):
        r = subprocess.run(["curl", "-s", "-m", "120", "-F", f"arquivo=@exemplos/{EX}/{n}.jpg;type=image/jpeg", f"{BASE}/anuncio-video-{SUF}-foto"], capture_output=True, text=True)
        ids.append(json.loads(r.stdout)["id"])
    print("fotos enviadas:", ids, flush=True)
    CAMPOS[EX]["fotos"] = ids
    EXTRA.pop("--enviar", None)
corpo = {**CAMPOS[EX], "duracao": 30, "formato": "vertical", "voz": "pt-BR-ThalitaMultilingualNeural", "clima": "auto", "legendas": True,
         "versao_musica": True, "cartao_final": True, "manter_ordem": False, **EXTRA}


def chama(url, dados=None):
    req = urllib.request.Request(url, data=json.dumps(dados).encode() if dados else None, method="POST" if dados else "GET",
                                 headers={"Content-Type": "text/plain"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


st, r = chama(f"{BASE}/anuncio-video-{SUF}", corpo)
print("pedido:", st, r, flush=True)
if not r.get("ok"):
    sys.exit(1)
job = r["link"].split("job=")[1]
t0, ultimo = time.time(), None
while time.time() - t0 < 900:
    time.sleep(10)
    st, s = chama(f"{BASE}/anuncio-video-{SUF}-status?job={job}")
    s = s.get("status", s) if isinstance(s, dict) else s
    linha = (s.get("etapa"), s.get("detalhe") or s.get("erro"))
    if linha != ultimo:
        print(int(time.time() - t0), "s", linha, flush=True)
        ultimo = linha
    if s.get("etapa") in ("pronto", "erro"):
        print(json.dumps({k: s.get(k) for k in ("etapa", "erro", "video", "video_musica", "capa", "pagina", "duracao", "segundos")}, ensure_ascii=False, indent=1))
        break
