# Teste do Sistema de Monitoramento

## ✅ Correções Aplicadas

### 1. PowerShell JSON Redirection (CRÍTICO)
**Problema**: Linhas 79,90,101,113 usavam `>` para redirecionar stdout Python para JSON
**Solução**: Substituído por captura em variável + `Out-File -Encoding UTF8`

**Antes**:
```powershell
& $PYTHON "$BIN_DIR\transcricao_video.py" $VideoPath "base" "pt" > $transcricaoJson
```

**Depois**:
```powershell
$transcricaoOutput = & $PYTHON "$BIN_DIR\transcricao_video.py" $VideoPath "base" "pt" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Log "✗ Falha na transcrição (exit code $LASTEXITCODE)"
    Write-Log "  Saída: $transcricaoOutput"
    return
}
$transcricaoOutput | Out-File -FilePath $transcricaoJson -Encoding UTF8
```

**Verificado**: Teste com Python `-c` mostra que JSON é capturado corretamente e parseável.

---

### 2. Postagem de Vídeos Camera Isolada
**Problema**: TODO não resolvido - vídeos processados não eram postados
**Solução**: Implementada detecção de canal + chamada para `Postar-Ou-Agendar`

**Código adicionado** (MonitorarVideos.ps1:48-92):
- Detecta canal do nome do arquivo (regex melhorado)
- Extrai título
- Chama `Postar-Ou-Agendar` com tratamento de erro
- Logs informativos se canal não for detectado

---

### 3. Detecção de Canal em Pastas Gerais
**Problema**: Regex `^([^_]+)_` capturava apenas primeiro segmento ("Stand" em vez de "Stand up IA")
**Solução**: Regex aprimorado com fallback

**Código** (MonitorarTodasPastas.ps1:118-130):
```powershell
# Tenta capturar tudo até o último underscore antes de um provável ID (8+ chars alfanuméricos)
if ($nomeBase -match '^(.+?)_[a-zA-Z0-9]{8,}$') {
    $canalSlug = $Matches[1]
    $canalNome = $canalSlug -replace '_', ' '
    Write-Log "Canal detectado (com ID): $canalNome"
    $canal = $canalNome
}
# Fallback: apenas primeiro segmento antes de underscore
elseif ($nomeBase -match '^([^_]+)_') {
    $canalSlug = $Matches[1]
    $canalNome = $canalSlug -replace '_', ' '
    Write-Log "Canal detectado (primeiro segmento): $canalNome"
    $canal = $canalNome
}
```

---

### 4. Validação de Canal em classificar_tema.py
**Problema**: Canal detectado por keywords podia não existir em youtube_canais.json
**Solução**: Função `selecionar_canal()` agora valida match exato ou parcial

**Código** (classificar_tema.py:244-262):
```python
# Valida que o canal existe no youtube_canais.json
canal_escolhido = candidatos[0]

# Carrega youtube_canais.json para validar
try:
    with open(CANAIS_JSON, "r", encoding="utf-8") as f:
        canais_raw = json.load(f)
    
    # Procura match exato ou parcial
    for canal_data in canais_raw:
        nome = canal_data.get("nome", "")
        if nome.lower() == canal_escolhido.lower() or canal_escolhido.lower() in nome.lower():
            return canal_data["nome"]  # Retorna nome exato do JSON
    
    print(f"[classificar] AVISO: canal '{canal_escolhido}' não encontrado em youtube_canais.json", file=sys.stderr)
    return None
except Exception as e:
    print(f"[classificar] Erro ao validar canal: {e}", file=sys.stderr)
    return canal_escolhido  # Retorna mesmo assim como fallback
```

---

### 5. Detecção Visual Implementada
**Problema**: `detectar_tipo_visual()` era placeholder que sempre retornava "camera"
**Solução**: Heurística implementada usando FFmpeg scene detection

**Código** (segmentar_video.py:83-116):
```python
# Extrai sample do vídeo e conta frames com mudanças
cmd = [
    "ffmpeg",
    "-ss", str(timestamp),
    "-i", str(video_path),
    "-t", str(duracao_sample),
    "-vf", "select='gt(scene,0.3)',showinfo",
    "-f", "null", "-"
]

result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")

# Conta quantas mudanças de cena no sample
mudancas = result.stderr.count("pts_time:")

# Heurística: > 3 mudanças em 2s = tela (interface animada)
# <= 3 mudanças = câmera (pessoa parada ou se movendo pouco)
if mudancas > 3:
    return "tela"
else:
    return "camera"
```

---

### 6. Tratamento de Erros Melhorado
**Adicionado**:
- Try-catch em todas as chamadas `Postar-Ou-Agendar`
- Logs detalhados com exit codes
- Mensagens informativas sobre canais não encontrados
- Validação de canal com `--listar-canais` (MonitorarTodasPastas.ps1:140-145)

---

## 🧪 Como Testar

### Teste 1: Camera Isolada
```powershell
# Crie arquivo de teste
$pastaCamera = "D:\recapd-ambientes\producao\fabrica-viral\videos_para_postar\camera_isolada"
# Copie um vídeo com nome: Stand_up_IA_teste_abc12345.mp4
# Inicie: .\IniciarMonitoramento.ps1
# Verifique logs: Get-Content "D:\recapd-ambientes\producao\logs\monitoramento\monitor.log" -Tail 50
```

### Teste 2: Corte Temático
```powershell
$pastaCorte = "D:\recapd-ambientes\producao\fabrica-viral\videos_para_postar\corte_tematico"
# Copie vídeo multi-tema
# Sistema vai: transcrever → classificar → segmentar → gerar shorts → postar
```

### Teste 3: Pastas Gerais
```powershell
$pastaGeral = "D:\recapd-ambientes\producao\fabrica-viral\videos_para_postar\com_minha_foto"
# Copie vídeo: Canal_Nome_titulo_id123456.mp4
# Sistema detecta canal e posta/agenda
```

---

## 📊 Status Final

| Item | Status | Arquivo |
|------|--------|---------|
| JSON redirection | ✅ Corrigido | MonitorarVideos.ps1:119-166 |
| Postagem camera isolada | ✅ Implementado | MonitorarVideos.ps1:48-92 |
| Detecção canal melhorada | ✅ Implementado | MonitorarTodasPastas.ps1:118-145 |
| Validação canal LLM | ✅ Implementado | classificar_tema.py:244-262 |
| Detecção visual | ✅ Implementado | segmentar_video.py:83-116 |
| Tratamento erros | ✅ Melhorado | Todos os scripts |

---

## ⚠️ Pendências Conhecidas (Opcionais)

1. **Erro handling upload**: Se `youtube_poster.py` falha, vídeo fica em limbo
   - Solução futura: Sistema de retry ou fila de falhas

2. **Estado de processamento**: Não há tracking de qual vídeo está em qual etapa
   - Solução futura: Banco de dados ou arquivo de estado

3. **Concorrência**: FileSystemWatcher pode processar múltiplos vídeos simultaneamente
   - Solução futura: Fila de processamento com controle de concorrência

---

**Data de conclusão**: 2026-10-07  
**Verificado por**: Revisão de código + testes unitários PowerShell
