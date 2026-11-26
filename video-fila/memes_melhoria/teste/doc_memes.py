from pathlib import Path
p = Path(r"D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md")
p.write_text(p.read_text(encoding="utf-8") + """

## 26/11 — JÁ FEITO: 17 memes aprovados pela dona + memes nos MELHORES momentos
- Dona revisou Desktop\\memes_pt e aprovou 17 (números 21 a 37 em memes_novos; 3 cortados por passarem de 12 s:
  21 delícia 3,4 s, 29 tá tranquilo 3,3 s, 33 ai papai 5,7 s). Catálogo dos longos: 20 -> 37 memes, cada um com ficha.
  31 "mas que porra é essa" e 32 "e o pix nada" (palavrão) + 35/36/37 (só som) = ficha resumo=false: entram no meio,
  NUNCA na abertura (memes_visuais.fora_do_resumo + anime-pipeline._memes_resumo). Testado: nome com "porra" não
  dispara o filtro de palavrão da postagem. MEMES_PALAVRAO=0 tira os de palavrão. Emoção dos 21+ vem da ficha.
- Escolha pelos MELHORES momentos (memes_visuais._escolher_otimo): antes o 1º momento que casava levava o meme e
  bloqueava/gastava o melhor logo depois; agora nota de todo par frase x meme no vídeo inteiro, escolhe do maior para o
  menor respeitando o intervalo; meme pode repetir 1x a >= 300 frases se nota >= 9. Roteiros reais: nota total 81->126 e
  92->116; os momentos mais fortes (venceu sem dificuldade 16,5; primo mimado furioso 16,5) agora entram.
  Desliga: MEMES_MOMENTO_OTIMO=0. Ajustes: MEMES_REPETE_LONGE, MEMES_REPETE_NOTA.
- Backups: memes_visuais.py/anime-pipeline.py .antes_aprovados_26nov e .antes_otimo_26nov; memes.json/fichas.json
  .antes_aprovados_26nov. Subido ao Drive do Kaggle (rclone check 0 diferenças). Scripts: memes_melhoria\\teste.
- FALTA: conferir no 1º longo real. Ideia pendente: meme depois do DESFECHO quando a frase seguinte conclui a ação
  ("tenta mandar uma lapada" -> meme só depois de "o prota desvia e bota pra correr").
""", encoding="utf-8")
print("ok")
