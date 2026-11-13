"""Teste da função microcortes."""
import wave
import numpy as np
import json
from pathlib import Path
from narracao import microcortes, ler_palavras

def criar_wav_teste(caminho, taxa=16000):
    """Cria um WAV de teste com fala-pausa-fala-pausa-fala."""
    # Gerar tom de 440 Hz para simular fala (500ms cada)
    duracao_fala = 0.5
    duracao_pausa_curta = 0.05  # 50ms - não deve ser cortada
    duracao_pausa_longa = 0.3   # 300ms - deve ser reduzida para 70ms

    t_fala = np.linspace(0, duracao_fala, int(taxa * duracao_fala))
    fala = (np.sin(2 * np.pi * 440 * t_fala) * 16000).astype(np.int16)

    pausa_curta = np.zeros(int(taxa * duracao_pausa_curta), dtype=np.int16)
    pausa_longa = np.zeros(int(taxa * duracao_pausa_longa), dtype=np.int16)

    # Sequência: fala - pausa curta - fala - pausa longa - fala
    audio = np.concatenate([fala, pausa_curta, fala, pausa_longa, fala])

    # Gravar WAV mono 16 bits
    with wave.open(caminho, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16 bits
        wf.setframerate(taxa)
        wf.writeframes(audio.tobytes())

    duracao_original = len(audio) / taxa
    print(f"✓ Criado {caminho}")
    print(f"  Duração: {duracao_original:.3f}s")
    print(f"  Estrutura: fala(500ms) - pausa(50ms) - fala(500ms) - pausa(300ms) - fala(500ms)")

    return duracao_original

def criar_words_teste(caminho_wav):
    """Cria um .words.json de teste."""
    palavras = [
        {"word": "primeira", "start": 0.1, "end": 0.4},
        {"word": "segunda", "start": 0.65, "end": 0.95},
        {"word": "terceira", "start": 1.4, "end": 1.7}
    ]

    caminho_json = Path(str(caminho_wav) + ".words.json")
    caminho_json.write_text(json.dumps(palavras, ensure_ascii=False), "utf-8")
    print(f"✓ Criado {caminho_json}")
    print(f"  Palavras: {[p['word'] for p in palavras]}")

    return palavras

def verificar_resultado(caminho_wav, duracao_original, palavras_original):
    """Verifica o resultado do microcorte."""
    print("\n--- Aplicando microcortes ---")
    resultado = microcortes(caminho_wav)

    if resultado is None:
        print("✗ ERRO: Deveria ter feito cortes mas retornou None")
        return False

    duracao_antes, duracao_depois = resultado
    tempo_economizado = duracao_antes - duracao_depois

    print(f"✓ Resultado: {resultado}")
    print(f"  Antes: {duracao_antes:.3f}s")
    print(f"  Depois: {duracao_depois:.3f}s")
    print(f"  Economizado: {tempo_economizado:.3f}s ({tempo_economizado/duracao_antes*100:.1f}%)")

    # Verificar que o arquivo foi modificado
    with wave.open(caminho_wav, 'rb') as wf:
        nova_duracao = wf.getnframes() / wf.getframerate()

    if abs(nova_duracao - duracao_depois) > 0.001:
        print(f"✗ ERRO: Duração reportada ({duracao_depois:.3f}s) != duração real ({nova_duracao:.3f}s)")
        return False

    # Verificar que houve redução (pausa longa de 300ms -> 70ms = ~230ms economizados)
    if tempo_economizado < 0.2 or tempo_economizado > 0.25:
        print(f"⚠ AVISO: Tempo economizado ({tempo_economizado:.3f}s) fora do esperado (~0.23s)")

    # Verificar timestamps das palavras
    palavras_novas = ler_palavras(caminho_wav)
    if palavras_novas:
        print("\n--- Timestamps atualizados ---")
        for i, (antiga, nova) in enumerate(zip(palavras_original, palavras_novas)):
            ajuste = antiga['start'] - nova['start']
            print(f"  {nova['word']}: {antiga['start']:.3f}-{antiga['end']:.3f} → {nova['start']:.3f}-{nova['end']:.3f} (Δ{ajuste:+.3f}s)")

    print("\n✓ Teste PASSOU")
    return True

def teste_sem_cortes():
    """Testa arquivo que não precisa de cortes."""
    print("\n" + "="*60)
    print("TESTE 2: Arquivo sem pausas longas")
    print("="*60)

    caminho = "teste_sem_pausas.wav"
    taxa = 16000

    # Criar áudio contínuo
    t = np.linspace(0, 1.0, taxa)
    audio = (np.sin(2 * np.pi * 440 * t) * 16000).astype(np.int16)

    with wave.open(caminho, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(taxa)
        wf.writeframes(audio.tobytes())

    print(f"✓ Criado {caminho} (1.0s de áudio contínuo)")

    resultado = microcortes(caminho)

    if resultado is None:
        print("✓ Retornou None corretamente (nada a cortar)")
        return True
    else:
        print(f"✗ ERRO: Deveria retornar None mas retornou {resultado}")
        return False

def main():
    print("="*60)
    print("TESTE 1: Arquivo com pausas longas")
    print("="*60)

    caminho_wav = "teste_microcortes.wav"

    # Criar arquivo de teste
    duracao_original = criar_wav_teste(caminho_wav)
    palavras_original = criar_words_teste(caminho_wav)

    # Aplicar e verificar
    sucesso1 = verificar_resultado(caminho_wav, duracao_original, palavras_original)

    # Teste 2
    sucesso2 = teste_sem_cortes()

    if sucesso1 and sucesso2:
        print("\n" + "="*60)
        print("TODOS OS TESTES PASSARAM ✓")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("ALGUNS TESTES FALHARAM ✗")
        print("="*60)

if __name__ == "__main__":
    main()
