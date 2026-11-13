"""
Gerador de shorts virais para MS Energy.
Monta vídeos verticais (1080x1920) a partir de templates configuráveis.
"""
import json
import sys
import argparse
import random
from pathlib import Path
from datetime import datetime

DIR_PROJETO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DIR_PROJETO / "bin"))

import motion

DIR_CONFIG = DIR_PROJETO / "config"
DIR_ASSETS = DIR_PROJETO / "assets"
DIR_VIDEOS = DIR_PROJETO / "videos" / "shorts"
DIR_TMP = DIR_PROJETO / "cache" / "tmp_render"


def carregar_config():
    with open(DIR_CONFIG / "marca.json", encoding="utf-8") as f:
        marca = json.load(f)
    with open(DIR_CONFIG / "templates.json", encoding="utf-8") as f:
        templates = json.load(f)
    return marca, templates


def obter_cor(marca, nome_cor):
    return marca["cores"].get(nome_cor, marca["cores"]["secundaria"])


def encontrar_fotos(subpasta=None):
    base = DIR_ASSETS / "fotos"
    if subpasta:
        base = base / subpasta
    if not base.exists():
        return []
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    return sorted([f for f in base.iterdir() if f.suffix.lower() in exts])


def gerar_short_economia(marca, template, params, output_path):
    """Gera short de economia na conta de luz."""
    DIR_TMP.mkdir(parents=True, exist_ok=True)
    clips = []

    valor_antes = params.get("valor_antes", "800")
    valor_depois = params.get("valor_depois", "47")
    economia_pct = round((1 - int(valor_depois) / int(valor_antes)) * 100)

    cor_fundo = obter_cor(marca, template.get("cor_fundo", "secundaria"))
    cor_primaria = marca["cores"]["primaria"]
    cor_accent = marca["cores"]["accent"]

    hook_text = params.get("hook", f"CONTA DE LUZ: R$ {valor_antes} → R$ {valor_depois}")
    hook_path = DIR_TMP / "hook.mp4"
    motion.gerar_clip_hook(hook_text, 3, hook_path, cor_primaria=cor_primaria, cor_fundo=cor_fundo)
    clips.append(hook_path)

    fotos = encontrar_fotos("instalacoes")
    if fotos:
        foto = random.choice(fotos)
        foto_clip = DIR_TMP / "foto_instalacao.mp4"
        motion.gerar_clip_foto(
            foto, 8, foto_clip,
            texto=params.get("texto_contexto", "INSTALAÇÃO MS ENERGY"),
            cor_fundo=cor_fundo
        )
        clips.append(foto_clip)
    else:
        contexto_path = DIR_TMP / "contexto.mp4"
        motion.gerar_clip_texto(
            "ENERGIA SOLAR\nTRANSFORMA", 8, contexto_path,
            cor_fundo=cor_fundo, cor_texto="white", fontsize=80
        )
        clips.append(contexto_path)

    comp_path = DIR_TMP / "comparativo.mp4"
    motion.gerar_clip_comparativo(valor_antes, valor_depois, 8, comp_path, cor_fundo=cor_fundo)
    clips.append(comp_path)

    cta_text = params.get("cta", marca["cta"]["padrao"])
    cta_path = DIR_TMP / "cta.mp4"
    motion.gerar_clip_cta(cta_text, 6, cta_path, cor_accent=cor_accent, cor_fundo=cor_fundo)
    clips.append(cta_path)

    musica = _escolher_musica("upbeat")
    motion.concatenar_clips(clips, output_path, musica_path=musica)
    return output_path


