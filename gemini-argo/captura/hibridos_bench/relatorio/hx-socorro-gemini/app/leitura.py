import csv


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return [{"canal": l["canal"], "titulo": l["titulo"], "segundos": int(l["segundos"])} for l in csv.DictReader(f)]
