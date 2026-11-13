# Adicionar PCs Linux no Sistema de Vídeos

Sistema para integrar os 2 PCs Linux na Tailscale (x200ma e server2-vps) como workers de vídeo.

## Status Atual (22/10/2026)

| Máquina | IP | Acesso | Situação |
|---|---|---|---|
| `server2-vps` | 100.101.154.80 | **Tailscale SSH (root) — FUNCIONANDO** | 8 núcleos, 23 GB RAM, 290 GB livres, ffmpeg 5.1, Python 3.11. É VPS de PRODUÇÃO (n8n, Hermes, Evolution, cas-*, faster-whisper em Docker): vídeo pesado só com limite de núcleos |
| `emerson-x200ma` | 100.87.195.108 | **Tailscale SSH (emerson) — FUNCIONANDO desde 22/10** | Zorin OS 18, 2 núcleos, 1,8 GB RAM (só ~0,5 GB livre), 259 GB livres, Python 3.12, **sem ffmpeg**; sudo pede senha. Máquina fraca: só tarefa leve |

## Canal mais simples: Tailscale SSH (sem abrir porta, sem chave, sem firewall)

O server2 já usa isso. No x200ma basta rodar **uma vez** no terminal dele (ou mandar a IA de lá rodar):

```bash
sudo tailscale set --ssh
```

Depois disso o PC1 entra direto: `python D:\video-fila\bin\canal_ia_remota.py testar x200ma`.

**Verificação de navegador ("check"):** a regra padrão da Tailscale pede aprovação no navegador
(link `login.tailscale.com/a/...`) de tempos em tempos — enquanto não aprovar, o comando fica parado.
Para automação, em https://login.tailscale.com/admin/acls troque, na regra `ssh`, `"action": "check"` por `"action": "accept"`.

O script grande abaixo (API de status + worker) é **opcional**; com Tailscale SSH o `canal_ia_remota.py executar` já basta.

## PASSO 1 (opcional): Script completo nos PCs Linux

**⚠️ IMPORTANTE: NADA FUNCIONA ATÉ RODAR ESTE SCRIPT NOS 2 PCs LINUX!**

### No PC1 (Windows):

1. Abra o arquivo de instruções:
   ```bash
   cat D:\video-fila\logs\instrucoes_linux.sh
   ```

2. **COPIE TODO O CONTEÚDO** (Ctrl+A, Ctrl+C no terminal ou abra no notepad)

### No terminal de CADA PC Linux (x200ma e server2):

1. **COLE TODO O CONTEÚDO** que você copiou acima

2. Aguarde finalizar (vai pedir senha do sudo)

3. Ao final, anote o **IP Tailscale** que aparecer

4. Me envie o IP para eu adicionar no sistema

**Observação:** O arquivo está no Windows (D:\), você não consegue acessá-lo do Linux. Por isso precisa copiar o conteúdo no PC1 e colar no terminal do Linux.

### O que esse script faz automaticamente:

✅ Habilita SSH  
✅ Abre portas 22, 5000, 8791 no firewall (só Tailscale)  
✅ Cria `/opt/video-producao/` com estrutura completa  
✅ Instala Python, FFmpeg, psutil  
✅ Gera `maquina.json` com specs da máquina  
✅ Cria API de status na porta 5000  
✅ **Instala worker daemon que monitora `/tmp/ia-tarefas/` e executa tarefas automaticamente**  
✅ Configura 2 systemd services (status API + worker daemon)  
✅ Testa tudo  

**Duração:** ~2-3 minutos por máquina

**Depois de rodar:** O PC Linux estará pronto para receber tarefas do PC1 via SSH. O worker daemon roda em segundo plano monitorando tarefas.

---

## PASSO 2: Testar do PC1 (DEPOIS que configurar os Linux)

