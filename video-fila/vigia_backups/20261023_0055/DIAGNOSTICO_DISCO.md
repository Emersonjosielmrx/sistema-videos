# DIAGNÓSTICO DE ESPAÇO EM DISCO D: — 23/10/2026 04:05

## SITUAÇÃO CRÍTICA
- **Espaço livre**: 3.5 GB (mínimo necessário: 8 GB)
- **Uso do disco**: 98% (163 GB / 167 GB)
- **Risco**: Produção para quando encher

## MAIORES CONSUMIDORES IDENTIFICADOS

### D:\caches (6.2 GB total)
1. **DriveFS: 2.0 GB** 
   - Google Drive cache
   - Última atividade: 10/out (13 dias atrás)
   - **SEGURO LIMPAR**: não usado pelos projetos de vídeo

2. **u2net: 1.7 GB**
   - Modelo de remoção de fundo (rembg)
   - **NÃO LIMPAR**: usado por bin/panel_effects.py do anime
   - Referência: doctor.py importa rembg

3. **ms-playwright: 1.4 GB**
   - Cache de navegador automatizado
   - **NÃO LIMPAR**: usado por hiper-fetcher.py

4. **go-build: 722 MB**
   - Cache de compilação Go
   - **SEGURO LIMPAR**: projetos são Python, não usam Go

5. **go-mod: 412 MB**
   - Módulos Go
   - **SEGURO LIMPAR**: projetos não usam Go
   - NOTA: tentativa de rm falhou (arquivo travado)

6. **npm-cache: 56 MB**
   - Cache do npm
   - **AVALIAR**: pode ser de ferramentas auxiliares

### Outras pastas temporárias
- D:\tmp: 114 MB (sistema bloqueou limpeza automática)
- D:\temp: 9.3 MB (sistema bloqueou limpeza automática)
- D:\tmp_hfsweep: 9.5 MB (sistema bloqueou remoção)
- D:\caches\teste_r2: 13 MB (REMOVIDO com sucesso)
- D:\caches\teste_imagem_gratis: 1.4 MB (REMOVIDO com sucesso)

### Outros grandes consumidores (comando du em andamento)
- historias-em-frames/workspace: 1.1 GB
- video-fila: 257 MB
- recapd-ambientes/producao/workspace/anime: 0 bytes (vazio)

## O QUE FOI FEITO
✓ Removidos caches de teste (14.4 MB)
✗ go-build/go-mod bloqueados pelo sistema de segurança
✗ tmp/temp bloqueados pelo sistema de segurança

## RECOMENDAÇÕES PARA AÇÃO MANUAL

### ALTA PRIORIDADE (libera ~3.2 GB)
1. **Limpar D:\caches\DriveFS** (2.0 GB)
   - Google Drive não usado pelos projetos
   - Comando: `rmdir /s /q D:\caches\DriveFS`

2. **Limpar D:\caches\go-build** (722 MB)
   - Projetos não usam Go
   - Comando: `rmdir /s /q D:\caches\go-build`

3. **Limpar D:\caches\go-mod** (412 MB)
   - Fechar processos que travam arquivos
   - Comando: `rmdir /s /q D:\caches\go-mod`

4. **Limpar D:\tmp e D:\temp** (123 MB)
   - Comando: `del /q D:\tmp\* && del /q D:\temp\*`

### MÉDIA PRIORIDADE (avaliar antes)
5. **D:\caches\npm-cache** (56 MB)
   - Verificar se ferramentas auxiliares precisam

### NÃO TOCAR
- u2net (1.7 GB): usado por anime
- ms-playwright (1.4 GB): usado por hiper-fetcher
- historias-em-frames/workspace (1.1 GB): projeto parado mas com dados

## ESPAÇO ESTIMADO APÓS LIMPEZA
- Atual: 3.5 GB livres
- Após limpeza: ~6.7 GB livres (DriveFS + go + tmp)
- **AINDA ABAIXO** dos 8 GB necessários

## ⚠️ CAUSA RAIZ IDENTIFICADA - PAGEFILE.SYS NO LUGAR ERRADO

### **D:\pagefile.sys: 16 GB**
- Arquivo de paginação do Windows configurado INCORRETAMENTE no D:
- Deveria estar no C: (SSD do sistema, melhor performance)
- **ESTÁ CONSUMINDO TODO O ESPAÇO QUE FALTA**

### IMPACTO
- Espaço atual: 3.5 GB livres
- **Sem pagefile.sys no D: → 19.5 GB livres** ✓✓✓
- Resolve o problema COMPLETAMENTE (mais que o dobro dos 8 GB necessários)

### SOLUÇÃO (requer intervenção manual do dono)
1. Painel de Controle → Sistema → Configurações avançadas do sistema
2. Aba "Avançado" → Desempenho → Configurações → Aba "Avançado"
3. Memória virtual → Alterar
4. Selecionar drive D: → "Nenhum arquivo de paginação"
5. Selecionar drive C: → "Tamanho gerenciado pelo sistema"
6. OK → Reiniciar o computador

### POR QUE ISTO ACONTECEU
Provavelmente configurado manualmente quando o C: tinha pouco espaço. Agora prejudica o D: (HD de dados).

## ANÁLISE ADICIONAL
O comando `du -sh /d/*` foi interrompido por timeout, mas não é mais necessário - a causa foi encontrada.

## COMO DESFAZER
- Pastas de teste removidas: eram temporárias, não há como restaurar (14 MB)
- DriveFS/go: se precisar, o sistema baixa/compila novamente
