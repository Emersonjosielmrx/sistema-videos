# -*- coding: utf-8 -*-
"""Producao em massa com image-to-video.

Mapeia categorias de imagem -> canais, pega imagem aleatoria da categoria
correspondente e envia pro Veo API como base (image-to-video).
Roda em loop ate acabar creditos ou ser interrompido.

Uso: python producao_imagens.py [--max N] [--canal NOME]
"""
import sys, os, time, random, json, traceback, urllib.request, urllib.error, argparse, shutil, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import VEO_API_URL, VEO_API_TOKEN, VIDEOS_DIR
from agentes import pipeline_criacao, CANAIS, montar_prompt_veo, montar_titulo
from db_local import add_video, update_video, get_stats

IMAGES_ROOT = r"D:\fotos para videos\fotos"
IMAGES_DIRS = {
    "retrato": os.path.join(IMAGES_ROOT, "fotos retrato novo para videos"),
    "paisagem": os.path.join(IMAGES_ROOT, "Fotos minhas paisagem"),
    "retrato2": os.path.join(IMAGES_ROOT, "Fotos minhas retrato"),
    "jornal": os.path.join(IMAGES_ROOT, "Fotos jornal"),
}

CANAL_TO_IMAGE_CAT = {
    "Stand-up IA": "retrato",
    "Humor de IA": "retrato",
    "Cassetadas IA": "retrato",
    "Entrevistas Rua": "paisagem",
    "IA Talk Show": "retrato",
    "Alienigenas": "paisagem",
    "Robos Desastrados": "retrato",
    "ReCenas IA": "paisagem",
    "E Se...": "paisagem",
    "Motivacao IA": "retrato2",
    "Transformacao": "retrato",
    "Dicas Financeiras": "retrato2",
    "Noticias de IA": "jornal",
    "Aulas IA": "retrato",
    "Curiosidades IA": "paisagem",
    "Fatos Bizarros": "paisagem",
    "Mitos vs Verdades": "retrato",
    "Corpo Humano": "retrato2",
    "Recordes Mundiais": "paisagem",
    "Cerebro Digital": "retrato",
    "AlucinaAI": "paisagem",
    "Fofos e Absurdos": "retrato",
    "Danca e Musica IA": "retrato2",
    "Fake News IA": "jornal",
    "Segredos do Oceano": "paisagem",
    "Dicas Fitness": "retrato2",
    "Podcast Cortes": "retrato",
    "Ilusoes de Otica": "paisagem",
    "Super Slow IA": "paisagem",
}

_image_cache = {}

def _listar_imagens(categoria):
    if categoria in _image_cache:
        return _image_cache[categoria]
    path = IMAGES_DIRS.get(categoria)
    if not path or not os.path.isdir(path):
        path = IMAGES_DIRS["retrato"]
    imgs = [os.path.join(path, f) for f in os.listdir(path)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
            and os.path.isfile(os.path.join(path, f))]
    if not imgs:
        for d in IMAGES_DIRS.values():
            if os.path.isdir(d):
                imgs = [os.path.join(d, f) for f in os.listdir(d)
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
                        and os.path.isfile(os.path.join(d, f))]
                if imgs:
                    break
    _image_cache[categoria] = imgs
    return imgs


def escolher_imagem(canal_nome):
    cat = CANAL_TO_IMAGE_CAT.get(canal_nome, "retrato")
    imgs = _listar_imagens(cat)
    if not imgs:
        imgs = _listar_imagens("retrato")
    return random.choice(imgs) if imgs else None


def enviar_veo(prompt, image_path=None):
    payload = {"prompt": prompt, "aspect": "9:16"}
    if image_path:
        payload["image"] = image_path
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    if VEO_API_TOKEN:
        headers["Authorization"] = f"Bearer {VEO_API_TOKEN}"
    req = urllib.request.Request(
        f"{VEO_API_URL}/v1/jobs", data=data, headers=headers, method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read()).get("job_id")
    except Exception as e:
        print(f"[prod] erro enviar Veo: {e}")
        return None


def poll_veo(job_id, timeout=900, interval=30):
    headers = {}
    if VEO_API_TOKEN:
        headers["Authorization"] = f"Bearer {VEO_API_TOKEN}"
    deadline = time.time() + timeout
    consecutive_404 = 0
    while time.time() < deadline:
        try:
            req = urllib.request.Request(
                f"{VEO_API_URL}/v1/jobs/{job_id}", headers=headers
            )
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            status = data.get("status", "")
            consecutive_404 = 0
            if status == "done":
                return data
            if status == "error":
                print(f"[prod] Veo erro: {data.get('error', '?')}")
                return None
            remaining = int(deadline - time.time())
            print(f"[prod] {status}... ({remaining}s)")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                consecutive_404 += 1
                if consecutive_404 >= 5:
                    print("[prod] 5x 404 seguidos — desistindo")
                    return None
                time.sleep(60)
                continue
            print(f"[prod] poll erro: {e}")
        except Exception as e:
            print(f"[prod] poll erro: {e}")
        time.sleep(interval)
    print("[prod] timeout")
    return None


