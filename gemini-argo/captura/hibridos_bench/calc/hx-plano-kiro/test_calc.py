from calc import media_movel, mediana

assert media_movel([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5], media_movel([1, 2, 3, 4], 2)
assert mediana([4, 1, 3, 2]) == 2.5, mediana([4, 1, 3, 2])
print("TODOS OS TESTES PASSARAM")
