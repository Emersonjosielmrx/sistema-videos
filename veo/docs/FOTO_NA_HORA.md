# Foto na hora (Flow) + revisor de rosto — 24/10/2026

Pedido do dono: "o problema é o contexto do vídeo pretendido com a foto; usar o Flow Imagem pra criar a minha foto na
hora no próprio contexto do vídeo, usando as imagens base de fundo branco; adicionar revisor pra ver se a imagem tem
mesmo meu rosto; prioridade: nunca mudar o rosto".

## Decisões
- Bases: `D:\fotos para videos\fotos\fotos base so suar se for criar uma foto nova\sem fundo retrato\*.jpg` (~30, fundo branco).
- NUNCA `imagem base inovare frente` (tem telefone/WhatsApp = o que baniu os canais).
- Geração: `D:\flow-imagens\gera_imagem.py` com `--ref` (2 bases) + cenário do vídeo, 9:16.
- Revisor: OpenCV FaceDetectorYN (YuNet) + FaceRecognizerSF (SFace), cosseno vs. todas as bases. Reprovou = tenta de
  novo; esgotou = cai na foto antiga (escolher_foto), nunca gera vídeo com rosto diferente.
- Ponto de ligação: `beta\cron_gerar_video_llm.py` antes de `gerar_video(prompt, foto, out_path)` (~linha 1945).

## Funil + rampa (24/10, noite)
Dono: "o Veo tem que passar pelo sistema de rampa de melhorias do YouTube dando preferência ao mais viral, faça como é lá".
- Medição: `postador\bin\notificar_telegram._placar_veo` → `_analise\placar_veo_temas.json` e `placar_veo_foto.json`
  (vitória = views 48 h > mediana do canal, mín. 4). Tema = nome do arquivo; foto = `beta\logs\veo_foto_por_clipe.json`.
- Gerador: `escolher_canal_inteligente` = sorteio ponderado por horário × Thompson do tema.
- Rede: `mr\rede.py` `_plano_veo` soma `veo_peso_viral` (3) × Thompson na nota; teto do Veo = `politica.teto_canal`
  (rampa) e degrau extra da rampa_canais. Backups `*.bak_20261024_funil_veo`.
- Validado: placar com os 27 Veo medidos; sorteio em 2000 ciclos; `manhwareact.py rede --simular` sem erro
  (InventoReact com Veo 2/dia — era 2 antes também, ver a correção na 2ª rodada).

## Melhorias 24/10 (lista) — dono: "faça todas as melhorias possíveis"
- [x] 1+2 visão (gateway gemini-3-flash): texto legível/marca/deformação; testado: pegou marca Grok em `image (5)`
- [x] 3 base: 1ª de frente (giro<0,35) se "falando pra câmera", Thompson das aprovações; 2ª outro ângulo
- [x] 4 foto vai com o prompt na fila (enfileirar/reenfileirar) e é reaproveitada  - [x] 5 `do_estoque` (cenário ≥40% igual, máx 2 usos)
- [x] 6 antigas: 290/638 reprovadas (`logs\fotos_rosto_reprovado.json`), fora do escolher_foto; sobra 59+ distintas
- [x] 7 porteiro 3ª checagem `[rosto]` (mediana 3 quadros ≥ 0,45); 1º vídeo deu 0,55/0,56/0,57
- [x] 8 falso positivo: 4 sósias gerados (barba+óculos) = 0,27-0,33, reprovados (`fotos_na_hora\_falso_positivo`)  - [x] 9 TikTok: `_placar_tiktok` 1ª volta própria (veo_reg) → veo_temas; 7 de 130 entraram (resto: conta <4 medidas/zerada). Instagram não tem medidor 48 h em projeto nenhum
- [x] 10 ficha por clipe (`logs\veo_foto_por_clipe.json` vira dict): placares veo_foto, veo_fonte, veo_nota_critico
- [x] 11 palavras do título por tema (placar palavras, grupo `veo:<tema>`), injetadas no `_palavras_buscadas_veo`; contato (whats/zap/link...) bloqueado. Carga única dos 27 feita
- [x] 12 `_metricas_do_funil`: views 48 h → cache (casa por clipe; 0 hoje, os do cache têm < 48 h)
- [x] 13 `escolher_viral_do_funil`: ≥1000 views no mesmo tema, 50% dos ciclos, máx 3 variações (`logs\replicas_virais.json`); réplica do cache agora só do MESMO canal (bug: replicava de qualquer canal)  - [x] 14 sem mudança: ManhwaReact (`novo_manhwareact_ia`) está em `limite_diario.json` → a rampa não sobe por regra
- [x] 16 `tentar()` também respeita `MAQUINA_VEZ_DE`; `vitrine.py` já pulava reserva do Veo (23/10)
- [x] 17 `cadeia_veo._RE_MAQ` reconhece "está exibindo"/"está com a vez de" = máquina OCUPADA (5 min), conta não é punida. Foi isso que pôs 18 contas fora e criou `PAUSE_SYSTEM` "bloqueio" às 15:52 (arquivo removido 22:3x, cópia `.removido_20261024_teste`). `teste_cadeia_a_seco.py`: foto/rosto desligados (abria o Flow!) e seebotsia com 100 nos cenários de notebook (ela agora está logada lá); 1 falha restante (cenário 5) é do ambiente: `_em_login` lê a reserva real do acer
- [x] 18 painel `:8790` aba Veo: fotos na hora hoje, nota média do rosto, tema que rende/perde, antigas fora (`painel_controlador._veo_funil`); print desktop+celular OK na porta 8799; o servidor real (desde 20:14) NÃO foi reiniciado (IA do painel ativa) → aparece no próximo reinício
- [x] 19 mesma linha diária de créditos + " | Funil Veo: tema que rende…; fotos na hora ontem a/b"
- fora: 15 (canais novos = dono decide), 20 (MS Energy proibido mexer; capas = outro projeto)

