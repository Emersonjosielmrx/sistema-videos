# Próximos passos: cadastrar o número no celular virtual (09/10/2026)

## Objetivo
Cadastrar um número no WhatsApp oficial rodando no celular virtual do PC (`wa-a37-4247`) e depois parear o
Hermes pela aba "Por código".

## Situação atual (conferida por adb em 09/10 ~10:45)
| Item | Estado |
|---|---|
| Emulador | `wa-a37-4247`, serial `emulator-5554`, Android 17 (API 37) com Google Play, ligado |
| WhatsApp | 2.26.39.75, instalado por `adb install` (sem loja). APK em `apk\WhatsApp.apk`, assinatura da WhatsApp Inc. (SHA-1 `38:A0:F7:D5:05:FE:18:FE:C6:4F:BF:34:3E:CA:AA:F3:10:DB:D7:99`) |
| Contas Google no aparelho | 0 |
| Play Store | instalada, ativa, parada na tela "Sign in" |
| Tela do WhatsApp | "Baixe o app oficial do WhatsApp para continuar" (`CustomRegistrationBlockActivity`): o WhatsApp não conseguiu confirmar que é o app oficial |
| Número cadastrado em celular virtual | nenhum até agora |
| Desempenho | 4 GB de RAM quase cheios; cada tela leva 20 a 60 s. Esperar, sem tocar repetido |

## O que precisa ser feito (nesta ordem)
1. **Entrar com uma conta Google na Play Store** (janela do emulador, botão Sign in). Usar uma conta dedicada a isso.
2. **Desinstalar o WhatsApp instalado por adb** (não há conta nele, nada se perde):
   `D:\whatsapp-activator-windows\sdk\platform-tools\adb.exe -s emulator-5554 uninstall com.whatsapp`
3. **Instalar o WhatsApp pela Play Store**: abrir
   `adb -s emulator-5554 shell am start -a android.intent.action.VIEW -d "market://details?id=com.whatsapp"`
   e tocar em Install.
4. **Abrir o WhatsApp e digitar o número e o código de SMS na janela do emulador** (com o mouse; toque automático por adb não é aceito nessa tela).
5. **Parear o Hermes**: aba "Por código" do painel (Hermes v0.10.0).
6. **Guardar o celular virtual**: não apagar `celulares\wa-a37-4247` nem matar o emulador enquanto a conta existir. Ligar alguns minutos a cada ~10 dias.

## Se o passo 4 ainda for recusado
O resultado depende da aceitação do WhatsApp para emulador; o Google não garante que um emulador comum passe como aparelho de verdade. Alternativas:
- Cadastrar o número num aparelho Android de verdade e parear o Hermes por código.
- API oficial da Meta (WhatsApp Business Platform): serve para atendimento e mensagens; ligação que parte da empresa exige autorização prévia de cada pessoa.

## Claude no terminal (anotação)
- Conta Claude logada no PC (pasta `C:\Users\Haylla\.claude`): plano Pro, login com renovação automática.
- O comando `claude` não está instalado; usar a cópia da extensão do VS Code (sem baixar nada, o disco C tem ~2,8 GB livres):
  ```powershell
  & (Get-ChildItem "$env:USERPROFILE\.vscode\extensions\anthropic.claude-code-*\resources\native-binary\claude.exe" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
  ```
- `/status` mostra a conta ativa; `/login` troca. O VS Code usa o OmniRoute (outra configuração), o terminal usa a assinatura.

## Referências
`README.md` (estado e API), `AVALIACAO.md` (análise), `D:\whatsapp-activator-windows\LEIA.md` (execução no PC).
