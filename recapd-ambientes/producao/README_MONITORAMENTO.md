# Sistema de Monitoramento Automático de Vídeos

Sistema completo para processamento e postagem automática de vídeos no YouTube com dois cenários principais e suporte a pastas adicionais.

## 📁 Estrutura

```
D:\recapd-ambientes\producao\
├── bin/
│   ├── transcricao_video.py          # Transcrição via Whisper
│   ├── classificar_tema.py           # Classificação de tema via LLM
│   ├── segmentar_video.py            # Segmentação temporal e visual
│   ├── gerar_shorts.py               # Geração de shorts verticais
│   ├── processar_camera.py           # Crop/upscale para câmera isolada
│   ├── verificar_postagem_canal.py   # Verifica se canal já postou hoje
│   ├── calcular_proximo_horario.py   # Calcula horário de agendamento
│   └── youtube_poster.py             # Upload para YouTube
│
├── MonitorarVideos.ps1               # Monitor para pastas especiais
├── MonitorarTodasPastas.ps1          # Monitor para pastas gerais
├── IniciarMonitoramento.ps1          # Script principal de inicialização
│
└── fabrica-viral/
    └── videos_para_postar/
        ├── camera_isolada/           # Cenário A: isolamento de câmera
        ├── corte_tematico/           # Cenário B: corte multi-tema
        ├── com_minha_foto/           # Pasta geral (auto-posta)
        ├── baixados_agora/           # Pasta geral (auto-posta)
        └── _sem_imagem_base/         # Pasta geral (auto-posta)
```

## 🎯 Cenários de Processamento

### Cenário A: Câmera Isolada (`camera_isolada/`)
Para gravações OBS onde você quer isolar apenas sua câmera.

**Processamento:**
1. Crop fixo: 600×490 pixels da posição (x=60, y=0)
2. Upscale para Full HD 1920×1080
3. Codec: H.264 com preset ultrafast
4. **Postagem automática**: detecta canal do nome do arquivo e posta/agenda

**Uso:**
- Coloque o vídeo `.mp4` na pasta `camera_isolada/`
- Formato do nome: `CanalNome_titulo_id.mp4`
- O sistema automaticamente processa, gera `*_fullhd.mp4` e posta/agenda

### Cenário B: Corte Temático (`corte_tematico/`)
Para vídeos com múltiplos temas em diferentes momentos.

**Processamento:**
1. **Transcrição** → extrai áudio e transcreve com Whisper (timestamps)
2. **Classificação** → LLM identifica temas (IA, política, finanças, etc)
3. **Segmentação** → corta por tema + mudanças visuais (câmera/tela)
4. **Shorts** → gera clipes verticais 9:16 de até 60s
5. **Postagem** → cada segmento vai para seu canal temático

**Uso:**
- Coloque o vídeo `.mp4` na pasta `corte_tematico/`
- O sistema processa automaticamente todo o pipeline

**Categorias suportadas:**
- `ia` → canais de IA/tecnologia
- `financeiro` → finanças/investimentos
- `politica` → política/governo
- `motivacao` → motivação/desenvolvimento pessoal
- `entretenimento` → humor/curiosidades
- `educacao`, `anime`, `gaming`, `musica`, `danca`

### Pastas Gerais
Pastas como `com_minha_foto/`, `baixados_agora/`, etc. têm processamento simplificado:

**Processamento:**
1. Detecta canal do nome do arquivo (padrão: `CanalNome_titulo_id.mp4`)
2. Verifica se o canal já postou hoje
3. **Se SIM** → agenda para daqui a 2 horas
4. **Se NÃO** → posta imediatamente

## 🚀 Como Usar

### Iniciar Monitoramento

#### Opção 1: Múltiplas janelas (foreground)
```powershell
.\IniciarMonitoramento.ps1
```
Abre uma janela separada para cada monitor. Ideal para desenvolvimento/debug.

#### Opção 2: Background (jobs)
```powershell
.\IniciarMonitoramento.ps1 -Background
```
Executa como jobs do PowerShell. Ideal para servidor/produção.

**Comandos úteis para jobs:**
```powershell
# Ver status dos jobs
Get-Job

# Ver logs de um job
Receive-Job -Id <ID> -Keep

# Parar todos os jobs
Get-Job | Stop-Job
Get-Job | Remove-Job
```

### Parar Monitoramento
- **Foreground**: Feche as janelas ou pressione `Ctrl+C`
- **Background**: Execute os comandos Stop-Job acima

## 📊 Logs

Todos os logs são salvos em:
```
D:\recapd-ambientes\producao\logs\monitoramento\
├── monitor.log           # MonitorarVideos.ps1
└── monitor_todas.log     # MonitorarTodasPastas.ps1
```

## ⚙️ Lógica de Postagem/Agendamento

O sistema verifica via **YouTube Data API v3** se o canal já postou hoje (timezone BRT/UTC-3):

- ✅ **Já postou hoje** → Agenda para daqui a 2 horas
- ❌ **Ainda não postou** → Posta imediatamente

Isso garante distribuição inteligente de conteúdo e respeita o limite de ~6 uploads/dia/canal.

## 🔧 Configurações

### Credenciais
As credenciais dos canais estão em:
```
D:\credenciais-canais\youtube_canais.json
```

Cada canal precisa de:
- `clientId` + `clientSecret`
- `refresh_token` (OAuth2)

### Python Environment
```
D:\recapd-ambientes\producao\venv\Scripts\python.exe
```

### Modelos
- **Whisper**: faster-whisper base (CPU, int8)
- **LLM**: OpenAI-compatible proxy em `http://157.173.207.22:20128`
  - Modelo: `antigravity/gemini-2.5-flash-lite`

## 📝 Formato de Nome de Arquivo

Para que o sistema detecte automaticamente o canal nas pastas gerais, use:

```
CanalNome_titulo_id.mp4
```

Exemplo:
```
Stand_up_IA_conversa_engracada_abc123.mp4
                     ↑
              Detecta "Stand up IA"
```

## 🛠️ Troubleshooting

### Vídeo não foi processado
1. Verifique os logs em `logs/monitoramento/`
2. Confirme que o arquivo é `.mp4`
3. Aguarde ~2s após copiar o arquivo (FileSystemWatcher espera arquivo terminar)

### Erro "moov atom not found"
- O sistema usa preset `ultrafast` e aguarda 5s após processamento
- Se persistir, o arquivo pode estar corrompido na origem

### Canal não encontrado
- Verifique o nome no arquivo vs `youtube_canais.json`
- O match é case-insensitive e aceita match parcial

### Erro na transcrição/LLM
- Verifique conectividade com o proxy LLM
- Confirme que o áudio do vídeo não está corrompido

## 📦 Dependências

Python:
```
faster-whisper
ffmpeg (binário)
```

PowerShell:
```
.NET FileSystemWatcher (built-in)
```

## 🔐 Segurança

- ⚠️ Nunca commite `youtube_canais.json` no git
- ⚠️ Tokens de API são renovados automaticamente via refresh_token
- ⚠️ Logs podem conter nomes de canais (não contêm tokens)

## 📞 Suporte

Em caso de problemas:
1. Consulte os logs
2. Verifique se o Python environment está ativo
3. Confirme que FFmpeg está no PATH
4. Teste scripts individuais antes do monitoramento completo

---

**Sistema criado em 2026-10-07**  
Processamento automático de vídeos com IA para 50+ canais YouTube.
