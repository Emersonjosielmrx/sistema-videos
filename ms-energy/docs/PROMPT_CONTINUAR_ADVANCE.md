# Prompt para o próximo agente — campanha da Advance (30/10/2026)

## PROMPT

Você vai continuar a campanha de Instagram da **Advance Energia Solar** (@advance_novoestrela, Castanhal-PA). É uma
empresa real; a conta é o perfil pessoal do Luiz Carlos Souza. O projeto mora em `D:\ms-energy` e reaproveita o
pipeline da MS Energy com troca de marca. Responda sempre em português do Brasil.

**Leia antes de mexer:** `D:\ms-energy\CLAUDE.md`, `D:\ms-energy\docs\ADVANCE.md` (estado atual, travas, pendências)
e `D:\postador-de-videos\docs\PASTAS_EMPRESAS.md`.

**Onde ficou (30/10 15:10):**
- O Instagram limitou a conta ("feedback_required, spam") depois de 9 carrosséis de hora em hora (03h–11h) + Reels.
  Os posts estão PAUSADOS até 31/10 08:19 (`D:\ms-energy\cache\advance_pausa.json`); a geração continua.
- Reel de clientes reais pronto e primeiro da fila: `D:\ms-energy\videos\reels_advance\advance_obra_20261030_145938.mp4`
  (Rodrigo William, Maria José, Açaí do Geléia + foto do Luiz com cliente). Sai na tarefa `AdvanceSolar_Reel` 09:40.
- Formato novo `D:\ms-energy\bin\obra_advance.py`: Reel com o material que o Luiz põe na pasta do Drive
  (`empresas/advance_novoestrela/entrada`), classificado por visão (cliente/obra usam; selfie/oferta/print/ruim fora).
  Entra no rodízio do `reel_advance.py` sempre que houver material novo.
- Corrigido: o remote `manhwa-drive` (escopo drive.file) não enxergava o que a empresa sobe; `pastas_empresas._loc`
  lê pelo `colab649` com o `pasta_id`. Travas novas: 90 min entre posts e pausa automática de 18 h no "spam".

**Tarefas, em ordem:**
1. **Depois de 31/10 08:19**, conferir se o Reel das 09:40 saiu (`D:\ms-energy\logs\reel_advance.log`) e se o original
   foi para `usados/` no Drive. Se o Instagram limitar de novo, a pausa liga sozinha: não insista e reduza o ritmo
   (por exemplo, 2 Reels/dia em vez de 3).
2. **Facebook** (pedido da dona: "as postagens vão para o Facebook também; ele tem essa opção de postar nas duas
   redes"):
   a) ler se o Instagram da Advance está ligado a um Facebook: `D:\ms-energy\_diag\advance_fb_ligado.py` (só GET);
   b) se estiver ligado, capturar UM post real feito pela tela com a chave "Compartilhar no Facebook" ligada
      (`D:\projeto-navegador-sem-navegador\tools\capturar_acao.py`, perfil do cofre `ig_solar_nova`), achar os campos
      exatos (no Story capturado eles vêm vazios: `share_to_facebook`, `share_to_fb_destination_id`,
      `share_to_fb_destination_type`) e só então ligar a opção por conta no `services\instagram\postar.py` (Reel,
      carrossel e Story), conferindo no Facebook que o post apareceu;
   c) se não estiver ligado, diga à dona o caminho no app (Perfil → ☰ → Central de Contas → Compartilhamento entre
      perfis → Facebook) e pare essa frente.
3. Quando entrar material novo na pasta do Drive, rodar `obra_advance.py --so-gerar` e **conferir os quadros a olho**
   (folha com `ffmpeg ... tile=6x2`) antes de deixar postar. Na entrada ainda sobrou `6109aa53` (Luiz com o Rodrigo).
4. Perguntar à dona se a promoção "Verão gelado" (central de ar 9.000 BTUs, "pagar em janeiro/2026") ainda vale;
   hoje ela está recusada no `D:\postador-de-videos\config\pastas_empresas_estado.json`.
5. Ao terminar, atualizar `docs\ADVANCE.md` com o que mudou.

**Ambiente:** Python `D:\veo\venv\Scripts\python.exe`, sempre `PYTHONUTF8=1`; ffmpeg em `D:\hipercool-materiais\bin`;
rclone em `D:\tools\rclone.exe`. O PC roda ~15 sessões do Claude ao mesmo tempo: comandos demoram, a RAM livre
fica perto de 2 GB e o Drive vive no limite de requisições (listar pode levar minutos). Outros agentes mexem nos
mesmos arquivos (`reel_advance.py` mudou durante o meu trabalho): releia antes de editar.

## RESTRIÇÕES (o que eu NÃO faço — vale para você também)

```
- Não postar com a conta pausada/limitada e não "testar" postando: cada tentativa piora o bloqueio do Instagram.
- Não religar a tarefa AdvanceSolar_Carrossel_Hora (de hora em hora) nem postar em rajada (mínimo 90 min entre posts).
- Não inventar endpoint nem campo de requisição do Instagram/Facebook: só o que foi capturado da tela real.
- Não apagar nada do Drive da empresa (só mover entrada -> usados depois de postado) nem posts do perfil.
- Não postar oferta/promoção (preço, brinde, data) sem a dona confirmar que ainda vale.
- Não postar print de outra conta, notícia de terceiro, foto tremida nem selfie como post.
- Não pôr outro rosto no lugar do Luiz: clone que não passa no revisor de rosto não posta.
- Não prometer "zerar" conta, R$ 0, números/porcentagens/prazos, "garantir/garante" resultado, nem citar
  concessionária; não deixar a IA inventar fato sobre a empresa (ex.: "a maior parte dos projetos vem de indicação").
- Não citar MS Energy/Paragominas nos posts da Advance (e vice-versa).
- Não dar Reel por pronto sem olhar os quadros reais; a trava automática sozinha deixou passar cliente repetido.
- Não matar processos de outras sessões (claude, pythonw, ffmpeg recentes, Chromes do cofre) para liberar RAM.
- Não baixar nem gravar nada no disco C (só no D) e não mexer nas configurações do sistema.
- Não usar o remote manhwa-drive para ler a pasta das empresas (ele não vê o que o cliente sobe): use o colab649.
```