def baixar_video(job_id):
    headers = {}
    if VEO_API_TOKEN:
        headers["Authorization"] = f"Bearer {VEO_API_TOKEN}"
    url = f"{VEO_API_URL}/v1/jobs/{job_id}/video"
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=60)
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        out = VIDEOS_DIR / f"{job_id}.mp4"
        out.write_bytes(resp.read())
        size = out.stat().st_size
        if size > 10000:
            print(f"[prod] Salvo: {out} ({size/1024/1024:.1f} MB)")
            return str(out)
        out.unlink()
    except Exception as e:
        print(f"[prod] download erro: {e}")
    return None


def gerar_um_com_imagem(canal=None):
    if not canal:
        canal = random.choice(CANAIS)
    print(f"\n{'='*60}")
    print(f"[prod] Canal: {canal['nome']} ({canal['tema']})")
    print(f"{'='*60}")

    resultado = pipeline_criacao(canal)
    if not resultado or not resultado.get("prompt_video"):
        print("[prod] Falha no pipeline de criacao")
        return None

    imagem = escolher_imagem(canal["nome"])
    print(f"[prod] Imagem base: {os.path.basename(imagem) if imagem else 'NENHUMA'}")
    print(f"[prod] Titulo: {resultado['titulo'][:70]}")
    print(f"[prod] Prompt: {resultado['prompt_video'][:100]}...")

    db_id = add_video(
        canal=resultado.get("canal", ""),
        modo="criacao_img",
        titulo=resultado["titulo"],
        prompt_video=resultado["prompt_video"],
        prompt_imagem=imagem or "",
    )

    veo_job = enviar_veo(resultado["prompt_video"], image_path=imagem)
    if not veo_job:
        update_video(db_id, status="error", error="falha enviar Veo")
        return None

    update_video(db_id, veo_job_id=veo_job, status="rendering", started_at=time.time())
    print(f"[prod] Job: {veo_job}")

    veo_result = poll_veo(veo_job)
    if not veo_result:
        update_video(db_id, status="error", error="timeout/erro Veo")
        return None

    video_path = baixar_video(veo_job)
    if video_path:
        update_video(db_id, status="done", video_path=video_path, finished_at=time.time())
        print(f"[prod] SUCESSO! {video_path}")
        POSTAR_DIR = os.path.join(os.path.dirname(__file__), "videos_para_postar", "com_minha_foto")
        os.makedirs(POSTAR_DIR, exist_ok=True)
        slug = re.sub(r'[^a-zA-Z0-9]+', '_', resultado["titulo"][:40])[:35]
        canal_slug = re.sub(r'[^a-zA-Z0-9]+', '_', canal["nome"][:20])[:20]
        dest = os.path.join(POSTAR_DIR, f"{canal_slug}_{slug}_{veo_job[:8]}.mp4")
        shutil.copy2(video_path, dest)
        print(f"[prod] Copiado pra postar: {os.path.basename(dest)}")
        return {"db_id": db_id, "video_path": video_path, "titulo": resultado["titulo"]}
    else:
        update_video(db_id, status="error", error="falha download")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=0, help="Max videos (0=infinito)")
    parser.add_argument("--canal", type=str, help="Forcar canal especifico")
    args = parser.parse_args()

    canal = None
    if args.canal:
        canal = next((c for c in CANAIS if c["nome"].lower() == args.canal.lower()), None)
        if not canal:
            print(f"Canal '{args.canal}' nao encontrado. Disponiveis:")
            for c in CANAIS:
                print(f"  - {c['nome']}")
            sys.exit(1)

    print(f"[prod] === PRODUCAO EM MASSA (image-to-video) ===")
    print(f"[prod] Imagens em: {IMAGES_ROOT}")
    print(f"[prod] Max: {'infinito' if not args.max else args.max}")
    print(f"[prod] Stats: {get_stats()}")

    gerados = 0
    erros_seq = 0
    while True:
        if args.max and gerados >= args.max:
            print(f"[prod] Limite de {args.max} videos atingido!")
            break
        try:
            result = gerar_um_com_imagem(canal)
            if result:
                gerados += 1
                erros_seq = 0
                print(f"[prod] Total gerados: {gerados}")
            else:
                erros_seq += 1
        except Exception as e:
            print(f"[prod] ERRO: {e}")
            traceback.print_exc()
            erros_seq += 1

        if erros_seq >= 5:
            print("[prod] 5 erros seguidos — pausa de 10min (creditos esgotados?)")
            time.sleep(600)
            erros_seq = 0
        else:
            time.sleep(60)


if __name__ == "__main__":
    main()
