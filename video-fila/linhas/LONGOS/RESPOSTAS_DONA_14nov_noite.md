# Respostas à dona — 14/11, noite

## 1. Por que o Kaggle baniu (o cruzamento)
**Causa achada:** o envio de Shorts **por HTTP** (sem Chrome) saía pela **internet de casa**. Só o caminho pelo Chrome usava
o IP fixo da conta (`_proxy_da_conta_kaggle`). As contas Google desses canais são as mesmas do Kaggle:

| Canal | Conta Google | Kaggle | Envios por HTTP de casa (12–14/11) | Situação |
|---|---|---|---:|---|
| Comédia Noturna | emersonjosiel02 | emerso | 10 | token recusado 14/11 ~21h40 |
| Empresário Inteligente IA | inovaremanhwaverse8 | inovaremanhwaverse8 | 11 | token recusado |
| Imóvel em Foco | inovaremanhwaverse7 | emersonverse7 | 9 | token recusado |
| Vendas que Escalam | emersonjosiel2034 | emersonjosiel2034 | 9 | token recusado |
| (sem canal) | emersonjosiel2038 | emersonjosiel2038 | — | token recusado |

A mesma conta Google aparecia em 2 IPs (casa no YouTube + IP fixo no Kaggle) = regra do 2º banimento (09/11).
A aulasrevolution (sem canal postando por HTTP) continua viva no mesmo Webshare.

Também houve login em lote dessas contas no STI e no desktop em 12/11 de manhã, antes da trava do login em lote.

**Travado (14/11 23h):** `postador bin/youtube_web_poster._subir_http` não sobe mais por HTTP conta VIVA do Kaggle
(`_conta_no_kaggle`) — vai pelo Chrome, que sai pelo IP fixo dela.

**Ainda vivas, mas também subiram por HTTP de casa (em risco):** Filme Noturno (6), Curiosidades Noturnas (15),
Manhwa Noturno (6), Inovare q8l (8), Inovare u8b (20), Lei e Lucro (6), Clínica Lucrativa IA (11).

## 2. Longos que mais rendem por horas assistidas
O relatório agora ordena por **horas assistidas** (views × duração média). Campeão: o jardineiro (113 h, 70 min de
média por pessoa). O "ex bilionário" tem mais views (577) mas média de 3 min = 30 h.

## 3. Por que tanta máquina livre com tanto vídeo pra fazer
- Shorts: 753 prontos + 309 feitos hoje. O limite é a vaga de postagem do YouTube por canal, não a produção.
- Longos: só GPU do Kaggle (7 contas) — e 5 delas acabaram de cair.
- O STI ficava parado esperando o Chrome do Flow fechar (calor); o Flow/Veo agora vai pro HP, X200MA e Acer primeiro.
- O HP não roda Short completo (processador de 2010 sem SSE4.2/AVX).

## 4. Vídeo sem capa
Era o JesjRW5uBR0 (HistoriasEmFrames). Capa aplicada às 18:10. Causa: Studio lento nos notebooks; agora tenta pelo
desktop na hora e não desiste. Q2kaVKOk7q0 (Animescomia) também ficou sem: voltou pra fila com 12 tentativas.

## 5. Medieval Age
Postadas: 1 (SNhb31ZuuFA -> https://youtu.be/ozKHuLUFUU0, sem número no nome), 3 a 17. **A parte 2 nunca foi feita:**
nenhuma fonte "(2) He got into the Medieval Age" entrou na lista — é um buraco na saga (quem vê a 1 pula pra 3). Partes depois da 17:
não há na lista de prioridade nem no log do canal-fonte (@Manhwa_Fresh) — pra saber se o canal já tem a 18+, é preciso
olhar a playlist dele (próximo passo, pela vez do yt-dlp).

## 6. Amostras de foto e banner
Pasta: `D:\hipercool-materiais\AMOSTRAS_CANAIS_14nov`. Versão 2 (`v2_*`) com a mascote ATUAL (morena brasileira,
biquíni dourado) e poses mais sensuais.

## 15/11 manhã — dona: "baner aprovados pode colocar, kangles considere banidos so lembre de eu verificar depois, os temas vc escolhe"
- Foto + banner v2 aplicados (Studio, Chrome do cofre de cada canal, 1 por vez): Animescomia, Fio da Meada (n7j), Plantão das Histórias. Prints em postador logs\yt_web\*branding_publicado*. Código: youtube_studio_extras.py --foto/--banner (foto e banner em IDAS SEPARADAS: juntos o recorte do banner trava).
- Kaggle: as 12 contas com 401 tratadas como BANIDAS. Lembrete pra dona: conferir no Gmail de uma delas (pela saída dela).
- Temas (config/parceiro.json, backup .bkp_1511_temas), escolhidos pelo placar_nicho_canal (vitórias/testes em 48 h):
  | Canal | Antes | Agora | Por quê |
  |---|---|---|---|
  | Assist-IA Investimentos | financas (29%) | filme_sem_voz | 64% em 21 testes |
  | Tech Noturno | tecnologia | dorama | 3/3; dorama = melhor nicho geral (67%) |
  | Mistérios Noturnos | misterios (3 fontes só) | fatos | 47% em 46 testes |
  | Bicho Noturno | animais | animais (+fatos/pesca no foco) | bate com o nome; fatos 47% |
  O funil (parceiro_diario._nicho_do_canal) continua testando 20% outros nichos.
