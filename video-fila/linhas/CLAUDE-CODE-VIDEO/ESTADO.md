# CLAUDE-CODE-VIDEO — ESTADO (retomar daqui) — atualizado 28/10 15h

Linha: o SISTEMA de Reels em Remotion (`D:\claude-code-video`). Missão: melhorar até a 1ª versão chegar à meta; aí
as outras linhas copiam (MURAL + ATUALIZACAO_PARA_LINHAS.md). Decisões com data/motivo/como desfazer: DECISOES.md.

## Quem melhora (dona 28/10)
O **melhorador.py fica DESLIGADO até a dona mandar ligar** (ela só liga quando abandonar o chat). Até lá o CHAT
melhora o sistema a CADA vídeo que sai: ler a nota/defeitos da 1ª versão (evolucao.jsonl + estado.json do
trabalho), achar o que se repete, mudar 1 coisa por vez (manual, kit, config ou código) e conferir no vídeo seguinte.

## Como roda
Tarefa ClaudeCodeVideo (20 min, oculta: rodar_oculto.vbs + `import sem_janela`) → `gerar.py --auto`:
roteiro (argon-gemini) → voz (anúncio: ELENCO de famosos que adulto conhece, com diálogo e BORDÃO gravado;
entretenimento: clone por nicho) → imagens Flow → preparação das fotos (`camadas.py`: profundidade, camadas,
recorte, fundo limpo) → referência (estudo de um vídeo viral do mesmo tipo) → editor hx-maos-gemini em Remotion
(EDITOR*.md + APRENDIDO*.md + kits `lib/efeitos.tsx`, `karaoke.tsx`, `vivo.tsx`, `tres.tsx`) → render → lapidar (júri
de 4 Gemini + trava de texto + movimento medido → corretor, 3 rodadas) → aprendiz → saida/<conta>.
Em paralelo, a cada rodada: `referencia.py rodada` (1 Short viral novo a cada 3 h, analisado).
Cadeia de modelos: Argon → Gemini Antigravity → Gemini API (sem Opus/Kiro). O proxy Argon (:20141) + túnel NÃO voltam
sozinhos depois que o PC reinicia (28/10 religados à mão; é do gemini-argo).

## Métrica (evolucao.jsonl)
Nota da 1ª versão, mesmo júri. Meta: 1ª >= 7,5, final >= 8, diretor >= 7, sem grave.
Até 28/10: 1ª versão média ~5,95 (4,25 a 6,5), final ~6,7. Ainda longe da meta; o corretor sobe ~0,8 por vídeo.
Tempo por vídeo 2h–2h40 (júri+correção 65–85 min, editor 28–40, Flow 8–18, clone 3–18, fotos vivas 4–6).

## A conferir nos próximos vídeos (28/10)
1. 1º anúncio com elenco/diálogo/bordão: o roteiro usou `quem`/`bordao`? clone por voz OK? bordão escrito na tela?
2. 1º vídeo com efeitos vivos (`cenas[].vivo`): o editor usou RecorteVivo/Profundidade/Impacto? movimento subiu?
3. 1º entretenimento com referência (sol_se_apagasse): plano.md diz o que levou? retenção subiu?
4. Legenda nova (mola + pulinho) sem palavra grudada.
5. Narrador do Chris: tom corrigido para 151 Hz (medido); amostra para a dona em
   D:\hipercool-materiais\claude-code-video\amostras\narrador_chris_v2.wav.

## Ainda falta trazer do historias-em-frames (levantado 11/11, antes de arquivar)
> 11/11: os 8 viraram pedidos abertos em `D:\claude-code-video\PEDIDOS_DO_DONO.md` (o melhorador faz 1 por vez,
> com teste/crítico/backup). Cópia do historias no Drive conferida (rclone check: 0 diferenças nas 4 pastas).
A dona quer arquivar `D:\historias-em-frames` (absorvido por esta linha). Visual (parallax, profundidade, recorte,
fundo limpo, legenda, câmera) JÁ veio. Estas 8 ainda não vieram — trazer antes de apagar as pastas locais
(cópia de segurança em `manhwa-drive:videos-backup/historias-em-frames/arquivo_20261111/`):
1. Capa IA com poses + teste A/B no Studio (`bin\capa_ia_historias.py`, `config\POSES_HISTORIAS.py`, `ab_tracker.py`, `metricas_historias.py`)
2. SFX/foley por palavra-gatilho (`fx_audio_final.py`, `fx_foley.py`, `config\gatilhos_palavras.json`)
3. Curva de clímax do locutor + microcortes de pausa (`narracao_curva.py`)
4. Catálogo de 251 memes por emoção (`memes_catalogo.py`; o JSON já foi copiado p/ `D:\hipercool-videos\config\`)
5. Escalada da trilha pelo arco narrativo (`music_escalation.py`)
6. Transições elementais por palavra (`elemental_transitions.py` + overlays)
7. Perguntas de engajamento / comentário fixado (`community_hooks.py`)
8. Banco de personagens (rosto igual entre cenas) (`character_bank.py`)
Ainda leem o historias: `postador-de-videos\bin\catalogo.py:40,61` e `montar-fila-materiais.py:81` — tirar antes de apagar.
NÃO apagar com Explorer/rm -rf: prod/teste/beta/workspace têm JUNÇÕES para `hipercool-materiais\assets`, `models` e o
venv central (98 GB "aparentes", ~500 MB próprios). Remover junção = `cmd /c rmdir <junção>` (só o atalho).

## PRECISA DA DONA
- Vozes de famosos nos anúncios: ela escolheu usar sabendo do risco (28/10).
- Ouvir a amostra do narrador do Chris.