def gerar_short_antes_depois(marca, template, params, output_path):
    """Gera short de antes/depois."""
    DIR_TMP.mkdir(parents=True, exist_ok=True)
    clips = []

    cor_fundo = obter_cor(marca, template.get("cor_fundo", "primaria"))
    cor_accent = marca["cores"]["accent"]

    hook_text = params.get("hook", "OLHA ESSA TRANSFORMAÇÃO 👇")
    hook_path = DIR_TMP / "hook.mp4"
    motion.gerar_clip_hook(hook_text, 2, hook_path, cor_fundo=cor_fundo)
    clips.append(hook_path)

    foto_antes = params.get("foto_antes")
    if foto_antes and Path(foto_antes).exists():
        antes_clip = DIR_TMP / "antes.mp4"
        motion.gerar_clip_foto(foto_antes, 6, antes_clip, texto="ANTES", cor_fundo=cor_fundo)
        clips.append(antes_clip)
    else:
        antes_clip = DIR_TMP / "antes.mp4"
        motion.gerar_clip_texto("ANTES ❌", 6, antes_clip, cor_fundo="#8B0000", fontsize=100)
        clips.append(antes_clip)

    trans_path = DIR_TMP / "transicao.mp4"
    motion.gerar_clip_texto("⚡", 2, trans_path, cor_fundo=cor_fundo, fontsize=200)
    clips.append(trans_path)

    foto_depois = params.get("foto_depois")
    if foto_depois and Path(foto_depois).exists():
        depois_clip = DIR_TMP / "depois.mp4"
        motion.gerar_clip_foto(foto_depois, 6, depois_clip, texto="DEPOIS ☀️", cor_fundo=cor_fundo)
        clips.append(depois_clip)
    else:
        depois_clip = DIR_TMP / "depois.mp4"
        motion.gerar_clip_texto("DEPOIS ☀️✅", 6, depois_clip, cor_fundo="#006400", fontsize=100)
        clips.append(depois_clip)

    cta_text = params.get("cta", marca["cta"]["padrao"])
    cta_path = DIR_TMP / "cta.mp4"
    motion.gerar_clip_cta(cta_text, 4, cta_path, cor_accent=cor_accent, cor_fundo=cor_fundo)
    clips.append(cta_path)

    musica = _escolher_musica("reveal")
    motion.concatenar_clips(clips, output_path, musica_path=musica)
    return output_path


def gerar_short_dados(marca, template, params, output_path):
    """Gera short de dados/curiosidades sobre energia solar."""
    DIR_TMP.mkdir(parents=True, exist_ok=True)
    clips = []

    cor_fundo = obter_cor(marca, template.get("cor_fundo", "secundaria"))
    cor_primaria = marca["cores"]["primaria"]
    cor_accent = marca["cores"]["accent"]

    hook_text = params.get("hook", "VOCÊ SABIA? ☀️")
    hook_path = DIR_TMP / "hook.mp4"
    motion.gerar_clip_hook(hook_text, 3, hook_path, cor_fundo=cor_fundo)
    clips.append(hook_path)

    dados = params.get("dados", [
        {"titulo": "SOL NO BRASIL", "dado": "O Brasil tem 3.000+ horas de sol por ano", "icone": "☀️"},
        {"titulo": "CAPACIDADE", "dado": "1 painel gera até 50 kWh/mês", "icone": "⚡"},
        {"titulo": "RETORNO", "dado": "Payback médio de 4-6 anos", "icone": "💰"},
    ])

    for i, d in enumerate(dados):
        clip_path = DIR_TMP / f"dado_{i}.mp4"
        motion.gerar_clip_infografico(
            d["titulo"], d["dado"], 5, clip_path,
            icone=d.get("icone", "☀️"), cor_fundo=cor_fundo
        )
        clips.append(clip_path)

    resumo_path = DIR_TMP / "resumo.mp4"
    resumo_texto = params.get("resumo", "ENERGIA SOLAR SE PAGA SOZINHA")
    motion.gerar_clip_texto(
        resumo_texto, 6, resumo_path,
        cor_fundo=cor_fundo, cor_texto=cor_primaria, fontsize=70
    )
    clips.append(resumo_path)

    cta_text = params.get("cta", marca["cta"]["padrao"])
    cta_path = DIR_TMP / "cta.mp4"
    motion.gerar_clip_cta(cta_text, 6, cta_path, cor_accent=cor_accent, cor_fundo=cor_fundo)
    clips.append(cta_path)

    musica = _escolher_musica("educational")
    motion.concatenar_clips(clips, output_path, musica_path=musica)
    return output_path


def gerar_short_processo(marca, template, params, output_path):
    """Gera short de passo a passo da instalação."""
    DIR_TMP.mkdir(parents=True, exist_ok=True)
    clips = []

    cor_fundo = obter_cor(marca, template.get("cor_fundo", "accent"))
    cor_primaria = marca["cores"]["primaria"]
    cor_accent = marca["cores"]["accent"]

    hook_text = params.get("hook", "COMO INSTALAR ENERGIA SOLAR? ⚡")
    hook_path = DIR_TMP / "hook.mp4"
    motion.gerar_clip_hook(hook_text, 3, hook_path, cor_fundo=cor_fundo)
    clips.append(hook_path)

    passos = params.get("passos", [
        "1. Análise do telhado",
        "2. Projeto personalizado",
        "3. Instalação (1-3 dias)",
        "4. Conexão à rede",
        "5. Economia começa!"
    ])

    for i, passo in enumerate(passos):
        clip_path = DIR_TMP / f"passo_{i}.mp4"
        motion.gerar_clip_texto(
            passo, 5, clip_path,
            cor_fundo=cor_fundo, cor_texto="white", fontsize=60
        )
        clips.append(clip_path)

    cta_text = params.get("cta", marca["cta"]["padrao"])
    cta_path = DIR_TMP / "cta.mp4"
    motion.gerar_clip_cta(cta_text, 7, cta_path, cor_accent=cor_accent, cor_fundo=cor_fundo)
    clips.append(cta_path)

    musica = _escolher_musica("upbeat")
    motion.concatenar_clips(clips, output_path, musica_path=musica)
    return output_path


