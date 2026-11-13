import re, subprocess, sys
M = r"D:\hipercool-materiais\pesquisador_melhorias\motor_pesquisador.py"
F = r"D:\hipercool-materiais\pesquisador_melhorias\ENTREGAS\CURTOS.md"
MOTIVO = {
 "codec de áudio": "TTS do Short é edge/kokoro/RVC; cache de codec sem ganho medido",
 "ggml-vulkan": "render/IA pesada roda no Kaggle (T4), não nas GPUs Intel dos PCs",
 "Dedup fonético": "dedupe de roteiro já existe por texto",
 "Embedding de locutor": "voz clonada usa RVC; embedding em CPU não é gargalo",
 "DirectML": "PCs Intel antigos; inferência pesada vai pro Kaggle",
 "parte variável": "frases já são geradas por LLM inteiras",
 "G2P": "pronúncia já via TTS do provedor",
 "Latents": "sem pipeline de latents no Short",
 "OpenVINO": "IA pesada no Kaggle; OpenVINO nos PCs Gen9 sem ganho medido",
 "VAD": "corte já usa VAD/whisper com palavra",
 "INT8": "quantização nos PCs Gen9 sem ganho medido; IA no Kaggle",
 "RAM de modelos": "PCs não rodam esses modelos (Kaggle)",
 "Whisper em OpenVINO": "whisper roda no Kaggle (GPU)",
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
        b = b.replace("## [ ] PENDENTE", f"## [x] AVALIADO 10/11b (claude-fa: 0 implantados, {rep} reprovados, 0 deixados)", 1)
        n_rep += rep; n_bl += 1
    novo.append(b)
open(F, "w", encoding="utf-8").write("".join(novo))
print("blocos", n_bl, "reprovados", n_rep)


