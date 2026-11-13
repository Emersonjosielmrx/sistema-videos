# VO3 Propaganda — clipes de anúncio Veo em rotação

> Feito na noite de 2026-07-30/31. **Nada disso está ligado na produção por padrão.**
> Precisa da sua validação antes de rodar de verdade. Segue a regra: não mexi
> no que já funciona.

## O que você pediu

Hoje o short sai assim:

```
INTRO → VÍDEO(criativo, já tem os atrativos) → TRANSIÇÃO → PROPAGANDA(card CTA + voz) → OUTRO
```

Você quer adicionar **mais um tipo de propaganda**: um **clipe Veo 3** que é SÓ o
anúncio do produto (uma cena bonita + fala curta em PT-BR, tipo comercial de 8s).
Gera uma vez por produto, salva, e vai **rodando** eles (rotação) — usando as
**5 contas novas** (conta5..9) só pra isso, sem atrapalhar a geração de conteúdo
das contas antigas.

Ordem alvo quando ligado:

```
VÍDEO(criativo) → VO3-PROPAGANDA(clipe do produto) → PROPAGANDA(card CTA + voz)
```

## O que eu fiz (sem tocar no que existe)

1. **`vo3_propaganda_rotator.py`** (arquivo NOVO). Faz duas coisas:
   - **Gera** o pool: pra cada produto, monta um prompt de comercial Veo
     (cena por produto + fala do `cta_curto` entre aspas + `spoken in Brazilian
     Portuguese`, 9:16, 8s) e chama o **mesmo `gera_auto.py`** de sempre, numa
     das 5 contas de propaganda (via `FLOW_PORT`, uma por vez). Salva em
     `propagandas_pool/vo3/<produto>_<n>.mp4`. É **idempotente** (se já existe,
     reusa) e respeita os exit codes do `gera_auto` (créditos/sessão/pausa).
   - **Rotaciona**: `escolher_vo3_propaganda(produto_id, stem)` sorteia (estável
     por hash) um clipe do produto — igual o `propaganda_pool_pre_gerada.py` já faz.

2. **`montar_final.py`** ganhou uma flag **opcional** `com_vo3_propaganda=False`.
   - **Default é False → produção 100% igual ao que era.**
   - Se ligar, insere o clipe vo3 entre o vídeo e o card CTA. Se o pool estiver
     vazio, **pula silencioso** e mantém o fluxo antigo (testado).

## Contas usadas pra propaganda (as 5 novas)

De `contas.py` (fonte única), estas 5 (tier pro), uma por vez:

| session               | porta | perfil            |
|-----------------------|-------|-------------------|
| fabiovideoseducativos | 9290  | chrome_gen_conta5 |
| fabricadeautomacoes   | 9300  | chrome_gen_conta6 |
| jogoscomia            | 9320  | chrome_gen_conta7 |
| fabricadeautomacoesia | 9330  | chrome_gen_conta8 |
| rezaulkarimul         | 9340  | chrome_gen_conta9 |

## Como usar (quando você aprovar)

**1) Gerar o pool** (1 clipe por produto TOP — Hermes, Avatar, Follow-up, SuperChat):

```bash
cd D:\veo\beta
PYTHONUTF8=1 python pos_producao\vo3_propaganda_rotator.py gerar --tops --n 1
```

Pra TODOS os 9 produtos: troca `--tops` por `--todos`. Pra mais de 1 clipe por
produto (mais variedade na rotação): `--n 2`.

**2) Ver o que já tem no pool:**

```bash
PYTHONUTF8=1 python pos_producao\vo3_propaganda_rotator.py listar
```

**3) Ligar no montar_final** — só passar `com_vo3_propaganda=True` na chamada do
`montar(...)` (quem chama hoje é o `worker_noite.py`). Enquanto não passar, nada muda.

## Decisões que deixei pra você (não adivinhei)

- **Quais produtos** entram na rotação de clipe (deixei default = os 4 TOP).
- **Quantos clipes por produto** (default 1; mais = mais variedade, mais crédito).
- **Se o número do WhatsApp** deve aparecer no clipe Veo. **Não coloquei na fala**
  porque o Veo erra número falado; o número continua no **card CTA** que vem
  depois. Se quiser o número no clipe, dá pra sobrepor por cima (ffmpeg) depois.
- **Quando ligar** a flag no worker (não liguei — produção intocada).

## Custo / risco

- Gerar o pool gasta crédito Veo **uma vez** por clipe (não a cada vídeo).
- Roda serial (o Flow serializa o Chrome mesmo), então é lento mas seguro.
- Se alguma conta estiver sem crédito/deslogada, ele pula e segue nas outras.
