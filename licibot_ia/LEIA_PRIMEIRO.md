# LiciBot-IA

Robô que lê **todas** as licitações com proposta aberta no PNCP, filtra as que servem para as carteiras
MEI / CPF / AMIGO_SOLAR, baixa itens e documentos, pede a análise a **modelos grátis em cadeia** e avisa
as melhores. Nenhum modelo pago é usado (decisão da dona, 12/11/2026).

## Onde roda
- Produção: **VPS 157** (`ssh hermes-bloqueio`), pasta `/opt/licibot_ia`, venv próprio, cron
  `/etc/cron.d/licibot` (varredura a cada 6 h, sempre com `flock`). Log: `licibot.log`; banco: `licibot.db`.
- Cópia de trabalho: `D:\licibot_ia` (editar aqui e copiar com `scp` para a VPS).
- IA pelo `http://localhost:20128` (OmniRoute), formato Anthropic `/v1/messages`, saída em JSON com schema.
  Se `/opt/omniroute/modo_tokens.json` disser `esgotado`, a IA é adiada (o edital espera, não é perdido).

## IA: só modelos grátis (12/11/2026)
Ordem padrão (ajustável no painel, `ai_analyzer.MODELOS_GRATIS`):
1. `cw/claude-sonnet-5-5` (Sonnet 5.5 web);
2. `genspark-opus-5-5-so` (Opus 5.5 Genspark, sem substituto);
3. `gemini-4-argon`;
4. `gemini-fila` (Gemini 3.8, sempre tem crédito: a garantia, sempre no fim).

Funcionamento:
- Falhou ou ficou sem cota: o modelo fica de lado alguns minutos e o próximo responde.
- Todos falharam 5 vezes seguidas: o resto da fila espera a próxima varredura (aviso no Telegram).
- Não usar:
  - `sonnet-fila` (tem `claude/` pago de reserva);
  - `genspark-opus-5-5` e `1min-opus-5-5` (o substituto é o Opus pago);
  - 1min (o teto de 15 mil créditos não cabe um edital).

## Simulação de investimento (`simulador.py`, aba 💹 Simulação)
"Com R$ X, quanto ganho e em quanto tempo", com o lance que o PRÓPRIO robô daria no automático:
- **Lance:** custo + impostos + margem mínima, 1% abaixo do preço provável do vencedor; só disputa se ganha.
- **Preço:** calculado só sobre os itens que atendemos (o custo da IA também é desses itens).
- **Chance:** a da IA × `realismo` (padrão 30%, até haver histórico próprio de vitórias).
- **Dinheiro:**
  - em média só sai nas que ganha;
  - a reserva cobre ganhar todas da mesma semana;
  - volta quando o órgão paga (federal ~15 dias, estadual ~35, municipal ~45 depois da entrega).
- **Serviço:** limitado pelas horas/mês da dona.
- **Resultado:** mostra pessimista / esperado / se ganhar todas. É estimativa para decidir, não promessa.

## Painel de controle
- **https://licitacoes.157-173-207-22.sslip.io/?k=CHAVE** (chave em `/opt/licibot_ia/painel.chave`).
  Na 1ª visita a chave vira cookie (1 ano) e a URL fica limpa.
- `painel.py` (serviço systemd `licibot-painel`) escuta só em 127.0.0.1 e 172.18.0.1:20180; o HTTPS vem do
  Traefik por um nginx no Swarm (`docker stack deploy -c painel_stack.yml licibot`, serviço `licibot_painel`).
- Mostra números, oportunidades (ordena/filtra/CSV/busca), fila, descartadas, varreduras, CNAEs e log;
  detalhe de cada edital com análise, dinheiro, exigências, riscos, itens e documentos.
- Botões reais: rodar/parar varredura, ligar/desligar o cron, ajustes (gravados em `ajustes.json`, que vale
  por cima do `.env`), "vou participar"/"ignorar" + anotação, reanalisar, avisar agora.
- Todas as datas do banco ficam em horário de Brasília.

## Comandos
```
venv/bin/python main.py --scan              # varredura completa
venv/bin/python main.py --scan --sem-ia     # só PNCP (não gasta Opus)
venv/bin/python main.py --stats             # números e as melhores abertas
venv/bin/python main.py --ver <numeroPNCP>  # tudo sobre um edital (JSON)
venv/bin/python main.py --reanalisar        # devolve à IA os que falharam 3x
venv/bin/python main.py --export-ranking-cnaes
venv/bin/python main.py --teste-filtro "texto do objeto"
```

## Fila de cada edital (`status`)
`novo` → `enriquecido` (itens + texto) → `analisado` (IA) → aviso se `nota_final >= NOTIFICAR_SCORE_MIN`.
Saídas laterais: `revogado`, `expirado` (fechou antes da análise), `sem_analise` (IA falhou 3x por motivo do
edital; falha do gateway/cota não conta tentativa).

