from t5_util import pausar


def tratar_erro(conta, status):
    if status == 429:
        return pausar(conta, "limite", 20)
    return None


print(tratar_erro("conta7", 429))  # esperado: "conta7 pausada 20 min: limite"
