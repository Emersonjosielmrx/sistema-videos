# Flow Imagens — gerador de imagem pelo Google Flow

Criado em 22/10/2026 a pedido do dono ("um gerador igual ao do Veo 3, mas de foto, que lá no Flow tem os modelos mais atuais").

## Como usar

```
D:\veo\venv\Scripts\python.exe D:\flow-imagens\gera_imagem.py "prompt" saida.png
    [--ref foto.jpg ...]          imagem(ns) de referência (editar/continuar uma foto real)
    [--formato 9:16]              16:9 | 4:3 | 1:1 | 3:4 | 9:16
    [--modelo "Nano Banana 2.1"]  "Nano Banana Pro" | "Nano Banana 2 Lite" | "Nano Banana 2.1" (padrão, o mais novo)
    [--quantidade 1..4]           mais de 1 = saida_1.png, saida_2.png...
    [--conta mundosolar]          sem isso tenta as contas do Veo em ordem até uma entregar
    [--max-contas 2]              no máximo N contas
    [--maquinas x200ma,acer]      (24/10) só essas máquinas; sem "pc1" na lista = nunca abre Chrome no PC1
```

`maquinas=` (24/10): a foto na hora do Veo (`D:\veo\beta\foto_na_hora.py`) passa as máquinas que a cadeia do Veo
liberou (notebook sem telão, desktop sem chamada, PC1 só sem pausa de carga). Antes ela abria Chrome no PC1 em pausa de
carga. Sem o parâmetro, nada muda para os outros projetos.

Em Python: `from gera_imagem import gerar_imagem` → lista de arquivos (levanta erro se nenhuma conta gerou).
Precisa do Python do Veo (`D:\veo\venv`), porque usa `playwright` e `filelock` de lá.

## Nos outros projetos (`cliente.py`, desde 22/10)

`cliente.gerar(prompt, saida, formato)` → Path ou None. Roda com qualquer Python (só biblioteca padrão; chama o
gera_imagem com o Python do Veo), no máximo 3 contas por imagem, e devolve None na hora se o PC não tem o Flow (PC2),
se `FLOW_IMAGEM=0` ou se o Flow falhou há menos de 30 min (`logs\cliente_pausa.json`). Onde já está ligado: ver
`INTEGRACAO.md`.

## Como funciona

- Usa as mesmas contas, os mesmos perfis do Chrome e a **mesma trava de porta** do Veo (`D:\veo\beta\contas.py`, `logs\.cdp_lock_<porta>`).
  Se o Veo está usando a conta, espera até 2 min e passa para a próxima.
- Reaproveita as funções do `D:\veo\beta\gera_auto.py`: login, crédito, nova sessão, envio de foto e grade de mídias.
- No painel "Configurações do agente" deixa o bloco **de imagem** com o formato, a quantidade e o modelo pedidos
  (o bloco de vídeo não é mexido) e "Confirmar antes de gerar" = Nunca.
- Baixa só as imagens **novas** da grade. A foto de referência também aparece na grade, então qualquer imagem idêntica
  a uma referência é descartada.
- **Quem abre fecha** (22/10, dono: "o Flow não está fechando depois do serviço e fica ocupando espaço"): se o Chrome da
  conta não estava aberto, ele é aberto dentro da trava da porta e fechado no fim (`gera_auto.fechar_chrome`, pelo CDP
  pra gravar os cookies, taskkill se travar). O mesmo vale pros vídeos do Veo (`gera_auto.gerar`; backup em
  `gera_auto.py.bak_20261022_fechar_chrome`). Chrome que já estava aberto (login manual etc.) não é fechado.
  `FLOW_MANTER_ABERTO=1` desliga o fechamento nos vídeos.
