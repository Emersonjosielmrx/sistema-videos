# Pendências dos anúncios do drone (05/11/2026)

- [ ] **Carretinha DUPLICADA**: os testes do `publicar_anuncio.py` enviaram 2× "Carretinha p/ Drone Agrícola com Placa Solar
      + Gerador + Misturador + Tanque 1000L" (R$ 29.000). As duas estão em "Aguardando Publicação". Quando a OLX
      aprovar, excluir UMA em conta.olx.com.br/anuncios/publicados (anúncio duplicado = risco de suspensão).
      O script agora tem trava de título repetido.
- [ ] Anúncio do drone (R$ 62.000): publicar com `anuncios/anuncio_drone.json`. A 1ª foto é ilustrativa e tem a faixa
      "FOTO ILUSTRATIVA DO MODELO" (a dona autorizou usar foto da internet).
- Dados: CEP do item 68665-000 (Garrafão do Norte-PA). A OLX preenche o CEP da conta (Paragominas) sozinha, e o script troca.
- A IA da OLX escolhe a categoria sozinha e às vezes erra (deu "Produção Rural"). O script troca para "Tratores e máquinas agrícolas".
