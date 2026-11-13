# Captação — preparar a lista antes de ligar

Esta pasta transforma uma lista **bruta** de empresas (como vem de qualquer lugar) numa lista
**limpa e priorizada**, pronta para o Hermes discar. É a etapa que vem **antes** da campanha.

Não acessa a internet, não raspa site nenhum e não liga para ninguém. Só lê os arquivos que
você já tem, arruma e organiza.

## O que ele faz

1. Lê um ou mais CSV, em qualquer formato de colunas (descobre sozinho qual é telefone, nome,
   cidade, site, segmento…).
2. Arruma o telefone para o padrão do WhatsApp (`+55 DDD 9XXXXXXXX`), separa celular de fixo,
   e acrescenta o "9" quando falta num celular antigo.
3. Tira repetidos (mesmo telefone) e junta o que cada linha trazia.
4. Tira quem está na **lista de bloqueio** (quem pediu para não ligar, ou já foi contatado).
5. Dá uma nota **A / B / C** a cada empresa e explica o porquê:
   - **A** = ligar primeiro (celular + segmento-alvo + sinais de que precisa);
   - **B** = ligar depois;
   - **C** = deixar por último (ex.: só telefone fixo, sem sinal nenhum).
   - Fixo nunca é A: o Hermes liga por WhatsApp, e fixo quase nunca tem.
6. Gera dois arquivos na pasta de saída:
   - **`pronto-hermes.csv`** (`telefone,nome`) → é o que entra no Hermes;
   - **`leads-completo.csv`** (tudo + nota + motivo) → é o que vira o CRM.

## Como usar (dois cliques)

Arraste o seu arquivo de leads para cima de **`CAPTAR-LEADS.bat`**. Ele pergunta o segmento-alvo
e gera a pasta `saida\` ao lado. Confira o `pronto-hermes.csv` antes de levar para o Hermes.

## Como usar (comando, se preferir)

```
python processar_leads.py SEU-ARQUIVO.csv --segmento imobiliaria --saida saida
```

Opções:
- `--segmento imobiliaria` — pontua mais quem é do segmento que você escolheu.
- `--bloqueio bloqueio.csv` — CSV com telefones que NÃO podem ser discados (opt-out, já contatado).
- `--so-celular` — joga fora os fixos.
- `--so-nota AB` — mantém só as notas A e B.
- vários arquivos de uma vez: `python processar_leads.py lista1.csv lista2.csv ...`

Exemplo que funciona agora (dados de teste):
```
python processar_leads.py exemplos/leads-brutos.csv --segmento imobiliaria --saida exemplos/saida
```

## Validar no WhatsApp antes de ligar

Na campanha espaçada (48 por dia) **cada número sem WhatsApp gasta uma vaga do dia** e uns 11
minutos de linha — o Hermes só faz o pré-filtro automático no modo imediato. Nos dois primeiros
dias do piloto, 11% da lista não tinha WhatsApp. O `validar-whatsapp.py` confere isso **antes**:
pergunta ao próprio Hermes (que pergunta ao WhatsApp) e separa a lista em dois arquivos.

```
export HERMES_API_KEY=...     (Windows: set HERMES_API_KEY=...)
python validar-whatsapp.py --api http://127.0.0.1:8080 --sid 8653 --entrada saida/pronto-hermes.csv --saida saida/pronto-hermes-validado.csv
```

- Gera **`pronto-hermes-validado.csv`** (só quem tem WhatsApp → é esse que entra no Hermes) e
  **`sem-whatsapp.csv`** (não discar; vale para a lista de bloqueio), na mesma pasta da saída.
- A chave da API vem **só** da variável de ambiente `HERMES_API_KEY` — nunca de arquivo nem de
  argumento. `--sid` é o id da linha no Hermes (a sessão precisa estar pareada).
- **Rode de dentro da VPS** (a porta 8080 não é pública) **ou por túnel SSH**
  (`ssh -L 8080:127.0.0.1:8080 usuario@vps` e aí `--api http://127.0.0.1:8080`).
- **No máximo ~300 números por dia.** O script manda lotes de 50 com pausa de 10 s e para em 300
  (`--max`): a consulta vem da sua linha do WhatsApp e, em excesso, dá cara de robô. Rode de novo
  no dia seguinte — ele pula quem já está nos arquivos de saída e continua de onde parou.
- O progresso mostra os telefones mascarados (só os 4 últimos dígitos). Se a conexão cair ou
  você interromper, o que já foi conferido fica salvo.

## Levar para o Hermes

Hoje (v0.9.0) o jeito que funciona:

1. Abra `pronto-hermes.csv`, **copie a coluna `telefone`** (todos os números).
2. No painel: **Disparo em massa (ligação)** → caixa **"adicionar números manualmente"** → cole →
   "Adicionar".
3. Escolha o agente **"Vendas Hermes Call"**, o número da campanha e o ritmo (começa devagar; ver
   `..\PLANO.md`, Fase 1) → iniciar.
4. A lista rica (`leads-completo.csv`) fica com você para consultar nota, ramo e motivo de cada contato.

> **Limitação conhecida (anotada para melhorar no Hermes):** a caixa de colar números só lê o
> telefone — o **nome da empresa é descartado** ao colar, então a IA não cumprimenta pelo nome.
> O backend já aceita número+nome juntos; falta a caixa aceitar linhas `telefone,nome` (ou subir o
> CSV). Está no `CONTINUAR_DAQUI.md` do Hermes como melhoria pequena de painel.

## Lista de bloqueio — importante (LGPD)

Mantenha um arquivo `bloqueio.csv` crescente com todo número que pedir para não ligar mais e
todo número já trabalhado. Passe-o em `--bloqueio` em toda rodada. O Hermes também guarda os
"não me ligue mais" por conta própria; esta lista é a sua cópia, para não recomeçar do zero.

De onde a lista pode vir, sem problema legal: **`DE-ONDE-VEM-A-LISTA.md`**.

## De onde TIRAR a lista de empresas (pronto): CNPJ da Receita

A pasta **`cnpj\`** monta a lista de empresas sozinha, a partir do cadastro público de CNPJ da
Receita Federal (dados abertos, não é raspagem nem lista comprada). Escolhe o **ramo** (imobiliária,
clínica, cobrança, call center…) e separa quem compra o plano **barato** de quem compra os **caros**,
pelo porte e capital. Sai já no formato que esta ferramenta lê. Ver **`cnpj\README.md`**.
