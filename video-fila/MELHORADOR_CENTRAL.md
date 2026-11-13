# Melhorador central — um sistema para melhorar todos os vídeos (29/10/2026, Fable 5.1)

**Pedido da dona (29/10):** "hoje tem chats abertos analisando cada vídeo, um sentinela que manda 'continue' quando
volta token, e um melhorador por linha; eles trabalham separados, um sai depois outro. Quero centralizar: um único
sistema que melhore todos os vídeos analisando os vídeos que vão saindo, trabalho contínuo sempre que tem tokens."

## O que é
`D:\video-fila\melhorador_central.py` + tarefa do Windows `MelhoradorCentral` (a cada 10 min, escondida, prioridade
baixa). Não reescreve os melhoradores das linhas (Cortes, Longo, Produtos, Claude Code Video): **usa os quatro**,
cada um com a sua análise → decisão → alavancas com faixa → revisor → desfazer. O central decide **quem roda, quando,
com que dados e com que botão**.

## A cada passada (10 min)
1. **Feed único:** vídeos dos últimos 7 dias de todas as linhas (ledger do postador, `_postados` dos produtos) com
   os dados reais: elegível no feed (ER_01: "continuaram" 100% e < 10 views = não mostrado), % assistido, impressões
   e CTR, curva de retenção (`ret_meio/ret_fim`), QA (`qa.json`), partes que faltaram (`faltou.json`), views/curtidas
   do Instagram (`medidas`).
2. **Brief por linha** em `estado\central\brief_<linha>.md` (números por canal, os que mais renderam, QA, faltou e as
   regras D1 — "o que decide views"). Nas linhas Cortes e Longo o brief entra **entre marcas** no `LICOES.md` que o
   melhorador já lê em toda decisão; Produtos/CCV recebem o caminho na variável `CENTRAL_BRIEF`; Hipercool e Veo
   ganham `BRIEF_CENTRAL.md` (ainda sem melhorador próprio: a melhoria deles é pelo chat/docs).
3. **Pressão:** nota por linha = vídeos novos desde a última rodada dela + 2×(QA com problema + faltou) + 2×(quão
   longe de 65% assistido + fração de não elegíveis). Roda **só a linha com mais pressão**, uma por passada, nunca a
   mesma antes de 1 h. Assim a produção de uma linha não espera a outra "sair": quem tem vídeo novo e resultado ruim
   vai primeiro.
4. **Tokens:** 1 teste de 5 tokens no gateway (`ia_reserva.testar`) antes de rodar. Sem modelo vivo = espera; voltou
   = continua sozinho e avisa. Também exige RAM livre ≥ 2,5 GB. É isso que substitui o "continue" nos chats: não há
   chat — é tarefa; e a linha roda pelo `baixa_prioridade.py` (não disputa com a produção).
5. **Telegram:** 1 linha por rodada (origem "melhorador central", pelo portão do `avisos.py`).

## Botão único
```
python D:\video-fila\melhorador_central.py ligar            # modo SOMBRA: cada linha decide e anota, não aplica
python D:\video-fila\melhorador_central.py ligar --aplicar  # liga as 4 linhas de vez (controle.json + configs) e elas APLICAM
python D:\video-fila\melhorador_central.py desligar         # desliga o central E as 4 linhas
python D:\video-fila\melhorador_central.py status | brief | volta --simular
```
Começa **desligado**. Em sombra, o que cada linha decidiria fica nos arquivos dela (`SOMBRA.md`, `estado\sombra`,
ensaio dos produtos) — dá para conferir antes de ligar `--aplicar`.

## O que continua valendo das linhas (o central não passa por cima)
- Modelos: só Argon (prazo curto) → Gemini 3.8 → Gemini 3 (regra da dona: nada de Opus/Kiro/Fable em pipeline).
- Alavancas com faixa, código nunca mexido pelo decisor (Produtos/Cortes) ou só em caixa isolada com backup (Longo/CCV).
- Revisor adversário, vigia de piora, desfazer sozinho, lições.
- O `melhoria_continua.py` (motor genérico por projeto, que mexe em código) fica como está (PARADO desde 26/10).

## Relação com o que já existe
| Peça | Antes | Com o central |
|---|---|---|
| Chats abertos analisando vídeo | 1 por linha, param sem token | nenhum necessário para melhoria rotineira |
| `sentinela_disparo.py` ("continue") | acorda chats quando o crédito volta | continua útil para os chats da dona; a melhoria não depende dele |
| 4 melhoradores (tarefas separadas) | cada um na própria tarefa, desligados | disparados pelo central pela pressão; ligados/desligados pelo botão único |
| Dados reais (ER_01/02, QA, faltou) | ninguém lia | brief em toda decisão |

## Como medir que está funcionando
`estado\central\estado.json` (`rodadas`, `historico`, `notas`), `logs\melhorador_central.log`, `logs\melhorador_central\<linha>_*.log`.
Semana a semana: % de vídeos elegíveis e % assistido mediano por linha (brief) devem subir; QA ruim e faltou, cair.

## Decisões e como desfazer
`D:\hipercool-materiais\tarefas complexas para fable 5.1\FABLE_DECISOES.md` (D12). Desfazer = `desligar` + apagar a
tarefa `MelhoradorCentral` (`schtasks /delete /tn MelhoradorCentral /f`). Os blocos entre `<!-- central:inicio -->` e
`<!-- central:fim -->` nas LIÇÕES podem ser apagados à mão.

## Modelos: Argon × Opus × os dois (29/10, D14)
Aba **Modelos da IA (Argon / Opus)** no painel :8790 (ou `python melhorador_central.py modelos argon|opus|ambos|auto`):
- **Argon** — quando a dona está gastando o Opus no chat (decisor gemini-4-argon → argon-pro → Gemini 3.8; revisor Gemini).
- **Opus 5.5** — quando ela não está (decisor cc/claude-opus-5-5 → Argon; revisor Opus).
- **Os dois** — Argon decide, Opus revisa (gasta pouco Opus, ganha o veto do melhor).
- **Auto** — Opus só se não há sessão de chat ativa há 30 min E há conta CC com cota; senão Argon.
O analista (olha os quadros) fica sempre no Gemini 3.8. O conjunto vai às linhas pela env `CENTRAL_MODELOS`; fora do
central cada linha usa a cadeia própria. Nunca Kiro.
**Bancada** (botão na aba, ou `python bancada_modelos.py`): mesma tarefa real dos Cortes para cada modelo; o Opus 5.5
responde e dá nota anônima a cada um (diagnóstico, alavancas, risco, distância da resposta dele, ideia de melhorar).
Resultado em `estado\central\bancada\<data>\BANCADA.md` e no `D:\gemini-argo\COMPARACAO_MODELOS.md`. Nada é aplicado.
