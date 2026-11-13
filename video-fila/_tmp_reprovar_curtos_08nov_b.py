import subprocess, sys
M = r"D:\hipercool-materiais\pesquisador_melhorias\motor_pesquisador.py"
R = {
 "pemistahl/lingua-py": "títulos de capítulo são de longos; Short não tem capítulo e a língua do canal é fixa",
 "zafercavdar/fasttext-langdetect": "idem: língua já é conhecida por canal",
 "cisnlp/GlotScript": "capítulos multilíngues = longos",
 "blip-box/confusable": "sem uso em Shorts",
 "cisnlp/GlotLID": "língua já é fixa por canal",
 "cisnlp/MaskLID": "code-switching acadêmico, sem uso",
 "TigreGotico/linguonnx": "língua já é fixa por canal",
 "Unbabel/COMET": "avaliação de tradução; Shorts não reaproveitam tradução (vídeo único por canal)",
 "googlefonts/gftools": "ferramenta de fontes; MIX já tem fonte definida",
 "jquast/wcwidth": "largura de terminal, sem uso em vídeo",
 "FireRedTeam/FireRedVAD": "mid-roll é de longos; Short não tem anúncio no meio",
 "ina-foss/inaSpeechSegmenter": "mid-roll/longos",
 "retkowski/chunkseg": "avaliação de capítulos de longos",
}
for repo, motivo in R.items():
    r = subprocess.run([sys.executable, M, "reprovar", repo, motivo, "CURTOS"], capture_output=True, text=True)
    if r.returncode:
        print("FALHA", repo, (r.stderr or r.stdout)[-120:])
print("fim", len(R))
