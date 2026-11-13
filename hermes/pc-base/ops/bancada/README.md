# Bancada (cópia de teste do Hermes na VPS de produção)

> **07/10/2026: a bancada passou a rodar na VPS de teste (209, `ssh hermes-staging`)**, com banco próprio
> (contêiner `hermes-bancada-pg`, `127.0.0.1:5440`). Na produção ela está desabilitada. O que está descrito abaixo
> é a instalação da produção, guardada como volta; o estado atual está no topo do `CONTINUAR_DAQUI.md`.

Cópia, em 05/10/2026, do que roda na VPS (`ssh hermes-prod`). Antes estes arquivos só existiam lá: se a VPS
se perdesse, a bancada teria que ser refeita de memória. Não têm senha, chave nem telefone: os segredos ficam
em `/etc/hermes-bancada/bancada.env` e os números em `/etc/hermes-call/ensaio.env`, só na VPS.

| Arquivo | Onde fica na VPS | Para que serve |
|---|---|---|
| `hermes-bancada.service` | `/etc/systemd/system/` | serviço da bancada (porta 127.0.0.1:8091, linha 8288) |
| `iniciar.sh` | `/opt/hermes-bancada/` | sobe a bancada com o ambiente da produção + o `bancada.env` por cima |
| `lab-bancada.sh` | `/root/` | `preparar <versão>`: instala uma versão na bancada e copia agentes e chaves de voz da produção, de banco para banco |
| `bateria-texto.sh` | `/root/` | bateria de perguntas por texto para comparar agentes e modelos |
| `ligacao-teste.sh` | `/root/` | a bancada liga para a produção e resume o registro das duas pontas |
| `../vps/ensaio.sh` | `/opt/hermes-call/ops/` | ensaio IA × IA completo (**faz o celular 8653 tocar: avise a dona antes**) |
| `../vps/bancada-aceite.sh` | `/root/bancada-aceite.sh` | liga e desliga o atendimento automático de teste (`ligar <variante>`, `desligar`, `estado`) |

Cuidados (detalhes em `docs/REGRESSOES_LIGACAO.md` §6 e `docs/CONTEXTO_PARA_NOVO_AGENTE.md` §4):
- a bancada **copia o ambiente da produção** ao subir. Chave que não pode valer na bancada (ex.: cobrança do
  Asaas) tem que estar **vazia** no `bancada.env`; o `configurar-asaas.sh` já faz isso;
- bancada com atendimento automático ligado entra nas ligações para o 8288. Desligue ao terminar;
- mudou um destes arquivos na VPS? Copie de novo para cá (e o contrário).
