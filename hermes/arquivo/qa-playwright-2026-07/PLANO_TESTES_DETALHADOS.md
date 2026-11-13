# Plano de testes detalhados — Hermes Call (rodada 3+)

Ambiente: QA isolado (`hermes-call-qa` :8092, banco `wacalls_qa_main` via namespace, túnel SSH). **Produção intocável.**
Princípio: dirigir pela UI/API real, tratar 4xx/5xx/erro como bug até provar o contrário, confirmar causa raiz antes de reportar (evitar falso positivo tipo TagsAndBlocks órfão).

## Bloco A — Ciclos CRUD completos com verificação de persistência
Para cada recurso: criar → ler-de-volta (bate campo a campo) → EDITAR (PUT) → confirmar mudança → deletar → confirmar ausência. Cobre o que rodadas anteriores só criaram/deletaram.
- [ ] Agente: criar → editar nome/voz/prompt → confirmar → deletar
- [ ] Produto: criar → editar preço/estoque/categoria → confirmar → deletar (+ lixeira/restore)
- [ ] Evento agenda: criar → remarcar (mudar start_at) → cancelar
- [ ] Etapa CRM: criar → renomear → deletar; mover lead entre etapas
- [ ] Credencial IA: criar → editar → deletar (com mask correto)
- [ ] Tag/Blocklist: criar → atribuir a contato → remover

## Bloco B — Concorrência e idempotência
- [ ] Criar mesmo agente 2x (ON CONFLICT name) → deve fazer upsert, não duplicar
- [ ] 10 POSTs simultâneos do mesmo recurso → sem race/duplicata
- [ ] Deletar 2x o mesmo id → 2º deve ser idempotente (não 500)
- [ ] Editar recurso já deletado → 404 limpo

## Bloco C — Limites de plano (todos os 6 planos)
Criar conta de cada plano (trial/start_texto/start_voz/pro/scale/enterprise) e verificar:
- [ ] tabs de `/api/auth/me` batem com plan_features.go
- [ ] Endpoints fora do plano → 403 (mass-call, meet, catalog, agenda conforme cada plano)
- [ ] Limites de quantidade (MaxInstances/MaxAgents/MonthlyTokens) são enforçados

## Bloco D — Segurança aprofundada
- [ ] IDOR em TODOS os recursos (agente/produto/evento/etapa/credencial/chave/followup): B não vê/edita/deleta de A
- [ ] SQL injection em campos de busca (`q=`, filtros) e nomes
- [ ] XSS armazenado: criar recurso com `<script>`/`<img onerror>` e ver se algum lugar renderiza sem escapar (grep dangerouslySetInnerHTML + teste visual)
- [ ] Token expirado/adulterado → 401
- [ ] Rate-limit de login/registro
- [ ] Campos mascarados: api_key/token nunca voltam em texto puro no GET

## Bloco E — Robustez de entrada (fuzzing leve)
- [ ] Strings muito longas (10k chars) em nome/prompt → sem 500
- [ ] Unicode/emoji em todos os campos texto
- [ ] Números fora de range (preço, delay_minutes, top_k, limit) → validação, não 500
- [ ] Datas inválidas (start_at malformado, passado) na agenda
- [ ] Arrays vazios / nulls onde espera dados
- [ ] Content-Type errado, body vazio, body gigante

## Bloco F — Fluxos E2E pela UI (Playwright, visão Gemini)
- [ ] Onboarding completo de conta nova (wizard) até o painel
- [ ] Wizard de agente 9 etapas preenchendo cada campo → publicar → confirmar no backend
- [ ] Gestor Fácil 4 etapas → salvar → reabrir e confirmar que carregou
- [ ] Navegação por todas as ~24 views sem tela branca/erro de console
- [ ] Toasts aparecem no lugar certo (top-center) em ações reais

## Bloco G — Consistência backend↔frontend
- [ ] Todo `/api/*` que o frontend chama existe no backend (cruzar lista) — pegar mais casos tipo #N1 (sync-app-state 404)
- [ ] Todo campo que o form envia é lido pelo handler (não cai no vazio)
- [ ] Toda coluna nullable escaneada em string (padrão #N4) — auditar stores com sintoma real

## Dependências / bloqueios conhecidos
- RAG/simulação IA precisam de chave Gemini COM cota (as ~90 atuais estão 429). Conseguir 1 chave viva desbloqueia Bloco relacionado a IA.
- WhatsApp/ligação/massa: nunca disparar envio real (só confirmar guards).

## Log de execução
(preenchido conforme roda)
