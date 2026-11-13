import wave
import numpy as np
from pathlib import Path
from narracao import microcortes, ler_palavras

def test_microcortes():
    wav_path = Path("test_audio.wav")
    framerate = 16000

    # Gerar 1 segundo de fala (senóide), 1 segundo de silêncio, 1 segundo de fala
    t_fala = np.linspace(0, 1.0, int(framerate * 1.0), endpoint=False)
    fala1 = (np.sin(2 * np.pi * 440 * t_fala) * 16384).astype(np.int16)

    silencio = np.zeros(int(framerate * 1.0), dtype=np.int16)

    t_fala2 = np.linspace(0, 1.0, int(framerate * 1.0), endpoint=False)
    fala2 = (np.sin(2 * np.pi * 880 * t_fala2) * 16384).astype(np.int16)

    audio = np.concatenate([fala1, silencio, fala2])

    # Gravar wav
    with wave.open(str(wav_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        wf.writeframes(audio.tobytes())

    # Criar words.json correspondente
    import json
    palavras = [
        {"word": "teste1", "start": 0.1, "end": 0.9},
        {"word": "teste2", "start": 2.1, "end": 2.9}
    ]
    Path(str(wav_path) + ".words.json").write_text(json.dumps(palavras, ensure_ascii=False), "utf-8")

    print(f"Arquivo de teste criado: {wav_path}")
    print(f"Duração original: {len(audio)/framerate:.2f}s")
    print(f"Palavras originais: {palavras}")

    dur_antes, dur_depois = microcortes(wav_path, gap_s=0.07)
    print(f"\nAntes: {dur_antes:.2f}s, Depois: {dur_depois:.2f}s")
    print(f"Redução: {dur_antes - dur_depois:.2f}s ({(1 - dur_depois/dur_antes)*100:.1f}%)")

    # Verificar words.json atualizado
    novas_palavras = ler_palavras(wav_path)
    print(f"\nPalavras após microcortes:")
    for p in novas_palavras:
        print(f"  {p['word']}: {p['start']:.3f}s - {p['end']:.3f}s")

    # Limpar
    if wav_path.exists():
        wav_path.unlink()
    if Path(str(wav_path) + ".words.json").exists():
        Path(str(wav_path) + ".words.json").unlink()

    print("\nTeste concluído com sucesso!")

if __name__ == "__main__":
    test_microcortes()
