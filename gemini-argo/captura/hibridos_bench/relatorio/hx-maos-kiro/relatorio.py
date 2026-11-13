import json
import sys

from app.agrupar import por_canal
from app.leitura import ler
from app.tempo import formatar


def main():
    args = [a for a in sys.argv[1:] if a != "--json"]
    usar_json = "--json" in sys.argv[1:]
    dados = por_canal(ler(args[0]))
    if usar_json:
        print(json.dumps(dados, ensure_ascii=False))
        return
    for canal in sorted(dados):
        d = dados[canal]
        print(f"{canal}: {d['videos']} vídeos, {formatar(d['segundos'])}")


if __name__ == "__main__":
    main()
