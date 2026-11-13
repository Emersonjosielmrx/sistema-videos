# Créditos rígidos + fila central do Flow/Veo (pedido da dona, 01/11/2026)

> "Adicione um controle de créditos rígido para todos os projetos que usam Veo, assim como fazemos no Argo, no Claude
> web, no Opus grátis Genspark e no 1min, para que ele não fique tentando usar contas que não têm créditos e saiba
> exatamente quanto crédito tem cada uma. Cada conta recebe créditos para ~150 vídeos no mês mais 50 todo dia:
> priorizamos as que têm muito primeiro, com rotação para não estourar nenhuma; quando todas tiverem só os 50 do dia,
> aumentamos a rotação. Enquanto está fazendo o vídeo/imagem, prioridade máxima para não falhar (falha = retrabalho).
> Uma fila independente do projeto, sempre rodando, onde cada projeto insere o que vai gerar; havendo recurso, abre
> uma 2ª fila, uma 3ª, até ver que uma está caindo, aí diminui até estabilizar — pelo menos uma nunca para. O que os
> chats pedirem tem prioridade (geralmente é teste e eu estou esperando)."

## Diagnóstico (01/11 10h)
- O painel de saúde (`D:\projeto-navegador-sem-navegador\tools\saude.py` → `relatorios\saida\saude.json`, chave
  `flow`) JÁ lê por HTTP, a cada poucos minutos, o saldo real (GetCredits, rpc `nzlxg`) de toda conta em toda máquina
  (`conta@maquina`). Ninguém usava: em 01/11 eram **51 contas logadas, 33.230 créditos (~1.660 vídeos a 20)**.
- `creditos_contas.json` tinha "50" velho em quase todas (só lia o saldo quando a conta abria o Flow para gerar).
- `sessoes_status.json`: ~50 contas com castigo de 6 h "login caiu ou conta bloqueada no Flow" (exit 3 do gera_auto),
  mas o painel lia as mesmas logadas com 1050. O castigo é POR CONTA e vale em TODAS as máquinas; a falha era da
  máquina/tentativa (ex.: emersonjosiel1995 tentada no PC1, onde não está logada — 20 min e exit 3 — embora tenha 1050
  no acer e no PC2). Resultado: "48 sessões em cooldown" e Veo pausado com o banco cheio de crédito.
- A MESMA conta tem saldo diferente por máquina (simonerebecaluizasilva: pc2 1020, notebooks 50; muitas com
  `desktop` 50): o cookie de cada máquina pode estar noutro login do Google → o saldo que vale é o da máquina onde gera.
- "Abrem várias de uma vez": cada projeto (veo cron, ms-energy/solares, foto_na_hora, claude-code-video, cadeia_veo)
  chama o gera_auto por conta própria; a única coordenação é a trava por porta (`.cdp_lock_<porta>`) e a reserva de
  notebooks. 1 notebook = 1 geração; com os notebooks ocupados os outros projetos ficam trocando de conta "sem castigo"
  (09:34–09:45 de 01/11, 9 tentativas da Globo) até cair numa conta do PC1.

## FEITO em 01/11 (MVP)
1. `veo\beta\flow_saldo_real.py` — saldo real por conta e por máquina a partir do saude.json (leitura ≤ 45 min).
   `python flow_saldo_real.py` lista tudo.
2. `creditos_contas.py`:
   - `real(sess, maquinas)`; `fora()` usa o real (< 20 = fora; ≥ 20 = dentro, mesmo com "50" velho no json).
   - `ordenar(cands, maquinas=)`: saldo real NAS máquinas da etapa, em faixas de 100; mesma faixa reveza pela que
     gerou menos hoje; 1000+ antes; quando só sobram as de ~50 do dia, todas na mesma faixa e o rodízio é só pelo uso.
3. `cron_gerar_video_llm.py`:
   - `escolher_sessao`: etapa usa `ordenar(..., maquinas=_maqs_et)`; sem etapa (ms-energy/solares) as de notebook vêm
     por crédito real em vez de sorteio.
   - `_castigo_desmentido`: castigo de "login caiu/deslogada" numa conta que o painel leu logada com ≥ 20 créditos
     DEPOIS do castigo sai (no máx. 1x/h por conta). No teste: 52 de 60 contas livres (antes ~8).
   Vale para todos que importam `escolher_sessao` (veo cron, ms-energy gerar_short_veo/cenas_veo, reel_advance/globo).

4. (01/11 13h40) `gera_auto._gerar_nos_notebooks`: máquinas onde o painel lê a conta deslogada (`flow_saldo_real
   .conta()["mortas"]`) saem da lista; "pediu login" por HTTP numa máquina passa para a PRÓXIMA (antes dava exit 3 na
   hora — en1653964 com 1030 no x200ma/acer caía no desktop deslogado). Exit 3 só se todas as tentadas pedirem login.

## FALTA (ordem sugerida)
1. **Castigo por conta@máquina** (não por conta): `marcar_conta_fora` / `sessao_em_cooldown` com a máquina; o
   gera_auto/cadeia escolhe a máquina onde a conta está viva e com saldo (flow_saldo_real.conta()["maquinas"]).
   Conta "do PC1" que só está viva nos notebooks não pode ir para o PC1.
2. **Fila central única** (`D:\video-fila\fila_flow\`?): serviço sempre ligado (tarefa oculta), projetos só INSEREM
   pedidos `{projeto, tipo: video|imagem, prioridade, prompt/foto, destino, callback}` e esperam o arquivo pronto.
   Prioridades: `chat` (pedido de sessão do Claude com a dona esperando) > clientes (solares) > produtos > Veo de
   reserva/entretenimento. Hoje cada projeto chama o gera_auto direto — migrar um por vez (solares primeiro).
3. **Paralelismo adaptativo**: começa com 1 trabalhador; com máquina+conta livres e taxa de falha < X% nos últimos N,
   abre o 2º, o 3º...; falha subindo → fecha 1; nunca menos de 1. Limite natural = máquinas com Flow (pc1, pc2, x200ma,
   acer, desktop) × 1.
4. **Prioridade máxima durante a geração**: processo do gera_auto/worker em `HIGH_PRIORITY_CLASS` (hoje roda em
   prioridade baixa em vários lugares) e a máquina reservada (os outros robôs não abrem Chrome nela). Chrome só os
   ~40 s do token (HTTP) — investigar onde ainda abre janela/gera pela tela.
5. **Modelo de crédito da dona** (~150 vídeos/mês + 50/dia): o saldo do GetCredits é um número só. Confirmar no
   Flow se dá para separar mensal x diário (rpc de detalhes?) — senão manter a regra das faixas.
6. Ler o saldo real também ANTES de cada geração (1 GET, ~1 s) em vez de depender do painel (que roda de 5 em 5 min).
7. Cookies que caíram (painel: emersonjosiel2027, vendeafiliados3@x200ma, jornalcomia@acer, inovaremanhwaverseita@pc2,
   fabricadeautomacoesia@acer...): login em lote (`login_em_lote.py`).
