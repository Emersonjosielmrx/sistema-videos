# 02 — Título + capa (CTR) com teste de verdade
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

**Objetivo:** subir o CTR (impressões → cliques) dos longos e Shorts com títulos/capas melhores e teste A/B real.

**Por que importa:** CTR multiplica tudo; um vídeo bom com capa ruim não é visto.

**Onde olhar**
- Títulos: `D:\recapd-ambientes\producao\bin\seo_generator.py`, regras em `bin\cortes_ajustes.json`,
  `D:\hipercool-videos\config\seo_palavras.json` (moldes "Ele era X… até Y"); memória "Títulos sem nome da obra".
- Capas: `D:\hipercool-videos\bin\capa_ia.py` (estilo Porão: casal/harém, vestida), `bin\anime_publish.py` (capa do longo).
- Postagem: `colab\postar_longos.py` → `D:\postador-de-videos\bin\politica.py` (`postar_youtube`, thumbnail pelo navegador).
- Referência: Porão "NERD Fracassado é HUMILHADO, mas consegue PODERES… E agora todas o QUEREM - Completo".

**O que já se sabe:** o título do Porão segue humilhação → poder → recompensa + "Completo". A dona quer títulos sem o
nome da obra, com palavras buscadas.

**Onde parei / limite:** nunca medimos CTR por título/capa. O YouTube Studio tem "Testar e comparar" (até 3 capas) —
não foi automatizado. Também não sei julgar uma capa como o público julga.

**Como medir:** CTR e views nas primeiras 48 h por variante (Studio), com o mesmo canal e horário.

## Fable — resultado
**29/10 (Fable).** O que faltava para medir CTR já está resolvido pelo ER_02: o lote do Studio
(`retencao_lista`) agora traz **impressões de miniatura e CTR por vídeo**, para o canal inteiro numa página, e o
`coletar_lote` preenche `impressoes`/`ctr` no `metricas_studio.json` — exatamente os campos que o `decidir()` do
`metricas_rede` usa para a nota de TÍTULO dos longos (CTR / mediana dos completos do canal, com `MIN_IMPRESSOES`).
Antes isso dependia do `metricas()` 1-a-1 que caía; a partir da próxima rodada do lote o placar de título começa a
receber dado sem mexer em nada.
- **Teste de capa:** `youtube_studio_extras.teste_ab(pg, vid, capas)` já existe (até 3 capas, "Testar e comparar"
  do Studio) e só exige canal verificado ("verificação única" por telefone — bloqueio da conta, não de código). Para
  os longos: gerar 2 capas por vídeo no `capa_ia` (mesma cena, texto diferente; ou casal × protagonista sozinho),
  chamar `teste_ab` no `postar_longos` após o upload e deixar o YouTube medir — ele escolhe pela duração de
  visualização, que é a métrica certa. Resultado lido no Studio em 1–2 semanas; o `teste_ab` precisa devolver qual
  venceu (hoje só abre o teste) — pendência pequena, 1 leitura da aba do teste.
- **Título:** com `titulos` (lista de candidatos) já salvos no postar.json e CTR real por vídeo, dá para fazer o
  teste A/B de título sem o Studio: alternar o título entre 2 candidatos a cada 24 h nos 4 primeiros dias
  (`editar_metadados` já existe) e comparar impressões→CTR de cada janela no `ret_lista` (período fixo de 28 dias
  não separa; aqui vale o `metricas()` por vídeo em cada dia — 1 leitura/dia/vídeo, dentro do ritmo). Antes de
  automatizar: só nos canais que recebem impressões (ER_01 — nos "não elegíveis" não há CTR para medir).
