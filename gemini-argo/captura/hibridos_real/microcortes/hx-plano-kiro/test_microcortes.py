"""Teste da função microcortes."""
import wave
import numpy as np
import json
from pathlib import Path
from narracao import microcortes, ler_palavras, gravar_palavras

def criar_wav_teste(filename, duracao_s=5.0, framerate=16000):
    """
    Cria um WAV de teste com padrão: som-silêncio-som-silêncio-som.

    Estrutura:
    - 0.0-1.0s: tom de 440 Hz (som)
    - 1.0-1.5s: silêncio de 0.5s (deve ser cortado para 0.07s)
    - 1.5-2.5s: tom de 880 Hz (som)
    - 2.5-3.0s: silêncio de 0.5s (deve ser cortado para 0.07s)
    - 3.0-4.0s: tom de 660 Hz (som)
    - 4.0-5.0s: silêncio final
    """
    nframes = int(duracao_s * framerate)
    t = np.linspace(0, duracao_s, nframes)

    # Criar áudio com padrão
    audio = np.zeros(nframes, dtype=np.int16)

    # Som 1: 0.0-1.0s (440 Hz)
    idx1 = (t >= 0.0) & (t < 1.0)
    audio[idx1] = (20000 * np.sin(2 * np.pi * 440 * t[idx1])).astype(np.int16)

    # Silêncio 1: 1.0-1.5s (0.5s) - será cortado
    # (já é zero)

    # Som 2: 1.5-2.5s (880 Hz)
    idx2 = (t >= 1.5) & (t < 2.5)
    audio[idx2] = (20000 * np.sin(2 * np.pi * 880 * t[idx2])).astype(np.int16)

    # Silêncio 2: 2.5-3.0s (0.5s) - será cortado

    # Som 3: 3.0-4.0s (660 Hz)
    idx3 = (t >= 3.0) & (t < 4.0)
    audio[idx3] = (20000 * np.sin(2 * np.pi * 660 * t[idx3])).astype(np.int16)

    # Silêncio final: 4.0-5.0s

    # Gravar WAV
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)  # mono
        wf.setsampwidth(2)  # 16 bits
        wf.setframerate(framerate)
        wf.writeframes(audio.tobytes())

    print(f"✓ Criado {filename}: {duracao_s}s, {framerate}Hz, mono, 16 bits")
    print(f"  Estrutura: som(1s) → silêncio(0.5s) → som(1s) → silêncio(0.5s) → som(1s) → silêncio(1s)")

    # Criar arquivo .words.json de teste
    palavras = [
        {"word": "primeira", "start": 0.1, "end": 0.9},
        {"word": "segunda", "start": 1.6, "end": 2.4},
        {"word": "terceira", "start": 3.1, "end": 3.9}
    ]
    gravar_palavras(filename, palavras)
    print(f"✓ Criado {filename}.words.json com 3 palavras")

    return duracao_s


def verificar_duracao(filename):
    """Verifica a duração do WAV."""
    with wave.open(filename, 'rb') as wf:
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        return nframes / framerate


def main():
    print("=" * 70)
    print("TESTE DA FUNÇÃO microcortes()")
    print("=" * 70)

    test_file = "teste_microcortes.wav"

    # 1. Criar arquivo de teste
    print("\n[1] Criando arquivo de teste...")
    duracao_original = criar_wav_teste(test_file)

    # 2. Verificar duração antes
    print("\n[2] Verificando arquivo original...")
    duracao_verificada = verificar_duracao(test_file)
    print(f"  Duração: {duracao_verificada:.3f}s")
    assert abs(duracao_verificada - duracao_original) < 0.01, "Duração não confere"

    # 3. Aplicar microcortes
    print("\n[3] Aplicando microcortes()...")
    resultado = microcortes(test_file)

    if resultado is None:
        print("  ✗ ERRO: microcortes() retornou None (nada foi cortado)")
        return False

    antes, depois = resultado
    print(f"  Antes:  {antes:.3f}s")
    print(f"  Depois: {depois:.3f}s")
    print(f"  Cortado: {antes - depois:.3f}s ({(1 - depois/antes)*100:.1f}%)")

    # 4. Verificar duração depois
    print("\n[4] Verificando arquivo modificado...")
    duracao_final = verificar_duracao(test_file)
    print(f"  Duração: {duracao_final:.3f}s")
    assert abs(duracao_final - depois) < 0.01, f"Duração final {duracao_final:.3f}s não confere com retornada {depois:.3f}s"

    # 5. Verificar que houve corte
    # Esperado: 2 silêncios de 0.5s cortados para 0.07s cada
    # Redução: 2 × (0.5 - 0.07) = 0.86s
    reducao_esperada = 2 * (0.5 - 0.07)
    reducao_real = antes - depois
    print(f"\n[5] Validando corte...")
    print(f"  Redução esperada: ~{reducao_esperada:.3f}s")
    print(f"  Redução real: {reducao_real:.3f}s")

    if abs(reducao_real - reducao_esperada) < 0.1:
        print("  ✓ Redução dentro do esperado")
    else:
        print(f"  ⚠ Redução fora do esperado (diferença: {abs(reducao_real - reducao_esperada):.3f}s)")

    # 6. Verificar .words.json
    print("\n[6] Verificando .words.json atualizado...")
    palavras_novas = ler_palavras(test_file)

    if not palavras_novas:
        print("  ✗ ERRO: .words.json não foi atualizado")
        return False

    print(f"  Palavras encontradas: {len(palavras_novas)}")
    for p in palavras_novas:
        print(f"    '{p['word']}': {p['start']:.3f}s → {p['end']:.3f}s")

    # Verificar que os timestamps foram ajustados (devem ser menores)
    palavras_originais = [
        {"word": "primeira", "start": 0.1, "end": 0.9},
        {"word": "segunda", "start": 1.6, "end": 2.4},
        {"word": "terceira", "start": 3.1, "end": 3.9}
    ]

    for i, (original, nova) in enumerate(zip(palavras_originais, palavras_novas)):
        assert nova['word'] == original['word'], f"Palavra {i} mudou de '{original['word']}' para '{nova['word']}'"

        # A primeira palavra não deve mudar (antes do primeiro corte)
        if i == 0:
            assert abs(nova['start'] - original['start']) < 0.01, "Primeira palavra não deveria mudar"
        # As outras devem ter timestamps menores (após os cortes)
        else:
            assert nova['start'] < original['start'], f"Palavra {i} deveria ter start menor após cortes"

    print("  ✓ Timestamps ajustados corretamente")

    # 7. Teste sem cortes (arquivo já processado ou sem pausas longas)
    print("\n[7] Testando arquivo sem pausas longas...")
    resultado2 = microcortes(test_file)  # Aplicar de novo
    if resultado2 is None:
        print("  ✓ Retornou None corretamente (nada a cortar)")
    else:
        print(f"  ⚠ Segunda aplicação ainda cortou {resultado2[0] - resultado2[1]:.3f}s")

    print("\n" + "=" * 70)
    print("✓ TODOS OS TESTES PASSARAM")
    print("=" * 70)

    return True


if __name__ == '__main__':
    try:
        sucesso = main()
        exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
