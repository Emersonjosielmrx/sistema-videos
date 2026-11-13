# OBRIGATÓRIO antes de qualquer melhoria em vídeo (dona, 01/11/2026)

> "Quero que esses pendentes sejam analisados obrigatoriamente pelo chat quando eu for fazer melhorias, deixando bem
> documentado isso pra fazer."

Vale para TODO chat que for melhorar vídeo (Shorts, longos, recap, hipercool, manhwa-react, historias-em-frames,
claude-code-video, Veo, produto/postador): roteiro, narração, legenda, efeitos, transições, trilha, capa, título, tags.

**Ninguém implanta isso sozinho.** O `aprendizado.py` (a cada 30 min, pelo VigiaVideos) só ESTUDA os vídeos dos
parceiros e levanta ideias; ele não mexe em código. Quem aplica é o chat que estiver melhorando. Se o chat pular este
passo, a ideia fica parada para sempre (01/11: 4 aprovadas e ~700 grupos candidatos esperando; nenhuma aplicada desde
25/10).

## O passo a passo (antes da 1ª edição de código)

1. Rodar:
   ```
   python D:\video-fila\aprendizado.py aprovados
   ```
   Isso refaz e mostra o topo de `D:\video-fila\aprendizado\PARA_IMPLEMENTAR.md`.
2. LER `PARA_IMPLEMENTAR.md`:
   - **Seção A (aprovados):** TODOS, sempre. São ordem da dona (ou aprovados sozinhos com nota >= 7).
   - **Seção B (candidatos):** pelo menos os grupos do TIPO que você vai mexer (ex.: mexendo em legenda → todos os
     [legenda]; em narração → [narração]/[roteiro]; em capa → [visual] de capa).
3. Para cada item lido, decidir uma das três:
   - **aplicar** — implantar no projeto que serve, testar num vídeo real (com backup) e OLHAR o resultado;
     ```
     python D:\video-fila\aprendizado.py marcar <ids> aplicado --motivo "projeto/arquivo/função + como testou"
     ```
   - **reprovar** — não serve (já temos, derruba monetização, copia marca do parceiro, não combina com o nicho);
     ```
     python D:\video-fila\aprendizado.py marcar <ids> reprovado --motivo "por que não serve"
     ```
   - **deixar** — serve, mas não cabe nesta tarefa: não marca, e escreve na resposta final por que ficou.
   Aplicado/reprovado entram no `ja_temos.json` e não são sugeridos de novo.
4. Na resposta final para a dona, uma linha: "Aprendizado: X aplicados, Y reprovados, Z deixados (motivo)".

## Cuidados
- Candidato é sugestão, não ordem. Aprovado é ordem, mas ainda precisa de teste real.
- Copiar só a ESTRUTURA do parceiro; nunca marca, texto, logo ou voz dele.
- Nada que derrube monetização (nudez, gore, humor ofensivo). Mascote só como figurinha PNG.
- Antes de aplicar, conferir se já existe no projeto (grep pelo nome do efeito/função).
- Mudou algo que serve a outros projetos? Linha em Novidades de
  `D:\hipercool-videos\docs\MELHORIAS_PARA_TODOS_OS_PROJETOS.md`.

## Longos (engenharia reversa dos canais de referência) — VALE A MESMA OBRIGAÇÃO
Quem mexer em LONGO (título, tags, narração, roteiro, capa, abertura, ritmo) segue
**`D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md`**: lista A FAZER (IDs L-xx), JÁ FEITO (L-Fx, com onde está no
código e como desliga) e DESCARTADO. Antes de implantar, `grep` do ID no código (achou = já feito, não refazer);
implantou = `# L-xx` no código + mover para JÁ FEITO. Fechar com "Longos: X feitos, Y descartados, Z deixados".
Contexto (só leitura):
- `D:\video-fila\linhas\LONGOS\referencias\PADROES_COMUNS.md` (o que se repete nos que dão milhões; seção 4 = lista
  do que copiar, em ordem de impacto);
- `D:\hipercool-materiais\tarefas complexas para fable 5.1\ENGENHARIA_REVERSA (parceiros - o que da views)\ER_07_LONGOS_PRIORIDADE.md`
  (números medidos e o que ainda não foi aplicado).