## 2ª rodada (workflow) — 24/10 ~22:45, dono: "faça todas as melhorias possíveis" (de novo, com /workflow-authoring)
- Workflow `wf_f073beb9-373` (só leitura, 4 lentes foto/funil/operação/oportunidades + 1 cético por lente, agentes UM POR VEZ
  e para no 1º que falhar — memória: 3 workflows em Opus caíram inteiros em 429). Script e journal em
  `C:\Users\Haylla\.claude-vscode\projects\d--\5e899044-1ca3-4008-900f-8798a8a40b28\subagents\workflows\wf_f073beb9-373\`.
- Depois: aplicar SÓ os achados com real=true do cético, direto (sem agente), anotando cada um aqui.
- [x] workflow terminou: CAIU no 1º agente (429 rate limit, ~97 mil tokens, 4 min). Revisão feita DIRETO (Read/Grep).
- [x] achados da revisão direta, todos corrigidos e testados (backups `*.bak_20261024_funil_veo`; gera_imagem
  `.bak_20261024_maquinas`):
  1. **foto abria Chrome no PC1 em pausa de carga** (teste 15:24) e podia usar o desktop em chamada: `gera_imagem(...,
     maquinas=)` novo (+ `--maquinas`); o cron passa as máquinas da cadeia; sem "pc1" na lista = nunca PC1. Teste a
     seco: sem lista = 1 notebook + 13 contas do PC1; com lista = no máx. 2, só nas máquinas da lista.
  2. foto sem limite de contas/tempo: `max_contas=2` por tentativa + prazo 15 min (`VEO_FOTO_PRAZO_MIN`); lista vazia
     = desiste na 1ª (6 s, não repete 3x).
  3. reserva de 12 min dos notebooks vencia (prompt ~7 min + foto ~7 min): renovada depois da foto.
  4. **rede: bônus viral nunca casava** (id "veo:<tema>_…" com o prefixo): corrigido; Cassetadas média 0,62, Dicas
     Financeiras 0,25 (antes ~0,5 todos).
  5. estoque devolvia foto de OUTRO cenário/tema (o molde do prompt dava ~40% de semelhança): só o mesmo tema, sem as
     palavras do molde, ≥ 50%. Teste: clube/stand-up acha; clube/fitness e praia/stand-up não.
  6. réplica de viral por "começa com" → tema exato.
  7. conta deslogada numa máquina + a outra ocupada não era marcada (a cadeia repetia a conta): 15 min fora.
  8. ficha por clipe gravada de forma atômica (o medidor lê de outro processo) e limitada a 3000.
  9. foto antiga: `rosto_ok` (cache de aprovadas 348 / reprovadas 290; foto nova é conferida na hora) no
     `escolher_foto`, no `escolher_foto_inteligente` e na foto do item da fila; sem foto válida no disco = sorteia uma
     conferida ou não gera (antes iria texto→vídeo com pessoa qualquer).
  10. `MAQUINA_VEZ_DE=veo` saiu do import (o MS Energy importa o cron e pegaria o notebook reservado pro Veo); agora só
      dentro do `run()`.
  11. registro da foto guarda a visão junto ("mesmo rosto; visao ok").
- **Correção de informação (dita ao dono antes):** o InventoReact NÃO subiu de 1 para 2 Veo/dia — já era 2 e continua 2
  (o `max_dia` 3 do cadastro segura o canal em 4). O ManhwaReact CAIU de 2 para 1: agora o Veo obedece o teto real do
  canal (`politica.teto_canal` = max_dia 3 do cadastro, como o hipercool); o código antigo usava 4 fixo e o canal fez
  4/dia de 18 a 22/10 e pegou "limite diário". Mantido (mais seguro); subir é no cadastro (decisão do dono).
- [x] compilação de tudo; `teste_cadeia_a_seco.py` 14/14 OK; `validate.py` OK menos "trava_render" (render real do
  `montar_final` pid 2784 desde 23:17 segurando a trava — ambiente).
- [x] **prova real com máquina livre — PASSOU 25/10 00:07**: `beta\teste_foto_na_hora_real.py` (0 crédito). PC1 crítico
  (CPU 100%, 0 vaga) → a cadeia liberou SÓ o acer; a foto saiu no Chrome do acer (conta emersonjosiel2032), nada no
  PC1. `fotos_na_hora\teste_maquinas_20261025_000731_1.png`: terraço ao pôr do sol, nota de rosto 0,70, "mesmo rosto;
  visao ok". Tempo 700 s (o acer é o notebook lento) — dentro do prazo de 15 min. **Nada mais pendente nesta rodada**;
  os crons de 02:43/03:03/04:03 só precisam conferir (opcional: olhar no `logs\cron_gerar_llm.log` o 1º ciclo real com
  `[foto_na_hora]` e `[rosto]` quando a reserva de limpos cair abaixo de 100).
- 25/10 madrugada (crons de conferência): nenhum ciclo real do Veo desde 00:00 (controlador não disparou geração:
  reserva de limpos acima do mínimo). Nada a corrigir.

## Progresso
- [x] achadas as bases e o ponto de ligação
- [x] modelos ONNX em `D:\hipercool-materiais\models\rosto` (yunet.onnx, sface.onnx, do opencv_zoo)
- [x] `beta\foto_na_hora.py`; calibrado: bases entre si 0,51-0,85; fotos antigas do Grok 0,44 e 0,34 (reprovadas) → limiar 0,50
- [x] teste real 24/10 13:59 (seebotsia, 0 crédito): `fotos_na_hora\teste_20261024_135906_1.png`, clube neon, nota 0,65, aprovada
- [x] ligado no cron (depois do prompt pronto, antes do laço de contas); validate.py TUDO OK
- [x] 1º vídeo real 24/10 16:20: `D:\hipercool-materiais\veo\cron_shorts\stand-up_ia_20261024_161528.mp4` (conta
  emersonjosiel2027): foto nota 0,58; rosto nos quadros 0,5 s/4 s/7,5 s = 0,54/0,56/0,60; validar_video OK 720x1280 8 s;
  fala 100% (groq). Não postado.
- [x] defeito achado no caminho: o worker pulava o notebook reservado pelo próprio cron ("vez de 'veo'") e descartava
  18 contas em 40 s. Corrigido: cron põe `MAQUINA_VEZ_DE=veo`; `postador\bin\maquina_remota.tentativas` passa isso a
  `reservado(nome, quem)` (+ `import os` que faltava). Validado no ciclo das 16:08.
- obs.: no teste os óculos foram pra cabeça; pedido reforçado ("glasses ON HIS EYES")
