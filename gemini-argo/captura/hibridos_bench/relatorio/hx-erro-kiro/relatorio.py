import json
import sys

from app.agrupar import por_canal
from app.leitura import ler
from app.tempo import formatar


def main():
    if "--json" in sys.argv:
        sys.argv.remove("--json")
        dados = por_canal(ler(sys.argv[1]))
        saida = {canal: {"videos": d["videos"], "segundos": d["segundos"]} for canal, d in dados.items()}
        print(json.dumps(saida, ensure_ascii=False))
    else:
        dados = por_canal(ler(sys.argv[1]))
        for canal in sorted(dados):
            d = dados[canal]
            print(f"{canal}: {d['videos']} vídeos, {formatar(d['segundos'])}")


if __name__ == "__main__":
    main()
