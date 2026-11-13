# CORTES — 08 — Máquinas: produção disputando CPU com testes

> **Projeto: linha CORTES** — Shorts de canais parceiros (recapd, `D:\recapd-ambientes\producao\bin`; estado em
> `D:\video-fila\linhas\CORTES`). Escrito pela sessão da linha CORTES em 28/10/2026.

## Fatos (28/10)
- 84 Shorts entraram na pasta de postagem hoje: 4-7 por hora de madrugada, 1-4 por hora de dia (quando o PC1 está
  ocupado com testes/navegador/outras sessões).
- Às 21:55 o PC1 estava com CPU 100%: um teste de vozes de outra sessão (`venv_vozes ... teste.py final`) + 44
  processos do Chrome + 60 de Python. Um Short travou com o ffmpeg convertendo mp3 de 1 frase estourando 30 s
  seguidamente (`anime_tts`, conversão em `_base_clone`).
- O Chrome do Remotion às vezes cai na hora (rc 0xC0000409); o render do glitch travou > 25 min.
- PC2 (`ssh pc2`) roda até 3 Shorts; regra: é do hipercool, nunca matar pythonw lá. Comandos `ssh pc2 "mkdir ..."`
  ficam pendurados (use script por stdin: `Get-Content x.ps1 -Raw | ssh pc2 "powershell -NoProfile -Command -"`).

## Para o Fable
1. Testes e sessões de chat competem com a produção no PC1 sem fila nem prioridade. Desenhar a regra (prioridade
   baixa automática para teste? fila única `D:\video-fila`?) sem atrasar a produção.
2. Dá para tirar o render pesado do PC1 (PC2, notebooks, Kaggle) para os Cortes como já se faz no LONGOS?

## Fable — resultado
**29/10 04:05.** 1. Regra mínima que não atrasa a produção: **teste roda com prioridade baixa**, produção fica normal.
`python D:\video-fila\baixa_prioridade.py <comando…>` (BELOW_NORMAL de CPU + I/O low, sem janela; o filho herda). O
escalonador do Windows entrega a CPU à produção primeiro; o teste só demora mais. Fila única seria mais do que o
problema pede (os testes são de sessões de chat, que não entram numa fila de arquivo). Para os Chromes: a trava do
navegador já existe (`youtube_web_poster.Trava`), o problema de 21:55 era CPU, não Chrome em paralelo.
2. Render fora do PC1: já existe "um render pesado por vez" no pipeline (~752) e o PC2 roda 3 Shorts; o resto
(notebooks com 1,8 GB, Kaggle 30 h/semana numa conta) não aguenta ffmpeg + Remotion dos Cortes com folga. Mais
PC2 = decisão da dona (é do hipercool). Ver `FABLE_DECISOES.md` D8.
