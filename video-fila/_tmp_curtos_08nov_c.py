import re, subprocess, sys
M = r"D:\hipercool-materiais\pesquisador_melhorias\motor_pesquisador.py"
F = r"D:\hipercool-materiais\pesquisador_melhorias\ENTREGAS\CURTOS.md"
MOTIVO = {
 "Upload e agenda": "postagem já é por navegador do cofre/HTTP com perfil fixo; trocar o driver arrisca contas sem a dona",
 "Corte em ponto de tensão": "sentimento léxico em inglês; o corte usa o LLM no roteiro",
 "Legenda original do YouTube": "parceiros Shorts quase nunca têm legenda; whisper já transcreve",
 "Chat e comentários": "chat de live/danmaku; parceiros são Shorts sem chat",
 "Eventos de áudio": "Shorts narrados não dependem de risada/aplauso",
 "Avaliar o seletor": "benchmark acadêmico; sem rótulos próprios",
 "Bordas de corte": "turn-taking de voz em tempo real; corte do Short já usa VAD+fim de frase",
 "Variante por plataforma": "postadores já têm limites por plataforma; ferramentas de agenda/rotulagem genéricas",
 "Facecam": "canais são dark (sem rosto); facecam não se aplica",
 "Visemas": "linha sem avatar falante em pt-BR ativa",
 "QA de render longo": "longos, não Shorts",
 "Roteiro para linha do tempo": "o roteiro já sai em JSON validado; biblioteca extra sem ganho",
 "Runtimes 2D": "Shorts são ffmpeg/Remotion; sem animação Lottie/Rive no pipeline",
 "Render determinístico": "sem WebGL no pipeline dos Shorts",
 "See-through": "decomposição de ilustração — hipercool parado",
 "Apresentador de produto": "cabeça falante pesada; produto já usa clone de foto + Veo",
 "Publicar traduções": "vídeo único por canal: não publicamos tradução de metadados",
 "Capítulos": "capítulos são de longos",
 "SEO por idioma": "Yandex/Rússia fora do público",
 "Checagem de tradução": "Shorts não são traduzidos (vídeo único por canal)",
 "Análise de títulos": "modelagem de tópicos de títulos; sem dataset de views próprio ainda",
 "Viewed vs swiped": "sem dado viewed/swiped (Studio só pelo navegador logado)",
 "Loop perfeito": "loop de corte de quadro; loop narrado depende do roteiro",
 "Barra de progresso": "longos",
 "Loop sem emenda": "stream ambiente, não Short",
 "Títulos de capítulo": "longos/idioma fixo por canal",
 "Hashtags": "já temos hashtags por plataforma",
 "Dados de título": "sem repos",
}
DEIXA = {"jrgillick/laughter-detection": "detector de risada pode marcar o pico da reação na Comédia Noturna; testar lá (linha comentarios)"}
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
            if repo in DEIXA:
                b = b.replace(f"github.com/{repo}", f"github.com/{repo} [DEIXADO 08/11: {DEIXA[repo]}]", 1)
                continue
            r = subprocess.run([sys.executable, M, "reprovar", repo, mot, "CURTOS"], capture_output=True, text=True)
            if r.returncode:
                print("FALHA", repo, (r.stderr or r.stdout)[-100:])
            rep += 1
        dx = sum(1 for d in DEIXA if d in b)
        b = b.replace("## [ ] PENDENTE", f"## [x] AVALIADO 08/11 (claude-fa: 0 implantados, {rep} reprovados, {dx} deixados)", 1)
        n_rep += rep; n_bl += 1
    novo.append(b)
open(F, "w", encoding="utf-8").write("".join(novo))
print("blocos", n_bl, "reprovados", n_rep)
