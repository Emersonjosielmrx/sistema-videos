# Advance Energia Solar (@advance_novoestrela, Castanhal-PA)

Conta pessoal do Luiz Carlos Souza, sem token da API: posta por HTTP com a sessão do cofre (`ig_solar_nova`,
`D:\projeto-navegador-sem-navegador\services\instagram\postar.py`). Mesmo pipeline da MS Energy com troca de marca
(roxo #5B21EA + laranja #F3661C, logo hexagonal em `assets\advance\logo_*.png`).

## O que roda
| Tarefa | Horário | Script | O que faz |
|---|---|---|---|
| AdvanceSolar_Reel | 09:40 / 14:10 / 19:20 | `bin\reel_advance.py` | posta o Reel pendente; sem pendente gera 1 (rodízio abaixo) |
| AdvanceSolar_Carrossel | 11:23 | `bin\carrossel_advance.py` | carrossel de 6 imagens + capa no Story |
| AdvanceSolar_Carrossel_Hora | desligada | — | era de hora em hora: 9 carrosséis 03h–11h em 30/10 = rajada |

Rodízio dos Reels (`reel_advance._proximo_tipo`): **material real da pasta do Drive** (`bin\obra_advance.py`) quando
houver e o último não foi dele → avatar do Luiz (Veo, `assets\advance\clone_bases`) ↔ foto real de obra animada (Veo).

## Material da empresa (pasta do Drive)
`empresas/advance_novoestrela/entrada` (link aberto de edição). **Armadilha (30/10):** o remote `manhwa-drive` é escopo
`drive.file` e não enxerga o que a empresa sobe pelo navegador (via 0 de 14 arquivos). `pastas_empresas._loc` agora lê,
baixa e move pelo `colab649` (escopo drive inteiro) entrando pelo `pasta_id` do `marcas_instagram.json` — vale para
todas as empresas.

`obra_advance.py`: classifica cada arquivo por visão (resultado guardado em
`postador\config\pastas_empresas_estado.json` → `classificados`):
- **cliente** (Luiz com cliente / arte "mais um cliente") → Reel de prova social, pauta `clientes`, legenda fixa (o LLM
  inventou "a maior parte dos projetos vem de indicação"); um mesmo cliente só 1x por Reel;
- **obra** → Reel com pauta normal;
- **selfie** (rosto do Luiz) → não posta; serve de foto-base do clone (as 2 HEIC de 30/10 viraram `luiz_base_7/8`);
- **oferta** → não posta sozinho: a promoção "Verão gelado" (central de ar 9.000 BTUs, "pagar em janeiro/2026") pode
  estar vencida — só com o OK da dona;
- **print / ruim / proibido** → recusado.
Montagem sem voz (Thalita pura é proibida aqui): foto/vídeo entre 11% e 60% da altura, legenda embaixo, fala de 10–22
palavras (~0,42 s por palavra), trilha livre, cartão da Advance, mesma trava final. Postado → original vai para
`usados/`. Drive fora → usa o que já foi baixado e aprovado.

30/10: 1º Reel de clientes pronto (`videos\reels_advance\advance_obra_20261030_145938.mp4`, 15,3 s; Rodrigo William,
Maria José, Açaí do Geléia + foto com cliente). Sai na 1ª rodada depois da pausa. Testes reprovados em
`videos\_revisar\advance_obra_*` (com MOTIVO.txt).
Sobrou na entrada: `6109aa53` (Luiz com o Rodrigo, foto sem arte) — vai num próximo Reel.

## Travas da conta
- **Intervalo**: nada posta a menos de 90 min do último post da conta (carrossel ou Reel) — `carrossel_advance.espaco_ok`.
- **Pausa**: resposta `feedback_required`/spam/checkpoint → posts PAUSADOS 18 h (`cache\advance_pausa.json`); geração
  continua. 30/10 14:15 a conta estava limitada até para ler o perfil → pausa até 31/10 08:19.
- Seguir recomendados: pausado até 01/11.
- **Material já postado não volta (31/10)**: o Drive recusa mover entrada→usados (403 `cannotAddParent`) e o Reel das
  14:12 repetiu as 4 fotos do das 08:09. `obra_advance.material()` agora tira da lista tudo o que já saiu (json do
  Reel com `postado` + `reuso` do estado), mesmo que o arquivo continue na entrada. O move no Drive segue quebrado.

## Facebook (pedido da dona 30/10: "as postagens vão para o Facebook também")
Pendente. O cofre não tem login de Facebook do Luiz (só o Instagram). O caminho é a opção "Compartilhar no Facebook" do
próprio Instagram, que só existe se o Instagram dele estiver ligado ao Facebook na Central de Contas. Os campos do
envio (`share_to_facebook`, `share_to_fb_destination_id`, `share_to_fb_destination_type`) aparecem vazios no Story
capturado; para Reel/carrossel ainda não há captura com a opção ligada (regra do projeto: nada de endpoint inventado).
Passos quando a pausa acabar: 1) ler `linked_fb_info` do perfil (`_diag\advance_fb_ligado.py`, só leitura);
2) se ligado, capturar 1 post feito pela tela com a chave ligada (`tools\capturar_acao.py`) e passar os campos no
`postar.py` (opção por conta); 3) se não ligado, o Luiz liga no app: Perfil → ☰ → Central de Contas → Compartilhamento
entre perfis → Facebook.
