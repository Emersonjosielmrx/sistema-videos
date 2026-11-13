# ManhwaReact - Guia Rápido de Uso

## ✅ Status do Projeto
O projeto está **configurado e pronto para uso**!

- Python 3.13 instalado e funcionando
- Todas as dependências necessárias já instaladas:
  - faster-whisper (transcrição)
  - mediapipe (detecção de lábios)
  - opencv (cv2) para processamento de vídeo
  - numpy, matplotlib, PIL para processamento de imagem
  - auto-editor para cortes
  - E muitas outras...

## 🚀 Como Usar

### Método 1: Botões na Área de Trabalho (Mais Fácil)

1. **Coloque o vídeo** no atalho "ManhwaReact - COLOQUE AQUI" (pasta `1-COLOQUE-AQUI\`)
2. **Clique em "ManhwaReact - PROCESSAR"** na área de trabalho
3. **Pronto!** O vídeo processado aparece em `D:\hipercool-materiais\manhwa-react\shorts\`

### Método 2: Linha de Comando

Abra o PowerShell na pasta do projeto:

```powershell
cd "D:\manhwa-react"

# Processar um vídeo específico
.\.venv\Scripts\python.exe manhwareact.py process "caminho\do\video.mp4"

# Processar todos os vídeos da pasta inbox
.\.venv\Scripts\python.exe manhwareact.py batch

# Ficar vigiando a pasta e processar automaticamente
.\.venv\Scripts\python.exe manhwareact.py watch

# Analisar um vídeo (info técnica)
.\.venv\Scripts\python.exe manhwareact.py analyze "video.mp4"
```

### Método 3: Scripts BAT (Atalhos Rápidos)

```bat
scripts\processar.bat "D:\downloads\meu-video.mp4"
scripts\lote.bat                    :: processa tudo em inbox\
scripts\vigiar.bat                  :: fica monitorando inbox\
```

### Cortar só a câmera (vídeo inteiro só com a webcam, 1920x1080)

Arraste a gravação do OBS (webcam em cima, vídeo/desenho embaixo) em cima do atalho **"ManhwaReact - CORTAR CAMERA"**
na área de trabalho (`scripts\BOTAO_CORTAR_CAMERA.bat`). Sai em `D:\hipercool-materiais\manhwa-react\camera\`
`<nome>_SO_CAMERA_1080p.mp4` + `<nome>_SO_CAMERA_area.jpg` (retângulo vermelho = o que foi cortado, para conferir).

```powershell
.\.venv\Scripts\python.exe manhwareact.py camera "video.mp4"            # ou uma pasta inteira
.\.venv\Scripts\python.exe manhwareact.py camera "video.mp4" --so-detectar   # só mostra a área (previa), sem cortar
.\.venv\Scripts\python.exe manhwareact.py camera "video.mp4" --area 3:0:714:402   # área manual se a detecção errar
```

Acha sozinho onde a câmera termina (borda reta presente em todos os quadros, perto de onde uma câmera 16:9 termina;
nas gravações de 06/10: linha 402, câmera 714x402). Se não achar, para e pede `--area`. Encode em pedaços de ~17 min
(se faltar memória refaz só o pedaço; rodar de novo continua de onde parou), áudio alinhado ao 1º quadro do vídeo
(o OBS às vezes começa o vídeo segundos depois do áudio) e confere se o número de quadros bate com o original.

## 📁 Estrutura de Pastas

| Pasta | Função |
|-------|--------|
| `1-COLOQUE-AQUI\` | Jogue os vídeos brutos aqui |
| `output\` | Saída temporária do processamento |
| `work\` | Cache e arquivos intermediários |
| `D:\hipercool-materiais\manhwa-react\shorts\` | **VÍDEOS PRONTOS** para publicar |

## ⚙️ Opções Úteis

```powershell
# Forçar reprocessamento (ignora cache)
python manhwareact.py process "video.mp4" --force

# Processar sem usar IA/Claude (mais rápido, menos inteligente)
python manhwareact.py process "video.mp4" --no-llm

# Modo dry-run (simula sem renderizar)
python manhwareact.py process "video.mp4" --dry-run

# Usar modelo Whisper diferente
python manhwareact.py process "video.mp4" --whisper medium

# Ativar trilha de fundo
python manhwareact.py process "video.mp4" --music
```

## 🎬 O que o Sistema Faz Automaticamente

1. ✅ Detecta o layout (webcam em cima, conteúdo embaixo)
2. ✅ Limpa e melhora o áudio (denoise, compressor, loudness)
3. ✅ Transcreve com Whisper (Groq API ou local)
4. ✅ Detecta quem está falando (você vs narração do vídeo)
5. ✅ Remove silêncios e vícios de linguagem
6. ✅ Gera legendas animadas palavra por palavra
7. ✅ Adiciona gancho inicial, marca d'água, CTAs
8. ✅ Insere divisória animada entre webcam e conteúdo
9. ✅ Zoom na webcam enquanto você fala
10. ✅ Adiciona emojis, reações e overlays
11. ✅ Cria thumbnail automaticamente
12. ✅ Gera título, descrição e tags otimizadas
13. ✅ Prepara arquivo `.postar.json` para publicação

## 🔧 Comandos Avançados

```powershell
# Gerenciar canais da rede
python manhwareact.py canais

# Gerar catálogo de memes
python manhwareact.py memes

# Analisar ideias de formato
python manhwareact.py ideias "D:\videos"

# Gerar trilhas originais com MusicGen
python manhwareact.py musica --por-mood 3

# Aprovar vídeos antes de publicar
python manhwareact.py aprovar

# Publicar no YouTube
python manhwareact.py publicar --simular    # teste
python manhwareact.py publicar              # real
```

## ❓ Resolução de Problemas

### Erro: "ffmpeg não encontrado"
Verifique se existe: `D:\hipercool-materiais\bin\ffmpeg.exe`

### Erro na transcrição
O sistema tenta Groq primeiro, depois fallback para Whisper local.
Chaves Groq em: `D:\postador-de-videos\secrets\groq_keys.json`

### Vídeo não processa
- Verifique se o vídeo está em formato MP4/MKV/MOV/WEBM
- Use `--force` para ignorar cache
- Veja os logs em `logs\`

## 📖 Documentação Completa

- `README.md` - Documentação técnica completa
- `HANDOFF.md` - Histórico e decisões do projeto
- `PLANO.md` - Roadmap e funcionalidades
- `AUDITORIA.md` - Auditoria técnica
- `config.json` - Todas as configurações

## 🎯 Próximos Passos

1. Teste com um vídeo: coloque em `1-COLOQUE-AQUI\` e rode o processador
2. Revise a saída em `D:\hipercool-materiais\manhwa-react\shorts\`
3. Ajuste configurações em `config.json` se necessário
4. Configure o canal no YouTube para publicação

---

**Dica**: Para ver todas as opções de um comando:
```powershell
python manhwareact.py <comando> --help
```