```bash
# Testar conectividade
python D:\video-fila\bin\canal_ia_remota.py testar x200ma
python D:\video-fila\bin\canal_ia_remota.py testar server2

# Ver status da máquina
python D:\video-fila\bin\canal_ia_remota.py status x200ma
python D:\video-fila\bin\canal_ia_remota.py status server2

# Executar comando remoto
python D:\video-fila\bin\canal_ia_remota.py executar x200ma "df -h"
python D:\video-fila\bin\canal_ia_remota.py executar server2 "free -h"
```

---

## PASSO 3: Comunicação com IA Remota

### Enviar tarefa para IA executar:

```bash
python D:\video-fila\bin\canal_ia_remota.py tarefa x200ma '{"acao": "info_sistema"}'
```

### Como funciona:

1. **PC1 envia** JSON com instruções via SSH → `/tmp/ia-tarefas/tarefa_TIMESTAMP.json`
2. **IA remota lê** o arquivo `/tmp/ia-tarefas/NOVA_TAREFA` (marcador)
3. **IA executa** as instruções do JSON
4. **IA grava resposta** em `/tmp/ia-resposta_TIMESTAMP.json`
5. **PC1 busca** a resposta a cada 2s (timeout 60s)
6. **PC1 mostra** resultado e salva em `D:\video-fila\logs\tarefas_remotas/`

### Exemplo de tarefa estruturada:

```json
{
  "acao": "verificar_requisitos",
  "passos": [
    "python3 --version",
    "ffmpeg -version | head -n1",
    "df -h /opt/video-producao",
    "free -h"
  ]
}
```

A IA remota verá isso em `/tmp/ia-tarefas/NOVA_TAREFA` e deve:
1. Ler o JSON
2. Executar cada passo
3. Gravar resultado em JSON no caminho especificado

---

## Arquivos Criados

### PC1 (Windows):
- `D:\video-fila\bin\preparar_pc_linux.py` - Gera script de configuração
- `D:\video-fila\bin\canal_ia_remota.py` - Canal de comunicação IA-a-IA
- `D:\video-fila\logs\instrucoes_linux.sh` - Script bash para rodar nos Linux
- `D:\video-fila\logs\tarefas_remotas/` - Log de tarefas e respostas

### PCs Linux (após rodar o script):
- `/opt/video-producao/maquina.json` - Configuração e capacidades
- `/opt/video-producao/bin/status_api.py` - API HTTP porta 5000
- `/etc/systemd/system/video-status.service` - Serviço systemd
- `/tmp/ia-tarefas/` - Pasta de comunicação (tarefas recebidas)

---

## Próximos Passos (DEPOIS dos testes)

1. Adicionar máquinas em `D:\hipercool-videos\maquinas.py`
2. Integrar no painel `:8790` 
3. Configurar distribuição de tarefas no `controle.py`
4. Testar produção de vídeo end-to-end

---

## Troubleshooting

### "Connection refused" no SSH
- O script de configuração ainda não rodou no Linux
- OU o firewall bloqueou (rode o script novamente)

### "Timeout" na resposta da IA
- IA remota não está lendo `/tmp/ia-tarefas/NOVA_TAREFA`
- OU não tem Claude rodando naquele Linux
- Solução: usar `executar` direto em vez de `tarefa`

### API status não responde
```bash
# No Linux, verificar:
sudo systemctl status video-status
sudo systemctl restart video-status
curl http://localhost:5000/
```

---

## Comandos Rápidos

```bash
# Gerar script de configuração
python D:\video-fila\bin\preparar_pc_linux.py

# Ler script gerado
cat D:\video-fila\logs\instrucoes_linux.sh

# Testar conexão
python D:\video-fila\bin\canal_ia_remota.py testar x200ma

# Status completo
python D:\video-fila\bin\canal_ia_remota.py status x200ma

# Executar comando
python D:\video-fila\bin\canal_ia_remota.py executar x200ma "uptime"

# Ver ajuda
python D:\video-fila\bin\canal_ia_remota.py
```
