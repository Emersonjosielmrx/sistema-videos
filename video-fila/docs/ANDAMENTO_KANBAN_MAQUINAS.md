# Andamento — kanban de máquinas, "até que dia", Kaggle todas as contas, Cortes no PC3 (24/10/2026)

Pedido do dono (24/10 ~11:45): Máquinas do painel :8790 em colunas (kanban) para arrastar tarefa de um PC para outro
(inclusive pro PC3 mesmo com a regra de câmera/OBS); Acer também aparece; o vigia confere se a transferência funcionou;
Kaggle conta as horas de TODAS as contas; campo "até que dia tem postagem em TODOS os canais" (pelo canal com menos,
contando o que está no PC + agendado) e outro "até que dia vai o canal com MAIS vídeos".

Respostas do dono:
- arrastar tarefa rodando = PARA no PC de origem e RECOMEÇA no destino; vigia confere em até 15 min e avisa se não começou
- PC3: instalar o projeto Cortes (venv, ffmpeg, modelos). Acer: só tarefa de navegador (Flow/Veo)
- Kaggle: abrir cada conta do cofre 1x/dia e ler as horas; contas com GPU livre podem ser usadas na fila de voz

Achados:
- ssh do desktop (PC3) recusa a chave desde 24/10 11:42 ("Permission denied (publickey...)"); antes funcionava
- Acer = emersonia-ao532h, ssh emerson-ia@100.98.55.125 (Atom 2 GB, telão); não está no ~/.ssh/config
- só a conta Kaggle emersonjosiel649 usa GPU (kaggle_rpa.CONTA); ~40 perfis do cofre já abriram kaggle.com

## Frentes
- [x] 1. "Até que dia": /api/cobertura (painel_controlador._cobertura) + 2 cartões. Testado 12:00.
- [x] 2. Kanban: index.html pcs()/kcard/kfixos/moverTarefa; /api/kanban, /api/mover, /api/soltar. Print conferido.
- [x] 3. transferencias.py (pedir/executar/parar/disparar/conferir); controlador._aplicar_fixos + tipo "desktop";
       cadeia_veo._fixo_primeiro; vigia_geral chama transferencias.conferir(). Testado: Cortes->PC2 recusado;
       Veo->Acer disparado e confirmado em 2 min (12:06), depois solto. controlador --simular sem erro.
- [x] 4. Acer em maquinas.LIMITES (ssh emerson-ia@...), medidas do controlador e /api/medir; mostra a "vez" do navegador.
- [x] 5a. Kaggle: kaggle_horas.py (POST /api/i/kernels.KernelsService/GetAcceleratorQuotaStatistics de dentro da
       página, só lê) + tarefa KaggleHoras 06:17 + maquinas._medir_kaggle soma (m["contas"]) + "horas por conta" no
       cartão. emersonjosiel649 = 30 h livres (renova 31/10).
- [ ] 5b. USAR as outras contas na fila de voz: NÃO feito — os Termos do Kaggle proíbem mais de uma conta por pessoa
       (usar várias pra somar cota de GPU = risco de banir TODAS, inclusive a 649). Perguntado ao dono.
- [x] 7. (pedido 24/10 ~12:35) Problemas do topo: vigia_geral._consertar_problemas_do_painel aperta o
       "corrigir todos" a cada rodada; painel mostra só situacao=="precisa" (consertando/conferindo/na fila viram 1
       linha); registro estado/problemas_registro.json + /api/erros + tabela "Registro de erros" no fim da Visão geral.
       Leitura completa do Kaggle: 23 contas com Kaggle (690 h livres), 18 sem conta/deslogadas.
- [x] 8. (pedido 24/10 ~13:00) Sessões: só AVISO das contas Google desconectadas (dono: "outro método mais leve,
       só quero saber quais estão desconectadas em avisos"). Tarefa CofreChecar 05:37 (cofre.py checar) + painel
       _sessoes_google lê contas.json (sem abrir navegador). Problema so_dono: aparece direto, o vigia não gasta IA.
       O antigo auto-refresh-sessoes (projetos-navegador, julho, 5 contas por cookies) NÃO foi usado.
- [~] 6. Cortes no PC3 — código pronto, cópia pela metade (ssh instável):
       instalar_pc3.py (passos pastas/codigo/segredos/venv/voz/vozes/modelos/assets/testar; estado\instalar_pc3.json),
       tarefa InstalarPC3 a cada 15 min (--auto) termina sozinha quando o ssh deixar. pc3_parceiro.ps1;
       ocioso.disparar_parceiro_pc3/buscar_parceiro_pc3 (PC1 baixa a fonte e manda por scp; volta por scp de
       C:\pc3_shorts); anime_fetch respeita SEM_YTDLP=1 (PC3 nunca baixa). Falta: rodar 1 Short de teste no PC3.
       ssh do PC3: aceitou ~13:05-13:21, recusou 11:42-13:0x e de novo 13:21 ("Permission denied (publickey)").
- [ ] 6 (antigo). Cortes no PC3 — BLOQUEADO: ssh desktop "Permission denied (publickey...)" desde 24/10 11:42 (porta 22 abre).
       Plano quando voltar: (a) copiar recapd producao\bin + config pra C:\video-cortes, venv próprio (python do
       hipercool-materiais como base), ffmpeg, whisper medium; (b) voz clonada: todo Short sai com ela (21/10) — o PC3
       precisa do modelo RVC (CPU, lento) senão o Short sai sem a voz e fica fora da regra; (c) yt-dlp: o PC3 NÃO
       baixa (mesmo IP da casa; o ytdlp_vez só existe no PC1) — usa só o estoque de fontes baixado pelo PC1
       (estoque_fontes) copiado por ssh; (d) cron_parceiro.bat producao no C:\video-cortes; (e) traz o Short pronto
       pro PC1 como o _buscar_parceiro_pc2 faz no PC2. transferencias.disparar("cortes","desktop") já procura
       C:\video-cortes\venv\Scripts\python.exe e recusa enquanto não existir.
