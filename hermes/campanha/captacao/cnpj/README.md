# Captar empresas pelos Dados Abertos do CNPJ

Monta a lista de empresas da campanha a partir do **cadastro público de CNPJ da Receita Federal**.
São dados abertos, publicados todo mês pela própria Receita — não é raspagem, não é lista comprada.

De cada empresa vêm: razão social e nome fantasia, **atividade (CNAE = o ramo)**, **porte**,
**capital social**, quantos estabelecimentos tem, cidade, e **o telefone que a própria empresa
declarou** à Receita. Com isso dá para escolher o ramo e separar quem compra o plano barato de
quem compra os caros.

## O que é "barato" e "caro" aqui

- **barato** = cabe no plano Start (199) e normalmente o dono decide rápido: imobiliária, clínica,
  estética, autoescola, academia, contabilidade, concessionária… (ramos em `segmentos.json`).
- **caro** = operação de volume, perfil Pro/Scale/Enterprise: cobrança, call center, financeira,
  consórcio, plano de saúde, provedor, incorporadora, agência de marketing, software…
- Uma empresa de ramo "barato" **sobe para "caro"** sozinha se for grande (porte médio/grande,
  capital alto, ou várias filiais). O motivo fica escrito em cada linha.

Os códigos de ramo (CNAE) em `segmentos.json` já foram conferidos contra a tabela oficial da
Receita: todos existem. Para mudar os ramos, é só editar esse arquivo.

## Passo a passo

Tudo roda num lugar só (precisa de ~8 GB de download + ~15 GB livres para processar). Dá para
rodar no PC ou numa VPS. No PC:

```
cd captacao\cnpj

python captar_cnpj.py baixar --mes 2026-09 --pasta dados
    baixa os arquivos do mês (continua de onde parou se cair). ~8 GB.

python captar_cnpj.py extrair --pasta dados --saida base.csv.gz
    lê os ~60 milhões de estabelecimentos, guarda só os dos ramos escolhidos, ATIVOS e
    com telefone; junta porte/capital/filiais; marca MEI; separa barato/caro. ~10 min.
    (--uf PA,AM  limita a saída a esses estados; --com-mei inclui MEI)

python captar_cnpj.py fatiar base.csv.gz --segmento imobiliarias --uf PA --nivel barato
       --so-celular --limite 300 --saida lista.csv
    tira uma fatia pronta: um ramo, um estado, um nível, com celular, as 300 melhores.
```

Depois, a fatia passa pela limpeza/pontuação normal da captação:

```
python ..\processar_leads.py lista.csv --segmento imobiliarias --so-celular --saida saida
```

e o `saida\pronto-hermes.csv` é o que entra no Hermes.

## Proteção (LGPD), ligada por padrão

- **MEI fica de fora** (o telefone costuma ser o celular pessoal do dono). `--com-mei` inclui.
- **Só empresa com situação ATIVA** na Receita.
- **Empresário individual** é marcado na coluna `individual` (o telefone pode ser pessoal) —
  `--sem-individual` no `fatiar` tira esses.
- É telefone **comercial, declarado pela empresa à Receita**, de registro público. Ainda assim:
  a IA se identifica, "não me ligue" vale na hora, e guarde sua `bloqueio.csv`. Ver
  `..\DE-ONDE-VEM-A-LISTA.md`.

## Por que tão grande

O cadastro é o Brasil inteiro (~60 milhões de estabelecimentos). O download é uma vez por mês;
depois o `base.csv.gz` fica pequeno (só os ramos que interessam) e o `fatiar` é instantâneo. A
Receita limita a velocidade por conexão, então o `baixar` usa várias conexões em paralelo.

## Testado com dados reais (08/10/2026)

Rodado na VPS de teste sobre o cadastro de setembro/2026:
- baixado o mês inteiro (~6,6 GB) e lidos **70 milhões de estabelecimentos**;
- a base ficou com **2,37 milhões de empresas** dos 23 ramos (1,9 mi "barato", 481 mil "caro"),
  só ativas e com telefone — arquivo `base.csv.gz` de 155 MB (reutilizável; o `fatiar` é instantâneo);
- exemplos de ramo: clínicas 617 mil, imobiliárias 165 mil, software 213 mil, contabilidade 109 mil;
- fatia "imobiliárias de SP" (40.020 empresas) → a nota separou: 2.234 **A** (as grandes/incorporadoras),
  27.209 **B**, 10.577 **C** (quase todas só fixo); metade tem celular/WhatsApp.
