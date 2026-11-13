import json
import sys

from app.agrupar import por_canal
from app.leitura import ler
from app.tempo import formatar


def main():
    usar_json = "--json" in sys.argv
    caminho = sys.argv[1] if sys.argv[1] != "--json" else sys.argv[2]

    dados = por_canal(ler(caminho))

    if usar_json:
        print(json.dumps(dados, ensure_ascii=False))
    else:
        for canal in sorted(dados):
            d = dados[canal]
            print(f"{canal}: {d['videos']} vídeos, {formatar(d['segundos'])}")


if __name__ == "__main__":
    main()
