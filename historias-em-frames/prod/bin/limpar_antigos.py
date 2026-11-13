import os
import glob
import time

def main():
    from hp_common import VIDEOS_DIR
    base_dir = str(VIDEOS_DIR)  # saida em hipercool-materiais
    if not os.path.exists(base_dir):
        return

    now = time.time()
    one_day = 86400  # segundos em 1 dia

    # 1. Limpar Quarentena (> 1 dia)
    quarantine_dir = os.path.join(base_dir, "_quarantine")
    if os.path.exists(quarantine_dir):
        for f in os.listdir(quarantine_dir):
            path = os.path.join(quarantine_dir, f)
            if os.path.isfile(path) and now - os.path.getmtime(path) > one_day:
                os.remove(path)
                print(f"[Quarentena] Removido: {f}")

    # 2. Limpar versões intermediárias antigas nas pastas de história
    for root, dirs, files in os.walk(base_dir):
        if "_quarantine" in root or "_APROVADOS" in root:
            continue

        # Filtramos arquivos que são mp4 finais (ignoramos shorts e _ULTIMO para lógica base)
        mp4_files = []
        for f in files:
            if f.endswith(".mp4") and "FINAL" in f and "ULTIMO" not in f:
                mp4_files.append(os.path.join(root, f))

        # Se tiver mais de 1 versão de vídeo gerada na mesma pasta...
        if len(mp4_files) > 1:
            # Ordenar por tempo de modificação, do mais antigo pro mais novo
            mp4_files.sort(key=os.path.getmtime)

            # Deletar todos exceto o útimo gerado, se eles tiverem mais de 1 dia de vida
            for old_mp4 in mp4_files[:-1]:
                if not os.path.exists(old_mp4):
                    continue
                if now - os.path.getmtime(old_mp4) > one_day:
                    try:
                        os.remove(old_mp4)
                        print(f"[Limpeza de Versão] Removido mp4 intermediário: {os.path.basename(old_mp4)}")

                        # Também remover possíveis txt, json, e JPG antigos com o mesmo prefixo
                        # "v1_" e nao "v1": senao apagar a v1 levava junto a v10/v11 (a mais nova)
                        prefix = os.path.basename(old_mp4).split("_FINAL")[0] + "_"
                        for other_file in os.listdir(os.path.dirname(old_mp4)):
                            if other_file.startswith(prefix) and other_file != os.path.basename(old_mp4):
                                other_path = os.path.join(os.path.dirname(old_mp4), other_file)
                                if os.path.isfile(other_path):
                                    os.remove(other_path)
                                    print(f"[Limpeza de Versão] Removido arquivo lateral: {other_file}")
                    except Exception as e:
                        print(e)

if __name__ == "__main__":
    main()
