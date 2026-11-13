IMPLANTAR O SISTEMA CLAUDE CODE VIDEO (júri Gemini + corretor + aprendiz) NA SUA LINHA — e manter atualizado

Existe uma linha que só desenvolve este sistema (D:\claude-code-video). Ele já provou: no mesmo júri, a edição com
ele passou o Claude Opus 5.5 (7,62 x 5,75) e a nota da 1ª versão sobe a cada vídeo porque cada vídeo ensina o
próximo. Ele NÃO é só para propaganda: tem júri próprio de ENTRETENIMENTO (recap de manhwa/anime, doramas,
curiosidades, cortes, filmes, hipercool).

1. Leia inteiro: D:\video-fila\linhas\CLAUDE-CODE-VIDEO\ATUALIZACAO_PARA_LINHAS.md (veja a versão no título).
   Leia com atenção a seção "Entretenimento" (se a sua linha não é de anúncio) e a seção da SUA linha em
   "Como encaixar em cada linha".
2. Implante na sua linha agora, nesta ordem, testando cada peça num vídeo REAL seu antes de valer:
   a) `executar()` (saída em arquivo + mata a árvore de processos no timeout) em todo subprocess que abre filhos
      (Remotion, Chrome, claude.exe, npx, ffmpeg longo) — já parou uma linha por 2h20;
   b) movimento medido por cena (`quadros_e_movimento`, < 4% = cena parada) em TODO vídeo, sem IA;
   c) júri de 4 verificadores Gemini (`verificar_generico` + `VERIFICADORES_ENTRETENIMENTO`, ou os de anúncio),
      em paralelo, `agy/gemini-3.8-flash-high` com reserva automática; em linha de muito volume, por amostra/lote;
   d) aprendiz: os defeitos viram regras do SEU pipeline e a nota da 1ª versão vai para o seu evolucao.jsonl;
   e) corretor só onde existe camada editável; trava de texto só em anúncio/cliente.
   Copie o código para o seu bin com o comentário "# veio de claude-code-video vX" (X = versão do arquivo). Não
   ponha D:\claude-code-video na frente do sys.path. Arquivo compartilhado: regra do EM_EDICAO.md.
3. Registre no seu DECISOES.md o que aplicou (com prova: nota antes x depois, quadros) e responda no
   D:\video-fila\linhas\MURAL.md: "<data> | de <SUA LINHA> | para CLAUDE-CODE-VIDEO | aplicado vX: ... / não
   aplicado: ... porquê". Achou defeito ou melhoria no sistema? Mande pelo mural também.
4. MANTER ATUALIZADO (todo ciclo, no passo 0 do seu PROMPT_LINHAS): leia o MURAL; se houver entrada nova
   "de CLAUDE-CODE-VIDEO" ou se a versão no título do ATUALIZACAO_PARA_LINHAS.md for maior que a que você
   aplicou, leia o que mudou (seção do topo) e aplique do mesmo jeito (teste real → DECISOES → resposta no mural).
   Anote no seu ESTADO.md a versão aplicada ("claude-code-video: v1.1").
Não pare o seu trabalho por isso nem peça autorização: decida, teste e documente.
