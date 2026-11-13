# Os perfis desta pasta mudaram de lugar (12/10/2026)

Tudo aqui agora é ATALHO de pasta (junção). Os perfis de verdade estão em `D:\logins-google\cofre\perfis\<conta>`,
uma pasta por conta, compartilhada por todos os projetos. Os caminhos daqui continuam funcionando.

- Onde está cada conta, o que foi movido e o que foi apagado: `D:\logins-google\cofre\MUDANCAS.md`
- Pedir uma conta num projeto: `D:\logins-google\cofre.py` -> `cofre.abrir("<conta>")`
- Logar uma conta de novo: `python D:\logins-google\cofre.py logar <conta>`
- Para remover um atalho daqui use `rmdir <pasta>` (ou Excluir no Explorer). NUNCA `rm -rf` nem apagar o conteúdo:
  isso apagaria a conta de verdade no cofre.
