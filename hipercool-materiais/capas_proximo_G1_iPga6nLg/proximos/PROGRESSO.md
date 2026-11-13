# Capas dos 8 vídeos — onde parei (01/11/2026 ~17h)

## 02/11 02h15 — ESTADO RÁPIDO (pra retomar)
- B mix (teste_b_mix): 2 saíram com mulheres VESTIDAS -> teste_b_mix\reprovadas. montar_b agora põe a regra do
  biquíni no COMEÇO e manda ignorar roupa das referências. Testar de novo (teste_b_mix.py ssMbrCz0fhE <poses>).
- Capas novas p/ mostrar: Morando B (boa: biquíni, cara de língua, dirigíveis), Prisioneiro A (boa), Morando A (fraca: 1 mulher, outras vestidas).
- refazer.py relançado 02:15 (hJaA primeiro). --trocar SÓ depois da dona aprovar.
- Fábrica de tokens (Chrome quente) no ar no DESKTOP; PC2 falta (ver D:\flow-imagens\ANALISE_GARGALO_01NOV.md).
- Login das 10 contas do desktop: 2 login_em_lote ainda rodando (esperam a dona digitar a senha na tela).

## O que a dona pediu (acumulado)
- Pastas: `brutas\<Obra> (<id>)\A.png...G.png` (Flow) e `brutas_google\...` (Google); `original.jpg` = capa do parceiro;
  reprovadas dela em `<obra>\reprovadas\`; `antigas\` = versões com prompt velho; `sem_referencia\` = Flow sem a ref.
- Prompt de imagem reprovada não roda de novo (`proibido()` em gerar_todos.py, lê `_prompts.jsonl`).
- Cada mulher num BIQUÍNI-FANTASIA do tema (como a mascote: bruxa com chapéu, estudante com gravata...), nunca roupa.
- Seios MUITO maiores (ela reclamou 5 vezes).
- Poses do hipercool (prints em `poses\`): mulher ENORME em close numa pose com ele (de quatro por cima dele, de quatro
  olhando pra trás, de quatro de costas na cama, colo de frente, sentada nele, harém na cama). Descrever a pose como
  SITUAÇÃO inocente ("tropeçou e caiu por cima dele"), nunca como posição sexual (dica da dona).

## O que já sei
- Google (google_imagem.py, conta por conta): faz biquíni e pose de colo; RECUSA de quatro ("sem imagem"); não aceita
  imagem de referência (testado: edits = 400, campo image = ignorado); seio fica médio por mais que o texto exagere.
- Flow com a pose do hipercool como 2ª ref: COPIA A POSE. Texto exagerado de seio ("bola de basquete") fez ele vestir
  as mulheres e diminuir tudo (teste\ssMbrCz0fhE_A_flow_v5.png). "Biquíni de estudante" virava uniforme -> veste().
- Melhor Flow até agora: a 1ª Ferreiro A (de quatro por cima, biquíni xadrez) — ainda seio médio.

## Rodando agora
- Teste Flow com 3ª referência de CORPO (poses\de_quatro_costas_cama.png = "waifu gasosa"): teste\ssMbrCz0fhE_A_flow.png
  e teste\vMyOmvaaFIk_B_flow.png. Se o seio crescer -> rodar `python gerar_todos.py` (Flow A/B/C) e depois
  `python gerar_google.py` (D/E/F/G; quando o Google recusa, o Flow faz).
- Se não crescer: tentar ref de corpo mais peituda / avisar a dona que o Flow tem teto.

## 18h40 — NA PRODUÇÃO
- `D:\recapd-ambientes\producao\bin\capa_longo_v2.py` + `_ficha_v2` no capa_ia_anime (capa_melhorada = A, capas_ab =
  B/C) — todo longo de parceiro sai assim sem chat. Desliga: CAPA_LONGO_V2=0. Teste ponta a ponta:
  `python teste_v2_producao.py <id>` -> teste_v2\<id>\capa.jpg, capa_b.jpg, capa_c.jpg.
- Seio ainda abaixo do que a dona quer (teto do Flow). Próximo: achar gerador com referência menos travado.

## 20h — pedido novo da dona
- Reprovou Ferreiro B (muito vestida) e teste\reprovada\vMyOmvaaFIk_B_flow; "todas continuam com seios pequenos".
- Poses pra CAPA B: biblioteca `D:\hipercool-materiais\capas_poses_ref\b\` (12 recortes das capas do hipercool
  `D:\hipercool-videos\config\capas_referencia` + 3 prints novos dela). As 6 antigas ficam na raiz.
- Ideia dela: Flow com ref 1 = capa do parceiro (personagens) + ref 2 = capa com a pose e SEM descrever a pose.
  `teste_pose_ref.py <id> <pose...>` -> teste_pose\. 1º resultado (colo_de_frente_2): pose copiada, mas o Flow VESTIU
  (saia+camisa) e seio pequeno. Faltam de_quatro_bom_dia, ele_nas_costas_dela, pernas_em_volta_cabeca.
- Refazer as capas dos 17 longos JÁ POSTADOS e trocar no Studio: `D:\hipercool-materiais\capas_longos_refeitas\refazer.py`
  (gera A/B/C pela produção; `--trocar` sobe o teste A/B; `--estado`). Teste A/B já em andamento = Studio devolve "ja".
- Flow à noite lotado (carrosséis/produto): teste ponta a ponta da produção não saiu ("Flow sem resposta em 25 min").
- 20h30: ele_nas_costas_dela saiu BOA (biquíni xadrez+gravata, inclinada, seio maior; pose não exata). Sem
  descrever a pose o Flow veste menos? comparar com as outras 2 quando saírem.
- Pesquisa (Argon + Gemini Pro concordam): NoobAI-XL 1.1 / WAI-illustrious v14 + ControlNet OpenPose (só esqueleto)
  + IP-Adapter. Prova sem Kaggle: Space r3gm/DiffuseCraft (`D:\hipercool-materiais\capas_poses_ref\poc_illustrious.py`,
  api em _diffusecraft_api.json) — o Space só aceita pré-processador Canny/None, então o esqueleto sai local
  (`esqueleto.py`, controlnet_aux). PC1 sem memória virtual (commit 38/39,8 GB, produção) -> rodar o esqueleto no
  DESKTOP. Kaggle: as 4 GPUs (1 por saída, regra da dona) estão no recap; 5ª GPU = perguntar à dona.
- Seio: pesquisando gerador anime SDXL (Illustrious/NoobAI) + ControlNet pose no Kaggle — o Flow/Google têm teto.

## Depois
- Capas de Short com Google (google_imagem.py) "de forma correta"; capa "cena que não existe" (CAPAS_REFERENCIA.md topo).