def gerar_short_depoimento(marca, template, params, output_path):
    """Gera short de depoimento de cliente."""
    DIR_TMP.mkdir(parents=True, exist_ok=True)
    clips = []

    cor_fundo = obter_cor(marca, template.get("cor_fundo", "primaria"))
    cor_primaria = marca["cores"]["primaria"]
    cor_accent = marca["cores"]["accent"]

    hook_text = params.get("hook", "CLIENTE SATISFEITO 💛")
    hook_path = DIR_TMP / "hook.mp4"
    motion.gerar_clip_hook(hook_text, 3, hook_path, cor_primaria=cor_primaria, cor_fundo=cor_fundo)
    clips.append(hook_path)

    foto_cliente = params.get("foto_cliente")
    if foto_cliente and Path(foto_cliente).exists():
        foto_clip = DIR_TMP / "foto_cliente.mp4"
        motion.gerar_clip_foto(
            foto_cliente, 5, foto_clip,
            texto=params.get("nome_cliente", "CLIENTE MS ENERGY"),
            cor_fundo=cor_fundo
        )
        clips.append(foto_clip)

    depo_texto = params.get("depoimento", "Minha conta caiu 90%%!\nMelhor investimento da minha vida!")
    depo_path = DIR_TMP / "depoimento.mp4"
    motion.gerar_clip_texto(
        depo_texto, 8, depo_path,
        cor_fundo=cor_fundo, cor_texto="white", fontsize=50
    )
    clips.append(depo_path)

    resultado_path = DIR_TMP / "resultado.mp4"
    motion.gerar_clip_texto(
        params.get("resultado", "ECONOMIA REAL ✅"), 3, resultado_path,
        cor_fundo=cor_fundo, cor_texto=cor_primaria, fontsize=80
    )
    clips.append(resultado_path)

    cta_text = params.get("cta", marca["cta"]["padrao"])
    cta_path = DIR_TMP / "cta.mp4"
    motion.gerar_clip_cta(cta_text, 3, cta_path, cor_accent=cor_accent, cor_fundo=cor_fundo)
    clips.append(cta_path)

    musica = _escolher_musica("emotional")
    motion.concatenar_clips(clips, output_path, musica_path=musica)
    return output_path


TEMPLATE_GERADORES = {
    "economia": gerar_short_economia,
    "antes_depois": gerar_short_antes_depois,
    "dados": gerar_short_dados,
    "processo": gerar_short_processo,
    "depoimento": gerar_short_depoimento,
}


def _escolher_musica(mood):
    """Encontra música de fundo pelo mood. Retorna None se não tiver."""
    musicas_dir = DIR_ASSETS / "musicas"
    if not musicas_dir.exists():
        return None
    for ext in [".mp3", ".wav", ".m4a", ".ogg"]:
        candidatas = list(musicas_dir.glob(f"*{mood}*{ext}")) + list(musicas_dir.glob(f"*{ext}"))
        if candidatas:
            return str(random.choice(candidatas))
    return None


