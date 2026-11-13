import subprocess, sys
M = r"D:\hipercool-materiais\pesquisador_melhorias\motor_pesquisador.py"
R = {
 "JuneYaooo/rea-video": "análise reversa de vídeo pronto; não gera nem melhora o Short",
 "ogkalu2/comic-translate": "tradução de mangá; Shorts de parceiro usam vídeo, não página",
 "pedrovgs/DeepPanel": "painel de mangá — linha hipercool (parada), não CURTOS",
 "MechTechnology/SmartStitch": "costura raws de manhwa — hipercool parado",
 "meangrinch/MangaTranslator": "tradução de mangá; fora da linha",
 "JHU-LCAP/FlexSED": "detecção de eventos sonoros; corte por fala já resolve no Short",
 "BTawaifi/Audio-DeSilencer": "silêncio em gravação longa; TTS do Short já sai sem pausa morta",
 "studio-dots-ai/dots.tts.edit-data-pipeline": "pipeline de dataset de TTS; não treinamos voz",
 "Jeevav62/voxpolish": "limpeza de dataset de TTS; não treinamos voz",
 "xytime/video-progress-bar-cli": "barra de capítulos é para longos, não Shorts",
 "DrBanshan/chapter-progress-bar-plus": "idem: longos",
 "ChecheChat/video-progress-bar-skill": "CapCut/longos",
 "ApeCodeAI/vmarker": "capítulos de longos",
 "Violinet-tech/seamless-loop-video": "stream ambiente com MiniMax H3; não é Short",
 "Zephurion/mp3-loop": "loop de 1 h de música; não é Short",
 "micilini/EternalLoop": "player de música Windows",
 "libraz/libsonare": "motor de áudio/DAW; mix do Short já é ffmpeg com ducking",
 "libraz/bpm-detector": "BPM/tom de mix longo; fora da linha",
}
for repo, motivo in R.items():
    r = subprocess.run([sys.executable, M, "reprovar", repo, motivo, "CURTOS"], capture_output=True, text=True)
    if r.returncode:
        print("FALHA", repo, (r.stderr or r.stdout)[-120:])
print("fim", len(R))
