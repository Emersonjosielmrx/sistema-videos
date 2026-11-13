# GPU do Kaggle nos vídeos grandes — plano e estado (dono 22/10 ~06:10: "vamos começar a usar ele em vídeos grandes")

Por quê (medido 22/10): a voz clonada na CPU do PC1 leva 2-4x a duração do áudio com o PC livre e ~19x com ele ocupado
(1 h de narração = 2 a 19 h); no T4 do Kaggle são minutos. A ida e volta do Kaggle (~15-25 min de fila + instalação)
não pesa em vídeo grande. Análise completa: D:\video-fila\MELHORIAS_SHORTS.md, seção "IDEIA DO DONO 22/10".

## Regras
- Produção primeiro: o Kaggle é um acelerador. Se falhar ou demorar, o projeto segue como hoje (nunca segurar
  postagem). Nada pesado no PC1 (incidente 22/10 05:31: separação no PC1 derrubou a voz clonada da produção).
- CONTAS (dona, 23/10/2026 — substitui a regra antiga de "uma conta só"): "agora são muitas contas, temos 14 e
  crescendo, e mais GPU do que podemos usar". Cada conta tem a sua cota (~30 h de GPU por semana); usar as contas
  que ela já criou, em rodízio. NÃO criar conta nova por conta própria (quem cria é a dona). Risco que ela conhece:
  a regra do Kaggle é 1 conta por pessoa e o Kaggle pode banir todas juntas — se uma conta for bloqueada, avisar a
  dona na hora e parar de abrir as outras até ela decidir.
- O QUE VAI PRO KAGGLE (dona 23/10): "tudo que for mais rápido fazer lá, contando o tempo de transferência e
  download, pode fazer". Conta: (tempo no PC) x (tempo de upload + fila/instalação ~15-25 min + GPU + download). Se
  o Kaggle ganhar, vai pra lá; se não, fica no PC. Antes cota de 30 h/semana dividida; agora a cota é a soma das
  contas.
- Um navegador do cofre por vez (trava compartilhada entre os scripts do Kaggle). Com várias contas, pode haver uma
  sessão de GPU por CONTA ao mesmo tempo (era "uma por vez" quando só havia uma conta).
- amostras_voz\TESTES_PAUSADOS.json (dono 21/10: "testes de clone voltando sozinhos, priorizar a produção") continua
  valendo pra fila de testes do PC (VozClonadaFila). O conversor e o piloto vieram de ordens DEPOIS (22/10 ~02:50 plano
  da fidelidade; ~06:10 "vamos começar a usar o Kaggle em vídeos grandes") e não pesam no PC1 (só subir/baixar).
- Mesmo som da produção: Applio no commit 5379cf2 + o NOSSO rvc\infer\pipeline.py (APPLIO_F0_ESCALA e
  APPLIO_F0_FINAL_ST) + mesmos parâmetros do voz_clonada.lote (tom, index_rate, protect, volume_envelope, f0_escala,
  final_st, formant). EQ continua no PC (ffmpeg, leve).

## Peças (ordem de construção)
1. [x] Fila de conversões (D:\hipercool-materiais\gpu_fila\pendentes|enviados|prontos|falhas\<job>\) + módulo
       D:\hipercool-materiais\comum\gpu_fila.py (só biblioteca padrão; qualquer venv importa): pedir(), estado(),
       saida(), motivo(), esperar().
2. [x] Notebook amostras_voz\kaggle_conversor_rvc.ipynb (gerado por bin\gerar_notebook_conversor.py; rodar de novo
       depois de mudar): Applio + nosso pipeline.py; converte cada job em processo próprio (core.py infer,
       --split-audio; fcpe e, se falhar, rmvpe); RESUMO.txt com o tempo de cada job; saidas.zip refeito a cada job.
