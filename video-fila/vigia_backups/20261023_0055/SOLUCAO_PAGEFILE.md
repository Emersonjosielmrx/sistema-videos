# SOLUÇÃO: Mover pagefile.sys de D: para C:

## PROBLEMA IDENTIFICADO
- **D:\pagefile.sys: 16 GB** (arquivo de paginação do Windows)
- Configurado incorretamente no disco D: (HD de dados/projetos)
- Está consumindo quase todo o espaço necessário

## IMPACTO
- Espaço atual no D: 3.5 GB livres (98% usado)
- **Após mover pagefile para C: → 19.5 GB livres no D:** ✓✓✓
- Resolve COMPLETAMENTE o problema (mais que o dobro dos 8 GB mínimos)

## INSTRUÇÕES PARA O DONO

### Passo a passo (requer reinicialização do PC):

1. **Abrir Configurações do Sistema:**
   - Teclar `Windows + Pause/Break` OU
   - Clique direito em "Este Computador" → Propriedades
   - Clicar em "Configurações avançadas do sistema" (no menu lateral)

2. **Acessar Memória Virtual:**
   - Na janela "Propriedades do Sistema", aba "Avançado"
   - Seção "Desempenho" → botão "Configurações..."
   - Nova janela: aba "Avançado"
   - Seção "Memória virtual" → botão "Alterar..."

3. **Desmarcar gerenciamento automático:**
   - Desmarcar: "Gerenciar automaticamente o tamanho do arquivo de paginação para todas as unidades"

4. **Remover pagefile do D::**
   - Selecionar drive **D:** na lista
   - Marcar opção: **"Nenhum arquivo de paginação"**
   - Clicar em "Definir"

5. **Adicionar pagefile no C::**
   - Selecionar drive **C:** na lista
   - Marcar opção: **"Tamanho gerenciado pelo sistema"**
   - Clicar em "Definir"

6. **Aplicar e Reiniciar:**
   - Clicar "OK" em todas as janelas
   - **REINICIAR O COMPUTADOR** (obrigatório para liberar o espaço)

### Após reinicialização:
- D:\pagefile.sys será removido automaticamente
- C:\pagefile.sys será criado automaticamente
- D: terá ~19.5 GB livres

## POR QUE O PAGEFILE ESTAVA NO D:?
Provavelmente foi configurado manualmente quando:
- O SSD C: tinha pouco espaço livre
- Alguém tentou liberar espaço no C: movendo o pagefile para o D:

## POR QUE MOVER DE VOLTA PARA C:?
1. **Performance**: SSD é muito mais rápido que HD para paginação
2. **Espaço**: C: tem espaço suficiente agora
3. **Organização**: D: é para projetos/dados, não para sistema
4. **Problema resolvido**: Libera 16 GB no D: imediatamente

## ALTERNATIVA (se C: não tiver espaço)
Se o C: realmente não puder receber o pagefile (verificar espaço livre):
- Reduzir tamanho do pagefile no D: de 16 GB para 4-8 GB
- Mas idealmente deve estar no C: por questão de performance

## VERIFICAÇÃO
Após reiniciar, verificar com:
```bash
ls -lh /d/pagefile.sys  # deve dar erro "not found"
ls -lh /c/pagefile.sys  # deve existir
df -h /d                # deve mostrar ~19.5 GB livres
```
