# Skills, plugins e MCP para os projetos de vídeo — o que vale (Opus, 04/11 03:40)

Fonte: rodada `rodadas/2026-11-04_skills` (argon-pesquisa 49 links + gemini-pro-pesquisa 42 links; 70 diferentes;
TODOS existem no GitHub, conferido). Estrelas não conferidas (cota da API) — não citar números deles como fato.
Hoje NÃO há nenhuma skill de vídeo instalada (só C:\Users\Haylla\.claude\skills\synced, genérica).

## Regra de instalação
- Skill de terceiro = instruções + scripts de outra pessoa. Ler o SKILL.md e os scripts ANTES; instalar na pasta
  `.claude/skills` do PROJETO que usa (não global). Oficiais (remotion-dev, anthropics, heygen, microsoft) são as mais seguras.
- Pesquisador não instala nada: quem implanta é o chat do projeto, seguindo `video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md`.

## Vale a pena (por chat)
### Chat dos VÍDEOS LONGOS (FFmpeg + Kaggle)
1. kajisho5/qc-skill + kajisho5/media-analysis-skill — checagem local (ffprobe) de resolução, quadro preto, congelado,
   áudio mudo, legenda. Comparar com o que a VigilanciaSistema/medidores já fazem; aproveitar só o que faltar.
2. HUANGCHIHHUNGLeo/claude-real-video — quadros-chave por troca de cena + transcrição: revisar um longo de 1–4 h com
   poucos quadros (regra "veredito só com quadro real").
3. zenstory-ai/video-recap-skills — pipeline de recap narrado (cenas + ASR + VLM + roteiro + voz): comparar etapa por
   etapa com o nosso recap longo.
4. kajisho5/remotion-ffmpeg-skill — padrão "Remotion só renderiza a camada de overlay e o FFmpeg compõe": só se o longo usar Remotion.
5. VOZ (conferido no código): RVC já usa Applio+FCPE e base Kokoro (voz_clonada_nuvem.py:65-109). INÉDITO:
   - run_infer_script é chamado 1 vez POR FRASE (:93-109): juntar frases em blocos de ~30 s com silêncio e cortar
     depois. Medir antes no log "[i/n] ... (x s)" quanto é custo fixo por frase.
   - roteiro anotado {speaker, text, instruct} + voz fixa por personagem (padrão de Finrandojin/alexandria-audiobook).
   - teste A/B MeanVC (ASLP-lab/MeanVC, zero-shot, Apache) x RVC: testes de voz estão PAUSADOS — só com OK da dona.
### Chat que COORDENA OS CURTOS
1. sharon-laicc/viral-video-decomposer — tabela plano a plano e gancho dos 3 s de um viral: alimenta o aprendizado com
   parceiros. Usar SÓ com arquivo local já baixado pela fila (com URL ele roda yt-dlp = rajada no IP de casa).
2. Vincentwei1021/video-talkcraft — receitas de câmera "anti-slideshow" sincronizadas com a locução: painel parado de manhwa.
3. iart-ai/motion-skills — tipografia cinética: ideias novas de entrada/saída de palavra para a legenda MIX.
4. ZeroPointRepo/youtube-skills + mvanhorn/last30days-skill — termos em alta para títulos (só leitura).
5. remotion-dev/skills (OFICIAL) — para as linhas em Remotion (claude-code-video, produto). Melhorador do
   claude-code-video está DESLIGADO até a dona: instalar a skill não religa nada.
6. kajisho5/ffmpeg-skill (check.py/look.py) — validação por plataforma (zona segura do TikTok/Reels) e folha de contato.

## PROIBIDO rodar (só ler código como referência)
- shepsci/kaggle-skill, HarrisonYangKuang/agent-gpu-pool — falam com o Kaggle pelo IP local (incidente 02/11).
- dreammis/social-auto-upload, trypostit/trypost — postam sem proxy por conta e sem publishAt.
- GTAI-1/flow-mcp — automação de navegador no Flow (nosso Flow é só HTTP).
- op7418/Youtube-clipper-skill — yt-dlp direto.
- Pequenos MCPs de FFmpeg com shell=True (ex. video-creator/ffmpeg-mcp); abandonados: egoist/ffmpeg-mcp, hyepartners-gmail/vibevideo-mcp.

## Placar desta rodada (skills)
Argon 49 links / 28 só dele (achou o catálogo dedicado zhuyansen/awesome-claude-video-skills e a família kajisho5);
Gemini Pro 42 / 21 só dele, 6x mais rápido (334 s x 1.786 s). Nenhum dos dois inventou link nesta rodada.