## O que aprendi da API do PNCP (testado em 10–11/11/2026)
- `contratacoes/proposta`: `dataFinal` é o limite do **encerramento** da proposta. `dataFinal=hoje` só traz o
  que fecha hoje (81 de ~21 mil). Usamos hoje + 60 dias.
- `tamanhoPagina` entre 10 e 50 (fora disso = 400).
- Mais de ~2 req/s dá **429**. O `Ritmo` em `pncp_client.py` é global para todos os fios e se ajusta sozinho.
- `/itens` sem `pagina`/`tamanhoPagina` devolve só os 10 primeiros.
- Arquivos chegam como `application/octet-stream`: o tipo vem da assinatura (PDF, ZIP, DOCX, RAR).
  ~30% dos editais vêm em ZIP. RAR/7z são lidos pelo `bsdtar` (pacote `libarchive-tools`).
- `/itens/{n}/resultados` dá o preço vencedor: guardamos para aprender o desconto real de cada gaveta
  (`--stats` mostra; com 8+ resultados ele substitui o desconto padrão da `config.py`).
- A VPS está no fuso de Berlim; `config.py` fixa `America/Sao_Paulo` para bater com os prazos do PNCP.

## Leitura incremental (11/11/2026)
- Varredura normal lê só `/contratacoes/atualizacao` (publicado ou alterado, inclui revogação) desde a última
  leitura sem falha, com 2 h de folga: ~5 mil registros e ~6 min, em vez de ~27 mil e ~35 min.
- Leitura completa (`/contratacoes/proposta`) quando: 1ª vez, última completa há mais de 20 h, falha na
  anterior, ou `main.py --scan --completa`. A coluna `execucoes.leitura` diz qual foi.
- A atualização traz também editais que não recebem mais proposta (sem `dataEncerramentoProposta`): o estágio 1
  só aceita quem tem prazo futuro.
- Fila da IA: 1º o que fecha em até 30 h (senão vence antes da vez), depois a pré-nota.
- Negativos novos no filtro foram medidos contra 491 análises do Opus: cortam 28 descartes e 0 aprovados.
  Regra para mexer no filtro: medir antes contra o gabarito (`status='analisado'`).
- O texto dos documentos é apagado 2 dias depois do encerramento (itens e análise ficam).

## Custo e volume (medido em 11/11/2026)
- Uma varredura lê ~27,8 mil licitações abertas (Dispensa, Pregão, Credenciamento, Concorrência) em ~38 min;
  ~800 passam no filtro. Na 1ª vez o estágio 2 leva ~2h40 (5 editais/min); depois só entram os novos.
- PDF escaneado: OCR em português (tesseract, máx. `OCR_MAX_PAGINAS`), ~7 s por página, um por vez.
- Acima de `DOCS_ATE_VALOR` (R$ 300 mil, exceto solar) baixa só itens e títulos dos documentos.
- Opus: ~18 s por edital. Com 120 mil caracteres gastava ~44 mil tokens por edital; o texto enviado
  agora é cortado em `IA_TEXTO_MAX_CHARS` (60 mil, repartido entre os documentos).
- A fila da IA é ordenada por `pre_nota` (valor que cabe numa carteira, bom pagador, exclusivo ME/EPP,
  serviço de IA, documento legível) e limitada a `IA_MAX_POR_VARREDURA` (120); o resto fica para a próxima.
- Nota final = 0,65 x viabilidade do Opus + 20 x bom pagador + até 15 pelo líquido. Aviso a partir de 50.

## Regras de dinheiro (em `ai_analyzer.calcular_financas`, não na IA)
- **MEI**: recebe sem retenção; só se `MEI_FATURADO_ANO + lance <= TETO_MEI_ANUAL` (atualize o faturado no `.env`).
  Desenvolvimento de software, web design, consultoria e suporte em TI **não** são ocupações do MEI.
- **CPF** (IN SEGES/ME 116/2021): o lance de comparação já inclui 20%; se vencer, o órgão tira os 20% e recolhe.
  Depois INSS 11% (até o teto) e IRRF 2026 com a isenção/redutor da Lei 15.270/2025.
  Edital exclusivo ME/EPP descarta o CPF.
- **AMIGO_SOLAR**: `COMISSAO_AMIGO_SOLAR` sobre o lance esperado.
- `INSS_TETO` no `.env` é de 2025: **confirmar o de 2026**.

## Pendências
- Escolher o bot do Telegram (nenhum dos atuais é de licitação) e pôr token/chat no `.env` da VPS.
- Conferir no Portal do Empreendedor os CNAEs do MEI em `config.CNAES_MEI` antes de usar a carteira MEI.
- PDF escaneado (sem texto) não é lido: o modelo recebe o aviso "[PDF ... escaneado]".
