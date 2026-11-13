"""Lembrete pedido pela dona em 30/10/2026: "as contas Kaggle não vou verificar até terça; me lembre depois de terça".
Tarefa agendada LembreteKaggleTelefone (04/11 09:00, uma vez) manda a lista pelo Telegram (avisos, importante)."""
import sys

sys.path.insert(0, r"D:\video-fila")
import avisos  # noqa: E402

CONTAS = ["emersonjosiel2027@gmail.com (central hermes-bloqueio — libera a 4ª GPU)",
          "emersonjosiel1995", "emersonjosiel2026", "emersonjosiel2029", "entrevistacomia", "fabiovideoseducativos",
          "fabricadeautomacoes0", "fabricadeautomacoesia", "filmescomia1", "gameoftroneskingsroadbrasil",
          "inovaremanhwabr", "inovaremanhwaverse", "inovaremanhwaverseesp", "inovaremanhwaversehindi", "jogoscomia",
          "jornalcomia", "maiteanajessicajesus", "msenergypara", "solarmundo195", "vendeafiliados3"]
texto = ("⏰ Lembrete (você pediu em 30/10): verificar o TELEFONE das contas do Kaggle — sem isso o kernel não tem "
         "internet nem GPU e o recap longo anda com menos GPUs.\n"
         + "\n".join(f"• {c}" for c in CONTAS)
         + "\n\nE entrar 1x no Kaggle com revolutionemerson2@gmail.com (conta nova pro rodízio). Depois de verificar, "
         "peça pra liberar no Claude (vps_central.py liberar).")
avisos.enviar(texto, "kaggle", importante=True)
print("lembrete enviado")