def gerar_short(template_id, params=None, output_dir=None, titulo=None):
    """Gera um short viral a partir de um template."""
    marca, templates_config = carregar_config()
    params = params or {}

    template_data = None
    for t in templates_config["templates"]:
        if t["id"] == template_id:
            template_data = t
            break

    if not template_data:
        print(f"ERRO: Template '{template_id}' não encontrado.")
        print(f"Templates disponíveis: {[t['id'] for t in templates_config['templates']]}")
        return None

    gerador = TEMPLATE_GERADORES.get(template_id)
    if not gerador:
        print(f"ERRO: Gerador para '{template_id}' não implementado.")
        return None

    output_dir = Path(output_dir) if output_dir else DIR_VIDEOS
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_titulo = (titulo or template_id).replace(" ", "_").replace(":", "")[:50]
    output_path = output_dir / f"ms_energy_{template_id}_{timestamp}.mp4"

    print(f"╔══════════════════════════════════════════════╗")
    print(f"║  MS Energy - Gerador de Shorts Virais       ║")
    print(f"╠══════════════════════════════════════════════╣")
    print(f"║  Template: {template_data['nome']:<33}║")
    print(f"║  Duração alvo: {template_data['duracao_s']}s{' ' * 28}║")
    print(f"║  Output: {output_path.name:<35}║")
    print(f"╚══════════════════════════════════════════════╝")

    DIR_TMP.mkdir(parents=True, exist_ok=True)

    try:
        resultado = gerador(marca, template_data, params, output_path)

        import subprocess
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)],
            capture_output=True, text=True
        )
        if r.returncode == 0:
            dur = float(r.stdout.strip())
            print(f"\n✅ Short gerado com sucesso!")
            print(f"   Duração: {dur:.1f}s")
            print(f"   Arquivo: {output_path}")

            sidecar = output_path.with_suffix(".json")
            meta = {
                "template": template_id,
                "titulo": titulo or template_data["nome"],
                "duracao_s": dur,
                "params": params,
                "gerado_em": datetime.now().isoformat(),
                "hashtags": marca.get("hashtags", []),
                "cta": params.get("cta", marca["cta"]["padrao"]),
            }
            with open(sidecar, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            print(f"   Sidecar: {sidecar.name}")
        else:
            print(f"\n❌ ERRO: ffprobe falhou ao validar o vídeo!")
            return None

        return resultado

    finally:
        motion.limpar_tmp()


def gerar_aleatorio(params=None, output_dir=None):
    """Gera um short de template aleatório com dados de exemplo."""
    templates_disponiveis = list(TEMPLATE_GERADORES.keys())
    template_id = random.choice(templates_disponiveis)

    exemplos = {
        "economia": {
            "valor_antes": str(random.choice([500, 600, 700, 800, 900, 1000, 1200])),
            "valor_depois": str(random.choice([35, 47, 58, 72, 89, 95])),
            "hook": random.choice([
                "CONTA DE LUZ: ABSURDO → QUASE ZERO",
                "PARE de jogar dinheiro fora ☀️",
                "CHOCANTE: sua conta pode cair 90%",
            ]),
        },
        "antes_depois": {
            "hook": random.choice([
                "OLHA ESSA TRANSFORMAÇÃO 👇",
                "TELHADO ANTIGO → USINA SOLAR ⚡",
                "INACREDITÁVEL a diferença!",
            ]),
        },
        "dados": {
            "hook": random.choice([
                "VOCÊ SABIA? ☀️",
                "3 FATOS sobre energia solar",
                "O SOL paga sua conta!",
            ]),
        },
        "processo": {
            "hook": random.choice([
                "COMO INSTALAR ENERGIA SOLAR? ⚡",
                "5 PASSOS pra zerar sua conta",
                "É mais fácil do que parece!",
            ]),
        },
        "depoimento": {
            "hook": "CLIENTE SATISFEITO 💛",
            "depoimento": random.choice([
                "Minha conta caiu 90%%!",
                "Melhor investimento da vida!",
                "Deveria ter feito antes!",
            ]),
        },
    }

    params_final = exemplos.get(template_id, {})
    if params:
        params_final.update(params)

    print(f"\n🎲 Template sorteado: {template_id}")
    return gerar_short(template_id, params_final, output_dir)


def main():
    parser = argparse.ArgumentParser(description="MS Energy - Gerador de Shorts Virais")
    parser.add_argument("--template", "-t", choices=list(TEMPLATE_GERADORES.keys()) + ["aleatorio"],
                        default="aleatorio", help="Template do short")
    parser.add_argument("--titulo", help="Título do short")
    parser.add_argument("--output", "-o", default=str(DIR_VIDEOS), help="Diretório de saída")
    parser.add_argument("--valor-antes", help="Valor da conta antes (template economia)")
    parser.add_argument("--valor-depois", help="Valor da conta depois (template economia)")
    parser.add_argument("--hook", help="Texto do hook (primeiros segundos)")
    parser.add_argument("--cta", help="Texto do CTA final")
    parser.add_argument("--foto-antes", help="Foto antes (template antes_depois)")
    parser.add_argument("--foto-depois", help="Foto depois (template antes_depois)")
    parser.add_argument("--lote", "-n", type=int, default=1, help="Quantidade de shorts a gerar")

    args = parser.parse_args()

    params = {}
    if args.valor_antes:
        params["valor_antes"] = args.valor_antes
    if args.valor_depois:
        params["valor_depois"] = args.valor_depois
    if args.hook:
        params["hook"] = args.hook
    if args.cta:
        params["cta"] = args.cta
    if args.foto_antes:
        params["foto_antes"] = args.foto_antes
    if args.foto_depois:
        params["foto_depois"] = args.foto_depois

    for i in range(args.lote):
        if args.lote > 1:
            print(f"\n{'='*50}")
            print(f"  Short {i+1}/{args.lote}")
            print(f"{'='*50}")

        if args.template == "aleatorio":
            gerar_aleatorio(params, args.output)
        else:
            gerar_short(args.template, params, args.output, args.titulo)


if __name__ == "__main__":
    main()
