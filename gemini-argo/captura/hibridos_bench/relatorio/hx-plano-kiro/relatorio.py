import json
import sys

from app.agrupar import por_canal
from app.leitura import ler
from app.tempo import formatar


def main():
    dados = por_canal(ler(sys.argv[1]))

    if "--json" in sys.argv:
        print(json.dumps(dados, ensure_ascii=False))
    else:
        for canal in sorted(dados):
            d = dados[canal]
            print(f"{canal}: {d['videos']} vídeos, {formatar(d['segundos'])}")


if __name__ == "__main__":
    main()