3. [x] bin\kaggle_conversor.py (python\venv, Playwright): enviar (empacota pendentes + modelos das vozes + nosso
       pipeline.py, sobe dataset, notebook novo, GPU, Save & Run) e conferir/baixar (distribui as saídas em prontos\;
       pedido sem saída volta pra fila, 2 tentativas e vai pra falhas\). Reaproveita as funções do bin\kaggle_rpa.py.
       Log: amostras_voz\kaggle_conversor\conversor.log. "auto" com fila vazia e sem lote sai calado (22/10 06:38).
4. [x] Trava compartilhada do navegador do Kaggle (kaggle_rpa.Navegador: amostras_voz\kaggle_navegador.lock) e vez da
       GPU NOS DOIS SENTIDOS (22/10 06:38): o conversor espera lote de treino/piloto e o treino (kaggle_rpa.treinar,
       chamado pelo vigia da voz clonada e pelo piloto) espera lote de qualquer outro uso
       (kaggle_rpa.ESTADOS_KAGGLE/_outro_lote; backup kaggle_rpa.py.bak_20261022_gpu_vez). Testado: o treino normal vê o
       lote do piloto; o piloto não vê a si mesmo.
5. [x] Tarefa agendada GpuKaggleFila (20 em 20 min, sem fim, IgnoreNew, limite 3 h, pythonw do python\venv):
       kaggle_conversor.py auto. Criada 22/10 06:37.
6. [ ] Teste de ponta a ponta com narração longa de verdade (8-10 min, voz porao), medindo ida e volta e minutos de
       GPU; mp3 pro dono ouvir.
7. [ ] Ligar no 1º projeto de vídeo grande (DECISÃO DO DONO: anime longo do Cortes no PC2 e/ou capítulo/compilado do
       hipercool depois de 24/10), com volta automática pra conversão local/voz sem clone se o Kaggle não entregar a
       tempo.

## Estado atual
- 22/10 06:15: plano escrito. O piloto de treino (porao_v3) está no Kaggle desde 05:47: o 1º lote do conversor só sai
  depois que ele terminar (1 sessão de GPU por vez).
- 22/10 06:38: peças 1-5 prontas; fila vazia (nada enviado ainda). PRÓXIMO: peça 6 (teste de ponta a ponta) depois que
  o piloto terminar: gerar uma narração de 8-10 min (edge, base francisca, igual ao Cortes), pedir com
  gpu_fila.pedir("porao", wav, origem="teste e2e", tom=<tom_fixo da base>) e acompanhar conversor.log (ENVIADO ->
  BAIXADO), medir ida e volta e minutos de GPU, mp3 pro dono ouvir. Depois, peça 7 (dono escolhe o 1º projeto).
- 22/10 06:41: peça 6 PEDIDA: job 20261022_064056_porao_09efc7 (9,5 min de narração real: 4 roteiros do Cortes em pt
  com a Francisca pelo edge_tts_engine, tom -10 da base francisca do porao). Script e saídas:
  D:\hipercool-materiais\amostras_voz\kaggle_conversor\teste_e2e.py e teste_e2e\. A GpuKaggleFila conferiu 07:00:
  "ESPERA lote do piloto" (certo). Quando o piloto sair da GPU ela manda sozinha. Depois: "teste_e2e.py status" (com o
  venv do Cortes) mostra a ida e volta e faz os mp3 (1_base_francisca.mp3 x 2_porao_kaggle.mp3) pro dono ouvir.
- 22/10 08:44-09:01: peça 6 OK (enviado 08:44, baixado 09:01: ~17 min de ida e volta pra 9,5 min de narração).
- 22/10 ~23:00 (dono: "adicione ela pra ser usada como um dos nossos PCs"): Kaggle virou máquina "kaggle" no
  maquinas.py (_medir_kaggle: livre = sem lote de conversor/treino/piloto e GpuKaggleFila ativa; fila de voz e horas
  de GPU da semana), no log do controlador e no painel :8790 (cartão próprio). NÃO recebe render comum: só voz clonada.
  Falta a peça 7 (algum vídeo grande pedir pela gpu_fila): hoje a voz clonada só existe nos Shorts (PC1), e Short não
  compensa ir pro Kaggle.
