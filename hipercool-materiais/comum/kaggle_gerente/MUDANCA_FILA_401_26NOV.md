# Central do Kaggle — fila e 401 (26/11/2026)

Pedido da dona: "tente resolver as 5 e ajuste o sistema de uso do Kaggle pra conseguirmos fazer o máximo possível com o
mínimo possível de paradas". Arquivo: `vps_central.py` das 4 centrais (`/opt/recap_central/` nas 3 VPS e
`D:\recap_central_casa\` na casa).

## O que estava acontecendo (lido no central.log da hermes-prod, sem falar com conta)
- **Fila do próprio Kaggle**: 5 contas lançadas 09:25-10:55 em `kernelworkerstatus.queued` (o Kaggle não dava GPU).
  O log mostra a fila crescendo desde 21/11 (por dia: 530-560 "em fila" de 21 a 24/11; 25/11 = 44 rodando;
  26/11 = 0 rodando). A central só soltava a vaga depois de **6 h** e ainda punha a conta de **descanso de 12 h**.
- **401 em 11 contas** (hermes-prod): voltava "401 na cota — descansa 12 h" a cada 12 h, para sempre. 401 = chave
  recusada (token velho/revogado) ou conta **banida** — o incidente de 02/11 também começou com 401 em massa.
- Pesquisa (web, com fonte): Kaggle limita **2 sessões de GPU por conta**; cota renova **sábado 00:00 UTC**; kernel
  preso em "Queued" é falha conhecida desde 09/11; 401 é autenticação, não cota. A central já lança só com
  `enable_gpu: true` (sem acelerador explícito) — a pista "acelerador trava a fila" não se aplica.

## O que mudou
1. **Fila**: limite **6 h -> 1,5 h** (`KAGGLE_QUEUED_MAX_H` ou `config.json` `kaggle.queued_max_h`). Ao estourar, só
   **solta a vaga** — a conta NÃO vai mais pro descanso de 12 h (ela não tem defeito). Ela fica fora só **6 h**
   (`KAGGLE_FILA_PAUSA_H` / `kaggle.fila_pausa_h`), pra não abrir uma 2ª sessão por cima do kernel que ainda está
   na fila (limite de 2 sessões por conta). Estado: `est["fila_kaggle"][conta] = hora`.
2. **401 repetido**: conta `est["n401"]`. 1º 401 = descanso de 12 h (como antes). **2º 401 seguido = para de tentar**
   (motivo "sem internet: 401 repetido…", que só volta com `python3 vps_central.py liberar <conta>`) e **avisa a dona
   1 vez no Telegram**. Cota medida sem erro zera o contador; `liberar` também zera.
3. Hermes-prod também recebeu a correção do **estado.json de 0 bytes** (que travou a central de 21 a 26/11), que só
   a central da casa tinha.

## Versões (cada central tinha uma diferente — cuidado ao publicar!)
| central | antes | depois | backup |
|---|---|---|---|
| hermes-prod | 4980ae79 (1279 linhas: _pausada com data, _motivo_do_log, _dono_kaggle, fila_teste_voz...) | **0ba7eeb5** | vps_central.py.antes_fila_401_2611 |
| hermes-staging | d08784fd (1129) | e3d0b3d5 (versão da casa + mudanças) | idem |
| hermes-bloqueio | d08784fd (1129) | e3d0b3d5 | idem |
| casa (D:\recap_central_casa) | adb69d45 (1177: + manter_teste/vaga de teste + estado vazio) | e3d0b3d5 | idem |
**Atenção:** às 14:40 eu publiquei por engano a versão da casa na hermes-prod, que apagaria as funções só dela
(_dono_kaggle etc.); restaurei às 14:48 (~8 min) e subi a versão certa (a dela + mudanças). As 4 centrais AINDA
divergem entre si (a prod não tem manter_teste; staging/bloqueio/casa não têm _dono_kaggle/_pausada/_motivo_do_log)
— unificar é outro trabalho.

## Como voltar
`cp vps_central.py.antes_fila_401_2611 vps_central.py` em cada central. Só o limite: `KAGGLE_QUEUED_MAX_H=6`.

## Testes
`teste_logica.py` (sem rede, conta falsa): 401 1x/2x/3x, aviso 1x só, cota boa zera, liberar zera, fila 1 h mantém,
fila 2 h solta sem descanso, conta fora 6 h e volta depois. 8/8 OK na versão da casa e na da prod.

## Não feito (depende da dona / do Kaggle)
- As 11 contas com 401: gerar token novo de cada uma **pela saída dela** (ou confirmar banimento no navegador do cofre
  pela saída da conta). Depois `vps_central.py liberar <conta>`.
- As 5 contas em fila: soltam sozinhas com a regra nova (1,5 h); o Kaggle decide quando dá a GPU.

## 26/11 ~22:50 — casa reaplicada + 2ª conta de teste
- A central da CASA foi trocada por outro chat às 15:01 (vaga de teste com várias contas) e VOLTOU à regra antiga
  (fila 6 h + descanso 12 h; sem 401 repetido). Reapliquei as mudanças por cima dessa versão nova (aplicar_mudancas.py,
  8/8 testes OK): casa = 419a10c5 (backup vps_central.py.antes_fila_401_v2_2611). VPS seguem com as mudanças:
  staging/bloqueio e3d0b3d5, prod 0ba7eeb5.
- **Quem mexer no vps_central de qualquer central: aplique em cima da versão que está LÁ (nunca copie de outra
  central — cada uma tem funções próprias) e rode `python aplicar_mudancas.py <entrada> <saida>` + teste_logica.py.**
- p76 `marinamartin14948` (telefone ok 26/11 21:15, IP 166.0.102.60 / rnprmtfo-76) = 2ª conta EXCLUSIVA de testes
  (papel "teste") no kaggle_pool da casa; anotada em saidas_usadas.json (p76). Já RODANDO com GPU na vaga de teste
  desde 21:27 (a carlabarbosa94254 está na fila do Kaggle). carlaramos27719 segue verificada=false (pediu selfie).

## 27/11 08:40 — contas de teste: fila de voz + porta do Webshare
- A conta de teste rodava com GPU mas o loop_teste do kaggle_trabalhador SÓ olhava a fila_teste (vídeo) e a produção:
  os 13 testes de voz (fila_teste_voz) nunca andavam. Agora loop_teste faz 1 lote_teste_voz() por volta, antes da
  fila_teste (TESTE_VOZ_NA_CONTA_TESTE=0 desliga). E a central conta fila_teste_voz como trabalho de "teste"
  (lança a conta de teste também sem longo). Publicado na casa (D:\recap_central_casa = junção p/
  D:\sistema\1-VIDEO\1-producao\longos\recap_central_casa) e no colab do PC1; backups .antes_voz_na_teste_2711.
- Fila reordenada: avalia88_* -> zz_avalia88_* (por último); cega_coleta_mike (v1 antiga) cancelada (erro.json).
- Proxy: p.webshare.io:80 dá "502 Bad Gateway"/timeout do PC1; a porta 45.39.15.202:6632 do mesmo plano funciona.
  As 2 contas de teste passaram para http://<USUARIO>:<SEGREDO_REMOVIDO>@45.39.15.202:6632 (backup kaggle_pool.json.antes_gateway_2711).
  A trava de IP usa o "-N" (não muda). Testado (ipv4.webshare.io): -76 sai 166.0.102.60 = IP do cadastro, OK.
  **ATENÇÃO: -28 (carlabarbosa94254) hoje sai por 185.72.240.55, NÃO pelo IP do cadastro 91.123.10.38** — o Webshare
  trocou o IP do proxy 28. Dona decide se segue usando essa conta.
