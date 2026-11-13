import sys
from pathlib import Path
import shutil

BASE = Path("D:/recapd-ambientes/producao/workspace/anime")

apagados = 0
for work_dir in BASE.iterdir():
    if not work_dir.is_dir(): continue
    roteiro = work_dir / "roteiro.txt"
    if not roteiro.exists(): continue
    texto = roteiro.read_text(encoding="utf-8")
    texto_lower = texto.lower()

    # Achei mais palavras de recusa da IA no Obito!
    # "trata-se apenas de uma letra de musica", "nao e possivel realizar o recap", "aguardo o envio"
    recusas = [
        "não contém informações",
        "letra de música",
        "letra de musica",
        "não é possível realizar o recap",
        "não e possivel realizar o recap",
        "desculpe, mas não posso criar",
        "isso não parece ser a transcrição",
        "aguardando o envio",
        "assim que você enviar",
        "estou pronto para transformar",
        "transcrição enviada está incompleta",
        "contém apenas ruído",
        "[erro: lixo]",
        "lamento, mas não posso",
        "não tenho como gerar",
    ]

    # Padrões que PRECISAM de contexto para serem considerados lixo
    # (palavras comuns em narrativas legítimas — NÃO sao, por si só, indicador de garbage)
    # Usamos contexto: se a palavra aparecer seguida de "eu", "você" ou em sentença
    # que parece ser da IA (começa com "claro", "aqui está", etc), aí sim é filler/recusa
    fillers_ia = [
        "aqui está", "aqui vai", "espero que goste", "claro que sim",
        "aqui vai o roteiro", "retornando novamente",
    ]

    is_garbage = False
    for r in recusas:
        if r in texto_lower:
            is_garbage = True
            break

    # Verificar fillers de IA em cada linha
    if not is_garbage:
        for linha in texto.splitlines():
            ll = linha.lower().strip()
            # Linha começa com filler de IA?
            for f in fillers_ia:
                if ll.startswith(f):
                    is_garbage = True
                    break
            # Linha é só "Narrador:" ou "Personagem:" sem texto?
            if ":" in linha and len(linha.split()) < 3 and not texto_lower[texto_lower.find(linha.lower()):].count("\n") > 0:
                pass  # Permitir
            if is_garbage:
                break

    if is_garbage:
        print(f"LIXO IA: {work_dir.name} — apagando.")
        shutil.rmtree(work_dir)
        apagados += 1

print(f"\nApaguei mais {apagados} resquícios escondidos.")
