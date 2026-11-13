# Regras Oficiais do Projeto e Padrão de Trabalho (Hipercool SaaS)

Este documento define o fluxo de trabalho (Workflow) estrito e obrigatório que o agente Frontend (Antigravity) e o Usuário devem seguir em todas as fases de construção das sub-abas do projeto.

## Workflow Obrigatório por Fase (Sub-Aba)

1. **Proposta de Funcionalidades (Brainstorming com Pesquisa GitHub)**
   - O Agente deve, **obrigatoriamente**, pesquisar na web e no GitHub por projetos open-source e painéis de IA (SaaS, AI Agent UI, Voice AI, LangGraph, etc) para se inspirar e trazer ideias validadas e inovadoras pelo mercado.
   - O Agente sugere funcionalidades de nível Enterprise baseadas no que as grandes startups e projetos do GitHub estão implementando, elevando o nível de criatividade.
   - **Regra de Separação de Abas:** Sempre que propor novas funcionalidades, o agente deve dividi-las CLARAMENTE em duas listas:
     - **A)** Melhorias para as Sub-abas Existentes (Aprimoramento do que já tem).
     - **B)** Novas Sub-abas (Coisas totalmente novas que devem ficar isoladas).
   - **Regra de Foco na Sub-Aba:** O Agente NUNCA deve pular para a próxima sub-aba automaticamente. O trabalho deve continuar na aba atual, em ciclos iterativos de "pesquisa -> proposta -> implementação -> novas propostas", até que o Usuário diga as palavras "próximo" ou "acabou".
   - O Usuário aprova, modifica ou descarta as propostas listadas.

2. **Implementação UI/UX (Front-end Seguro e Mockado)**
   - O Agente codifica a interface mantendo o design system (Glassmorphism, Dark Mode, Lucide icons).
   - *Regra estrita:* É **obrigatória** a injeção de dados *mock* (falsos/visuais) para evitar telas vazias caso o backend não tenha dados, permitindo que o usuário visualize a UX completa.

3. **Revisão e Ajustes Finos**
   - O Usuário testa a interface no navegador e passa o feedback de usabilidade/design.
   - O Agente corrige até a aprovação.

4. **Documentação para o Agente Backend**
   - Com a UI aprovada, o Agente **obrigatoriamente** atualiza o arquivo `backend_implementation_plan.md`.
   - Deve documentar as regras de negócio, tabelas de banco de dados, endpoints e WebSockets que o backend deverá construir.

5. **Conclusão e Avanço**
   - O Agente faz o resumo da entrega e solicita autorização para avançar para a próxima fase.
