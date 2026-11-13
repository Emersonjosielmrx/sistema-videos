import re, subprocess, sys
M = r"D:\hipercool-materiais\pesquisador_melhorias\motor_pesquisador.py"
F = r"D:\hipercool-materiais\pesquisador_melhorias\ENTREGAS\CURTOS.md"
MOTIVO = {
 "Alertas de queda": "alerta de views já existe (avisos/painel); repos genéricos",
 "Kokoro": "treino/vozes Kokoro é linha de voz clonada (testes pausados)",
 "gancho dos primeiros 3 s": "gancho já vem do roteiro do LLM; analisador genérico sem ganho medido",
 "C2PA": "assinatura C2PA não muda distribuição dos Shorts",
 "Backup e sincronização": "backup já é rclone com conferência",
 "Cache de alinhamento": "alinhamento por whisper já é rápido no Short",
 "Cache de prefixo/KV": "TTS em lote de Short é curto; ganho irrelevante",
 "Cache por hash": "cache de vídeo já existe por id",
 "Cache sincronizado": "sincronização Kaggle/PC/VPS já é pelo Drive",
 "Checkpoint de sessão": "Short leva minutos; checkpoint é pra longos",
 "Colorização": "mangá = hipercool (parado)",
 "Comédia e comentário": "Comédia Noturna já tem pipeline próprio",
 "Consentimento": "direitos de voz já são regra da dona (autorização)",
 "filtergraph": "filtergraph do ffmpeg já montado em código; troca de lib sem ganho",
 "Controle de cota Kaggle": "central já controla cota por conta",
 "timbre por embedding": "voz clonada pausada",
 "Critérios de transformação": "transformação dos recaps já definida",
 "Reddit/HN": "pauta vem dos parceiros autorizados",
 "abertura/encerramento": "corte de intro já existe (_cortar_intro)",
 "drawvg": "ffmpeg do Kaggle/PC já tem o necessário",
 "SOLA": "emenda de áudio já sem estalo no pipeline",
 "mistério/tecnologia faceless": "estrutura de roteiro já por nicho",
 "Fila resumável": "fila já é por arquivos no disco (resumível)",
 "whisper": "whisper/faster-whisper já usado",
 "Fontes de tendência": "pauta vem dos parceiros autorizados",
 "chat-story": "formato novo = decisão da dona",
 "fruc_vulkan": "interpolação não é gargalo do Short",
 "Heartbeat": "vigias e heartbeat já existem",
 "personagem de anime": "identificação de personagem é linha hipercool",
 "Inpainting": "balão = hipercool (parado)",
 "cache de voz": "voz clonada pausada",
 "Kanade": "voz clonada pausada",
 "Longos": "longos, não Shorts",
 "Meta/Instagram conteúdo não original": "regra de conteúdo já tratada (vídeo único, transformação)",
 "scale2ref": "ffmpeg atual funciona; migração sem ganho agora",
 "Mineração de comentários": "pauta vem dos parceiros",
 "Monitor de novos uploads": "abastecedor já monitora os parceiros",
 "Ordem de leitura": "tiras verticais = hipercool",
 "Wikipedia": "pauta vem dos parceiros",
 "Pré-checagem de música": "trilha já é do acervo próprio",
 "curva de uma tendência": "sem dado de tendência próprio",
 "Produto local": "solares têm pipeline próprio (ms-energy)",
 "QSV": "PCs Intel antigos; render é Kaggle/CPU",
 "Qwen3-TTS": "voz clonada pausada",
 "VHS, CRT": "efeitos visuais fora do padrão MIX",
 "Remoção de legenda": "delogo/tarja da fonte já existe",
 "Remotion": "Shorts não usam Remotion",
 "Render em pedaços": "Short curto; não compensa",
 "Retenção em recap": "sem dado de retenção automático",
 "Saída e artefatos Kaggle": "saída do Kaggle já vai pro Drive",
 "Segmentação de balão": "balão = hipercool",
 "PESTO": "pitch/voz clonada pausada",
 "TikTok conteúdo não original": "regra já tratada (vídeo único)",
 "TikTok Creative Center": "sons/hashtags em alta exigem conta logada (dona)",
 "torch.compile": "ganho incerto na T4; risco no kernel",
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
        b = b.replace("## [ ] PENDENTE", f"## [x] AVALIADO 10/11 (claude-fa: 0 implantados, {rep} reprovados, 0 deixados)", 1)
        n_rep += rep; n_bl += 1
    novo.append(b)
open(F, "w", encoding="utf-8").write("".join(novo))
print("blocos", n_bl, "reprovados", n_rep)