- "The agent is experiencing high demand / Try again" (visto 22/10 na seebotsia): aperta "Tentar novamente" até 3x.
  Espera no máximo 150 s pela imagem; falhou → print + texto da tela em `logs\falhas\` (prova do motivo).
- Painel de ajustes que não abre (às vezes, com a página ainda carregando) não derruba: o pedido já cita modelo e formato.
- Conta que falha fica fora da lista: 3 h se for login ou crédito, 20 min no resto (sem entregar, alta demanda) (`logs\contas_fora.json`); conta só
  ocupada pelo Veo não conta como falha.
- **Todas as contas** (23/10, dono: "use o Veo em todas as contas que temos TikTok e YouTube"): as contas Google
  logadas nos notebooks (x200ma, acer, desktop; PC2 nunca) entram como "só notebook" em `D:\veo\beta\contas.py`
  (36 contas, 23 só notebook). Cada pedido sorteia uma delas se alguma máquina está livre; senão usa as contas do PC1.
  Conta só notebook nunca abre Chrome aqui.
- Conta que nunca abriu o Flow mostra uma janela de cadastro ("Conheça e molde ferramentas de IA…" → Avançar →
  Política de Privacidade → Continuar). `gera_auto._passar_boas_vindas` passa por ela sem marcar e-mail de marketing
  e cria o projeto. Teste 23/10: mentoriaiapro no x200ma → `_diag\teste_mentoria.png` (0 crédito, saldo 1050).
- Quem usa: carrossel do MS Energy (`D:\ms-energy\bin\carrossel_ms.py`, desde 22/10).
- Cada geração fica registrada em `logs\geracoes.jsonl` (conta, modelo, créditos antes e depois, arquivos, tempo).

## Testes de 22/10 (conta mundosolar)

| Teste | Resultado |
|---|---|
| Texto → telhado com placas no Norte do Brasil, 9:16, Nano Banana 2.1 | `saidas\teste_telhado.png` 768x1376, ~30 s, **0 crédito** (50 → 50) |
| Foto real do MS Energy + "mesmo lugar, só luz de pôr do sol" | `saidas\teste_ref.png` com o mesmo telhado e ângulo, 0 crédito |

O tamanho da saída é o que o Flow entrega na grade (~768x1376 em 9:16). Os modelos Pro e 2 Lite ainda não foram testados
(custo e tamanho desconhecidos).

## Cuidados

- Imagem de IA só **ilustra**. Nunca apresentar como "instalação da empresa" nem como cliente real (regra do MS Energy).
- Recusa por política (pessoa famosa etc.) para de tentar nas outras contas: o problema é o pedido, não a conta.

## 16/11 — "sem máquina" com as máquinas PARADAS (causa raiz e conserto, vale pra TODO o Flow de imagem)
Medido em `logs\pedidos_falhos.jsonl`: 413 de 417 pedidos falhos (desde 14/11) tinham PC2/STI/desktop LIVRES.
1. **Limite preso em 1** (`logs\capacidade.json`): `cap_falha` contava qualquer `TimeoutError` do Playwright (botão do
   Flow que não apareceu) como falta de capacidade; com limite 1 + teto 1 nunca subia. Agora: só falha da MÁQUINA
   (Chrome/porta/túnel/ssh/sem resposta), mede antes de baixar (folgada = não baixa), teto mínimo 2, e grava em
   `capacidade.json` -> `baixou` quem baixou (pid, script, motivo, cpu/ram).
2. **CPU medida errada**: medida ÚNICA agora em `D:\video-fila\maquinas.PS_CPU` (média de 3 amostras; no desktop o
   LoadPercentage vem vazio -> tempo de CPU dos processos). Usada por gera_imagem (`_ps_cpu`), maquinas.PS_MEDIR e
   `D:\postador-de-videos\bin\workers.py`.
3. **Ordem**: STI -> PC2 -> desktop -> notebooks (`FLOW_NOTEBOOK_PRIMEIRO=1` volta).
4. **Vigia** `vigia_capacidade.py` (tarefa VigiaCapacidadeFlow, 10/10 min, oculta; `VIGIA_CAPACIDADE=0`): limite abaixo
   do piso (PC2 4, STI 5, desktop 3) com a máquina folgada -> devolve; log `logs\vigia_capacidade.log`.
   Por quê: processo que IMPORTA o gera_imagem (produto.diario, carrossel_marca, foto_na_hora) segue com o código
   antigo até reiniciar.
Backups: `gera_imagem.py.bak_16nov_capacidade`, `D:\video-fila\maquinas.py.bak_16nov_cpu`, `workers.py.bak_16nov_cpu`.
