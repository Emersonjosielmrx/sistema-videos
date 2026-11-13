import re, subprocess, sys
M = r"D:\hipercool-materiais\pesquisador_melhorias\motor_pesquisador.py"
F = r"D:\hipercool-materiais\pesquisador_melhorias\ENTREGAS\CURTOS.md"
MOTIVO = {
 "A/B": "sem dado de retenção por vídeo automático (Studio só pelo navegador logado da dona)",
 "Analytics por OAuth": "OAuth só leitura já existe (tokens noturnos); repos genéricos sem ganho",
 "ublagem": "vídeo único por canal: não dublamos nem reaproveitamos em outro idioma",
 "radução": "Shorts não são traduzidos (vídeo único por canal)",
 "Tradutores": "Shorts não são traduzidos",
 "Glossário": "consistência de nomes de obra = hipercool (parado)",
 "Camada persistente": "marca/cartão já é overlay fixo no ffmpeg",
 "Coleta pública": "baixador já usa yt-dlp com pausa (ytdlp_vez); RSS sem ganho",
 "Comentário e DM": "resposta/DM automático arrisca bloqueio das contas",
 "Comentários como fonte": "pauta vem do vídeo do parceiro, não de comentários",
 "Postar comentário": "comentário automático arrisca bloqueio",
 "Rascunho de resposta": "resposta a comentário é humana",
 "Pergunta fixada": "comentário fixado automático arrisca bloqueio",
 "CTA": "CTA já existe no roteiro; repos genéricos",
 "Dailymotion": "plataforma nova = decisão da dona (contas/login)",
 "Facebook": "plataforma nova = decisão da dona",
 "Kwai": "plataforma nova = decisão da dona",
 "TikTok em 2026": "artigos de ranking, sem código aplicável",
 "Dessincronia": "legenda MIX já alinha por whisper com palavra",
 "Duas T4": "Short cabe em 1 T4; 2 GPUs só complica o kernel",
 "ETL": "métricas já ficam em json/painel; DuckDB sem ganho",
 "Exportar analytics": "export do TikTok Studio exige navegador logado (dona)",
 "Exportar CSV": "export do YouTube Studio exige navegador logado (dona)",
 "Instagram Insights": "navegador logado; risco às contas",
 "Instagram Reels, Trial": "Trial Reels/Collabs precisa de teste com a dona (collabs já tem tarefa)",
 "Vulkan": "render do Short já é CPU/NVENC; libplacebo sem ganho",
 "NVENC": "Kaggle já usa ENCODER_GPU",
 "TensorRT": "conversão ONNX/TensorRT é risco sem ganho medido",
 "xfade": "transições já no ffmpeg; xfade em GPU não é gargalo",
 "Render paralelo": "Short tem 30-60 s; pedaços+concat não compensa",
 "Regressão de render": "qa.json já confere cada render",
 "Frequência ideal": "tetos por conta já definidos pela dona (rampa)",
 "Horários de postagem": "horário de pico por país já existe",
 "Gestão multi-conta": "regra da dona: 1 conta por IP, já aplicada",
 "Legenda/texto queimado": "delogo/tarja da legenda da fonte já existe",
 "Línguas com pouca": "vídeo único por canal; idiomas = decisão da dona",
 "LLM com visão": "QA visual já usa modelo de visão",
 "Loudness": "loudnorm -14 LUFS já aplicado",
 "Nudez": "censura por partes já existe",
 "Pré-upload": "postadores já checam formato por plataforma",
}
t = open(F, encoding="utf-8").read()
blocos = re.split(r"(?m)^(?=## )", t)
n_rep = n_bl = 0
novo = []
for b in blocos:
    if b.startswith("## [ ] PENDENTE"):
        titulo = b.split("\n", 1)[0]
        mot = next((v for k, v in MOTIVO.items() if k in titulo), "fora do escopo dos Shorts")
        rep = 0
        for repo in dict.fromkeys(re.findall(r"github\.com/([\w.\-]+/[\w.\-]+)", b)):
            r = subprocess.run([sys.executable, M, "reprovar", repo, mot, "CURTOS"], capture_output=True, text=True)
            if r.returncode:
                print("FALHA", repo, (r.stderr or r.stdout)[-100:])
            rep += 1
        b = b.replace("## [ ] PENDENTE", f"## [x] AVALIADO 09/11 (claude-fa: 0 implantados, {rep} reprovados, 0 deixados)", 1)
        n_rep += rep; n_bl += 1
    novo.append(b)
open(F, "w", encoding="utf-8").write("".join(novo))
print("blocos", n_bl, "reprovados", n_rep)
