# Canal Histórias em Frames — kit completo

**Nome:** Histórias em Frames
**Handle:** @HistoriasEmFrames (se estiver ocupado: @HistoriasEmFramesBR, @HistoriasEmFrame, @HistoriasEmFramesOficial)
**Slogan:** Histórias que prendem do primeiro ao último frame
**Cores:** dourado `#FFC83D` + noite `#080A12`

## Arquivos desta pasta

| Arquivo | Onde usar |
|---|---|
| `perfil.png` | Foto do perfil (800x800). Principal: foto #13. |
| `perfil_opcao2.png`, `perfil_opcao3.png` | Outras opções de perfil (fotos #28 e #19). |
| `banner.png` | Banner do canal (2560x1440). Rosto, nome e handle ficam dentro da área que aparece no celular. |
| `marca_dagua.png` | Marca d'água dos vídeos (150x150): YouTube Studio > Personalização > Marca. |
| `logo.png` / `logo_sem_fundo.png` | Logo "HF" (1024x1024) pra TikTok, Instagram, Kwai, Facebook. |
| `descricao.txt` | Texto da aba "Sobre" do canal. |
| `palavras_chave.txt` | Palavras-chave do canal (Configurações > Canal). |
| `bios_redes_sociais.txt` | Bios prontas pra TikTok, Kwai, Instagram e Facebook. |
| `comentarios_fixados.txt` | Perguntas pra fixar nos comentários (engajamento). |
| `modelo_descricao_e_playlists.txt` | Hashtags por gênero e nomes de playlists. |
| `canal.json` | Os mesmos dados em formato de máquina (pro pipeline). |
| `gerar_kit_canal.py` | Regera tudo. Pra trocar nome, handle ou foto, edite as linhas do topo e rode. |

## Passo a passo pra criar

1. Criar o canal com o nome acima e tentar o handle (ou uma alternativa).
2. Subir `perfil.png`, `banner.png` e `marca_dagua.png`.
3. Colar `descricao.txt` no "Sobre" e `palavras_chave.txt` nas palavras-chave.
4. País: Brasil · idioma: Português (Brasil) · categoria: Entretenimento.
5. Criar as playlists de `modelo_descricao_e_playlists.txt`.
6. Quando o handle estiver confirmado, avisar pra trocar a marca d'água do pipeline
   (hoje os vídeos saem com `@InovareStories`).

## Pra este canal durar

O que derrubou os 22 canais em 04/09 foi o padrão de rede de spam (postagem 100% automática,
dezenas de vídeos por dia, vários canais iguais). Neste canal:

- Ao subir cada vídeo, marcar **"Conteúdo alterado ou sintético: Sim"** (as imagens e a voz são de IA).
  A descrição do canal já diz isso.
- 1 a 2 vídeos por dia, em horários fixos, com alguém olhando o vídeo antes de publicar.
- Um canal só, sem espelhar os mesmos vídeos em outros canais.
- Trilhas: o pipeline já bloqueia as faixas com copyright (lista em hipercool-materiais/_curadoria).
