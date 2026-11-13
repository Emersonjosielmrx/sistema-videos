# 08 — Automação do Veo/Flow frágil
> **PROJETO: LONGOS** — recap longo de anime/manhwa do recapd (`D:\recapd-ambientes\producao`, linha `D:\video-fila\linhas\LONGOS`). Escrito pela sessão Opus da linha LONGOS em 28/10/2026.

**Fatos de 28/10:** (1) `gera_auto` baixou o vídeo de OUTRO robô da mesma conta (homem com placas solares no lugar da
mascote): ele detecta "mídia nova no projeto" e, quando o bloco novo é imagem, tenta uma "URL construída" que pegou um
vídeo antigo; (2) "o texto não entrou na caixa do pedido"; (3) "caixa de prompt não achada" 2x; (4) conta "só
notebook" escolhida com os notebooks desligados (`SO_NOTEBOOK`) 3x seguidas; (5) imagem enviada sem "ver a miniatura".

**29/10 (6) conta emerson2030 (porta 9360):** botão "nova sessão" não aparece, "painel de ajustes falhou" e "envio da
imagem falhou" → o pedido vai SEM imagem e sem modo vídeo e o Flow gera IMAGEM (bloco IMG sem /asb/) → "timeout sem
vídeo novo baixável" depois de 30 min, 2x seguidas. O gera_auto segue em frente mesmo com o ajuste/imagem falhando —
devia parar (antes de gastar crédito e tempo) e trocar de conta.

**Onde olhar:** `D:\veo\beta\gera_auto.py` (`_gerar_impl`, `_video_do_bloco`, `midias`, `_subir_imagem`),
`cron_gerar_video_llm.py` (`escolher_sessao`, `_maquina_livre_para`), `D:\postador-de-videos\bin\cadeia_veo.py`,
`maquina_remota.py`. Logs: `D:\veo\beta\logs\`, `D:\hipercool-materiais\mascote_waifu_v2\veo.log`.

**O que falta:** identificar o vídeo pelo PEDIDO (prompt/id do job) e não por "o que apareceu de novo"; conferir o
conteúdo baixado (rosto/fundo); saber em tempo real se notebook está ligado antes de escolher conta. Remendo atual
na mascote: `mascote_producao._e_ela` (fundo branco) + preferir contas do PC1.

## Fable — resultado
**29/10 (Fable) — caminho, não implementação (o `gera_auto` está sendo revisto por outra sessão em 29/10; mexer
junto quebra os dois).**
1. **Identificar pelo pedido:** a peça já existe no projeto navegador-sem-navegador — `services\veo_flow\flow_gerar.py`
   gera por HTTP e `flow_http.py` fala com `FlowService.BatchCheckMediaGenerationStatus` (lista de ids de mídia por
   job) e o download por id. Trocar no `gera_auto._video_do_bloco` o "mídia nova no projeto" por "mídia cujo id veio
   do job que EU abri" acaba com o vídeo de outro robô (e com a "URL construída"). Enquanto o DOM continuar: gravar o
   nome/prompt do pedido no `postar.json` do bloco e recusar mídia cuja data de criação é anterior ao pedido.
2. **Conferir o conteúdo baixado:** mesma trava do produto (YuNet + SFace, memória `project_veo_foto_funil`): embedding
   do 1º quadro × foto-base da mascote/dono, recusar < 0,6 e tentar o próximo id do job. `_e_ela` por fundo branco é
   fraco (o robô errado também tinha fundo claro).
3. **Notebook ligado antes de escolher conta:** `maquina_remota.Remoto(nome).vivo()` (SSH, 25 s) já é a verdade;
   o `cadeia_veo._livre` chama; o `escolher_sessao` do cron escolhia a conta ANTES da cadeia. Ordem certa: cadeia →
   máquinas vivas → contas dessas máquinas (`contas.perfil_notebook`), nunca o contrário. Desde 24/10 há também
   `maquina_remota.exibindo()` (telão tocando) — 29/10 o Flow de imagens entrou no Acer em cima de um vídeo por não
   usar isso; já está no `tentativas()`/`tentar()`.
4. "Texto não entrou na caixa"/"caixa não achada": sintoma clássico de pedir pelo DOM com a página meio carregada;
   o caminho 1 (HTTP) elimina os dois. Até lá, `wait_for_selector` da caixa + conferir `inner_text` depois de digitar
   antes de clicar em enviar (ler de volta o que foi digitado, como o `tiktok_notebooks` faz).
