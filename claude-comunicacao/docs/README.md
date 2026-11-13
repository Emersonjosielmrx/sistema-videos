# Projetos de Comunicação e Infraestrutura

## 1. Modo Fora de Casa (`D:\claude-comunicacao\modo-fora-de-casa\`)
Sistema para responder pelo Telegram quando não estiver no PC.
- Claude verifica mensagens novas no bot periodicamente
- Usuário manda texto/áudio pelo Telegram → Claude processa e responde
- Respostas vão como texto (Macrodroid lê em voz alta)

## 2. Chat de Voz (`D:\claude-comunicacao\chat-de-voz\`)
Sistema tipo Alexa para interagir por voz no PC.
- Palavra-chave ativa escuta (tipo "Hey Claude" ou outra)
- Transcreve áudio → envia como input pro Claude
- Resposta sai em voz (edge-tts já funciona)
- Alternativa: botão de atalho (tecla) pra ativar transcrição

## 3. Speech-to-Text com Botão
App/atalho que ao apertar uma tecla, transcreve voz em texto como se estivesse digitando.
- Funciona em qualquer campo de texto (VS Code, browser, etc.)
- Opções: Whisper local, Windows Speech Recognition, ou app dedicado

## 4. Cluster Caseiro (`D:\cluster-caseiro\`)
Usar outro PC na mesma rede WiFi como worker remoto.
- Enviar arquivos (painéis, scripts) pro PC remoto
- Executar pipeline de vídeo lá (usar CPU/GPU dele)
- Receber vídeos prontos de volta
- Tipo um mini render farm caseiro

---

Status: DOCUMENTADO. Implementar um por vez nas próximas sessões.
Prioridade sugerida: Speech-to-Text (mais rápido) → Modo Fora de Casa → Chat de Voz → Cluster
