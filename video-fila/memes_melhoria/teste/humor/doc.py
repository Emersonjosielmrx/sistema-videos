from pathlib import Path
p = Path(r"D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md")
p.write_text(p.read_text(encoding="utf-8") + """

## 26/11 — JÁ FEITO: narrador REAGE ao vivo (humor do Virjão/Momo)
Dona: "elementos dos vídeos do Virjão ou Momo que ainda não tem — analise e implemente da melhor maneira".
Análise (fala real x nossos roteiros, por mil palavras): D:\\video-fila\\memes_melhoria\\ANALISE_HUMOR_VIRJAO_MOMO.md.
Nossos longos saíam como texto lido: 1ª pessoa 0,2 (Momo 13,7), pergunta 1 (11-18), '!' e '...' ZERO em todos,
"Sinceramente, esse cara não aprende, né?" 3x no mesmo vídeo, a piada de virada pedida nunca saía, "nosso garoto" 7,7/mil.
- bin\\humor_narrador.py (novo) + bin\\humor_narradores.json (perfil de 107 narradores, sem palavrão). Chamado em
  anime_script.rewrite_longo_com_tempo antes de guardar no cache: SÓ roteiro novo, SÓ anime/manhwa.
  1) tira comentário repetido; 2) 'Sinceramente,'/'Cá entre nós,'... com teto de usos; 3) 'nosso garoto' no máximo 1 a
  cada 40 frases (o resto vira 'o prota'/'o protinha', nunca 'o cara'); 4) a IA SUGERE reações curtas (1ª pessoa,
  pergunta incrédula, imitação, piada de virada, piada recorrente com placar, golpe) e temperos (interjeição + '!' numa
  frase de impacto); o CÓDIGO confere: sem palavrão, sem ofender o público, sem cena triste (morrer de medo/rir não
  conta), sem repetir, sem começar igual, espaçado, dentro do teto de frases. Reação entra depois da frase, com o mesmo
  segundo. Fatos e ordem não mudam.
- Teste real (300 frases do Virjão): 10 reações + 8 temperos; '!' 0 -> 2,9/mil, pergunta 0,7 -> 2,5, interjeição
  2,5 -> 4,0. Ainda abaixo dos reais de propósito (começar sem cansar).
- Desliga: HUMOR_POLIR=0 (tudo) ou HUMOR_DEDUP / HUMOR_ABERTURAS / HUMOR_APELIDO / HUMOR_REACOES = 0.
  Ajuste de quantidade: HUMOR_CADA (14) e HUMOR_TEMPERO_CADA (20) — menor = mais reações.
- Backup: anime_script.py.antes_humor_26nov. Subido ao Drive do Kaggle (rclone check 0 diferenças). Testes em
  memes_melhoria\\teste\\humor.
- FALTA: ouvir o 1º longo novo. Roteiro que já estava no cache não muda (só os novos).
""", encoding="utf-8")
print("doc ok")
