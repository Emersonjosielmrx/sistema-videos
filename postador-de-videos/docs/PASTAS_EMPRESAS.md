# Pastas das empresas no Drive + cor de cada Instagram (24/10)

Pedido do dono (24/10): "padronização de cores por Instagram nas postagens (carrossel, imagem, vídeos), cada um com
sua cor; cada um com sua pasta de conteúdos no Drive, pública, para as empresas colocarem conteúdo; o sistema normaliza
e posta fotos e vídeos dela, move para uma subpasta 'usados' e reaproveita se não tiver nada novo, balanceando com o
Veo; contas sem conteúdo específico viram conta de produto (Hermes Call, agenda inteligente, cardápio...)".

Decisões do dono (24/10):
- Produto por conta: inovarecom.ia = Hermes Call · futebolcom.ia2 = Cardápio digital (restaurante/lanches) ·
  sintetizerisada = Agenda IA. (SuperChat / Agente Pessoal ficam pra fabricadeautomacoesia e
  emerson.inteligenciaartificial quando elas postarem.) As de tema seguem no tema, só ganham cor própria.
- Pasta: link aberto para EDITAR (qualquer pessoa com o link). Tudo que entra passa por checagem antes de postar.
- Contas que postam hoje: videocassetadascom.ia, _lucrocomia_, iapro.mentoria, inovarecom.ia (token);
  recenas.ia, fakenews.ia4, futebolcom.ia2, sintetizerisada, msenergysolar.pa, jornalcomia, canalhistoriacomia (navegador).

## Fotos do CLONE (25/10) — `empresas/<conta>/fotos_base`
Dono 25/10: "tem que ter uma subpasta do Drive só para as fotos dos clones dentro da pasta do material do produto;
hoje seria a minha para todos, mas vão entrar mais 2 clientes que, na pasta pública deles, vão colocar as fotos de rosto
para o clone".
- Toda conta tem `entrada/`, `usados/` e **`fotos_base/`** (o `criar` faz nas novas; mesmo link de edição da pasta).
- `pastas_empresas.clone_bases(conta)`: >= 3 fotos em fotos_base = o clone é ESSA pessoa; conta da casa (produto/tema)
  vazia = o clone é o DONO (fotos-base locais do dono — nunca copiadas pro Drive, que tem link aberto); conta marcada
  `"cliente": true` no marcas_instagram.json e vazia = sem clone (o rosto do dono nunca vai pra cliente).
- Quem usa: `D:\ms-energy\bin\roteiro_ms._clone` (apresentador do MS Energy) e o revisor de rosto do
  `D:\veo\beta\foto_na_hora.py` (limiar 0,57, mesmo do Veo normal): a foto do 1º quadro é criada no cenário e só vira
  vídeo se o rosto bater com as fotos da pasta; o vídeo pronto é conferido de novo.
- Cliente novo: linha no marcas_instagram.json com `"cliente": true` + `python pastas_empresas.py criar` + mandar o link
  pra ele com o aviso "fotos do rosto de quem vai aparecer (com autorização), de frente e de lado, boa luz, na pasta
  fotos_base". Baixar/conferir: `python pastas_empresas.py fotos_base <conta>`.

## Como funciona
- Marca de cada conta: `config\marcas_instagram.json` (produto, cor principal, cor de apoio, cor do texto, pasta, link).
- Drive: `manhwa-drive:empresas/<conta>/entrada` (empresa coloca) e `.../usados` (o sistema move depois de postar).
- `bin\pastas_empresas.py`: criar pastas + liberar link; baixar o novo; normalizar (vídeo 9:16 com fundo na cor da
  marca, até 90 s; fotos viram Reel curto com moldura/faixa na cor da marca); checar por visão; entregar ao postador.
- `postar_insta_auto.py`: a pasta da empresa entra ANTES do Veo de reserva, no máximo metade das vagas do dia
  (o resto: vídeo da conta / Veo). Pasta vazia = reaproveita 1 dos usados por dia.

## Frentes
1. [x] marcas_instagram.json com cores e produtos (links gravados lá)
2. [x] pastas no Drive + link de edição: 11 pastas, abrem sem login. Google limita ~5 compartilhamentos/min (403
   "Queries per minute"): o `criar` espera e tenta de novo.
3. [x] pastas_empresas.py — teste 24/10 no msenergysolar.pa: 4 fotos → Reel de 14 s; drone deitado → 1080x1920 com
   fundo desfocado, moldura e faixa na cor da marca. Recusado fica em config\pastas_empresas_estado.json.
4. [x] postar_insta_auto.py: `--simular` mostrou as 2 montagens da pasta na frente da fila do msenergysolar.pa.
5. [x] carrossel com a cor de cada conta: `bin\carrossel_marca.py` (token = carrossel de verdade; navegador = Reel de
   slides). Teste 24/10 23:01 publicado na futebolcom.ia2. Tarefa `Marcas_Carrossel` todo dia 07:13 (`--todas`, ~30 min
   por conta: o Flow leva 2–7 min por imagem).
6. [x] produto Cardápio digital (peso 0, sem url/preço até o dono passar) + comercial_veo: conta de produto anuncia só
   o seu, 1 a cada 2 Veo.
7. [ ] primeira postagem real vinda da pasta (próxima rodada do Instagram)

## Material real do Google Fotos (MS Energy) — situação 25/10 04:10
Busca nas contas do cofre terminou (24/10 23:42): **3.960 itens novos** (3.768 fotos + 192 vídeos); índice total 4.683
(antes 832). Contas vazias ficam em `D:\logins-google\fotos_contas_vazias.json` e não são mais buscadas.

| Conta | Novos | Vídeos | Fotos checadas | Aprovadas p/ vídeo/carrossel |
|---|---|---|---|---|
| contapessoal | 342 | 16 | 326 | 78 |
| emersonjosiel649 | 363 | 11 | 352 | 74 |
| emersonjosiel1995 | 377 | 1 | 376 | 43 |
| en1653964 | 423 | 5 | 100 (em andamento) | 41 |
| emersongencshin | 339 | 2 | 337 | 26 |
| emersongenc | 279 | 19 | 260 | 12 |
| fabiovideoseducativos, vendeafiliados3, mundosolar1995, fabricadeautomacoes0, fabricadeautomacoesia, emersonjosielmrx1995, solarmundo195 | 1.837 | 138 | na fila | — |

Às 04:10: checagem por visão em 2.375/4.600 (termina ~5h); cópia pro Drive `manhwa-drive:ms-energy/material_real`
em 2.991 arquivos / 1,0 GB de 4,3 GB (lenta: divide a internet com o backup de vídeos; vídeos grandes no fim).
Antes havia 82 fotos do Google aprovadas; já são 274 aprovadas a mais com metade checada.

**Final da checagem (25/10 ~05:40):** 4.600 fotos checadas, 863 "boas para vídeo"; passando também no filtro do
roteiro_ms (sem rosto, sem texto, mostra energia solar) = **309 fotos do Google aprovadas** (antes 82; total MS Energy 325).
Por conta: fabricadeautomacoesia 78 · en1653964 53 · mundosolar1995 53 · contapessoal 43 · emersonjosiel649 38 ·
emersonjosielmrx1995 12 · fabiovideoseducativos 11 · emersongenc 9 · emersonjosiel1995 7 · emersongencshin 3 · solarmundo195 2.
Drive: 3.763 de 4.684 arquivos (1,4 de 4,3 GB) às 05:40 — a cópia continua sozinha.
