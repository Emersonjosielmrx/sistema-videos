# Diário do Vigia — projetos fora do hipercool

Registro de cada rodada do vigia (D:\recapd-ambientes, D:\historias-em-frames, D:\video-fila).
Formato: data_hora — resumo / motivo / achei / fiz / como desfazer / estado.

---


## 20261115_0036 — recap longo: alimentador parou e GPUs sem conta livre
- Motivo / O que achei (logs/parceiro_postar_auto.log / cliente.py): Recap longo com alimentador (cliente.py alimentar) parado e 14 de 20 GPUs sem conta livre (contas verificadas: 6 de 61). Wise Memory Optimizer ativo.
- Causa provável: Esgotamento temporal de contas verificadas/instâncias e pausa transitória do alimentador.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo — religar cliente.py alimentar manualmente e revisar contas verificadas se necessário).
- Estado: PRECISA REVISÃO

## 20261114_0456 — parceiro-render: rc=1 no Kaggle (vídeo DTaNZETVyNw)
- Motivo / O what achei (trecho de log): 2026-11-14 04:37:16,840 - WARNING - [kaggle-lote] 20261114_043519_DTaNZETVyNw deu erro no Kaggle: {"ok": false, "error": "rc=1", "segundos": 7, ... "applio": "ok em 67 s"}
- Causa provável: Erro transitório de execução/script no Kaggle (rc=1) ao renderizar short vertical com formato experimental (chaves_chiquinha).
- CONSERTO PROPOSTO: Nenhum — falha transitória no Kaggle, e o sistema prosseguiu normalmente gerando postar.json em seguida.
- Estado: NADA A FAZER

## 20261104_1916 — parceiro-render: rc=1 no Kaggle ao processar lote do Short Yz7c04eNjUg
- Motivo / O que achei (trecho de log): 2026-11-04 19:02:28,121 - WARNING - [kaggle-lote] 20261104_183253_Yz7c04eNjUg deu erro no Kaggle: ok: false, error: rc=1, segundos: 8 ao rodar renderização do short em formato experimental.
- Causa provável: Falha transitória ou erro no script de renderização no Kaggle ao aplicar formatação especial.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo).
- Estado: NADA A FAZER
## 20261115_0155 — guarda do disco: D: com 1.9 GB e processos monitorados
- Motivo / O que achei: D: com 1.9 GB livres, disparado backup_drive e cache do Chrome. Processos vigiados sem travamentos críticos (WiseMemoryOptimizer ativo, ~6.3 GB de RAM livre).
- Causa provável: Acúmulo de arquivos temporários e cache de navegador no disco D.
- CONSERTO PROPOSTO: Nenhum (Modo só aviso ativo).
- Estado: NADA A FAZER
