# Andamento — Painel de Clientes

NADA de Agent/Workflow no Opus (429 sempre — ver memória project_trocador_subagentes).

1. [feito 24/10 21:30] Levantamento das fontes → `CONTEXTO.md`.
2. [cancelado] Workflow de desenho caiu todo em 429 → desenho feito direto.
3. [feito 24/10 23:30] servidor (`app.py`), coletor da VPS, Docker, página, coletor do Instagram, config, publicar.
4. [feito 24/10 23:35] Testes da API (permissões, campanha, CSV, link rastreado, clique, robô, pessoa) e publicação em
   https://clientes.opus-sem-limites.com.br; precioso/landings/hermescall seguem 200 depois do reload do nginx.
5. [feito] Prints desktop/celular local e de produção, sem erro de JS nem rolagem lateral (`teste\prints`).
6. [feito] `ESPECIFICACAO.md`, `PENDENCIAS.md`.
7. [feito 30/10 manhã, outra sessão] Advance Energia Solar + login com usuário/senha + coletor HTTP (conta pessoal).
8. [feito 30/10 tarde] Revisão geral (testado contra cópia do banco de produção, `teste\dados_prod`):
   - Bugs: o coletor da API mandava "sem acesso" da Advance a cada 30 min por cima do coletor HTTP; a tarefa
     `PainelClientes_ColetarHTTP` nunca tinha sido criada (Advance nunca coletou); chave com acento dava erro 500;
     link com acento no destino dava erro 500; CSV com a mesma campanha em várias linhas criava duplicadas; um arquivo
     de fonte com erro travava os outros; seguidores somavam só as contas do último dia e ignoravam o período;
     cartões do Instagram mostravam 0 quando não havia número; plurais ("1 pessoas").
   - Novo: juntar/separar pessoas; quem entra no painel não conta como visita/clique (`casa.json`); limite de 20
     tentativas erradas por IP; backup diário do banco (14 dias); gzip; auto-atualização a cada 5 min; aviso
     "esperando resposta no Direct"; renovação diária dos tokens que ainda funcionam; tarefas com prioridade 6 e
     limite de tempo (antes 7 / 72 h).
