# TikTok: todas as contas nos IPs grátis do Webshare (12/11/2026)

## O que a dona decidiu
> "usar os proxys grátis do Webshare nessas contas mortas; são 10 IPs de verdade"
> "tem que ver se não vai matar as contas que estão boas; a ideia seria todas com proxy, mas tem que ter uma análise
> se as novas postadas nos canais top ainda vão dar bem até o final do dia, e isso tem que estar altamente
> documentado e lembrete"

Ela escolheu **"todas dividindo IP"** sabendo que vai contra a regra "nunca 2 contas pelo mesmo IP".
**É exceção só do TikTok.** Kaggle, Google, YouTube e Instagram continuam 1 conta por IP.

## Como estava antes (11/11)
- 58 contas no TikTok, **só 9 postando** (as 9 de mais views, 1 por IP grátis).
- 49 pausadas: 34 por "todos os vídeos em 0 views" e 15 por "sem IP próprio".
- O código achava que eram 9 IPs.

## O que mudou (12/11 07:53)
| O quê | Antes | Agora |
|---|---|---|
| IPs grátis | 9 (`-1`..`-9`) | **10** (`-1`..`-10`) |
| Contas postando | 9 | **58** (todas) |
| Contas por IP | 1 | 3 a 7 |
| Espera entre contas do mesmo IP | — | **30 min** |
| Vigia das contas boas | — | **todo dia 09:00** |

- **O 10º IP existe.** Em 12/11 o `-10` respondeu 200 (IP 64.137.96.74) com um login que tinha banda. O "403 no -10"
  de 19/10 era de um login SEM banda. O `-11` responde 407 (não existe). Porta local do IP 10 = **18220** (a 18210 é
  do proxy do celular).
- **Ninguém trocou de IP.** Cada conta ficou no IP de sempre (trocar o IP de conta logada é sinal ruim pro TikTok).
  Só as 3 contas que não tinham IP foram para o IP 10.
- **As 5 contas que crescem de verdade ficaram cada uma num IP diferente**, então nenhuma boa divide IP com outra boa.

### Distribuição (12/11)
| IP | Boa (a que mais cresce no IP) | Cresceu em 6 dias | Normal (views/dia) | Outras contas no IP |
|---|---|---|---|---|
| 1 | filmenoturno | +1.582 | 527 | jornalcomia, entrevistacomia, en1653964, emersongenc, emersonjosiel0 |
| 2 | inovaremanhwabr | 0 | — | inovaremanhwaverseita, vendeafiliados3, jogoscomia, inovaremanhwaverseviet, 3dfabricadeautomacoesia |
| 3 | fabricadeautomacoesia | +1.841 | 368 | inovaremanhwaversehindi, inovaremanhwaverseind, inovaremultiatendimento, canalalucinaai, inovaremanhwaverseesp, murilodoctor192 |
| 4 | emersonjosiel649 | +967 | 484 | emersonjosiel1995, canalhistoriacomia, emersonjosiel2031, gameoftroneskingsroadbrasil, emersongencshin, inovaremanhwaverseing |
| 5 | fabricadeautomacoes0 | 0 | 0 | filmescomia1, emersonjosiel2026, solarmundo195, canalanimescomia |
| 6 | emersonjosiel2027 | +85 | 17 | aulasrevolution, inovaremanhwaverserussian, fabiovideoseducativos, revolutionemerson1, mentoriaiapro |
| 7 | doramanoturno | +2.396 | 479 | emersonjosiel2029, mundosolar1995, e4487017, inovaremanhwaversethai, revolutionemerson2, aulacomia |
| 8 | inovarecap | +1.682 | 336 | emersonjosiel2030, seebotsia, inovaremanhwaverse, revolutionemerson3, comoseriasecomia |
| 9 | emersonjosiel2033 | +1 | 0 | empressinovare, emersonjosielmrx1995, inovaremanhwaversefrench, rezaulkarimul355 |
| 10 | inovaremanhwaverse2 | 0 | 0 | curiosidadesnoturnas, emersonjosiel2032 |

**Achado:** fabricadeautomacoes0, empressinovare e inovaremanhwaversehindi estavam no "top" pelo total de views, mas
estão **paradas desde 06/11** (mesmos 24 vídeos, mesmas views). A "boa" agora é escolhida pelo **crescimento**.

## O vigia (proteção das boas)
`bin\vigia_tiktok_ip.py`, tarefa **VigiaTikTokIP** (todo dia 09:00, depois da medição TikTok_MedirViews das 07:23).
- Ganho de cada conta boa = views ganhas de ontem para hoje, **vídeo a vídeo** (o total do perfil não serve: a grade
  carrega um número diferente de vídeos a cada dia — 37 num dia, 24 no outro).
- Normal = média desse ganho nos 5 dias antes de 12/11 (gravado em `logs\vigia_tiktok_ip.json`, chave `base`).
- Ganho abaixo de **50% do normal por 2 dias seguidos** = queda:
  1. aviso no Telegram (bot de métricas);
  2. **pausa as outras contas do mesmo IP** (a boa continua).
- Dia em que a medição falhou (perfil não abriu) não conta. Ex.: 12/11 a medição fechou o navegador e nenhum perfil abriu.
- Contas com normal abaixo de 30 views/dia não são julgadas (ruído). **Na prática o vigia protege 5 contas:**
  filmenoturno, doramanoturno, emersonjosiel649, fabricadeautomacoesia, inovarecap.

### Por que não "até o fim do dia"
A medição do TikTok é **1 vez por dia**, por um único navegador logado que abre o perfil de todas as contas. Medir de
hora em hora faria esse navegador varrer as 58 contas várias vezes por dia pela mesma internet — o laço sobre contas
que a regra proíbe. Então o vigia julga **dia a dia**, e a pausa só vem com 2 dias seguidos de queda (1 dia ruim pode
ser só um vídeo fraco).

## Arquivos mexidos
- `bin\proxy_tiktok.py` — `IPS = range(1, 11)`; porta do IP 10 = 18220.
- `bin\postar_tiktok_auto.py` — `minutos_desde_ultimo_ip` + espera de 30 min entre contas do mesmo IP
  (`"intervalo_ip_min"` na config tiktok; 0 desliga).
- `bin\tiktok_pausar_zeradas.py` — modo `--compartilhar` (este plano); 10 IPs.
- `bin\vigia_tiktok_ip.py` — o vigia (novo).
- `config\proxy_tiktok.json` — chave `_boas` (as 10 boas e o IP de cada uma).
- `config\reuso_plataformas.json` — tirada a `"pausada"` das 49 contas.

## Desfazer
- Tudo: copiar de volta `config\reuso_plataformas.json.bkp_20261112_0753` e `config\proxy_tiktok.json.bkp_20261112_0753`.
- Só o vigia: `VIGIA_TIKTOK_IP=0` ou desligar a tarefa VigiaTikTokIP.
- Voltar a 1 conta por IP: `python bin\tiktok_pausar_zeradas.py --fazer` (pausa as zeradas e as sem IP próprio).

## Lembretes
- **19/11 (1 semana):** comparar as 5 boas (views/dia) com a linha de base. Caiu? Voltar a 1 por IP.
- **19/11:** alguma conta morta voltou a ter view? (`TIKTOK_VISUALIZACOES.md`, coluna "ganho").
- O vigia avisa sozinho no Telegram se uma boa cair 2 dias seguidos.
