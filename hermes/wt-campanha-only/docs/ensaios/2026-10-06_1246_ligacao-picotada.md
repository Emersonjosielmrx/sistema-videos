# 06/10 12:46 — ligação da produção (linha 8653) para o 8288: a dona achou a gravação picotada

A dona pediu a ligação pelo Telegram, atendeu no celular do 8288 e conversou 69 s com a "Vendas Hermes Call"
(produção, v0.8.1, build `20261005-1148_f28526a`). Depois: **"a gravação está picotando tanto a minha voz como a da
IA"**. A bancada (mesma linha 8288) só viu a ligação tocar; o atendimento automático dela estava desligado.

## O que o registro diz
| | 05/10 11:38 (bancada, ela achou boa) | 06/10 12:46 (produção, picotada) |
|---|---|---|
| pacotes recebidos / perdidos | 966 / 3 (0,3%) | 446 / 2 (0,4%) |
| jitter do recebido | 42,8 ms | **144,1 ms** |
| buracos no recebido | 112 | 128 (maior 833 ms) |
| buracos no nosso envio | 8 (maior 281 ms) | **14 (maior 382 ms)** |
| resposta da IA | 1,7–3,3 s | 2,1–3,0 s |

Rede boa (perda de 0,4%). O que piorou foi o **tempo**: os pacotes saíram e chegaram fora de hora.

## O que a gravação mostra (medido no MP3)
Trechos de zero digital depois do atendimento. Na de 06/10 o som de fundo estava ligado: ali zero só existe se
faltou áudio. Nas outras, parte do silêncio pode ser pausa de verdade (olhe os buracos por segundo):

| Gravação | Buracos | Por segundo | Tempo em silêncio | Maior |
|---|---|---|---|---|
| 06/10 12:46 produção → 8288 | 132 | 1,9 | 5,9 s de 69 s (8,5%) | 325 ms |
| 05/10 11:38 bancada → dona (a "boa") | 197 | 2,0 | 13,1 s de 100 s | 1.670 ms |
| 05/10 11:11 ensaio IA × IA (bancada) | 284 | 3,2 | 27,9 s de 89 s | 1.020 ms |
| 04/10 09:21 produção | 83 | 1,3 | 3,1 s de 62 s | 160 ms |

Na onda do som são **cortes secos no meio da fala** (não é pausa natural). A isca gravada levou 7,3 s para tocar
(pelo tamanho do arquivo ela tem perto de 6 s; não foi medida): só nela há sete buracos de 85 a 120 ms, fora os
menores. **O defeito é antigo**: aparece em todas as gravações, inclusive na que a dona aprovou.

## Causa 1 — a VPS da produção engasga (não é o código)
Um processo que só dorme 20 ms e mede quanto atrasou para acordar, 20 s em cada VPS (06/10 ~17:30):

| VPS | atraso p99 | maior | acordou mais de 5 ms atrasado |
|---|---|---|---|
| **produção (62.171.128.241)** | **109 ms** | **175 ms** | **180 vezes** |
| teste (209.145.60.53) | 2,3 ms | 25 ms | 3 vezes |
| 157.173.207.22 | 8,1 ms | 41 ms | 18 vezes |

Na produção acontece igual com **prioridade máxima de tempo real** e em qualquer das 4 CPUs, com a máquina 96%
ociosa, sem swap em uso, disco parado, sem limite de CPU no serviço (`cpu.max: max`, 0 vezes freado) e sem
`steal` informado. Com a CPU mantida ocupada melhora (p99 30 ms) mas não some. Ou seja: quem pausa é o
**hospedeiro da VPS** (máquina física dividida com vizinhos). Nada dentro da VPS resolve; é com o provedor ou
mudando o Hermes de máquina. A bancada ainda soma um engasgo próprio: tem limite de 150% de CPU e foi freada 65
vezes desde 05/10 21:23.

## Causa 2 — o Hermes não tolerava o engasgo (código; corrigido neste ramo, ainda não publicado)
1. **Envio da fala seguia um `time.Ticker`**, que descarta os ticks perdidos. Depois de cada engasgo a fala inteira
   passava a sair atrasada: para o celular, cada engasgo era um buraco, por maior que fosse o buffer dele.
   Agora o ritmo é por prazo (`pacer` em `internal/voice/voiceagent.go`): os frames atrasados saem em seguida e o
   ritmo é retomado, até 300 ms de atraso. Vale para a fala, a isca/oferta e o som de fundo.
2. **O silêncio de manutenção entrava com 120 ms sem áudio** (`internal/voip/call/callmanager_media.go`): num
   engasgo de 150 ms um frame de silêncio ia parar entre duas sílabas. Agora só com 300 ms.
3. **A gravação punha cada frame na hora em que chegou** (`cmd/server/recorder.go`): o atrasado deixava um buraco e
   os que vinham juntos depois eram somados um por cima do outro. Por isso a gravação soava pior que a ligação.
   Agora cada lado é montado em sequência (`recLane`); pausa de verdade (acima de 300 ms) continua na hora em que
   aconteceu. O que foi arrumado sai no registro: `gravação: frames fora do ritmo recolocados em sequência`.

Testes (cada um falha com o defeito antigo de volta): `TestPlay_RecuperaAtrasoDoServidor` (fala de 1,14 s levava
1,57 s), `TestPacer_AtrasoGrandeRecomecaDeAgora`, `TestGravacao_AtrasoERajadaNaoViramBuracoNemSobreposicao`,
`TestGravacao_PausaDeVerdadeEOutroLadoFicamNaHoraDeChegada`, `TestKeepalive_EngasgoNoMeioDaFalaNaoViraSilencio`.

## O que NÃO foi provado
- Que no celular a fala soa melhor com a correção: só uma ligação de verdade diz. A conta é que o buffer do
  celular absorve atraso recuperado, mas isso não foi ouvido ainda.
- Por que o hospedeiro engasga, nem se é o dia todo. Foram medidas de 20 a 45 s, em 06/10 entre 17:10 e 17:40.
- As outras duas ligações de hoje (12:48 e 14:32) não foram atendidas; não há áudio delas.

## Como medir de novo
- Engasgo da máquina: o programa de 10 linhas acima (dorme 20 ms, mede o atraso), com e sem `chrt -f 50`.
- Buracos numa gravação: decodificar em 16 kHz mono e contar trechos abaixo de −75 dB em janelas de 5 ms.
- No registro da ligação: `tx_buracos`, `tx_maior_buraco_ms`, `rx_jitter_ms` e a linha nova da gravação.

## Sobre o que o outro agente fez (sessão do VS Code, 12:50–13:20)
Baixou a gravação, acrescentou dois avisos de registro em `D:\hermes-call` (o `main`, sem commit) e declarou
"concluído". Nada foi publicado nem corrigido. As alterações estão guardadas em
`D:\hermes-call-backups\alteracoes-soltas-no-main_agente-vscode_2026-10-06_tarde_gravacao.patch` e o `main` voltou
a ser igual ao que está no ar. A hipótese dele ("sobrecarga do servidor") apontava para o lado certo, mas o serviço
não está sobrecarregado: é a máquina que é pausada por fora.
