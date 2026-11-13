# Risadas reais + retreino das vozes — 04/11 (pedido da dona)

Dona 04/11: "áudios originais sim é bom, principalmente risadas, porque a IA não ri direito; cada narrador tem várias
risadas e nenhuma igual à outra" · "temos também que retreinar algumas vozes dos narradores pra ver se ficam melhores
— é um teste, às vezes já são boas, mas não custa tentar".

## 1. Banco de risadas por narrador (começado)
- `D:\hipercool-materiais\bin\risadas_colher.py pedir|colher [voz]`
- Fonte: vídeo COMPLETO de cada narrador (amostras_voz\dataset_narradores\<voz>\fonte.txt). O dataset do clone é só
  1:00–14:00 e LIMPO — por isso as reações deram 0 em 22/10.
- Download pelo baixador do Kaggle (fila manhwa-drive:baixador, ids `risada_<vid>`, 360p): 13 pedidos postos 04/11 ~09:50.
- Detector: MIT/ast-finetuned-audioset (AudioSet: Laughter, Giggle, Snicker, Belly laugh, Chuckle), CPU, janela 1 s.
- Cada risada: corte +0,15/+0,25 s, separação de voz (audio-separator/UVR), fade e -20 LUFS.
- Sai em models\rvc\vozes\<voz>\humano\risadas\risada_NN.wav + risadas.json ("aprovado": false) e PRÉVIA em
  amostras_voz\clone2\humano\<voz>_risadas.wav. NÃO entra em vídeo antes da dona ouvir.
- Encaixe (falta): depois dos comentários irônicos do narrador ("Cá entre nós,", "E olha a ironia:"...), 1 risada a
  cada ~3–5 min, nunca a mesma 2x no vídeo; a pasta humano\risadas precisa ir pro cache do Drive (colab_recap/vozes).
- Anime original (falta): mesmo detector no áudio da FONTE (na GPU do Kaggle, parte de antes da CPU); onde o
  personagem ri, o áudio original fica audível 1–2 s por baixo/depois da narração.

## 2. Retreino de vozes (plano — teste)
- O treino antigo (bin\kaggle_rpa.py) era pelo NAVEGADOR na conta emersonjosiel649 (BANIDA 02/11) e pelo IP de casa:
  PROIBIDO hoje (regra: cada conta só pela saída dela). O novo tem de ser um tipo de trabalho da central
  (vps_central/kaggle_trabalhador), como os longos, numa conta com IP fixo.
- Material: os mesmos vídeos completos do item 1 (20–40 min por narrador, em vez de ~13), voz separada (UVR na GPU).
- Teste com 2 vozes (sugestão: momo e porao, as mais usadas). Applio, ~300 épocas na T4 (~1 h/voz).
- Comparar v_atual x v_nova na MESMA frase (amostras_voz\clone2\comparar_retreino\<voz>_atual/_nova.mp3) pra dona.
- testes de voz estavam pausados (TESTES_PAUSADOS.json 21/10); a dona liberou ESTE teste em 04/11.
