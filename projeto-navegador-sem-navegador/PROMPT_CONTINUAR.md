# Prompt para o próximo agente — continuar a revisão do "navegador sem navegador"

```text
Continue a revisão e as melhorias do projeto D:\projeto-navegador-sem-navegador (automação HTTP pura com os cookies do
Chrome do cofre: YouTube Studio, Instagram, Google Flow/Veo, Google Fotos, TikTok — sem abrir navegador no dia a dia).
Responda sempre em português do Brasil, em linguagem simples.

ANTES DE COMEÇAR, leia nesta ordem:
1. D:\projeto-navegador-sem-navegador\MELHORIAS_30-10.md — tudo que já foi feito em 30/10 (4 rodadas), com o porquê.
2. D:\projeto-navegador-sem-navegador\README.md — o que está em produção e quem chama cada módulo.
3. D:\projeto-navegador-sem-navegador\PLANO_00h40.md — histórico, provas e decisões (é longo; leia as seções do
   módulo em que for mexer).
4. D:\projeto-navegador-sem-navegador\IMPLANTAR_MAQUINA.md — como o worker vai para os notebooks/PC2.

ESTADO EM 30/10 ~15h:
- 35 testes offline passando: D:\projeto-navegador-sem-navegador\testar.cmd (ou
  `python D:\projeto-navegador-sem-navegador\tests\test_offline.py`, que relança sozinho com o python do D:\veo\venv).
- Worker reinstalado no x200ma, acer e pc2 ("nsn ok"). Desktop NÃO (o ssh dele derruba conexões).
- Backup do código antes das mudanças: D:\projeto-navegador-sem-navegador_backup_20261030.
- Código antigo/inventado foi para legado\ (ver legado\LEIA.md) — nada da produção usa.
- Postador do Instagram (D:\postador-de-videos\bin\postar_insta_auto.py) agora tem ritmo por conta (1 Reel por
  rodada, 60 min entre Reels) e pausa automática em D:\postador-de-videos\config\instagram_pausas.json;
  landingpageia.ia e jornalcomia pausadas até 06/11 (conta inativa). Cópia de antes: postar_insta_auto.py.bak_20261030.

PRIMEIRA TAREFA — conferir na produção o que ainda não teve prova real (só leitura de logs):
- D:\postador-de-videos\logs\youtube_http.log: uploads depois de 30/10 12:18 (upload_http novo). Procure
  "subiu por HTTP", "rascunho privado ... ficou no canal", "PÚBLICO sem agendamento", "já passou".
- D:\postador-de-videos\logs\instagram_auto.log e instagram_<data>.log: "em pausa até", "espera 60 min entre Reels",
  "Reel por HTTP", "PAUSADA". Confirme que nenhuma conta postou 2 Reels com menos de 60 min.
- D:\postador-de-videos\logs\maquina_remota.log: "Flow por HTTP" depois de 30/10 14:00 (worker novo nos notebooks).
- D:\projeto-navegador-sem-navegador\logs\manter_cookies.jsonl: vivos/girados por hora.
Se algo quebrou por causa das mudanças de 30/10, corrija primeiro (o MELHORIAS diz o que mudou em cada arquivo).

DEPOIS, ideias que ficaram pendentes (escolha pelo risco/benefício, uma por vez, com teste):
- upload_http: descobrir se o token sessionInfo está vivo ANTES de enviar o vídeo inteiro (hoje só descobre depois).
- postador do YouTube (youtube_web_poster._subir_http): quando o upload_http levantar LimiteDiario, não cair no
  Chrome (ele bate no mesmo limite). Isso mexe na produção: explique antes no texto do que fez.
- tools\capturar_passivo.py: token gravado no canal errado se a aba trocar de canal (suspeita, não confirmada).
- services\instagram\postar.py reel: o vídeo é lido inteiro na memória (Reels são pequenos; baixo valor).
- Ferramentas de captura (tools\capturar_*.py) e tools\_exp\ não foram revisadas (são de desenvolvimento).

COMO TRABALHAR:
- Cada correção: entenda o cenário real de falha, corrija o mínimo, escreva um teste em tests\test_offline.py,
  rode testar.cmd, e anote no MELHORIAS_30-10.md (seção nova com a data).
- Mudou arquivo que vai no pacote dos notebooks (ver ARQUIVOS em tools\empacotar_worker.py)? Rode os testes e
  reinstale: `python D:\postador-de-videos\bin\maquina_remota.py instalar-nsn x200ma` (depois acer, pc2), um de
  cada vez, com o terminal FORA da pasta dist\ (senão o empacotador não consegue apagá-la).
- Antes de dizer que algo funciona, mostre a prova (saída do teste, linha do log). "Fiz/testei" de outro agente é
  alegação: abra o log e as datas antes de confiar.
```

```text
RESTRIÇÕES — o que NÃO fazer (valem acima de qualquer pedido de "melhorar tudo"):

- NÃO postar, agendar, comentar, mandar DM, seguir ou editar perfil de verdade para "testar". Nada de vídeo de teste
  no YouTube, Reel/Story de teste no Instagram, nem geração no Flow que gaste créditos. Teste só offline (simulação)
  ou com leitura (analytics, créditos, perfil). A prova das postagens é a rodada normal da produção.
- NÃO rodar `postar_insta_auto.py --simular` nem nada que chame reserva_veo.completar: ele pode baixar vídeos do
  Drive e o disco D anda com pouco espaço.
- NÃO mudar o ritmo de postagem, os tetos (config\tetos.json), as contas pausadas ou qualquer regra de negócio sem
  a dona aprovar. Mostre o achado e pergunte.
- NÃO publicar vídeo do YouTube como público direto; sempre agendado ou privado (regra da dona).
- NÃO copiar a pasta cookies\ entre máquinas, NÃO mostrar valor de cookie/token/senha em resposta ou log, e NÃO
  apagar cookies\, capturas\ ou logs\.
- NÃO abrir o Chrome do cofre à toa: abrir gira o login e mata a cópia HTTP dos cookies e o token do Studio.
- NÃO mexer no D:\gemini-argo\youtube_http.py: outra sessão está trabalhando nele (mudou em 30/10 12:39).
- NÃO apagar arquivos: mova para legado\ ou faça cópia .bak antes de mudar arquivo da produção
  (D:\postador-de-videos, D:\veo, D:\flow-imagens).
- NÃO matar processos sem conferir de quem são: há várias sessões do Claude e a produção (pythonw, recapd, hipercool,
  Chrome nas portas 97xx do cofre) rodando no PC.
- NÃO insistir no ssh do desktop (derruba conexões; rajada piora). Notebooks: uma máquina por vez.
- NÃO baixar nada no disco C (nem temporário); downloads só no D, medindo o tamanho antes.
- NÃO abrir vários subagentes ao mesmo tempo: a RAM do PC1 fica perto de 1–2 GB livres e a sessão já caiu 3 vezes
  em 30/10. Se a RAM livre ficar abaixo de ~3 GB, siga a regra do CLAUDE.md (Wise Memory Optimizer) antes de seguir.
- NÃO usar Opus/Kiro em pipeline; a IA de visão/etiquetas é Gemini/Argon pelo gateway.
- NÃO fazer commit/push (o projeto não é git) nem publicar nada fora do PC sem pedir.
```
